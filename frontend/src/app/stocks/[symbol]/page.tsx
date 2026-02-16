'use client';

/**
 * HisseRadar Hisse Detay Sayfası
 * ===============================
 * Tek bir hissenin tüm analizlerini gösterir
 */

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { 
  ArrowLeft, TrendingUp, TrendingDown, Minus, 
  RefreshCw, ExternalLink, Share2
} from 'lucide-react';
import { getStockInfo, formatCurrency, formatPercent, getChangeColor } from '@/lib/api';
import PriceChart from '@/components/PriceChart';
import TechnicalIndicators from '@/components/TechnicalIndicators';
import FundamentalData from '@/components/FundamentalData';
import StockNews from '@/components/StockNews';
import type { Stock } from '@/types';

type TabType = 'chart' | 'technical' | 'fundamental' | 'news';

export default function StockDetailPage() {
  const params = useParams();
  const symbol = (params.symbol as string)?.toUpperCase();
  
  const [stock, setStock] = useState<Stock | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('chart');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [mounted, setMounted] = useState(false);

  // Client mount
  useEffect(() => {
    setMounted(true);
  }, []);

  // Veri yükle
  useEffect(() => {
    async function loadStock() {
      if (!symbol) return;
      
      setIsLoading(true);
      setError(null);

      try {
        const data = await getStockInfo(symbol);
        setStock(data);
        setLastUpdate(new Date().toLocaleTimeString('tr-TR'));
      } catch (err) {
        console.error('Hisse bilgisi yüklenemedi:', err);
        setError('Hisse bilgisi yüklenemedi');
      } finally {
        setIsLoading(false);
      }
    }

    loadStock();
  }, [symbol]);

  // Yenile
  const handleRefresh = () => {
    window.location.reload();
  };

  // Değişim ikonu
  const getChangeIcon = (change: number | undefined) => {
    if (!change) return <Minus className="w-5 h-5 text-gray-400" />;
    if (change > 0) return <TrendingUp className="w-5 h-5 text-up" />;
    if (change < 0) return <TrendingDown className="w-5 h-5 text-down" />;
    return <Minus className="w-5 h-5 text-gray-400" />;
  };

  if (!symbol) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Hisse sembolü bulunamadı</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Sol - Geri ve Hisse Bilgisi */}
            <div className="flex items-center gap-4">
              <a 
                href="/"
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </a>

              <div>
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-primary-100 text-primary-700 font-bold rounded">
                    {symbol}
                  </span>
                  <h1 className="text-xl font-bold text-gray-900">
                    {isLoading ? 'Yükleniyor...' : stock?.name || symbol}
                  </h1>
                </div>
                
                {stock?.sector && (
                  <p className="text-sm text-gray-500 mt-1">{stock.sector}</p>
                )}
              </div>
            </div>

            {/* Sağ - Fiyat Bilgisi */}
            {stock && (
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatCurrency(stock.current_price)}
                  </div>
                  <div className="flex items-center justify-end gap-2 mt-1">
                    {getChangeIcon(stock.change_percent)}
                    <span className={`font-medium ${getChangeColor(stock.change_percent)}`}>
                      {formatPercent(stock.change_percent)}
                    </span>
                  </div>
                </div>

                {/* Aksiyonlar */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRefresh}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Yenile"
                  >
                    <RefreshCw className="w-5 h-5 text-gray-600" />
                  </button>
                  <a
                    href={`https://www.google.com/finance/quote/${symbol}:IST`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Google Finance'da aç"
                  >
                    <ExternalLink className="w-5 h-5 text-gray-600" />
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-4 mt-4 border-b border-gray-200 -mb-4">
            <button
              onClick={() => setActiveTab('chart')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'chart'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📈 Grafik
            </button>
            <button
              onClick={() => setActiveTab('technical')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'technical'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📊 Teknik Analiz
            </button>
            <button
              onClick={() => setActiveTab('fundamental')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'fundamental'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📋 Temel Analiz
            </button>
            <button
              onClick={() => setActiveTab('news')}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'news'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📰 Haberler
            </button>
          </div>
        </div>
      </div>

      {/* İçerik */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="spinner"></div>
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <p className="text-red-500 mb-4">{error}</p>
            <a href="/" className="text-primary-600 hover:underline">
              Ana sayfaya dön
            </a>
          </div>
        ) : (
          <>
            {/* Grafik Tab */}
            {activeTab === 'chart' && (
              <div className="space-y-6">
                <PriceChart symbol={symbol} height={500} />
                
                {/* TradingView Widget - Alternatif */}
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    📺 TradingView'da Görüntüle
                  </h3>
                  <a
                    href={`https://www.tradingview.com/chart/?symbol=BIST:${symbol}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    TradingView'da Aç
                  </a>
                  <p className="text-sm text-gray-500 mt-2">
                    Daha detaylı grafik analizi için TradingView platformunu kullanabilirsiniz.
                  </p>
                </div>
              </div>
            )}

            {/* Teknik Analiz Tab */}
            {activeTab === 'technical' && (
              <TechnicalIndicators symbol={symbol} />
            )}

            {/* Temel Analiz Tab */}
            {activeTab === 'fundamental' && (
              <FundamentalData symbol={symbol} />
            )}

            {/* Haberler Tab */}
            {activeTab === 'news' && (
              <StockNews symbol={symbol} />
            )}
          </>
        )}
      </div>

      {/* Son güncelleme */}
      {mounted && (
        <div className="text-center py-4 text-xs text-gray-400">
          {lastUpdate ? `Son güncelleme: ${lastUpdate}` : ''} (Veriler 15-20 dk gecikmelidir)
        </div>
      )}
    </div>
  );
}
