'use client';

import React from 'react';
import type { RiskMetrics } from '@/types';

interface RiskMetricsCardProps {
  metrics: RiskMetrics;
  symbol: string;
}

export default function RiskMetricsCard({ metrics, symbol }: RiskMetricsCardProps) {
  const getInterpretationColor = (interp: string) => {
    if (interp?.includes('iyi') || interp?.includes('güçlü') || interp?.includes('pozitif')) return 'text-emerald-400';
    if (interp?.includes('zayıf') || interp?.includes('negatif') || interp?.includes('yüksek_risk')) return 'text-red-400';
    return 'text-amber-400';
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span>⚠️</span> Risk Analizi
          <span className="text-base font-normal text-gray-500">- {symbol}</span>
        </h3>
        <div className={`px-4 py-2 rounded-lg font-bold ${
          metrics.risk_level?.includes('düşük') ? 'bg-emerald-500/30 text-emerald-400' :
          metrics.risk_level?.includes('orta') ? 'bg-amber-500/30 text-amber-400' :
          'bg-red-500/30 text-red-400'
        }`}>
          Risk: {metrics.risk_level?.toUpperCase() || 'Bilinmiyor'}
        </div>
      </div>

      {/* Risk Score */}
      <div className="bg-gray-50 rounded-lg p-5 mb-6 border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-500">Risk Skoru</span>
          <span className={`text-4xl font-bold ${
            metrics.risk_score < 40 ? 'text-emerald-400' :
            metrics.risk_score < 70 ? 'text-amber-400' : 'text-red-400'
          }`}>
            {metrics.risk_score || 0}
          </span>
        </div>
        <div className="h-4 bg-white rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              metrics.risk_score < 40 ? 'bg-emerald-500' :
              metrics.risk_score < 70 ? 'bg-amber-500' : 'bg-red-500'
            }`}
            style={{ width: `${metrics.risk_score || 0}%` }}
          />
        </div>
      </div>

      {/* Ana Metrikler */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {/* Sharpe Ratio */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Sharpe Oranı</div>
          <div className={`text-2xl font-bold ${getInterpretationColor(metrics.sharpe_ratio?.interpretation)}`}>
            {metrics.sharpe_ratio?.sharpe_ratio?.toFixed(2) || '-'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics.sharpe_ratio?.interpretation || '-'}
          </div>
        </div>

        {/* Sortino Ratio */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Sortino Oranı</div>
          <div className={`text-2xl font-bold ${getInterpretationColor(metrics.sortino_ratio?.interpretation)}`}>
            {metrics.sortino_ratio?.sortino_ratio?.toFixed(2) || '-'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics.sortino_ratio?.interpretation || '-'}
          </div>
        </div>

        {/* Calmar Ratio */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Calmar Oranı</div>
          <div className={`text-2xl font-bold ${getInterpretationColor(metrics.calmar_ratio?.interpretation)}`}>
            {metrics.calmar_ratio?.calmar_ratio?.toFixed(2) || '-'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics.calmar_ratio?.interpretation || '-'}
          </div>
        </div>

        {/* Max Drawdown */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Max Drawdown</div>
          <div className="text-2xl font-bold text-red-400">
            %{metrics.max_drawdown?.max_drawdown_pct?.toFixed(1) || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Güncel: %{metrics.max_drawdown?.current_drawdown_pct?.toFixed(1) || 0}
          </div>
        </div>

        {/* VaR 95% */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">VaR (95%)</div>
          <div className="text-2xl font-bold text-amber-400">
            %{metrics.var_95?.var_pct?.toFixed(2) || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            CVaR: %{metrics.var_95?.cvar_pct?.toFixed(2) || 0}
          </div>
        </div>

        {/* VaR 99% */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">VaR (99%)</div>
          <div className="text-2xl font-bold text-red-400">
            %{metrics.var_99?.var_pct?.toFixed(2) || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            CVaR: %{metrics.var_99?.cvar_pct?.toFixed(2) || 0}
          </div>
        </div>

        {/* Beta */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Beta</div>
          <div className={`text-2xl font-bold ${
            (metrics.beta_analysis?.beta || 1) > 1.2 ? 'text-red-400' :
            (metrics.beta_analysis?.beta || 1) < 0.8 ? 'text-emerald-400' : 'text-amber-400'
          }`}>
            {metrics.beta_analysis?.beta?.toFixed(2) || '-'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics.beta_analysis?.interpretation || '-'}
          </div>
        </div>

        {/* Volatilite */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Volatilite (Yıllık)</div>
          <div className={`text-2xl font-bold ${
            (metrics.volatility?.annualized_pct || 0) > 30 ? 'text-red-400' :
            (metrics.volatility?.annualized_pct || 0) > 20 ? 'text-amber-400' : 'text-emerald-400'
          }`}>
            %{metrics.volatility?.annualized_pct?.toFixed(1) || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {metrics.volatility?.level || '-'} | {metrics.volatility?.trend || '-'}
          </div>
        </div>
      </div>

      {/* VaR Açıklama */}
      {metrics.var_95?.explanation && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
          <h4 className="font-bold text-gray-900 mb-2">📊 VaR Açıklaması</h4>
          <p className="text-sm text-gray-600">{metrics.var_95.explanation}</p>
        </div>
      )}

      {/* Öneri */}
      {metrics.recommendation && (
        <div className={`p-4 rounded-lg border ${
          metrics.risk_level?.includes('düşük') ? 'bg-emerald-500/20 border-emerald-500/30' :
          metrics.risk_level?.includes('orta') ? 'bg-amber-500/20 border-amber-500/30' :
          'bg-red-500/20 border-red-500/30'
        }`}>
          <h4 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
            <span>💡</span> Öneri
          </h4>
          <p className="text-gray-700">{metrics.recommendation}</p>
        </div>
      )}
    </div>
  );
}
