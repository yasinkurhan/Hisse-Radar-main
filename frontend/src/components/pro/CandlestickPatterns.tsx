'use client';

import React from 'react';
import type { CandlestickAnalysis } from '@/types';

interface CandlestickPatternsProps {
  data: CandlestickAnalysis;
}

export default function CandlestickPatterns({ data }: CandlestickPatternsProps) {
  const getDirectionColor = (direction: string) => {
    if (direction === 'bullish' || direction === 'yükseliş') return 'text-emerald-400';
    if (direction === 'bearish' || direction === 'düşüş') return 'text-red-400';
    return 'text-amber-400';
  };

  const getTrendLabel = (trend: string) => {
    switch (trend) {
      case 'yükseliş': return 'Yükseliş Trendi';
      case 'düşüş': return 'Düşüş Trendi';
      case 'yatay': return 'Yatay Seyir';
      default: return trend || 'Bilinmiyor';
    }
  };

  return (
    <div className="space-y-6">
      {/* Genel Durum */}
      <div className="bg-slate-800 rounded-xl p-6 shadow-lg border border-slate-700">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <span>🕯️</span> Mum Grafiği Analizi
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Genel Sinyal */}
          <div className={`p-4 rounded-lg border ${
            data.overall_signal === 'AL' ? 'bg-emerald-500/20 border-emerald-500' :
            data.overall_signal === 'SAT' ? 'bg-red-500/20 border-red-500' :
            'bg-amber-500/20 border-amber-500'
          }`}>
            <div className="text-sm text-slate-400 mb-1">Genel Sinyal</div>
            <div className={`text-2xl font-bold ${
              data.overall_signal === 'AL' ? 'text-emerald-400' :
              data.overall_signal === 'SAT' ? 'text-red-400' :
              'text-amber-400'
            }`}>
              {data.overall_signal || 'BEKLE'}
            </div>
            <div className="text-sm text-slate-400 mt-1">
              Güç: {data.signal_strength || 0}
            </div>
          </div>

          {/* Son Mum */}
          <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
            <div className="text-sm text-slate-400 mb-1">Son Mum</div>
            <div className={`text-xl font-bold ${getDirectionColor(data.last_candle?.direction)}`}>
              {data.last_candle?.direction === 'bullish' ? '📈 Yükseliş' :
               data.last_candle?.direction === 'bearish' ? '📉 Düşüş' : '➖ Nötr'}
            </div>
            <div className="text-sm text-slate-400 mt-1">
              Değişim: {data.last_candle?.change_percent?.toFixed(2) || 0}%
            </div>
          </div>

          {/* Mum Trendi */}
          <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
            <div className="text-sm text-slate-400 mb-1">Mum Trendi</div>
            <div className={`text-xl font-bold ${getDirectionColor(data.candle_trend?.trend)}`}>
              {getTrendLabel(data.candle_trend?.trend)}
            </div>
            <div className="text-sm text-slate-400 mt-1">
              Güç: {data.candle_trend?.strength || 0}
            </div>
          </div>
        </div>

        {/* Mum İstatistikleri */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
            <div className="text-sm text-slate-400">Yükseliş Mumu</div>
            <div className="text-xl font-bold text-emerald-400">{data.candle_trend?.bullish_candles || 0}</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
            <div className="text-sm text-slate-400">Düşüş Mumu</div>
            <div className="text-xl font-bold text-red-400">{data.candle_trend?.bearish_candles || 0}</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
            <div className="text-sm text-slate-400">Volatilite</div>
            <div className="text-xl font-bold text-white">{data.volatility?.level || '-'}</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3 text-center border border-slate-600">
            <div className="text-sm text-slate-400">ATR</div>
            <div className="text-xl font-bold text-white">{data.volatility?.atr?.toFixed(2) || '-'}</div>
          </div>
        </div>

        {/* Son Mum Detayları */}
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <h4 className="font-bold text-white mb-3">Son Mum Detayları</h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-slate-400">Gövde</div>
              <div className="font-bold text-white text-lg">%{data.last_candle?.body_percent?.toFixed(1) || 0}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400">Tip</div>
              <div className="font-bold text-white text-lg">{data.last_candle?.type || '-'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400">ATR %</div>
              <div className="font-bold text-white text-lg">%{data.volatility?.atr_percent?.toFixed(2) || 0}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Formasyonlar */}
      <div className="bg-slate-800 rounded-xl p-6 shadow-lg border border-slate-700">
        <h3 className="text-lg font-bold text-white mb-4">
          Tespit Edilen Formasyonlar ({data.patterns?.pattern_count || 0})
        </h3>
        
        {data.patterns?.patterns && data.patterns.patterns.length > 0 ? (
          <div className="space-y-3">
            {data.patterns.patterns.map((pattern, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${
                  pattern.type === 'bullish' ? 'bg-emerald-500/20 border-emerald-500/30' :
                  pattern.type === 'bearish' ? 'bg-red-500/20 border-red-500/30' :
                  'bg-slate-700/50 border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-bold text-white">{pattern.pattern_tr || pattern.pattern}</span>
                    <span className={`ml-2 text-xs px-2 py-1 rounded ${
                      pattern.reliability === 'high' ? 'bg-emerald-500/30 text-emerald-400' :
                      pattern.reliability === 'medium' ? 'bg-amber-500/30 text-amber-400' :
                      'bg-slate-600 text-slate-300'
                    }`}>
                      {pattern.reliability === 'high' ? 'Yüksek' :
                       pattern.reliability === 'medium' ? 'Orta' : 'Düşük'} Güvenilirlik
                    </span>
                  </div>
                  <span className={`px-4 py-1 rounded font-bold ${
                    pattern.type === 'bullish' ? 'bg-emerald-500/30 text-emerald-400' :
                    pattern.type === 'bearish' ? 'bg-red-500/30 text-red-400' :
                    'bg-slate-600 text-slate-300'
                  }`}>
                    {pattern.type === 'bullish' ? 'Yükseliş' :
                     pattern.type === 'bearish' ? 'Düşüş' : 'Nötr'}
                  </span>
                </div>
                {pattern.description && (
                  <p className="text-sm text-slate-300 mt-2">{pattern.description}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">
            <span className="text-4xl mb-2 block">🔍</span>
            <p className="font-medium">Son dönemde formasyon tespit edilmedi</p>
            <p className="text-sm mt-1">Piyasa normal seyrinde</p>
          </div>
        )}
      </div>
    </div>
  );
}
