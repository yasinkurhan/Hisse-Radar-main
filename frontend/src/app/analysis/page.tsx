'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Filter, RefreshCw, BarChart3, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import AdvancedFilterPanel, { FilterState, defaultFilters } from '@/components/AdvancedFilterPanel';

// API Base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const STORAGE_KEY_DAILY = 'hisseradar_analysis_daily';
const STORAGE_KEY_WEEKLY = 'hisseradar_analysis_weekly';
const STORAGE_TAB_KEY = 'hisseradar_analysis_tab';
const STORAGE_FILTERS_KEY = 'hisseradar_filters';

interface StockAnalysis {
  symbol: string;
  name: string;
  sector: string;
  current_price: number;
  change_percent: number;
  volume: number;
  avg_volume: number;
  volume_ratio: number;
  score: number;
  signal: string;
  signal_strength: string;
  indicators: {
    rsi: number;
    rsi_signal: string;
    macd: number;
    macd_signal_line: number;
    macd_histogram: number;
    macd_signal: string;
    bb_position: number;
    bb_signal: string;
    ma_trend: string;
    stochastic_k: number;
    stochastic_d: number;
    stoch_signal: string;
    atr: number;
    atr_percent: number;
  };
  sentiment?: {
    score: number;
    label: string;
    signal: string;
    news_count: number;
    positive_news: number;
    negative_news: number;
    has_data: boolean;
  };
  potential: {
    target_percent: number;
    stop_loss_percent: number;
    risk_reward_ratio: number;
    target_price: number;
    stop_loss_price: number;
    potential_profit: number;
    potential_loss: number;
  };
  reasons: string[];
  tags?: string[];
}

interface AnalysisResult {
  analysis_type: string;
  analysis_date: string;
  total_analyzed: number;
  buy_signals: number;
  sell_signals: number;
  strong_buy_count: number;
  market_summary: {
    bullish_percent: number;
    bearish_percent: number;
    neutral_percent: number;
    market_sentiment: string;
    avg_rsi: number;
    oversold_count: number;
    overbought_count: number;
    avg_sentiment?: number;
    positive_sentiment_stocks?: number;
    negative_sentiment_stocks?: number;
  };
  top_picks: StockAnalysis[];
  all_results: StockAnalysis[];
}

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

export default function AnalysisPage() {
  const [activeTab, setActiveTab] = useState<'daily' | 'weekly'>('daily');
  const [isLoading, setsLoading] = useState(false);
  const [dailyResult, setDailyResult] = useState<AnalysisResult | null>(null);
  const [weeklyResult, setWeeklyResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [indexFilter, setndexFilter] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);
  const [showAllResults, setShowAllResults] = useState(false);
  const [sortBy, setSortBy] = useState<'score' | 'change' | 'volume' | 'rsi' | 'target'>('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [performanceStats, setPerformanceStats] = useState<PerformanceStats | null>(null);

  // Aktif sekmeye göre result
  const result = activeTab === 'daily' ? dailyResult : weeklyResult;
  const setResult = activeTab === 'daily' ? setDailyResult : setWeeklyResult;

  // Gelimi filtreleme
  const [isFilterPanelOpen, setsFilterPanelOpen] = useState(false);
  const [advancedFilters, setAdvancedFilters] = useState<FilterState>(defaultFilters);
  const [activeFilterCount, setActiveFilterCount] = useState(0);

  // Sayfa yklendiinde localStorage'dan sonular al
  useEffect(() => {
    try {
      const savedDailyResult = localStorage.getItem(STORAGE_KEY_DAILY);
      const savedWeeklyResult = localStorage.getItem(STORAGE_KEY_WEEKLY);
      const savedTab = localStorage.getItem(STORAGE_TAB_KEY);
      const savedFilters = localStorage.getItem(STORAGE_FILTERS_KEY);

      if (savedDailyResult) {
        setDailyResult(JSON.parse(savedDailyResult));
      }
      if (savedWeeklyResult) {
        setWeeklyResult(JSON.parse(savedWeeklyResult));
      }
      if (savedTab) {
        setActiveTab(savedTab as 'daily' | 'weekly');
      }
      if (savedFilters) {
        setAdvancedFilters(JSON.parse(savedFilters));
      }
    } catch (e) {
      console.error('localStorage okuma hatas:', e);
    }

    // Performans istatistiklerini yükle (retry ile)
    const fetchPerformance = async (attempt = 0) => {
      try {
        const res = await fetch(`http://localhost:8001/api/backtest/performance`);
        const data = await res.json();
        if (data && Object.keys(data).length > 0) {
          setPerformanceStats(data);
        }
      } catch (e) {
        if (attempt < 3) {
          setTimeout(() => fetchPerformance(attempt + 1), 2000);
        }
      }
    };
    fetchPerformance();
  }, []);

  // Sonular deitiinde localStorage'a kaydet
  useEffect(() => {
    if (dailyResult) {
      try {
        localStorage.setItem(STORAGE_KEY_DAILY, JSON.stringify(dailyResult));
      } catch (e) {
        console.error('localStorage yazma hatas:', e);
      }
    }
  }, [dailyResult]);

  useEffect(() => {
    if (weeklyResult) {
      try {
        localStorage.setItem(STORAGE_KEY_WEEKLY, JSON.stringify(weeklyResult));
      } catch (e) {
        console.error('localStorage yazma hatas:', e);
      }
    }
  }, [weeklyResult]);

  useEffect(() => {
    localStorage.setItem(STORAGE_TAB_KEY, activeTab);
  }, [activeTab]);

  // Aktif filtre saysn hesapla
  useEffect(() => {
    let count = 0;
    if (advancedFilters.indices.length > 0) count++;
    if (advancedFilters.sectors.length > 0) count++;
    if (advancedFilters.signals.length > 0) count++;
    if (advancedFilters.minPrice !== null || advancedFilters.maxPrice !== null) count++;
    if (advancedFilters.rsiMin !== null || advancedFilters.rsiMax !== null) count++;
    if (advancedFilters.macdSignal !== null) count++;
    if (advancedFilters.maTrend !== null) count++;
    if (advancedFilters.minScore !== null) count++;
    if (advancedFilters.minTargetPercent !== null || advancedFilters.minRiskReward !== null) count++;
    if (advancedFilters.volumeRatioMin !== null) count++;
    setActiveFilterCount(count);

    // Filtreleri kaydet
    localStorage.setItem(STORAGE_FILTERS_KEY, JSON.stringify(advancedFilters));
  }, [advancedFilters]);

  // Filtrelenmi sonular
  const filteredResults = useMemo(() => {
    if (!result) return [];

    let filtered = [...result.all_results];

    // Endeks filtresi
    if (advancedFilters.indices.length > 0) {
      filtered = filtered.filter(stock => {
        const tags = stock.tags || [];
        return advancedFilters.indices.some(idx => tags.includes(idx));
      });
    }

    // Sektr filtresi
    if (advancedFilters.sectors.length > 0) {
      filtered = filtered.filter(stock =>
        advancedFilters.sectors.includes(stock.sector)
      );
    }

    // Sinyal filtresi
    if (advancedFilters.signals.length > 0) {
      filtered = filtered.filter(stock =>
        advancedFilters.signals.includes(stock.signal)
      );
    }

    // Fiyat filtresi
    if (advancedFilters.minPrice !== null) {
      filtered = filtered.filter(stock => stock.current_price >= advancedFilters.minPrice!);
    }
    if (advancedFilters.maxPrice !== null) {
      filtered = filtered.filter(stock => stock.current_price <= advancedFilters.maxPrice!);
    }

    // RS filtresi
    if (advancedFilters.rsiMin !== null) {
      filtered = filtered.filter(stock => stock.indicators.rsi >= advancedFilters.rsiMin!);
    }
    if (advancedFilters.rsiMax !== null) {
      filtered = filtered.filter(stock => stock.indicators.rsi <= advancedFilters.rsiMax!);
    }

    // MACD sinyal filtresi
    if (advancedFilters.macdSignal) {
      filtered = filtered.filter(stock => {
        const isBullish = stock.indicators.macd_histogram > 0;
        return advancedFilters.macdSignal === 'bullish' ? isBullish : !isBullish;
      });
    }

    // MA trend filtresi
    if (advancedFilters.maTrend) {
      filtered = filtered.filter(stock => {
        const trend = stock.indicators.ma_trend?.toLowerCase() || '';
        if (advancedFilters.maTrend === 'bullish') {
          return trend.includes('yukar') || trend.includes('yukari') || trend.includes('bullish');
        }
        return trend.includes('aa') || trend.includes('asagi') || trend.includes('bearish');
      });
    }

    // Skor filtresi
    if (advancedFilters.minScore !== null) {
      filtered = filtered.filter(stock => stock.score >= advancedFilters.minScore!);
    }
    if (advancedFilters.maxScore !== null) {
      filtered = filtered.filter(stock => stock.score <= advancedFilters.maxScore!);
    }

    // Hedef yzde filtresi
    if (advancedFilters.minTargetPercent !== null) {
      filtered = filtered.filter(stock =>
        stock.potential.target_percent >= advancedFilters.minTargetPercent!
      );
    }

    // Risk/Getiri filtresi
    if (advancedFilters.minRiskReward !== null) {
      filtered = filtered.filter(stock =>
        stock.potential.risk_reward_ratio >= advancedFilters.minRiskReward!
      );
    }

    // Hacim oran filtresi
    if (advancedFilters.volumeRatioMin !== null) {
      filtered = filtered.filter(stock =>
        stock.volume_ratio >= advancedFilters.volumeRatioMin!
      );
    }

    // Sralama
    filtered.sort((a, b) => {
      let aVal = 0, bVal = 0;
      switch (sortBy) {
        case 'score':
          aVal = a.score;
          bVal = b.score;
          break;
        case 'change':
          aVal = a.change_percent;
          bVal = b.change_percent;
          break;
        case 'volume':
          aVal = a.volume_ratio;
          bVal = b.volume_ratio;
          break;
        case 'rsi':
          aVal = a.indicators.rsi;
          bVal = b.indicators.rsi;
          break;
        case 'target':
          aVal = a.potential.target_percent;
          bVal = b.potential.target_percent;
          break;
      }
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    return filtered;
  }, [result, advancedFilters, sortBy, sortOrder]);

  const runAnalysis = async () => {
    setsLoading(true);
    setError(null);

    try {
      const endpoint = activeTab === 'daily' ? 'daily' : 'weekly';
      const params = new URLSearchParams();
      if (indexFilter) params.append('index_filter', indexFilter);
      params.append('limit', limit.toString());

      const response = await fetch(
        `${API_BASE}/api/analysis/${endpoint}?${params.toString()}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('Analiz yaplrken bir hata olutu');
      }

      const data = await response.json();
      // Aktif sekmeye göre doğru state'e kaydet
      if (activeTab === 'daily') {
        setDailyResult(data);
      } else {
        setWeeklyResult(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen bir hata olutu');
    } finally {
      setsLoading(false);
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'GUCLU_AL': return 'bg-green-600 text-white';
      case 'AL': return 'bg-green-500 text-white';
      case 'TUT': return 'bg-yellow-500 text-white';
      case 'SAT': return 'bg-red-500 text-white';
      case 'GUCLU_SAT': return 'bg-red-700 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getSignalText = (signal: string) => {
    switch (signal) {
      case 'GUCLU_AL': return 'GÜÇLÜ AL';
      case 'AL': return 'AL';
      case 'TUT': return 'TUT';
      case 'SAT': return 'SAT';
      case 'GUCLU_SAT': return 'GÜÇLÜ SAT';
      default: return signal;
    }
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    return num?.toFixed(decimals) ?? '-';
  };

  const formatCurrency = (num: number) => {
    return num?.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? '-';
  };

  const toggleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-lg sm:text-xl font-bold"></span>
              </div>
              <span className="text-lg sm:text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                HisseRadar
              </span>
            </Link>
            <nav className="hidden sm:flex space-x-2">
              <Link href="/" className="px-3 py-2 rounded-lg hover:bg-gray-700 transition text-sm">Ana Sayfa</Link>
              <Link href="/heatmap" className="px-3 py-2 rounded-lg hover:bg-gray-700 transition text-sm">Isı Haritası</Link>
              <Link href="/compare" className="px-3 py-2 rounded-lg hover:bg-gray-700 transition text-sm">Karşılaştır</Link>
              <Link href="/analysis" className="px-3 py-2 rounded-lg bg-blue-600 text-sm">Analiz</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* Analiz Kontrollar */}
        <div className="mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
            <h1 className="text-xl sm:text-2xl font-bold"> Otomatik Hisse Analizi</h1>

            {/* Gelimi Filtre Butonu */}
            <button
              onClick={() => setsFilterPanelOpen(true)}
              className={`flex items-center justify-center gap-2 px-3 sm:px-4 py-2 rounded-lg transition ${activeFilterCount > 0
                ? 'bg-blue-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
            >
              <Filter className="w-4 h-4" />
              <span className="text-sm sm:text-base">Gelişmiş Filtreler</span>
              {activeFilterCount > 0 && (
                <span className="px-1.5 py-0.5 bg-white/20 rounded text-xs">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>

          {/* Tab ve Temel Filtreler */}
          <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
            <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-3 sm:gap-4">
              {/* Analiz Tipi */}
              <div className="flex bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('daily')}
                  className={`flex-1 px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition ${activeTab === 'daily' ? 'bg-blue-500 text-white' : 'text-gray-300 hover:text-white'
                    }`}
                >
                  Günlük
                </button>
                <button
                  onClick={() => setActiveTab('weekly')}
                  className={`flex-1 px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition ${activeTab === 'weekly' ? 'bg-purple-500 text-white' : 'text-gray-300 hover:text-white'
                    }`}
                >
                  Haftalık
                </button>
              </div>

              {/* Endeks ve Limit */}
              <div className="flex gap-2 sm:gap-4">
                <select
                  value={indexFilter}
                  onChange={(e) => setndexFilter(e.target.value)}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-2 sm:px-3 py-2 text-sm"
                >
                  <option value="">Tüm Hisseler</option>
                  <option value="BIST30">BIST 30</option>
                  <option value="BIST100">BIST 100</option>
                  <option value="KATILIM">Katılım</option>
                </select>

                <select
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-2 sm:px-3 py-2 text-sm"
                >
                  <option value={50}>50 Hisse</option>
                  <option value={100}>100 Hisse</option>
                  <option value={200}>200 Hisse</option>
                  <option value={500}>500 Hisse</option>
                  <option value={0}>Tümü</option>
                </select>
              </div>

              {/* Analiz Baslat */}
              <button
                onClick={runAnalysis}
                disabled={isLoading}
                className={`w-full sm:w-auto flex items-center justify-center gap-2 px-4 sm:px-6 py-2.5 sm:py-2 rounded-lg font-medium transition ${isLoading
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700'
                  }`}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analiz Yapılıyor...</span>
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-4 h-4" />
                    <span>Analizi Başlat</span>
                  </>
                )}
              </button>
            </div>

            {/* Aktif Filtreler */}
            {activeFilterCount > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-700">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-gray-400 text-sm">Aktif filtreler:</span>
                  {advancedFilters.indices.length > 0 && (
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                      Endeks: {advancedFilters.indices.join(', ')}
                    </span>
                  )}
                  {advancedFilters.signals.length > 0 && (
                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">
                      Sinyal: {advancedFilters.signals.map(s => getSignalText(s)).join(', ')}
                    </span>
                  )}
                  {advancedFilters.minScore !== null && (
                    <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">
                      Min Skor: {advancedFilters.minScore}
                    </span>
                  )}
                  {(advancedFilters.rsiMin !== null || advancedFilters.rsiMax !== null) && (
                    <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs">
                      RS: {advancedFilters.rsiMin ?? 0} - {advancedFilters.rsiMax ?? 100}
                    </span>
                  )}
                  <button
                    onClick={() => setAdvancedFilters(defaultFilters)}
                    className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs hover:bg-red-500/30"
                  >
                    Temizle
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Hata Mesaj */}
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
            <p className="text-red-400"> {error}</p>
          </div>
        )}

        {/* Sonular */}
        {result && (
          <div className="space-y-4 sm:space-y-6">
            {/* zet Kartlar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 sm:gap-4">
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
                <p className="text-gray-400 text-xs sm:text-sm">Analiz Edilen</p>
                <p className="text-lg sm:text-2xl font-bold">{result.total_analyzed}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
                <p className="text-gray-400 text-xs sm:text-sm">Filtrelenmiş</p>
                <p className="text-lg sm:text-2xl font-bold text-blue-400">{filteredResults.length}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
                <p className="text-gray-400 text-xs sm:text-sm">Al Sinyali</p>
                <p className="text-lg sm:text-2xl font-bold text-green-400">{result.buy_signals}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
                <p className="text-gray-400 text-xs sm:text-sm">Güçlü Al</p>
                <p className="text-lg sm:text-2xl font-bold text-green-500">{result.strong_buy_count}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
                <p className="text-gray-400 text-xs sm:text-sm">Sat Sinyali</p>
                <p className="text-lg sm:text-2xl font-bold text-red-400">{result.sell_signals}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4">
                <p className="text-gray-400 text-xs sm:text-sm">Ort. RS</p>
                <p className="text-lg sm:text-2xl font-bold">{formatNumber(result.market_summary.avg_rsi, 0)}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-3 sm:p-4 border border-purple-500/30 col-span-2 sm:col-span-1">
                <p className="text-gray-400 text-xs sm:text-sm">Hedef Vadesi</p>
                <p className="text-lg sm:text-xl font-bold text-purple-400">
                  {activeTab === 'daily' ? '1 Gün' : '1 Hafta'}
                </p>
              </div>
            </div>

            {/* Piyasa Duygusu */}
            <div className="bg-gray-800 rounded-xl p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4"> Piyasa Duygusu</h3>
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <div className="flex-1">
                  <div className="flex h-4 rounded-full overflow-hidden">
                    <div
                      className="bg-green-500"
                      style={{ width: `${result.market_summary.bullish_percent}%` }}
                    />
                    <div
                      className="bg-yellow-500"
                      style={{ width: `${result.market_summary.neutral_percent}%` }}
                    />
                    <div
                      className="bg-red-500"
                      style={{ width: `${result.market_summary.bearish_percent}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-2 text-xs sm:text-sm">
                    <span className="text-green-400">Yükseliş: %{formatNumber(result.market_summary.bullish_percent, 0)}</span>
                    <span className="text-yellow-400">Nötr: %{formatNumber(result.market_summary.neutral_percent, 0)}</span>
                    <span className="text-red-400">Düşüş: %{formatNumber(result.market_summary.bearish_percent, 0)}</span>
                  </div>
                </div>
                <div className="text-center px-0 sm:px-6 pt-4 sm:pt-0 border-t sm:border-t-0 sm:border-l border-gray-700">
                  <p className="text-gray-400 text-xs sm:text-sm">Genel Durum</p>
                  <p className={`text-lg sm:text-xl font-bold ${result.market_summary.bullish_percent > 50 ? 'text-green-400' :
                    result.market_summary.bearish_percent > 50 ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                    {result.market_summary.market_sentiment}
                  </p>
                </div>
              </div>
            </div>

            {/* Haber Sentiment Özeti */}
            {result.market_summary.avg_sentiment !== null && result.market_summary.avg_sentiment !== undefined && (
              <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-xl p-4 sm:p-6 border border-purple-500/30">
                <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
                  📰 Haber Sentiment Analizi
                  <span className="text-xs text-gray-400 font-normal">(Top 30 hisse)</span>
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-4">
                  <div className="bg-gray-900/50 rounded-lg p-3 sm:p-4 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Ortalama Sentiment</p>
                    <p className={`text-lg sm:text-2xl font-bold ${result.market_summary.avg_sentiment > 0.1 ? 'text-green-400' :
                        result.market_summary.avg_sentiment < -0.1 ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                      {result.market_summary.avg_sentiment > 0.1 ? '📈 Olumlu' :
                        result.market_summary.avg_sentiment < -0.1 ? '📉 Olumsuz' : '➖ Nötr'}
                    </p>
                    <p className="text-[10px] sm:text-xs text-gray-500 mt-1">
                      Skor: {(result.market_summary.avg_sentiment * 100).toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-3 sm:p-4 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Olumlu Haberli</p>
                    <p className="text-lg sm:text-2xl font-bold text-green-400">
                      {result.market_summary.positive_sentiment_stocks || 0}
                    </p>
                    <p className="text-[10px] sm:text-xs text-gray-500 mt-1">hisse</p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-3 sm:p-4 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Olumsuz Haberli</p>
                    <p className="text-lg sm:text-2xl font-bold text-red-400">
                      {result.market_summary.negative_sentiment_stocks || 0}
                    </p>
                    <p className="text-[10px] sm:text-xs text-gray-500 mt-1">hisse</p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-3 sm:p-4 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Nötr Haberli</p>
                    <p className="text-lg sm:text-2xl font-bold text-gray-400">
                      {30 - (result.market_summary.positive_sentiment_stocks || 0) - (result.market_summary.negative_sentiment_stocks || 0)}
                    </p>
                    <p className="text-[10px] sm:text-xs text-gray-500 mt-1">hisse</p>
                  </div>
                </div>
                <p className="text-[10px] sm:text-xs text-gray-500 mt-2 sm:mt-3 text-center">
                  💡 Sentiment analizi Google News ve finans RSS kaynaklarından gerçek haberler kullanılarak hesaplanır
                </p>
              </div>
            )}

            {/* Sinyal Performans İstatistikleri */}
            {performanceStats && performanceStats.total_signals > 0 && (
              <div className="bg-gradient-to-r from-gray-800 to-gray-800/50 rounded-xl p-4 sm:p-6 border border-blue-500/20">
                <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
                  📊 Geçmiş Sinyal Performansı
                  <span className="text-xs text-gray-400 font-normal">({performanceStats.total_signals} sinyal)</span>
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-4">
                  <div className="bg-gray-900/50 rounded-lg p-2 sm:p-3 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Başarı Oranı</p>
                    <p className={`text-lg sm:text-2xl font-bold ${performanceStats.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                      %{performanceStats.win_rate}
                    </p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-2 sm:p-3 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Ort. Getiri</p>
                    <p className={`text-lg sm:text-2xl font-bold ${performanceStats.avg_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {performanceStats.avg_profit >= 0 ? '+' : ''}{performanceStats.avg_profit}%
                    </p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-2 sm:p-3 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">AL Başarısı</p>
                    <p className={`text-lg sm:text-2xl font-bold ${performanceStats.al_win_rate >= 50 ? 'text-green-400' : 'text-yellow-400'}`}>
                      %{performanceStats.al_win_rate}
                    </p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-2 sm:p-3 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">SAT Başarısı</p>
                    <p className={`text-lg sm:text-2xl font-bold ${performanceStats.sat_win_rate >= 50 ? 'text-green-400' : 'text-yellow-400'}`}>
                      %{performanceStats.sat_win_rate}
                    </p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-2 sm:p-3 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Yüksek Skor</p>
                    <p className={`text-lg sm:text-2xl font-bold ${performanceStats.high_score_win_rate >= 60 ? 'text-green-400' : 'text-yellow-400'}`}>
                      %{performanceStats.high_score_win_rate}
                    </p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-2 sm:p-3 text-center">
                    <p className="text-gray-400 text-[10px] sm:text-xs mb-1">Ort. Kazanç</p>
                    <p className="text-lg sm:text-2xl font-bold text-green-400">+{performanceStats.avg_win}%</p>
                  </div>
                </div>
                <p className="text-[10px] sm:text-xs text-gray-500 mt-2 sm:mt-3 text-right">
                  Son güncelleme: {performanceStats.last_updated}
                </p>
              </div>
            )}

            {/* Sonu Tablosu */}
            <div className="bg-gray-800 rounded-xl overflow-hidden">
              <div className="p-3 sm:p-4 border-b border-gray-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h3 className="text-base sm:text-lg font-semibold">
                  Analiz Sonuçları
                  <span className="text-gray-400 text-sm ml-2">({filteredResults.length} hisse)</span>
                </h3>
                <div className="flex items-center gap-2 text-xs sm:text-sm overflow-x-auto">
                  <span className="text-gray-400 hidden sm:inline">Sırala:</span>
                  {[
                    { key: 'score', label: 'Skor' },
                    { key: 'change', label: 'Değişim' },
                    { key: 'rsi', label: 'RS' },
                    { key: 'target', label: 'Hedef' },
                  ].map(item => (
                    <button
                      key={item.key}
                      onClick={() => toggleSort(item.key as typeof sortBy)}
                      className={`px-2 py-1 rounded whitespace-nowrap ${sortBy === item.key ? 'bg-blue-500 text-white' : 'bg-gray-700 text-gray-300'
                        }`}
                    >
                      {item.label}
                      {sortBy === item.key && (
                        sortOrder === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-1" /> : <ChevronUp className="w-3 h-3 inline ml-1" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Mobil Kart Görünümü */}
              <div className="block sm:hidden">
                {filteredResults.slice(0, showAllResults ? undefined : 20).map((stock, index) => (
                  <div key={stock.symbol} className="border-t border-gray-700/50 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 text-xs w-5">{index + 1}</span>
                        <Link href={`/stock/${stock.symbol}`} className="font-semibold text-white hover:text-blue-400">
                          {stock.symbol}
                        </Link>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${getSignalColor(stock.signal)}`}>
                          {getSignalText(stock.signal)}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(stock.current_price)} ₺</p>
                        <p className={`text-xs ${stock.change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {stock.change_percent >= 0 ? '+' : ''}{formatNumber(stock.change_percent)}%
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-xs text-center">
                      <div className="bg-gray-700/50 rounded p-1.5">
                        <p className="text-gray-400">Skor</p>
                        <p className="font-semibold">{stock.score}</p>
                      </div>
                      <div className="bg-gray-700/50 rounded p-1.5">
                        <p className="text-gray-400">RSI</p>
                        <p className={`font-semibold ${stock.indicators.rsi < 30 ? 'text-green-400' : stock.indicators.rsi > 70 ? 'text-red-400' : ''}`}>
                          {formatNumber(stock.indicators.rsi, 0)}
                        </p>
                      </div>
                      <div className="bg-gray-700/50 rounded p-1.5">
                        <p className="text-gray-400">Hedef</p>
                        <p className="font-semibold text-green-400">+{formatNumber(stock.potential.target_percent)}%</p>
                      </div>
                      <div className="bg-gray-700/50 rounded p-1.5">
                        <p className="text-gray-400">R/R</p>
                        <p className="font-semibold">{formatNumber(stock.potential.risk_reward_ratio, 1)}</p>
                      </div>
                    </div>
                    {stock.sentiment?.has_data && (
                      <div className="mt-2 text-xs text-center">
                        <span className={`px-2 py-0.5 rounded ${stock.sentiment.score > 0.2 ? 'bg-green-500/20 text-green-400' :
                            stock.sentiment.score < -0.2 ? 'bg-red-500/20 text-red-400' :
                              'bg-gray-500/20 text-gray-400'
                          }`}>
                          📰 {stock.sentiment.score > 0.2 ? 'Olumlu' : stock.sentiment.score < -0.2 ? 'Olumsuz' : 'Nötr'} ({stock.sentiment.news_count} haber)
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Desktop Tablo Görünümü */}
              <div className="overflow-x-auto hidden sm:block">
                <table className="w-full">
                  <thead className="bg-gray-700/50">
                    <tr className="text-gray-400 text-xs sm:text-sm">
                      <th className="text-left p-2 sm:p-3">Hisse</th>
                      <th className="text-right p-2 sm:p-3">Fiyat</th>
                      <th className="text-right p-2 sm:p-3">Değişim</th>
                      <th className="text-center p-2 sm:p-3">Sinyal</th>
                      <th className="text-center p-2 sm:p-3">Skor</th>
                      <th className="text-center p-2 sm:p-3 hidden lg:table-cell">Sentiment</th>
                      <th className="text-right p-2 sm:p-3">RSI</th>
                      <th className="text-right p-2 sm:p-3">Hedef %</th>
                      <th className="text-right p-2 sm:p-3 hidden md:table-cell">R/R</th>
                      <th className="text-center p-2 sm:p-3">Grafik</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredResults.slice(0, showAllResults ? undefined : 20).map((stock, index) => (
                      <tr
                        key={stock.symbol}
                        className="border-t border-gray-700/50 hover:bg-gray-700/30 transition"
                      >
                        <td className="p-2 sm:p-3">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500 text-xs sm:text-sm w-5 sm:w-6">{index + 1}</span>
                            <div>
                              <Link
                                href={`/stock/${stock.symbol}`}
                                className="font-semibold text-white hover:text-blue-400 text-sm"
                              >
                                {stock.symbol}
                              </Link>
                              <p className="text-gray-400 text-[10px] sm:text-xs truncate max-w-20 sm:max-w-32">{stock.name}</p>
                            </div>
                          </div>
                        </td>
                        <td className="p-2 sm:p-3 text-right font-medium text-sm">
                          {formatCurrency(stock.current_price)}
                        </td>
                        <td className={`p-2 sm:p-3 text-right font-medium text-sm ${stock.change_percent >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                          {stock.change_percent >= 0 ? '+' : ''}{formatNumber(stock.change_percent)}%
                        </td>
                        <td className="p-2 sm:p-3 text-center">
                          <span className={`px-1.5 sm:px-2 py-0.5 sm:py-1 rounded text-[10px] sm:text-xs font-medium ${getSignalColor(stock.signal)}`}>
                            {getSignalText(stock.signal)}
                          </span>
                        </td>
                        <td className="p-2 sm:p-3 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <div className="w-8 sm:w-12 h-2 bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${stock.score >= 70 ? 'bg-green-500' :
                                  stock.score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                style={{ width: `${stock.score}%` }}
                              />
                            </div>
                            <span className="text-xs sm:text-sm font-medium w-6 sm:w-8">{stock.score}</span>
                          </div>
                        </td>
                        <td className="p-2 sm:p-3 text-center hidden lg:table-cell">
                          {stock.sentiment?.has_data ? (
                            <div className="flex flex-col items-center">
                              <span className={`text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded ${stock.sentiment.score > 0.15 ? 'bg-green-500/20 text-green-400' :
                                  stock.sentiment.score < -0.15 ? 'bg-red-500/20 text-red-400' :
                                    'bg-gray-500/20 text-gray-400'
                                }`}>
                                {stock.sentiment.score > 0.15 ? '📈 Olumlu' :
                                  stock.sentiment.score < -0.15 ? '📉 Olumsuz' : '➖ Nötr'}
                              </span>
                              <span className="text-[10px] text-gray-500 mt-0.5">
                                {stock.sentiment.news_count} haber
                              </span>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-500">-</span>
                          )}
                        </td>
                        <td className={`p-2 sm:p-3 text-right text-sm ${stock.indicators.rsi < 30 ? 'text-green-400' :
                          stock.indicators.rsi > 70 ? 'text-red-400' : 'text-white'
                          }`}>
                          {formatNumber(stock.indicators.rsi, 0)}
                        </td>
                        <td className={`p-2 sm:p-3 text-right font-medium text-sm ${stock.potential.target_percent >= 10 ? 'text-green-400' : 'text-white'
                          }`}>
                          +{formatNumber(stock.potential.target_percent)}%
                        </td>
                        <td className={`p-2 sm:p-3 text-right text-sm hidden md:table-cell ${stock.potential.risk_reward_ratio >= 2 ? 'text-green-400' :
                          stock.potential.risk_reward_ratio >= 1.5 ? 'text-yellow-400' : 'text-gray-400'
                          }`}>
                          {formatNumber(stock.potential.risk_reward_ratio, 1)}
                        </td>
                        <td className="p-2 sm:p-3 text-center">
                          <Link
                            href={`/stock/${stock.symbol}`}
                            className="p-1 sm:p-1.5 bg-gray-700 hover:bg-gray-600 rounded transition inline-block"
                          >
                            <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {filteredResults.length > 20 && !showAllResults && (
                <div className="p-4 border-t border-gray-700 text-center">
                  <button
                    onClick={() => setShowAllResults(true)}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
                  >
                    Tümünü Göster ({filteredResults.length - 20} daha)
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analiz yaplmadysa */}
        {!result && !isLoading && !error && (
          <div className="bg-gray-800 rounded-xl p-12 text-center">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-600" />
            <h3 className="text-xl font-semibold mb-2">Analiz Başlatın</h3>
            <p className="text-gray-400 mb-6">
              BIST hisselerini teknik göstergelerle analiz ederek al/sat sinyalleri alın
            </p>
            <button
              onClick={runAnalysis}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg font-medium hover:from-blue-600 hover:to-purple-600 transition"
            >
              Analizi Baslat
            </button>
          </div>
        )}
      </main>

      {/* Gelimi Filtre Paneli */}
      <AdvancedFilterPanel
        isOpen={isFilterPanelOpen}
        onClose={() => setsFilterPanelOpen(false)}
        onApplyFilters={setAdvancedFilters}
        currentFilters={advancedFilters}
      />
    </div>
  );
}
