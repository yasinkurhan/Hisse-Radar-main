'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData, LineData } from 'lightweight-charts';
import Link from 'next/link';

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

export default function StockDetailPage() {
  const params = useParams();
  const symbol = params.symbol as string;

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<HTMLDivElement>(null);
  const macdChartRef = useRef<HTMLDivElement>(null);
  const volumeChartRef = useRef<HTMLDivElement>(null);

  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('3mo');
  const [showBollinger, setShowBollinger] = useState(true);
  const [showSMA, setShowSMA] = useState(true);
  const [showEMA, setShowEMA] = useState(false);

  const chartRef = useRef<IChartApi | null>(null);
  const rsiChartInstance = useRef<IChartApi | null>(null);
  const macdChartInstance = useRef<IChartApi | null>(null);
  const volumeChartInstance = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!symbol) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/charts/ohlc/${symbol}?period=${period}&interval=1d`
        );
        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || 'Veri alınamadı');
        }

        setStockInfo(data.info);

        // Mevcut grafikleri temizle
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
        if (rsiChartInstance.current) {
          rsiChartInstance.current.remove();
          rsiChartInstance.current = null;
        }
        if (macdChartInstance.current) {
          macdChartInstance.current.remove();
          macdChartInstance.current = null;
        }
        if (volumeChartInstance.current) {
          volumeChartInstance.current.remove();
          volumeChartInstance.current = null;
        }

        // Ana mum grafiği
        if (chartContainerRef.current) {
          const chart = createChart(chartContainerRef.current, {
            layout: {
              background: { type: ColorType.Solid, color: '#1a1a2e' },
              textColor: '#d1d5db',
            },
            grid: {
              vertLines: { color: '#2d2d44' },
              horzLines: { color: '#2d2d44' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 400,
            crosshair: {
              mode: 1,
            },
            timeScale: {
              borderColor: '#2d2d44',
              timeVisible: true,
            },
            rightPriceScale: {
              borderColor: '#2d2d44',
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

          const candleData: CandlestickData[] = data.ohlc.map((d: OHLCData) => ({
            time: d.time,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
          }));

          candlestickSeries.setData(candleData);

          // Bollinger Bands
          if (showBollinger && data.indicators.bollinger) {
            const bbUpper = chart.addLineSeries({
              color: 'rgba(156, 163, 175, 0.5)',
              lineWidth: 1,
              title: 'BB Upper',
            });
            const bbMiddle = chart.addLineSeries({
              color: 'rgba(156, 163, 175, 0.7)',
              lineWidth: 1,
              lineStyle: 2,
              title: 'BB Middle',
            });
            const bbLower = chart.addLineSeries({
              color: 'rgba(156, 163, 175, 0.5)',
              lineWidth: 1,
              title: 'BB Lower',
            });

            bbUpper.setData(
              data.indicators.bollinger.upper
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
            bbMiddle.setData(
              data.indicators.bollinger.middle
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
            bbLower.setData(
              data.indicators.bollinger.lower
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
          }

          // SMA
          if (showSMA) {
            const sma20 = chart.addLineSeries({
              color: '#f59e0b',
              lineWidth: 2,
              title: 'SMA 20',
            });
            const sma50 = chart.addLineSeries({
              color: '#8b5cf6',
              lineWidth: 2,
              title: 'SMA 50',
            });

            sma20.setData(
              data.indicators.sma20
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
            sma50.setData(
              data.indicators.sma50
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
          }

          // EMA
          if (showEMA) {
            const ema12 = chart.addLineSeries({
              color: '#06b6d4',
              lineWidth: 1,
              title: 'EMA 12',
            });
            const ema26 = chart.addLineSeries({
              color: '#ec4899',
              lineWidth: 1,
              title: 'EMA 26',
            });

            ema12.setData(
              data.indicators.ema12
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
            ema26.setData(
              data.indicators.ema26
                .filter((d: IndicatorData) => d.value !== null)
                .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
            );
          }

          chart.timeScale().fitContent();
        }

        // RSI Grafiği
        if (rsiChartRef.current && data.indicators.rsi) {
          const rsiChart = createChart(rsiChartRef.current, {
            layout: {
              background: { type: ColorType.Solid, color: '#1a1a2e' },
              textColor: '#d1d5db',
            },
            grid: {
              vertLines: { color: '#2d2d44' },
              horzLines: { color: '#2d2d44' },
            },
            width: rsiChartRef.current.clientWidth,
            height: 150,
            timeScale: {
              borderColor: '#2d2d44',
              visible: false,
            },
            rightPriceScale: {
              borderColor: '#2d2d44',
            },
          });

          rsiChartInstance.current = rsiChart;

          const rsiSeries = rsiChart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
            title: 'RSI',
          });

          rsiSeries.setData(
            data.indicators.rsi
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );

          // RSI 30 ve 70 çizgileri
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

          const rsiTimes = data.indicators.rsi
            .filter((d: IndicatorData) => d.value !== null)
            .map((d: IndicatorData) => d.time);

          rsi30.setData(rsiTimes.map((t: number) => ({ time: t, value: 30 })));
          rsi70.setData(rsiTimes.map((t: number) => ({ time: t, value: 70 })));

          rsiChart.timeScale().fitContent();
        }

        // MACD Grafiği
        if (macdChartRef.current && data.indicators.macd) {
          const macdChart = createChart(macdChartRef.current, {
            layout: {
              background: { type: ColorType.Solid, color: '#1a1a2e' },
              textColor: '#d1d5db',
            },
            grid: {
              vertLines: { color: '#2d2d44' },
              horzLines: { color: '#2d2d44' },
            },
            width: macdChartRef.current.clientWidth,
            height: 150,
            timeScale: {
              borderColor: '#2d2d44',
              visible: false,
            },
            rightPriceScale: {
              borderColor: '#2d2d44',
            },
          });

          macdChartInstance.current = macdChart;

          const macdLine = macdChart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 2,
            title: 'MACD',
          });

          const signalLine = macdChart.addLineSeries({
            color: '#ef4444',
            lineWidth: 2,
            title: 'Signal',
          });

          const histogram = macdChart.addHistogramSeries({
            color: '#22c55e',
            title: 'Histogram',
          });

          macdLine.setData(
            data.indicators.macd.macd
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );

          signalLine.setData(
            data.indicators.macd.signal
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({ time: d.time, value: d.value }))
          );

          histogram.setData(
            data.indicators.macd.histogram
              .filter((d: IndicatorData) => d.value !== null)
              .map((d: IndicatorData) => ({
                time: d.time,
                value: d.value,
                color: d.value! >= 0 ? '#22c55e' : '#ef4444',
              }))
          );

          macdChart.timeScale().fitContent();
        }

        // Volume Grafiği
        if (volumeChartRef.current) {
          const volumeChart = createChart(volumeChartRef.current, {
            layout: {
              background: { type: ColorType.Solid, color: '#1a1a2e' },
              textColor: '#d1d5db',
            },
            grid: {
              vertLines: { color: '#2d2d44' },
              horzLines: { color: '#2d2d44' },
            },
            width: volumeChartRef.current.clientWidth,
            height: 100,
            timeScale: {
              borderColor: '#2d2d44',
            },
            rightPriceScale: {
              borderColor: '#2d2d44',
            },
          });

          volumeChartInstance.current = volumeChart;

          const volumeSeries = volumeChart.addHistogramSeries({
            color: '#6366f1',
            title: 'Volume',
          });

          volumeSeries.setData(
            data.ohlc.map((d: OHLCData, i: number) => ({
              time: d.time,
              value: d.volume,
              color: i > 0 && d.close >= data.ohlc[i - 1].close ? '#22c55e' : '#ef4444',
            }))
          );

          volumeChart.timeScale().fitContent();
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Cleanup
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
      }
      if (rsiChartInstance.current) {
        rsiChartInstance.current.remove();
      }
      if (macdChartInstance.current) {
        macdChartInstance.current.remove();
      }
      if (volumeChartInstance.current) {
        volumeChartInstance.current.remove();
      }
    };
  }, [symbol, period, showBollinger, showSMA, showEMA]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">📊</span>
              </div>
              <span className="text-xl font-bold text-white">HisseRadar</span>
            </Link>
            <nav className="flex gap-4">
              <Link href="/analysis" className="text-gray-300 hover:text-white">Analiz</Link>
              <Link href="/heatmap" className="text-gray-300 hover:text-white">Isı Haritası</Link>
              <Link href="/compare" className="text-gray-300 hover:text-white">Karşılaştır</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-6 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        ) : (
          <>
            {/* Hisse Bilgileri */}
            {stockInfo && (
              <div className="bg-gray-800/50 rounded-xl p-6 mb-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h1 className="text-3xl font-bold text-white">{stockInfo.symbol}</h1>
                    <p className="text-gray-400">{stockInfo.name}</p>
                    <span className="inline-block mt-2 px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">
                      {stockInfo.sector}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-4xl font-bold text-white">₺{formatNumber(stockInfo.currentPrice)}</p>
                    <p className={`text-xl ${stockInfo.changePercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {stockInfo.changePercent >= 0 ? '+' : ''}{stockInfo.change.toFixed(2)} ({stockInfo.changePercent.toFixed(2)}%)
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">Günlük En Yüksek</p>
                    <p className="text-white font-semibold">₺{formatNumber(stockInfo.dayHigh)}</p>
                  </div>
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">Günlük En Düşük</p>
                    <p className="text-white font-semibold">₺{formatNumber(stockInfo.dayLow)}</p>
                  </div>
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">Hacim</p>
                    <p className="text-white font-semibold">{formatVolume(stockInfo.volume)}</p>
                  </div>
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">Ort. Hacim</p>
                    <p className="text-white font-semibold">{formatVolume(stockInfo.avgVolume)}</p>
                  </div>
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">52H En Yüksek</p>
                    <p className="text-white font-semibold">₺{formatNumber(stockInfo.fiftyTwoWeekHigh)}</p>
                  </div>
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">52H En Düşük</p>
                    <p className="text-white font-semibold">₺{formatNumber(stockInfo.fiftyTwoWeekLow)}</p>
                  </div>
                  <div className="bg-gray-700/30 rounded-lg p-3">
                    <p className="text-gray-400 text-sm">Önceki Kapanış</p>
                    <p className="text-white font-semibold">₺{formatNumber(stockInfo.previousClose)}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Periyod ve Gösterge Seçimi */}
            <div className="flex flex-wrap items-center gap-4 mb-4">
              <div className="flex gap-2">
                {['1mo', '3mo', '6mo', '1y', '2y'].map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                      period === p
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
              <div className="flex gap-2 ml-auto">
                <button
                  onClick={() => setShowBollinger(!showBollinger)}
                  className={`px-3 py-2 rounded-lg text-sm ${
                    showBollinger ? 'bg-purple-500 text-white' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Bollinger
                </button>
                <button
                  onClick={() => setShowSMA(!showSMA)}
                  className={`px-3 py-2 rounded-lg text-sm ${
                    showSMA ? 'bg-yellow-500 text-white' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  SMA
                </button>
                <button
                  onClick={() => setShowEMA(!showEMA)}
                  className={`px-3 py-2 rounded-lg text-sm ${
                    showEMA ? 'bg-cyan-500 text-white' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  EMA
                </button>
              </div>
            </div>

            {/* Ana Grafik (Mum Grafik) */}
            <div className="bg-gray-800/50 rounded-xl p-4 mb-4">
              <h3 className="text-white font-semibold mb-2">Fiyat Grafiği</h3>
              <div ref={chartContainerRef} className="w-full" />
            </div>

            {/* Teknik Göstergeler */}
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-800/50 rounded-xl p-4">
                <h3 className="text-white font-semibold mb-2">RSI (14)</h3>
                <div ref={rsiChartRef} className="w-full" />
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4">
                <h3 className="text-white font-semibold mb-2">MACD (12, 26, 9)</h3>
                <div ref={macdChartRef} className="w-full" />
              </div>
            </div>

            {/* Hacim */}
            <div className="bg-gray-800/50 rounded-xl p-4">
              <h3 className="text-white font-semibold mb-2">Hacim</h3>
              <div ref={volumeChartRef} className="w-full" />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

