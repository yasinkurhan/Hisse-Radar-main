'use client';

import React, { useState, useEffect } from 'react';
import { getProAnalysis } from '@/lib/api';
import type { ProAnalysis, Period } from '@/types';
import IchimokuIndicator from './IchimokuIndicator';
import RiskMetricsCard from './RiskMetricsCard';
import CandlestickPatterns from './CandlestickPatterns';
import AISignalCard from './AISignalCard';
import SuperTrendIndicator from './SuperTrendIndicator';
import VWAPIndicator from './VWAPIndicator';
import DivergenceIndicator from './DivergenceIndicator';

interface ProAnalysisDashboardProps {
  symbol: string;
  initialPeriod?: Period;
}

export default function ProAnalysisDashboard({ 
  symbol, 
  initialPeriod = '6mo' 
}: ProAnalysisDashboardProps) {
  const [analysis, setAnalysis] = useState<ProAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>(initialPeriod);
  const [activeTab, setActiveTab] = useState<'overview' | 'indicators' | 'patterns' | 'risk'>('overview');

  useEffect(() => {
    loadAnalysis();
  }, [symbol, period]);

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProAnalysis(symbol, period);
      setAnalysis(data as ProAnalysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analiz yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-surface rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-surface rounded-lg p-6">
        <div className="text-center text-red-400 py-8">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>{error}</p>
          <button 
            onClick={loadAnalysis}
            className="mt-4 px-4 py-2 bg-accent text-white rounded hover:bg-accent/80"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  // API yanıt yapısına göre verileri al
  const ichimoku = analysis.pro_indicators?.ichimoku;
  const supertrend = analysis.pro_indicators?.supertrend;
  const vwap = analysis.pro_indicators?.vwap;
  const divergence = analysis.divergence_analysis;
  const candlestick = analysis.candlestick_analysis;
  const risk = analysis.risk_analysis;

  const tabs = [
    { id: 'overview', label: 'Genel Bakış', icon: '📊' },
    { id: 'indicators', label: 'Göstergeler', icon: '📈' },
    { id: 'patterns', label: 'Formasyonlar', icon: '🕯️' },
    { id: 'risk', label: 'Risk Analizi', icon: '⚠️' },
  ] as const;

  const periods: { value: Period; label: string }[] = [
    { value: '1mo', label: '1 Ay' },
    { value: '3mo', label: '3 Ay' },
    { value: '6mo', label: '6 Ay' },
    { value: '1y', label: '1 Yıl' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <span className="text-blue-400">PRO</span> Analiz
              <span className="text-base font-normal text-slate-400">- {symbol}</span>
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              Gelişmiş teknik göstergeler ve AI destekli analiz
            </p>
          </div>
          
          {/* Period Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400 font-medium">Periyot:</span>
            <div className="flex gap-1">
              {periods.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setPeriod(p.value)}
                  className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${
                    period === p.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mt-4 border-t border-slate-700 pt-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Signal - Büyük kart */}
          {analysis.ai_signal && (
            <div className="lg:col-span-2">
              <AISignalCard signal={analysis.ai_signal} />
            </div>
          )}
          
          {/* Ichimoku */}
          {ichimoku && <IchimokuIndicator data={ichimoku} />}
          
          {/* SuperTrend */}
          {supertrend && <SuperTrendIndicator data={supertrend} />}
          
          {/* Quick Risk Summary */}
          <div className="bg-slate-800 rounded-xl p-5 shadow-lg border border-slate-700">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span>⚠️</span> Hızlı Risk Özeti
            </h3>
            {risk ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <div className="text-sm text-slate-400 mb-1">Sharpe Oranı</div>
                  <div className={`text-2xl font-bold ${
                    (risk.sharpe_ratio?.sharpe_ratio ?? 0) > 1 ? 'text-emerald-400' : 
                    (risk.sharpe_ratio?.sharpe_ratio ?? 0) > 0 ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {(risk.sharpe_ratio?.sharpe_ratio ?? 0).toFixed(2)}
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <div className="text-sm text-slate-400 mb-1">Max Drawdown</div>
                  <div className="text-2xl font-bold text-red-400">
                    {(risk.max_drawdown?.max_drawdown_pct ?? 0).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <div className="text-sm text-slate-400 mb-1">VaR (95%)</div>
                  <div className="text-2xl font-bold text-amber-400">
                    {(risk.var_95?.var_pct ?? 0).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                  <div className="text-sm text-slate-400 mb-1">Beta</div>
                  <div className={`text-2xl font-bold ${
                    (risk.beta_analysis?.beta ?? 1) > 1.2 ? 'text-red-400' : 
                    (risk.beta_analysis?.beta ?? 1) < 0.8 ? 'text-emerald-400' : 'text-amber-400'
                  }`}>
                    {(risk.beta_analysis?.beta ?? 0).toFixed(2)}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-slate-400 text-center py-4">Risk verisi yüklenemedi</p>
            )}
          </div>
          
          {/* Position Advice */}
          {analysis.position_advice && (
            <div className="bg-slate-800 rounded-xl p-5 shadow-lg border border-slate-700">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>💡</span> Pozisyon Önerisi
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-slate-700">
                  <span className="text-slate-400">Önerilen Pozisyon</span>
                  <span className="font-bold text-white text-lg">%{analysis.position_advice.suggested_position_pct}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700">
                  <span className="text-slate-400">Stop Loss</span>
                  <span className="font-bold text-red-400 text-lg">{analysis.position_advice.suggested_stop_loss?.toFixed(2)} TL</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700">
                  <span className="text-slate-400">Hedef Fiyat</span>
                  <span className="font-bold text-emerald-400 text-lg">{analysis.position_advice.suggested_target?.toFixed(2)} TL</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-slate-400">Risk/Ödül</span>
                  <span className="font-bold text-white text-lg">{analysis.position_advice.risk_reward_ratio?.toFixed(2)}</span>
                </div>
                <div className="mt-3 p-3 bg-blue-500/20 border border-blue-500/30 rounded-lg text-sm text-slate-200">
                  {analysis.position_advice.advice}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'indicators' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {ichimoku && <IchimokuIndicator data={ichimoku} detailed />}
          {supertrend && <SuperTrendIndicator data={supertrend} detailed />}
          {vwap && <VWAPIndicator data={vwap} />}
          {divergence && <DivergenceIndicator data={divergence} />}
        </div>
      )}

      {activeTab === 'patterns' && candlestick && (
        <CandlestickPatterns data={candlestick} />
      )}

      {activeTab === 'risk' && risk && (
        <RiskMetricsCard metrics={risk} symbol={symbol} />
      )}
    </div>
  );
}
