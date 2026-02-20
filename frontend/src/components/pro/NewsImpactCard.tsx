'use client';

import React from 'react';

interface NewsItem {
  title: string;
  date: string;
  category: string;
  sentiment_score: number;
  impact: string;
  impact_icon: string;
  url: string;
}

interface NewsImpactData {
  has_data: boolean;
  sentiment_score: number;
  sentiment_label: string;
  news_count: number;
  positive_count?: number;
  negative_count?: number;
  neutral_count?: number;
  strong_positive_count?: number;
  strong_negative_count?: number;
  impact_summary: string;
  recent_news?: NewsItem[];
}

interface NewsImpactCardProps {
  data: NewsImpactData;
  symbol: string;
}

export default function NewsImpactCard({ data, symbol }: NewsImpactCardProps) {
  const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-emerald-400';
    if (score > 0.1) return 'text-emerald-300';
    if (score < -0.3) return 'text-red-400';
    if (score < -0.1) return 'text-red-300';
    return 'text-amber-400';
  };

  const getSentimentBg = (score: number) => {
    if (score > 0.3) return 'bg-emerald-500/20 border-emerald-500/30';
    if (score > 0.1) return 'bg-emerald-500/10 border-emerald-500/20';
    if (score < -0.3) return 'bg-red-500/20 border-red-500/30';
    if (score < -0.1) return 'bg-red-500/10 border-red-500/20';
    return 'bg-amber-500/10 border-amber-500/20';
  };

  const getLabelBadge = (label: string) => {
    switch (label) {
      case 'Çok Olumlu': return 'bg-emerald-600 text-gray-900';
      case 'Olumlu': return 'bg-emerald-500/30 text-emerald-300';
      case 'Çok Olumsuz': return 'bg-red-600 text-gray-900';
      case 'Olumsuz': return 'bg-red-500/30 text-red-300';
      case 'Nötr': return 'bg-amber-500/30 text-amber-300';
      default: return 'bg-gray-200 text-gray-600';
    }
  };

  const getSentimentIcon = (label: string) => {
    switch (label) {
      case 'Çok Olumlu': return '🚀';
      case 'Olumlu': return '📈';
      case 'Çok Olumsuz': return '🔻';
      case 'Olumsuz': return '📉';
      case 'Nötr': return '➖';
      default: return '❓';
    }
  };

  const getItemSentimentDot = (score: number) => {
    if (score > 0.3) return 'bg-emerald-500';
    if (score > 0.1) return 'bg-emerald-400';
    if (score < -0.3) return 'bg-red-500';
    if (score < -0.1) return 'bg-red-400';
    return 'bg-amber-400';
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateStr;
    }
  };

  if (!data.has_data) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <span>📰</span> Haber Etkisi
        </h3>
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
          </svg>
          <p>{data.impact_summary || `${symbol} için son 30 günde KAP bildirimi bulunamadı.`}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <span>📰</span> Haber Etkisi Analizi
        </h3>
        <span className={`px-4 py-1.5 rounded-lg text-sm font-bold ${getLabelBadge(data.sentiment_label)}`}>
          {getSentimentIcon(data.sentiment_label)} {data.sentiment_label}
        </span>
      </div>

      {/* Sentiment Summary */}
      <div className={`rounded-lg p-4 border mb-5 ${getSentimentBg(data.sentiment_score)}`}>
        <p className="text-gray-700 text-sm leading-relaxed">{data.impact_summary}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <div className="bg-gray-50 rounded-lg p-3 text-center border border-gray-200">
          <div className="text-sm text-gray-500 mb-1">Toplam Haber</div>
          <div className="text-2xl font-bold text-gray-900">{data.news_count}</div>
        </div>
        <div className="bg-emerald-500/10 rounded-lg p-3 text-center border border-emerald-500/20">
          <div className="text-sm text-emerald-300 mb-1">Olumlu</div>
          <div className="text-2xl font-bold text-emerald-400">{data.positive_count || 0}</div>
        </div>
        <div className="bg-red-500/10 rounded-lg p-3 text-center border border-red-500/20">
          <div className="text-sm text-red-300 mb-1">Olumsuz</div>
          <div className="text-2xl font-bold text-red-400">{data.negative_count || 0}</div>
        </div>
        <div className="bg-amber-500/10 rounded-lg p-3 text-center border border-amber-500/20">
          <div className="text-sm text-amber-300 mb-1">Nötr</div>
          <div className="text-2xl font-bold text-amber-400">{data.neutral_count || 0}</div>
        </div>
      </div>

      {/* Sentiment Score Bar */}
      <div className="mb-5">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-gray-500 font-medium">Sentiment Skoru</span>
          <span className={`font-bold ${getSentimentColor(data.sentiment_score)}`}>
            {(data.sentiment_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden relative">
          {/* Center marker */}
          <div className="absolute left-1/2 top-0 w-0.5 h-full bg-slate-500 z-10" />
          <div
            className={`h-full transition-all duration-500 ${
              data.sentiment_score >= 0 ? 'bg-emerald-500' : 'bg-red-500'
            }`}
            style={{
              width: `${Math.abs(data.sentiment_score) * 50}%`,
              marginLeft: data.sentiment_score >= 0 ? '50%' : `${50 - Math.abs(data.sentiment_score) * 50}%`,
            }}
          />
        </div>
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>Çok Olumsuz</span>
          <span>Nötr</span>
          <span>Çok Olumlu</span>
        </div>
      </div>

      {/* Recent News List */}
      {data.recent_news && data.recent_news.length > 0 && (
        <div>
          <h4 className="text-sm font-bold text-gray-600 mb-3 uppercase tracking-wider">
            Son Haberler ({data.recent_news.length})
          </h4>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1 custom-scrollbar">
            {data.recent_news.map((news, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200/50 hover:bg-gray-100/60 transition-colors"
              >
                {/* Sentiment dot */}
                <div className="mt-1.5 flex-shrink-0">
                  <div className={`w-3 h-3 rounded-full ${getItemSentimentDot(news.sentiment_score)}`} />
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600 font-medium">
                      {news.category}
                    </span>
                    <span className="text-xs text-slate-500">{formatDate(news.date)}</span>
                  </div>
                  <p className="text-sm text-gray-700 leading-snug truncate">{news.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs">{news.impact_icon}</span>
                    <span className={`text-xs ${getSentimentColor(news.sentiment_score)}`}>
                      {news.impact}
                    </span>
                  </div>
                </div>

                {/* Score */}
                <div className={`flex-shrink-0 text-sm font-bold ${getSentimentColor(news.sentiment_score)}`}>
                  {news.sentiment_score > 0 ? '+' : ''}{(news.sentiment_score * 100).toFixed(0)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
