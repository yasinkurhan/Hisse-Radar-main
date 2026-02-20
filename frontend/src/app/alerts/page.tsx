'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Alert {
  id: string;
  symbol: string;
  alert_type: string;
  condition: string;
  value: number;
  note: string;
  created: string;
  triggered?: boolean;
  triggered_at?: string;
  triggered_price?: number;
}

interface AlertsData {
  active: Alert[];
  triggered: Alert[];
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertsData>({ active: [], triggered: [] });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'active' | 'triggered' | 'create'>('active');
  
  // Create form
  const [symbol, setSymbol] = useState('');
  const [alertType, setAlertType] = useState('price_above');
  const [value, setValue] = useState('');
  const [note, setNote] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/user/alerts');
      const data = await res.json();
      setAlerts(data);
    } catch (error) {
      console.error('Alarmlar yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };

  const createAlert = async () => {
    if (!symbol || !value) {
      alert('Hisse ve değer alanları zorunlu');
      return;
    }

    setCreating(true);
    try {
      const res = await fetch('http://localhost:8001/api/user/alerts/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: symbol.toUpperCase(),
          alert_type: alertType,
          value: parseFloat(value),
          note
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        alert('Alarm oluşturuldu!');
        setSymbol('');
        setValue('');
        setNote('');
        fetchAlerts();
        setActiveTab('active');
      }
    } catch (error) {
      alert('Hata oluştu');
    } finally {
      setCreating(false);
    }
  };

  const deleteAlert = async (alertId: string) => {
    if (!confirm('Alarmı silmek istediğinize emin misiniz?')) return;
    
    try {
      await fetch(`http://localhost:8001/api/user/alerts/delete?alert_id=${alertId}`, { method: 'POST' });
      fetchAlerts();
    } catch (error) {
      alert('Hata oluştu');
    }
  };

  const resetAlert = async (alertId: string) => {
    try {
      await fetch(`http://localhost:8001/api/user/alerts/reset?alert_id=${alertId}`, { method: 'POST' });
      fetchAlerts();
    } catch (error) {
      alert('Hata oluştu');
    }
  };

  const getAlertTypeText = (type: string) => {
    switch (type) {
      case 'price_above': return '📈 Fiyat Üstünde';
      case 'price_below': return '📉 Fiyat Altında';
      case 'score_above': return '⬆️ Skor Üstünde';
      case 'score_below': return '⬇️ Skor Altında';
      case 'signal_change': return '🔄 Sinyal Değişimi';
      default: return type;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Alarmlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">🔔 Fiyat Alarmları</h1>
            <p className="text-gray-400 mt-1">Fiyat ve sinyal değişikliklerinde bildirim alın</p>
          </div>
          <Link href="/" className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded">
            Ana Sayfa
          </Link>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <p className="text-gray-400">Aktif Alarmlar</p>
            <p className="text-4xl font-bold text-blue-400">{alerts.active.length}</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <p className="text-gray-400">Tetiklenen</p>
            <p className="text-4xl font-bold text-yellow-400">{alerts.triggered.length}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button 
            onClick={() => setActiveTab('active')}
            className={`px-6 py-2 rounded ${activeTab === 'active' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            Aktif ({alerts.active.length})
          </button>
          <button 
            onClick={() => setActiveTab('triggered')}
            className={`px-6 py-2 rounded ${activeTab === 'triggered' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            Tetiklenen ({alerts.triggered.length})
          </button>
          <button 
            onClick={() => setActiveTab('create')}
            className={`px-6 py-2 rounded ${activeTab === 'create' ? 'bg-green-600' : 'bg-gray-700 hover:bg-gray-600'}`}
          >
            + Yeni Alarm
          </button>
        </div>

        {/* Active Alerts */}
        {activeTab === 'active' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">🔔 Aktif Alarmlar</h2>
            {alerts.active.length === 0 ? (
              <p className="text-gray-400 text-center py-8">
                Henüz alarm yok. "Yeni Alarm" sekmesinden oluşturabilirsiniz.
              </p>
            ) : (
              <div className="space-y-3">
                {alerts.active.map((alert) => (
                  <div key={alert.id} className="bg-gray-700 rounded-lg p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Link href={`/stock/${alert.symbol}`} className="text-blue-400 hover:underline font-bold text-lg">
                        {alert.symbol}
                      </Link>
                      <span className="text-gray-300">{getAlertTypeText(alert.alert_type)}</span>
                      <span className="text-yellow-400 font-semibold">₺{alert.value}</span>
                      {alert.note && <span className="text-gray-400 text-sm">({alert.note})</span>}
                    </div>
                    <button 
                      onClick={() => deleteAlert(alert.id)}
                      className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                    >
                      Sil
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Triggered Alerts */}
        {activeTab === 'triggered' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">⚡ Tetiklenen Alarmlar</h2>
            {alerts.triggered.length === 0 ? (
              <p className="text-gray-400 text-center py-8">
                Henüz tetiklenen alarm yok.
              </p>
            ) : (
              <div className="space-y-3">
                {alerts.triggered.map((alert) => (
                  <div key={alert.id} className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-4">
                        <Link href={`/stock/${alert.symbol}`} className="text-blue-400 hover:underline font-bold text-lg">
                          {alert.symbol}
                        </Link>
                        <span className="text-gray-300">{getAlertTypeText(alert.alert_type)}</span>
                        <span className="text-yellow-400 font-semibold">₺{alert.value}</span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">
                        Tetiklenme: {alert.triggered_at ? new Date(alert.triggered_at).toLocaleString('tr-TR') : '-'} 
                        {alert.triggered_price && ` - Fiyat: ₺${alert.triggered_price}`}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => resetAlert(alert.id)}
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                      >
                        Tekrar Aktif Et
                      </button>
                      <button 
                        onClick={() => deleteAlert(alert.id)}
                        className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                      >
                        Sil
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Create Alert */}
        {activeTab === 'create' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">➕ Yeni Alarm Oluştur</h2>
            <div className="max-w-md mx-auto space-y-4">
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
                <label className="block text-gray-400 mb-2">Alarm Tipi</label>
                <select
                  value={alertType}
                  onChange={(e) => setAlertType(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-3"
                >
                  <option value="price_above">📈 Fiyat bu değerin üstüne çıkarsa</option>
                  <option value="price_below">📉 Fiyat bu değerin altına düşerse</option>
                  <option value="score_above">⬆️ Skor bu değerin üstüne çıkarsa</option>
                  <option value="score_below">⬇️ Skor bu değerin altına düşerse</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-400 mb-2">
                  {alertType.includes('price') ? 'Fiyat (₺)' : 'Skor (0-100)'}
                </label>
                <input
                  type="number"
                  step={alertType.includes('price') ? '0.01' : '1'}
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder={alertType.includes('price') ? 'Örn: 250.50' : 'Örn: 70'}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-3"
                />
              </div>

              <div>
                <label className="block text-gray-400 mb-2">Not (opsiyonel)</label>
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Örn: Kısa vadeli hedef"
                  className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-3"
                />
              </div>

              <button
                onClick={createAlert}
                disabled={creating}
                className="w-full bg-green-600 hover:bg-green-700 py-4 rounded font-semibold text-lg disabled:opacity-50"
              >
                {creating ? 'Oluşturuluyor...' : '🔔 Alarm Oluştur'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
