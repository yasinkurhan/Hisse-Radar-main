'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';

interface KAPNotification {
  title: string;
  summary: string;
  publish_date: string;
  category: string;
  category_name: string;
  importance: string;
  sentiment_score: number;
  sentiment_label: string;
  source: string;
  symbol: string;
  url?: string;
}

interface CollectionStatus {
  is_running: boolean;
  progress: number;
  total_symbols: number;
  percent: number;
  fetched_count: number;
  error_count: number;
  total_news_collected: number;
  started_at: string | null;
  completed_at: string | null;
  cycle_count: number;
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

// TradingView tarzı sembol renkleri
const SYMBOL_COLORS: Record<string, string> = {
  'A': 'bg-blue-600', 'B': 'bg-emerald-600', 'C': 'bg-purple-600', 'D': 'bg-orange-600',
  'E': 'bg-pink-600', 'F': 'bg-teal-600', 'G': 'bg-indigo-600', 'H': 'bg-rose-600',
  'I': 'bg-cyan-600', 'J': 'bg-amber-600', 'K': 'bg-violet-600', 'L': 'bg-lime-600',
  'M': 'bg-fuchsia-600', 'N': 'bg-sky-600', 'O': 'bg-red-600', 'P': 'bg-green-600',
  'Q': 'bg-yellow-600', 'R': 'bg-blue-500', 'S': 'bg-emerald-500', 'T': 'bg-purple-500',
  'U': 'bg-orange-500', 'V': 'bg-pink-500', 'W': 'bg-teal-500', 'X': 'bg-indigo-500',
  'Y': 'bg-rose-500', 'Z': 'bg-cyan-500',
};

function getSymbolColor(symbol: string): string {
  return SYMBOL_COLORS[symbol?.charAt(0)?.toUpperCase() || 'A'] || 'bg-blue-600';
}

function getRelativeTime(dateStr: string): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr.replace(' ', 'T'));
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    if (diffMs < 0) return 'az önce';
    const diffMin = Math.floor(diffMs / 60000);
    const diffHour = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffMs / 86400000);
    if (diffMin < 1) return 'az önce';
    if (diffMin < 60) return `${diffMin} dk önce`;
    if (diffHour < 24) return `${diffHour} saat önce`;
    if (diffDay < 7) return `${diffDay} gün önce`;
    if (diffDay < 30) return `${Math.floor(diffDay / 7)} hafta önce`;
    return `${Math.floor(diffDay / 30)} ay önce`;
  } catch {
    return dateStr;
  }
}

function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    'FR': '📊', 'ODA': '📋', 'GENEL_KURUL': '🏛️', 'TEMETTÜ': '💰',
    'SERMAYE': '📈', 'ORTAKLIK': '🤝', 'YONETIM': '👔', 'HABERLER': '📰', 'DIGER': '📄',
  };
  return icons[category] || '📄';
}

function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    'FR': 'Finansal Rapor', 'ODA': 'Özel Durum', 'GENEL_KURUL': 'Genel Kurul',
    'TEMETTÜ': 'Temettü', 'SERMAYE': 'Sermaye', 'ORTAKLIK': 'Ortaklık',
    'YONETIM': 'Yönetim', 'HABERLER': 'Haberler', 'DIGER': 'Diğer',
  };
  return labels[category] || category || 'Diğer';
}

export default function NewsPage() {
  const [allKap, setAllKap] = useState<KAPNotification[]>([]);
  const [filteredKap, setFilteredKap] = useState<KAPNotification[]>([]);
  const [allNews, setAllNews] = useState<NewsItem[]>([]);
  const [sentimentStocks, setSentimentStocks] = useState<StockSentiment[]>([]);
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatus | null>(null);
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'kap' | 'news' | 'sentiment'>('kap');
  const [searchSymbol, setSearchSymbol] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState<string>('ALL');
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchKapData = useCallback(async (refresh: boolean = false) => {
    try {
      const ts = Date.now();
      const refreshParam = refresh ? '&refresh=true' : '';
      const res = await fetch(
        `http://localhost:8001/api/news/kap?limit=500&days=90&t=${ts}${refreshParam}`,
        { cache: 'no-store' }
      );
      if (res.ok) {
        const data = await res.json();
        const notifications: KAPNotification[] = (data.notifications || []).map((item: any) => ({
          title: item.title || 'KAP Bildirimi',
          summary: item.summary || item.title || '',
          publish_date: item.publish_date || item.date || '',
          category: item.category || 'DIGER',
          category_name: getCategoryLabel(item.category),
          importance: item.importance || 'medium',
          sentiment_score: item.sentiment_score || 0,
          sentiment_label: item.sentiment_label || 'neutral',
          source: item.source || 'KAP',
          symbol: item.symbol || '',
          url: item.url || 'https://www.kap.org.tr',
        }));
        setAllKap(notifications);
        if (data.collection_status) {
          setCollectionStatus(data.collection_status);
        }
      }
    } catch (err) {
      console.error('KAP verisi yüklenemedi:', err);
    }
  }, []);

  const fetchNewsData = useCallback(async () => {
    try {
      const ts = Date.now();
      const [marketRes, sentimentRes] = await Promise.all([
        fetch(`http://localhost:8001/api/news/real/market?t=${ts}`, { cache: 'no-store' }).catch(() => null),
        fetch(`http://localhost:8001/api/news/kap/sentiment?days=90&min_news=1&t=${ts}`, { cache: 'no-store' }).catch(() => null),
      ]);
      if (marketRes?.ok) {
        const data = await marketRes.json();
        setAllNews(data.news || []);
      }
      if (sentimentRes?.ok) {
        const data = await sentimentRes.json();
        setSentimentStocks((data.stocks || []).map((s: any) => ({
          symbol: s.symbol,
          sentiment: s.overall_sentiment,
          score: s.avg_sentiment,
          label: s.overall_sentiment === 'positive' ? 'Olumlu' : s.overall_sentiment === 'negative' ? 'Olumsuz' : 'Nötr',
          news_count: s.total_news,
        })));
      }
    } catch (err) {
      console.error('Haber verisi yüklenemedi:', err);
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchKapData(), fetchNewsData()]);
      setLoading(false);
    };
    init();
  }, [fetchKapData, fetchNewsData]);

  // Collection durumu polling
  useEffect(() => {
    if (collectionStatus?.is_running) {
      statusIntervalRef.current = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:8001/api/news/kap/collection-status?t=${Date.now()}`, { cache: 'no-store' });
          if (res.ok) {
            const status = await res.json();
            setCollectionStatus(status);
            if (!status.is_running && status.completed_at) {
              await fetchKapData();
              setRefreshing(false);
              if (statusIntervalRef.current) { clearInterval(statusIntervalRef.current); statusIntervalRef.current = null; }
            }
          }
        } catch { /* ignore */ }
      }, 3000);
    }
    return () => { if (statusIntervalRef.current) { clearInterval(statusIntervalRef.current); statusIntervalRef.current = null; } };
  }, [collectionStatus?.is_running, fetchKapData]);

  // Filtreleme
  useEffect(() => {
    let filtered = allKap;
    if (searchSymbol) { const s = searchSymbol.toUpperCase(); filtered = filtered.filter(k => k.symbol.includes(s)); }
    if (selectedCategory !== 'ALL') { filtered = filtered.filter(k => k.category === selectedCategory); }
    if (selectedSentiment !== 'ALL') { filtered = filtered.filter(k => k.sentiment_label === selectedSentiment); }
    setFilteredKap(filtered);
  }, [allKap, searchSymbol, selectedCategory, selectedSentiment]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchKapData(true);
  };

  const getSentimentColor = (score: number) => {
    if (score >= 0.3) return 'text-emerald-400';
    if (score >= 0.1) return 'text-green-400';
    if (score <= -0.3) return 'text-red-500';
    if (score <= -0.1) return 'text-red-400';
    return 'text-amber-400';
  };
  const getSentimentBg = (score: number) => {
    if (score >= 0.15) return 'bg-emerald-500/20 border-emerald-500/30';
    if (score <= -0.15) return 'bg-red-500/20 border-red-500/30';
    return 'bg-amber-500/20 border-amber-500/30';
  };
  const getSentimentDot = (score: number) => {
    if (score > 0.05) return '🟢';
    if (score < -0.05) return '🔴';
    return '🟡';
  };

  const uniqueSymbols = [...new Set(allKap.map(k => k.symbol))].sort();
  const uniqueCategories = [...new Set(allKap.map(k => k.category))].filter(Boolean);

  // Prevent hydration mismatch - only show after client mount
  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#131722] text-white"></div>
    );
  }

  if (loading && allKap.length === 0) {
    return (
      <div className="min-h-screen bg-[#131722] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">KAP bildirimleri yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#131722] text-white">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-[#1e222d] border-b border-gray-700/50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-white">KAP Bildirimleri</h1>
              <span className="text-sm text-gray-400 bg-gray-700/50 px-2 py-0.5 rounded">
                {allKap.length} bildirim · {uniqueSymbols.length} hisse
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={handleRefresh} disabled={refreshing || collectionStatus?.is_running}
                className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all ${refreshing || collectionStatus?.is_running ? 'bg-blue-600/50 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}>
                {refreshing || collectionStatus?.is_running ? (
                  <><div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>Toplanıyor...</>
                ) : (<>🔄 Tümünü Yenile</>)}
              </button>
              <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm">Ana Sayfa</Link>
            </div>
          </div>

          {/* Collection Progress Bar */}
          {collectionStatus?.is_running && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                <span>Tüm BIST hisseleri taranıyor... {collectionStatus.progress}/{collectionStatus.total_symbols}</span>
                <span>%{collectionStatus.percent} · {collectionStatus.total_news_collected} yeni haber</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div className="bg-blue-500 h-1.5 rounded-full transition-all duration-300" style={{ width: `${collectionStatus.percent}%` }} />
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="flex gap-1 mt-3">
            {(['kap', 'news', 'sentiment'] as const).map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${activeTab === tab ? 'bg-[#131722] text-white border-t-2 border-blue-500' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`}>
                {tab === 'kap' ? `📋 KAP (${filteredKap.length})` : tab === 'news' ? `📰 Haberler (${allNews.length})` : '📈 Sentiment'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-4">
        {/* KAP Tab */}
        {activeTab === 'kap' && (
          <div>
            <div className="flex flex-wrap gap-3 mb-4">
              <div className="relative">
                <input type="text" placeholder="Sembol ara..." value={searchSymbol} onChange={(e) => setSearchSymbol(e.target.value)}
                  className="bg-[#1e222d] border border-gray-600 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 w-40 focus:border-blue-500 focus:outline-none" />
                {searchSymbol && <button onClick={() => setSearchSymbol('')} className="absolute right-2 top-2.5 text-gray-500 hover:text-white text-xs">✕</button>}
              </div>
              <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-[#1e222d] border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
                <option value="ALL">Tüm Kategoriler</option>
                {uniqueCategories.map(cat => <option key={cat} value={cat}>{getCategoryIcon(cat)} {getCategoryLabel(cat)}</option>)}
              </select>
              <select value={selectedSentiment} onChange={(e) => setSelectedSentiment(e.target.value)}
                className="bg-[#1e222d] border border-gray-600 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none">
                <option value="ALL">Tüm Sentiment</option>
                <option value="positive">🟢 Olumlu</option>
                <option value="neutral">🟡 Nötr</option>
                <option value="negative">🔴 Olumsuz</option>
              </select>
              {collectionStatus?.completed_at && !collectionStatus.is_running && (
                <div className="flex items-center gap-2 text-xs text-gray-500 ml-auto">
                  <span>Son güncelleme: {getRelativeTime(collectionStatus.completed_at)}</span>
                  <span>·</span>
                  <span>Döngü #{collectionStatus.cycle_count}</span>
                </div>
              )}
            </div>

            <div className="space-y-1">
              {filteredKap.length === 0 ? (
                <div className="text-center py-16 text-gray-500">
                  <p className="text-4xl mb-4">📋</p>
                  <p className="text-lg">Henüz KAP bildirimi yok</p>
                  <p className="text-sm mt-2">&quot;Tümünü Yenile&quot; butonuna tıklayarak tüm BIST hisselerinin KAP bildirimlerini çekebilirsiniz.</p>
                </div>
              ) : (
                filteredKap.map((kap, idx) => (
                  <div key={idx} className="bg-[#1e222d] hover:bg-[#262b38] rounded-lg px-4 py-3 flex items-start gap-3 transition-colors border border-transparent hover:border-gray-600/50 group">
                    <Link href={`/stock/${kap.symbol}`}
                      className={`${getSymbolColor(kap.symbol)} text-white font-bold text-xs px-2 py-1 rounded min-w-[52px] text-center shrink-0 hover:brightness-110 transition-all`}>
                      {kap.symbol}
                    </Link>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[11px] text-gray-500">{getCategoryIcon(kap.category)} {getCategoryLabel(kap.category)}</span>
                        <span className="text-[10px] text-gray-600">·</span>
                        <span className="text-[11px] text-gray-500">{getRelativeTime(kap.publish_date)}</span>
                      </div>
                      <h4 className="text-[13px] text-gray-200 leading-snug line-clamp-2 group-hover:text-white transition-colors">{kap.title}</h4>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs" title={`Sentiment: ${(kap.sentiment_score * 100).toFixed(0)}`}>{getSentimentDot(kap.sentiment_score)}</span>
                      {kap.url && kap.url !== 'https://www.kap.org.tr' && (
                        <a href={kap.url} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-blue-400 transition-colors opacity-0 group-hover:opacity-100" title="KAP'ta aç">↗</a>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* News Tab */}
        {activeTab === 'news' && (
          <div className="space-y-1">
            {allNews.length === 0 ? (
              <div className="text-center py-16 text-gray-500"><p className="text-4xl mb-4">📰</p><p className="text-lg">Haber bulunamadı</p></div>
            ) : (
              allNews.map((news, idx) => (
                <div key={idx} className="bg-[#1e222d] hover:bg-[#262b38] rounded-lg px-4 py-3 flex items-start gap-3 transition-colors border border-transparent hover:border-gray-600/50 group">
                  <span className="bg-purple-600 text-white font-bold text-xs px-2 py-1 rounded min-w-[52px] text-center shrink-0">{news.symbol || 'BIST'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[11px] text-gray-500">{news.source}</span>
                      <span className="text-[10px] text-gray-600">·</span>
                      <span className="text-[11px] text-gray-500">{getRelativeTime(news.date)}</span>
                    </div>
                    <h4 className="text-[13px] text-gray-200 leading-snug line-clamp-2 group-hover:text-white">{news.title}</h4>
                    {news.summary && news.summary !== news.title && <p className="text-[12px] text-gray-500 mt-1 line-clamp-1">{news.summary}</p>}
                  </div>
                  <span className="text-xs shrink-0">{getSentimentDot(news.sentiment_score)}</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* Sentiment Tab */}
        {activeTab === 'sentiment' && (
          <div className="bg-[#1e222d] rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="text-gray-400 text-xs uppercase border-b border-gray-700">
                  <th className="text-left py-3 px-4">Hisse</th>
                  <th className="text-left py-3 px-4">Sentiment</th>
                  <th className="text-right py-3 px-4">Skor</th>
                  <th className="text-right py-3 px-4">Haber</th>
                  <th className="text-right py-3 px-4">Detay</th>
                </tr>
              </thead>
              <tbody>
                {sentimentStocks.map((stock, idx) => (
                  <tr key={idx} className="border-b border-gray-700/50 hover:bg-[#262b38] transition-colors">
                    <td className="py-3 px-4">
                      <Link href={`/stock/${stock.symbol}`} className={`${getSymbolColor(stock.symbol)} text-white font-bold text-xs px-2 py-1 rounded hover:brightness-110`}>{stock.symbol}</Link>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs border ${getSentimentBg(stock.score)}`}>
                        <span className={getSentimentColor(stock.score)}>
                          {stock.score >= 0.15 ? 'Olumlu' : stock.score <= -0.15 ? 'Olumsuz' : 'Nötr'}
                        </span>
                      </span>
                    </td>
                    <td className={`py-3 px-4 text-right font-mono font-bold ${getSentimentColor(stock.score)}`}>{(stock.score * 100).toFixed(0)}</td>
                    <td className="py-3 px-4 text-right text-gray-400">{stock.news_count}</td>
                    <td className="py-3 px-4 text-right"><Link href={`/stock/${stock.symbol}`} className="text-blue-400 hover:text-blue-300 text-xs">Detay →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
