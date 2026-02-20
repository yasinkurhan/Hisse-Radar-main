'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface ScreenResult {
    [key: string]: any;
}

const TEMPLATES = [
    { id: 'high_dividend', name: 'Yüksek Temettü', icon: '💰', desc: 'Temettü verimi yüksek hisseler' },
    { id: 'low_pe', name: 'Düşük F/K', icon: '📉', desc: 'Fiyat/Kazanç oranı düşük hisseler' },
    { id: 'high_roe', name: 'Yüksek ROE', icon: '📈', desc: 'Özkaynak karlılığı yüksek hisseler' },
    { id: 'high_upside', name: 'Yüksek Potansiyel', icon: '🚀', desc: 'Hedef fiyata göre yükseliş potansiyeli' },
    { id: 'growth', name: 'Büyüme', icon: '🌱', desc: 'Gelir ve kar artışı yüksek hisseler' },
    { id: 'value', name: 'Değer', icon: '💎', desc: 'Ucuz kalmış değerli hisseler' },
    { id: 'momentum', name: 'Momentum', icon: '⚡', desc: 'Güçlü yükseliş trendinde hisseler' },
];

const SCAN_PRESETS = [
    { label: 'Aşırı Satım (RSI<30)', condition: 'rsi < 30', icon: '📉', color: 'text-red-400' },
    { label: 'Aşırı Alım (RSI>70)', condition: 'rsi > 70', icon: '📈', color: 'text-green-400' },
    { label: 'MACD Al Sinyali', condition: 'macd > signal', icon: '🟢', color: 'text-emerald-400' },
    { label: 'MACD Sat Sinyali', condition: 'macd < signal', icon: '🔴', color: 'text-red-400' },
    { label: 'SMA20 Üzerinde', condition: 'close > sma20', icon: '⬆️', color: 'text-blue-400' },
    { label: 'SMA200 Üzerinde', condition: 'close > sma200', icon: '🏔️', color: 'text-indigo-400' },
    { label: 'Yüksek Hacim', condition: 'volume > 5000000', icon: '🔊', color: 'text-amber-400' },
    { label: 'Düşük Volatilite', condition: 'atr < 1', icon: '🎯', color: 'text-cyan-400' },
    { label: 'Altın Çapraz', condition: 'sma50 > sma200', icon: '✨', color: 'text-yellow-400' },
    { label: 'Bollinger Alt Band', condition: 'close < bb_lower', icon: '📊', color: 'text-purple-400' },
];

export default function ScreenerPage() {
    const [results, setResults] = useState<ScreenResult[]>([]);
    const [columns, setColumns] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [activeTemplate, setActiveTemplate] = useState<string | null>(null);
    const [scanMode, setScanMode] = useState(false);

    // Custom filters
    const [peMax, setPeMax] = useState('');
    const [divMin, setDivMin] = useState('');
    const [roeMin, setRoeMin] = useState('');
    const [pbMax, setPbMax] = useState('');

    // Scan filters
    const [scanIndex, setScanIndex] = useState('XU030');
    const [scanCondition, setScanCondition] = useState('rsi < 30');
    const [scanInterval, setScanInterval] = useState('1d');

    const runTemplate = async (template: string) => {
        setLoading(true);
        setActiveTemplate(template);
        try {
            const res = await fetch(`http://localhost:8001/api/screener/stocks?template=${template}`);
            if (res.ok) {
                const data = await res.json();
                const rows = data?.results || data?.stocks || (Array.isArray(data) ? data : []);
                setResults(rows);
                if (rows.length > 0) setColumns(Object.keys(rows[0]));
            } else {
                setResults([]);
                setColumns([]);
            }
        } catch {
            setResults([]);
            setColumns([]);
        } finally {
            setLoading(false);
        }
    };

    const runCustomFilter = async () => {
        setLoading(true);
        setActiveTemplate('custom');
        try {
            const params = new URLSearchParams();
            if (peMax) params.append('pe_max', peMax);
            if (divMin) params.append('dividend_yield_min', divMin);
            if (roeMin) params.append('roe_min', roeMin);
            if (pbMax) params.append('pb_max', pbMax);

            const res = await fetch(`http://localhost:8001/api/screener/stocks?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                const rows = data?.results || data?.stocks || (Array.isArray(data) ? data : []);
                setResults(rows);
                if (rows.length > 0) setColumns(Object.keys(rows[0]));
            } else {
                setResults([]);
                setColumns([]);
            }
        } catch {
            setResults([]);
            setColumns([]);
        } finally {
            setLoading(false);
        }
    };

    const runTechnicalScan = async () => {
        setLoading(true);
        setActiveTemplate('scan');
        try {
            const res = await fetch(
                `http://localhost:8001/api/screener/scan?index=${scanIndex}&condition=${encodeURIComponent(scanCondition)}&interval=${scanInterval}`
            );
            if (res.ok) {
                const data = await res.json();
                const rows = data?.results || data?.stocks || (Array.isArray(data) ? data : []);
                setResults(rows);
                if (rows.length > 0) setColumns(Object.keys(rows[0]));
            } else {
                setResults([]);
                setColumns([]);
            }
        } catch {
            setResults([]);
            setColumns([]);
        } finally {
            setLoading(false);
        }
    };

    const renderVal = (v: any) => {
        if (v == null) return '—';
        if (typeof v === 'number') return v.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
        return String(v);
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-4 md:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
                            🔍 Gelişmiş Hisse Tarama
                        </h1>
                        <p className="text-gray-400 mt-1">Temel ve teknik kriterlere göre BIST hisse tarama</p>
                    </div>
                    <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm transition-colors">
                        Ana Sayfa
                    </Link>
                </div>

                {/* Mode Toggle */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => setScanMode(false)}
                        className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${!scanMode ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/20' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                            }`}
                    >
                        📊 Temel Analiz Tarama
                    </button>
                    <button
                        onClick={() => setScanMode(true)}
                        className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${scanMode ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/20' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                            }`}
                    >
                        📈 Teknik Tarama
                    </button>
                </div>

                {/* Fundamental Screening */}
                {!scanMode && (
                    <div className="space-y-6">
                        {/* Template Buttons */}
                        <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                            <h3 className="text-lg font-semibold mb-4">⚡ Hazır Şablonlar</h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                                {TEMPLATES.map(t => (
                                    <button
                                        key={t.id}
                                        onClick={() => runTemplate(t.id)}
                                        className={`p-4 rounded-xl border text-left transition-all hover:scale-[1.02] ${activeTemplate === t.id
                                                ? 'bg-violet-600/20 border-violet-500/50'
                                                : 'bg-gray-700/50 border-gray-600/50 hover:border-violet-500/30'
                                            }`}
                                    >
                                        <div className="text-2xl mb-2">{t.icon}</div>
                                        <div className="font-semibold">{t.name}</div>
                                        <div className="text-xs text-gray-400 mt-1">{t.desc}</div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Custom Filters */}
                        <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                            <h3 className="text-lg font-semibold mb-4">🎛️ Özel Filtreler</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">F/K Maks</label>
                                    <input
                                        type="number"
                                        value={peMax}
                                        onChange={e => setPeMax(e.target.value)}
                                        placeholder="ör: 15"
                                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Temettü Verimi Min (%)</label>
                                    <input
                                        type="number"
                                        value={divMin}
                                        onChange={e => setDivMin(e.target.value)}
                                        placeholder="ör: 5"
                                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">ROE Min (%)</label>
                                    <input
                                        type="number"
                                        value={roeMin}
                                        onChange={e => setRoeMin(e.target.value)}
                                        placeholder="ör: 20"
                                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">PD/DD Maks</label>
                                    <input
                                        type="number"
                                        value={pbMax}
                                        onChange={e => setPbMax(e.target.value)}
                                        placeholder="ör: 3"
                                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={runCustomFilter}
                                disabled={loading}
                                className="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 px-6 py-2.5 rounded-lg font-medium text-sm transition-colors"
                            >
                                {loading ? '⏳ Taranıyor...' : '🔎 Tara'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Technical Scan */}
                {scanMode && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold mb-4">📈 Teknik Koşul Tarama</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Endeks</label>
                                <select
                                    value={scanIndex}
                                    onChange={e => setScanIndex(e.target.value)}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                >
                                    <option value="XU030">BIST 30</option>
                                    <option value="XU050">BIST 50</option>
                                    <option value="XU100">BIST 100</option>
                                    <option value="XUTUM">BIST Tüm</option>
                                    <option value="XBANK">Banka</option>
                                    <option value="XHOLD">Holding</option>
                                    <option value="XUSIN">Sanayi</option>
                                    <option value="XKTUM">Katılım</option>
                                    <option value="XUTEK">Teknoloji</option>
                                    <option value="XGIDA">Gıda</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Koşul</label>
                                <input
                                    type="text"
                                    value={scanCondition}
                                    onChange={e => setScanCondition(e.target.value)}
                                    placeholder="ör: rsi < 30 and volume > 1000000"
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Periyot</label>
                                <select
                                    value={scanInterval}
                                    onChange={e => setScanInterval(e.target.value)}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-violet-500 focus:outline-none"
                                >
                                    <option value="1d">Günlük</option>
                                    <option value="1h">Saatlik</option>
                                    <option value="15m">15 Dakika</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-4">
                            <span className="text-xs text-gray-500">Hazır koşullar:</span>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 mb-4">
                            {SCAN_PRESETS.map(preset => (
                                <button
                                    key={preset.condition}
                                    onClick={() => setScanCondition(preset.condition)}
                                    className={`text-xs p-2 rounded-lg border transition-all hover:scale-[1.02] ${
                                        scanCondition === preset.condition
                                            ? 'bg-violet-600/20 border-violet-500/50'
                                            : 'bg-gray-700/50 border-gray-600/50 hover:border-violet-500/30'
                                    }`}
                                >
                                    <span className="mr-1">{preset.icon}</span>
                                    <span className={preset.color}>{preset.label}</span>
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={runTechnicalScan}
                            disabled={loading}
                            className="bg-violet-600 hover:bg-violet-700 disabled:opacity-50 px-6 py-2.5 rounded-lg font-medium text-sm transition-colors"
                        >
                            {loading ? '⏳ Taranıyor...' : '🔎 Teknik Tara'}
                        </button>
                    </div>
                )}

                {/* Results */}
                {loading && (
                    <div className="flex items-center justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500 mr-3"></div>
                        <span className="text-gray-400">Hisseler taranıyor...</span>
                    </div>
                )}

                {!loading && results.length > 0 && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50 mt-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">📋 Sonuçlar ({results.length} hisse)</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="text-gray-400 text-left border-b border-gray-700">
                                        {columns.map(col => (
                                            <th key={col} className="py-3 px-3 whitespace-nowrap">{col}</th>
                                        ))}
                                        <th className="py-3 px-3">Detay</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {results.map((row, idx) => {
                                        const symbol = row.symbol || row.Symbol || row.ticker || '';
                                        return (
                                            <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                                                {columns.map(col => (
                                                    <td key={col} className={`py-3 px-3 ${col.toLowerCase().includes('symbol') ? 'font-bold text-violet-400' : ''}`}>
                                                        {renderVal(row[col])}
                                                    </td>
                                                ))}
                                                <td className="py-3 px-3">
                                                    {symbol && (
                                                        <Link
                                                            href={`/stock/${symbol}`}
                                                            className="text-violet-400 hover:text-violet-300 text-xs font-medium"
                                                        >
                                                            Detay →
                                                        </Link>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {!loading && results.length === 0 && activeTemplate && (
                    <div className="bg-gray-800/80 rounded-xl p-12 text-center mt-6 border border-gray-700/50">
                        <div className="text-4xl mb-4">🔍</div>
                        <p className="text-gray-400">Kriterlere uygun hisse bulunamadı veya veriler yüklenemedi.</p>
                        <p className="text-gray-500 text-sm mt-2">Filtreleri değiştirip tekrar deneyin.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
