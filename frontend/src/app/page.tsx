'use client';

/**
 * HisseRadar Ana Sayfa
 * =====================
 * BIST hisse analiz platformunun ana sayfası
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, TrendingUp, BarChart3, PieChart, Zap, LineChart, Calendar, Bell, Briefcase, Target, History, Newspaper } from 'lucide-react';
import StockSearch from '@/components/StockSearch';
import StockList from '@/components/StockList';

export default function HomePage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-primary-700 text-white py-2 sm:py-3 overflow-x-auto">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between min-w-max sm:min-w-0">
            <Link href="/" className="flex items-center space-x-2 flex-shrink-0">
              <span className="text-xl sm:text-2xl">📡</span>
              <span className="font-bold text-lg sm:text-xl">HisseRadar</span>
            </Link>
            <div className="flex items-center space-x-1 sm:space-x-2 ml-4">
              <Link
                href="/analysis"
                className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-xs sm:text-sm"
              >
                <LineChart className="w-4 h-4" />
                <span className="hidden xs:inline">Analiz</span>
              </Link>
              <Link
                href="/heatmap"
                className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-xs sm:text-sm"
              >
                <PieChart className="w-4 h-4" />
                <span className="hidden sm:inline">Isı Haritası</span>
              </Link>
              <Link
                href="/compare"
                className="hidden sm:flex items-center space-x-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-sm"
              >
                <BarChart3 className="w-4 h-4" />
                <span className="hidden sm:inline">Karşılaştır</span>
              </Link>
              <Link
                href="/watchlist"
                className="hidden md:flex items-center space-x-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-sm"
              >
                <Target className="w-4 h-4" />
                <span className="hidden sm:inline">Takip</span>
              </Link>
              <Link
                href="/portfolio"
                className="hidden md:flex items-center space-x-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-sm"
              >
                <Briefcase className="w-4 h-4" />
                <span className="hidden sm:inline">Portföy</span>
              </Link>
              <Link
                href="/alerts"
                className="hidden lg:flex items-center space-x-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-sm"
              >
                <Bell className="w-4 h-4" />
                <span className="hidden sm:inline">Alarmlar</span>
              </Link>
              <Link
                href="/backtest"
                className="hidden lg:flex items-center space-x-2 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition text-sm"
              >
                <History className="w-4 h-4" />
                <span className="hidden sm:inline">Backtest</span>
              </Link>
              <Link
                href="/news"
                className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 sm:py-2 bg-yellow-500/80 hover:bg-yellow-500 rounded-lg transition text-xs sm:text-sm"
              >
                <Newspaper className="w-4 h-4" />
                <span className="hidden xs:inline">Haberler</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 to-primary-800 text-white py-10 sm:py-16">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-2xl sm:text-4xl md:text-5xl font-bold mb-3 sm:mb-4">
              BIST Hisse Analiz Platformu
            </h1>
            <p className="text-base sm:text-xl text-primary-100 mb-6 sm:mb-8 max-w-2xl mx-auto px-2">
              500+ BIST hissesini gelişmiş teknik analiz, backtesting ve sanal portföy ile takip edin.
            </p>

            {/* Arama */}
            <div className="max-w-xl mx-auto px-2">
              <StockSearch placeholder="Hisse ara... (örn: THYAO, Garanti)" />
            </div>

            {/* Hızlı erişim */}
            <div className="mt-6 sm:mt-8 flex flex-wrap justify-center gap-2 sm:gap-3 px-2">
              <Link href="/stock/THYAO" className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-full text-xs sm:text-sm transition-colors">
                THYAO
              </Link>
              <Link href="/stock/GARAN" className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-full text-xs sm:text-sm transition-colors">
                GARAN
              </Link>
              <Link href="/stock/ASELS" className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-full text-xs sm:text-sm transition-colors">
                ASELS
              </Link>
              <Link href="/stock/SISE" className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-full text-xs sm:text-sm transition-colors">
                SISE
              </Link>
              <Link href="/stock/KCHOL" className="px-3 sm:px-4 py-1.5 sm:py-2 bg-white/10 hover:bg-white/20 rounded-full text-xs sm:text-sm transition-colors">
                KCHOL
              </Link>
            </div>

            {/* Analiz CTA */}
            <div className="mt-8 sm:mt-10 px-2">
              <Link
                href="/analysis"
                className="inline-flex items-center space-x-2 px-5 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 rounded-xl text-base sm:text-lg font-semibold transition shadow-lg hover:shadow-xl"
              >
                <LineChart className="w-5 h-5 sm:w-6 sm:h-6" />
                <span>Otomatik Hisse Analizi Başlat</span>
              </Link>
              <p className="text-primary-200 text-xs sm:text-sm mt-2 sm:mt-3">
                500+ hisseyi saniyeler içinde analiz edin
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Yeni Özellikler */}
      <section className="py-8 sm:py-12 bg-gradient-to-r from-blue-900 to-purple-900 text-white">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <h2 className="text-xl sm:text-2xl font-bold text-center mb-6 sm:mb-8">🚀 Yeni Özellikler</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-4">
            <Link href="/screener" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <Zap className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-violet-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Gelişmiş Tarama</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Teknik & temel tarama</p>
            </Link>
            <Link href="/heatmap" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <PieChart className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-orange-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Isı Haritası</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Sektör performansı</p>
            </Link>
            <Link href="/compare" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <BarChart3 className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-cyan-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Karşılaştır</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Hisse performansı</p>
            </Link>
            <Link href="/watchlist" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <Target className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-yellow-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Takip Listesi</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Favori hisseler</p>
            </Link>
            <Link href="/portfolio" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <Briefcase className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-green-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Sanal Portföy</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Risk almadan pratik</p>
            </Link>
            <Link href="/alerts" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <Bell className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-red-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Fiyat Alarmları</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Fiyat değişimleri</p>
            </Link>
            <Link href="/news" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <Newspaper className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-amber-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">KAP Haberleri</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Güncel bildirimler</p>
            </Link>
            <Link href="/backtest" className="bg-white/10 hover:bg-white/20 rounded-xl p-3 sm:p-6 text-center transition">
              <History className="w-8 h-8 sm:w-10 sm:h-10 mx-auto mb-2 sm:mb-3 text-blue-400" />
              <h3 className="font-semibold text-sm sm:text-base mb-0.5 sm:mb-1">Backtest</h3>
              <p className="text-xs text-gray-300 hidden sm:block">Sinyal performansı</p>
            </Link>
          </div>
          
          {/* Yeni Stok Detay Özellikleri */}
          <div className="mt-8 bg-white/5 rounded-xl p-4 sm:p-6 border border-white/10">
            <h3 className="text-lg font-semibold text-center mb-4">✨ Yeni: Gelişmiş Hisse Analizi</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl mb-1">🌍</div>
                <div className="text-sm font-medium">ETF Sahipliği</div>
                <div className="text-xs text-gray-400">Yabancı ETF portföyleri</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl mb-1">🎯</div>
                <div className="text-sm font-medium">Analist Tahminleri</div>
                <div className="text-xs text-gray-400">Hedef fiyat & öneriler</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl mb-1">📡</div>
                <div className="text-sm font-medium">Teknik Sinyaller</div>
                <div className="text-xs text-gray-400">AL/SAT/NÖTR sinyalleri</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl mb-1">⚡</div>
                <div className="text-sm font-medium">Osilatör Analizi</div>
                <div className="text-xs text-gray-400">RSI, MACD, Stochastic</div>
              </div>
            </div>
            <p className="text-xs text-gray-400 text-center mt-3">
              Herhangi bir hisseye tıklayıp &quot;Analist &amp; ETF&quot; ve &quot;Teknik Sinyaller&quot; sekmelerini kullanabilirsiniz
            </p>
          </div>
        </div>
      </section>

      {/* Özellikler */}
      <section className="py-10 sm:py-16 bg-white">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 text-center mb-8 sm:mb-12">
            Teknik Analiz Araçları
          </h2>

          <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-6 gap-2 sm:gap-4">
            {/* RSI */}
            <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-xl">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3">
                <span className="text-blue-600 font-bold text-xs sm:text-sm">RSI</span>
              </div>
              <h3 className="font-semibold text-gray-900 text-xs sm:text-sm">RSI (14)</h3>
              <p className="text-[10px] sm:text-xs text-gray-600 hidden sm:block">Aşırı alım/satım</p>
            </div>

            {/* MACD */}
            <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-xl">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3">
                <BarChart3 className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 text-xs sm:text-sm">MACD</h3>
              <p className="text-[10px] sm:text-xs text-gray-600 hidden sm:block">Momentum</p>
            </div>

            {/* Bollinger */}
            <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-xl">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3">
                <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 text-xs sm:text-sm">Bollinger</h3>
              <p className="text-[10px] sm:text-xs text-gray-600 hidden sm:block">Volatilite</p>
            </div>

            {/* ADX */}
            <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-xl">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-orange-100 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3">
                <span className="text-orange-600 font-bold text-xs sm:text-sm">ADX</span>
              </div>
              <h3 className="font-semibold text-gray-900 text-xs sm:text-sm">ADX</h3>
              <p className="text-[10px] sm:text-xs text-gray-600 hidden sm:block">Trend gücü</p>
            </div>

            {/* Fibonacci */}
            <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-xl">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-yellow-100 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3">
                <span className="text-yellow-600 font-bold text-xs sm:text-sm">Fib</span>
              </div>
              <h3 className="font-semibold text-gray-900 text-xs sm:text-sm">Fibonacci</h3>
              <p className="text-[10px] sm:text-xs text-gray-600 hidden sm:block">Destek/Direnç</p>
            </div>

            {/* OBV */}
            <div className="text-center p-2 sm:p-4 bg-gray-50 rounded-xl">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-red-100 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3">
                <span className="text-red-600 font-bold text-xs sm:text-sm">OBV</span>
              </div>
              <h3 className="font-semibold text-gray-900 text-xs sm:text-sm">OBV</h3>
              <p className="text-[10px] sm:text-xs text-gray-600 hidden sm:block">Hacim analizi</p>
            </div>
          </div>
        </div>
      </section>

      {/* Analiz Öne Çıkan */}
      <section className="py-12 bg-gradient-to-r from-purple-600 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-3xl font-bold mb-4">🎯 Akıllı Analiz Sistemi</h2>
              <p className="text-lg text-white/90 mb-6">
                500+ BIST hissesini gelişmiş göstergeler ve formasyonlarla analiz edin.
                Dinamik skorlama sistemi ile en potansiyelli hisseleri keşfedin.
              </p>
              <ul className="space-y-3 mb-6">
                <li className="flex items-center space-x-3">
                  <span className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-sm">âœ“</span>
                  <span>Formasyon tespiti (Çift dip, OBO, Üçgen)</span>
                </li>
                <li className="flex items-center space-x-3">
                  <span className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-sm">âœ“</span>
                  <span>Sektöre göre dinamik ağırlıklandırma</span>
                </li>
                <li className="flex items-center space-x-3">
                  <span className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-sm">âœ“</span>
                  <span>Piyasa koşuluna göre ayarlanan skorlar</span>
                </li>
                <li className="flex items-center space-x-3">
                  <span className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-sm">âœ“</span>
                  <span>Backtest ile sinyal başarı takibi</span>
                </li>
              </ul>
              <Link
                href="/analysis"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-white text-purple-600 hover:bg-gray-100 rounded-lg font-semibold transition"
              >
                <span>Analizi Başlat</span>
                <span>â†’</span>
              </Link>
            </div>
            <div className="bg-white/10 rounded-xl p-6 backdrop-blur">
              <div className="space-y-4">
                <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                  <div>
                    <div className="font-semibold">Günlük Analiz</div>
                    <div className="text-sm text-white/70">502 hisse â€¢ ~50 saniye</div>
                  </div>
                  <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5" />
                  </div>
                </div>
                <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                  <div>
                    <div className="font-semibold">Haftalık Analiz</div>
                    <div className="text-sm text-white/70">Uzun vadeli trendler</div>
                  </div>
                  <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5" />
                  </div>
                </div>
                <div className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                  <div>
                    <div className="font-semibold">Backtest Performansı</div>
                    <div className="text-sm text-white/70">Sinyal başarı oranı</div>
                  </div>
                  <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                    <History className="w-5 h-5" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Hisse Listesi */}
      <section id="stocks" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">
              BIST Hisseleri
            </h2>
            <span className="text-sm text-gray-500">
              500+ hisse
            </span>
          </div>

          <StockList showSectorFilter={true} />
        </div>
      </section>

      {/* Bilgi Banner */}
      <section className="py-12 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-primary-400">502</div>
              <div className="text-gray-400 mt-1">BIST Hissesi</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-400">10+</div>
              <div className="text-gray-400 mt-1">Teknik Gösterge</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-400">5</div>
              <div className="text-gray-400 mt-1">Formasyon Tespiti</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-400">%99.8</div>
              <div className="text-gray-400 mt-1">Analiz Başarısı</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-yellow-400">~50s</div>
              <div className="text-gray-400 mt-1">Analiz Süresi</div>
            </div>
          </div>
        </div>
      </section>

      {/* Uyarı */}
      <section className="py-8 bg-yellow-50 border-t border-yellow-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <span className="text-2xl">âš ï¸</span>
            </div>
            <div>
              <h4 className="font-semibold text-yellow-800 mb-1">Yasal Uyarı</h4>
              <p className="text-sm text-yellow-700">
                Bu platform yatırım tavsiyesi vermez. Tüm bilgiler sadece eğitim amaçlıdır.
                Yatırım kararlarınızı vermeden önce profesyonel danışmanlık alınız.
                Veriler 15-20 dakika gecikmeli olabilir.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-gray-800 text-gray-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <span className="text-xl">📡</span>
              <span className="font-semibold text-white">HisseRadar v2.0</span>
            </div>
            <div className="flex items-center space-x-6 text-sm">
              <Link href="/" className="hover:text-white transition">Ana Sayfa</Link>
              <Link href="/analysis" className="hover:text-white transition">Analiz</Link>
              <Link href="/watchlist" className="hover:text-white transition">Takip</Link>
              <Link href="/portfolio" className="hover:text-white transition">Portföy</Link>
              <Link href="/alerts" className="hover:text-white transition">Alarmlar</Link>
              <Link href="/backtest" className="hover:text-white transition">Backtest</Link>
            </div>
            <div className="text-sm mt-4 md:mt-0">
              Â© 2024 HisseRadar - Veriler borsapy ile İş Yatırım, TradingView, KAP, TCMB kaynaklarından sağlanmaktadır
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
