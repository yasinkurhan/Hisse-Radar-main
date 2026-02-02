'use client';

import React from 'react';
import type { IchimokuData } from '@/types';

interface IchimokuIndicatorProps {
  data: IchimokuData;
  detailed?: boolean;
}

export default function IchimokuIndicator({ data, detailed = false }: IchimokuIndicatorProps) {
  const getSignalColor = (signal: string) => {
    const s = signal?.toLowerCase() || '';
    if (s.includes('al') || s.includes('bullish') || s.includes('yükseliş')) return 'text-emerald-400';
    if (s.includes('sat') || s.includes('bearish') || s.includes('düşüş')) return 'text-red-400';
    return 'text-amber-400';
  };

  const getCloudColor = (color: string) => {
    return color === 'green' ? 'bg-emerald-500/20 border-emerald-500' : 'bg-red-500/20 border-red-500';
  };

  const translateSignal = (signal: string) => {
    const labels: Record<string, string> = {
      'bullish': 'Yükseliş',
      'bearish': 'Düşüş',
      'above': 'Bulutun Üstünde',
      'below': 'Bulutun Altında',
      'inside': 'Bulut İçinde',
      'green': 'Yeşil (Yükseliş)',
      'red': 'Kırmızı (Düşüş)'
    };
    return labels[signal?.toLowerCase()] || signal;
  };

  return (
    <div className="bg-slate-800 rounded-xl p-5 shadow-lg border border-slate-700">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>☁️</span> Ichimoku Cloud
      </h3>

      {/* Ana Sinyal */}
      <div className={`p-4 rounded-lg mb-4 border ${getCloudColor(data.cloud_color)}`}>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Genel Sinyal</span>
          <span className={`text-xl font-bold ${getSignalColor(data.signal)}`}>
            {data.signal || 'Bilinmiyor'}
          </span>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-slate-400">Trend</span>
          <span className={`font-medium ${getSignalColor(data.trend)}`}>
            {data.trend || 'Bilinmiyor'}
          </span>
        </div>
      </div>

      {/* Güncel Değerler */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
          <div className="text-sm text-slate-400">Tenkan-sen</div>
          <div className="text-lg font-bold text-blue-400">
            {data.tenkan_sen?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
          <div className="text-sm text-slate-400">Kijun-sen</div>
          <div className="text-lg font-bold text-red-400">
            {data.kijun_sen?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
          <div className="text-sm text-slate-400">Senkou Span A</div>
          <div className="text-lg font-bold text-emerald-400">
            {data.senkou_span_a?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 border border-slate-600">
          <div className="text-sm text-slate-400">Senkou Span B</div>
          <div className="text-lg font-bold text-orange-400">
            {data.senkou_span_b?.toFixed(2) || '-'}
          </div>
        </div>
      </div>

      {/* Sinyaller */}
      <div className="space-y-2">
        <div className="flex items-center justify-between py-2 border-b border-slate-700">
          <span className="text-slate-400">TK Kesişimi</span>
          <span className={`font-medium ${getSignalColor(data.tk_cross)}`}>
            {translateSignal(data.tk_cross)}
          </span>
        </div>
        <div className="flex items-center justify-between py-2 border-b border-slate-700">
          <span className="text-slate-400">Fiyat vs Bulut</span>
          <span className={`font-medium ${getSignalColor(data.price_vs_cloud)}`}>
            {translateSignal(data.price_vs_cloud)}
          </span>
        </div>
        <div className="flex items-center justify-between py-2 border-b border-slate-700">
          <span className="text-slate-400">Bulut Rengi</span>
          <span className={data.cloud_color === 'green' ? 'text-emerald-400 font-medium' : 'text-red-400 font-medium'}>
            {translateSignal(data.cloud_color)}
          </span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-slate-400">Sinyal Gücü</span>
          <span className="font-bold text-white">{data.strength || 0}</span>
        </div>
      </div>

      {detailed && (
        <div className="mt-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
          <h4 className="font-bold text-white mb-3">Bulut Detayları</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Bulut Üst:</span>
              <span className="text-white font-medium">{data.cloud_top?.toFixed(2) || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Bulut Alt:</span>
              <span className="text-white font-medium">{data.cloud_bottom?.toFixed(2) || '-'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Kalınlık:</span>
              <span className="text-white font-medium">%{data.cloud_thickness_pct?.toFixed(1) || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Chikou Span:</span>
              <span className="text-white font-medium">{data.chikou_span?.toFixed(2) || '-'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
