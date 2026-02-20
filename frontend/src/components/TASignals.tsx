'use client';

/**
 * Teknik Sinyal Bileşeni
 * =======================
 * TradingView tabanlı AL/SAT/NÖTR sinyalleri
 */

import { useEffect, useState } from 'react';
import { Activity, TrendingUp, TrendingDown, Minus, Loader2, Clock } from 'lucide-react';
import { getTASignals } from '@/lib/api';

interface TASignalsProps {
  symbol: string;
}

interface SignalData {
  summary: {
    recommendation: string;
    buy: number;
    sell: number;
    neutral: number;
  };
  oscillators: {
    recommendation: string;
    buy: number;
    sell: number;
    neutral: number;
    compute: Record<string, string>;
    values: Record<string, number>;
  };
  moving_averages: {
    recommendation: string;
    buy: number;
    sell: number;
    neutral: number;
    compute: Record<string, string>;
    values: Record<string, number>;
  };
  symbol: string;
  interval: string;
}

const INTERVALS = [
  { value: '1h', label: '1 Saat' },
  { value: '4h', label: '4 Saat' },
  { value: '1d', label: 'Günlük' },
  { value: '1W', label: 'Haftalık' },
  { value: '1M', label: 'Aylık' },
];

function getRecommendationColor(rec: string) {
  switch (rec?.toUpperCase()) {
    case 'STRONG_BUY': return 'text-green-300 bg-green-500/25 border border-green-500/40';
    case 'BUY': return 'text-green-300 bg-green-500/25 border border-green-500/40';
    case 'NEUTRAL': return 'text-yellow-300 bg-yellow-500/25 border border-yellow-500/40';
    case 'SELL': return 'text-red-300 bg-red-500/25 border border-red-500/40';
    case 'STRONG_SELL': return 'text-red-300 bg-red-600/30 border border-red-600/50';
    default: return 'text-gray-300 bg-gray-500/20 border border-gray-500/30';
  }
}

function getRecommendationLabel(rec: string) {
  switch (rec?.toUpperCase()) {
    case 'STRONG_BUY': return 'GÜÇLÜ AL';
    case 'BUY': return 'AL';
    case 'NEUTRAL': return 'NÖTR';
    case 'SELL': return 'SAT';
    case 'STRONG_SELL': return 'GÜÇLÜ SAT';
    default: return rec || '-';
  }
}

function getSignalIcon(rec: string) {
  switch (rec?.toUpperCase()) {
    case 'STRONG_BUY':
    case 'BUY':
      return <TrendingUp className="w-4 h-4" />;
    case 'SELL':
    case 'STRONG_SELL':
      return <TrendingDown className="w-4 h-4" />;
    default:
      return <Minus className="w-4 h-4" />;
  }
}

function getSignalBadgeColor(signal: string) {
  switch (signal?.toUpperCase()) {
    case 'BUY': return 'bg-green-500/30 text-green-300 border border-green-500/40';
    case 'SELL': return 'bg-red-500/30 text-red-300 border border-red-500/40';
    case 'NEUTRAL': return 'bg-gray-600/50 text-gray-200 border border-gray-500/40';
    default: return 'bg-gray-600/50 text-gray-200 border border-gray-500/40';
  }
}

export default function TASignals({ symbol }: TASignalsProps) {
  const [data, setData] = useState<SignalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [interval, setInterval] = useState('1d');

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const result = await getTASignals(symbol, interval) as SignalData & { error?: string };
        if (result && !result.error) {
          setData(result as SignalData);
        } else {
          setData(null);
        }
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [symbol, interval]);

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-center py-8 text-gray-300">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Teknik sinyaller yükleniyor...
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-bold text-white">Teknik Sinyaller</h3>
        </div>
        <p className="text-gray-300 text-sm">Sinyal verisi bulunamadı.</p>
      </div>
    );
  }

  const { summary, oscillators, moving_averages } = data;

  return (
    <div className="space-y-4">
      {/* Interval Selector & Summary */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white">Teknik Sinyaller</h3>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-3 h-3 text-gray-400" />
            <div className="flex gap-1">
              {INTERVALS.map((iv) => (
                <button
                  key={iv.value}
                  onClick={() => setInterval(iv.value)}
                  className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                    interval === iv.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                  }`}
                >
                  {iv.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Summary Gauge */}
        <div className="flex items-center justify-center mb-5">
          <div className={`flex items-center gap-3 px-8 py-4 rounded-xl text-3xl font-black ${getRecommendationColor(summary.recommendation)}`}>
            {getSignalIcon(summary.recommendation)}
            <span>{getRecommendationLabel(summary.recommendation)}</span>
          </div>
        </div>

        {/* Buy/Neutral/Sell counts */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-green-500/15 border border-green-500/30 rounded-lg p-3 text-center">
            <p className="text-3xl font-black text-green-300">{summary.buy}</p>
            <p className="text-sm font-semibold text-green-400 mt-0.5">Al</p>
          </div>
          <div className="bg-gray-600/30 border border-gray-500/40 rounded-lg p-3 text-center">
            <p className="text-3xl font-black text-gray-200">{summary.neutral}</p>
            <p className="text-sm font-semibold text-gray-400 mt-0.5">Nötr</p>
          </div>
          <div className="bg-red-500/15 border border-red-500/30 rounded-lg p-3 text-center">
            <p className="text-3xl font-black text-red-300">{summary.sell}</p>
            <p className="text-sm font-semibold text-red-400 mt-0.5">Sat</p>
          </div>
        </div>

        {/* Summary bar */}
        <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
          <div
            className="bg-green-500 rounded-l-full"
            style={{ width: `${(summary.buy / (summary.buy + summary.neutral + summary.sell)) * 100}%` }}
          />
          <div
            className="bg-gray-500"
            style={{ width: `${(summary.neutral / (summary.buy + summary.neutral + summary.sell)) * 100}%` }}
          />
          <div
            className="bg-red-500 rounded-r-full"
            style={{ width: `${(summary.sell / (summary.buy + summary.neutral + summary.sell)) * 100}%` }}
          />
        </div>
      </div>

      {/* Oscillators Section */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-base font-bold text-white">Osilatörler</h4>
          <span className={`px-3 py-1 rounded-lg text-xs font-bold ${getRecommendationColor(oscillators.recommendation)}`}>
            {getRecommendationLabel(oscillators.recommendation)}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Object.entries(oscillators.compute).map(([name, signal]) => (
            <div key={name} className="bg-gray-800 border border-gray-700 rounded-lg p-2.5 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-100">{name}</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${getSignalBadgeColor(signal)}`}>
                {signal === 'BUY' ? 'AL' : signal === 'SELL' ? 'SAT' : 'NÖTR'}
              </span>
            </div>
          ))}
        </div>
        {/* Oscillator values */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-1">
          {Object.entries(oscillators.values).slice(0, 12).map(([name, value]) => (
            <div key={name} className="flex justify-between px-2 py-1.5 rounded bg-gray-800/60">
              <span className="text-xs text-gray-400">{name}:</span>
              <span className="text-xs font-mono font-semibold text-gray-100">{typeof value === 'number' ? value.toFixed(2) : value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Moving Averages Section */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-base font-bold text-white">Hareketli Ortalamalar</h4>
          <span className={`px-3 py-1 rounded-lg text-xs font-bold ${getRecommendationColor(moving_averages.recommendation)}`}>
            {getRecommendationLabel(moving_averages.recommendation)}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Object.entries(moving_averages.compute).map(([name, signal]) => (
            <div key={name} className="bg-gray-800 border border-gray-700 rounded-lg p-2.5 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-100">{name}</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${getSignalBadgeColor(signal)}`}>
                {signal === 'BUY' ? 'AL' : signal === 'SELL' ? 'SAT' : 'NÖTR'}
              </span>
            </div>
          ))}
        </div>
        {/* Key MA values */}
        <div className="mt-4 grid grid-cols-2 gap-1">
          {['close', 'SMA20', 'SMA50', 'SMA200', 'EMA20', 'EMA50', 'EMA200', 'VWAP', 'BB.upper', 'BB.lower', 'ATR', 'P.SAR'].map((key) => {
            const val = moving_averages.values[key];
            if (val === undefined) return null;
            return (
              <div key={key} className="flex justify-between px-2 py-1.5 rounded bg-gray-800/60">
                <span className="text-xs text-gray-400">{key}:</span>
                <span className="text-xs font-mono font-semibold text-gray-100">
                  {typeof val === 'number' ? val.toFixed(2) : val}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
