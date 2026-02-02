'use client';

import React from 'react';
import type { AISignal } from '@/types';

interface AISignalCardProps {
  signal: AISignal;
}

export default function AISignalCard({ signal }: AISignalCardProps) {
  const getSignalColor = (signalType: string) => {
    switch (signalType) {
      case 'GÜÇLÜ_AL':
      case 'AL': return 'bg-emerald-600 text-white';
      case 'NÖTR':
      case 'BEKLE': return 'bg-amber-500 text-white';
      case 'SAT':
      case 'GÜÇLÜ_SAT': return 'bg-red-600 text-white';
      default: return 'bg-slate-600 text-white';
    }
  };

  const getSignalIcon = (signalType: string) => {
    switch (signalType) {
      case 'GÜÇLÜ_AL': return '🚀';
      case 'AL': return '📈';
      case 'NÖTR':
      case 'BEKLE': return '➖';
      case 'SAT': return '📉';
      case 'GÜÇLÜ_SAT': return '🔻';
      default: return '❓';
    }
  };

  const scoreToGauge = (score: number) => {
    return (score - 50) / 50;
  };

  const gaugeValue = scoreToGauge(signal.score || 50);

  return (
    <div className="bg-slate-800 rounded-xl p-6 shadow-lg">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span>🤖</span> AI Sinyal Analizi
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Yapay zeka destekli birleşik sinyal analizi
          </p>
        </div>
        
        <div className={`px-6 py-3 rounded-lg ${getSignalColor(signal.combined_signal)} shadow-lg`}>
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getSignalIcon(signal.combined_signal)}</span>
            <div>
              <div className="text-xl font-bold">{signal.combined_signal}</div>
              <div className="text-sm opacity-90">Güven: %{signal.confidence?.toFixed(0) || 0}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sinyal Detayları */}
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <h4 className="font-bold text-white mb-4">Sinyal Detayları</h4>
          {signal.breakdown && signal.breakdown.length > 0 ? (
            <div className="space-y-3">
              {signal.breakdown.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-3 h-3 rounded-full ${
                      item.signal === 'AL' ? 'bg-emerald-500' :
                      item.signal === 'SAT' ? 'bg-red-500' : 'bg-amber-500'
                    }`}></span>
                    <span className="text-slate-200 font-medium">{item.indicator}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm px-3 py-1 rounded font-bold ${
                      item.signal === 'AL' ? 'bg-emerald-500/30 text-emerald-300' :
                      item.signal === 'SAT' ? 'bg-red-500/30 text-red-300' : 'bg-amber-500/30 text-amber-300'
                    }`}>
                      {item.signal}
                    </span>
                    <span className="text-slate-400 text-sm">({item.strength})</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400 text-center py-4">Detay bulunamadı</p>
          )}
        </div>

        {/* Birleşik Sinyal Gauge */}
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <h4 className="font-bold text-white mb-4">Birleşik Sinyal</h4>
          
          <div className="relative h-32 mb-4">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={`text-5xl font-bold ${
                  signal.score > 60 ? 'text-emerald-400' :
                  signal.score < 40 ? 'text-red-400' :
                  'text-amber-400'
                }`}>
                  {signal.score?.toFixed(0) || 0}
                </div>
                <div className="text-sm text-slate-400 font-medium">Skor</div>
              </div>
            </div>
            <svg className="w-full h-full" viewBox="0 0 200 100">
              <defs>
                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#ef4444" />
                  <stop offset="50%" stopColor="#f59e0b" />
                  <stop offset="100%" stopColor="#22c55e" />
                </linearGradient>
              </defs>
              <path
                d="M 20 90 A 80 80 0 0 1 180 90"
                fill="none"
                stroke="url(#gaugeGradient)"
                strokeWidth="14"
                strokeLinecap="round"
                opacity="0.3"
              />
              <path
                d="M 20 90 A 80 80 0 0 1 180 90"
                fill="none"
                stroke="url(#gaugeGradient)"
                strokeWidth="14"
                strokeLinecap="round"
                strokeDasharray={`${((gaugeValue + 1) / 2) * 251.2} 251.2`}
              />
              <line
                x1="100"
                y1="90"
                x2={100 + 60 * Math.cos(Math.PI * (1 - (gaugeValue + 1) / 2))}
                y2={90 - 60 * Math.sin(Math.PI * (1 - (gaugeValue + 1) / 2))}
                stroke="white"
                strokeWidth="4"
                strokeLinecap="round"
              />
              <circle cx="100" cy="90" r="8" fill="white" />
            </svg>
          </div>

          <div className="flex justify-between text-sm text-slate-400 px-2 font-medium">
            <span>Güçlü Sat</span>
            <span>Nötr</span>
            <span>Güçlü Al</span>
          </div>
        </div>
      </div>

      {/* Sinyal İstatistikleri */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-700/50 rounded-lg p-4 text-center border border-slate-600">
          <div className="text-sm text-slate-400 mb-1">Sinyal Uyumu</div>
          <div className="text-2xl font-bold text-white">%{signal.signal_agreement?.toFixed(0) || 0}</div>
        </div>
        <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-4 text-center">
          <div className="text-sm text-emerald-300 mb-1">Yükseliş Sinyali</div>
          <div className="text-2xl font-bold text-emerald-400">{signal.bullish_signals || 0}</div>
        </div>
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 text-center">
          <div className="text-sm text-red-300 mb-1">Düşüş Sinyali</div>
          <div className="text-2xl font-bold text-red-400">{signal.bearish_signals || 0}</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4 text-center border border-slate-600">
          <div className="text-sm text-slate-400 mb-1">Nötr Sinyal</div>
          <div className="text-2xl font-bold text-white">{signal.neutral_signals || 0}</div>
        </div>
      </div>

      {/* Risk & Giriş Zamanı */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <div className="text-sm text-slate-400 mb-1">Risk Seviyesi</div>
          <div className={`text-lg font-bold ${
            signal.risk_level === 'düşük' ? 'text-emerald-400' :
            signal.risk_level === 'orta' ? 'text-amber-400' : 'text-red-400'
          }`}>
            {signal.risk_level?.toUpperCase() || 'Bilinmiyor'}
          </div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
          <div className="text-sm text-slate-400 mb-1">Giriş Zamanlaması</div>
          <div className="text-lg font-bold text-white">{signal.entry_timing || 'Bilinmiyor'}</div>
        </div>
      </div>

      {/* Öneri */}
      <div className="mt-6 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
        <h4 className="font-bold text-blue-300 mb-2 flex items-center gap-2">
          <span>💡</span> Öneri
        </h4>
        <p className="text-slate-200">{signal.recommendation || 'Öneri bulunamadı'}</p>
      </div>

      {/* Güven Göstergesi */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-slate-400 font-medium">Sinyal Güveni</span>
          <span className={`font-bold ${
            (signal.confidence || 0) > 70 ? 'text-emerald-400' :
            (signal.confidence || 0) > 50 ? 'text-amber-400' : 'text-red-400'
          }`}>
            %{signal.confidence?.toFixed(0) || 0}
          </span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              (signal.confidence || 0) > 70 ? 'bg-emerald-500' :
              (signal.confidence || 0) > 50 ? 'bg-amber-500' : 'bg-red-500'
            }`}
            style={{ width: `${signal.confidence || 0}%` }}
          />
        </div>
      </div>
    </div>
  );
}
