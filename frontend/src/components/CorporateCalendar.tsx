'use client';

/**
 * Kurumsal Takvim Bileşeni
 * =========================
 * Şirketin temettü tarihleri, kazanç açıklama tarihleri ve kurumsal etkinlikleri
 */

import { useEffect, useState } from 'react';
import { Calendar, Clock, DollarSign, AlertCircle, Loader2, CalendarDays } from 'lucide-react';
import { getCorporateCalendar } from '@/lib/api';

interface CorporateCalendarProps {
  symbol: string;
}

export default function CorporateCalendar({ symbol }: CorporateCalendarProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await getCorporateCalendar(symbol);
        setData(result);
      } catch (err: any) {
        setError('Takvim verisi yüklenemedi');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [symbol]);

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('tr-TR', { 
        day: 'numeric', month: 'long', year: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  const isUpcoming = (dateStr: string | null | undefined) => {
    if (!dateStr) return false;
    try {
      return new Date(dateStr) > new Date();
    } catch {
      return false;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-gray-900">Kurumsal Takvim</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
          <span className="ml-2 text-gray-500 text-sm">Yükleniyor...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-gray-900">Kurumsal Takvim</h3>
        </div>
        <div className="flex items-center gap-2 text-gray-500 text-sm py-4">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  const hasCalendar = data?.has_calendar;
  const hasEarnings = data?.has_earnings;
  const calendar = data?.calendar;
  const earningsDates = data?.earnings_dates;

  if (!hasCalendar && !hasEarnings) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-gray-900">Kurumsal Takvim</h3>
        </div>
        <p className="text-gray-500 text-sm py-4">
          Bu hisse için takvim verisi bulunamadı.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="w-5 h-5 text-emerald-600" />
        <h3 className="font-semibold text-gray-900">Kurumsal Takvim</h3>
      </div>

      <div className="space-y-6">
        {/* Takvim Bilgileri */}
        {hasCalendar && calendar && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-green-600" />
              Temettü & Kurumsal Etkinlikler
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.entries(calendar).map(([key, value]) => {
                const label = getCalendarLabel(key);
                const dateStr = typeof value === 'string' ? value : 
                  Array.isArray(value) ? (value as string[]).join(', ') : String(value ?? '-');
                const upcoming = isUpcoming(typeof value === 'string' ? value : null);
                
                return (
                  <div 
                    key={key} 
                    className={`p-3 rounded-lg border ${
                      upcoming 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="text-xs text-gray-500 mb-1">{label}</div>
                    <div className={`font-medium text-sm ${
                      upcoming ? 'text-green-700' : 'text-gray-900'
                    }`}>
                      {formatDate(dateStr) !== '-' ? formatDate(dateStr) : dateStr}
                      {upcoming && (
                        <span className="ml-2 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                          Yaklaşan
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Kazanç Tarihleri */}
        {hasEarnings && earningsDates && earningsDates.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <CalendarDays className="w-4 h-4 text-blue-600" />
              Kazanç Açıklama Tarihleri
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    {Object.keys(earningsDates[0]).map((col) => (
                      <th key={col} className="text-left py-2 px-3 text-gray-500 font-medium text-xs">
                        {getEarningsLabel(col)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {earningsDates.slice(0, 10).map((row: any, idx: number) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      {Object.entries(row).map(([col, val]) => {
                        const isDate = col.toLowerCase().includes('date') || col === 'index';
                        return (
                          <td key={col} className="py-2 px-3 text-gray-800">
                            {isDate && typeof val === 'string' ? formatDate(val) :
                             typeof val === 'number' ? val.toLocaleString('tr-TR') :
                             val != null ? String(val) : '-'}
                          </td>
                        );
                      })}
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

function getCalendarLabel(key: string): string {
  const labels: Record<string, string> = {
    'ex_dividend_date': 'Temettü Hak Tarihi',
    'exDividendDate': 'Temettü Hak Tarihi',
    'dividend_date': 'Temettü Ödeme Tarihi',
    'dividendDate': 'Temettü Ödeme Tarihi',
    'earnings_date': 'Kazanç Açıklama',
    'earningsDate': 'Kazanç Açıklama',
    'earnings_high': 'Kazanç Tahmini (Üst)',
    'earnings_low': 'Kazanç Tahmini (Alt)',
    'earnings_average': 'Kazanç Tahmini (Ort)',
    'revenue_average': 'Gelir Tahmini (Ort)',
    'revenue_high': 'Gelir Tahmini (Üst)',
    'revenue_low': 'Gelir Tahmini (Alt)',
  };
  return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function getEarningsLabel(key: string): string {
  const labels: Record<string, string> = {
    'index': 'Tarih',
    'date': 'Tarih',
    'eps_estimate': 'HBK Tahmini',
    'epsEstimate': 'HBK Tahmini',
    'reported_eps': 'Gerçekleşen HBK',
    'reportedEps': 'Gerçekleşen HBK',
    'surprise': 'Sürpriz',
    'surprise_percent': 'Sürpriz %',
    'surprisePercent': 'Sürpriz %',
  };
  return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
