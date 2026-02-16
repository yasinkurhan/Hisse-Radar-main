'use client';

import { useState, useEffect, useRef } from 'react';
import {
  BarChart3, TrendingUp, TrendingDown, DollarSign,
  PieChart, Activity, Building2, ArrowUpRight, ArrowDownRight,
  Info, RefreshCw
} from 'lucide-react';
import { getAdvancedFundamental } from '@/lib/api';

interface FundamentalChartsProps {
  symbol: string;
}

interface ChartData {
  revenue_trend: Array<{ period: string; value: number }>;
  profit_trend: Array<{ period: string; value: number }>;
  margin_trend: Array<{ period: string; gross_margin: number; net_margin: number }>;
  assets_liabilities: Array<{ period: string; assets: number; liabilities: number; equity: number }>;
  cash_flow_trend: Array<{ period: string; operating: number; investing: number; financing: number }>;
}

interface Ratios {
  profitability: { gross_margin?: number; net_margin?: number; roe?: number; roa?: number };
  liquidity: { current_ratio?: number; quick_ratio?: number };
  leverage: { debt_to_equity?: number };
  valuation: { pe_ratio?: number; pb_ratio?: number; ps_ratio?: number; ev_ebitda?: number };
}

interface GrowthMetrics {
  yoy_revenue_growth?: number;
  yoy_profit_growth?: number;
  cagr_3y_revenue?: number;
}

export default function FundamentalCharts({ symbol }: FundamentalChartsProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [charts, setCharts] = useState<ChartData | null>(null);
  const [ratios, setRatios] = useState<Ratios | null>(null);
  const [growth, setGrowth] = useState<GrowthMetrics | null>(null);
  const [valuation, setValuation] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'income' | 'balance' | 'cashflow'>('overview');

  const revenueCanvasRef = useRef<HTMLCanvasElement>(null);
  const marginCanvasRef = useRef<HTMLCanvasElement>(null);
  const balanceCanvasRef = useRef<HTMLCanvasElement>(null);
  const cashflowCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchData();
  }, [symbol]);

  useEffect(() => {
    if (charts) {
      drawCharts();
    }
  }, [charts, activeTab]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getAdvancedFundamental(symbol) as any;
      setCharts(data.charts_data);
      setRatios(data.ratios);
      setGrowth(data.growth_metrics);
      setValuation(data.valuation);
    } catch (err: any) {
      setError(err.message || 'Veri alınamadı');
    } finally {
      setLoading(false);
    }
  };

  const drawCharts = () => {
    if (!charts) return;

    // Gelir grafiği
    if (revenueCanvasRef.current && charts.revenue_trend?.length > 0) {
      drawBarChart(revenueCanvasRef.current, charts.revenue_trend, charts.profit_trend || [], 'Gelir & Kar (Milyon ₺)');
    }

    // Marj grafiği
    if (marginCanvasRef.current && charts.margin_trend?.length > 0) {
      drawMarginChart(marginCanvasRef.current, charts.margin_trend);
    }

    // Bilanço grafiği
    if (balanceCanvasRef.current && charts.assets_liabilities?.length > 0) {
      drawStackedBarChart(balanceCanvasRef.current, charts.assets_liabilities);
    }

    // Nakit akış grafiği
    if (cashflowCanvasRef.current && charts.cash_flow_trend?.length > 0) {
      drawCashFlowChart(cashflowCanvasRef.current, charts.cash_flow_trend);
    }
  };

  const drawBarChart = (
    canvas: HTMLCanvasElement,
    data1: Array<{ period: string; value: number }>,
    data2: Array<{ period: string; value: number }>,
    title: string
  ) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 20, bottom: 50, left: 70 };

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);

    const allValues = [...data1.map(d => d.value), ...data2.map(d => d.value)];
    const maxValue = Math.max(...allValues) * 1.1;
    const minValue = Math.min(0, ...allValues) * 1.1;
    const range = maxValue - minValue;

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const barGroupWidth = chartWidth / data1.length;
    const barWidth = barGroupWidth * 0.3;

    // Y ekseni
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;

    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const value = maxValue - (range / 5) * i;
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(formatNumber(value), padding.left - 8, y + 4);
    }

    // Barlar
    data1.forEach((d, i) => {
      const x = padding.left + barGroupWidth * i + barGroupWidth * 0.2;
      const barHeight = (d.value - minValue) / range * chartHeight;
      const y = padding.top + chartHeight - barHeight;

      // Gelir bar
      ctx.fillStyle = '#3b82f6';
      ctx.fillRect(x, y, barWidth, barHeight);

      // Kar bar
      if (data2[i]) {
        const profitHeight = (data2[i].value - minValue) / range * chartHeight;
        const profitY = padding.top + chartHeight - profitHeight;
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(x + barWidth + 4, profitY, barWidth, profitHeight);
      }

      // X etiketi
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.period, x + barWidth, height - padding.bottom + 20);
    });

    // Başlık
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(title, padding.left, 25);

    // Legend
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(width - 130, 15, 12, 12);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.fillText('Gelir', width - 115, 25);

    ctx.fillStyle = '#22c55e';
    ctx.fillRect(width - 70, 15, 12, 12);
    ctx.fillText('Kar', width - 55, 25);
  };

  const drawMarginChart = (canvas: HTMLCanvasElement, data: Array<{ period: string; gross_margin: number; net_margin: number }>) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 20, bottom: 50, left: 50 };

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Y ekseni (0-100%)
    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.strokeStyle = '#334155';
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const value = 100 - (20 * i);
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`%${value}`, padding.left - 8, y + 4);
    }

    const xScale = (i: number) => padding.left + (chartWidth / (data.length - 1)) * i;
    const yScale = (v: number) => padding.top + chartHeight - (v / 100 * chartHeight);

    // Gross margin çizgisi
    ctx.strokeStyle = '#8b5cf6';
    ctx.lineWidth = 3;
    ctx.beginPath();
    data.forEach((d, i) => {
      const x = xScale(i);
      const y = yScale(d.gross_margin);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Net margin çizgisi
    ctx.strokeStyle = '#f59e0b';
    ctx.beginPath();
    data.forEach((d, i) => {
      const x = xScale(i);
      const y = yScale(d.net_margin);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Noktalar ve etiketler
    data.forEach((d, i) => {
      const x = xScale(i);

      ctx.fillStyle = '#8b5cf6';
      ctx.beginPath();
      ctx.arc(x, yScale(d.gross_margin), 4, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#f59e0b';
      ctx.beginPath();
      ctx.arc(x, yScale(d.net_margin), 4, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.period, x, height - padding.bottom + 20);
    });

    // Başlık
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Kar Marjları (%)', padding.left, 25);

    // Legend
    ctx.fillStyle = '#8b5cf6';
    ctx.fillRect(width - 150, 15, 12, 12);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.fillText('Brüt', width - 135, 25);

    ctx.fillStyle = '#f59e0b';
    ctx.fillRect(width - 80, 15, 12, 12);
    ctx.fillText('Net', width - 65, 25);
  };

  const drawStackedBarChart = (canvas: HTMLCanvasElement, data: Array<{ period: string; assets: number; liabilities: number; equity: number }>) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 20, bottom: 50, left: 70 };

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const maxValue = Math.max(...data.map(d => d.assets)) * 1.1;
    const barWidth = chartWidth / data.length * 0.6;

    // Y ekseni
    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.strokeStyle = '#334155';
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const value = maxValue - (maxValue / 5) * i;
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(formatNumber(value), padding.left - 8, y + 4);
    }

    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / data.length) * i + (chartWidth / data.length - barWidth) / 2;

      // Borç
      const liabHeight = (d.liabilities / maxValue) * chartHeight;
      ctx.fillStyle = '#ef4444';
      ctx.fillRect(x, padding.top + chartHeight - liabHeight, barWidth / 2 - 2, liabHeight);

      // Özsermaye
      const equityHeight = (d.equity / maxValue) * chartHeight;
      ctx.fillStyle = '#22c55e';
      ctx.fillRect(x + barWidth / 2, padding.top + chartHeight - equityHeight, barWidth / 2 - 2, equityHeight);

      // X etiketi
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.period, x + barWidth / 2, height - padding.bottom + 20);
    });

    // Başlık
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Bilanço Yapısı (Milyon ₺)', padding.left, 25);

    // Legend
    ctx.fillStyle = '#ef4444';
    ctx.fillRect(width - 150, 15, 12, 12);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.fillText('Borç', width - 135, 25);

    ctx.fillStyle = '#22c55e';
    ctx.fillRect(width - 80, 15, 12, 12);
    ctx.fillText('Özkaynak', width - 65, 25);
  };

  const drawCashFlowChart = (canvas: HTMLCanvasElement, data: Array<{ period: string; operating: number; investing: number; financing: number }>) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 20, bottom: 50, left: 70 };

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, width, height);

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const allValues = data.flatMap(d => [d.operating, d.investing, d.financing]);
    const maxValue = Math.max(...allValues) * 1.1;
    const minValue = Math.min(...allValues) * 1.1;
    const range = maxValue - minValue;

    const yScale = (v: number) => padding.top + chartHeight - ((v - minValue) / range * chartHeight);
    const barGroupWidth = chartWidth / data.length;
    const barWidth = barGroupWidth * 0.2;

    // Y ekseni ve sıfır çizgisi
    const zeroY = yScale(0);

    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.strokeStyle = '#334155';
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const value = maxValue - (range / 5) * i;
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(formatNumber(value), padding.left - 8, y + 4);
    }

    // Sıfır çizgisi vurgu
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, zeroY);
    ctx.lineTo(width - padding.right, zeroY);
    ctx.stroke();
    ctx.lineWidth = 1;

    data.forEach((d, i) => {
      const x = padding.left + barGroupWidth * i + barGroupWidth * 0.15;

      const drawBar = (value: number, offsetX: number, color: string) => {
        const barHeight = Math.abs(value) / range * chartHeight;
        const y = value >= 0 ? yScale(value) : zeroY;
        ctx.fillStyle = color;
        ctx.fillRect(x + offsetX, y, barWidth, barHeight);
      };

      drawBar(d.operating, 0, '#22c55e');
      drawBar(d.investing, barWidth + 2, '#f59e0b');
      drawBar(d.financing, (barWidth + 2) * 2, '#3b82f6');

      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.period, x + barWidth * 1.5, height - padding.bottom + 20);
    });

    // Başlık
    ctx.fillStyle = '#f1f5f9';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Nakit Akışı (Milyon ₺)', padding.left, 25);
  };

  const formatNumber = (num: number) => {
    if (Math.abs(num) >= 1000) {
      return (num / 1000).toFixed(1) + 'B';
    }
    return num.toFixed(0) + 'M';
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-6 h-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Temel Analiz</h3>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-3" />
            <p className="text-slate-400">Finansal veriler yükleniyor...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-6 h-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Temel Analiz</h3>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 text-center">
          <Info className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
          <p className="text-yellow-400">{error}</p>
          <p className="text-slate-400 text-sm mt-2">Bu hisse için finansal veri bulunmuyor olabilir.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 sm:p-6 border-b border-slate-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Temel Analiz</h3>
              <p className="text-sm text-slate-400">Finansal tablolar ve oranlar</p>
            </div>
          </div>

          {/* Tab seçici */}
          <div className="flex gap-1 bg-slate-700/50 rounded-lg p-1">
            {[
              { id: 'overview', label: 'Özet', icon: PieChart },
              { id: 'income', label: 'Gelir', icon: TrendingUp },
              { id: 'balance', label: 'Bilanço', icon: Building2 },
              { id: 'cashflow', label: 'Nakit', icon: DollarSign }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition ${activeTab === id
                  ? 'bg-purple-500 text-white'
                  : 'text-slate-400 hover:text-white'
                  }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* İçerik */}
      <div className="p-4">
        {activeTab === 'overview' && ratios && (
          <div className="space-y-4">
            {/* Özet Kartları */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">F/K Oranı</p>
                <p className="text-xl font-bold text-white">
                  {ratios.valuation?.pe_ratio?.toFixed(1) || 'N/A'}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">PD/DD</p>
                <p className="text-xl font-bold text-white">
                  {ratios.valuation?.pb_ratio?.toFixed(2) || 'N/A'}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">ROE</p>
                <p className="text-xl font-bold text-green-400">
                  {ratios.profitability?.roe ? `%${ratios.profitability.roe.toFixed(1)}` : 'N/A'}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-slate-400 text-xs mb-1">Borç/Özkaynak</p>
                <p className="text-xl font-bold text-white">
                  {ratios.leverage?.debt_to_equity?.toFixed(2) || 'N/A'}
                </p>
              </div>
            </div>

            {/* Büyüme Metrikleri */}
            {growth && (
              <div className="bg-slate-700/30 rounded-lg p-4">
                <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-purple-400" />
                  Büyüme Metrikleri
                </h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-slate-400 text-xs">Yıllık Gelir Büyümesi</p>
                    <p className={`text-lg font-bold flex items-center gap-1 ${(growth.yoy_revenue_growth || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                      {(growth.yoy_revenue_growth || 0) >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      {growth.yoy_revenue_growth?.toFixed(1) || 'N/A'}%
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Yıllık Kar Büyümesi</p>
                    <p className={`text-lg font-bold flex items-center gap-1 ${(growth.yoy_profit_growth || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                      {(growth.yoy_profit_growth || 0) >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      {growth.yoy_profit_growth?.toFixed(1) || 'N/A'}%
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">3 Yıllık CAGR</p>
                    <p className={`text-lg font-bold ${(growth.cagr_3y_revenue || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                      {growth.cagr_3y_revenue?.toFixed(1) || 'N/A'}%
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Analist Hedefi */}
            {valuation && (valuation.target_mean || 0) > 0 && (
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-slate-400 text-sm">Analist Hedef Fiyat</p>
                    <p className="text-2xl font-bold text-white">₺{valuation.target_mean.toFixed(2)}</p>
                  </div>
                  {valuation.upside_potential && (
                    <div className={`text-right ${valuation.upside_potential >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      <p className="text-sm">Potansiyel</p>
                      <p className="text-xl font-bold">
                        {valuation.upside_potential >= 0 ? '+' : ''}{valuation.upside_potential.toFixed(1)}%
                      </p>
                    </div>
                  )}
                </div>
                {valuation.number_of_analysts > 0 && (
                  <p className="text-slate-400 text-xs mt-2">
                    {valuation.number_of_analysts} analist değerlendirmesi •
                    Düşük: ₺{valuation.target_low?.toFixed(2)} •
                    Yüksek: ₺{valuation.target_high?.toFixed(2)}
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'income' && charts && (
          <div className="space-y-4">
            <canvas ref={revenueCanvasRef} width={600} height={250} className="w-full rounded-lg" />
            <canvas ref={marginCanvasRef} width={600} height={200} className="w-full rounded-lg" />
          </div>
        )}

        {activeTab === 'balance' && charts && (
          <canvas ref={balanceCanvasRef} width={600} height={280} className="w-full rounded-lg" />
        )}

        {activeTab === 'cashflow' && charts && (
          <canvas ref={cashflowCanvasRef} width={600} height={280} className="w-full rounded-lg" />
        )}
      </div>
    </div>
  );
}
