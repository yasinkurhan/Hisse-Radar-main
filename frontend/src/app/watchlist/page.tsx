'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface WatchlistStock {
  symbol: string;
  added_date: string;
  note: string;
}

interface WatchlistData {
  name: string;
  stocks: WatchlistStock[];
  created: string;
}

interface StockPrice {
  symbol: string;
  price: number;
  change_percent: number;
}

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<WatchlistData | null>(null);
  const [prices, setPrices] = useState<Record<string, StockPrice>>({});
  const [newSymbol, setNewSymbol] = useState('');
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  const fetchWatchlist = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/user/watchlist');
      const data = await res.json();
      setWatchlist(data);
    } catch (error) {
      console.error('Watchlist yuklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchWatchlist(); }, []);

  const addToWatchlist = async () => {
    if (!newSymbol.trim()) return;
    setAdding(true);
    try {
      const res = await fetch('http://localhost:8000/api/user/watchlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: newSymbol.toUpperCase(), list_id: 'default', note: '' })
      });
      const data = await res.json();
      if (data.success) { setNewSymbol(''); fetchWatchlist(); }
      else { alert(data.message); }
    } catch (error) { alert('Hata olustu'); }
    finally { setAdding(false); }
  };

  const removeFromWatchlist = async (symbol: string) => {
    try {
      await fetch('http://localhost:8000/api/user/watchlist/remove?symbol=' + symbol, { method: 'POST' });
      fetchWatchlist();
    } catch (error) { alert('Hata olustu'); }
  };

  if (loading) return <div className="min-h-screen bg-gray-900 text-white p-8 text-center">Yukleniyor...</div>;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Takip Listem</h1>
          <Link href="/" className="text-blue-400 hover:underline">Ana Sayfa</Link>
        </div>
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Hisse Ekle</h2>
          <div className="flex gap-4">
            <input type="text" value={newSymbol} onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              placeholder="Hisse sembolu (or: THYAO)" className="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2"
              onKeyPress={(e) => e.key === 'Enter' && addToWatchlist()} />
            <button onClick={addToWatchlist} disabled={adding}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-semibold disabled:opacity-50">
              {adding ? 'Ekleniyor...' : 'Ekle'}
            </button>
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">{watchlist?.name} ({watchlist?.stocks.length || 0} hisse)</h2>
          {watchlist?.stocks.length === 0 ? (
            <p className="text-gray-400 text-center py-8">Takip listesi bos. Yukardaki alandan hisse ekleyin.</p>
          ) : (
            <div className="space-y-2">
              {watchlist?.stocks.map((stock) => (
                <div key={stock.symbol} className="flex items-center justify-between bg-gray-700 rounded p-4">
                  <Link href={'/stocks/' + stock.symbol} className="text-blue-400 hover:underline font-semibold text-lg">
                    {stock.symbol}
                  </Link>
                  <div className="flex items-center gap-4">
                    <span className="text-gray-400 text-sm">{new Date(stock.added_date).toLocaleDateString('tr-TR')}</span>
                    <button onClick={() => removeFromWatchlist(stock.symbol)} className="text-red-400 hover:text-red-300">Sil</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
