'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface BondData {
    [key: string]: any;
}

interface TCMBRate {
    borrowing: number;
    lending: number;
}

interface TCMBData {
    policy_rate: number | null;
    overnight: number | TCMBRate | null;
    late_liquidity: number | TCMBRate | null;
}

interface CalendarEvent {
    date?: string;
    time?: string;
    event?: string;
    actual?: string;
    forecast?: string;
    previous?: string;
    impact?: string;
    country?: string;
    [key: string]: any;
}

export default function EconomyPage() {
    const [bonds, setBonds] = useState<any>(null);
    const [tcmb, setTcmb] = useState<TCMBData | null>(null);
    const [inflation, setInflation] = useState<any>(null);
    const [calendar, setCalendar] = useState<CalendarEvent[]>([]);
    const [eurobonds, setEurobonds] = useState<any>(null);
    const [riskFreeRate, setRiskFreeRate] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'bonds' | 'calendar' | 'eurobonds'>('overview');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [bondsRes, tcmbRes, inflationRes, calendarRes, eurobondsRes, riskRes] = await Promise.all([
                fetch('http://localhost:8001/api/economy/bonds').catch(() => null),
                fetch('http://localhost:8001/api/economy/tcmb').catch(() => null),
                fetch('http://localhost:8001/api/economy/inflation').catch(() => null),
                fetch('http://localhost:8001/api/economy/calendar').catch(() => null),
                fetch('http://localhost:8001/api/economy/eurobonds').catch(() => null),
                fetch('http://localhost:8001/api/economy/risk-free-rate').catch(() => null),
            ]);

            if (bondsRes?.ok) {
                const data = await bondsRes.json();
                setBonds(data.bonds || data);
            }
            if (tcmbRes?.ok) {
                const data = await tcmbRes.json();
                setTcmb(data.tcmb_rates || data);
            }
            if (inflationRes?.ok) {
                const data = await inflationRes.json();
                setInflation(data.inflation || data);
            }
            if (calendarRes?.ok) {
                const calData = await calendarRes.json();
                setCalendar(Array.isArray(calData) ? calData : calData?.events || calData?.data || []);
            }
            if (eurobondsRes?.ok) {
                const data = await eurobondsRes.json();
                setEurobonds(data.eurobonds || data);
            }
            if (riskRes?.ok) {
                const riskData = await riskRes.json();
                setRiskFreeRate(typeof riskData === 'number' ? riskData : riskData?.risk_free_rate ?? riskData?.rate ?? null);
            }
        } catch (err) {
            console.error('Ekonomi verileri yüklenemedi:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">Ekonomi verileri yükleniyor...</p>
                </div>
            </div>
        );
    }

    const renderValue = (val: any) => {
        if (val === null || val === undefined) return <span className="text-gray-500">—</span>;
        if (typeof val === 'number') return val.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
        if (typeof val === 'object') return JSON.stringify(val);
        return String(val);
    };

    const renderTcmbRate = (rate: number | TCMBRate | null | undefined, type: 'lending' | 'borrowing' = 'lending') => {
        if (rate === null || rate === undefined) return '—';
        if (typeof rate === 'number') return `%${rate}`;
        if (typeof rate === 'object' && rate !== null) return `%${rate[type]}`;
        return '—';
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white p-4 md:p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                            🏦 Ekonomi & Makro Dashboard
                        </h1>
                        <p className="text-gray-400 mt-1">Türkiye makro ekonomik göstergeleri — TCMB, tahvil, enflasyon</p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={fetchData} className="bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded-lg transition-colors text-sm font-medium">
                            🔄 Yenile
                        </button>
                        <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors text-sm">
                            Ana Sayfa
                        </Link>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {/* TCMB Politika Faizi */}
                    <div className="bg-gradient-to-br from-emerald-900/50 to-emerald-800/30 border border-emerald-700/30 rounded-xl p-5">
                        <div className="text-sm text-emerald-300 mb-1">TCMB Politika Faizi</div>
                        <div className="text-3xl font-bold text-emerald-400">
                            {tcmb?.policy_rate != null ? `%${tcmb.policy_rate}` : '—'}
                        </div>
                        <div className="text-xs text-gray-400 mt-2">Haftalık repo faiz oranı</div>
                    </div>
                    {/* Gecelik */}
                    <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700/30 rounded-xl p-5">
                        <div className="text-sm text-blue-300 mb-1">Gecelik Faiz</div>
                        <div className="text-3xl font-bold text-blue-400">
                            {renderTcmbRate(tcmb?.overnight, 'lending')}
                        </div>
                        <div className="text-xs text-gray-400 mt-2">Gecelik borç verme</div>
                    </div>
                    {/* Risk-Free Rate */}
                    <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700/30 rounded-xl p-5">
                        <div className="text-sm text-purple-300 mb-1">Risksiz Faiz (10Y)</div>
                        <div className="text-3xl font-bold text-purple-400">
                            {riskFreeRate != null ? `%${riskFreeRate.toFixed(2)}` : '—'}
                        </div>
                        <div className="text-xs text-gray-400 mt-2">10 yıllık devlet tahvili</div>
                    </div>
                    {/* Late Liquidity */}
                    <div className="bg-gradient-to-br from-amber-900/50 to-amber-800/30 border border-amber-700/30 rounded-xl p-5">
                        <div className="text-sm text-amber-300 mb-1">Geç Likidite Penceresi</div>
                        <div className="text-3xl font-bold text-amber-400">
                            {renderTcmbRate(tcmb?.late_liquidity, 'lending')}
                        </div>
                        <div className="text-xs text-gray-400 mt-2">GLP faiz oranı</div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6 flex-wrap">
                    {(['overview', 'bonds', 'calendar', 'eurobonds'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${activeTab === tab
                                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/20'
                                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                                }`}
                        >
                            {tab === 'overview' && '📊 Genel Bakış'}
                            {tab === 'bonds' && '📈 Tahvil & Faiz'}
                            {tab === 'calendar' && '📅 Ekonomik Takvim'}
                            {tab === 'eurobonds' && '🌐 Eurobondlar'}
                        </button>
                    ))}
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Enflasyon */}
                        <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <span>📊</span> Enflasyon Verileri
                            </h3>
                            {inflation ? (
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {typeof inflation === 'object' && Object.entries(inflation).slice(0, 8).map(([key, val]) => (
                                        <div key={key} className="bg-gray-700/50 rounded-lg p-4">
                                            <div className="text-xs text-gray-400 mb-1">{key}</div>
                                            <div className="text-xl font-bold text-white">{renderValue(val)}</div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-500">Enflasyon verisi bulunamadı</p>
                            )}
                        </div>

                        {/* TCMB Detay */}
                        <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <span>🏦</span> TCMB Faiz Oranları
                            </h3>
                            {tcmb ? (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="text-gray-400 text-left border-b border-gray-700">
                                                <th className="py-3 px-4">Faiz Türü</th>
                                                <th className="py-3 px-4 text-right">Oran (%)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                <td className="py-3 px-4 font-medium">Politika Faizi (1 Haftalık Repo)</td>
                                                <td className="py-3 px-4 text-right text-emerald-400 font-bold text-lg">{tcmb.policy_rate ?? '—'}</td>
                                            </tr>
                                            <tr className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                <td className="py-3 px-4 font-medium">Gecelik Borç Verme</td>
                                                <td className="py-3 px-4 text-right text-blue-400 font-bold text-lg">{renderTcmbRate(tcmb.overnight, 'lending')}</td>
                                            </tr>
                                            <tr className="hover:bg-gray-700/30">
                                                <td className="py-3 px-4 font-medium">Geç Likidite Penceresi</td>
                                                <td className="py-3 px-4 text-right text-amber-400 font-bold text-lg">{renderTcmbRate(tcmb.late_liquidity, 'lending')}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p className="text-gray-500">TCMB verisi bulunamadı</p>
                            )}
                        </div>
                    </div>
                )}

                {/* Bonds Tab */}
                {activeTab === 'bonds' && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>📈</span> Devlet Tahvili Faiz Oranları
                        </h3>
                        {bonds ? (
                            <div className="overflow-x-auto">
                                {Array.isArray(bonds) ? (
                                    <table className="w-full">
                                        <thead>
                                            <tr className="text-gray-400 text-left border-b border-gray-700">
                                                {bonds[0] && Object.keys(bonds[0]).map((key) => (
                                                    <th key={key} className="py-3 px-4">{key}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {bonds.map((row: any, idx: number) => (
                                                <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                    {Object.values(row).map((val: any, i: number) => (
                                                        <td key={i} className="py-3 px-4">{renderValue(val)}</td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : typeof bonds === 'object' ? (
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                        {Object.entries(bonds).map(([key, val]) => (
                                            <div key={key} className="bg-gray-700/50 rounded-lg p-4">
                                                <div className="text-xs text-gray-400 mb-1">{key}</div>
                                                <div className="text-xl font-bold text-emerald-400">{renderValue(val)}</div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-400">{renderValue(bonds)}</p>
                                )}
                            </div>
                        ) : (
                            <p className="text-gray-500">Tahvil verisi bulunamadı</p>
                        )}
                    </div>
                )}

                {/* Calendar Tab */}
                {activeTab === 'calendar' && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>📅</span> Ekonomik Takvim
                        </h3>
                        {calendar.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="text-gray-400 text-left border-b border-gray-700">
                                            <th className="py-3 px-4">Tarih</th>
                                            <th className="py-3 px-4">Etkinlik</th>
                                            <th className="py-3 px-4 text-center">Önem</th>
                                            <th className="py-3 px-4 text-right">Gerçekleşen</th>
                                            <th className="py-3 px-4 text-right">Beklenti</th>
                                            <th className="py-3 px-4 text-right">Önceki</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {calendar.slice(0, 30).map((event, idx) => (
                                            <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                <td className="py-3 px-4 text-sm whitespace-nowrap">
                                                    {event.date || '—'} {event.time || ''}
                                                </td>
                                                <td className="py-3 px-4 font-medium">{event.event || '—'}</td>
                                                <td className="py-3 px-4 text-center">
                                                    {event.impact === 'high' || event.impact === '3' ? (
                                                        <span className="text-red-400 font-bold">🔴</span>
                                                    ) : event.impact === 'medium' || event.impact === '2' ? (
                                                        <span className="text-amber-400">🟡</span>
                                                    ) : (
                                                        <span className="text-gray-400">⚪</span>
                                                    )}
                                                </td>
                                                <td className="py-3 px-4 text-right font-medium">{renderValue(event.actual)}</td>
                                                <td className="py-3 px-4 text-right text-gray-400">{renderValue(event.forecast)}</td>
                                                <td className="py-3 px-4 text-right text-gray-400">{renderValue(event.previous)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="text-gray-500">Ekonomik takvim verisi bulunamadı</p>
                        )}
                    </div>
                )}

                {/* Eurobonds Tab */}
                {activeTab === 'eurobonds' && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>🌐</span> Türk Devlet Eurobondları
                        </h3>
                        {eurobonds ? (
                            <div className="overflow-x-auto">
                                {Array.isArray(eurobonds) ? (
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-gray-400 text-left border-b border-gray-700">
                                                {eurobonds[0] && Object.keys(eurobonds[0]).map((key) => (
                                                    <th key={key} className="py-3 px-3">{key}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {eurobonds.map((row: any, idx: number) => (
                                                <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                                                    {Object.values(row).map((val: any, i: number) => (
                                                        <td key={i} className="py-3 px-3">{renderValue(val)}</td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : typeof eurobonds === 'object' ? (
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                        {Object.entries(eurobonds).map(([key, val]) => (
                                            <div key={key} className="bg-gray-700/50 rounded-lg p-4">
                                                <div className="text-xs text-gray-400 mb-1">{key}</div>
                                                <div className="text-lg font-bold text-cyan-400">{renderValue(val)}</div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-400">{renderValue(eurobonds)}</p>
                                )}
                            </div>
                        ) : (
                            <p className="text-gray-500">Eurobond verisi bulunamadı</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
