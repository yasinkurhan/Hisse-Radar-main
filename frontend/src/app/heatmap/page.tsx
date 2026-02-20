'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface SectorData {
  sector: string;
  avgChange: number;
  totalVolume: number;
  stockCount: number;
  topGainer: { symbol: string; change: number } | null;
  topLoser: { symbol: string; change: number } | null;
  stocks: Array<{
    symbol: string;
    name: string;
    change: number;
    volume: number;
    price: number;
  }>;
}

export default function HeatmapPage() {
  const [sectors, setSectors] = useState<SectorData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSector, setSelectedSector] = useState<string | null>(null);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/charts/sector-heatmap');
        const data = await response.json();

        if (!data.success) {
          throw new Error(data.error || 'Veri alınamad');
        }

        setSectors(data.sectors);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHeatmap();
  }, []);

  const getHeatColor = (change: number): string => {
    if (change >= 5) return 'bg-green-500';
    if (change >= 3) return 'bg-green-600';
    if (change >= 1) return 'bg-green-700';
    if (change >= 0) return 'bg-green-800';
    if (change >= -1) return 'bg-red-800';
    if (change >= -3) return 'bg-red-700';
    if (change >= -5) return 'bg-red-600';
    return 'bg-red-500';
  };

  const getTextColor = (change: number): string => {
    return Math.abs(change) >= 1 ? 'text-white' : 'text-gray-200';
  };

  const formatVolume = (num: number) => {
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(1) + 'B';
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(1) + 'K';
    return num.toString();
  };

  const selectedSectorData = (sectors || []).find(s => s.sector === selectedSector);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg sm:text-xl"></span>
              </div>
              <span className="text-lg sm:text-xl font-bold text-white">HisseRadar</span>
            </Link>
            <nav className="hidden sm:flex gap-4">
              <Link href="/analysis" className="text-gray-300 hover:text-white">Analiz</Link>
              <Link href="/heatmap" className="text-blue-400 font-semibold">Isı Haritası</Link>
              <Link href="/compare" className="text-gray-300 hover:text-white">Karşılaştır</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        <div className="mb-4 sm:mb-8">
          <h1 className="text-xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Sektör Isı Haritası</h1>
          <p className="text-gray-400 text-sm sm:text-base">Sektörlerin Günlük performansını görsel olarak takip edin</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 sm:p-6 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
            {/* s Haritas */}
            <div className="lg:col-span-2">
              <div className="bg-gray-800/50 rounded-xl p-4 sm:p-6">
                <h2 className="text-lg sm:text-xl font-semibold text-white mb-3 sm:mb-4">Sektör Performansı</h2>

                {/* Renk skalas */}
                <div className="flex items-center gap-2 mb-4 sm:mb-6">
                  <span className="text-gray-400 text-xs sm:text-sm">-5%</span>
                  <div className="flex-1 h-2 sm:h-3 rounded-full bg-gradient-to-r from-red-500 via-gray-600 to-green-500"></div>
                  <span className="text-gray-400 text-xs sm:text-sm">+5%</span>
                </div>

                {/* Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
                  {(sectors || []).map((sector) => (
                    <button
                      key={sector.sector}
                      onClick={() => setSelectedSector(sector.sector)}
                      className={`
                        ${getHeatColor(sector.avgChange)} 
                        ${selectedSector === sector.sector ? 'ring-2 ring-white' : ''}
                        rounded-xl p-2.5 sm:p-4 transition-all hover:scale-105 cursor-pointer
                      `}
                    >
                      <h3 className={`font-semibold text-xs sm:text-sm mb-0.5 sm:mb-1 truncate ${getTextColor(sector.avgChange)}`}>
                        {sector.sector}
                      </h3>
                      <p className={`text-lg sm:text-2xl font-bold ${getTextColor(sector.avgChange)}`}>
                        {sector.avgChange >= 0 ? '+' : ''}{sector.avgChange.toFixed(2)}%
                      </p>
                      <p className={`text-[10px] sm:text-xs opacity-80 ${getTextColor(sector.avgChange)}`}>
                        {sector.stockCount} hisse
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              {/* En İyi/Kt Sektrler */}
              <div className="grid sm:grid-cols-2 gap-3 sm:gap-4 mt-4 sm:mt-6">
                <div className="bg-gray-800/50 rounded-xl p-4 sm:p-6">
                  <h3 className="text-base sm:text-lg font-semibold text-green-400 mb-3 sm:mb-4"> En İyi Sektörler</h3>
                  <div className="space-y-2 sm:space-y-3">
                    {[...(sectors || [])]
                      .sort((a, b) => b.avgChange - a.avgChange)
                      .slice(0, 5)
                      .map((sector, i) => (
                        <div key={sector.sector} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500 text-xs sm:text-sm">{i + 1}.</span>
                            <span className="text-white text-sm sm:text-base truncate max-w-[150px]">{sector.sector}</span>
                          </div>
                          <span className="text-green-400 font-semibold text-sm sm:text-base">
                            +{sector.avgChange.toFixed(2)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-xl p-4 sm:p-6">
                  <h3 className="text-base sm:text-lg font-semibold text-red-400 mb-3 sm:mb-4"> En Kötü Sektörler</h3>
                  <div className="space-y-2 sm:space-y-3">
                    {[...(sectors || [])]
                      .sort((a, b) => a.avgChange - b.avgChange)
                      .slice(0, 5)
                      .map((sector, i) => (
                        <div key={sector.sector} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500 text-xs sm:text-sm">{i + 1}.</span>
                            <span className="text-white text-sm sm:text-base truncate max-w-[150px]">{sector.sector}</span>
                          </div>
                          <span className="text-red-400 font-semibold text-sm sm:text-base">
                            {sector.avgChange.toFixed(2)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Sektr Detay */}
            <div className="lg:col-span-1">
              <div className="bg-gray-800/50 rounded-xl p-4 sm:p-6 lg:sticky lg:top-6">
                <h2 className="text-lg sm:text-xl font-semibold text-white mb-3 sm:mb-4">
                  {selectedSectorData ? selectedSectorData.sector : 'Sektör Seçin'}
                </h2>

                {selectedSectorData ? (
                  <div className="space-y-4 sm:space-y-6">
                    {/* zet */}
                    <div className="grid grid-cols-2 gap-3 sm:gap-4">
                      <div className="bg-gray-700/30 rounded-lg p-2.5 sm:p-3">
                        <p className="text-gray-400 text-xs sm:text-sm">Ort. Değişim</p>
                        <p className={`text-lg sm:text-xl font-bold ${selectedSectorData.avgChange >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                          {selectedSectorData.avgChange >= 0 ? '+' : ''}
                          {selectedSectorData.avgChange.toFixed(2)}%
                        </p>
                      </div>
                      <div className="bg-gray-700/30 rounded-lg p-2.5 sm:p-3">
                        <p className="text-gray-400 text-xs sm:text-sm">Toplam Hacim</p>
                        <p className="text-lg sm:text-xl font-bold text-white">
                          {formatVolume(selectedSectorData.totalVolume)}
                        </p>
                      </div>
                    </div>

                    {/* En İyi/Kt Hisse */}
                    <div className="space-y-2 sm:space-y-3">
                      {selectedSectorData.topGainer && (
                        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-2.5 sm:p-3">
                          <p className="text-green-400 text-xs sm:text-sm"> En Çok Yükselen</p>
                          <div className="flex items-center justify-between mt-1">
                            <Link
                              href={`/stock/${selectedSectorData.topGainer.symbol}`}
                              className="text-white font-semibold hover:text-green-400 text-sm sm:text-base"
                            >
                              {selectedSectorData.topGainer.symbol}
                            </Link>
                            <span className="text-green-400 text-sm sm:text-base">
                              +{selectedSectorData.topGainer.change.toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      )}

                      {selectedSectorData.topLoser && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2.5 sm:p-3">
                          <p className="text-red-400 text-xs sm:text-sm"> En Çok Düşen</p>
                          <div className="flex items-center justify-between mt-1">
                            <Link
                              href={`/stock/${selectedSectorData.topLoser.symbol}`}
                              className="text-white font-semibold hover:text-red-400 text-sm sm:text-base"
                            >
                              {selectedSectorData.topLoser.symbol}
                            </Link>
                            <span className="text-red-400 text-sm sm:text-base">
                              {selectedSectorData.topLoser.change.toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Hisseler Listesi */}
                    <div>
                      <h4 className="text-white font-semibold mb-2 sm:mb-3 text-sm sm:text-base">Sektör Hisseleri</h4>
                      <div className="max-h-56 sm:max-h-64 overflow-y-auto space-y-2">
                        {selectedSectorData.stocks
                          .sort((a, b) => b.change - a.change)
                          .map((stock) => (
                            <Link
                              key={stock.symbol}
                              href={`/stock/${stock.symbol}`}
                              className="flex items-center justify-between p-2 bg-gray-700/30 rounded-lg hover:bg-gray-700/50"
                            >
                              <div>
                                <p className="text-white font-medium text-sm sm:text-base">{stock.symbol}</p>
                                <p className="text-gray-400 text-[10px] sm:text-xs truncate max-w-24 sm:max-w-32">{stock.name}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-white text-sm sm:text-base">{stock.price.toFixed(2)}</p>
                                <p className={`text-xs sm:text-sm ${stock.change >= 0 ? 'text-green-400' : 'text-red-400'
                                  }`}>
                                  {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%
                                </p>
                              </div>
                            </Link>
                          ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-6 sm:py-8 text-sm sm:text-base">
                    Detay görmek için bir sektöre tıklayın
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
