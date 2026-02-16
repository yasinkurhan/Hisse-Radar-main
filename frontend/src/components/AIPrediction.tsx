'use client';

import { useState, useEffect, useRef } from 'react';
import { Brain, TrendingUp, TrendingDown, AlertCircle, Target, Shield, Zap, Info } from 'lucide-react';
import { getAIPrediction, getAISignal } from '@/lib/api';

interface AIPredictionProps {
  symbol: string;
}

interface Prediction {
  date: string;
  predicted_price: number;
  lower_bound: number;
  upper_bound: number;
}

interface AIResult {
  success: boolean;
  current_price: number;
  predictions: Prediction[];
  summary: {
    trend: string;
    expected_change_percent: number;
    target_price_7d: number;
    confidence_score: number;
    model_used: string;
  };
  support_resistance: {
    pivot: number;
    resistance_1: number;
    resistance_2: number;
    support_1: number;
    support_2: number;
  };
  ai_signal: {
    signal: string;
    strength: number;
    reason: string;
    target_price: number;
    stop_loss: number;
    take_profit: number;
  };
}

export default function AIPrediction({ symbol }: AIPredictionProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResult | null>(null);
  const [selectedDays, setSelectedDays] = useState(7);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchPrediction();
  }, [symbol, selectedDays]);

  useEffect(() => {
    if (result && canvasRef.current) {
      drawChart();
    }
  }, [result]);

  const fetchPrediction = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getAIPrediction(symbol, selectedDays, 'ensemble') as AIResult;
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Tahmin alınamadı');
    } finally {
      setLoading(false);
    }
  };

  const drawChart = () => {
    if (!canvasRef.current || !result) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Canvas boyutları
    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 30, bottom: 50, left: 70 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Arka plan gradient
    const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
    bgGradient.addColorStop(0, '#0f172a');
    bgGradient.addColorStop(1, '#1e293b');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, width, height);

    // Veri hazırla
    const currentPrice = result.current_price;
    const predictions = result.predictions;
    const allPrices = predictions.flatMap(p => [p.lower_bound, p.upper_bound, p.predicted_price]);
    allPrices.push(currentPrice);
    
    const minPrice = Math.min(...allPrices) * 0.97;
    const maxPrice = Math.max(...allPrices) * 1.03;
    const priceRange = maxPrice - minPrice;

    // Y ekseni (fiyat)
    const yScale = (price: number) => padding.top + chartHeight - ((price - minPrice) / priceRange * chartHeight);
    const xScale = (index: number) => padding.left + (index / predictions.length) * chartWidth;

    // Grid çizgileri - yatay
    ctx.strokeStyle = 'rgba(71, 85, 105, 0.3)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Fiyat etiketi
      const price = maxPrice - (priceRange / 5) * i;
      ctx.fillStyle = '#94a3b8';
      ctx.font = '12px Inter, system-ui, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`₺${price.toFixed(2)}`, padding.left - 10, y + 4);
    }
    ctx.setLineDash([]);

    // Grid çizgileri - dikey
    predictions.forEach((_, i) => {
      if (i % Math.ceil(predictions.length / 7) === 0) {
        const x = xScale(i + 1);
        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = 'rgba(71, 85, 105, 0.2)';
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, height - padding.bottom);
        ctx.stroke();
      }
    });
    ctx.setLineDash([]);

    // Güven aralığı (band) - gradient
    const bandGradient = ctx.createLinearGradient(0, yScale(maxPrice), 0, yScale(minPrice));
    bandGradient.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
    bandGradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.15)');
    bandGradient.addColorStop(1, 'rgba(59, 130, 246, 0.05)');
    
    ctx.fillStyle = bandGradient;
    ctx.beginPath();
    ctx.moveTo(padding.left, yScale(currentPrice));
    
    // Üst çizgi (smooth curve)
    predictions.forEach((p, i) => {
      const x = xScale(i + 1);
      const y = yScale(p.upper_bound);
      if (i === 0) {
        ctx.lineTo(x, y);
      } else {
        const prevX = xScale(i);
        const prevY = yScale(predictions[i-1].upper_bound);
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(cpX, prevY, x, y);
      }
    });
    
    // Alt çizgi (ters, smooth curve)
    for (let i = predictions.length - 1; i >= 0; i--) {
      const x = xScale(i + 1);
      const y = yScale(predictions[i].lower_bound);
      if (i === predictions.length - 1) {
        ctx.lineTo(x, y);
      } else {
        const nextX = xScale(i + 2);
        const nextY = yScale(predictions[i+1].lower_bound);
        const cpX = (nextX + x) / 2;
        ctx.quadraticCurveTo(cpX, nextY, x, y);
      }
    }
    
    ctx.lineTo(padding.left, yScale(currentPrice));
    ctx.closePath();
    ctx.fill();

    // Üst sınır çizgisi (glow efekti)
    ctx.strokeStyle = 'rgba(147, 197, 253, 0.5)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, yScale(currentPrice));
    predictions.forEach((p, i) => {
      const x = xScale(i + 1);
      const y = yScale(p.upper_bound);
      if (i === 0) {
        ctx.lineTo(x, y);
      } else {
        const prevX = xScale(i);
        const prevY = yScale(predictions[i-1].upper_bound);
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(cpX, prevY, x, y);
      }
    });
    ctx.stroke();

    // Alt sınır çizgisi
    ctx.beginPath();
    ctx.moveTo(padding.left, yScale(currentPrice));
    predictions.forEach((p, i) => {
      const x = xScale(i + 1);
      const y = yScale(predictions[i].lower_bound);
      if (i === 0) {
        ctx.lineTo(x, y);
      } else {
        const prevX = xScale(i);
        const prevY = yScale(predictions[i-1].lower_bound);
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(cpX, prevY, x, y);
      }
    });
    ctx.stroke();

    // Mevcut fiyat çizgisi (yatay, glow efekti)
    ctx.save();
    ctx.shadowColor = 'rgba(34, 197, 94, 0.5)';
    ctx.shadowBlur = 10;
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([8, 6]);
    ctx.beginPath();
    ctx.moveTo(padding.left, yScale(currentPrice));
    ctx.lineTo(width - padding.right, yScale(currentPrice));
    ctx.stroke();
    ctx.restore();
    ctx.setLineDash([]);

    // Ana tahmin çizgisi - glow efekti
    ctx.save();
    ctx.shadowColor = 'rgba(59, 130, 246, 0.8)';
    ctx.shadowBlur = 15;
    
    // Gradient çizgi
    const lineGradient = ctx.createLinearGradient(padding.left, 0, width - padding.right, 0);
    lineGradient.addColorStop(0, '#22c55e');
    lineGradient.addColorStop(0.3, '#3b82f6');
    lineGradient.addColorStop(1, '#8b5cf6');
    
    ctx.strokeStyle = lineGradient;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(padding.left, yScale(currentPrice));
    
    predictions.forEach((p, i) => {
      const x = xScale(i + 1);
      const y = yScale(p.predicted_price);
      if (i === 0) {
        ctx.lineTo(x, y);
      } else {
        const prevX = xScale(i);
        const prevY = yScale(predictions[i-1].predicted_price);
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(cpX, prevY, x, y);
      }
    });
    ctx.stroke();
    ctx.restore();

    // İkinci çizgi katmanı (daha ince, parlak)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, yScale(currentPrice));
    predictions.forEach((p, i) => {
      const x = xScale(i + 1);
      const y = yScale(p.predicted_price);
      if (i === 0) {
        ctx.lineTo(x, y);
      } else {
        const prevX = xScale(i);
        const prevY = yScale(predictions[i-1].predicted_price);
        const cpX = (prevX + x) / 2;
        ctx.quadraticCurveTo(cpX, prevY, x, y);
      }
    });
    ctx.stroke();

    // Noktalar - modern tasarım
    predictions.forEach((p, i) => {
      const x = xScale(i + 1);
      const y = yScale(p.predicted_price);
      
      // Glow efekti
      ctx.save();
      ctx.shadowColor = 'rgba(59, 130, 246, 0.8)';
      ctx.shadowBlur = 12;
      
      // Dış halka
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(59, 130, 246, 0.2)';
      ctx.fill();
      
      ctx.restore();
      
      // Orta halka
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#1e293b';
      ctx.fill();
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // İç nokta (gradient)
      const pointGradient = ctx.createRadialGradient(x-1, y-1, 0, x, y, 3);
      pointGradient.addColorStop(0, '#93c5fd');
      pointGradient.addColorStop(1, '#3b82f6');
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = pointGradient;
      ctx.fill();
    });

    // Başlangıç noktası (mevcut fiyat) - parlak yeşil
    ctx.save();
    ctx.shadowColor = 'rgba(34, 197, 94, 1)';
    ctx.shadowBlur = 20;
    
    // Dış glow
    ctx.beginPath();
    ctx.arc(padding.left, yScale(currentPrice), 12, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(34, 197, 94, 0.2)';
    ctx.fill();
    
    ctx.restore();
    
    // Ana nokta
    const startGradient = ctx.createRadialGradient(
      padding.left - 2, yScale(currentPrice) - 2, 0,
      padding.left, yScale(currentPrice), 8
    );
    startGradient.addColorStop(0, '#86efac');
    startGradient.addColorStop(0.5, '#22c55e');
    startGradient.addColorStop(1, '#16a34a');
    
    ctx.beginPath();
    ctx.arc(padding.left, yScale(currentPrice), 8, 0, Math.PI * 2);
    ctx.fillStyle = startGradient;
    ctx.fill();
    
    // Parlak merkez
    ctx.beginPath();
    ctx.arc(padding.left - 2, yScale(currentPrice) - 2, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.fill();

    // X ekseni etiketleri
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, system-ui, sans-serif';
    ctx.textAlign = 'center';
    
    predictions.forEach((p, i) => {
      const step = Math.max(1, Math.floor(predictions.length / 7));
      if (i % step === step - 1 || i === predictions.length - 1) {
        const date = new Date(p.date);
        const label = `${date.getDate()}/${date.getMonth() + 1}`;
        ctx.fillText(label, xScale(i + 1), height - padding.bottom + 25);
      }
    });

    // "Bugün" etiketi
    ctx.fillStyle = '#22c55e';
    ctx.font = 'bold 11px Inter, system-ui, sans-serif';
    ctx.fillText('Bugün', padding.left, height - padding.bottom + 25);

    // Başlık
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 14px Inter, system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`AI Fiyat Tahmini (${selectedDays} Gün)`, padding.left, 25);

    // Hedef fiyat göstergesi (sağ tarafta)
    const lastPrediction = predictions[predictions.length - 1];
    const targetY = yScale(lastPrediction.predicted_price);
    
    // Hedef çizgisi
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = 'rgba(139, 92, 246, 0.5)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(xScale(predictions.length), targetY);
    ctx.lineTo(width - padding.right + 5, targetY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Hedef fiyat etiketi
    ctx.fillStyle = '#8b5cf6';
    ctx.font = 'bold 11px Inter, system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`₺${lastPrediction.predicted_price.toFixed(2)}`, width - padding.right + 8, targetY + 4);
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'GÜÇLÜ AL': return 'text-green-400 bg-green-500/20 border-green-500/30';
      case 'AL': return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'GÜÇLÜ SAT': return 'text-red-400 bg-red-500/20 border-red-500/30';
      case 'SAT': return 'text-red-400 bg-red-500/10 border-red-500/20';
      default: return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
    }
  };

  const getSignalIcon = (signal: string) => {
    if (signal.includes('AL')) return <TrendingUp className="w-5 h-5" />;
    if (signal.includes('SAT')) return <TrendingDown className="w-5 h-5" />;
    return <AlertCircle className="w-5 h-5" />;
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-6 h-6 text-blue-400 animate-pulse" />
          <h3 className="text-lg font-semibold text-white">AI Fiyat Tahmini</h3>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-400">AI modeli çalışıyor...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">AI Fiyat Tahmini</h3>
        </div>
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-400">{error}</p>
          <button 
            onClick={fetchPrediction}
            className="mt-3 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const { summary, support_resistance, ai_signal } = result;
  const changePercent = summary.expected_change_percent;
  const isPositive = changePercent >= 0;

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 sm:p-6 border-b border-slate-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">AI Fiyat Tahmini</h3>
              <p className="text-sm text-slate-400">Ensemble ML Model</p>
            </div>
          </div>
          
          {/* Süre seçici */}
          <div className="flex gap-2">
            {[7, 14, 30].map((days) => (
              <button
                key={days}
                onClick={() => setSelectedDays(days)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  selectedDays === days
                    ? 'bg-blue-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {days} Gün
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* AI Sinyal Banner */}
      <div className={`p-4 border-b border-slate-700 ${getSignalColor(ai_signal.signal)}`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            {getSignalIcon(ai_signal.signal)}
            <div>
              <span className="text-lg font-bold">{ai_signal.signal}</span>
              <span className="ml-2 text-sm opacity-80">Güç: %{ai_signal.strength}</span>
            </div>
          </div>
          <p className="text-sm opacity-90">{ai_signal.reason}</p>
        </div>
      </div>

      {/* Grafik */}
      <div className="p-4 sm:p-6">
        <canvas
          ref={canvasRef}
          width={800}
          height={320}
          className="w-full rounded-lg"
          style={{ maxHeight: '250px' }}
        />
      </div>

      {/* Özet Kartları */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 border-t border-slate-700">
        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Target className="w-3 h-3" />
            <span>Hedef Fiyat</span>
          </div>
          <p className="text-lg font-bold text-white">₺{summary.target_price_7d.toFixed(2)}</p>
          <p className={`text-xs ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
          </p>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Zap className="w-3 h-3" />
            <span>Güven Skoru</span>
          </div>
          <p className="text-lg font-bold text-white">%{summary.confidence_score}</p>
          <div className="w-full h-1.5 bg-slate-600 rounded-full mt-1">
            <div 
              className={`h-full rounded-full ${
                summary.confidence_score >= 70 ? 'bg-green-500' :
                summary.confidence_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${summary.confidence_score}%` }}
            />
          </div>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Shield className="w-3 h-3" />
            <span>Stop Loss</span>
          </div>
          <p className="text-lg font-bold text-red-400">₺{ai_signal.stop_loss.toFixed(2)}</p>
          <p className="text-xs text-slate-400">Destek: ₺{support_resistance.support_1.toFixed(2)}</p>
        </div>

        <div className="bg-slate-700/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <TrendingUp className="w-3 h-3" />
            <span>Kar Al</span>
          </div>
          <p className="text-lg font-bold text-green-400">₺{ai_signal.take_profit.toFixed(2)}</p>
          <p className="text-xs text-slate-400">Direnç: ₺{support_resistance.resistance_1.toFixed(2)}</p>
        </div>
      </div>

      {/* Uyarı */}
      <div className="p-4 bg-slate-700/30 border-t border-slate-700">
        <div className="flex items-start gap-2 text-xs text-slate-400">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          <p>
            Bu tahminler yapay zeka modelleri tarafından üretilmiştir ve yatırım tavsiyesi niteliği taşımaz. 
            Tüm yatırım kararlarınızı kendi araştırmanıza dayanarak verin.
          </p>
        </div>
      </div>
    </div>
  );
}
