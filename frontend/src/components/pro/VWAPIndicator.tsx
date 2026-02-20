'use client';

import React from 'react';
import type { VWAPData } from '@/types';

interface VWAPIndicatorProps {
  data: VWAPData;
}

export default function VWAPIndicator({ data }: VWAPIndicatorProps) {
  const getZoneColor = (zone: string) => {
    if (zone?.includes('üst') || zone?.includes('above')) return 'text-emerald-400';
    if (zone?.includes('alt') || zone?.includes('below')) return 'text-red-400';
    return 'text-amber-400';
  };

  return (
    <div className="bg-white rounded-xl p-5 shadow-lg border border-gray-200">
      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <span>📈</span> VWAP Analizi
      </h3>

      {/* Ana VWAP */}
      <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-500">VWAP</span>
          <span className="text-2xl font-bold text-blue-400">
            {data.vwap?.toFixed(2) || '-'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-gray-500">Sapma</span>
          <span className={`font-bold ${data.deviation_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.deviation_pct > 0 ? '+' : ''}{data.deviation_pct?.toFixed(2) || 0}%
          </span>
        </div>
      </div>

      {/* Bantlar */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-3">
          <div className="text-sm text-emerald-300">Üst Bant 1</div>
          <div className="text-lg font-bold text-emerald-400">
            {data.upper_band_1?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-3">
          <div className="text-sm text-emerald-300">Üst Bant 2</div>
          <div className="text-lg font-bold text-emerald-400">
            {data.upper_band_2?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3">
          <div className="text-sm text-red-300">Alt Bant 1</div>
          <div className="text-lg font-bold text-red-400">
            {data.lower_band_1?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3">
          <div className="text-sm text-red-300">Alt Bant 2</div>
          <div className="text-lg font-bold text-red-400">
            {data.lower_band_2?.toFixed(2) || '-'}
          </div>
        </div>
      </div>

      {/* Sinyal ve Bölge */}
      <div className="space-y-2">
        <div className="flex items-center justify-between py-2 border-b border-gray-200">
          <span className="text-gray-500">Sinyal</span>
          <span className={`font-bold px-3 py-1 rounded ${
            data.signal === 'AL' ? 'bg-emerald-500/30 text-emerald-400' : 
            data.signal === 'SAT' ? 'bg-red-500/30 text-red-400' : 'bg-amber-500/30 text-amber-400'
          }`}>
            {data.signal || 'NÖTR'}
          </span>
        </div>
        <div className="flex items-center justify-between py-2 border-b border-gray-200">
          <span className="text-gray-500">Bölge</span>
          <span className={`font-medium ${getZoneColor(data.zone)}`}>
            {data.zone || '-'}
          </span>
        </div>
        <div className="flex items-center justify-between py-2">
          <span className="text-gray-500">Trend</span>
          <span className={`font-medium ${data.trend === 'bullish' ? 'text-emerald-400' : data.trend === 'bearish' ? 'text-red-400' : 'text-amber-400'}`}>
            {data.trend === 'bullish' ? 'Yükseliş' : data.trend === 'bearish' ? 'Düşüş' : data.trend || '-'}
          </span>
        </div>
      </div>
    </div>
  );
}
