'use client';

/**
 * ETF Sahipliği Bileşeni
 * =======================
 * Hisseyi portföyünde tutan uluslararası ETF'leri gösterir
 */

import { useEffect, useState } from 'react';
import { Globe, TrendingUp, AlertCircle, Loader2 } from 'lucide-react';
import { getETFHolders } from '@/lib/api';

interface ETFHoldersProps {
  symbol: string;
}

interface ETFHolder {
  [key: string]: any;
}

export default function ETFHolders({ symbol }: ETFHoldersProps) {
  const [data, setData] = useState<{ holders: ETFHolder[]; count: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await getETFHolders(symbol) as { holders: ETFHolder[]; count: number };
        setData(result);
      } catch (err: any) {
        setError('ETF sahiplik verisi yüklenemedi');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [symbol]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">ETF Sahipliği</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-500 text-sm">Yükleniyor...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">ETF Sahipliği</h3>
        </div>
        <div className="flex items-center gap-2 text-gray-500 text-sm py-4">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!data || data.count === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">ETF Sahipliği</h3>
        </div>
        <p className="text-gray-500 text-sm py-4">
          Bu hisse için ETF sahiplik verisi bulunamadı.
        </p>
      </div>
    );
  }

  // Değişken isimlerini anlamlandır
  const getColumnLabel = (key: string) => {
    const labels: Record<string, string> = {
      'symbol': 'ETF Sembol',
      'name': 'ETF Adı',
      'fund_name': 'Fon Adı',
      'etf_name': 'ETF Adı',
      'percent': 'Ağırlık %',
      'weight': 'Ağırlık %',
      'shares': 'Hisse Adedi',
      'value': 'Değer',
      'market_value': 'Piyasa Değeri',
    };
    return labels[key.toLowerCase()] || key;
  };

  const holders = data.holders;
  const columns = holders.length > 0 ? Object.keys(holders[0]) : [];

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">ETF Sahipliği</h3>
        </div>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
          {data.count} ETF
        </span>
      </div>

      <p className="text-xs text-gray-500 mb-4">
        Bu hisseyi portföyünde tutan uluslararası ETF&apos;ler
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              {columns.map((col) => (
                <th key={col} className="text-left py-2 px-3 text-gray-500 font-medium text-xs">
                  {getColumnLabel(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {holders.slice(0, 20).map((holder, idx) => (
              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                {columns.map((col) => {
                  const val = holder[col];
                  const isPercent = col.toLowerCase().includes('percent') || col.toLowerCase().includes('weight');
                  const isNumber = typeof val === 'number';
                  
                  return (
                    <td key={col} className="py-2 px-3 text-gray-800">
                      {isPercent && isNumber
                        ? `%${val.toFixed(2)}`
                        : isNumber
                        ? val.toLocaleString('tr-TR')
                        : val ?? '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {holders.length > 20 && (
        <p className="text-xs text-gray-400 mt-3 text-center">
          İlk 20 ETF gösteriliyor. Toplam: {holders.length}
        </p>
      )}
    </div>
  );
}
