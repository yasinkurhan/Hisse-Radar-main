'use client';

import { useState, useEffect } from 'react';
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
  symbol: string;
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
}

interface StockSentiment {
  symbol: string;
  sentiment: string;
  score: number;
  label: string;
  news_count: number;
}

interface MarketSummary {
  market_sentiment_score: number;
  market_sentiment_label: string;
  positive_stocks: number;
  negative_stocks: number;
  total_analyzed: number;
  stocks: StockSentiment[];
  latest_kap: KAPNotification[];
  latest_news: NewsItem[];
}

export default function NewsPage() {
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [allKap, setAllKap] = useState<KAPNotification[]>([]);
  const [allNews, setAllNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'summary' | 'kap' | 'news' | 'sentiment'>('summary');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Gerçek haberler endpoint'lerini kullan
      const [marketRes, sentimentRes] = await Promise.all([
        fetch('http://localhost:8000/api/news/real/market'),
        fetch('http://localhost:8000/api/news/real/sentiment?symbols=THYAO,SASA,EREGL,ASELS,AKBNK,GARAN,KCHOL,TUPRS,FROTO,BIMAS')
      ]);
      
      const [marketData, sentimentData] = await Promise.all([
        marketRes.json(),
        sentimentRes.json()
      ]);
      
      // Market summary'yi oluştur
      setSummary({
        market_sentiment_score: marketData.market_sentiment_score,
        market_sentiment_label: marketData.market_sentiment_label,
        positive_stocks: sentimentData.stocks?.filter((s: any) => s.sentiment_score > 0.1).length || 0,
        negative_stocks: sentimentData.stocks?.filter((s: any) => s.sentiment_score < -0.1).length || 0,
        total_analyzed: sentimentData.total || 0,
        stocks: sentimentData.stocks?.map((s: any) => ({
          symbol: s.symbol,
          sentiment: s.sentiment_label,
          score: s.sentiment_score,
          label: s.sentiment_label,
          news_count: s.news_count
        })) || [],
        latest_kap: [],
        latest_news: marketData.news?.slice(0, 5) || []
      });
      
      setAllNews(marketData.news || []);
      setAllKap([]); // Gerçek KAP verisi yok
    } catch (err) {
      console.error('Veri yüklenemedi:', err);
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
    if (score >= 0.2) return 'bg-emerald-500/20';
    if (score <= -0.2) return 'bg-red-500/20';
    return 'bg-amber-500/20';
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'bg-red-500/30 text-red-300 border-red-500/50';
      case 'medium': return 'bg-amber-500/30 text-amber-300 border-amber-500/50';
      default: return 'bg-slate-500/30 text-slate-300 border-slate-500/50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Haber verileri yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">📰 Haber & Sentiment Merkezi</h1>
            <p className="text-gray-400 mt-1">KAP bildirimleri, haberler ve piyasa sentiment analizi</p>
          </div>
          <div className="flex gap-4">
            <button onClick={fetchData} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
              🔄 Yenile
            </button>
            <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded">
              Ana Sayfa
            </Link>
          </div>
        </div>

        {/* Market Sentiment Overview */}
        {summary && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">🌍 Piyasa Sentiment Özeti</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className={`rounded-lg p-4 text-center ${getSentimentBg(summary.market_sentiment_score)}`}>
                <div className={`text-3xl font-bold ${getSentimentColor(summary.market_sentiment_score)}`}>
                  {summary.market_sentiment_label}
                </div>
                <div className="text-sm text-gray-400 mt-1">Genel Sentiment</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-blue-400">
                  {(summary.market_sentiment_score * 100).toFixed(0)}
                </div>
                <div className="text-sm text-gray-400 mt-1">Sentiment Skoru</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-emerald-400">{summary.positive_stocks}</div>
                <div className="text-sm text-gray-400 mt-1">Olumlu Hisse</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-red-400">{summary.negative_stocks}</div>
                <div className="text-sm text-gray-400 mt-1">Olumsuz Hisse</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-purple-400">{summary.total_analyzed}</div>
                <div className="text-sm text-gray-400 mt-1">Analiz Edilen</div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-6 py-2 rounded-lg font-medium ${
              activeTab === 'summary' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            📊 Özet
          </button>
          <button
            onClick={() => setActiveTab('kap')}
            className={`px-6 py-2 rounded-lg font-medium ${
              activeTab === 'kap' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            📋 KAP Bildirimleri ({allKap.length})
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`px-6 py-2 rounded-lg font-medium ${
              activeTab === 'news' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            📰 Haberler ({allNews.length})
          </button>
          <button
            onClick={() => setActiveTab('sentiment')}
            className={`px-6 py-2 rounded-lg font-medium ${
              activeTab === 'sentiment' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            📈 Hisse Sentiment
          </button>
        </div>

        {/* Summary Tab */}
        {activeTab === 'summary' && summary && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Son KAP */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span>📋</span> Son KAP Bildirimleri
              </h3>
              <div className="space-y-3">
                {summary.latest_kap.map((kap, idx) => (
                  <div key={idx} className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-blue-500">
                    <div className="flex items-center gap-2 mb-2">
                      <Link href={`/stocks/${kap.symbol}`} className="text-blue-400 hover:underline font-semibold">
                        {kap.symbol}
                      </Link>
                      <span className={`px-2 py-0.5 rounded text-xs border ${getImportanceColor(kap.importance)}`}>
                        {kap.category_name}
                      </span>
                    </div>
                    <h4 className="text-white font-medium">{kap.title}</h4>
                    <p className="text-gray-400 text-sm mt-1 line-clamp-2">{kap.summary}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-500">{kap.date}</span>
                      <span className={`text-xs ${getSentimentColor(kap.sentiment_score)}`}>
                        {kap.sentiment_score > 0 ? '▲ Olumlu' : kap.sentiment_score < 0 ? '▼ Olumsuz' : '● Nötr'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Son Haberler */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span>📰</span> Son Haberler
              </h3>
              <div className="space-y-3">
                {summary.latest_news.map((news, idx) => (
                  <div key={idx} className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-purple-500">
                    <div className="flex items-center gap-2 mb-2">
                      <Link href={`/stocks/${news.symbol}`} className="text-purple-400 hover:underline font-semibold">
                        {news.symbol}
                      </Link>
                      <span className="text-xs bg-gray-600 px-2 py-0.5 rounded text-gray-300">
                        {news.source}
                      </span>
                    </div>
                    <h4 className="text-white font-medium">{news.title}</h4>
                    <p className="text-gray-400 text-sm mt-1 line-clamp-2">{news.summary}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-500">{news.date}</span>
                      <span className={`text-xs ${getSentimentColor(news.sentiment_score)}`}>
                        {news.sentiment_score > 0 ? '▲ Olumlu' : news.sentiment_score < 0 ? '▼ Olumsuz' : '● Nötr'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* KAP Tab */}
        {activeTab === 'kap' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">📋 Tüm KAP Bildirimleri</h3>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {allKap.map((kap, idx) => (
                <div key={idx} className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-blue-500 hover:bg-gray-700 transition-colors">
                  <div className="flex items-center gap-2 mb-2">
                    <Link href={`/stocks/${kap.symbol}`} className="text-blue-400 hover:underline font-bold text-lg">
                      {kap.symbol}
                    </Link>
                    <span className={`px-2 py-0.5 rounded text-xs border ${getImportanceColor(kap.importance)}`}>
                      {kap.importance === 'high' ? '🔴 Önemli' : '🟡 Normal'}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-gray-600 text-gray-300">
                      {kap.category_name}
                    </span>
                  </div>
                  <h4 className="text-white font-semibold text-lg">{kap.title}</h4>
                  <p className="text-gray-400 mt-2">{kap.summary}</p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-600">
                    <span className="text-sm text-gray-500">📅 {kap.date}</span>
                    <div className={`px-3 py-1 rounded ${getSentimentBg(kap.sentiment_score)}`}>
                      <span className={`text-sm font-medium ${getSentimentColor(kap.sentiment_score)}`}>
                        {kap.sentiment_score > 0 ? '📈 Olumlu' : kap.sentiment_score < 0 ? '📉 Olumsuz' : '➖ Nötr'}
                        {' '}({(kap.sentiment_score * 100).toFixed(0)})
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* News Tab */}
        {activeTab === 'news' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">📰 Tüm Haberler</h3>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {allNews.map((news, idx) => (
                <div key={idx} className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-purple-500 hover:bg-gray-700 transition-colors">
                  <div className="flex items-center gap-2 mb-2">
                    <Link href={`/stocks/${news.symbol}`} className="text-purple-400 hover:underline font-bold text-lg">
                      {news.symbol}
                    </Link>
                    <span className="px-2 py-0.5 rounded text-xs bg-gray-600 text-gray-300">
                      {news.source}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-blue-600/30 text-blue-300">
                      {news.category}
                    </span>
                  </div>
                  <h4 className="text-white font-semibold text-lg">{news.title}</h4>
                  <p className="text-gray-400 mt-2">{news.summary}</p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-600">
                    <span className="text-sm text-gray-500">📅 {news.date}</span>
                    <div className={`px-3 py-1 rounded ${getSentimentBg(news.sentiment_score)}`}>
                      <span className={`text-sm font-medium ${getSentimentColor(news.sentiment_score)}`}>
                        {news.sentiment_score > 0 ? '📈 Olumlu' : news.sentiment_score < 0 ? '📉 Olumsuz' : '➖ Nötr'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sentiment Tab */}
        {activeTab === 'sentiment' && summary && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">📈 Hisse Bazlı Sentiment</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-gray-400 text-left border-b border-gray-700">
                    <th className="py-3 px-4">Hisse</th>
                    <th className="py-3 px-4">Sentiment</th>
                    <th className="py-3 px-4">Skor</th>
                    <th className="py-3 px-4">Haber Sayısı</th>
                    <th className="py-3 px-4">Detay</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.stocks.map((stock, idx) => (
                    <tr key={idx} className="border-b border-gray-700 hover:bg-gray-700/50">
                      <td className="py-3 px-4">
                        <Link href={`/stocks/${stock.symbol}`} className="text-blue-400 hover:underline font-bold">
                          {stock.symbol}
                        </Link>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-3 py-1 rounded ${getSentimentBg(stock.score)}`}>
                          <span className={getSentimentColor(stock.score)}>{stock.label}</span>
                        </span>
                      </td>
                      <td className={`py-3 px-4 font-bold ${getSentimentColor(stock.score)}`}>
                        {(stock.score * 100).toFixed(0)}
                      </td>
                      <td className="py-3 px-4 text-gray-400">{stock.news_count}</td>
                      <td className="py-3 px-4">
                        <Link 
                          href={`/stocks/${stock.symbol}`}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          Detay →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
