'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Triangle, Flag, Activity, BarChart3, Target, Layers, Zap, Gem, ArrowUpDown, CandlestickChart } from 'lucide-react';

interface ChartPattern {
  type: string;
  name: string;
  direction: string;
  confidence: number;
  current_price: number;
  target_price?: number;
  target_change?: number;
  description: string;
  signal: string;
  start_index: number;
  end_index: number;
  category?: string;
  neckline?: number;
  upper_channel?: number;
  lower_channel?: number;
  gap_size?: number;
  volume_ratio?: number;
}

interface FibLevel {
  ratio: number;
  price: number;
  label: string;
}

interface SRData {
  current_price: number;
  resistances: { price: number; strength: number }[];
  supports: { price: number; strength: number }[];
  nearest_resistance?: { price: number; strength: number };
  nearest_support?: { price: number; strength: number };
}

interface FibData {
  swing_high: number;
  swing_low: number;
  trend: string;
  current_price: number;
  closest_level: FibLevel;
  levels: Record<string, FibLevel>;
}

interface ChartPatternsProps {
  symbol: string;
  period?: string;
}

const CATEGORY_INFO: Record<string, { label: string; icon: any; color: string }> = {
  all: { label: 'Tümü', icon: Layers, color: 'blue' },
  classic: { label: 'Klasik', icon: Triangle, color: 'blue' },
  advanced: { label: 'Gelişmiş', icon: Gem, color: 'purple' },
  gap: { label: 'Boşluk', icon: ArrowUpDown, color: 'orange' },
  harmonic: { label: 'Harmonik', icon: Target, color: 'pink' },
  volume: { label: 'Hacim', icon: BarChart3, color: 'cyan' },
  candlestick: { label: 'Mum', icon: CandlestickChart, color: 'amber' },
};

export default function ChartPatterns({ symbol, period = '6mo' }: ChartPatternsProps) {
  const [loading, setLoading] = useState(true);
  const [patterns, setPatterns] = useState<ChartPattern[]>([]);
  const [summary, setSummary] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [fibData, setFibData] = useState<FibData | null>(null);
  const [srData, setSrData] = useState<SRData | null>(null);
  const [showFib, setShowFib] = useState(false);
  const [showSR, setShowSR] = useState(false);

  useEffect(() => {
    fetchPatterns();
  }, [symbol, period]);

  const fetchPatterns = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `http://localhost:8001/api/technical/${symbol}/patterns?period=${period}`
      );
      if (!response.ok) throw new Error('Formasyon verisi alınamadı');
      const data = await response.json();
      if (data.success) {
        setPatterns(data.patterns || []);
        setSummary(data.summary || '');
        setFibData(data.fibonacci || null);
        setSrData(data.support_resistance || null);
      } else {
        setError(data.message || 'Veri alınamadı');
      }
    } catch (err: any) {
      setError(err.message || 'Bağlantı hatası');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (cat: string) => {
    if (cat.includes('flag') || cat.includes('pennant')) return <Flag className="w-5 h-5" />;
    if (cat.includes('triangle') || cat.includes('wedge')) return <Triangle className="w-5 h-5" />;
    if (cat.includes('harmonic') || cat.includes('gartley') || cat.includes('butterfly') || cat.includes('bat') || cat.includes('crab') || cat.includes('abcd')) return <Target className="w-5 h-5" />;
    if (cat.includes('gap') || cat.includes('island')) return <ArrowUpDown className="w-5 h-5" />;
    if (cat.includes('volume') || cat.includes('accumulation') || cat.includes('distribution')) return <BarChart3 className="w-5 h-5" />;
    if (cat.includes('doji') || cat.includes('hammer') || cat.includes('engulfing') || cat.includes('star') || cat.includes('marubozu') || cat.includes('harami') || cat.includes('tweezer') || cat.includes('soldiers') || cat.includes('crows') || cat.includes('shooting') || cat.includes('hanging')) return <CandlestickChart className="w-5 h-5" />;
    if (cat.includes('channel') || cat.includes('rectangle') || cat.includes('broadening')) return <Activity className="w-5 h-5" />;
    if (cat.includes('cup') || cat.includes('rounding')) return <Gem className="w-5 h-5" />;
    return <TrendingUp className="w-5 h-5" />;
  };

  const getCategoryColor = (category?: string) => {
    const colors: Record<string, string> = {
      classic: 'text-blue-400 bg-blue-500/10',
      advanced: 'text-purple-400 bg-purple-500/10',
      gap: 'text-orange-400 bg-orange-500/10',
      harmonic: 'text-pink-400 bg-pink-500/10',
      volume: 'text-cyan-400 bg-cyan-500/10',
      candlestick: 'text-amber-400 bg-amber-500/10',
    };
    return colors[category || 'classic'] || 'text-blue-400 bg-blue-500/10';
  };

  const getSignalColor = (signal: string) => {
    if (signal === 'Al') return 'text-green-400 bg-green-500/10 border-green-500/30';
    if (signal === 'Sat') return 'text-red-400 bg-red-500/10 border-red-500/30';
    return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
  };

  const getDirectionIcon = (direction: string) => {
    if (direction === 'yukselis') return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (direction === 'dusus') return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Activity className="w-4 h-4 text-yellow-400" />;
  };

  const filteredPatterns = activeCategory === 'all'
    ? patterns
    : patterns.filter(p => p.category === activeCategory);

  // Kategorilerdeki formasyon sayıları
  const categoryCounts: Record<string, number> = {};
  patterns.forEach(p => {
    const c = p.category || 'classic';
    categoryCounts[c] = (categoryCounts[c] || 0) + 1;
  });

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-100 rounded w-1/3"></div>
          <div className="flex gap-2">{[...Array(5)].map((_, i) => <div key={i} className="h-8 bg-gray-100 rounded-lg w-20"></div>)}</div>
          <div className="h-24 bg-gray-100 rounded"></div>
          <div className="h-24 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="text-center text-red-400">
          <p className="text-lg font-medium">Hata</p>
          <p className="text-sm mt-2">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Özet */}
      {summary && (
        <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-gray-900 font-medium">{summary}</p>
              <p className="text-gray-500 text-xs mt-1">
                {patterns.length} formasyon · {Object.keys(categoryCounts).length} kategori
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Kategori sekmeleri */}
      <div className="flex gap-2 flex-wrap">
        {Object.entries(CATEGORY_INFO).map(([key, info]) => {
          const count = key === 'all' ? patterns.length : (categoryCounts[key] || 0);
          if (key !== 'all' && count === 0) return null;
          const Icon = info.icon;
          const isActive = activeCategory === key;
          return (
            <button
              key={key}
              onClick={() => setActiveCategory(key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                  : 'bg-white border border-gray-200 text-gray-500 border border-gray-200/50 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {info.label}
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${isActive ? 'bg-blue-500/30' : 'bg-gray-100'}`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Fibonacci & Destek/Direnç Toggle */}
      <div className="flex gap-2">
        {fibData && Object.keys(fibData).length > 0 && (
          <button
            onClick={() => setShowFib(!showFib)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition ${
              showFib ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-white border border-gray-200 text-gray-500 border border-gray-200/50 hover:text-gray-900'
            }`}
          >
            📐 Fibonacci
          </button>
        )}
        {srData && srData.resistances && (
          <button
            onClick={() => setShowSR(!showSR)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition ${
              showSR ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-white border border-gray-200 text-gray-500 border border-gray-200/50 hover:text-gray-900'
            }`}
          >
            📊 Destek/Direnç
          </button>
        )}
      </div>

      {/* Fibonacci Seviyeleri */}
      {showFib && fibData && fibData.levels && (
        <div className="bg-gradient-to-b from-amber-500/5 to-slate-800/50 border border-amber-500/20 rounded-xl p-4">
          <h3 className="text-amber-300 font-semibold mb-3 flex items-center gap-2">
            📐 Fibonacci Seviyeleri
            <span className="text-xs text-gray-500 font-normal">
              Swing: ₺{fibData.swing_low?.toFixed(2)} → ₺{fibData.swing_high?.toFixed(2)}
            </span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.entries(fibData.levels).map(([key, lv]) => {
              const isClose = fibData.closest_level && Math.abs(lv.price - fibData.closest_level.price) < 0.01;
              return (
                <div key={key} className={`rounded-lg p-2 text-center ${isClose ? 'bg-amber-500/20 border border-amber-500/30' : 'bg-gray-50'}`}>
                  <p className="text-xs text-gray-500">{lv.label}</p>
                  <p className={`font-semibold ${isClose ? 'text-amber-300' : 'text-gray-900'}`}>
                    ₺{lv.price.toFixed(2)}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Destek/Direnç */}
      {showSR && srData && (
        <div className="bg-gradient-to-b from-emerald-500/5 to-slate-800/50 border border-emerald-500/20 rounded-xl p-4">
          <h3 className="text-emerald-300 font-semibold mb-3">📊 Destek / Direnç Seviyeleri</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-red-400 text-sm font-medium mb-2">🔴 Direnç</p>
              {srData.resistances?.length > 0 ? srData.resistances.map((r, i) => (
                <div key={i} className={`flex justify-between py-1 px-2 rounded ${srData.nearest_resistance?.price === r.price ? 'bg-red-500/10' : ''}`}>
                  <span className="text-gray-900">₺{r.price.toFixed(2)}</span>
                  <span className="text-gray-500 text-sm">Güç: {r.strength}</span>
                </div>
              )) : <p className="text-slate-500 text-sm">Seviye bulunamadı</p>}
            </div>
            <div>
              <p className="text-green-400 text-sm font-medium mb-2">🟢 Destek</p>
              {srData.supports?.length > 0 ? srData.supports.map((s, i) => (
                <div key={i} className={`flex justify-between py-1 px-2 rounded ${srData.nearest_support?.price === s.price ? 'bg-green-500/10' : ''}`}>
                  <span className="text-gray-900">₺{s.price.toFixed(2)}</span>
                  <span className="text-gray-500 text-sm">Güç: {s.strength}</span>
                </div>
              )) : <p className="text-slate-500 text-sm">Seviye bulunamadı</p>}
            </div>
          </div>
        </div>
      )}

      {/* Formasyonlar */}
      {filteredPatterns.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-gray-500">
            {activeCategory === 'all' ? 'Belirgin formasyon tespit edilmedi' : 'Bu kategoride formasyon yok'}
          </p>
          <p className="text-slate-500 text-sm mt-2">Farklı bir zaman dilimi deneyin</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filteredPatterns.map((pattern, index) => (
            <div
              key={index}
              className="bg-white border border-gray-200 hover:bg-white/70 transition rounded-xl p-4 border border-gray-200/50"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${getCategoryColor(pattern.category)}`}>
                    {getCategoryIcon(pattern.type)}
                  </div>
                  <div>
                    <h3 className="text-gray-900 font-semibold flex items-center gap-2">
                      {pattern.name}
                      {getDirectionIcon(pattern.direction)}
                    </h3>
                    <p className="text-gray-500 text-sm">{pattern.description}</p>
                  </div>
                </div>
                <div className={`px-3 py-1 rounded-lg text-sm font-medium border whitespace-nowrap ${getSignalColor(pattern.signal)}`}>
                  {pattern.signal}
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-gray-200/50">
                <div>
                  <p className="text-slate-500 text-xs mb-1">Güven</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full ${pattern.confidence >= 75 ? 'bg-green-500' : pattern.confidence >= 60 ? 'bg-yellow-500' : 'bg-orange-500'}`}
                        style={{ width: `${pattern.confidence}%` }}
                      ></div>
                    </div>
                    <span className="text-gray-900 font-medium text-sm">%{Math.round(pattern.confidence)}</span>
                  </div>
                </div>
                <div>
                  <p className="text-slate-500 text-xs mb-1">Fiyat</p>
                  <p className="text-gray-900 font-semibold">₺{pattern.current_price.toFixed(2)}</p>
                </div>
                {pattern.target_price != null && (
                  <div>
                    <p className="text-slate-500 text-xs mb-1">Hedef</p>
                    <p className="text-gray-900 font-semibold">₺{pattern.target_price.toFixed(2)}</p>
                  </div>
                )}
                {pattern.target_change != null && (
                  <div>
                    <p className="text-slate-500 text-xs mb-1">Potansiyel</p>
                    <p className={`font-semibold ${pattern.target_change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {pattern.target_change > 0 ? '+' : ''}{pattern.target_change.toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>

              {(pattern.neckline || pattern.upper_channel || pattern.lower_channel || pattern.gap_size) && (
                <div className="flex flex-wrap gap-3 mt-3 pt-3 border-t border-gray-200/50 text-sm">
                  {pattern.neckline != null && (
                    <span className="text-gray-600">Boyun: <b>₺{pattern.neckline.toFixed(2)}</b></span>
                  )}
                  {pattern.upper_channel != null && (
                    <span className="text-gray-600">Üst: <b>₺{pattern.upper_channel.toFixed(2)}</b></span>
                  )}
                  {pattern.lower_channel != null && (
                    <span className="text-gray-600">Alt: <b>₺{pattern.lower_channel.toFixed(2)}</b></span>
                  )}
                  {pattern.gap_size != null && (
                    <span className="text-gray-600">Boşluk: <b>%{pattern.gap_size.toFixed(2)}</b></span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="bg-white/30 rounded-lg p-4 text-sm text-gray-500">
        <p className="flex items-center gap-2">
          <span className="text-blue-400">ℹ️</span>
          Profesyonel formasyon robotu 8 kategoride 35+ formasyon tipi analiz eder. Yatırım tavsiyesi değildir.
        </p>
      </div>
    </div>
  );
}
