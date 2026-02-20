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
import NewsImpactCard from './NewsImpactCard';

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
  const [activeTab, setActiveTab] = useState<'overview' | 'indicators' | 'patterns' | 'risk' | 'news'>('overview');

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
      setError(err instanceof Error ? err.message : 'Analiz yuklenemedi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="text-center text-red-500 py-8">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-700">{error}</p>
          <button 
            onClick={loadAnalysis}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const ichimoku = analysis.pro_indicators?.ichimoku;
  const supertrend = analysis.pro_indicators?.supertrend;
  const vwap = analysis.pro_indicators?.vwap;
  const divergence = analysis.divergence_analysis;
  const candlestick = analysis.candlestick_analysis;
  const risk = analysis.risk_analysis;
  const newsImpact = (analysis as any).news_impact;

  const tabs = [
    { id: 'overview', label: 'Genel Bakis', icon: '' },
    { id: 'indicators', label: 'Gostergeler', icon: '' },
    { id: 'patterns', label: 'Formasyonlar', icon: '' },
    { id: 'risk', label: 'Risk Analizi', icon: '' },
    { id: 'news', label: 'Haber Etkisi', icon: '' },
  ] as const;

  const periods: { value: Period; label: string }[] = [
    { value: '1mo', label: '1 Ay' },
    { value: '3mo', label: '3 Ay' },
    { value: '6mo', label: '6 Ay' },
    { value: '1y', label: '1 Yil' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <span className="text-purple-600">PRO</span> Analiz
              <span className="text-base font-normal text-gray-500">- {symbol}</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Gelismis teknik gostergeler ve AI destekli analiz
            </p>
          </div>
          
          {/* Period Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 font-medium">Periyot:</span>
            <div className="flex gap-1">
              {periods.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setPeriod(p.value)}
                  className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${
                    period === p.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mt-4 border-t border-gray-200 pt-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
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
          {/* AI Signal */}
          {analysis.ai_signal && (
            <div className="lg:col-span-2">
              <AISignalCard signal={analysis.ai_signal} />
            </div>
          )}
          
          {/* Ichimoku */}
          {ichimoku && <IchimokuIndicator data={ichimoku} />}
          
          {/* SuperTrend */}
          {supertrend && <SuperTrendIndicator data={supertrend} />}
          
          {/* News Impact Summary */}
          {newsImpact && newsImpact.has_data && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                <span></span> Haber Etkisi
                <span className={`ml-auto text-sm px-3 py-1 rounded-lg font-bold ${
                  newsImpact.sentiment_label === 'Cok Olumlu' || newsImpact.sentiment_label === 'Olumlu' 
                    ? 'bg-green-100 text-green-700' 
                    : newsImpact.sentiment_label === 'Cok Olumsuz' || newsImpact.sentiment_label === 'Olumsuz'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-amber-100 text-amber-700'
                }`}>
                  {newsImpact.sentiment_label}
                </span>
              </h3>
              <p className="text-sm text-gray-600 mb-3">{newsImpact.impact_summary}</p>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-green-50 rounded-lg p-2 text-center border border-green-100">
                  <div className="text-lg font-bold text-green-600">{newsImpact.positive_count || 0}</div>
                  <div className="text-xs text-gray-500">Olumlu</div>
                </div>
                <div className="bg-amber-50 rounded-lg p-2 text-center border border-amber-100">
                  <div className="text-lg font-bold text-amber-600">{newsImpact.neutral_count || 0}</div>
                  <div className="text-xs text-gray-500">Notr</div>
                </div>
                <div className="bg-red-50 rounded-lg p-2 text-center border border-red-100">
                  <div className="text-lg font-bold text-red-600">{newsImpact.negative_count || 0}</div>
                  <div className="text-xs text-gray-500">Olumsuz</div>
                </div>
              </div>
              {(analysis.ai_signal as any)?.news_impact_bonus !== undefined && (analysis.ai_signal as any).news_impact_bonus !== 0 && (
                <div className={`mt-3 text-sm font-medium flex items-center gap-1 ${
                  (analysis.ai_signal as any).news_impact_bonus > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <span>{(analysis.ai_signal as any).news_impact_bonus > 0 ? '' : ''}</span>
                  AI Skor Etkisi: {(analysis.ai_signal as any).news_impact_bonus > 0 ? '+' : ''}{(analysis.ai_signal as any).news_impact_bonus} puan
                </div>
              )}
              <button 
                onClick={() => setActiveTab('news')}
                className="mt-3 w-full text-sm text-blue-600 hover:text-blue-700 font-medium text-center py-1"
              >
                Detayli Haber Analizi 
              </button>
            </div>
          )}

          {/* Quick Risk Summary */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span></span> Hizli Risk Ozeti
            </h3>
            {risk ? (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="text-sm text-gray-500 mb-1">Sharpe Orani</div>
                  <div className={`text-2xl font-bold ${
                    (risk.sharpe_ratio?.sharpe_ratio ?? 0) > 1 ? 'text-green-600' : 
                    (risk.sharpe_ratio?.sharpe_ratio ?? 0) > 0 ? 'text-amber-600' : 'text-red-600'
                  }`}>
                    {(risk.sharpe_ratio?.sharpe_ratio ?? 0).toFixed(2)}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="text-sm text-gray-500 mb-1">Max Drawdown</div>
                  <div className="text-2xl font-bold text-red-600">
                    {(risk.max_drawdown?.max_drawdown_pct ?? 0).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="text-sm text-gray-500 mb-1">VaR (95%)</div>
                  <div className="text-2xl font-bold text-amber-600">
                    {(risk.var_95?.var_pct ?? 0).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="text-sm text-gray-500 mb-1">Beta</div>
                  <div className={`text-2xl font-bold ${
                    (risk.beta_analysis?.beta ?? 1) > 1.2 ? 'text-red-600' : 
                    (risk.beta_analysis?.beta ?? 1) < 0.8 ? 'text-green-600' : 'text-amber-600'
                  }`}>
                    {(risk.beta_analysis?.beta ?? 0).toFixed(2)}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Risk verisi yuklenemedi</p>
            )}
          </div>
          
          {/* Position Advice */}
          {analysis.position_advice && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <span></span> Pozisyon Onerisi
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-200">
                  <span className="text-gray-500">Onerilen Pozisyon</span>
                  <span className="font-bold text-gray-900 text-lg">%{analysis.position_advice.suggested_position_pct}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-200">
                  <span className="text-gray-500">Stop Loss</span>
                  <span className="font-bold text-red-600 text-lg">{analysis.position_advice.suggested_stop_loss?.toFixed(2)} TL</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-200">
                  <span className="text-gray-500">Hedef Fiyat</span>
                  <span className="font-bold text-green-600 text-lg">{analysis.position_advice.suggested_target?.toFixed(2)} TL</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-500">Risk/Odul</span>
                  <span className="font-bold text-gray-900 text-lg">{analysis.position_advice.risk_reward_ratio?.toFixed(2)}</span>
                </div>
                <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-gray-700">
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

      {activeTab === 'news' && (
        <NewsImpactCard data={newsImpact || { has_data: false, sentiment_score: 0, sentiment_label: 'Haber Yok', news_count: 0, recent_news: [], impact_summary: `${symbol} icin haber verisi bulunamadi.` }} symbol={symbol} />
      )}
    </div>
  );
}