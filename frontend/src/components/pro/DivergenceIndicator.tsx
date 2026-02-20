'use client';

import React from 'react';
import type { DivergenceData } from '@/types';

interface DivergenceIndicatorProps {
  data: DivergenceData;
}

export default function DivergenceIndicator({ data }: DivergenceIndicatorProps) {
  const getDivergenceColor = (divergence: string) => {
    if (divergence === 'bullish') return 'text-emerald-400';
    if (divergence === 'bearish') return 'text-red-400';
    return 'text-gray-500';
  };

  const getDivergenceLabel = (divergence: string) => {
    switch (divergence) {
      case 'bullish': return 'Boğa Diverjansı';
      case 'bearish': return 'Ayı Diverjansı';
      case 'none': return 'Diverjans Yok';
      default: return divergence || 'Bilinmiyor';
    }
  };

  const rsi = data.rsi_divergence;
  const macd = data.macd_divergence;

  return (
    <div className="bg-white rounded-xl p-5 shadow-lg border border-gray-200">
      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <span>🔀</span> Diverjans Analizi
      </h3>

      {/* RSI Diverjans */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
        <h4 className="font-bold text-gray-900 mb-3">RSI Diverjansı</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Durum</span>
            <span className={`font-bold ${getDivergenceColor(rsi?.divergence)}`}>
              {getDivergenceLabel(rsi?.divergence)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Sinyal</span>
            <span className={`px-3 py-1 rounded text-sm font-bold ${
              rsi?.signal === 'AL' ? 'bg-emerald-500/30 text-emerald-400' :
              rsi?.signal === 'SAT' ? 'bg-red-500/30 text-red-400' :
              'bg-gray-200 text-gray-600'
            }`}>
              {rsi?.signal || 'BEKLE'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Güç</span>
            <span className="font-bold text-gray-900">{rsi?.strength || 0}</span>
          </div>
          {rsi?.description && (
            <div className="mt-2 p-3 bg-white rounded text-sm text-gray-600">
              {rsi.description}
            </div>
          )}
        </div>
      </div>

      {/* MACD Diverjans */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <h4 className="font-bold text-gray-900 mb-3">MACD Diverjansı</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Durum</span>
            <span className={`font-bold ${getDivergenceColor(macd?.divergence)}`}>
              {getDivergenceLabel(macd?.divergence)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Sinyal</span>
            <span className={`px-3 py-1 rounded text-sm font-bold ${
              macd?.signal === 'AL' ? 'bg-emerald-500/30 text-emerald-400' :
              macd?.signal === 'SAT' ? 'bg-red-500/30 text-red-400' :
              'bg-gray-200 text-gray-600'
            }`}>
              {macd?.signal || 'BEKLE'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Güç</span>
            <span className="font-bold text-gray-900">{macd?.strength || 0}</span>
          </div>
          {macd?.description && (
            <div className="mt-2 p-3 bg-white rounded text-sm text-gray-600">
              {macd.description}
            </div>
          )}
        </div>
      </div>

      {/* Özet */}
      {(rsi?.divergence !== 'none' || macd?.divergence !== 'none') && (
        <div className="mt-4 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className="font-bold text-blue-300">Aktif Diverjans Tespit Edildi!</span>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Diverjanslar trend dönüşünün erken sinyalleri olabilir.
          </p>
        </div>
      )}
    </div>
  );
}
