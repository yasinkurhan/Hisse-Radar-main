'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface FXData {
    currency: string;
    buy?: number;
    sell?: number;
    price?: number;
    change?: number;
    change_percent?: number;
    [key: string]: any;
}

const CURRENCIES = [
    { code: 'USD', name: 'Amerikan Doları', flag: '🇺🇸' },
    { code: 'EUR', name: 'Euro', flag: '🇪🇺' },
    { code: 'GBP', name: 'İngiliz Sterlini', flag: '🇬🇧' },
    { code: 'CHF', name: 'İsviçre Frangı', flag: '🇨🇭' },
    { code: 'JPY', name: 'Japon Yeni', flag: '🇯🇵' },
];

const GOLD_TYPES = [
    { code: 'gram-altin', name: 'Gram Altın', icon: '🥇' },
    { code: 'ceyrek-altin', name: 'Çeyrek Altın', icon: '🪙' },
    { code: 'yarim-altin', name: 'Yarım Altın', icon: '🏅' },
    { code: 'tam-altin', name: 'Tam Altın', icon: '💰' },
];

export default function FXPage() {
    const [fxData, setFxData] = useState<Record<string, any>>({});
    const [goldData, setGoldData] = useState<Record<string, any>>({});
    const [bankRates, setBankRates] = useState<Record<string, any>>({});
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'currencies' | 'gold' | 'banks'>('currencies');
    const [selectedCurrency, setSelectedCurrency] = useState('USD');

    useEffect(() => {
        fetchAllData();
    }, []);

    const fetchAllData = async () => {
        setLoading(true);
        try {
            // Döviz kurları
            const fxPromises = CURRENCIES.map(c =>
                fetch(`http://localhost:8001/api/fx/current/${c.code}?t=${Date.now()}`, { cache: 'no-store' })
                    .then(r => r.ok ? r.json() : null)
                    .catch(() => null)
            );

            // Altın fiyatları
            const goldPromises = GOLD_TYPES.map(g =>
                fetch(`http://localhost:8001/api/fx/gold?gold_type=${g.code}&t=${Date.now()}`, { cache: 'no-store' })
                    .then(r => r.ok ? r.json() : null)
                    .catch(() => null)
            );

            // Banka kurları (USD ve EUR)
            const bankPromises = ['USD', 'EUR'].map(c =>
                fetch(`http://localhost:8001/api/fx/bank-rates/${c}?t=${Date.now()}`, { cache: 'no-store' })
                    .then(r => r.ok ? r.json() : null)
                    .catch(() => null)
            );

            const [fxResults, goldResults, bankResults] = await Promise.all([
                Promise.all(fxPromises),
                Promise.all(goldPromises),
                Promise.all(bankPromises),
            ]);

            // API format: {currency, data: {last, open, high, low, ...}, timestamp}
            // Extract the inner .data object for display
            const fxMap: Record<string, any> = {};
            CURRENCIES.forEach((c, i) => {
                const res = fxResults[i];
                if (res) {
                    const d = res.data || res;
                    // Calculate change percent from open/last if not provided
                    if (d && d.last && d.open && !d.change_percent) {
                        d.change_percent = ((d.last - d.open) / d.open) * 100;
                    }
                    fxMap[c.code] = d;
                }
            });
            setFxData(fxMap);

            const goldMap: Record<string, any> = {};
            GOLD_TYPES.forEach((g, i) => {
                const res = goldResults[i];
                if (res) {
                    const d = res.data || res;
                    if (d && d.last && d.open && !d.change_percent) {
                        d.change_percent = ((d.last - d.open) / d.open) * 100;
                    }
                    goldMap[g.code] = d;
                }
            });
            setGoldData(goldMap);

            const bankMap: Record<string, any> = {};
            ['USD', 'EUR'].forEach((c, i) => {
                const res = bankResults[i];
                if (res) bankMap[c] = res.bank_rates || res.data || res.rates || res;
            });
            setBankRates(bankMap);
        } catch (err) {
            console.error('FX verileri yüklenemedi:', err);
        } finally {
            setLoading(false);
        }
    };

    const renderVal = (v: any) => {
        if (v == null) return '—';
        if (typeof v === 'number') return v.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
        return String(v);
    };

    if (loading && Object.keys(fxData).length === 0) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">Döviz ve altın verileri yükleniyor...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white p-4 md:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
                            💱 Döviz & Altın Dashboard
                        </h1>
                        <p className="text-gray-400 mt-1">Canlı döviz kurları, altın fiyatları ve banka kurları</p>
                    </div>
                    <div className="flex gap-3">
                        <button 
                            onClick={fetchAllData} 
                            disabled={loading}
                            className={`bg-amber-600 hover:bg-amber-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${loading ? 'opacity-75 cursor-not-allowed' : ''}`}
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    Yenileniyor...
                                </>
                            ) : (
                                <>
                                    🔄 Yenile
                                </>
                            )}
                        </button>
                        <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm transition-colors">
                            Ana Sayfa
                        </Link>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6 flex-wrap">
                    {(['currencies', 'gold', 'banks'] as const).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${activeTab === tab
                                ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/20'
                                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                }`}
                        >
                            {tab === 'currencies' && '💵 Döviz Kurları'}
                            {tab === 'gold' && '🥇 Altın Fiyatları'}
                            {tab === 'banks' && '🏦 Banka Kurları'}
                        </button>
                    ))}
                </div>

                {/* Currencies Tab */}
                {activeTab === 'currencies' && (
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {CURRENCIES.map(curr => {
                                const data = fxData[curr.code];
                                const price = data?.last || data?.price || data?.buy || data?.selling;
                                const change = data?.change_percent || data?.change || 0;
                                return (
                                    <div
                                        key={curr.code}
                                        className="bg-gray-800/80 backdrop-blur border border-gray-700/50 rounded-xl p-6 hover:border-amber-500/30 transition-all cursor-pointer"
                                        onClick={() => setSelectedCurrency(curr.code)}
                                    >
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center gap-3">
                                                <span className="text-3xl">{curr.flag}</span>
                                                <div>
                                                    <div className="font-bold text-lg">{curr.code}/TRY</div>
                                                    <div className="text-xs text-gray-400">{curr.name}</div>
                                                </div>
                                            </div>
                                            {typeof change === 'number' && change !== 0 && (
                                                <span className={`text-sm font-medium px-2 py-1 rounded ${change > 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                                    {change > 0 ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-3xl font-bold text-amber-400">
                                            {price != null ? renderVal(price) : '—'}
                                        </div>
                                        {data && (
                                            <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
                                                {data.open != null && (
                                                    <div className="bg-gray-700/50 rounded px-3 py-1.5">
                                                        <span className="text-gray-400">Açılış:</span> <span className="text-white font-medium">{renderVal(data.open)}</span>
                                                    </div>
                                                )}
                                                {data.high != null && (
                                                    <div className="bg-gray-700/50 rounded px-3 py-1.5">
                                                        <span className="text-gray-400">Yüksek:</span> <span className="text-emerald-400 font-medium">{renderVal(data.high)}</span>
                                                    </div>
                                                )}
                                                {data.low != null && (
                                                    <div className="bg-gray-700/50 rounded px-3 py-1.5">
                                                        <span className="text-gray-400">Düşük:</span> <span className="text-red-400 font-medium">{renderVal(data.low)}</span>
                                                    </div>
                                                )}
                                                {data.update_time && (
                                                    <div className="bg-gray-700/50 rounded px-3 py-1.5">
                                                        <span className="text-gray-400">Güncelleme:</span> <span className="text-gray-300 font-medium text-xs">{new Date(data.update_time).toLocaleDateString('tr-TR')}</span>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        {!data && <p className="text-gray-500 text-sm mt-2">Veri bulunamadı</p>}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Gold Tab */}
                {activeTab === 'gold' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {GOLD_TYPES.map(gold => {
                            const data = goldData[gold.code];
                            const price = data?.last || data?.price || data?.buy || data?.selling;
                            const change = data?.change_percent || 0;
                            return (
                                <div key={gold.code} className="bg-gradient-to-br from-amber-900/40 to-yellow-900/20 border border-amber-700/30 rounded-xl p-6">
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-3">
                                            <span className="text-3xl">{gold.icon}</span>
                                            <div>
                                                <div className="font-bold text-lg">{gold.name}</div>
                                                <div className="text-xs text-gray-400">TL</div>
                                            </div>
                                        </div>
                                        {typeof change === 'number' && change !== 0 && (
                                            <span className={`text-sm font-medium px-2 py-1 rounded ${change > 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                                {change > 0 ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
                                            </span>
                                        )}
                                    </div>
                                    <div className="text-3xl font-bold text-amber-400 mb-3">
                                        {price != null ? renderVal(price) : '—'}
                                    </div>
                                    {data && typeof data === 'object' && (
                                        <div className="grid grid-cols-2 gap-2 text-sm">
                                            {data.open != null && (
                                                <div className="bg-gray-800/50 rounded px-3 py-1.5">
                                                    <span className="text-gray-400">Açılış:</span> <span className="text-white font-medium">{renderVal(data.open)}</span>
                                                </div>
                                            )}
                                            {data.high != null && (
                                                <div className="bg-gray-800/50 rounded px-3 py-1.5">
                                                    <span className="text-gray-400">Yüksek:</span> <span className="text-emerald-400 font-medium">{renderVal(data.high)}</span>
                                                </div>
                                            )}
                                            {data.low != null && (
                                                <div className="bg-gray-800/50 rounded px-3 py-1.5">
                                                    <span className="text-gray-400">Düşük:</span> <span className="text-red-400 font-medium">{renderVal(data.low)}</span>
                                                </div>
                                            )}
                                            {data.update_time && (
                                                <div className="bg-gray-800/50 rounded px-3 py-1.5">
                                                    <span className="text-gray-400">Güncelleme:</span> <span className="text-gray-300 font-medium text-xs">{new Date(data.update_time).toLocaleDateString('tr-TR')}</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {!data && <p className="text-gray-500 text-sm">Veri bulunamadı</p>}
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Bank Rates Tab */}
                {activeTab === 'banks' && (
                    <div className="space-y-6">
                        {['USD', 'EUR'].map(curr => {
                            const data = bankRates[curr];
                            return (
                                <div key={curr} className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                        <span>{curr === 'USD' ? '🇺🇸' : '🇪🇺'}</span> {curr}/TRY Banka Kurları
                                    </h3>
                                    {data ? (
                                        <div className="overflow-x-auto">
                                            {Array.isArray(data) ? (
                                                <table className="w-full text-sm">
                                                    <thead>
                                                        <tr className="text-gray-400 text-left border-b border-gray-700">
                                                            {data[0] && Object.keys(data[0]).map(key => (
                                                                <th key={key} className="py-3 px-4">{key}</th>
                                                            ))}
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {data.map((row: any, idx: number) => (
                                                            <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                                {Object.values(row).map((val: any, i: number) => (
                                                                    <td key={i} className="py-3 px-4">{renderVal(val)}</td>
                                                                ))}
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            ) : typeof data === 'object' ? (
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                    {Object.entries(data).map(([k, v]) => (
                                                        <div key={k} className="bg-gray-700/50 rounded-lg p-3">
                                                            <div className="text-xs text-gray-400 mb-1">{k}</div>
                                                            <div className="text-lg font-bold text-white">{renderVal(v)}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-gray-400">{renderVal(data)}</p>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-gray-500">Banka kuru verisi bulunamadı</p>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
