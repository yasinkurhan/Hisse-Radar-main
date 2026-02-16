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
    return 'text-slate-400';
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
    <div className="bg-slate-800 rounded-xl p-5 shadow-lg border border-slate-700">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>🔀</span> Diverjans Analizi
      </h3>

      {/* RSI Diverjans */}
      <div className="bg-slate-700/50 rounded-lg p-4 mb-4 border border-slate-600">
        <h4 className="font-bold text-white mb-3">RSI Diverjansı</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Durum</span>
            <span className={`font-bold ${getDivergenceColor(rsi?.divergence)}`}>
              {getDivergenceLabel(rsi?.divergence)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Sinyal</span>
            <span className={`px-3 py-1 rounded text-sm font-bold ${
              rsi?.signal === 'AL' ? 'bg-emerald-500/30 text-emerald-400' :
              rsi?.signal === 'SAT' ? 'bg-red-500/30 text-red-400' :
              'bg-slate-600 text-slate-300'
            }`}>
              {rsi?.signal || 'BEKLE'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Güç</span>
            <span className="font-bold text-white">{rsi?.strength || 0}</span>
          </div>
          {rsi?.description && (
            <div className="mt-2 p-3 bg-slate-800 rounded text-sm text-slate-300">
              {rsi.description}
            </div>
          )}
        </div>
      </div>

      {/* MACD Diverjans */}
      <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
        <h4 className="font-bold text-white mb-3">MACD Diverjansı</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Durum</span>
            <span className={`font-bold ${getDivergenceColor(macd?.divergence)}`}>
              {getDivergenceLabel(macd?.divergence)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Sinyal</span>
            <span className={`px-3 py-1 rounded text-sm font-bold ${
              macd?.signal === 'AL' ? 'bg-emerald-500/30 text-emerald-400' :
              macd?.signal === 'SAT' ? 'bg-red-500/30 text-red-400' :
              'bg-slate-600 text-slate-300'
            }`}>
              {macd?.signal || 'BEKLE'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Güç</span>
            <span className="font-bold text-white">{macd?.strength || 0}</span>
          </div>
          {macd?.description && (
            <div className="mt-2 p-3 bg-slate-800 rounded text-sm text-slate-300">
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
          <p className="text-sm text-slate-300 mt-2">
            Diverjanslar trend dönüşünün erken sinyalleri olabilir.
          </p>
        </div>
      )}
    </div>
  );
}
