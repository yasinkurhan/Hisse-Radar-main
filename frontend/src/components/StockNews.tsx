'use client';

import { useState, useEffect, useRef } from 'react';

interface NewsItem {
  id?: number;
  symbol: string;
  title: string;
  summary: string;
  category: string;
  category_name: string;
  importance: 'high' | 'medium' | 'low';
  publish_date: string;
  url: string;
  source: string;
  sentiment_score: number;
  sentiment_label: 'positive' | 'negative' | 'neutral';
}

interface StockNewsProps {
  symbol: string;
}

export default function StockNews({ symbol }: StockNewsProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Haber kategorisi renkleri
  const categoryColors: Record<string, string> = {
    'FR': '#3b82f6',       // Finansal Rapor - Mavi
    'ODA': '#ef4444',      // Özel Durum - Kırmızı
    'TEMETTÜ': '#22c55e',  // Temettü - Yeşil
    'SERMAYE': '#f59e0b',  // Sermaye - Turuncu
    'GK': '#8b5cf6',       // Genel Kurul - Mor
    'ORTAKLIK': '#06b6d4', // Ortaklık - Cyan
    'DIGER': '#6b7280',    // Diğer - Gri
  };

  useEffect(() => {
    fetchNews();
  }, [symbol]);

  useEffect(() => {
    if (news.length > 0 && canvasRef.current) {
      drawSentimentChart();
    }
  }, [news]);

  const fetchNews = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8001/api/kap/news/${symbol}?limit=50`);
      
      if (!response.ok) {
        throw new Error('Haberler yüklenemedi');
      }
      
      const data = await response.json();
      setNews(data.news || []);
      setError(null);
    } catch (err) {
      setError('Haberler yüklenirken hata oluştu');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const collectNews = async () => {
    try {
      setCollecting(true);
      const response = await fetch(`http://localhost:8001/api/kap/collect/${symbol}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Haber toplama başarısız');
      }
      
      const data = await response.json();
      if (data.news) {
        setNews(data.news);
      }
      setError(null);
    } catch (err) {
      setError('Haber toplama sırasında hata oluştu');
      console.error(err);
    } finally {
      setCollecting(false);
    }
  };

  const drawSentimentChart = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Yüksek DPI için ölçeklendirme
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Temizle
    ctx.clearRect(0, 0, width, height);
    
    // Köşeleri yuvarla
    ctx.beginPath();
    ctx.roundRect(0, 0, width, height, 16);
    ctx.clip();

    // Arka plan (Koyu tema her zaman şık durur grafikte)
    const bgGradient = ctx.createLinearGradient(0, 0, width, height);
    bgGradient.addColorStop(0, '#1e293b'); // slate-800
    bgGradient.addColorStop(1, '#0f172a'); // slate-900
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, width, height);

    // Sentiment sayıları
    const positive = news.filter(n => n.sentiment_label === 'positive').length;
    const negative = news.filter(n => n.sentiment_label === 'negative').length;
    const neutral = news.filter(n => n.sentiment_label === 'neutral').length;
    const total = news.length;

    if (total === 0) return;

    // Pie chart çiz
    const centerX = 60;
    const centerY = height / 2;
    const radius = 35;
    
    let startAngle = -Math.PI / 2;
    
    const segments = [
      { value: positive, color: '#22c55e', label: 'Pozitif' },
      { value: neutral, color: '#94a3b8', label: 'Nötr' },
      { value: negative, color: '#ef4444', label: 'Negatif' },
    ];

    segments.forEach(segment => {
      if (segment.value > 0) {
        const sliceAngle = (segment.value / total) * 2 * Math.PI;
        
        ctx.shadowColor = segment.color;
        ctx.shadowBlur = 15;
        
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
        ctx.closePath();
        ctx.fillStyle = segment.color;
        ctx.fill();
        
        ctx.shadowBlur = 0;
        startAngle += sliceAngle;
      }
    });

    // Donut hole
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.6, 0, 2 * Math.PI);
    ctx.fillStyle = '#1e293b';
    ctx.fill();

    // Toplam sayı
    ctx.font = 'bold 16px Inter, system-ui, sans-serif';
    ctx.fillStyle = '#f1f5f9';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total.toString(), centerX, centerY);

    // Legend
    const legendX = 120;
    let legendY = 30;

    ctx.font = '12px Inter, system-ui, sans-serif';
    ctx.textAlign = 'left';

    segments.forEach(segment => {
      // Dot
      ctx.fillStyle = segment.color;
      ctx.beginPath();
      ctx.arc(legendX, legendY - 4, 4, 0, 2 * Math.PI);
      ctx.fill();

      // Text
      ctx.fillStyle = '#cbd5e1';
      ctx.fillText(`${segment.label}: ${segment.value}`, legendX + 10, legendY);
      
      legendY += 20;
    });
    
    // Average Line
    const avgSentiment = news.reduce((acc, n) => acc + n.sentiment_score, 0) / total;
    ctx.fillStyle = avgSentiment > 0.2 ? '#4ade80' : avgSentiment < -0.2 ? '#f87171' : '#cbd5e1';
    ctx.font = 'bold 11px Inter, system-ui, sans-serif';
    ctx.fillText(`Skor: ${avgSentiment.toFixed(2)}`, legendX, legendY + 5);
  };

  const filteredNews = filter === 'all' 
    ? news 
    : news.filter(n => n.category === filter || n.importance === filter || n.sentiment_label === filter);

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('tr-TR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-100 dark:border-gray-700 shadow-sm">
        <div className="flex flex-col items-center justify-center py-8">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
          <span className="mt-4 text-gray-500 dark:text-gray-400 text-sm">Finansal haberler analiz ediliyor...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>
            </span>
             KAP Haberleri & Analizler
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 ml-1">{symbol} için toplanan son gelişmeler</p>
        </div>

        <button
          onClick={collectNews}
          disabled={collecting}
          className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 shadow-sm ${
            collecting 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-800' 
              : 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700'
          }`}
        >
          {collecting ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          )}
          <span>{collecting ? 'Güncelleniyor...' : 'Haberleri Güncelle'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sol Kolon: Sentiment & Filtreler */}
        <div className="space-y-6">
          {/* Sentiment Widget */}
          {news.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
               <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Yapay Zeka Duygu Analizi</h3>
               <div className="w-full relative h-[120px] rounded-lg overflow-hidden bg-slate-900 shadow-inner">
                 <canvas 
                    ref={canvasRef} 
                    className="w-full h-full object-contain"
                  />
               </div>
               <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                  * Yapay zeka son {news.length} haberi analiz ederek piyasa algısını puanladı.
               </div>
            </div>
          )}

          {/* Filtreler */}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Filtreleme</h3>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${
                  filter === 'all' 
                    ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-200 dark:shadow-none' 
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300'
                }`}
              >
                Tümü
              </button>
              <button onClick={() => setFilter('high')} className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${filter === 'high' ? 'bg-red-600 text-white border-red-600' : 'bg-white text-gray-600 border-gray-200 hover:border-red-300 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300'}`}>Önemli</button>
              <button onClick={() => setFilter('positive')} className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${filter === 'positive' ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-600 border-gray-200 hover:border-emerald-300 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300'}`}>Pozitif</button>
              <button onClick={() => setFilter('FR')} className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${filter === 'FR' ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300'}`}>Finansal</button>
            </div>
          </div>
        </div>

        {/* Sağ Kolon: Haber Listesi */}
        <div className="lg:col-span-2 space-y-4">
          {error ? (
             <div className="p-4 bg-red-50 text-red-600 rounded-xl border border-red-100 flex items-center gap-3">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                {error}
             </div>
          ) : filteredNews.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center bg-white dark:bg-gray-800 rounded-xl border border-dashed border-gray-300 dark:border-gray-700">
              <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-full mb-3">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Henüz haber bulunamadı</h3>
              <p className="text-gray-500 dark:text-gray-400 max-w-sm mt-1">Kriterlere uygun haber yok veya henüz veri toplanmadı.</p>
              <button
                onClick={collectNews}
                className="mt-4 text-primary-600 font-medium hover:underline"
              >
                Şimdi Tara
              </button>
            </div>
          ) : (
            filteredNews.map((item, index) => (
              <a
                key={index}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group block bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md hover:border-blue-200 dark:hover:border-blue-900 transition-all duration-200"
              >
                <div className="flex gap-4">
                  {/* Kategori Çizgisi */}
                  <div 
                    className="w-1 rounded-full flex-shrink-0" 
                    style={{ backgroundColor: categoryColors[item.category] || categoryColors['DIGER'] }}
                  />
                  
                  <div className="flex-grow min-w-0">
                    {/* Header: Badges & Date */}
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                       <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-semibold px-2 py-0.5 rounded text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700">
                             {item.category_name}
                          </span>
                          {item.importance === 'high' && (
                             <span className="text-xs font-semibold px-2 py-0.5 rounded bg-red-50 text-red-600 border border-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-900">
                               Önemli
                             </span>
                          )}
                          <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${
                            item.sentiment_label === 'positive' ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-900' :
                            item.sentiment_label === 'negative' ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-900' :
                            'bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700'
                          }`}>
                            {item.sentiment_label === 'positive' ? 'Pozitif' : item.sentiment_label === 'negative' ? 'Negatif' : 'Nötr'}
                          </span>
                       </div>
                       <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
                          {formatDate(item.publish_date)}
                       </span>
                    </div>

                    <h3 className="text-base font-semibold text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors line-clamp-2 mb-2">
                      {item.title}
                    </h3>

                    {item.summary && item.summary !== item.title && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-3 leading-relaxed">
                        {item.summary.replace(/\u0026nbsp;/g, ' ').replace(/\u0026/g, '&')}
                      </p>
                    )}

                    <div className="flex items-center justify-between mt-auto pt-2 border-t border-gray-50 dark:border-gray-700/50">
                       <span className="text-xs font-medium text-gray-400 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600"></span>
                          {item.source}
                       </span>
                       <span className="text-xs font-medium text-primary-600 dark:text-primary-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0 duration-200">
                          Haberi Oku 
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                       </span>
                    </div>
                  </div>
                </div>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
