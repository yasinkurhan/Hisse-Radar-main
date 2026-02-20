'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface PortfolioStock {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price?: number;
  total_value?: number;
  profit_loss?: number;
  profit_loss_pct?: number;
}

interface PortfolioData {
  name: string;
  initial_capital: number;
  current_capital: number;
  total_value: number;
  total_profit_loss: number;
  total_profit_loss_pct: number;
  stocks: PortfolioStock[];
  created: string;
}

interface Transaction {
  id: string;
  type: 'buy' | 'sell';
  symbol: string;
  quantity: number;
  price: number;
  total: number;
  date: string;
}

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'portfolio' | 'trade' | 'history'>('portfolio');
  
  // Trade form
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');
  const [trading, setTrading] = useState(false);

  useEffect(() => {
    fetchPortfolio();
    fetchTransactions();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/user/portfolio');
      const data = await res.json();
      setPortfolio(data);
    } catch (error) {
      console.error('Portföy yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/user/portfolio/transactions?limit=50');
      const data = await res.json();
      setTransactions(data);
    } catch (error) {
      console.error('İşlemler yüklenemedi:', error);
    }
  };

  const executeTrade = async () => {
    if (!symbol || !quantity || !price) {
      alert('Tüm alanları doldurun');
      return;
    }

    setTrading(true);
    try {
      const endpoint = tradeType === 'buy' 
        ? 'http://localhost:8001/api/user/portfolio/buy'
        : 'http://localhost:8001/api/user/portfolio/sell';
      
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: symbol.toUpperCase(),
          quantity: parseInt(quantity),
          price: parseFloat(price)
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert(data.message);
        setSymbol('');
        setQuantity('');
        setPrice('');
        fetchPortfolio();
        fetchTransactions();
      } else {
        alert(data.message || 'İşlem başarısız');
      }
    } catch (error) {
      alert('Hata oluştu');
    } finally {
      setTrading(false);
    }
  };

  const resetPortfolio = async () => {
    if (!confirm('Portföyü sıfırlamak istediğinize emin misiniz? Tüm veriler silinecek.')) return;
    
    try {
      await fetch('http://localhost:8001/api/user/portfolio/reset?initial_capital=100000', { method: 'POST' });
      fetchPortfolio();
      fetchTransactions();
    } catch (error) {
      alert('Hata oluştu');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Portföy yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">💼 Sanal Portföy</h1>
            <p className="text-gray-400 mt-1">Sanal para ile hisse alım-satım simülasyonu</p>
          </div>
          <div className="flex gap-4">
            <button onClick={resetPortfolio} className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">
              🔄 Sıfırla
            </button>
            <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded">
              Ana Sayfa
            </Link>
          </div>
        </div>

        {/* Portfolio Summary */}
        {portfolio && (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">📊 Portföy Özeti</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-gray-700 rounded p-4 text-center">
                <p className="text-gray-400 text-sm">Başlangıç Sermayesi</p>
                <p className="text-2xl font-bold">₺{portfolio.initial_capital?.toLocaleString()}</p>
              </div>
              <div className="bg-gray-700 rounded p-4 text-center">
                <p className="text-gray-400 text-sm">Nakit</p>
                <p className="text-2xl font-bold text-blue-400">₺{portfolio.current_capital?.toLocaleString()}</p>
              </div>
              <div className="bg-gray-700 rounded p-4 text-center">
                <p className="text-gray-400 text-sm">Portföy Değeri</p>
                <p className="text-2xl font-bold">₺{portfolio.total_value?.toLocaleString()}</p>
              </div>
              <div className="bg-gray-700 rounded p-4 text-center">
                <p className="text-gray-400 text-sm">Kar/Zarar</p>
                <p className={`text-2xl font-bold ${(portfolio.total_profit_loss || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(portfolio.total_profit_loss || 0) >= 0 ? '+' : ''}₺{portfolio.total_profit_loss?.toLocaleString()}
                </p>
              </div>
              <div className="bg-gray-700 rounded p-4 text-center">
                <p className="text-gray-400 text-sm">Getiri</p>
                <p className={`text-2xl font-bold ${(portfolio.total_profit_loss_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(portfolio.total_profit_loss_pct || 0) >= 0 ? '+' : ''}%{portfolio.total_profit_loss_pct?.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button 
            onClick={() => setActiveTab('portfolio')}
            className={`px-6 py-2 rounded ${activeTab === 'portfolio' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            Pozisyonlar ({portfolio?.stocks?.length || 0})
          </button>
          <button 
            onClick={() => setActiveTab('trade')}
            className={`px-6 py-2 rounded ${activeTab === 'trade' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            İşlem Yap
          </button>
          <button 
            onClick={() => setActiveTab('history')}
            className={`px-6 py-2 rounded ${activeTab === 'history' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            İşlem Geçmişi ({transactions.length})
          </button>
        </div>

        {/* Portfolio Positions */}
        {activeTab === 'portfolio' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">📈 Açık Pozisyonlar</h2>
            {!portfolio?.stocks || portfolio.stocks.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz pozisyon yok. "İşlem Yap" sekmesinden hisse alabilirsiniz.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-gray-400 text-left border-b border-gray-700">
                      <th className="py-3 px-4">Hisse</th>
                      <th className="py-3 px-4">Adet</th>
                      <th className="py-3 px-4">Ort. Maliyet</th>
                      <th className="py-3 px-4">Güncel Fiyat</th>
                      <th className="py-3 px-4">Toplam Değer</th>
                      <th className="py-3 px-4">Kar/Zarar</th>
                      <th className="py-3 px-4">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolio.stocks.map((stock, idx) => (
                      <tr key={idx} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="py-3 px-4">
                          <Link href={`/stock/${stock.symbol}`} className="text-blue-400 hover:underline font-semibold">
                            {stock.symbol}
                          </Link>
                        </td>
                        <td className="py-3 px-4">{stock.quantity}</td>
                        <td className="py-3 px-4">₺{stock.avg_price?.toFixed(2)}</td>
                        <td className="py-3 px-4">₺{stock.current_price?.toFixed(2) || '-'}</td>
                        <td className="py-3 px-4">₺{stock.total_value?.toLocaleString() || '-'}</td>
                        <td className={`py-3 px-4 font-semibold ${(stock.profit_loss || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(stock.profit_loss || 0) >= 0 ? '+' : ''}₺{stock.profit_loss?.toFixed(2) || '0'}
                        </td>
                        <td className={`py-3 px-4 font-semibold ${(stock.profit_loss_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(stock.profit_loss_pct || 0) >= 0 ? '+' : ''}%{stock.profit_loss_pct?.toFixed(2) || '0'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Trade Form */}
        {activeTab === 'trade' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">💰 İşlem Yap</h2>
            <div className="max-w-md mx-auto">
              {/* Trade Type */}
              <div className="flex gap-2 mb-6">
                <button
                  onClick={() => setTradeType('buy')}
                  className={`flex-1 py-3 rounded font-semibold ${tradeType === 'buy' ? 'bg-green-600' : 'bg-gray-700'}`}
                >
                  📈 AL
                </button>
                <button
                  onClick={() => setTradeType('sell')}
                  className={`flex-1 py-3 rounded font-semibold ${tradeType === 'sell' ? 'bg-red-600' : 'bg-gray-700'}`}
                >
                  📉 SAT
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-gray-400 mb-2">Hisse Sembolü</label>
                  <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    placeholder="Örn: THYAO"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-3"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 mb-2">Adet</label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="Örn: 100"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-3"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 mb-2">Fiyat (₺)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="Örn: 250.50"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-3"
                  />
                </div>

                {/* Summary */}
                {quantity && price && (
                  <div className="bg-gray-700 rounded p-4">
                    <p className="text-gray-400">Toplam Tutar:</p>
                    <p className="text-2xl font-bold">₺{(parseFloat(quantity) * parseFloat(price)).toLocaleString()}</p>
                  </div>
                )}

                <button
                  onClick={executeTrade}
                  disabled={trading}
                  className={`w-full py-4 rounded font-semibold text-lg ${
                    tradeType === 'buy' 
                      ? 'bg-green-600 hover:bg-green-700' 
                      : 'bg-red-600 hover:bg-red-700'
                  } disabled:opacity-50`}
                >
                  {trading ? 'İşlem yapılıyor...' : (tradeType === 'buy' ? '📈 SATIN AL' : '📉 SAT')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Transaction History */}
        {activeTab === 'history' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">📜 İşlem Geçmişi</h2>
            {transactions.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Henüz işlem yapılmadı.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-gray-400 text-left border-b border-gray-700">
                      <th className="py-3 px-4">Tarih</th>
                      <th className="py-3 px-4">İşlem</th>
                      <th className="py-3 px-4">Hisse</th>
                      <th className="py-3 px-4">Adet</th>
                      <th className="py-3 px-4">Fiyat</th>
                      <th className="py-3 px-4">Toplam</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx, idx) => (
                      <tr key={idx} className="border-b border-gray-700 hover:bg-gray-700/50">
                        <td className="py-3 px-4 text-gray-400">
                          {new Date(tx.date).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-3 py-1 rounded text-sm ${
                            tx.type === 'buy' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
                          }`}>
                            {tx.type === 'buy' ? 'ALIŞ' : 'SATIŞ'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <Link href={`/stock/${tx.symbol}`} className="text-blue-400 hover:underline font-semibold">
                            {tx.symbol}
                          </Link>
                        </td>
                        <td className="py-3 px-4">{tx.quantity}</td>
                        <td className="py-3 px-4">₺{tx.price?.toFixed(2)}</td>
                        <td className="py-3 px-4">₺{tx.total?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
