'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { TrendingUp, TrendingDown, Filter, ChevronDown, X, Check, Search, ChevronRight } from 'lucide-react';

interface Stock {
  symbol: string;
  name: string;
  sector: string;
  indexes?: string[];
  current_price?: number;
  change_percent?: number;
  volume?: number;
  market_cap?: number;
}

interface Index {
  id: string;
  name: string;
  description: string;
}

interface StockListProps {
  showSectorFilter?: boolean;
  limit?: number;
}

export default function StockList({ showSectorFilter = true, limit }: StockListProps) {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [filteredStocks, setFilteredStocks] = useState<Stock[]>([]);
  const [sectors, setSectors] = useState<string[]>([]);
  const [indexes, setIndexes] = useState<Index[]>([]);
  const [selectedSector, setSelectedSector] = useState<string>('');
  const [selectedIndex, setSelectedIndex] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showSectorDropdown, setShowSectorDropdown] = useState(false);
  const [showIndexDropdown, setShowIndexDropdown] = useState(false);

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/stocks/');
        const data = await response.json();
        setStocks(data.stocks);
        setSectors(data.sectors);
        setIndexes(data.indexes || []);
        setFilteredStocks(data.stocks);
      } catch (error) {
        console.error('Error fetching stocks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStocks();
  }, []);

  useEffect(() => {
    let result = [...stocks];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        stock =>
          stock.symbol.toLowerCase().includes(query) ||
          stock.name.toLowerCase().includes(query)
      );
    }

    if (selectedSector) {
      result = result.filter(stock => stock.sector === selectedSector);
    }

    if (selectedIndex) {
      result = result.filter(stock => stock.indexes?.includes(selectedIndex));
    }

    setFilteredStocks(result);
  }, [stocks, searchQuery, selectedSector, selectedIndex]);

  const displayedStocks = limit ? filteredStocks.slice(0, limit) : filteredStocks;

  const clearFilters = () => {
    setSelectedSector('');
    setSelectedIndex('');
    setSearchQuery('');
  };

  const hasActiveFilters = selectedSector || selectedIndex || searchQuery;

  const getIndexCount = (indexId: string) => {
    return stocks.filter(s => s.indexes?.includes(indexId)).length;
  };

  const formatLargeNumber = (num: number) => {
    if (num >= 1e12) return (num / 1e12).toFixed(2) + ' T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + ' Mr';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + ' Mn';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + ' B';
    return num.toString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showSectorFilter && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Hisse ara (sembol veya isim)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg 
                         bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition ${
                showFilters || hasActiveFilters
                  ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                  : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>Filtrele</span>
              {hasActiveFilters && (
                <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                  {[selectedSector, selectedIndex, searchQuery].filter(Boolean).length}
                </span>
              )}
              <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Endeks
                  </label>
                  <button
                    onClick={() => {
                      setShowIndexDropdown(!showIndexDropdown);
                      setShowSectorDropdown(false);
                    }}
                    className="w-full flex items-center justify-between px-4 py-2.5 border border-gray-200 dark:border-gray-600 
                             rounded-lg bg-white dark:bg-gray-700 text-left hover:bg-gray-50 dark:hover:bg-gray-600 transition"
                  >
                    <span className={selectedIndex ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
                      {selectedIndex 
                        ? indexes.find(i => i.id === selectedIndex)?.name || selectedIndex
                        : 'Tum Endeksler'}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showIndexDropdown ? 'rotate-180' : ''}`} />
                  </button>

                  {showIndexDropdown && (
                    <div className="absolute z-20 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 
                                  rounded-lg shadow-lg max-h-64 overflow-auto">
                      <button
                        onClick={() => {
                          setSelectedIndex('');
                          setShowIndexDropdown(false);
                        }}
                        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 
                                 text-gray-900 dark:text-white text-left border-b border-gray-100 dark:border-gray-700"
                      >
                        <span>Tum Endeksler</span>
                        {!selectedIndex && <Check className="w-4 h-4 text-blue-600" />}
                      </button>
                      {indexes.map((index) => (
                        <button
                          key={index.id}
                          onClick={() => {
                            setSelectedIndex(index.id);
                            setShowIndexDropdown(false);
                          }}
                          className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 
                                   text-gray-900 dark:text-white text-left"
                        >
                          <div>
                            <div className="font-medium">{index.name}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">{index.description}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded">
                              {getIndexCount(index.id)} hisse
                            </span>
                            {selectedIndex === index.id && <Check className="w-4 h-4 text-blue-600" />}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="relative">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Sektor
                  </label>
                  <button
                    onClick={() => {
                      setShowSectorDropdown(!showSectorDropdown);
                      setShowIndexDropdown(false);
                    }}
                    className="w-full flex items-center justify-between px-4 py-2.5 border border-gray-200 dark:border-gray-600 
                             rounded-lg bg-white dark:bg-gray-700 text-left hover:bg-gray-50 dark:hover:bg-gray-600 transition"
                  >
                    <span className={selectedSector ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
                      {selectedSector || 'Tum Sektorler'}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showSectorDropdown ? 'rotate-180' : ''}`} />
                  </button>

                  {showSectorDropdown && (
                    <div className="absolute z-20 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 
                                  rounded-lg shadow-lg max-h-64 overflow-auto">
                      <button
                        onClick={() => {
                          setSelectedSector('');
                          setShowSectorDropdown(false);
                        }}
                        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 
                                 text-gray-900 dark:text-white text-left border-b border-gray-100 dark:border-gray-700"
                      >
                        <span>Tum Sektorler</span>
                        {!selectedSector && <Check className="w-4 h-4 text-blue-600" />}
                      </button>
                      {sectors.map((sector) => (
                        <button
                          key={sector}
                          onClick={() => {
                            setSelectedSector(sector);
                            setShowSectorDropdown(false);
                          }}
                          className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 
                                   text-gray-900 dark:text-white text-left"
                        >
                          <span>{sector}</span>
                          {selectedSector === sector && <Check className="w-4 h-4 text-blue-600" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {hasActiveFilters && (
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Aktif filtreler:</span>
                  
                  {selectedIndex && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900/50 
                                   text-blue-800 dark:text-blue-300 rounded-full text-sm">
                      {indexes.find(i => i.id === selectedIndex)?.name}
                      <button onClick={() => setSelectedIndex('')} className="hover:text-blue-600">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  )}
                  
                  {selectedSector && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 dark:bg-green-900/50 
                                   text-green-800 dark:text-green-300 rounded-full text-sm">
                      {selectedSector}
                      <button onClick={() => setSelectedSector('')} className="hover:text-green-600">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  )}
                  
                  {searchQuery && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 dark:bg-purple-900/50 
                                   text-purple-800 dark:text-purple-300 rounded-full text-sm">
                      &quot;{searchQuery}&quot;
                      <button onClick={() => setSearchQuery('')} className="hover:text-purple-600">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  )}

                  <button
                    onClick={clearFilters}
                    className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 underline"
                  >
                    Tumunu Temizle
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedIndex('')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                !selectedIndex
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Tumu ({stocks.length})
            </button>
            {indexes.map((index) => (
              <button
                key={index.id}
                onClick={() => setSelectedIndex(selectedIndex === index.id ? '' : index.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  selectedIndex === index.id
                    ? index.id === 'KATILIM' 
                      ? 'bg-emerald-600 text-white'
                      : 'bg-blue-600 text-white'
                    : index.id === 'KATILIM'
                      ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 border border-emerald-200 dark:border-emerald-800'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title={index.description}
              >
                {index.id === 'KATILIM' && ' '}{index.name} ({getIndexCount(index.id)})
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>
          {filteredStocks.length} hisse bulundu
          {limit && filteredStocks.length > limit && ` (${limit} tanesi gosteriliyor)`}
        </span>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Sembol
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Sirket
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider hidden md:table-cell">
                  Sektor
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Endeksler
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider hidden sm:table-cell">
                  Fiyat
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider hidden sm:table-cell">
                  Degisim
                </th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {displayedStocks.map((stock) => (
                <tr
                  key={stock.symbol}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/stock/${stock.symbol}`}
                >
                  <td className="px-4 py-3">
                    <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                      {stock.symbol}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-gray-900 dark:text-white text-sm truncate max-w-[200px] block">
                      {stock.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-200">
                      {stock.sector}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {stock.indexes?.map((idx) => (
                        <span
                          key={idx}
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            idx === 'KATILIM'
                              ? 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-300'
                              : idx === 'BIST30'
                                ? 'bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-300'
                                : 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300'
                          }`}
                        >
                          {idx === 'KATILIM' ? ' Katilim' : idx}
                        </span>
                      ))}
                      {(!stock.indexes || stock.indexes.length === 0) && (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right hidden sm:table-cell">
                    {stock.current_price ? (
                      <span className="font-mono text-gray-900 dark:text-white">
                        {stock.current_price.toFixed(2)} TL
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right hidden sm:table-cell">
                    {stock.change_percent !== undefined ? (
                      <span
                        className={`inline-flex items-center gap-1 font-mono ${
                          stock.change_percent >= 0
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {stock.change_percent >= 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        {stock.change_percent >= 0 ? '+' : ''}
                        {stock.change_percent.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ChevronRight className="w-5 h-5 text-gray-400 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {displayedStocks.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">
              Filtrelere uygun hisse bulunamadi.
            </p>
            <button
              onClick={clearFilters}
              className="mt-2 text-blue-600 hover:text-blue-700 dark:text-blue-400 underline"
            >
              Filtreleri temizle
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
