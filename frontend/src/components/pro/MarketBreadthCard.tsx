'use client';

import React from 'react';
import type { MarketBreadth } from '@/types';

interface MarketBreadthCardProps {
  data: MarketBreadth;
}

export default function MarketBreadthCard({ data }: MarketBreadthCardProps) {
  const totalStocks = (data.advancing || 0) + (data.declining || 0) + (data.unchanged || 0);
  const advancingPercent = totalStocks > 0 ? ((data.advancing || 0) / totalStocks) * 100 : 0;
  const decliningPercent = totalStocks > 0 ? ((data.declining || 0) / totalStocks) * 100 : 0;
  const unchangedPercent = totalStocks > 0 ? ((data.unchanged || 0) / totalStocks) * 100 : 0;

  // Use market_signal or breadth_signal or breadth field
  const signalText = data.market_signal || data.breadth_signal || data.breadth || 'NÖTR';

  const getBreadthSignalColor = (signal: string) => {
    const s = (signal || '').toLowerCase();
    if (s.includes('bullish') || s.includes('yükseliş') || s.includes('güçlü') || s.includes('al')) {
      return 'text-up bg-up/10 border-up/20';
    }
    if (s.includes('bearish') || s.includes('düşüş') || s.includes('sat')) {
      return 'text-down bg-down/10 border-down/20';
    }
    return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
  };

  // Safe access for optional fields
  const adRatio = data.ad_ratio ?? 1;
  const newHighs = data.new_highs ?? 0;
  const newLows = data.new_lows ?? 0;
  const pctSma20 = data.percent_above_sma20 ?? 50;
  const pctSma50 = data.percent_above_sma50 ?? 50;
  const pctSma200 = data.percent_above_sma200 ?? 50;

  return (
    <div className="bg-surface rounded-lg p-6">
      <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <span>📊</span> Piyasa Genişliği
      </h3>

      {/* Signal Badge */}
      <div className={`p-3 rounded-lg border mb-6 text-center ${getBreadthSignalColor(signalText)}`}>
        <div className="text-lg font-bold">{signalText}</div>
      </div>

      {/* Advance/Decline Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-up">Yükselen: {data.advancing || 0}</span>
          <span className="text-muted">Değişmeyen: {data.unchanged || 0}</span>
          <span className="text-down">Düşen: {data.declining || 0}</span>
        </div>
        <div className="h-4 bg-card rounded-full overflow-hidden flex">
          <div
            className="bg-up transition-all duration-500"
            style={{ width: `${advancingPercent}%` }}
          />
          <div
            className="bg-gray-500 transition-all duration-500"
            style={{ width: `${unchangedPercent}%` }}
          />
          <div
            className="bg-down transition-all duration-500"
            style={{ width: `${decliningPercent}%` }}
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-card rounded-lg p-3">
          <div className="text-sm text-muted">A/D Oranı</div>
          <div className={`text-xl font-bold ${adRatio > 1 ? 'text-up' :
              adRatio < 1 ? 'text-down' : 'text-muted'
            }`}>
            {adRatio.toFixed(2)}
          </div>
        </div>
        <div className="bg-card rounded-lg p-3">
          <div className="text-sm text-muted">Yeni Zirveler</div>
          <div className="text-xl font-bold text-up">{newHighs}</div>
        </div>
        <div className="bg-card rounded-lg p-3">
          <div className="text-sm text-muted">Yeni Dipler</div>
          <div className="text-xl font-bold text-down">{newLows}</div>
        </div>
      </div>

      {/* Moving Average Breadth - Only show if sma data available */}
      {(data.percent_above_sma20 !== undefined || data.percent_above_sma50 !== undefined || data.percent_above_sma200 !== undefined) && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted">Hareketli Ortalama Üstünde</h4>

          {/* SMA 20 */}
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted">20 Günlük MA Üstünde</span>
              <span className={pctSma20 > 50 ? 'text-up' : 'text-down'}>
                %{pctSma20.toFixed(1)}
              </span>
            </div>
            <div className="h-2 bg-card rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${pctSma20 > 50 ? 'bg-up' : 'bg-down'
                  }`}
                style={{ width: `${pctSma20}%` }}
              />
            </div>
          </div>

          {/* SMA 50 */}
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted">50 Günlük MA Üstünde</span>
              <span className={pctSma50 > 50 ? 'text-up' : 'text-down'}>
                %{pctSma50.toFixed(1)}
              </span>
            </div>
            <div className="h-2 bg-card rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${pctSma50 > 50 ? 'bg-up' : 'bg-down'
                  }`}
                style={{ width: `${pctSma50}%` }}
              />
            </div>
          </div>

          {/* SMA 200 */}
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted">200 Günlük MA Üstünde</span>
              <span className={pctSma200 > 50 ? 'text-up' : 'text-down'}>
                %{pctSma200.toFixed(1)}
              </span>
            </div>
            <div className="h-2 bg-card rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${pctSma200 > 50 ? 'bg-up' : 'bg-down'
                  }`}
                style={{ width: `${pctSma200}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Interpretation */}
      <div className="mt-6 p-4 bg-card rounded-lg">
        <h4 className="font-semibold mb-2">📖 Piyasa Genişliği Yorumu</h4>
        <div className="text-sm text-muted space-y-1">
          {adRatio > 2 && (
            <p className="text-up">✓ A/D oranı çok güçlü - Geniş tabanlı yükseliş</p>
          )}
          {adRatio > 1 && adRatio <= 2 && (
            <p className="text-up">✓ A/D oranı pozitif - Piyasa genelinde yükseliş</p>
          )}
          {adRatio < 1 && adRatio >= 0.5 && (
            <p className="text-down">✗ A/D oranı negatif - Piyasa genelinde düşüş</p>
          )}
          {adRatio < 0.5 && (
            <p className="text-down">✗ A/D oranı çok zayıf - Geniş tabanlı satış</p>
          )}
          {newHighs > newLows * 2 && (
            <p className="text-up">✓ Yeni zirveler yeni diplerden fazla - Boğa piyasası</p>
          )}
          {newLows > newHighs * 2 && (
            <p className="text-down">✗ Yeni dipler yeni zirvelerden fazla - Ayı piyasası</p>
          )}
          {pctSma200 < 30 && (
            <p className="text-yellow-400">⚠ Çoğu hisse 200 günlük MA altında - Aşırı satım olabilir</p>
          )}
          {pctSma200 > 70 && (
            <p className="text-yellow-400">⚠ Çoğu hisse 200 günlük MA üstünde - Aşırı alım olabilir</p>
          )}
        </div>
      </div>
    </div>
  );
}
