'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, Time } from 'lightweight-charts';
import Link from 'next/link';

interface ComparisonStock {
  symbol: string;
  name: string;
  data: Array<{
    time: number;
    value: number;
    normalizedValue: number;
  }>;
  startPrice: number;
  endPrice: number;
  totalReturn: number;
  volatility: number;
  maxDrawdown: number;
}

const COLORS = [
  '#3b82f6', // blue
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
];

const POPULAR_STOCKS = [
  'THYAO', 'GARAN', 'AKBNK', 'ASELS', 'KCHOL',
  'SAHOL', 'SSE', 'TUPRS', 'EREGL', 'BMAS'
];

export default function ComparePage() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['THYAO', 'GARAN']);
  const [searchQuery, setSearchQuery] = useState('');
  const [period, setPeriod] = useState('1y');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonStock[]>([]);
  const [showNormalized, setShowNormalized] = useState(true);

  const fetchComparison = async () => {
    if (selectedSymbols.length < 2) return;

    setLoading(true);
    setError(null);

    try {
      const symbolsParam = selectedSymbols.join(',');
      const response = await fetch(
        `http://localhost:8001/api/charts/compare?symbols=${symbolsParam}&period=${period}`
      );
      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Veri alınamad');
      }

      setComparisonData(data.stocks);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedSymbols.length >= 2) {
      fetchComparison();
    }
  }, [selectedSymbols, period]);

  useEffect(() => {
    if (!comparisonData || comparisonData.length === 0 || !chartContainerRef.current) return;

    // Mevcut grafii temizle
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#2d2d44' },
        horzLines: { color: '#2d2d44' },
      },
      width: chartContainerRef.current.clientWidth,
      height: window.innerWidth < 640 ? 300 : 500,
      crosshair: {
        mode: 1,
      },
      timeScale: {
        borderColor: '#2d2d44',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: '#2d2d44',
      },
    });

    chartRef.current = chart;

    (comparisonData || []).forEach((stock, index) => {
      const series = chart.addLineSeries({
        color: COLORS[index % COLORS.length],
        lineWidth: 2,
        title: stock.symbol,
      });

      const chartData = stock.data.map((d) => ({
        time: d.time as Time,
        value: showNormalized ? d.normalizedValue : d.value,
      }));

      series.setData(chartData);
    });

    chart.timeScale().fitContent();

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [comparisonData, showNormalized]);

  // Resize handler
  useEffect(() => {
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const addSymbol = (symbol: string) => {
    const upperSymbol = symbol.toUpperCase().replace('.S', '');
    if (!selectedSymbols.includes(upperSymbol) && selectedSymbols.length < 8) {
      setSelectedSymbols([...selectedSymbols, upperSymbol]);
    }
    setSearchQuery('');
  };

  const removeSymbol = (symbol: string) => {
    setSelectedSymbols(selectedSymbols.filter(s => s !== symbol));
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      addSymbol(searchQuery.trim());
    }
  };

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
              <Link href="/heatmap" className="text-gray-300 hover:text-white">Isı Haritası</Link>
              <Link href="/compare" className="text-blue-400 font-semibold">Karşılaştır</Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        <div className="mb-4 sm:mb-8">
          <h1 className="text-xl sm:text-3xl font-bold text-white mb-1 sm:mb-2">Hisse Karşılaştırma</h1>
          <p className="text-gray-400 text-sm sm:text-base">Birden fazla hissenin performansını karşılaştırın</p>
        </div>

        {/* Hisse Seimi */}
        <div className="bg-gray-800/50 rounded-xl p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 mb-4">
            <div className="flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Hisse kodu ekle (Örn: THYAO)"
                className="w-full px-3 sm:px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
              />
            </div>
            <button
              onClick={() => searchQuery && addSymbol(searchQuery)}
              disabled={!searchQuery || selectedSymbols.length >= 8}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
            >
              Ekle
            </button>
          </div>

          {/* Seili Hisseler */}
          <div className="flex flex-wrap gap-2 mb-4">
            {selectedSymbols.map((symbol, index) => (
              <div
                key={symbol}
                className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1 rounded-full text-sm"
                style={{ backgroundColor: COLORS[index % COLORS.length] + '30' }}
              >
                <div
                  className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-white font-medium">{symbol}</span>
                <button
                  onClick={() => removeSymbol(symbol)}
                  className="text-gray-400 hover:text-white"
                >

                </button>
              </div>
            ))}
          </div>

          {/* Popler Hisseler */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-gray-400 text-xs sm:text-sm">Popüler:</span>
            {POPULAR_STOCKS.filter(s => !selectedSymbols.includes(s)).slice(0, 5).map((symbol) => (
              <button
                key={symbol}
                onClick={() => addSymbol(symbol)}
                disabled={selectedSymbols.length >= 8}
                className="px-2.5 sm:px-3 py-1 bg-gray-700 text-gray-300 rounded-full text-xs sm:text-sm hover:bg-gray-600 disabled:opacity-50"
              >
                + {symbol}
              </button>
            ))}
          </div>
        </div>

        {/* Kontroller */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 mb-4">
          <div className="flex gap-1.5 sm:gap-2 overflow-x-auto">
            {['1mo', '3mo', '6mo', '1y', '2y', '5y'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${period === p
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
              >
                {p.toUpperCase()}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowNormalized(!showNormalized)}
            className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-medium sm:ml-auto ${showNormalized
              ? 'bg-purple-500 text-white'
              : 'bg-gray-700 text-gray-300'
              }`}
          >
            {showNormalized ? 'Normalize (%)' : 'Gerçek Fiyat (₺)'}
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64 sm:h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 sm:p-6 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        ) : selectedSymbols.length < 2 ? (
          <div className="bg-gray-800/50 rounded-xl p-8 sm:p-12 text-center">
            <p className="text-gray-400 text-base sm:text-lg">Karşılaştırma için en az 2 hisse seçin</p>
          </div>
        ) : (
          <>
            {/* Grafik */}
            <div className="bg-gray-800/50 rounded-xl p-3 sm:p-4 mb-4 sm:mb-6">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <h3 className="text-white font-semibold text-sm sm:text-base">
                  {showNormalized ? 'Normalize Edilmiş Performans (%)' : 'Fiyat Grafiği (₺)'}
                </h3>
              </div>
              <div ref={chartContainerRef} className="w-full" />
            </div>

            {/* İstatistikler */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
              {(comparisonData || []).map((stock, index) => (
                <Link
                  key={stock.symbol}
                  href={`/stock/${stock.symbol}`}
                  className="bg-gray-800/50 rounded-xl p-4 sm:p-6 hover:bg-gray-800/70 transition"
                >
                  <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                    <div
                      className="w-3 h-3 sm:w-4 sm:h-4 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <div className="overflow-hidden">
                      <h4 className="text-white font-bold text-sm sm:text-base">{stock.symbol}</h4>
                      <p className="text-gray-400 text-xs sm:text-sm truncate">{stock.name}</p>
                    </div>
                  </div>

                  <div className="space-y-2 sm:space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400 text-xs sm:text-sm">Toplam Getiri</span>
                      <span className={`font-semibold ${stock.totalReturn >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                        {stock.totalReturn >= 0 ? '+' : ''}{stock.totalReturn.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400 text-xs sm:text-sm">Volatilite</span>
                      <span className="text-white font-semibold">
                        {stock.volatility.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400 text-xs sm:text-sm">Maks. Düşüş</span>
                      <span className="text-red-400 font-semibold">
                        {stock.maxDrawdown.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400 text-xs sm:text-sm">Başlangıç</span>
                      <span className="text-white">{stock.startPrice.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400 text-sm">Güncel</span>
                      <span className="text-white">{stock.endPrice.toFixed(2)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {/* Sralama Tablosu */}
            <div className="bg-gray-800/50 rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4">Performans Sıralaması</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-gray-400 text-sm border-b border-gray-700">
                      <th className="text-left py-3 px-4">Sıra</th>
                      <th className="text-left py-3 px-4">Hisse</th>
                      <th className="text-right py-3 px-4">Getiri</th>
                      <th className="text-right py-3 px-4">Volatilite</th>
                      <th className="text-right py-3 px-4">Max D</th>
                      <th className="text-right py-3 px-4">Risk/Getiri</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...(comparisonData || [])]
                      .sort((a, b) => b.totalReturn - a.totalReturn)
                      .map((stock, index) => {
                        const riskReturn = stock.volatility > 0
                          ? stock.totalReturn / stock.volatility
                          : 0;
                        const originalndex = (comparisonData || []).findIndex(s => s.symbol === stock.symbol);

                        return (
                          <tr key={stock.symbol} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                            <td className="py-3 px-4">
                              <span className={`
                                w-6 h-6 rounded-full inline-flex items-center justify-center text-sm font-bold
                                ${index === 0 ? 'bg-yellow-500 text-black' :
                                  index === 1 ? 'bg-gray-400 text-black' :
                                    index === 2 ? 'bg-orange-600 text-white' : 'bg-gray-700 text-white'}
                              `}>
                                {index + 1}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <div
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: COLORS[originalndex % COLORS.length] }}
                                />
                                <Link
                                  href={`/stock/${stock.symbol}`}
                                  className="text-white font-medium hover:text-blue-400"
                                >
                                  {stock.symbol}
                                </Link>
                              </div>
                            </td>
                            <td className={`py-3 px-4 text-right font-semibold ${stock.totalReturn >= 0 ? 'text-green-400' : 'text-red-400'
                              }`}>
                              {stock.totalReturn >= 0 ? '+' : ''}{stock.totalReturn.toFixed(2)}%
                            </td>
                            <td className="py-3 px-4 text-right text-white">
                              {stock.volatility.toFixed(2)}%
                            </td>
                            <td className="py-3 px-4 text-right text-red-400">
                              {stock.maxDrawdown.toFixed(2)}%
                            </td>
                            <td className={`py-3 px-4 text-right font-semibold ${riskReturn >= 0.5 ? 'text-green-400' :
                              riskReturn >= 0 ? 'text-yellow-400' : 'text-red-400'
                              }`}>
                              {riskReturn.toFixed(2)}
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
