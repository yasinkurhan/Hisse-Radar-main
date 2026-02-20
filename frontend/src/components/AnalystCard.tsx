'use client';

/**
 * Analist Tahminleri Bileşeni
 * ============================
 * Analist hedef fiyatları ve al/sat önerileri
 */

import { useEffect, useState } from 'react';
import { Target, TrendingUp, TrendingDown, BarChart3, Loader2, Users } from 'lucide-react';
import { getAnalystData } from '@/lib/api';

interface AnalystCardProps {
  symbol: string;
}

interface PriceTargets {
  current: number;
  low: number;
  high: number;
  mean: number;
  median: number;
  numberOfAnalysts: number;
}

interface RecSummary {
  strongBuy: number;
  buy: number;
  hold: number;
  sell: number;
  strongSell: number;
}

export default function AnalystCard({ symbol }: AnalystCardProps) {
  const [data, setData] = useState<{
    price_targets: PriceTargets | null;
    recommendations_summary: RecSummary | null;
    has_data: boolean;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const result = await getAnalystData(symbol) as {
          price_targets: PriceTargets | null;
          recommendations_summary: RecSummary | null;
          has_data: boolean;
        };
        setData(result);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [symbol]);

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center justify-center py-8 text-gray-300">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Analist verileri yükleniyor...
        </div>
      </div>
    );
  }

  if (!data?.has_data) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Target className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-bold text-white">Analist Tahminleri</h3>
        </div>
        <p className="text-gray-300 text-sm">Bu hisse için analist verisi bulunamadı.</p>
      </div>
    );
  }

  const targets = data.price_targets && data.price_targets.mean > 0 ? data.price_targets : null;
  const recs = data.recommendations_summary;

  // Recommendation bar chart total
  const recTotal = recs
    ? recs.strongBuy + recs.buy + recs.hold + recs.sell + recs.strongSell
    : 0;

  // Her iki veri de yoksa "veri yok" mesajı göster
  if (!targets && recTotal === 0) {
    return (
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Target className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-bold text-white">Analist Tahminleri</h3>
        </div>
        <p className="text-gray-300 text-sm">Bu hisse için analist hedef fiyatı bulunamadı.</p>
      </div>
    );
  }

  // Upside potential
  const upsidePct = targets
    ? (((targets.mean - targets.current) / targets.current) * 100).toFixed(1)
    : null;
  const isUpside = upsidePct ? parseFloat(upsidePct) > 0 : false;

  return (
    <div className="space-y-4">
      {/* Hedef Fiyat Kartı */}
      {targets && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-400" />
              <h3 className="text-lg font-bold text-white">Hedef Fiyat Analizi</h3>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-semibold bg-gray-700 text-gray-200 px-2.5 py-1 rounded-full">
              <Users className="w-3 h-3" />
              {targets.numberOfAnalysts} Analist
            </div>
          </div>

          {/* Current vs Target */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-400 mb-1">Güncel Fiyat</p>
              <p className="text-xl font-bold text-white">₺{targets.current.toFixed(2)}</p>
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
              <p className="text-xs font-medium text-gray-400 mb-1">Ort. Hedef</p>
              <p className={`text-xl font-bold ${isUpside ? 'text-green-300' : 'text-red-300'}`}>
                ₺{targets.mean.toFixed(2)}
              </p>
              {upsidePct && (
                <div className={`flex items-center gap-1 text-xs font-semibold ${isUpside ? 'text-green-400' : 'text-red-400'}`}>
                  {isUpside ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  %{upsidePct} potansiyel
                </div>
              )}
            </div>
          </div>

          {/* Price Range Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-xs font-medium text-gray-300 mb-2">
              <span>En Düşük: ₺{targets.low.toFixed(2)}</span>
              <span>Medyan: ₺{targets.median.toFixed(2)}</span>
              <span>En Yüksek: ₺{targets.high.toFixed(2)}</span>
            </div>
            <div className="relative h-3 bg-gray-700 rounded-full overflow-hidden">
              {/* Range bar */}
              <div
                className="absolute h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full"
                style={{
                  left: '0%',
                  width: '100%',
                }}
              />
              {/* Current price marker */}
              <div
                className="absolute top-0 h-full w-0.5 bg-white"
                style={{
                  left: `${Math.max(0, Math.min(100, ((targets.current - targets.low) / (targets.high - targets.low)) * 100))}%`,
                }}
              />
            </div>
            <div className="flex justify-between text-xs mt-1">
              <span className="text-red-400">Düşüş</span>
              <span className="text-white text-xs">▲ Güncel</span>
              <span className="text-green-400">Yükseliş</span>
            </div>
          </div>
        </div>
      )}

      {/* Analist Önerileri */}
      {recs && recTotal > 0 && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-bold text-white">Analist Önerileri</h3>
            <span className="text-xs font-semibold bg-gray-700 text-gray-200 px-2 py-0.5 rounded-full">{recTotal} analist</span>
          </div>

          {/* Stacked bar */}
          <div className="flex h-8 rounded-lg overflow-hidden mb-3">
            {recs.strongBuy > 0 && (
              <div
                className="bg-green-600 flex items-center justify-center text-xs font-bold text-white"
                style={{ width: `${(recs.strongBuy / recTotal) * 100}%` }}
                title={`Güçlü Al: ${recs.strongBuy}`}
              >
                {recs.strongBuy}
              </div>
            )}
            {recs.buy > 0 && (
              <div
                className="bg-green-400 flex items-center justify-center text-xs font-bold text-gray-900"
                style={{ width: `${(recs.buy / recTotal) * 100}%` }}
                title={`Al: ${recs.buy}`}
              >
                {recs.buy}
              </div>
            )}
            {recs.hold > 0 && (
              <div
                className="bg-yellow-500 flex items-center justify-center text-xs font-bold text-gray-900"
                style={{ width: `${(recs.hold / recTotal) * 100}%` }}
                title={`Tut: ${recs.hold}`}
              >
                {recs.hold}
              </div>
            )}
            {recs.sell > 0 && (
              <div
                className="bg-red-400 flex items-center justify-center text-xs font-bold text-white"
                style={{ width: `${(recs.sell / recTotal) * 100}%` }}
                title={`Sat: ${recs.sell}`}
              >
                {recs.sell}
              </div>
            )}
            {recs.strongSell > 0 && (
              <div
                className="bg-red-600 flex items-center justify-center text-xs font-bold text-white"
                style={{ width: `${(recs.strongSell / recTotal) * 100}%` }}
                title={`Güçlü Sat: ${recs.strongSell}`}
              >
                {recs.strongSell}
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 text-xs font-medium">
            {recs.strongBuy > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-green-600 rounded" />
                <span className="text-gray-200">Güçlü Al ({recs.strongBuy})</span>
              </div>
            )}
            {recs.buy > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-green-400 rounded" />
                <span className="text-gray-200">Al ({recs.buy})</span>
              </div>
            )}
            {recs.hold > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-yellow-500 rounded" />
                <span className="text-gray-200">Tut ({recs.hold})</span>
              </div>
            )}
            {recs.sell > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-red-400 rounded" />
                <span className="text-gray-200">Sat ({recs.sell})</span>
              </div>
            )}
            {recs.strongSell > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-red-600 rounded" />
                <span className="text-gray-200">Güçlü Sat ({recs.strongSell})</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
