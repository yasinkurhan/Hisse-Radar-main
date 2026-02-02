'use client';

import React, { useState, useEffect } from 'react';
import { getMarketOverview, getSectorRotation, getFearGreedIndex } from '@/lib/api';
import type { MarketOverview, FearGreedIndex, SectorPerformance } from '@/types';
import FearGreedGauge from '@/components/pro/FearGreedGauge';
import SectorRotation from '@/components/pro/SectorRotation';
import MarketBreadthCard from '@/components/pro/MarketBreadthCard';

export default function MarketOverviewPage() {
  const [marketData, setMarketData] = useState<MarketOverview | null>(null);
  const [fearGreed, setFearGreed] = useState<FearGreedIndex | null>(null);
  const [sectors, setSectors] = useState<SectorPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [marketRes, fearGreedRes, sectorRes] = await Promise.all([
        getMarketOverview().catch(() => null),
        getFearGreedIndex().catch(() => null),
        getSectorRotation().catch(() => null)
      ]);

      if (marketRes) setMarketData(marketRes as MarketOverview);
      if (fearGreedRes) setFearGreed(fearGreedRes as FearGreedIndex);
      if (sectorRes) setSectors((sectorRes as any).sectors || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Veri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
              <p className="text-muted">Piyasa verileri yükleniyor...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-surface rounded-lg p-8 text-center">
            <div className="text-red-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold mb-2">Veri Yüklenemedi</h2>
            <p className="text-muted mb-4">{error}</p>
            <button 
              onClick={loadData}
              className="px-4 py-2 bg-accent text-white rounded hover:bg-accent/80"
            >
              Tekrar Dene
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-surface rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <span>🌍</span> Piyasa Genel Görünümü
              </h1>
              <p className="text-muted mt-1">
                BIST piyasasının anlık durumu ve sektör analizi
              </p>
            </div>
            <button
              onClick={loadData}
              className="flex items-center gap-2 px-4 py-2 bg-card hover:bg-card/80 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Yenile
            </button>
          </div>
        </div>

        {/* Market Regime & Signal */}
        {marketData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-surface rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Piyasa Rejimi</h3>
              <div className={`p-4 rounded-lg border ${
                marketData.market_regime === 'trending_up' ? 'bg-up/10 border-up/20' :
                marketData.market_regime === 'trending_down' ? 'bg-down/10 border-down/20' :
                marketData.market_regime === 'volatile' ? 'bg-orange-500/10 border-orange-500/20' :
                'bg-yellow-500/10 border-yellow-500/20'
              }`}>
                <div className="text-3xl mb-2">
                  {marketData.market_regime === 'trending_up' && '📈'}
                  {marketData.market_regime === 'trending_down' && '📉'}
                  {marketData.market_regime === 'volatile' && '🌊'}
                  {marketData.market_regime === 'ranging' && '↔️'}
                </div>
                <div className={`text-xl font-bold ${
                  marketData.market_regime === 'trending_up' ? 'text-up' :
                  marketData.market_regime === 'trending_down' ? 'text-down' :
                  marketData.market_regime === 'volatile' ? 'text-orange-400' :
                  'text-yellow-400'
                }`}>
                  {marketData.market_regime === 'trending_up' && 'Yükseliş Trendi'}
                  {marketData.market_regime === 'trending_down' && 'Düşüş Trendi'}
                  {marketData.market_regime === 'volatile' && 'Yüksek Volatilite'}
                  {marketData.market_regime === 'ranging' && 'Yatay Seyir'}
                </div>
              </div>
            </div>

            <div className="bg-surface rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Genel Sinyal</h3>
              {(() => {
                const signalValue = typeof marketData.overall_signal === 'object' 
                  ? (marketData.overall_signal?.signal || '') 
                  : (marketData.overall_signal || '');
                const signalStr = String(signalValue).toLowerCase();
                const isBullish = signalStr.includes('bullish') || signalStr.includes('al') || signalStr.includes('yüksel');
                const isBearish = signalStr.includes('bearish') || signalStr.includes('sat') || signalStr.includes('düş');
                
                return (
                  <div className={`p-4 rounded-lg border ${
                    isBullish ? 'bg-up/10 border-up/20' :
                    isBearish ? 'bg-down/10 border-down/20' :
                    'bg-yellow-500/10 border-yellow-500/20'
                  }`}>
                    <div className="text-3xl mb-2">
                      {isBullish ? '🟢' : isBearish ? '🔴' : '🟡'}
                    </div>
                    <div className={`text-xl font-bold ${
                      isBullish ? 'text-up' : isBearish ? 'text-down' : 'text-yellow-400'
                    }`}>
                      {signalValue || 'Belirsiz'}
                    </div>
                    {typeof marketData.overall_signal === 'object' && marketData.overall_signal?.recommendation && (
                      <div className="text-sm text-muted mt-2">{marketData.overall_signal.recommendation}</div>
                    )}
                    {typeof marketData.overall_signal === 'object' && marketData.overall_signal?.score !== undefined && (
                      <div className="text-sm text-muted mt-1">Skor: {marketData.overall_signal.score.toFixed(1)}</div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* Fear & Greed + Market Breadth */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {fearGreed && <FearGreedGauge data={fearGreed} />}
          {marketData?.breadth && <MarketBreadthCard data={marketData.breadth} />}
        </div>

        {/* Sector Rotation */}
        {sectors.length > 0 && <SectorRotation sectors={sectors} />}

        {/* Quick Stats */}
        {marketData?.breadth && (
          <div className="bg-surface rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">📊 Hızlı İstatistikler</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="bg-card rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-up">{marketData.breadth.advancing}</div>
                <div className="text-sm text-muted">Yükselen</div>
              </div>
              <div className="bg-card rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-down">{marketData.breadth.declining}</div>
                <div className="text-sm text-muted">Düşen</div>
              </div>
              <div className="bg-card rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-muted">{marketData.breadth.unchanged}</div>
                <div className="text-sm text-muted">Değişmeyen</div>
              </div>
              <div className="bg-card rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-up">{marketData.breadth.new_highs}</div>
                <div className="text-sm text-muted">Yeni Zirve</div>
              </div>
              <div className="bg-card rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-down">{marketData.breadth.new_lows}</div>
                <div className="text-sm text-muted">Yeni Dip</div>
              </div>
              <div className="bg-card rounded-lg p-4 text-center">
                <div className={`text-2xl font-bold ${marketData.breadth.ad_ratio > 1 ? 'text-up' : 'text-down'}`}>
                  {marketData.breadth.ad_ratio.toFixed(2)}
                </div>
                <div className="text-sm text-muted">A/D Oranı</div>
              </div>
            </div>
          </div>
        )}

        {/* Info Card */}
        <div className="bg-surface rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">ℹ️ Piyasa Analizi Hakkında</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-muted">
            <div>
              <h4 className="font-medium text-foreground mb-2">Korku & Açgözlülük Endeksi</h4>
              <p>
                Piyasa duyarlılığını 0-100 arasında ölçer. 0-25 arası aşırı korku (potansiyel alım fırsatı), 
                75-100 arası aşırı açgözlülük (dikkatli olunmalı) anlamına gelir.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-foreground mb-2">Piyasa Genişliği</h4>
              <p>
                Yükselen/düşen hisse oranı piyasanın genel sağlığını gösterir. 
                A/D oranı 1'in üzerindeyse piyasa genelinde yükseliş var demektir.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-foreground mb-2">Sektör Rotasyonu</h4>
              <p>
                Sektörlerin performans döngüsünü takip eder. "Lider" sektörler en iyi performansı gösterirken, 
                "Yükselen" sektörler momentum kazanıyor demektir.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-foreground mb-2">MA Üstündeki Hisseler</h4>
              <p>
                Hareketli ortalamaların üzerinde işlem gören hisse yüzdesi. 
                %50'nin üzerinde değerler genel yükseliş trendini, altında ise düşüşü işaret eder.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
