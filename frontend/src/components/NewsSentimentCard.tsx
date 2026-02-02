'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface KAPNotification {
  title: string;
  summary: string;
  date: string;
  category: string;
  category_name: string;
  importance: string;
  sentiment: string;
  sentiment_score: number;
  source: string;
  symbol?: string;
}

interface NewsItem {
  title: string;
  summary: string;
  source: string;
  date: string;
  url: string;
  category: string;
  symbol: string;
  sentiment: string;
  sentiment_score: number;
  is_direct?: boolean;
}

interface StockSentiment {
  symbol: string;
  overall_sentiment: string;
  sentiment_score: number;
  sentiment_label: string;
  total_news: number;
  positive_news: number;
  negative_news: number;
  neutral_news: number;
  kap_count: number;
  news_count: number;
  latest_kap: KAPNotification[];
  latest_news: NewsItem[];
  sentiment_trend: string;
  recommendation: string;
}

interface NewsSentimentCardProps {
  symbol: string;
}

export default function NewsSentimentCard({ symbol }: NewsSentimentCardProps) {
  const [sentiment, setSentiment] = useState<StockSentiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'kap' | 'news'>('overview');

  useEffect(() => {
    fetchSentiment();
  }, [symbol]);

  const fetchSentiment = async () => {
    try {
      setLoading(true);
      // Gerçek haberler endpoint'ini kullan
      const response = await fetch(`http://localhost:8000/api/news/real/stock/${symbol}`);
      if (!response.ok) throw new Error('Veri alınamadı');
      const data = await response.json();
      
      // Veriyi uygun formata dönüştür
      setSentiment({
        symbol: data.symbol,
        overall_sentiment: data.sentiment_label,
        sentiment_score: data.sentiment_score,
        sentiment_label: data.sentiment_label,
        total_news: data.total_news,
        positive_news: data.positive_news,
        negative_news: data.negative_news,
        neutral_news: data.neutral_news,
        kap_count: 0,
        news_count: data.total_news,
        latest_kap: [],
        latest_news: data.news || [],
        sentiment_trend: 'stable',
        recommendation: data.sentiment_score > 0.1 
          ? 'Haberler olumlu görünüyor.' 
          : data.sentiment_score < -0.1 
          ? 'Haberler olumsuz görünüyor.' 
          : 'Haberler nötr görünüyor.'
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (score: number) => {
    if (score >= 0.3) return 'text-emerald-400';
    if (score >= 0.1) return 'text-green-400';
    if (score <= -0.3) return 'text-red-500';
    if (score <= -0.1) return 'text-red-400';
    return 'text-amber-400';
  };

  const getSentimentBg = (score: number) => {
    if (score >= 0.3) return 'bg-emerald-500/20 border-emerald-500/50';
    if (score >= 0.1) return 'bg-green-500/20 border-green-500/50';
    if (score <= -0.3) return 'bg-red-500/20 border-red-500/50';
    if (score <= -0.1) return 'bg-red-400/20 border-red-400/50';
    return 'bg-amber-500/20 border-amber-500/50';
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'bg-red-500/30 text-red-300';
      case 'medium': return 'bg-amber-500/30 text-amber-300';
      default: return 'bg-slate-500/30 text-slate-300';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      default: return '➡️';
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-slate-700 rounded w-full"></div>
          <div className="h-4 bg-slate-700 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (error || !sentiment) {
    return (
      <div className="bg-slate-800 rounded-xl p-6">
        <p className="text-red-400">Haber verileri yüklenemedi: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-xl p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📰</span> Haber & Sentiment Analizi
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            KAP bildirimleri ve haber sentiment'i
          </p>
        </div>
        
        <div className={`px-4 py-3 rounded-lg border ${getSentimentBg(sentiment.sentiment_score)}`}>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getSentimentColor(sentiment.sentiment_score)}`}>
              {sentiment.sentiment_label}
            </div>
            <div className="text-sm text-slate-400">
              Skor: {(sentiment.sentiment_score * 100).toFixed(0)}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">{sentiment.total_news}</div>
          <div className="text-xs text-slate-400">Toplam Haber</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-emerald-400">{sentiment.positive_news}</div>
          <div className="text-xs text-slate-400">Olumlu</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-red-400">{sentiment.negative_news}</div>
          <div className="text-xs text-slate-400">Olumsuz</div>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-amber-400">{sentiment.kap_count}</div>
          <div className="text-xs text-slate-400">KAP Bildirimi</div>
        </div>
      </div>

      {/* Trend & Recommendation */}
      <div className="bg-slate-700/30 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">{getTrendIcon(sentiment.sentiment_trend)}</span>
          <span className="text-white font-medium">
            Trend: {sentiment.sentiment_trend === 'improving' ? 'İyileşiyor' : 
                   sentiment.sentiment_trend === 'declining' ? 'Kötüleşiyor' : 'Stabil'}
          </span>
        </div>
        <p className="text-slate-300 text-sm">{sentiment.recommendation}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'overview' 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Özet
        </button>
        <button
          onClick={() => setActiveTab('kap')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'kap' 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          KAP ({sentiment.kap_count})
        </button>
        <button
          onClick={() => setActiveTab('news')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'news' 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          Haberler ({sentiment.news_count})
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Son KAP */}
          {sentiment.latest_kap.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-2">📋 Son KAP Bildirimi</h4>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className="text-white font-medium">{sentiment.latest_kap[0].title}</h5>
                    <p className="text-slate-400 text-sm mt-1">{sentiment.latest_kap[0].summary}</p>
                  </div>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${getImportanceColor(sentiment.latest_kap[0].importance)}`}>
                    {sentiment.latest_kap[0].importance === 'high' ? 'Önemli' : 'Normal'}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                  <span>{sentiment.latest_kap[0].date}</span>
                  <span>•</span>
                  <span>{sentiment.latest_kap[0].category_name}</span>
                </div>
              </div>
            </div>
          )}

          {/* Son Haber */}
          {sentiment.latest_news.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-2">📰 Son Haber</h4>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <h5 className="text-white font-medium">{sentiment.latest_news[0].title}</h5>
                <p className="text-slate-400 text-sm mt-1">{sentiment.latest_news[0].summary}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                  <span>{sentiment.latest_news[0].source}</span>
                  <span>•</span>
                  <span>{sentiment.latest_news[0].date}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'kap' && (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {sentiment.latest_kap.length === 0 ? (
            <p className="text-slate-400 text-center py-4">KAP bildirimi bulunamadı</p>
          ) : (
            sentiment.latest_kap.map((kap, idx) => (
              <div key={idx} className="bg-slate-700/50 rounded-lg p-3 border-l-4 border-blue-500">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${getImportanceColor(kap.importance)}`}>
                        {kap.category_name}
                      </span>
                      <span className={`text-xs ${getSentimentColor(kap.sentiment_score)}`}>
                        {kap.sentiment_score > 0 ? '▲' : kap.sentiment_score < 0 ? '▼' : '●'}
                      </span>
                    </div>
                    <h5 className="text-white font-medium mt-1">{kap.title}</h5>
                    <p className="text-slate-400 text-sm mt-1 line-clamp-2">{kap.summary}</p>
                  </div>
                </div>
                <div className="text-xs text-slate-500 mt-2">{kap.date}</div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'news' && (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {sentiment.latest_news.length === 0 ? (
            <p className="text-slate-400 text-center py-4">Haber bulunamadı</p>
          ) : (
            sentiment.latest_news.map((news, idx) => (
              <div 
                key={idx} 
                className={`bg-slate-700/50 rounded-lg p-3 border-l-4 ${
                  news.is_direct ? 'border-emerald-500' : 'border-slate-500'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs bg-slate-600 px-2 py-0.5 rounded text-slate-300">
                    {news.source}
                  </span>
                  {news.is_direct && (
                    <span className="text-xs bg-emerald-500/30 px-2 py-0.5 rounded text-emerald-300">
                      Doğrudan
                    </span>
                  )}
                  <span className={`text-xs ${getSentimentColor(news.sentiment_score)}`}>
                    {news.sentiment_score > 0 ? '▲ Olumlu' : news.sentiment_score < 0 ? '▼ Olumsuz' : '● Nötr'}
                  </span>
                </div>
                <h5 className="text-white font-medium">{news.title}</h5>
                <p className="text-slate-400 text-sm mt-1 line-clamp-2">{news.summary}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                  <span>{news.date}</span>
                  <span>•</span>
                  <span>{news.category}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
