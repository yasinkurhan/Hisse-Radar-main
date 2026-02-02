'use client';

/**
 * HisseRadar Hisse Arama Bileşeni
 * ================================
 * Hisse sembolü veya şirket adına göre arama yapar
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { searchStocks } from '@/lib/api';
import { debounce } from '@/lib/utils';
import type { Stock } from '@/types';

interface StockSearchProps {
  onSelect?: (stock: Stock) => void;
  placeholder?: string;
}

export default function StockSearch({ 
  onSelect, 
  placeholder = "Hisse ara (örn: THYAO)" 
}: StockSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Stock[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Dışarı tıklamayı algıla
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Arama fonksiyonu (debounce ile)
  const performSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (searchQuery.length < 2) {
        setResults([]);
        setIsOpen(false);
        return;
      }

      setIsLoading(true);
      try {
        const response = await searchStocks(searchQuery);
        setResults(response.stocks.slice(0, 10));
        setIsOpen(true);
      } catch (error) {
        console.error('Arama hatası:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    []
  );

  // Input değişikliği
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    performSearch(value);
  };

  // Hisse seçimi
  const handleSelect = (stock: Stock) => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    if (onSelect) {
      onSelect(stock);
    } else {
      // Varsayılan davranış: hisse sayfasına git
      window.location.href = `/stocks/${stock.symbol}`;
    }
  };

  // Aramayı temizle
  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-lg">
      {/* Arama Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
        </div>
        
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          className="
            w-full pl-9 sm:pl-10 pr-9 sm:pr-10 py-2.5 sm:py-3
            bg-white border border-gray-300 rounded-lg
            text-gray-900 placeholder-gray-500
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            transition-all duration-200
            text-sm sm:text-base
          "
        />

        {/* Temizle butonu */}
        {query && (
          <button
            onClick={clearSearch}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400 hover:text-gray-600" />
          </button>
        )}

        {/* Yükleniyor göstergesi */}
        {isLoading && (
          <div className="absolute inset-y-0 right-8 flex items-center">
            <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Sonuç Dropdown */}
      {isOpen && results.length > 0 && (
        <div className="
          absolute z-50 w-full mt-2
          bg-white border border-gray-200 rounded-lg shadow-lg
          max-h-80 sm:max-h-96 overflow-y-auto
          animate-fade-in
        ">
          {results.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => handleSelect(stock)}
              className="
                w-full px-3 sm:px-4 py-2.5 sm:py-3 flex items-center justify-between
                hover:bg-gray-50 active:bg-gray-100 transition-colors
                border-b border-gray-100 last:border-b-0
              "
            >
              <div className="flex items-center space-x-2 sm:space-x-3 overflow-hidden">
                {/* Sembol badge */}
                <span className="
                  px-1.5 sm:px-2 py-0.5 sm:py-1 bg-primary-100 text-primary-700 
                  text-xs sm:text-sm font-bold rounded shrink-0
                ">
                  {stock.symbol}
                </span>
                
                {/* Şirket adı */}
                <span className="text-gray-900 text-xs sm:text-sm truncate">
                  {stock.name}
                </span>
              </div>

              {/* Sektör */}
              {stock.sector && (
                <span className="text-[10px] sm:text-xs text-gray-500 shrink-0 ml-2 hidden sm:block">
                  {stock.sector}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Sonuç yok */}
      {isOpen && query.length >= 2 && results.length === 0 && !isLoading && (
        <div className="
          absolute z-50 w-full mt-2
          bg-white border border-gray-200 rounded-lg shadow-lg
          px-3 sm:px-4 py-4 sm:py-6 text-center text-gray-500 text-sm
        ">
          "{query}" için sonuç bulunamadı
        </div>
      )}
    </div>
  );
}
