'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface PerformanceStats {
  total_signals: number;
  win_rate: number;
  avg_profit: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  expectancy: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  final_capital_100k: number;
  al_win_rate: number;
  sat_win_rate: number;
  guclu_al_win_rate: number;
  high_score_win_rate: number;
  mid_score_win_rate: number;
  low_score_win_rate: number;
  kar_al_count: number;
  zarar_kes_count: number;
  zaman_asimi_count: number;
  avg_days_held: number;
  equity_curve: number[];
  monthly_performance: { month: string; avg_profit: number; trade_count: number; win_count: number }[];
  top_symbols: { symbol: string; trades: number; avg_profit: number; win_rate: number }[];
  worst_symbols: { symbol: string; trades: number; avg_profit: number; win_rate: number }[];
  last_updated: string;
}

interface ActiveSignal {
  symbol: string;
  signal: string;
  score: number;
  entry_price: number;
  date: string;
  status: string;
  exit_price: number | null;
  exit_date: string | null;
  profit_pct: number | null;
}

interface CompletedSignal {
  symbol: string;
  signal: string;
  score: number;
  entry_price: number;
  exit_price: number;
  profit_pct: number;
  date: string;
  exit_date: string;
  exit_reason: string;
  days_held: number;
  status: string;
}

interface SymbolRow {
  symbol: string;
  total_trades: number;
  win_count: number;
  win_rate: number;
  avg_profit: number;
  total_profit: number;
  best_trade: number;
  worst_trade: number;
  avg_days: number;
}

interface HistoricalResult {
  symbol?: string;
  period?: string;
  total_trades: number;
  winning_trades: number;
  win_rate: number;
  total_profit: number;
  avg_profit: number;
  avg_days_held: number;
  best_trade: number;
  worst_trade: number;
  trades: { entry_price: number; exit_price: number; profit_pct: number; days_held: number; score: number }[];
  error?: string;
}

interface MarketCondition {
  condition: string;
  trend: string;
  volatility: string;
  recommendation: string;
  details: { rsi: number; trend_direction: string; above_sma20: boolean; above_sma50: boolean };
}

function MiniEquityCurve({ data }: { data: number[] }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const w = 300; const h = 60;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * (h - 4) - 2;
    return `${x},${y}`;
  }).join(' ');
  const last = data[data.length - 1];
  const color = last >= 100 ? '#4ade80' : '#f87171';
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-16">
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
    </svg>
  );
}

export default function BacktestPage() {
  const [performance, setPerformance] = useState<PerformanceStats | null>(null);
  const [activeSignals, setActiveSignals] = useState<ActiveSignal[]>([]);
  const [recentResults, setRecentResults] = useState<CompletedSignal[]>([]);
  const [symbolBreakdown, setSymbolBreakdown] = useState<SymbolRow[]>([]);
  const [marketCondition, setMarketCondition] = useState<MarketCondition | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'active' | 'history' | 'symbols' | 'historical'>('overview');
  const [historicalSymbol, setHistoricalSymbol] = useState('ASELS');
  const [historicalPeriod, setHistoricalPeriod] = useState('1y');
  const [historicalResult, setHistoricalResult] = useState<HistoricalResult | null>(null);
  const [historicalLoading, setHistoricalLoading] = useState(false);

  useEffect(() => { fetchAllData(); }, []);

  const fetchWithTimeout = async (url: string, timeoutMs = 10000) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      // Tamamen benzersiz bir query parametresi ekleyerek TARAYICI ve ServiceWorker önbelleklerini zorla aşıyoruz.
      const separator = url.includes('?') ? '&' : '?';
      const cacheBustedUrl = `${url}${separator}_t=${Date.now()}`;
      
      const res = await fetch(cacheBustedUrl, { 
        signal: controller.signal,
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      clearTimeout(timeout);
      return res.ok ? await res.json() : null;
    } catch { 
      clearTimeout(timeout); 
      return null; 
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    const defaultMarket: MarketCondition = {
      condition: 'neutral', trend: 'Yatay', volatility: 'Normal',
      recommendation: 'Piyasa verisi yükleniyor...',
      details: { rsi: 50, trend_direction: 'neutral', above_sma20: false, above_sma50: false }
    };
    try {
      const [perfData, activeData, recentData, marketData, symbolData] = await Promise.all([
        fetchWithTimeout('http://localhost:8000/api/backtest/performance'),
        fetchWithTimeout('http://localhost:8000/api/backtest/active-signals'),
        fetchWithTimeout('http://localhost:8000/api/backtest/recent-results?limit=50'),
        fetchWithTimeout('http://localhost:8000/api/backtest/market-condition', 15000),
        fetchWithTimeout('http://localhost:8000/api/backtest/symbol-breakdown'),
      ]);
      if (perfData) setPerformance(perfData);
      if (activeData) setActiveSignals(activeData);
      if (recentData) setRecentResults(recentData);
      if (symbolData) setSymbolBreakdown(symbolData);
      setMarketCondition(marketData || defaultMarket);
      setLastRefresh(new Date().toLocaleTimeString('tr-TR'));
    } catch { setMarketCondition(defaultMarket); }
    finally { setLoading(false); }
  };

  const refreshSignals = async () => {
    setRefreshing(true);
    try {
      await fetchWithTimeout('http://localhost:8000/api/backtest/refresh');
      await fetchAllData();
    } catch { } finally { setRefreshing(false); }
  };

  const runHistorical = async () => {
    setHistoricalLoading(true);
    setHistoricalResult(null);
    try {
      const data = await fetchWithTimeout(
        `http://localhost:8000/api/backtest/historical/${historicalSymbol.toUpperCase()}?period=${historicalPeriod}`, 30000
      );
      setHistoricalResult(data);
    } finally { setHistoricalLoading(false); }
  };

  const getSignalColor = (s: string) => s.includes('AL') ? 'text-green-400' : s.includes('SAT') ? 'text-red-400' : 'text-yellow-400';
  const getConditionColor = (c: string) => c === 'bullish' ? 'text-green-400' : c === 'bearish' ? 'text-red-400' : 'text-yellow-400';
  const fmt = (n: number, d = 1) => (n ?? 0).toFixed(d);

  if (loading) return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
        <p>Backtest verileri yükleniyor...</p>
      </div>
    </div>
  );

  const tabs: { key: typeof activeTab; label: string }[] = [
    { key: 'overview', label: '📈 Genel Bakış' },
    { key: 'active', label: `🎯 Aktif (${activeSignals.length})` },
    { key: 'history', label: `📜 Geçmiş (${recentResults.length})` },
    { key: 'symbols', label: '🏆 Hisse Analizi' },
    { key: 'historical', label: '🔬 Geçmiş Test' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold">📊 Backtest & Performans</h1>
            <p className="text-gray-400 mt-1">Geçmiş sinyallerin başarı analizi</p>
            {lastRefresh && <p className="text-gray-500 text-xs mt-1">Son güncelleme: {lastRefresh}</p>}
          </div>
          <div className="flex gap-2 flex-wrap">
            <button onClick={refreshSignals} disabled={refreshing}
              className={`px-3 py-2 rounded text-sm flex items-center gap-2 ${refreshing ? 'bg-yellow-600 cursor-wait' : 'bg-green-600 hover:bg-green-700'}`}>
              <span className={refreshing ? 'animate-spin inline-block' : ''}>🔄</span>
              {refreshing ? 'Güncelleniyor...' : 'Güncelle'}
            </button>
            <button onClick={fetchAllData} className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm">📥 Yenile</button>
            <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded text-sm">← Ana Sayfa</Link>
          </div>
        </div>

        {/* Market Condition */}
        {marketCondition && (
          <div className="bg-gray-800 rounded-xl p-4 sm:p-6 mb-6 border border-gray-700">
            <h2 className="text-lg font-semibold mb-3">🌍 Piyasa Durumu (BIST100)</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Durum', value: marketCondition.condition === 'bullish' ? '🐂 Boğa' : marketCondition.condition === 'bearish' ? '🐻 Ayı' : '➡️ Yatay', color: getConditionColor(marketCondition.condition) },
                { label: 'Trend', value: marketCondition.trend, color: 'text-white' },
                { label: 'Volatilite', value: marketCondition.volatility, color: 'text-white' },
                { label: 'RSI', value: marketCondition.details?.rsi?.toFixed(1) ?? 'N/A', color: 'text-white' },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-gray-700/50 rounded-lg p-3">
                  <p className="text-gray-400 text-xs mb-1">{label}</p>
                  <p className={`text-xl font-bold ${color}`}>{value}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 p-3 bg-blue-900/30 rounded-lg">
              <p className="text-blue-300 text-sm">💡 {marketCondition.recommendation}</p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {tabs.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === t.key ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {performance && performance.total_signals ? (
              <>
                {/* Temel metrikler */}
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h2 className="text-lg font-semibold mb-4">🎯 Temel Performans</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    {[
                      { label: 'Toplam Sinyal', value: String(performance.total_signals), color: 'text-blue-400' },
                      { label: 'Kazanma Oranı', value: `%${fmt(performance.win_rate)}`, color: performance.win_rate >= 50 ? 'text-green-400' : 'text-red-400' },
                      { label: 'Ort. Kar/Zarar', value: `%${fmt(performance.avg_profit, 2)}`, color: performance.avg_profit >= 0 ? 'text-green-400' : 'text-red-400' },
                      { label: 'Ort. Kazanç', value: `%${fmt(performance.avg_win, 2)}`, color: 'text-green-400' },
                      { label: 'Ort. Kayıp', value: `%${fmt(performance.avg_loss, 2)}`, color: 'text-red-400' },
                      { label: 'Ort. Süre', value: `${fmt(performance.avg_days_held, 0)} gün`, color: 'text-gray-300' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="bg-gray-700/50 rounded-lg p-3 text-center">
                        <p className="text-gray-400 text-xs mb-1">{label}</p>
                        <p className={`text-xl font-bold ${color}`}>{value}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* İleri metrikler */}
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h2 className="text-lg font-semibold mb-4">⚡ İleri Metrikler</h2>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-xs mb-1">Profit Factor</p>
                      <p className={`text-2xl font-bold ${(performance.profit_factor ?? 0) >= 1.5 ? 'text-green-400' : (performance.profit_factor ?? 0) >= 1 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {fmt(performance.profit_factor ?? 0, 2)}
                      </p>
                      <p className="text-gray-500 text-xs mt-1">≥1.5 = İyi</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-xs mb-1">Beklenti (Expectancy)</p>
                      <p className={`text-2xl font-bold ${(performance.expectancy ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        %{fmt(performance.expectancy ?? 0, 2)}
                      </p>
                      <p className="text-gray-500 text-xs mt-1">İşlem başı ort. getiri</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-xs mb-1">Sharpe Oranı</p>
                      <p className={`text-2xl font-bold ${(performance.sharpe_ratio ?? 0) >= 1 ? 'text-green-400' : (performance.sharpe_ratio ?? 0) >= 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {fmt(performance.sharpe_ratio ?? 0, 2)}
                      </p>
                      <p className="text-gray-500 text-xs mt-1">≥1.0 = İyi</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-gray-400 text-xs mb-1">Maks. Drawdown</p>
                      <p className={`text-2xl font-bold ${(performance.max_drawdown ?? 0) <= 10 ? 'text-green-400' : (performance.max_drawdown ?? 0) <= 20 ? 'text-yellow-400' : 'text-red-400'}`}>
                        -%{fmt(performance.max_drawdown ?? 0, 1)}
                      </p>
                      <p className="text-gray-500 text-xs mt-1">≤10% = İyi</p>
                    </div>
                  </div>

                  {/* Sermaye Simülasyonu */}
                  <div className="mt-4 bg-gray-900/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-gray-300 text-sm font-medium">💰 Sermaye Simülasyonu (100.000 TL başlangıç)</p>
                      <p className={`text-lg font-bold ${(performance.total_return ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(performance.total_return ?? 0) >= 0 ? '+' : ''}{fmt(performance.total_return ?? 0, 1)}% → {(performance.final_capital_100k ?? 100000).toLocaleString('tr-TR')} ₺
                      </p>
                    </div>
                    {performance.equity_curve && performance.equity_curve.length > 1 && (
                      <MiniEquityCurve data={performance.equity_curve} />
                    )}
                  </div>
                </div>

                {/* Sinyal & Skor bazlı */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <h2 className="text-lg font-semibold mb-4">📊 Sinyal Türüne Göre</h2>
                    <div className="space-y-3">
                      {[
                        { label: '🟢 GÜÇLÜ AL', rate: performance.guclu_al_win_rate ?? 0 },
                        { label: '🟩 AL', rate: performance.al_win_rate ?? 0 },
                        { label: '🔴 SAT', rate: performance.sat_win_rate ?? 0 },
                      ].map(({ label, rate }) => (
                        <div key={label}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-300">{label}</span>
                            <span className={rate >= 50 ? 'text-green-400' : 'text-red-400'}>%{fmt(rate)}</span>
                          </div>
                          <div className="bg-gray-700 rounded-full h-2">
                            <div className={`h-2 rounded-full ${rate >= 50 ? 'bg-green-500' : 'bg-red-500'}`} style={{ width: `${Math.min(rate, 100)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <h2 className="text-lg font-semibold mb-4">🎯 Skor Grubuna Göre</h2>
                    <div className="space-y-3">
                      {[
                        { label: '⭐ Yüksek Skor (≥70)', rate: performance.high_score_win_rate ?? 0 },
                        { label: '🔵 Orta Skor (50-69)', rate: performance.mid_score_win_rate ?? 0 },
                        { label: '⚪ Düşük Skor (<50)', rate: performance.low_score_win_rate ?? 0 },
                      ].map(({ label, rate }) => (
                        <div key={label}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-300">{label}</span>
                            <span className={rate >= 50 ? 'text-green-400' : 'text-red-400'}>%{fmt(rate)}</span>
                          </div>
                          <div className="bg-gray-700 rounded-full h-2">
                            <div className={`h-2 rounded-full ${rate >= 50 ? 'bg-green-500' : 'bg-yellow-500'}`} style={{ width: `${Math.min(rate, 100)}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Çıkış Nedenleri */}
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h2 className="text-lg font-semibold mb-4">🚪 Çıkış Nedenleri</h2>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-green-900/20 rounded-lg p-4 text-center border border-green-800/50">
                      <p className="text-green-300 text-xs mb-1">✅ Kar Al (%10)</p>
                      <p className="text-3xl font-bold text-green-400">{performance.kar_al_count ?? 0}</p>
                      <p className="text-gray-400 text-xs mt-1">sinyal</p>
                    </div>
                    <div className="bg-red-900/20 rounded-lg p-4 text-center border border-red-800/50">
                      <p className="text-red-300 text-xs mb-1">🛑 Stop Loss (-%7)</p>
                      <p className="text-3xl font-bold text-red-400">{performance.zarar_kes_count ?? 0}</p>
                      <p className="text-gray-400 text-xs mt-1">sinyal</p>
                    </div>
                    <div className="bg-yellow-900/20 rounded-lg p-4 text-center border border-yellow-800/50">
                      <p className="text-yellow-300 text-xs mb-1">⏱ Süre Aşımı (30g)</p>
                      <p className="text-3xl font-bold text-yellow-400">{performance.zaman_asimi_count ?? 0}</p>
                      <p className="text-gray-400 text-xs mt-1">sinyal</p>
                    </div>
                  </div>
                </div>

                {/* Aylık Performans */}
                {performance.monthly_performance && performance.monthly_performance.length > 0 && (
                  <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <h2 className="text-lg font-semibold mb-4">📅 Aylık Performans</h2>
                    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                      {performance.monthly_performance.map(m => (
                        <div key={m.month} className={`rounded-lg p-3 text-center border ${m.avg_profit >= 0 ? 'bg-green-900/20 border-green-800/50' : 'bg-red-900/20 border-red-800/50'}`}>
                          <p className="text-gray-400 text-xs">{m.month}</p>
                          <p className={`font-bold text-sm ${m.avg_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {m.avg_profit >= 0 ? '+' : ''}{fmt(m.avg_profit, 1)}%
                          </p>
                          <p className="text-gray-500 text-xs">{m.win_count}/{m.trade_count}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-xs text-gray-500 text-right">Son güncelleme: {performance.last_updated}</p>
              </>
            ) : (
              <div className="bg-gray-800 rounded-xl p-10 text-center border border-gray-700">
                <p className="text-4xl mb-3">📭</p>
                <p className="text-lg text-gray-300">Henüz backtest verisi yok</p>
                <p className="text-sm text-gray-500 mt-2">Analiz sayfasından analiz yaparak sinyal oluşturun — performans otomatik takip edilecek.</p>
              </div>
            )}
          </div>
        )}

        {/* ── ACTIVE TAB ── */}
        {activeTab === 'active' && (
          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4">🎯 Aktif Sinyaller ({activeSignals.length} adet)</h2>
            {activeSignals.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz aktif sinyal yok.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-400 border-b border-gray-700">
                      {['Hisse', 'Sinyal', 'Skor', 'Giriş', 'Tarih', 'Durum'].map(h => (
                        <th key={h} className="py-3 px-3 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activeSignals.map((s, i) => (
                      <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                        <td className="py-3 px-3">
                          <Link href={`/stock/${s.symbol}`} className="text-blue-400 hover:underline font-semibold">{s.symbol}</Link>
                        </td>
                        <td className={`py-3 px-3 font-semibold ${getSignalColor(s.signal)}`}>{s.signal}</td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-1 rounded text-xs ${s.score >= 70 ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'}`}>{s.score}</span>
                        </td>
                        <td className="py-3 px-3">₺{s.entry_price.toFixed(2)}</td>
                        <td className="py-3 px-3 text-gray-400">{s.date}</td>
                        <td className="py-3 px-3"><span className="px-2 py-1 rounded text-xs bg-blue-900/50 text-blue-400">🔄 Aktif</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── HISTORY TAB ── */}
        {activeTab === 'history' && (
          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4">📜 Sinyal Geçmişi</h2>
            {recentResults.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz sonuçlanan sinyal yok.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-400 border-b border-gray-700">
                      {['Hisse', 'Sinyal', 'Skor', 'Giriş', 'Çıkış', 'K/Z', 'Gün', 'Neden'].map(h => (
                        <th key={h} className="py-3 px-3 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {recentResults.map((r, i) => (
                      <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                        <td className="py-3 px-3"><Link href={`/stock/${r.symbol}`} className="text-blue-400 hover:underline font-semibold">{r.symbol}</Link></td>
                        <td className={`py-3 px-3 font-semibold text-xs ${getSignalColor(r.signal)}`}>{r.signal}</td>
                        <td className="py-3 px-3 text-gray-300">{r.score}</td>
                        <td className="py-3 px-3 text-gray-300">₺{r.entry_price.toFixed(2)}</td>
                        <td className="py-3 px-3 text-gray-300">₺{r.exit_price.toFixed(2)}</td>
                        <td className={`py-3 px-3 font-bold ${r.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {r.profit_pct >= 0 ? '+' : ''}%{r.profit_pct.toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-gray-400">{r.days_held}</td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-1 rounded text-xs ${r.exit_reason === 'kar_al' ? 'bg-green-900/50 text-green-400' : r.exit_reason === 'zarar_kes' ? 'bg-red-900/50 text-red-400' : 'bg-yellow-900/50 text-yellow-400'}`}>
                            {r.exit_reason === 'kar_al' ? '✓ Kar Al' : r.exit_reason === 'zarar_kes' ? '✗ Stop' : '⏱ Süre'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── SYMBOLS TAB ── */}
        {activeTab === 'symbols' && (
          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4">🏆 Hisse Bazlı Performans</h2>
            {symbolBreakdown.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz veri yok.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-400 border-b border-gray-700">
                      {['Sıra', 'Hisse', 'İşlem', 'Kazanma %', 'Ort. K/Z', 'Top. K/Z', 'En İyi', 'En Kötü', 'Ort. Gün'].map(h => (
                        <th key={h} className="py-3 px-3 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {symbolBreakdown.map((s, i) => (
                      <tr key={s.symbol} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                        <td className="py-3 px-3 text-gray-500">{i + 1}</td>
                        <td className="py-3 px-3"><Link href={`/stock/${s.symbol}`} className="text-blue-400 hover:underline font-semibold">{s.symbol}</Link></td>
                        <td className="py-3 px-3 text-gray-300">{s.total_trades} ({s.win_count}✓)</td>
                        <td className="py-3 px-3">
                          <span className={`font-semibold ${s.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>%{fmt(s.win_rate)}</span>
                        </td>
                        <td className={`py-3 px-3 font-bold ${s.avg_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {s.avg_profit >= 0 ? '+' : ''}%{fmt(s.avg_profit, 2)}
                        </td>
                        <td className={`py-3 px-3 font-bold ${s.total_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {s.total_profit >= 0 ? '+' : ''}%{fmt(s.total_profit, 1)}
                        </td>
                        <td className="py-3 px-3 text-green-400">+%{fmt(s.best_trade, 1)}</td>
                        <td className="py-3 px-3 text-red-400">%{fmt(s.worst_trade, 1)}</td>
                        <td className="py-3 px-3 text-gray-400">{fmt(s.avg_days, 0)}g</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── HISTORICAL TAB ── */}
        {activeTab === 'historical' && (
          <div className="space-y-5">
            <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
              <h2 className="text-lg font-semibold mb-2">🔬 Geçmiş Veri Backtest</h2>
              <p className="text-gray-400 text-sm mb-4">
                Belirtilen hisse için sistemin teknik analizini geçmiş verilere uygulayarak strateji performansını ölçer.
              </p>
              <div className="flex gap-3 flex-wrap items-end">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Hisse Kodu</label>
                  <input
                    value={historicalSymbol}
                    onChange={e => setHistoricalSymbol(e.target.value.toUpperCase())}
                    className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white w-28 text-sm focus:outline-none focus:border-blue-500"
                    placeholder="ASELS"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Dönem</label>
                  <select
                    value={historicalPeriod}
                    onChange={e => setHistoricalPeriod(e.target.value)}
                    className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  >
                    <option value="3ay">3 Ay</option>
                    <option value="6ay">6 Ay</option>
                    <option value="1y">1 Yıl</option>
                    <option value="2y">2 Yıl</option>
                  </select>
                </div>
                <button
                  onClick={runHistorical}
                  disabled={historicalLoading}
                  className={`px-5 py-2 rounded-lg text-sm font-medium ${historicalLoading ? 'bg-yellow-600 cursor-wait' : 'bg-blue-600 hover:bg-blue-700'}`}
                >
                  {historicalLoading ? '⏳ Hesaplanıyor...' : '▶ Test Çalıştır'}
                </button>
              </div>
            </div>

            {historicalResult && (
              historicalResult.error ? (
                <div className="bg-red-900/30 rounded-xl p-5 border border-red-700">
                  <p className="text-red-400">⚠️ {historicalResult.error}</p>
                </div>
              ) : (
                <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                  <h3 className="text-lg font-semibold mb-4">
                    📊 {historicalResult.symbol} — {historicalResult.period} Sonuçları
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                    {[
                      { label: 'Toplam İşlem', value: String(historicalResult.total_trades), color: 'text-blue-400' },
                      { label: 'Kazanma Oranı', value: `%${fmt(historicalResult.win_rate)}`, color: historicalResult.win_rate >= 50 ? 'text-green-400' : 'text-red-400' },
                      { label: 'Top. Getiri', value: `%${fmt(historicalResult.total_profit, 1)}`, color: historicalResult.total_profit >= 0 ? 'text-green-400' : 'text-red-400' },
                      { label: 'Ort. Getiri', value: `%${fmt(historicalResult.avg_profit, 2)}`, color: historicalResult.avg_profit >= 0 ? 'text-green-400' : 'text-red-400' },
                      { label: 'Kazanan', value: String(historicalResult.winning_trades), color: 'text-green-400' },
                      { label: 'Kaybeden', value: String(historicalResult.total_trades - historicalResult.winning_trades), color: 'text-red-400' },
                      { label: 'En İyi İşlem', value: `+%${fmt(historicalResult.best_trade, 1)}`, color: 'text-green-400' },
                      { label: 'En Kötü İşlem', value: `%${fmt(historicalResult.worst_trade, 1)}`, color: 'text-red-400' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="bg-gray-700/50 rounded-lg p-3 text-center">
                        <p className="text-gray-400 text-xs mb-1">{label}</p>
                        <p className={`text-xl font-bold ${color}`}>{value}</p>
                      </div>
                    ))}
                  </div>
                  {historicalResult.trades && historicalResult.trades.length > 0 && (
                    <>
                      <h4 className="text-sm font-semibold text-gray-300 mb-2">Son {historicalResult.trades.length} İşlem</h4>
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-gray-500 border-b border-gray-700">
                              {['#', 'Giriş', 'Çıkış', 'K/Z', 'Gün', 'Skor'].map(h => (
                                <th key={h} className="py-2 px-2 text-left">{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {historicalResult.trades.map((t, i) => (
                              <tr key={i} className="border-b border-gray-700/50">
                                <td className="py-2 px-2 text-gray-500">{i + 1}</td>
                                <td className="py-2 px-2">₺{t.entry_price.toFixed(2)}</td>
                                <td className="py-2 px-2">₺{t.exit_price.toFixed(2)}</td>
                                <td className={`py-2 px-2 font-bold ${t.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                  {t.profit_pct >= 0 ? '+' : ''}%{t.profit_pct.toFixed(2)}
                                </td>
                                <td className="py-2 px-2 text-gray-400">{t.days_held}</td>
                                <td className="py-2 px-2 text-gray-400">{t.score}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              )
            )}
          </div>
        )}

      </div>
    </div>
  );
}
