'use client';

/**
 * HisseRadar Temel Analiz Bileşeni
 * =================================
 * F/K, PD/DD, ROE ve diğer temel verileri gösterir
 */

import { useEffect, useState } from 'react';
import { 
  Building2, TrendingUp, DollarSign, PieChart, 
  BarChart2, Wallet, AlertCircle, CheckCircle, XCircle
} from 'lucide-react';
import { getFundamentalData, formatLargeNumber, formatPercent } from '@/lib/api';
import type { FundamentalData } from '@/types';

interface FundamentalDataProps {
  symbol: string;
}

export default function FundamentalDataComponent({ symbol }: FundamentalDataProps) {
  const [data, setData] = useState<FundamentalData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getFundamentalData(symbol);
        setData(response);
      } catch (err) {
        console.error('Temel analiz yüklenemedi:', err);
        setError('Veriler yüklenemedi');
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [symbol]);

  // Değerlendirme rengi
  const getRatingColor = (rating: string) => {
    if (['Güçlü Al', 'Al', 'Ucuz', 'Mükemmel', 'İyi', 'Yüksek Temettü'].includes(rating)) {
      return 'text-green-600 bg-green-50';
    }
    if (['Sat', 'Azalt', 'Pahalı', 'Çok Pahalı', 'Zarar', 'Zayıf'].includes(rating)) {
      return 'text-red-600 bg-red-50';
    }
    return 'text-gray-600 bg-gray-50';
  };

  // Değerlendirme ikonu
  const getRatingIcon = (rating: string) => {
    if (['Güçlü Al', 'Al', 'Ucuz', 'Mükemmel', 'İyi'].includes(rating)) {
      return <CheckCircle className="w-4 h-4" />;
    }
    if (['Sat', 'Azalt', 'Pahalı', 'Çok Pahalı', 'Zarar'].includes(rating)) {
      return <XCircle className="w-4 h-4" />;
    }
    return <AlertCircle className="w-4 h-4" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12 text-red-500">
        {error || 'Veri bulunamadı'}
      </div>
    );
  }

  const summary = data.analysis_summary;

  return (
    <div className="space-y-6">
      {/* Şirket Bilgileri */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{data.company_name}</h3>
            <p className="text-sm text-gray-500 mt-1">
              {data.sector} {data.industry && `• ${data.industry}`}
            </p>
          </div>
          
          {summary && (
            <div className={`px-4 py-2 rounded-lg ${getRatingColor(summary.overall)}`}>
              <div className="flex items-center gap-2">
                {getRatingIcon(summary.overall)}
                <span className="font-semibold">{summary.overall}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Analiz Özeti */}
      {summary && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Temel Analiz Özeti</h4>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="text-center p-3 rounded-lg border border-gray-200">
              <div className={`text-sm font-medium ${getRatingColor(summary.valuation)} px-2 py-1 rounded inline-block`}>
                {summary.valuation}
              </div>
              <div className="text-xs text-gray-500 mt-1">Değerleme</div>
            </div>
            <div className="text-center p-3 rounded-lg border border-gray-200">
              <div className={`text-sm font-medium ${getRatingColor(summary.profitability)} px-2 py-1 rounded inline-block`}>
                {summary.profitability}
              </div>
              <div className="text-xs text-gray-500 mt-1">Kârlılık</div>
            </div>
            <div className="text-center p-3 rounded-lg border border-gray-200">
              <div className={`text-sm font-medium ${getRatingColor(summary.growth)} px-2 py-1 rounded inline-block`}>
                {summary.growth}
              </div>
              <div className="text-xs text-gray-500 mt-1">Büyüme</div>
            </div>
            <div className="text-center p-3 rounded-lg border border-gray-200">
              <div className={`text-sm font-medium ${getRatingColor(summary.dividend)} px-2 py-1 rounded inline-block`}>
                {summary.dividend}
              </div>
              <div className="text-xs text-gray-500 mt-1">Temettü</div>
            </div>
          </div>

          {/* Notlar */}
          {summary.notes && summary.notes.length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <h5 className="text-sm font-medium text-blue-800 mb-2">Önemli Notlar:</h5>
              <ul className="text-sm text-blue-700 space-y-1">
                {summary.notes.map((note, index) => (
                  <li key={index}>• {note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Metrik Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Değerleme Oranları */}
        <div className="indicator-card">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900">Değerleme Oranları</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">F/K (P/E)</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.pe_ratio?.toFixed(2) || '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">PD/DD (P/B)</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.pb_ratio?.toFixed(2) || '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">F/S (P/S)</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.ps_ratio?.toFixed(2) || '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">PEG</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.peg_ratio?.toFixed(2) || '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Kârlılık Oranları */}
        <div className="indicator-card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900">Kârlılık Oranları</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">ROE</span>
              <span className={`font-mono font-medium ${
                data.roe && data.roe > 15 ? 'text-green-600' : 
                data.roe && data.roe < 0 ? 'text-red-600' : ''
              }`}>
                {data.roe ? `%${data.roe.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">ROA</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.roa ? `%${data.roa.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Kâr Marjı</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.profit_margin ? `%${data.profit_margin.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Faaliyet Marjı</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.operating_margin ? `%${data.operating_margin.toFixed(2)}` : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Piyasa Verileri */}
        <div className="indicator-card">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Piyasa Verileri</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Piyasa Değeri</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.market_cap ? formatLargeNumber(data.market_cap) : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">52H En Yüksek</span>
              <span className="font-mono font-medium text-green-600">
                {data.week_52_high ? `₺${data.week_52_high.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">52H En Düşük</span>
              <span className="font-mono font-medium text-red-600">
                {data.week_52_low ? `₺${data.week_52_low.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Beta</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.beta?.toFixed(2) || '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Temettü Bilgileri */}
        <div className="indicator-card">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Temettü Bilgileri</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Temettü Verimi</span>
              <span className={`font-mono font-medium ${
                data.dividend_yield && data.dividend_yield > 5 ? 'text-green-600' : 'text-gray-900 dark:text-white'
              }`}>
                {data.dividend_yield ? `%${data.dividend_yield.toFixed(2)}` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Yıllık Temettü</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.dividend_rate ? `₺${data.dividend_rate.toFixed(2)}` : '-'}
              </span>
            </div>
          </div>
          
          <p className="mt-4 text-xs text-gray-500">
            {data.dividend_yield && data.dividend_yield > 5 
              ? '💰 Yüksek temettü verimi - Gelir yatırımcıları için cazip'
              : data.dividend_yield && data.dividend_yield > 0
              ? '📊 Düzenli temettü ödemesi yapıyor'
              : '⚠️ Temettü bilgisi mevcut değil'
            }
          </p>
        </div>

        {/* Bilanço Özeti */}
        <div className="indicator-card">
          <div className="flex items-center gap-2 mb-4">
            <Wallet className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Bilanço Özeti</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Toplam Nakit</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.total_cash ? formatLargeNumber(data.total_cash) : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Toplam Borç</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.total_debt ? formatLargeNumber(data.total_debt) : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Borç/Özkaynak</span>
              <span className={`font-mono font-medium ${
                data.debt_to_equity && data.debt_to_equity > 1 ? 'text-red-600' : 'text-gray-900 dark:text-white'
              }`}>
                {data.debt_to_equity?.toFixed(2) || '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 text-sm">Toplam Gelir</span>
              <span className="font-mono font-medium text-gray-900 dark:text-white">
                {data.total_revenue ? formatLargeNumber(data.total_revenue) : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Risk Göstergeleri */}
        <div className="indicator-card">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 className="w-5 h-5 text-primary-600" />
            <h4 className="font-semibold text-gray-900 dark:text-white">Risk Göstergeleri</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-500 text-sm">Beta Değeri</span>
              <div className="flex items-center gap-2">
                <span className="font-mono font-medium text-gray-900 dark:text-white">
                  {data.beta?.toFixed(2) || '-'}
                </span>
                {data.beta && (
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    data.beta > 1.5 ? 'bg-red-100 text-red-700' :
                    data.beta > 1 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {data.beta > 1.5 ? 'Yüksek Risk' :
                     data.beta > 1 ? 'Orta Risk' : 'Düşük Risk'}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <p className="mt-4 text-xs text-gray-500">
            Beta &gt; 1: Piyasadan daha volatil
            <br />
            Beta &lt; 1: Piyasadan daha az volatil
          </p>
        </div>
      </div>

      {/* Uyarı */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium">Önemli Uyarı</p>
            <p className="mt-1">
              Bu veriler yatırım tavsiyesi niteliği taşımaz. Yatırım kararlarınızı 
              vermeden önce profesyonel danışmanlık alınız. Gecikmeli veriler 
              kullanılmaktadır.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
