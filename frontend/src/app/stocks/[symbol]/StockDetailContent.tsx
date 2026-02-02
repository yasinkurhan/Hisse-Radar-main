'use client';

/**
 * HisseRadar Hisse Detay Sayfası İçeriği
 * =====================================
 * Tek bir hissenin tüm detaylı analizlerini gösterir
 */

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  Star,
  BarChart3,
  Activity,
  PieChart,
  Newspaper,
  Brain
} from 'lucide-react';

import PriceChart from '@/components/PriceChart';
import TechnicalIndicators from '@/components/TechnicalIndicators';
import FundamentalData from '@/components/FundamentalData';
import StockNews from '@/components/StockNews';
import AIPrediction from '@/components/AIPrediction';

import { getStockInfo, getLatestPrice, formatCurrency, formatPercent, getChangeColor } from '@/lib/api';

interface StockInfo {
  symbol: string;
  name: string;
  sector: string;
  indexes?: string[];
}

interface PriceData {
  symbol: string;
  current_price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  volume: number;
}

type TabType = 'chart' | 'technical' | 'fundamental' | 'news' | 'ai';

export default function StockDetailContent() {
  const params = useParams();
  const router = useRouter();
  const symbol = params?.symbol as string;

  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [priceData, setPriceData] = useState<PriceData | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('chart');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Veri yükle
  useEffect(() => {
    if (!symbol) return;

    async function loadData() {
      setIsLoading(true);
      setError(null);

      try {
        const [info, price] = await Promise.all([
          getStockInfo(symbol),
          getLatestPrice(symbol)
        ]);

        setStockInfo(info);
        setPriceData(price);
      } catch (err) {
        console.error('Hisse bilgileri yüklenemedi:', err);
        setError('Hisse bilgileri yüklenemedi');
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [symbol]);

  // Fiyatı yenile
  const refreshPrice = async () => {
    if (!symbol || isRefreshing) return;

    setIsRefreshing(true);
    try {
      const price = await getLatestPrice(symbol);
      setPriceData(price);
    } catch (err) {
      console.error('Fiyat güncellenemedi:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Tab içeriğini render et
  const renderTabContent = () => {
    if (!symbol) return null;

    switch (activeTab) {
      case 'chart':
        return <PriceChart symbol={symbol} height={450} />;
      case 'technical':
        return <TechnicalIndicators symbol={symbol} />;
      case 'fundamental':
        return <FundamentalData symbol={symbol} />;
      case 'news':
        return <StockNews symbol={symbol} />;
      case 'ai':
        return <AIPrediction symbol={symbol} />;
      default:
        return null;
    }
  };

  // Yükleniyor
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  // Hata
  if (error || !stockInfo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error || 'Hisse bulunamadı'}</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Ana Sayfaya Dön
          </button>
        </div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'chart', label: 'Grafik', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'technical', label: 'Teknik', icon: <Activity className="w-4 h-4" /> },
    { id: 'fundamental', label: 'Temel', icon: <PieChart className="w-4 h-4" /> },
    { id: 'news', label: 'Haberler', icon: <Newspaper className="w-4 h-4" /> },
    { id: 'ai', label: 'AI Tahmin', icon: <Brain className="w-4 h-4" /> }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Üst Bar */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          {/* Geri ve Başlık */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.back()}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-gray-900">
                    {symbol}
                  </h1>
                  <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                    <Star className="w-5 h-5 text-gray-400 hover:text-yellow-400" />
                  </button>
                </div>
                <p className="text-gray-500">{stockInfo.name}</p>
              </div>
            </div>

            {/* Sektör ve Endeksler */}
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                {stockInfo.sector}
              </span>
              {stockInfo.indexes?.map((index) => (
                <span 
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  {index}
                </span>
              ))}
            </div>
          </div>

          {/* Fiyat Bilgileri */}
          {priceData && (
            <div className="flex items-center gap-6 flex-wrap">
              <div className="flex items-center gap-3">
                <span className="text-3xl font-bold text-gray-900">
                  {formatCurrency(priceData.current_price)}
                </span>
                <div className={`flex items-center gap-1 ${priceData.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {priceData.change_percent >= 0 ? (
                    <TrendingUp className="w-5 h-5" />
                  ) : (
                    <TrendingDown className="w-5 h-5" />
                  )}
                  <span className="font-medium">
                    {formatPercent(priceData.change_percent)}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>Önceki: {formatCurrency(priceData.previous_close)}</span>
                <span>Hacim: {(priceData.volume / 1000000).toFixed(2)}M</span>
              </div>

              <button
                onClick={refreshPrice}
                disabled={isRefreshing}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                title="Fiyatı Yenile"
              >
                <RefreshCw className={`w-4 h-4 text-gray-500 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          )}

          {/* Tab Navigasyonu */}
          <div className="flex gap-1 mt-4 border-b">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors
                  border-b-2 -mb-[2px]
                  ${activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                  }
                `}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* İçerik */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {renderTabContent()}
      </div>
    </div>
  );
}
