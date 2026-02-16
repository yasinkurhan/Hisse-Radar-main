'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface PerformanceStats {
  total_signals: number;
  win_rate: number;
  avg_profit: number;
  avg_win: number;
  avg_loss: number;
  al_win_rate: number;
  sat_win_rate: number;
  high_score_win_rate: number;
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

interface MarketCondition {
  condition: string;
  trend: string;
  volatility: string;
  recommendation: string;
  details: {
    rsi: number;
    trend_direction: string;
    above_sma20: boolean;
    above_sma50: boolean;
  };
}

export default function BacktestPage() {
  const [performance, setPerformance] = useState<PerformanceStats | null>(null);
  const [activeSignals, setActiveSignals] = useState<ActiveSignal[]>([]);
  const [recentResults, setRecentResults] = useState<CompletedSignal[]>([]);
  const [marketCondition, setMarketCondition] = useState<MarketCondition | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'active' | 'history'>('overview');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);

    // Default market condition
    const defaultMarket: MarketCondition = {
      condition: 'neutral',
      trend: 'Yatay',
      volatility: 'Normal',
      recommendation: 'Piyasa verisi yükleniyor...',
      details: { rsi: 50, trend_direction: 'neutral', above_sma20: false, above_sma50: false }
    };

    try {
      // Fetch each endpoint with individual error handling
      const fetchWithTimeout = async (url: string, timeoutMs = 10000) => {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), timeoutMs);
        try {
          const res = await fetch(url, { signal: controller.signal });
          clearTimeout(timeout);
          return res.ok ? await res.json() : null;
        } catch {
          clearTimeout(timeout);
          return null;
        }
      };

      const [perfData, activeData, recentData, marketData] = await Promise.all([
        fetchWithTimeout('/api/backtest/performance'),
        fetchWithTimeout('/api/backtest/active-signals'),
        fetchWithTimeout('/api/backtest/recent-results?limit=20'),
        fetchWithTimeout('/api/backtest/market-condition', 15000)
      ]);

      if (perfData) setPerformance(perfData);
      if (activeData) setActiveSignals(activeData);
      if (recentData) setRecentResults(recentData);
      setMarketCondition(marketData || defaultMarket);
      setLastRefresh(new Date().toLocaleTimeString('tr-TR'));
    } catch (error) {
      console.error('Veri yuklenemedi:', error);
      setMarketCondition(defaultMarket);
    } finally {
      setLoading(false);
    }
  };

  const refreshSignals = async () => {
    setRefreshing(true);
    try {
      // Önce sinyalleri güncelle
      const refreshRes = await fetch('http://localhost:8000/api/backtest/refresh');
      const refreshData = await refreshRes.json();
      console.log('Refresh sonucu:', refreshData);

      // Sonra tüm verileri tekrar çek
      await fetchAllData();
    } catch (error) {
      console.error('Yenileme hatası:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getSignalColor = (signal: string) => {
    if (signal.includes('AL')) return 'text-green-400';
    if (signal.includes('SAT')) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getResultColor = (result: string) => {
    return result === 'success' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400';
  };

  const getConditionColor = (condition: string) => {
    switch (condition) {
      case 'bullish': return 'text-green-400';
      case 'bearish': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Backtest verileri yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">📊 Backtest & Performans</h1>
            <p className="text-gray-400 mt-1">Geçmiş sinyallerin başarı analizi</p>
            {lastRefresh && (
              <p className="text-gray-500 text-sm mt-1">Son güncelleme: {lastRefresh}</p>
            )}
          </div>
          <div className="flex gap-4">
            <button
              onClick={refreshSignals}
              disabled={refreshing}
              className={`px-4 py-2 rounded flex items-center gap-2 ${refreshing
                  ? 'bg-yellow-600 cursor-wait'
                  : 'bg-green-600 hover:bg-green-700'
                }`}
            >
              <span className={refreshing ? 'animate-spin' : ''}>🔄</span>
              {refreshing ? 'Güncelleniyor...' : 'Sinyalleri Güncelle'}
            </button>
            <button onClick={fetchAllData} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
              📥 Verileri Çek
            </button>
            <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded">
              Ana Sayfa
            </Link>
          </div>
        </div>

        {/* Market Condition Card */}
        {marketCondition && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">🌍 Piyasa Durumu (BIST100)</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-700 rounded p-4">
                <p className="text-gray-400 text-sm">Genel Durum</p>
                <p className={`text-2xl font-bold ${getConditionColor(marketCondition.condition)}`}>
                  {marketCondition.condition === 'bullish' ? '🐂 Boğa' :
                    marketCondition.condition === 'bearish' ? '🐻 Ayı' : '➡️ Yatay'}
                </p>
              </div>
              <div className="bg-gray-700 rounded p-4">
                <p className="text-gray-400 text-sm">Trend</p>
                <p className="text-xl font-semibold">{marketCondition.trend}</p>
              </div>
              <div className="bg-gray-700 rounded p-4">
                <p className="text-gray-400 text-sm">Volatilite</p>
                <p className="text-xl font-semibold">{marketCondition.volatility}</p>
              </div>
              <div className="bg-gray-700 rounded p-4">
                <p className="text-gray-400 text-sm">RSI</p>
                <p className="text-xl font-semibold">{marketCondition.details?.rsi?.toFixed(1) || 'N/A'}</p>
              </div>
            </div>
            <div className="mt-4 p-3 bg-blue-900/30 rounded">
              <p className="text-blue-300">💡 {marketCondition.recommendation}</p>
            </div>
          </div>
        )}

        {/* Performance Overview */}
        {performance && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">📈 Performans Özeti</h2>
            {performance.total_signals ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <p className="text-gray-400 text-sm">Toplam Sinyal</p>
                    <p className="text-3xl font-bold text-blue-400">{performance.total_signals || 0}</p>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <p className="text-gray-400 text-sm">Kazanma Oranı</p>
                    <p className={`text-3xl font-bold ${(performance.win_rate || 0) >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                      %{(performance.win_rate || 0).toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <p className="text-gray-400 text-sm">Ort. Kar</p>
                    <p className={`text-3xl font-bold ${(performance.avg_profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      %{(performance.avg_profit || 0).toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <p className="text-gray-400 text-sm">Ort. Kazanç</p>
                    <p className="text-3xl font-bold text-green-400">%{(performance.avg_win || 0).toFixed(2)}</p>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <p className="text-gray-400 text-sm">Ort. Kayıp</p>
                    <p className="text-3xl font-bold text-red-400">%{(performance.avg_loss || 0).toFixed(2)}</p>
                  </div>
                  <div className="bg-gray-700 rounded p-4 text-center">
                    <p className="text-gray-400 text-sm">Yüksek Skor K.O.</p>
                    <p className={`text-3xl font-bold ${(performance.high_score_win_rate || 0) >= 50 ? 'text-green-400' : 'text-yellow-400'}`}>
                      %{(performance.high_score_win_rate || 0).toFixed(1)}
                    </p>
                  </div>
                </div>

                {/* AL/SAT Win Rates */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div className="bg-green-900/30 rounded p-4">
                    <p className="text-green-300 text-sm">🟢 AL Sinyalleri Başarı Oranı</p>
                    <p className="text-2xl font-bold text-green-400">%{(performance.al_win_rate || 0).toFixed(1)}</p>
                  </div>
                  <div className="bg-blue-900/30 rounded p-4">
                    <p className="text-blue-300 text-sm">📅 Son Güncelleme</p>
                    <p className="text-xl font-bold text-blue-400">{performance.last_updated || '-'}</p>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <p className="text-lg">Henüz backtest verisi yok</p>
                <p className="text-sm mt-2">Analiz yaparak sinyaller oluşturun, performans otomatik takip edilecek.</p>
              </div>
            )}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('active')}
            className={`px-6 py-2 rounded ${activeTab === 'active' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            Aktif Sinyaller ({activeSignals.length})
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-6 py-2 rounded ${activeTab === 'history' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            Geçmiş ({recentResults.length})
          </button>
        </div>

        {/* Active Signals */}
        {activeTab === 'active' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">🎯 Aktif Sinyaller ({activeSignals.length} adet)</h2>
            {activeSignals.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz aktif sinyal yok. Analiz yaparak sinyal oluşturun.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-gray-400 text-left border-b border-gray-700">
                      <th className="py-3 px-4">Hisse</th>
                      <th className="py-3 px-4">Sinyal</th>
                      <th className="py-3 px-4">Skor</th>
                      <th className="py-3 px-4">Giriş Fiyatı</th>
                      <th className="py-3 px-4">Giriş Tarihi</th>
                      <th className="py-3 px-4">Durum</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeSignals.map((signal, idx) => (
                      <tr key={idx} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="py-3 px-4">
                          <Link href={`/stocks/${signal.symbol}`} className="text-blue-400 hover:underline font-semibold">
                            {signal.symbol}
                          </Link>
                        </td>
                        <td className={`py-3 px-4 font-semibold ${getSignalColor(signal.signal)}`}>
                          {signal.signal}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-sm ${signal.score >= 75 ? 'bg-green-900/50 text-green-400' : 'bg-yellow-900/50 text-yellow-400'}`}>
                            {signal.score}
                          </span>
                        </td>
                        <td className="py-3 px-4">₺{signal.entry_price.toFixed(2)}</td>
                        <td className="py-3 px-4 text-gray-400">{signal.date}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-1 rounded text-sm bg-blue-900/50 text-blue-400">
                            🔄 Aktif
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

        {/* History */}
        {activeTab === 'history' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">📜 Sinyal Geçmişi</h2>
            {recentResults.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz sonuçlanan sinyal yok.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-gray-400 text-left border-b border-gray-700">
                      <th className="py-3 px-4">Hisse</th>
                      <th className="py-3 px-4">Sinyal</th>
                      <th className="py-3 px-4">Skor</th>
                      <th className="py-3 px-4">Giriş</th>
                      <th className="py-3 px-4">Çıkış</th>
                      <th className="py-3 px-4">Kar/Zarar</th>
                      <th className="py-3 px-4">Gün</th>
                      <th className="py-3 px-4">Sonuç</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentResults.map((result, idx) => (
                      <tr key={idx} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="py-3 px-4">
                          <Link href={`/stocks/${result.symbol}`} className="text-blue-400 hover:underline font-semibold">
                            {result.symbol}
                          </Link>
                        </td>
                        <td className={`py-3 px-4 font-semibold ${getSignalColor(result.signal)}`}>
                          {result.signal}
                        </td>
                        <td className="py-3 px-4">{result.score}</td>
                        <td className="py-3 px-4">₺{result.entry_price.toFixed(2)}</td>
                        <td className="py-3 px-4">₺{result.exit_price.toFixed(2)}</td>
                        <td className={`py-3 px-4 font-bold ${result.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {result.profit_pct >= 0 ? '+' : ''}%{result.profit_pct.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-gray-400">{result.days_held}</td>
                        <td className="py-3 px-4">
                          <span className={`px-3 py-1 rounded text-sm ${result.exit_reason === 'kar_al'
                              ? 'bg-green-900/50 text-green-400'
                              : result.exit_reason === 'zarar_kes'
                                ? 'bg-red-900/50 text-red-400'
                                : 'bg-yellow-900/50 text-yellow-400'
                            }`}>
                            {result.exit_reason === 'kar_al' ? '✓ Kar Al' :
                              result.exit_reason === 'zarar_kes' ? '✗ Stop' :
                                '⏱ Süre Aşımı'}
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
      </div>
    </div>
  );
}
