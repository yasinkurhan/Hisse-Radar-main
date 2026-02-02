'use client';

/**
 * HisseRadar Teknik Göstergeler Bileşeni
 * =======================================
 * RSI, MACD, Bollinger ve MA göstergelerini gösterir
 */

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus, Activity, BarChart3, Target } from 'lucide-react';
import { getTechnicalSummary } from '@/lib/api';
import type { TechnicalSummary } from '@/types';

interface TechnicalIndicatorsProps {
  symbol: string;
}

export default function TechnicalIndicators({ symbol }: TechnicalIndicatorsProps) {
  const [data, setData] = useState<TechnicalSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getTechnicalSummary(symbol);
        setData(response);
      } catch (err) {
        console.error('Teknik analiz yüklenemedi:', err);
        setError('Veriler yüklenemedi');
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [symbol]);

  // Sinyal badge rengi
  const getSignalClass = (signal: string) => {
    if (signal === 'Alış' || signal === 'Güçlü Al' || signal === 'Al') return 'signal-buy';
    if (signal === 'Satış' || signal === 'Sat' || signal === 'Azalt') return 'signal-sell';
    return 'signal-neutral';
  };

  // Sinyal ikonu
  const getSignalIcon = (signal: string) => {
    if (signal === 'Alış' || signal === 'Güçlü Al' || signal === 'Al') {
      return <TrendingUp className="w-4 h-4" />;
    }
    if (signal === 'Satış' || signal === 'Sat' || signal === 'Azalt') {
      return <TrendingDown className="w-4 h-4" />;
    }
    return <Minus className="w-4 h-4" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12 text-red-500">
        {error || 'Veri bulunamadı'}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Genel Sinyal */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Teknik Analiz Özeti</h3>
            <p className="text-sm text-gray-500 mt-1">
              Güncel fiyat: ₺{data.current_price?.toFixed(2)}
            </p>
          </div>
          
          <div className={`signal-badge ${getSignalClass(data.overall_signal)} flex items-center gap-2`}>
            {getSignalIcon(data.overall_signal)}
            <span className="font-semibold">{data.overall_signal}</span>
          </div>
        </div>

        {/* Sinyal sayıları */}
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{data.buy_signals}</div>
            <div className="text-xs text-green-700">Alış Sinyali</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">{data.neutral_signals}</div>
            <div className="text-xs text-gray-700">Nötr</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{data.sell_signals}</div>
            <div className="text-xs text-red-700">Satış Sinyali</div>
          </div>
        </div>
      </div>

      {/* Gösterge Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* RSI */}
        <div className="indicator-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" />
              <h4 className="font-semibold text-gray-900">RSI (14)</h4>
            </div>
            <span className={`signal-badge ${getSignalClass(data.indicators.rsi.signal)}`}>
              {data.indicators.rsi.signal}
            </span>
          </div>
          
          {/* RSI Göstergesi */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Değer</span>
              <span className="font-mono font-semibold">{data.indicators.rsi.value}</span>
            </div>
            
            {/* RSI Bar */}
            <div className="relative h-4 bg-gray-100 rounded-full overflow-hidden">
              {/* Aşırı satım bölgesi */}
              <div className="absolute left-0 top-0 bottom-0 w-[30%] bg-green-200" />
              {/* Aşırı alım bölgesi */}
              <div className="absolute right-0 top-0 bottom-0 w-[30%] bg-red-200" />
              {/* Gösterge */}
              <div 
                className="absolute top-0 bottom-0 w-1 bg-primary-600 rounded"
                style={{ left: `${Math.min(Math.max(data.indicators.rsi.value, 0), 100)}%` }}
              />
            </div>
            
            <div className="flex justify-between text-xs text-gray-400">
              <span>0 (Aşırı Satım)</span>
              <span>50</span>
              <span>100 (Aşırı Alım)</span>
            </div>
          </div>

          <p className="mt-3 text-xs text-gray-500">
            RSI &gt; 70: Aşırı alım, RSI &lt; 30: Aşırı satım
          </p>
        </div>

        {/* MACD */}
        <div className="indicator-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary-600" />
              <h4 className="font-semibold text-gray-900">MACD (12,26,9)</h4>
            </div>
            <span className={`signal-badge ${getSignalClass(data.indicators.macd.signal)}`}>
              {data.indicators.macd.signal}
            </span>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Histogram</span>
              <span className={`font-mono font-semibold ${
                data.indicators.macd.histogram > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {data.indicators.macd.histogram?.toFixed(4)}
              </span>
            </div>
            
            {/* MACD Histogram Visualizasyonu */}
            <div className="h-8 flex items-center justify-center bg-gray-50 rounded">
              <div 
                className={`h-6 w-8 rounded ${
                  data.indicators.macd.histogram > 0 ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
            </div>
          </div>

          <p className="mt-3 text-xs text-gray-500">
            Histogram &gt; 0: Yükseliş momentumu, &lt; 0: Düşüş momentumu
          </p>
        </div>

        {/* Bollinger Bands */}
        <div className="indicator-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-600" />
              <h4 className="font-semibold text-gray-900">Bollinger Bands</h4>
            </div>
            <span className="text-sm text-gray-500">
              Pozisyon: {data.indicators.bollinger.position}
            </span>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Üst Bant</span>
              <span className="font-mono">₺{data.indicators.bollinger.upper?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Orta (SMA20)</span>
              <span className="font-mono">₺{data.indicators.bollinger.middle?.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Alt Bant</span>
              <span className="font-mono">₺{data.indicators.bollinger.lower?.toFixed(2)}</span>
            </div>
          </div>

          <p className="mt-3 text-xs text-gray-500">
            Bantlara yaklaşma aşırı alım/satım sinyali verebilir
          </p>
        </div>

        {/* Trend */}
        <div className="indicator-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary-600" />
              <h4 className="font-semibold text-gray-900">Trend Analizi</h4>
            </div>
            <span className={`signal-badge ${
              data.indicators.trend.includes('Yükseliş') ? 'signal-buy' :
              data.indicators.trend.includes('Düşüş') ? 'signal-sell' : 'signal-neutral'
            }`}>
              {data.indicators.trend}
            </span>
          </div>
          
          <p className="text-sm text-gray-600">
            {data.indicators.trend === 'Güçlü Yükseliş' && 
              'Fiyat SMA50 ve SMA200 üzerinde. Güçlü boğa trendi.'}
            {data.indicators.trend === 'Yükseliş' && 
              'Fiyat SMA50 üzerinde. Yükseliş eğilimi.'}
            {data.indicators.trend === 'Güçlü Düşüş' && 
              'Fiyat SMA50 ve SMA200 altında. Güçlü ayı trendi.'}
            {data.indicators.trend === 'Düşüş' && 
              'Fiyat SMA50 altında. Düşüş eğilimi.'}
            {data.indicators.trend === 'Yatay' && 
              'Belirgin bir trend yok. Yatay seyir.'}
          </p>

          <p className="mt-3 text-xs text-gray-500">
            SMA50 ve SMA200 kullanılarak hesaplanır
          </p>
        </div>
      </div>

      {/* Sinyal Detayları */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Sinyal Detayları</h4>
        
        <div className="space-y-3">
          {data.signals.map((signal, index) => (
            <div 
              key={index}
              className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
            >
              <div className="flex items-center gap-3">
                {getSignalIcon(signal.signal)}
                <span className="font-medium text-gray-900">{signal.indicator}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">{signal.reason}</span>
                <span className={`signal-badge ${getSignalClass(signal.signal)}`}>
                  {signal.signal}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
