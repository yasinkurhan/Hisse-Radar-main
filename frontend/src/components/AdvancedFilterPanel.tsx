'use client';

import { useState, useEffect } from 'react';
import { X, Filter, ChevronDown, ChevronUp, Save, RotateCcw } from 'lucide-react';

interface FilterPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyFilters: (filters: FilterState) => void;
  currentFilters: FilterState;
}

export interface FilterState {
  // Endeks filtreleri
  indices: string[];
  // Sektör filtreleri
  sectors: string[];
  // Fiyat filtreleri
  minPrice: number | null;
  maxPrice: number | null;
  // Değişim filtreleri
  minChange: number | null;
  maxChange: number | null;
  // Hacim filtreleri
  volumeRatioMin: number | null;
  // RSI filtreleri
  rsiMin: number | null;
  rsiMax: number | null;
  // MACD sinyal
  macdSignal: string | null;
  // Bollinger pozisyonu
  bbPosition: string | null;
  // MA trend
  maTrend: string | null;
  // Sinyal filtreleri
  signals: string[];
  // Skor filtreleri
  minScore: number | null;
  maxScore: number | null;
  // Potansiyel filtreleri
  minTargetPercent: number | null;
  minRiskReward: number | null;
}

export const defaultFilters: FilterState = {
  indices: [],
  sectors: [],
  minPrice: null,
  maxPrice: null,
  minChange: null,
  maxChange: null,
  volumeRatioMin: null,
  rsiMin: null,
  rsiMax: null,
  macdSignal: null,
  bbPosition: null,
  maTrend: null,
  signals: [],
  minScore: null,
  maxScore: null,
  minTargetPercent: null,
  minRiskReward: null,
};

interface PresetFilter {
  id: string;
  name: string;
  description: string;
  icon: string;
  filters: Partial<FilterState>;
}

const PRESET_FILTERS: PresetFilter[] = [
  {
    id: 'strong_buy',
    name: 'Güçlü Al Sinyalleri',
    description: 'Güçlü al sinyali veren hisseler',
    icon: '🚀',
    filters: { signals: ['GUCLU_AL'], minScore: 70 }
  },
  {
    id: 'oversold_bounce',
    name: 'Aşırı Satım Toparlanma',
    description: 'RSI aşırı satımda, toparlanma potansiyeli',
    icon: '📈',
    filters: { rsiMax: 35, macdSignal: 'bullish', volumeRatioMin: 1.2 }
  },
  {
    id: 'high_momentum',
    name: 'Yüksek Momentum',
    description: 'Güçlü trend ve momentum',
    icon: '⚡',
    filters: { rsiMin: 50, rsiMax: 70, macdSignal: 'bullish', maTrend: 'bullish' }
  },
  {
    id: 'value_pick',
    name: 'Değer Fırsatları',
    description: 'Düşük fiyatlı, potansiyelli hisseler',
    icon: '💎',
    filters: { maxPrice: 50, minTargetPercent: 15, minRiskReward: 2 }
  },
  {
    id: 'blue_chip_buy',
    name: 'Blue Chip Al',
    description: 'BIST30 hisselerinde al sinyalleri',
    icon: '🏦',
    filters: { indices: ['BIST30'], signals: ['GUCLU_AL', 'AL'] }
  },
  {
    id: 'katilim_buy',
    name: 'Katılım Endeksi Al',
    description: 'Faizsiz yatırım uyumlu al sinyalleri',
    icon: '🌙',
    filters: { indices: ['KATILIM'], signals: ['GUCLU_AL', 'AL'] }
  },
  {
    id: 'high_volume',
    name: 'Yüksek Hacim',
    description: 'Ortalamanın 2x üstü hacim',
    icon: '📊',
    filters: { volumeRatioMin: 2.0 }
  },
  {
    id: 'low_risk',
    name: 'Düşük Risk',
    description: 'Yüksek R/R oranı, kontrollü risk',
    icon: '🛡️',
    filters: { minRiskReward: 2.5, signals: ['GUCLU_AL', 'AL'] }
  }
];

const INDICES = ['BIST30', 'BIST100', 'KATILIM'];
const SIGNALS = ['GUCLU_AL', 'AL', 'TUT', 'SAT', 'GUCLU_SAT'];

export default function AdvancedFilterPanel({
  isOpen,
  onClose,
  onApplyFilters,
  currentFilters
}: FilterPanelProps) {
  const [filters, setFilters] = useState<FilterState>(currentFilters);
  const [expandedSections, setExpandedSections] = useState<string[]>(['presets', 'indices', 'signals']);
  const [sectors, setSectors] = useState<string[]>([]);

  useEffect(() => {
    // Sektörleri yükle (retry ile)
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    let retryCount = 0;
    const maxRetries = 3;

    const loadSectors = () => {
      fetch(`${API_BASE}/api/filters/sectors`)
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            setSectors(data.sectors);
          }
        })
        .catch(() => {
          if (retryCount < maxRetries) {
            retryCount++;
            setTimeout(loadSectors, 2000);
          }
        });
    };
    loadSectors();
  }, []);

  useEffect(() => {
    setFilters(currentFilters);
  }, [currentFilters]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const applyPreset = (preset: PresetFilter) => {
    const newFilters = { ...defaultFilters, ...preset.filters };
    setFilters(newFilters);
  };

  const handleApply = () => {
    onApplyFilters(filters);
    onClose();
  };

  const handleReset = () => {
    setFilters(defaultFilters);
  };

  const toggleArrayFilter = (key: 'indices' | 'sectors' | 'signals', value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: prev[key].includes(value)
        ? prev[key].filter(v => v !== value)
        : [...prev[key], value]
    }));
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.indices.length > 0) count++;
    if (filters.sectors.length > 0) count++;
    if (filters.signals.length > 0) count++;
    if (filters.minPrice !== null || filters.maxPrice !== null) count++;
    if (filters.minChange !== null || filters.maxChange !== null) count++;
    if (filters.volumeRatioMin !== null) count++;
    if (filters.rsiMin !== null || filters.rsiMax !== null) count++;
    if (filters.macdSignal !== null) count++;
    if (filters.maTrend !== null) count++;
    if (filters.minScore !== null || filters.maxScore !== null) count++;
    if (filters.minTargetPercent !== null || filters.minRiskReward !== null) count++;
    return count;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative ml-auto w-full max-w-md bg-gray-900 h-full overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-4 z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-bold text-white">Gelişmiş Filtreler</h2>
              {getActiveFilterCount() > 0 && (
                <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                  {getActiveFilterCount()} aktif
                </span>
              )}
            </div>
            <button onClick={onClose} className="p-1 hover:bg-gray-700 rounded">
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* Hazır Filtreler */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('presets')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">🎯 Hazır Filtreler</span>
              {expandedSections.includes('presets') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('presets') && (
              <div className="px-4 pb-4 grid grid-cols-2 gap-2">
                {PRESET_FILTERS.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => applyPreset(preset)}
                    className="p-3 bg-gray-700/50 hover:bg-gray-700 rounded-lg text-left transition"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span>{preset.icon}</span>
                      <span className="text-white text-sm font-medium truncate">{preset.name}</span>
                    </div>
                    <p className="text-gray-400 text-xs line-clamp-2">{preset.description}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Endeks Filtreleri */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('indices')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">📊 Endeks</span>
              {expandedSections.includes('indices') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('indices') && (
              <div className="px-4 pb-4 flex flex-wrap gap-2">
                {INDICES.map(index => (
                  <button
                    key={index}
                    onClick={() => toggleArrayFilter('indices', index)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition ${filters.indices.includes(index)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                  >
                    {index}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Sinyal Filtreleri */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('signals')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">🎯 Sinyal</span>
              {expandedSections.includes('signals') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('signals') && (
              <div className="px-4 pb-4 flex flex-wrap gap-2">
                {SIGNALS.map(signal => {
                  const signalColors: Record<string, string> = {
                    'GUCLU_AL': 'bg-green-600',
                    'AL': 'bg-green-500',
                    'TUT': 'bg-yellow-500',
                    'SAT': 'bg-red-500',
                    'GUCLU_SAT': 'bg-red-700'
                  };
                  const signalNames: Record<string, string> = {
                    'GUCLU_AL': 'Güçlü Al',
                    'AL': 'Al',
                    'TUT': 'Tut',
                    'SAT': 'Sat',
                    'GUCLU_SAT': 'Güçlü Sat'
                  };
                  return (
                    <button
                      key={signal}
                      onClick={() => toggleArrayFilter('signals', signal)}
                      className={`px-3 py-1.5 rounded-lg text-sm transition ${filters.signals.includes(signal)
                          ? `${signalColors[signal]} text-white`
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                    >
                      {signalNames[signal]}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Fiyat Filtreleri */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('price')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">💰 Fiyat</span>
              {expandedSections.includes('price') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('price') && (
              <div className="px-4 pb-4 space-y-3">
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Min Fiyat (₺)</label>
                    <input
                      type="number"
                      value={filters.minPrice ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        minPrice: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Max Fiyat (₺)</label>
                    <input
                      type="number"
                      value={filters.maxPrice ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        maxPrice: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="∞"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RSI Filtreleri */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('rsi')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">📉 RSI</span>
              {expandedSections.includes('rsi') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('rsi') && (
              <div className="px-4 pb-4 space-y-3">
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Min RSI</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.rsiMin ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        rsiMin: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Max RSI</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.rsiMax ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        rsiMax: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="100"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, rsiMin: null, rsiMax: 30 }))}
                    className="flex-1 py-1.5 bg-green-600/30 text-green-400 rounded text-xs hover:bg-green-600/50"
                  >
                    Aşırı Satım (&lt;30)
                  </button>
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, rsiMin: 70, rsiMax: null }))}
                    className="flex-1 py-1.5 bg-red-600/30 text-red-400 rounded text-xs hover:bg-red-600/50"
                  >
                    Aşırı Alım (&gt;70)
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* MACD ve Trend */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('trend')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">📈 Trend & MACD</span>
              {expandedSections.includes('trend') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('trend') && (
              <div className="px-4 pb-4 space-y-3">
                <div>
                  <label className="text-gray-400 text-xs">MACD Sinyali</label>
                  <div className="flex gap-2 mt-1">
                    <button
                      onClick={() => setFilters(prev => ({
                        ...prev,
                        macdSignal: prev.macdSignal === 'bullish' ? null : 'bullish'
                      }))}
                      className={`flex-1 py-2 rounded-lg text-sm ${filters.macdSignal === 'bullish'
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300'
                        }`}
                    >
                      Yükseliş
                    </button>
                    <button
                      onClick={() => setFilters(prev => ({
                        ...prev,
                        macdSignal: prev.macdSignal === 'bearish' ? null : 'bearish'
                      }))}
                      className={`flex-1 py-2 rounded-lg text-sm ${filters.macdSignal === 'bearish'
                          ? 'bg-red-500 text-white'
                          : 'bg-gray-700 text-gray-300'
                        }`}
                    >
                      Düşüş
                    </button>
                  </div>
                </div>
                <div>
                  <label className="text-gray-400 text-xs">MA Trend</label>
                  <div className="flex gap-2 mt-1">
                    <button
                      onClick={() => setFilters(prev => ({
                        ...prev,
                        maTrend: prev.maTrend === 'bullish' ? null : 'bullish'
                      }))}
                      className={`flex-1 py-2 rounded-lg text-sm ${filters.maTrend === 'bullish'
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300'
                        }`}
                    >
                      Yukarı
                    </button>
                    <button
                      onClick={() => setFilters(prev => ({
                        ...prev,
                        maTrend: prev.maTrend === 'bearish' ? null : 'bearish'
                      }))}
                      className={`flex-1 py-2 rounded-lg text-sm ${filters.maTrend === 'bearish'
                          ? 'bg-red-500 text-white'
                          : 'bg-gray-700 text-gray-300'
                        }`}
                    >
                      Aşağı
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Skor ve Potansiyel */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('score')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">⭐ Skor & Potansiyel</span>
              {expandedSections.includes('score') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('score') && (
              <div className="px-4 pb-4 space-y-3">
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Min Skor</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.minScore ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        minScore: e.target.value ? parseInt(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Min Hedef %</label>
                    <input
                      type="number"
                      value={filters.minTargetPercent ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        minTargetPercent: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="0"
                    />
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Min Risk/Getiri Oranı</label>
                    <input
                      type="number"
                      step="0.1"
                      value={filters.minRiskReward ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        minRiskReward: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="1.5"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-gray-400 text-xs">Min Hacim Oranı</label>
                    <input
                      type="number"
                      step="0.1"
                      value={filters.volumeRatioMin ?? ''}
                      onChange={e => setFilters(prev => ({
                        ...prev,
                        volumeRatioMin: e.target.value ? parseFloat(e.target.value) : null
                      }))}
                      className="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
                      placeholder="1.0"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sektör Filtreleri */}
          <div className="bg-gray-800/50 rounded-xl overflow-hidden">
            <button
              onClick={() => toggleSection('sectors')}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-700/30"
            >
              <span className="font-medium text-white">🏭 Sektör</span>
              {expandedSections.includes('sectors') ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>
            {expandedSections.includes('sectors') && (
              <div className="px-4 pb-4 max-h-48 overflow-y-auto">
                <div className="flex flex-wrap gap-2">
                  {sectors.map(sector => (
                    <button
                      key={sector}
                      onClick={() => toggleArrayFilter('sectors', sector)}
                      className={`px-2 py-1 rounded text-xs transition ${filters.sectors.includes(sector)
                          ? 'bg-purple-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                    >
                      {sector}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-900 border-t border-gray-700 p-4">
          <div className="flex gap-3">
            <button
              onClick={handleReset}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition"
            >
              <RotateCcw className="w-4 h-4" />
              Sıfırla
            </button>
            <button
              onClick={handleApply}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-medium"
            >
              <Filter className="w-4 h-4" />
              Filtreleri Uygula
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
