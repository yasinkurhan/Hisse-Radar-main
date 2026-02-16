'use client';

/**
 * HisseRadar Fiyat Grafiği Bileşeni
 * ==================================
 * TradingView Lightweight Charts kullanarak mum grafiği gösterir
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts';
import { getCandleData, getVolumeData } from '@/lib/api';
import type { Period, Interval, CandleData, VolumeData } from '@/types';
import { PERIODS, INTERVALS } from '@/types';

interface PriceChartProps {
  symbol: string;
  initialPeriod?: Period;
  initialInterval?: Interval;
  height?: number;
}

export default function PriceChart({
  symbol,
  initialPeriod = '3mo',
  initialInterval = '1d',
  height = 400
}: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const isDisposedRef = useRef(false);
  
  const [period, setPeriod] = useState<Period>(initialPeriod);
  const [interval, setInterval] = useState<Interval>(initialInterval);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartKey, setChartKey] = useState(0); // Chart'ı yeniden oluşturmak için key

  // Chart'ı güvenli şekilde temizle
  const cleanupChart = useCallback(() => {
    isDisposedRef.current = true;
    if (chartRef.current) {
      try {
        chartRef.current.remove();
      } catch (e) {
        // Chart zaten disposed olabilir
      }
      chartRef.current = null;
    }
    candleSeriesRef.current = null;
    volumeSeriesRef.current = null;
  }, []);

  // Grafik oluştur - period veya interval değiştiğinde de yeniden oluştur
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Önceki grafiği temizle
    cleanupChart();
    isDisposedRef.current = false;

    // Yeni grafik oluştur
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#1e293b' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#334155' },
        horzLines: { color: '#334155' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#475569',
      },
      timeScale: {
        borderColor: '#475569',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Mum serisi ekle
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    // Hacim serisi ekle
    const volumeSeries = chart.addHistogramSeries({
      color: '#3b82f6',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Pencere yeniden boyutlandırma
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current && !isDisposedRef.current) {
        try {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth
          });
        } catch (e) {
          // Chart disposed olabilir
        }
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cleanupChart();
    };
  }, [height, chartKey, cleanupChart]);

  // Veri yükle
  useEffect(() => {
    let isCancelled = false;
    
    async function loadData() {
      if (!chartRef.current || isDisposedRef.current) return;
      
      setIsLoading(true);
      setError(null);

      try {
        // Mum ve hacim verilerini paralel yükle
        const [candleResponse, volumeResponse] = await Promise.all([
          getCandleData(symbol, period, interval),
          getVolumeData(symbol, period, interval)
        ]);

        // İptal edilmişse veya chart disposed ise işlem yapma
        if (isCancelled || isDisposedRef.current || !chartRef.current) return;

        if (candleSeriesRef.current && candleResponse.candles) {
          // Veriyi TradingView formatına çevir
          const candleData: CandlestickData[] = candleResponse.candles.map((c: CandleData) => ({
            time: c.time as any,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
          }));
          try {
            candleSeriesRef.current.setData(candleData);
          } catch (e) {
            // Series disposed olabilir
          }
        }

        if (volumeSeriesRef.current && volumeResponse.volumes) {
          const volumeData: HistogramData[] = volumeResponse.volumes.map((v: VolumeData) => ({
            time: v.time as any,
            value: v.value,
            color: v.color || '#3b82f6'
          }));
          try {
            volumeSeriesRef.current.setData(volumeData);
          } catch (e) {
            // Series disposed olabilir
          }
        }

        // Görünümü ayarla
        if (chartRef.current && !isDisposedRef.current) {
          try {
            chartRef.current.timeScale().fitContent();
          } catch (e) {
            // Chart disposed olabilir
          }
        }

      } catch (err) {
        if (!isCancelled) {
          console.error('Grafik verisi yüklenemedi:', err);
          setError('Grafik verisi yüklenemedi');
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    // Chart hazır olduğunda veriyi yükle
    const timer = setTimeout(() => {
      if (chartRef.current && !isDisposedRef.current) {
        loadData();
      }
    }, 100);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [symbol, period, interval, chartKey]);

  // Period değiştiğinde chart'ı yeniden oluştur
  const handlePeriodChange = (newPeriod: Period) => {
    setPeriod(newPeriod);
    setChartKey(prev => prev + 1);
  };

  // Interval değiştiğinde chart'ı yeniden oluştur  
  const handleIntervalChange = (newInterval: Interval) => {
    setInterval(newInterval);
    setChartKey(prev => prev + 1);
  };

  return (
    <div className="space-y-4">
      {/* Kontroller */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        {/* Period Seçici */}
        <div className="flex flex-wrap gap-1">
          {Object.entries(PERIODS).map(([key, label]) => (
            <button
              key={key}
              onClick={() => handlePeriodChange(key as Period)}
              className={`
                px-3 py-1.5 text-sm font-medium rounded transition-colors
                ${period === key
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }
              `}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Interval Seçici */}
        <div className="flex gap-1">
          {['1d', '1wk', '1mo'].map((int) => (
            <button
              key={int}
              onClick={() => handleIntervalChange(int as Interval)}
              className={`
                px-3 py-1.5 text-sm font-medium rounded transition-colors
                ${interval === int
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }
              `}
            >
              {INTERVALS[int as Interval]}
            </button>
          ))}
        </div>
      </div>

      {/* Grafik */}
      <div className="relative bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        {/* Yükleniyor */}
        {isLoading && (
          <div className="absolute inset-0 bg-slate-800/80 flex items-center justify-center z-10">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-slate-300">Yükleniyor...</span>
            </div>
          </div>
        )}

        {/* Hata */}
        {error && (
          <div className="absolute inset-0 bg-slate-800/80 flex items-center justify-center z-10">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Chart Container */}
        <div ref={chartContainerRef} style={{ height: `${height}px` }} />
      </div>

      {/* Bilgi */}
      <div className="text-xs text-slate-400 text-center">
        💡 Grafiği yakınlaştırmak için kaydırın, sürükleyerek hareket ettirin
      </div>
    </div>
  );
}
