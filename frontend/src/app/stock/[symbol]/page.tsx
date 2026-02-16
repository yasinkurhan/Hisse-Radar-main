'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { createChart, ColorType, IChartApi, CandlestickData } from 'lightweight-charts';
import Link from 'next/link';
import { ProAnalysisDashboard } from '@/components/pro';
import AIPrediction from '@/components/AIPrediction';
import FundamentalCharts from '@/components/FundamentalCharts';

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

export default function StockDetailPage() {
  const params = useParams();
  const symbol = params.symbol as string;

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
  const [activeTab, setActiveTab] = useState<'chart' | 'pro' | 'ai' | 'fundamental'>('chart');
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
        try {
          ref.current.remove();
        } catch (e) {
          // Chart zaten disposed olabilir
        }
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
        const response = await fetch(
          `/api/charts/ohlc/${symbol}?period=${period}&interval=1d`
        );
        
        if (isCancelled) return;
        
        const data = await response.json();

        if (isCancelled) return;
        
        if (!data.success) {
          throw new Error(data.error || 'Veri alinamadi');
        }

        setStockInfo(data.info);
        setChartData(data);
      } catch (err: any) {
        if (!isCancelled) {
          setError(err.message);
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isCancelled = true;
    };
  }, [symbol, period]);

  // Chart olusturma - veri geldikten ve DOM hazir olduktan sonra
  useEffect(() => {
    if (!chartData || loading) return;

    // Onceki grafikleri temizle
    cleanupAllCharts();
    isDisposedRef.current = false;

    // DOM'un hazir olmasini bekle
    const timer = setTimeout(() => {
      if (isDisposedRef.current || !chartData) return;

      // Ana mum grafigi
      if (chartContainerRef.current) {
        const chart = createChart(chartContainerRef.current, {
          layout: {
            background: { type: ColorType.Solid, color: '#1e293b' },
            textColor: '#94a3b8',
          },
          grid: {
            vertLines: { color: '#334155' },
            horzLines: { color: '#334155' },
          },
          width: chartContainerRef.current.clientWidth,
          height: window.innerWidth < 640 ? 280 : 400,
          crosshair: {
            mode: 1,
          },
          timeScale: {
            borderColor: '#475569',
            timeVisible: true,
          },
          rightPriceScale: {
            borderColor: '#475569',
          },
        });

        chartRef.current = chart;

        // Candlestick serisi
        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#22c55e',
          downColor: '#ef4444',
          borderUpColor: '#22c55e',
          borderDownColor: '#ef4444',
          wickUpColor: '#22c55e',
          wickDownColor: '#ef4444',
        });

        const candleData = chartData.ohlc.map((d: OHLCData) => ({
          time: d.time as any,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        }));

        candlestickSeries.setData(candleData as any);

        // Bollinger Bands
        if (showBollinger && chartData.indicators?.bollinger) {
          const bbUpper = chart.addLineSeries({
            color: 'rgba(156, 163, 175, 0.5)',
            lineWidth: 1,
          });
          const bbMiddle = chart.addLineSeries({
            color: 'rgba(156, 163, 175, 0.7)',
            lineWidth: 1,
            lineStyle: 2,
          });
          const bbLower = chart.addLineSeries({
            color: 'rgba(156, 163, 175, 0.5)',
            lineWidth: 1,
          });

          bbUpper.setData(
            chartData.indicators.bollinger.upper
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );
          bbMiddle.setData(
            chartData.indicators.bollinger.middle
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );
          bbLower.setData(
            chartData.indicators.bollinger.lower
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );
        }

        // SMA
        if (showSMA && chartData.indicators?.sma20) {
          const sma20 = chart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
          });
          const sma50 = chart.addLineSeries({
            color: '#8b5cf6',
            lineWidth: 2,
          });

          sma20.setData(
            chartData.indicators.sma20
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );
          if (chartData.indicators.sma50) {
            sma50.setData(
              chartData.indicators.sma50
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
          }
        }

        // EMA
        if (showEMA && chartData.indicators?.ema12) {
          const ema12 = chart.addLineSeries({
            color: '#06b6d4',
            lineWidth: 1,
          });
          const ema26 = chart.addLineSeries({
            color: '#ec4899',
            lineWidth: 1,
          });

          ema12.setData(
            chartData.indicators.ema12
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );
          if (chartData.indicators.ema26) {
            ema26.setData(
              chartData.indicators.ema26
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
          }
        }

        chart.timeScale().fitContent();
      }

      // RSI Grafigi
      if (rsiChartRef.current && chartData.indicators?.rsi) {
        const rsiChart = createChart(rsiChartRef.current, {
          layout: {
            background: { type: ColorType.Solid, color: '#1e293b' },
            textColor: '#94a3b8',
          },
          grid: {
            vertLines: { color: '#334155' },
            horzLines: { color: '#334155' },
          },
          width: rsiChartRef.current.clientWidth,
          height: 150,
          timeScale: {
            borderColor: '#475569',
            visible: false,
          },
          rightPriceScale: {
            borderColor: '#475569',
          },
        });

        rsiChartInstance.current = rsiChart;

        const rsiSeries = rsiChart.addLineSeries({
          color: '#f59e0b',
          lineWidth: 2,
        });

        rsiSeries.setData(
          chartData.indicators.rsi
            .filter((d: IndicatorData) => d.value !== null)
            .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
        );

        // RSI 30 ve 70 cizgileri
        const rsi30 = rsiChart.addLineSeries({
          color: 'rgba(34, 197, 94, 0.5)',
          lineWidth: 1,
          lineStyle: 2,
        });
        const rsi70 = rsiChart.addLineSeries({
          color: 'rgba(239, 68, 68, 0.5)',
          lineWidth: 1,
          lineStyle: 2,
        });

        const rsiTimes = chartData.indicators.rsi
          .filter((d: IndicatorData) => d.value !== null)
          .map((d: IndicatorData) => d.time);

        rsi30.setData(rsiTimes.map((t: number) => ({ time: t, value: 30 })));
        rsi70.setData(rsiTimes.map((t: number) => ({ time: t, value: 70 })));

        rsiChart.timeScale().fitContent();
      }

      // MACD Grafigi
      if (macdChartRef.current && chartData.indicators?.macd) {
        const macdChart = createChart(macdChartRef.current, {
          layout: {
            background: { type: ColorType.Solid, color: '#1e293b' },
            textColor: '#94a3b8',
          },
          grid: {
            vertLines: { color: '#334155' },
            horzLines: { color: '#334155' },
          },
          width: macdChartRef.current.clientWidth,
          height: 150,
          timeScale: {
            borderColor: '#475569',
            visible: false,
          },
          rightPriceScale: {
            borderColor: '#475569',
          },
        });

        macdChartInstance.current = macdChart;

        const macdLine = macdChart.addLineSeries({
          color: '#3b82f6',
          lineWidth: 2,
        });

        const signalLine = macdChart.addLineSeries({
          color: '#ef4444',
          lineWidth: 2,
        });

        const histogram = macdChart.addHistogramSeries({
          color: '#22c55e',
        });

        macdLine.setData(
          chartData.indicators.macd.macd
            .filter((d: IndicatorData) => d.value !== null)
            .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
        );

        signalLine.setData(
          chartData.indicators.macd.signal
            .filter((d: IndicatorData) => d.value !== null)
            .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
        );

        histogram.setData(
          chartData.indicators.macd.histogram
            .filter((d: IndicatorData) => d.value !== null)
            .map((d: IndicatorData) => ({
              time: d.time,
              value: d.value,
              color: d.value! >= 0 ? '#22c55e' : '#ef4444',
            }))
        );

        macdChart.timeScale().fitContent();
      }

      // Volume Grafigi
      if (volumeChartRef.current && chartData.ohlc) {
        const volumeChart = createChart(volumeChartRef.current, {
          layout: {
            background: { type: ColorType.Solid, color: '#1e293b' },
            textColor: '#94a3b8',
          },
          grid: {
            vertLines: { color: '#334155' },
            horzLines: { color: '#334155' },
          },
          width: volumeChartRef.current.clientWidth,
          height: 100,
          timeScale: {
            borderColor: '#475569',
          },
          rightPriceScale: {
            borderColor: '#475569',
          },
        });

        volumeChartInstance.current = volumeChart;

        const volumeSeries = volumeChart.addHistogramSeries({
          color: '#6366f1',
        });

        volumeSeries.setData(
          chartData.ohlc.map((d: OHLCData, i: number) => ({
            time: d.time as any,
            value: d.volume,
            color: i > 0 && d.close >= chartData.ohlc[i - 1].close ? '#22c55e' : '#ef4444',
          })) as any
        );

        volumeChart.timeScale().fitContent();
      }
    }, 100);

    return () => {
      clearTimeout(timer);
      cleanupAllCharts();
    };
  }, [chartData, loading, showBollinger, showSMA, showEMA, cleanupAllCharts]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (isDisposedRef.current) return;
      try {
        if (chartRef.current && chartContainerRef.current) {
          chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        }
        if (rsiChartInstance.current && rsiChartRef.current) {
          rsiChartInstance.current.applyOptions({ width: rsiChartRef.current.clientWidth });
        }
        if (macdChartInstance.current && macdChartRef.current) {
          macdChartInstance.current.applyOptions({ width: macdChartRef.current.clientWidth });
        }
        if (volumeChartInstance.current && volumeChartRef.current) {
          volumeChartInstance.current.applyOptions({ width: volumeChartRef.current.clientWidth });
        }
      } catch (e) {
        // Chart disposed olabilir
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('tr-TR').format(num);
  };

  const formatVolume = (num: number) => {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(2) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(2) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(2) + 'K';
    return num.toString();
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 sm:p-6 text-center">
            <p className="text-red-400">{error}</p>
            <Link href="/" className="text-blue-400 hover:underline mt-2 inline-block">
              Ana Sayfaya Don
            </Link>
          </div>
        ) : (
          <>
            {/* Hisse Bilgileri */}
            {stockInfo && (
              <div className="bg-slate-800/50 rounded-xl p-4 sm:p-6 mb-4 sm:mb-6">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 sm:gap-4">
                  <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-white">{stockInfo.symbol}</h1>
                    <p className="text-slate-400 text-sm sm:text-base">{stockInfo.name}</p>
                    <span className="inline-block mt-2 px-2 sm:px-3 py-0.5 sm:py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs sm:text-sm">
                      {stockInfo.sector || 'Bilinmiyor'}
                    </span>
                  </div>
                  <div className="text-left sm:text-right">
                    <p className="text-2xl sm:text-4xl font-bold text-white">₺{formatNumber(stockInfo.currentPrice)}</p>
                    <p className={`text-lg sm:text-xl ${stockInfo.changePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {stockInfo.changePercent >= 0 ? '+' : ''}{stockInfo.change.toFixed(2)} ({stockInfo.changePercent.toFixed(2)}%)
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 mt-4 sm:mt-6">
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3">
                    <p className="text-slate-400 text-xs sm:text-sm">Günlük En Yüksek</p>
                    <p className="text-white font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.dayHigh)}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3">
                    <p className="text-slate-400 text-xs sm:text-sm">Günlük En Düşük</p>
                    <p className="text-white font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.dayLow)}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3">
                    <p className="text-slate-400 text-xs sm:text-sm">Hacim</p>
                    <p className="text-white font-semibold text-sm sm:text-base">{formatVolume(stockInfo.volume)}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3">
                    <p className="text-slate-400 text-xs sm:text-sm">Ort. Hacim</p>
                    <p className="text-white font-semibold text-sm sm:text-base">{formatVolume(stockInfo.avgVolume)}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3">
                    <p className="text-slate-400 text-xs sm:text-sm">52H En Yüksek</p>
                    <p className="text-white font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.fiftyTwoWeekHigh)}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3">
                    <p className="text-slate-400 text-xs sm:text-sm">52H En Düşük</p>
                    <p className="text-white font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.fiftyTwoWeekLow)}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-2 sm:p-3 col-span-2 sm:col-span-1">
                    <p className="text-slate-400 text-xs sm:text-sm">Önceki Kapanış</p>
                    <p className="text-white font-semibold text-sm sm:text-base">₺{formatNumber(stockInfo.previousClose)}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Tab Seçimi */}
            <div className="flex gap-2 mb-4 sm:mb-6 overflow-x-auto pb-2">
              <button
                onClick={() => setActiveTab('chart')}
                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition flex items-center gap-2 whitespace-nowrap text-sm sm:text-base ${
                  activeTab === 'chart'
                    ? 'bg-blue-500 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <span>📊</span> <span className="hidden sm:inline">Grafik & </span>Teknik
              </button>
              <button
                onClick={() => setActiveTab('pro')}
                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition flex items-center gap-2 whitespace-nowrap text-sm sm:text-base ${
                  activeTab === 'pro'
                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <span>🚀</span> PRO Analiz
              </button>
              <button
                onClick={() => setActiveTab('ai')}
                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition flex items-center gap-2 whitespace-nowrap text-sm sm:text-base ${
                  activeTab === 'ai'
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <span>🤖</span> AI Tahmin
              </button>
              <button
                onClick={() => setActiveTab('fundamental')}
                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-medium transition flex items-center gap-2 whitespace-nowrap text-sm sm:text-base ${
                  activeTab === 'fundamental'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <span>📈</span> Temel Analiz
              </button>
            </div>

            {activeTab === 'pro' ? (
              <ProAnalysisDashboard symbol={symbol} />
            ) : activeTab === 'ai' ? (
              <AIPrediction symbol={symbol} />
            ) : activeTab === 'fundamental' ? (
              <FundamentalCharts symbol={symbol} />
            ) : (
              <>
                {/* Periyod ve Gosterge Secimi */}
            <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 mb-4">
              <div className="flex gap-1.5 sm:gap-2 overflow-x-auto">
                {['1mo', '3mo', '6mo', '1y', '2y'].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${period === p
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
              <div className="flex gap-1.5 sm:gap-2 sm:ml-auto overflow-x-auto">
                <button
                  onClick={() => setShowBollinger(!showBollinger)}
                  className={`px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm whitespace-nowrap ${showBollinger ? 'bg-purple-500 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                >
                  Bollinger
                </button>
                <button
                  onClick={() => setShowSMA(!showSMA)}
                  className={`px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm whitespace-nowrap ${showSMA ? 'bg-yellow-500 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                >
                  SMA
                </button>
                <button
                  onClick={() => setShowEMA(!showEMA)}
                  className={`px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm whitespace-nowrap ${showEMA ? 'bg-cyan-500 text-white' : 'bg-slate-700 text-slate-300'
                    }`}
                >
                  EMA
                </button>
              </div>
            </div>

            {/* Ana Grafik (Mum Grafik) */}
            <div className="bg-slate-800/50 rounded-xl p-3 sm:p-4 mb-3 sm:mb-4">
              <h3 className="text-white font-semibold mb-2 text-sm sm:text-base">Fiyat Grafiği</h3>
              <div ref={chartContainerRef} className="w-full" />
            </div>

            {/* Teknik Gostergeler */}
            <div className="grid md:grid-cols-2 gap-3 sm:gap-4 mb-3 sm:mb-4">
              <div className="bg-slate-800/50 rounded-xl p-3 sm:p-4">
                <h3 className="text-white font-semibold mb-2 text-sm sm:text-base">RSI (14)</h3>
                <div ref={rsiChartRef} className="w-full" />
              </div>
              <div className="bg-slate-800/50 rounded-xl p-3 sm:p-4">
                <h3 className="text-white font-semibold mb-2 text-sm sm:text-base">MACD (12, 26, 9)</h3>
                <div ref={macdChartRef} className="w-full" />
              </div>
            </div>

            {/* Hacim */}
            <div className="bg-slate-800/50 rounded-xl p-3 sm:p-4">
              <h3 className="text-white font-semibold mb-2 text-sm sm:text-base">Hacim</h3>
              <div ref={volumeChartRef} className="w-full" />
            </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}