'use client';

import React from 'react';
import type { SuperTrendData } from '@/types';

interface SuperTrendIndicatorProps {
  data: SuperTrendData;
  detailed?: boolean;
}

export default function SuperTrendIndicator({ data, detailed = false }: SuperTrendIndicatorProps) {
  const isBullish = data.direction === 'UP' || data.trend === 'yükseliş';
  
  return (
    <div className="bg-slate-800 rounded-xl p-5 shadow-lg border border-slate-700">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>📊</span> SuperTrend
      </h3>

      {/* Ana Sinyal */}
      <div className={`p-4 rounded-lg mb-4 border ${isBullish ? 'bg-emerald-500/20 border-emerald-500' : 'bg-red-500/20 border-red-500'}`}>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Sinyal</span>
          <span className={`text-xl font-bold ${isBullish ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.signal || (isBullish ? 'AL' : 'SAT')}
          </span>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-slate-400">Trend</span>
          <span className={`font-medium ${isBullish ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.trend || (isBullish ? 'Yükseliş' : 'Düşüş')}
          </span>
        </div>
      </div>

      {/* Değerler */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <div className="text-sm text-slate-400">SuperTrend Değeri</div>
          <div className={`text-xl font-bold ${isBullish ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.supertrend?.toFixed(2) || '-'}
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <div className="text-sm text-slate-400">Yön</div>
          <div className={`text-xl font-bold ${isBullish ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.direction === 'UP' ? '↑ Yukarı' : '↓ Aşağı'}
          </div>
        </div>
      </div>

      {/* Mesafe */}
      <div className="bg-slate-700/50 rounded-lg p-4 mb-4 border border-slate-600">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Fiyat Uzaklığı</span>
          <span className={`text-lg font-bold ${data.distance_pct > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.distance_pct > 0 ? '+' : ''}{data.distance_pct?.toFixed(2) || 0}%
          </span>
        </div>
      </div>

      {/* Trend Değişimi */}
      {data.trend_changed && (
        <div className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className="font-bold text-blue-300">Trend Değişimi Tespit Edildi!</span>
          </div>
        </div>
      )}

      {detailed && (
        <div className="mt-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
          <h4 className="font-bold text-white mb-3">Kullanım İpuçları</h4>
          <ul className="text-sm text-slate-300 space-y-2">
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              SuperTrend üstünde: Alım bölgesi
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              SuperTrend altında: Satım bölgesi
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              Trend değişimlerinde dikkatli olun
            </li>
            <li className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              Diğer göstergelerle teyit edin
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
