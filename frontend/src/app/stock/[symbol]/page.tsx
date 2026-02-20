'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { createChart, ColorType, IChartApi } from 'lightweight-charts';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { getOHLCData } from '@/lib/api';
import { ProAnalysisDashboard } from '@/components/pro';
import FundamentalCharts from '@/components/FundamentalCharts';
import FundamentalData from '@/components/FundamentalData';
import StockNews from '@/components/StockNews';
import ChartPatterns from '@/components/ChartPatterns';
import TechnicalIndicators from '@/components/TechnicalIndicators';
import ETFHolders from '@/components/ETFHolders';
import AnalystCard from '@/components/AnalystCard';
import TASignals from '@/components/TASignals';

interface StockInfo {
  symbol: string;
  name: string;
  sector: string;
  currentPrice: number;
  previousClose: number;
  change: number;
  changePercent: number;
  dayHigh: number;
  dayLow: number;
  volume: number;
  avgVolume: number;
  fiftyTwoWeekHigh: number;
  fiftyTwoWeekLow: number;
}

interface OHLCData {
  time: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface IndicatorData {
  time: number;
  value: number | null;
}

interface ChartData {
  success: boolean;
  info: StockInfo;
  ohlc: OHLCData[];
  indicators: any;
}

type TabType = 'chart' | 'pro' | 'fundamental' | 'analyst' | 'signals' | 'news' | 'patterns' | 'technical';

export default function StockDetailPage() {
  const params = useParams();
  const symbol = (params.symbol as string)?.toUpperCase();

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<HTMLDivElement>(null);
  const macdChartRef = useRef<HTMLDivElement>(null);
  const volumeChartRef = useRef<HTMLDivElement>(null);

  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('3mo');
  const [showBollinger, setShowBollinger] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('chart');
  const [showSMA, setShowSMA] = useState(true);
  const [showEMA, setShowEMA] = useState(false);

  const chartRef = useRef<IChartApi | null>(null);
  const rsiChartInstance = useRef<IChartApi | null>(null);
  const macdChartInstance = useRef<IChartApi | null>(null);
  const volumeChartInstance = useRef<IChartApi | null>(null);
  const isDisposedRef = useRef(false);
  // Guvenli chart temizleme
  const cleanupAllCharts = useCallback(() => {
    isDisposedRef.current = true;
    const refs = [chartRef, rsiChartInstance, macdChartInstance, volumeChartInstance];
    refs.forEach(ref => {
      if (ref.current) {
        try { ref.current.remove(); } catch (e) { }
        ref.current = null;
      }
    });
  }, []);

  // Veri cekme
  useEffect(() => {
    if (!symbol) return;
    let isCancelled = false;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getOHLCData(symbol, period, '1d');
        if (isCancelled) return;
        if (!data.success) throw new Error(data.error || 'Veri alinamadi');
        setStockInfo(data.info);
        setChartData(data);
      } catch (err: any) {
        if (!isCancelled) setError(err.message);
      } finally {
        if (!isCancelled) setLoading(false);
      }
    };
    fetchData();
    return () => { isCancelled = true; };
  }, [symbol, period]);

  // Chart olusturma
  useEffect(() => {
    if (!chartData || loading) return;
    cleanupAllCharts();
    isDisposedRef.current = false;

    const timer = setTimeout(() => {
      if (isDisposedRef.current || !chartData) return;

      // Ana mum grafigi
      if (chartContainerRef.current) {
        const chart = createChart(chartContainerRef.current, {
          layout: { background: { type: ColorType.Solid, color: '#ffffff' }, textColor: '#374151' },
          grid: { vertLines: { color: '#e5e7eb' }, horzLines: { color: '#e5e7eb' } },
          width: chartContainerRef.current.clientWidth,
          height: window.innerWidth < 640 ? 280 : 400,
          crosshair: { mode: 1 },
          timeScale: { borderColor: '#d1d5db', timeVisible: true },
          rightPriceScale: { borderColor: '#d1d5db' },
        });
        chartRef.current = chart;

        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#22c55e', downColor: '#ef4444',
          borderUpColor: '#16a34a', borderDownColor: '#dc2626',
          wickUpColor: '#22c55e', wickDownColor: '#ef4444',
        });
        const candleData = chartData.ohlc.map((d: OHLCData) => ({
          time: d.time as any, open: d.open, high: d.high, low: d.low, close: d.close,
        }));
        candlestickSeries.setData(candleData as any);

        // Bollinger Bands
        if (showBollinger && chartData.indicators?.bollinger) {
          const bbUpper = chart.addLineSeries({ color: 'rgba(99, 102, 241, 0.4)', lineWidth: 1 });
          const bbMiddle = chart.addLineSeries({ color: 'rgba(99, 102, 241, 0.6)', lineWidth: 1, lineStyle: 2 });
          const bbLower = chart.addLineSeries({ color: 'rgba(99, 102, 241, 0.4)', lineWidth: 1 });
          bbUpper.setData(chartData.indicators.bollinger.upper.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
          bbMiddle.setData(chartData.indicators.bollinger.middle.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
          bbLower.setData(chartData.indicators.bollinger.lower.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
        }

        // SMA
        if (showSMA && chartData.indicators?.sma20) {
          const sma20 = chart.addLineSeries({ color: '#f59e0b', lineWidth: 2 });
          const sma50 = chart.addLineSeries({ color: '#8b5cf6', lineWidth: 2 });
          sma20.setData(chartData.indicators.sma20.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
          if (chartData.indicators.sma50) {
            sma50.setData(chartData.indicators.sma50.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
          }
        }

        // EMA
        if (showEMA && chartData.indicators?.ema12) {
          const ema12 = chart.addLineSeries({ color: '#06b6d4', lineWidth: 1 });
          const ema26 = chart.addLineSeries({ color: '#ec4899', lineWidth: 1 });
          ema12.setData(chartData.indicators.ema12.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
          if (chartData.indicators.ema26) {
            ema26.setData(chartData.indicators.ema26.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
          }
        }
        chart.timeScale().fitContent();
      }
      // RSI Grafigi
      if (rsiChartRef.current && chartData.indicators?.rsi) {
        const rsiChart = createChart(rsiChartRef.current, {
          layout: { background: { type: ColorType.Solid, color: '#ffffff' }, textColor: '#374151' },
          grid: { vertLines: { color: '#e5e7eb' }, horzLines: { color: '#e5e7eb' } },
          width: rsiChartRef.current.clientWidth, height: 150,
          timeScale: { borderColor: '#d1d5db', visible: false },
          rightPriceScale: { borderColor: '#d1d5db' },
        });
        rsiChartInstance.current = rsiChart;
        const rsiSeries = rsiChart.addLineSeries({ color: '#f59e0b', lineWidth: 2 });
        rsiSeries.setData(chartData.indicators.rsi.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
        const rsiTimes = chartData.indicators.rsi.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => d.time);
        const rsi30 = rsiChart.addLineSeries({ color: 'rgba(34, 197, 94, 0.5)', lineWidth: 1, lineStyle: 2 });
        const rsi70 = rsiChart.addLineSeries({ color: 'rgba(239, 68, 68, 0.5)', lineWidth: 1, lineStyle: 2 });
        rsi30.setData(rsiTimes.map((t: number) => ({ time: t, value: 30 })));
        rsi70.setData(rsiTimes.map((t: number) => ({ time: t, value: 70 })));
        rsiChart.timeScale().fitContent();
      }

      // MACD Grafigi
      if (macdChartRef.current && chartData.indicators?.macd) {
        const macdChart = createChart(macdChartRef.current, {
          layout: { background: { type: ColorType.Solid, color: '#ffffff' }, textColor: '#374151' },
          grid: { vertLines: { color: '#e5e7eb' }, horzLines: { color: '#e5e7eb' } },
          width: macdChartRef.current.clientWidth, height: 150,
          timeScale: { borderColor: '#d1d5db', visible: false },
          rightPriceScale: { borderColor: '#d1d5db' },
        });
        macdChartInstance.current = macdChart;
        const macdLine = macdChart.addLineSeries({ color: '#3b82f6', lineWidth: 2 });
        const signalLine = macdChart.addLineSeries({ color: '#ef4444', lineWidth: 2 });
        const histogram = macdChart.addHistogramSeries({ color: '#22c55e' });
        macdLine.setData(chartData.indicators.macd.macd.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
        signalLine.setData(chartData.indicators.macd.signal.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value })));
        histogram.setData(chartData.indicators.macd.histogram.filter((d: IndicatorData) => d.value !== null).map((d: IndicatorData) => ({ time: d.time, value: d.value, color: d.value! >= 0 ? '#22c55e' : '#ef4444' })));
        macdChart.timeScale().fitContent();
      }

      // Volume Grafigi
      if (volumeChartRef.current && chartData.ohlc) {
        const volumeChart = createChart(volumeChartRef.current, {
          layout: { background: { type: ColorType.Solid, color: '#ffffff' }, textColor: '#374151' },
          grid: { vertLines: { color: '#e5e7eb' }, horzLines: { color: '#e5e7eb' } },
          width: volumeChartRef.current.clientWidth, height: 100,
          timeScale: { borderColor: '#d1d5db' },
          rightPriceScale: { borderColor: '#d1d5db' },
        });
        volumeChartInstance.current = volumeChart;
        const volumeSeries = volumeChart.addHistogramSeries({ color: '#6366f1' });
        volumeSeries.setData(
          chartData.ohlc.map((d: OHLCData, i: number) => ({
            time: d.time as any, value: d.volume,
            color: i > 0 && d.close >= chartData.ohlc[i - 1].close ? '#22c55e' : '#ef4444',
          })) as any
        );
        volumeChart.timeScale().fitContent();
      }
    }, 100);

    return () => { clearTimeout(timer); cleanupAllCharts(); };
  }, [chartData, loading, showBollinger, showSMA, showEMA, cleanupAllCharts]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (isDisposedRef.current) return;
      try {
        if (chartRef.current && chartContainerRef.current) chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        if (rsiChartInstance.current && rsiChartRef.current) rsiChartInstance.current.applyOptions({ width: rsiChartRef.current.clientWidth });
        if (macdChartInstance.current && macdChartRef.current) macdChartInstance.current.applyOptions({ width: macdChartRef.current.clientWidth });
        if (volumeChartInstance.current && volumeChartRef.current) volumeChartInstance.current.applyOptions({ width: volumeChartRef.current.clientWidth });
      } catch (e) { }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const formatNumber = (num: number) => new Intl.NumberFormat('tr-TR').format(num);
  const formatVolume = (num: number) => {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toString();
  };
  const getChangeIcon = (pct: number) => {
    if (pct > 0) return <TrendingUp className="w-5 h-5 text-green-600" />;
    if (pct < 0) return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <Minus className="w-5 h-5 text-gray-400" />;
  };
  const tabs = [
    { id: 'chart' as TabType, label: 'Grafik & Teknik', icon: '📊', activeClass: 'bg-blue-600 text-white shadow-md' },
    { id: 'pro' as TabType, label: 'PRO Analiz', icon: '⚡', activeClass: 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md' },
    { id: 'technical' as TabType, label: 'Teknik Analiz', icon: '📈', activeClass: 'bg-indigo-600 text-white shadow-md' },
    { id: 'fundamental' as TabType, label: 'Temel Analiz', icon: '🏢', activeClass: 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md' },
    { id: 'analyst' as TabType, label: 'Analist & ETF', icon: '🎯', activeClass: 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-md' },
    { id: 'signals' as TabType, label: 'Teknik Sinyaller', icon: '📡', activeClass: 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md' },
    { id: 'news' as TabType, label: 'Haberler', icon: '📰', activeClass: 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white shadow-md' },
    { id: 'patterns' as TabType, label: 'Formasyonlar', icon: '🔍', activeClass: 'bg-gradient-to-r from-pink-500 to-rose-500 text-white shadow-md' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Link href="/" className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="Geri don">
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </Link>
              <div>
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 font-bold rounded-lg text-lg">{symbol}</span>
                  <h1 className="text-xl font-bold text-gray-900">
                    {loading ? 'Yukleniyor...' : stockInfo?.name || symbol}
                  </h1>
                </div>
                {stockInfo?.sector && (
                  <p className="text-sm text-gray-500 mt-1 ml-1">{stockInfo.sector}</p>
                )}
              </div>
            </div>
            {stockInfo && (
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-2xl sm:text-3xl font-bold text-gray-900">
                    ₺{formatNumber(stockInfo.currentPrice)}
                  </div>
                  <div className="flex items-center justify-end gap-2 mt-1">
                    {getChangeIcon(stockInfo.changePercent)}
                    <span className={`font-semibold text-lg ${stockInfo.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {stockInfo.changePercent >= 0 ? '+' : ''}{stockInfo.change.toFixed(2)} ({stockInfo.changePercent.toFixed(2)}%)
                    </span>
                  </div>
                </div>
                <a href={`https://www.tradingview.com/chart/?symbol=BIST:${symbol}`} target="_blank" rel="noopener noreferrer"
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="TradingView'da ac">
                  <ExternalLink className="w-5 h-5 text-gray-500" />
                </a>
              </div>
            )}
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-600 font-medium">{error}</p>
            <Link href="/" className="text-blue-600 hover:underline mt-3 inline-block font-medium">Ana Sayfaya Don</Link>
          </div>
        ) : (
          <>
            {/* Hisse Detay Kartlari */}
            {stockInfo && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 sm:p-6 mb-4 sm:mb-6">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">Gunluk En Yuksek</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.dayHigh)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">Gunluk En Dusuk</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.dayLow)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">Hacim</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">{formatVolume(stockInfo.volume)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">Ort. Hacim</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">{formatVolume(stockInfo.avgVolume)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">52H En Yuksek</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.fiftyTwoWeekHigh)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">52H En Dusuk</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.fiftyTwoWeekLow)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">Onceki Kapanis</p>
                    <p className="text-gray-900 font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.previousClose)}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs sm:text-sm">Degisim</p>
                    <p className={`font-semibold text-sm sm:text-base ${stockInfo.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {stockInfo.changePercent >= 0 ? '+' : ''}{stockInfo.changePercent.toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
            )}
            {/* Tab Secimi */}
            <div className="flex gap-2 mb-4 sm:mb-6 overflow-x-auto pb-2 scrollbar-thin">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 sm:px-5 py-2.5 rounded-xl font-medium transition-all flex items-center gap-2 whitespace-nowrap text-sm sm:text-base ${
                    activeTab === tab.id
                      ? tab.activeClass
                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200 shadow-sm'
                  }`}
                >
                  <span>{tab.icon}</span> {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Icerikleri */}
            {activeTab === 'pro' ? (
              <ProAnalysisDashboard symbol={symbol} />
            ) : activeTab === 'fundamental' ? (
              <div className="space-y-6">
                <FundamentalData symbol={symbol} />
                <FundamentalCharts symbol={symbol} />
              </div>
            ) : activeTab === 'analyst' ? (
              <div className="space-y-6">
                <AnalystCard symbol={symbol} />
                <ETFHolders symbol={symbol} />
              </div>
            ) : activeTab === 'signals' ? (
              <div className="space-y-6">
                <TASignals symbol={symbol} />
              </div>
            ) : activeTab === 'news' ? (
              <StockNews symbol={symbol} />
            ) : activeTab === 'patterns' ? (
              <ChartPatterns symbol={symbol} period={period} />
            ) : activeTab === 'technical' ? (
              <TechnicalIndicators symbol={symbol} />
            ) : (
              <>
                {/* Periyod ve Gosterge Secimi */}
                <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 mb-4">
                  <div className="flex gap-1.5 sm:gap-2 overflow-x-auto">
                    {['1mo', '3mo', '6mo', '1y', '2y'].map((p) => (
                      <button
                        key={p}
                        onClick={() => setPeriod(p)}
                        className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${
                          period === p
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                        }`}
                      >
                        {p.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-1.5 sm:gap-2 sm:ml-auto overflow-x-auto">
                    <button
                      onClick={() => setShowBollinger(!showBollinger)}
                      className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${
                        showBollinger ? 'bg-purple-600 text-white shadow-sm' : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      Bollinger
                    </button>
                    <button
                      onClick={() => setShowSMA(!showSMA)}
                      className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${
                        showSMA ? 'bg-amber-500 text-white shadow-sm' : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      SMA
                    </button>
                    <button
                      onClick={() => setShowEMA(!showEMA)}
                      className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${
                        showEMA ? 'bg-cyan-500 text-white shadow-sm' : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      EMA
                    </button>
                  </div>
                </div>

                {/* Ana Grafik (Mum Grafik) */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-3 sm:p-4 mb-3 sm:mb-4">
                  <h3 className="text-gray-900 font-semibold mb-2 text-sm sm:text-base">Fiyat Grafigi</h3>
                  <div ref={chartContainerRef} className="w-full" />
                </div>

                {/* Teknik Gostergeler */}
                <div className="grid md:grid-cols-2 gap-3 sm:gap-4 mb-3 sm:mb-4">
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-3 sm:p-4">
                    <h3 className="text-gray-900 font-semibold mb-2 text-sm sm:text-base">RSI (14)</h3>
                    <div ref={rsiChartRef} className="w-full" />
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-3 sm:p-4">
                    <h3 className="text-gray-900 font-semibold mb-2 text-sm sm:text-base">MACD (12, 26, 9)</h3>
                    <div ref={macdChartRef} className="w-full" />
                  </div>
                </div>

                {/* Hacim */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-3 sm:p-4">
                  <h3 className="text-gray-900 font-semibold mb-2 text-sm sm:text-base">Hacim</h3>
                  <div ref={volumeChartRef} className="w-full" />
                </div>
              </>
            )}
          </>
        )}
      </main>

      {/* Son guncelleme */}
      <div className="text-center py-4 text-xs text-gray-400">
        Veriler 15-20 dk gecikmelidir
      </div>
    </div>
  );
}