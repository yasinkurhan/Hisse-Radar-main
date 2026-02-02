'use client';

import React from 'react';
import type { FearGreedIndex } from '@/types';

interface FearGreedGaugeProps {
  data: FearGreedIndex;
  compact?: boolean;
}

export default function FearGreedGauge({ data, compact = false }: FearGreedGaugeProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'extreme_fear': return '#ef4444';
      case 'fear': return '#f97316';
      case 'neutral': return '#eab308';
      case 'greed': return '#84cc16';
      case 'extreme_greed': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getStatusBgClass = (status: string) => {
    switch (status) {
      case 'extreme_fear': return 'bg-red-500/10 border-red-500/20 text-red-400';
      case 'fear': return 'bg-orange-500/10 border-orange-500/20 text-orange-400';
      case 'neutral': return 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400';
      case 'greed': return 'bg-lime-500/10 border-lime-500/20 text-lime-400';
      case 'extreme_greed': return 'bg-green-500/10 border-green-500/20 text-green-400';
      default: return 'bg-gray-500/10 border-gray-500/20 text-gray-400';
    }
  };

  const statusColor = getStatusColor(data.status);

  if (compact) {
    return (
      <div className={`p-4 rounded-lg border ${getStatusBgClass(data.status)}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm opacity-75">Korku & Açgözlülük</div>
            <div className="text-xl font-bold">{data.status_tr}</div>
          </div>
          <div className="text-3xl font-bold">{data.value}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-lg p-6">
      <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <span>😱</span> Korku & Açgözlülük Endeksi
      </h3>

      {/* Main Gauge */}
      <div className="relative h-48 mb-4">
        <svg className="w-full h-full" viewBox="0 0 200 120">
          <defs>
            <linearGradient id="fearGreedGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="25%" stopColor="#f97316" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="75%" stopColor="#84cc16" />
              <stop offset="100%" stopColor="#22c55e" />
            </linearGradient>
          </defs>
          
          {/* Background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#fearGreedGradient)"
            strokeWidth="16"
            strokeLinecap="round"
          />
          
          {/* Value indicator */}
          <circle
            cx={20 + ((data.value || 0) / 100) * 160}
            cy={100 - Math.sin(Math.PI * ((data.value || 0) / 100)) * 80}
            r="8"
            fill="white"
            stroke={statusColor}
            strokeWidth="3"
          />
          
          {/* Center text */}
          <text x="100" y="75" textAnchor="middle" className="fill-current text-4xl font-bold">
            {data.value ?? 0}
          </text>
          <text x="100" y="95" textAnchor="middle" className="fill-muted text-sm">
            {data.status_tr}
          </text>
        </svg>
        
        {/* Scale labels */}
        <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-muted px-4">
          <span>0 - Aşırı Korku</span>
          <span>50 - Nötr</span>
          <span>100 - Aşırı Açgözlülük</span>
        </div>
      </div>

      {/* Status Badge */}
      <div className={`p-4 rounded-lg border mb-6 ${getStatusBgClass(data.status)}`}>
        <div className="flex items-center justify-center gap-3">
          <span className="text-3xl">
            {data.status === 'extreme_fear' && '😱'}
            {data.status === 'fear' && '😰'}
            {data.status === 'neutral' && '😐'}
            {data.status === 'greed' && '😏'}
            {data.status === 'extreme_greed' && '🤑'}
          </span>
          <div className="text-center">
            <div className="text-2xl font-bold">{data.status_tr}</div>
            <div className="text-sm opacity-75">Piyasa Duyarlılığı</div>
          </div>
        </div>
      </div>

      {/* Components */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted">Endeks Bileşenleri</h4>
        
        {data.components && Object.entries(data.components).map(([key, value]) => {
          const labels: Record<string, string> = {
            market_momentum: 'Piyasa Momentumu',
            market_breadth: 'Piyasa Genişliği',
            volatility: 'Volatilite',
            safe_haven: 'Güvenli Liman Talebi',
            put_call_ratio: 'Put/Call Oranı'
          };
          
          const numValue = typeof value === 'number' ? value : 50;
          
          return (
            <div key={key}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-muted">{labels[key] || key}</span>
                <span className={
                  numValue > 60 ? 'text-up' :
                  numValue < 40 ? 'text-down' : 'text-yellow-400'
                }>{numValue.toFixed(0)}</span>
              </div>
              <div className="h-2 bg-card rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    numValue > 60 ? 'bg-up' :
                    numValue < 40 ? 'bg-down' : 'bg-yellow-400'
                  }`}
                  style={{ width: `${numValue}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Interpretation */}
      <div className="mt-6 p-4 bg-card rounded-lg">
        <h4 className="font-semibold mb-2">📊 Yorum</h4>
        <p className="text-sm text-muted">
          {data.status === 'extreme_fear' && (
            'Piyasada aşırı korku hakim. Tarihsel olarak bu seviyeler alım fırsatı sunabilir, ancak düşüş devam edebilir.'
          )}
          {data.status === 'fear' && (
            'Piyasada korku hakim. Temkinli olmak gerekli, ancak kaliteli hisselerde fırsatlar olabilir.'
          )}
          {data.status === 'neutral' && (
            'Piyasa duyarlılığı nötr seviyede. Belirgin bir yön baskısı yok.'
          )}
          {data.status === 'greed' && (
            'Piyasada açgözlülük artıyor. Dikkatli olmak ve kar realizasyonu düşünmek mantıklı olabilir.'
          )}
          {data.status === 'extreme_greed' && (
            'Piyasada aşırı açgözlülük hakim. Tarihsel olarak bu seviyeler düzeltme öncesi görülür. Risk yönetimi önemli.'
          )}
        </p>
      </div>
    </div>
  );
}
