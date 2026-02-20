'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function VIOPPage() {
    const [futures, setFutures] = useState<any>(null);
    const [options, setOptions] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'futures' | 'options'>('futures');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [futuresRes, optionsRes] = await Promise.all([
                fetch('http://localhost:8001/api/viop/futures').catch(() => null),
                fetch('http://localhost:8001/api/viop/options').catch(() => null),
            ]);

            if (futuresRes?.ok) setFutures(await futuresRes.json());
            if (optionsRes?.ok) setOptions(await optionsRes.json());
        } catch (err) {
            console.error('VIOP verileri yüklenemedi:', err);
        } finally {
            setLoading(false);
        }
    };

    const renderVal = (v: any) => {
        if (v == null) return '—';
        if (typeof v === 'number') return v.toLocaleString('tr-TR', { maximumFractionDigits: 4 });
        return String(v);
    };

    const renderTable = (data: any) => {
        if (!data) return <p className="text-gray-500">Veri bulunamadı</p>;

        let rows: any[] = [];
        if (Array.isArray(data)) rows = data;
        else if (data?.data && Array.isArray(data.data)) rows = data.data;
        else if (data?.results && Array.isArray(data.results)) rows = data.results;
        else if (typeof data === 'object' && !Array.isArray(data)) {
            return (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(data).map(([key, val]) => (
                        <div key={key} className="bg-gray-700/50 rounded-lg p-3">
                            <div className="text-xs text-gray-400 mb-1">{key}</div>
                            <div className="text-lg font-bold text-white">{renderVal(val)}</div>
                        </div>
                    ))}
                </div>
            );
        }

        if (rows.length === 0) return <p className="text-gray-500">Veri bulunamadı</p>;

        const cols = Object.keys(rows[0]);

        return (
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-gray-400 text-left border-b border-gray-700">
                            {cols.map(col => (
                                <th key={col} className="py-3 px-3 whitespace-nowrap">{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row: any, idx: number) => (
                            <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                                {cols.map(col => (
                                    <td key={col} className="py-3 px-3 whitespace-nowrap">
                                        {renderVal(row[col])}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">VIOP verileri yükleniyor...</p>
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
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                            📊 VIOP Dashboard
                        </h1>
                        <p className="text-gray-400 mt-1">Vadeli İşlem ve Opsiyon Piyasası kontratları</p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={fetchData} className="bg-cyan-600 hover:bg-cyan-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                            🔄 Yenile
                        </button>
                        <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm transition-colors">
                            Ana Sayfa
                        </Link>
                    </div>
                </div>

                {/* Info Banner */}
                <div className="bg-gradient-to-r from-cyan-900/30 to-blue-900/30 border border-cyan-700/30 rounded-xl p-4 mb-6">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">ℹ️</span>
                        <div className="text-sm">
                            <span className="font-semibold text-cyan-400">VIOP</span> — Borsa İstanbul Vadeli İşlem ve Opsiyon Piyasası.
                            Pay, endeks, döviz ve emtia üzerine vadeli işlem ve opsiyon kontratları işlem görür.
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => setActiveTab('futures')}
                        className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${activeTab === 'futures'
                                ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/20'
                                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                            }`}
                    >
                        📈 Vadeli İşlemler
                    </button>
                    <button
                        onClick={() => setActiveTab('options')}
                        className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${activeTab === 'options'
                                ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/20'
                                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                            }`}
                    >
                        📊 Opsiyonlar
                    </button>
                </div>

                {/* Content */}
                {activeTab === 'futures' && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>📈</span> Vadeli İşlem Kontratları
                        </h3>
                        {renderTable(futures)}
                    </div>
                )}

                {activeTab === 'options' && (
                    <div className="bg-gray-800/80 backdrop-blur rounded-xl p-6 border border-gray-700/50">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <span>📊</span> Opsiyon Kontratları
                        </h3>
                        {renderTable(options)}
                    </div>
                )}
            </div>
        </div>
    );
}
