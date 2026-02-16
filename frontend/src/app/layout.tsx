import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import './globals.css';
import PWAProvider from '@/components/PWAProvider';
import PWAInstallPrompt from '@/components/PWAInstallPrompt';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'HisseRadar - BIST Borsa Analiz Platformu',
  description: 'Borsa İstanbul hisseleri için kapsamlı teknik ve temel analiz platformu',
  keywords: ['borsa', 'BIST', 'hisse', 'analiz', 'teknik analiz', 'temel analiz', 'yatırım'],
  authors: [{ name: 'HisseRadar' }],
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'HisseRadar',
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    title: 'HisseRadar - BIST Borsa Analiz Platformu',
    description: 'Borsa İstanbul hisseleri için kapsamlı teknik ve temel analiz platformu',
    type: 'website',
  },
  other: {
    'mobile-web-app-capable': 'yes',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#3b82f6',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <head>
        {/* PWA Meta Tags */}
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" href="/icons/icon-192x192.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.svg" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="HisseRadar" />
        <meta name="msapplication-TileColor" content="#3b82f6" />
        <meta name="msapplication-TileImage" content="/icons/icon-144x144.svg" />
      </head>
      <body className={`${inter.className} bg-slate-900 min-h-screen`}>
        <PWAProvider>
          {/* Header */}
          <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-14 sm:h-16">
                {/* Logo */}
                <Link href="/" className="flex items-center space-x-1.5 sm:space-x-2">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-5 h-5 sm:w-6 sm:h-6 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <span className="text-lg sm:text-xl font-bold text-white">
                    Hisse<span className="text-primary-400">Radar</span>
                  </span>
                </Link>

                {/* Desktop Navigation */}
                <nav className="hidden md:flex items-center space-x-3 lg:space-x-5">
                  <Link
                    href="/analysis"
                    className="text-slate-300 hover:text-primary-400 transition-colors font-medium text-sm"
                  >
                    Analiz
                  </Link>
                  <Link
                    href="/market"
                    className="text-slate-300 hover:text-primary-400 transition-colors font-medium flex items-center gap-1 text-sm"
                  >
                    <span className="text-xs bg-gradient-to-r from-purple-500 to-blue-500 text-white px-1.5 py-0.5 rounded">PRO</span>
                    Piyasa
                  </Link>
                  <Link
                    href="/economy"
                    className="text-slate-300 hover:text-emerald-400 transition-colors font-medium text-sm"
                  >
                    Ekonomi
                  </Link>
                  <Link
                    href="/fx"
                    className="text-slate-300 hover:text-amber-400 transition-colors font-medium text-sm"
                  >
                    Döviz
                  </Link>
                  <Link
                    href="/screener"
                    className="text-slate-300 hover:text-violet-400 transition-colors font-medium text-sm"
                  >
                    Tarama
                  </Link>
                  <Link
                    href="/news"
                    className="text-slate-300 hover:text-primary-400 transition-colors font-medium text-sm"
                  >
                    Haberler
                  </Link>
                  <Link
                    href="/heatmap"
                    className="text-slate-300 hover:text-primary-400 transition-colors font-medium text-sm"
                  >
                    Isı Haritası
                  </Link>
                </nav>

                {/* Mobile Menu Button + Badge */}
                <div className="flex items-center space-x-2">
                  <span className="hidden sm:inline text-xs text-slate-400 bg-slate-700 px-2 py-1 rounded">
                    Gecikmeli Veri
                  </span>

                  {/* Mobile Menu */}
                  <div className="md:hidden relative group">
                    <button className="p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-700">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                      </svg>
                    </button>

                    {/* Dropdown Menu */}
                    <div className="absolute right-0 top-full mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                      <div className="py-2">
                        <Link href="/analysis" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          📊 Analiz
                        </Link>
                        <Link href="/market" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          🏢 PRO Piyasa
                        </Link>
                        <Link href="/economy" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          🏦 Ekonomi
                        </Link>
                        <Link href="/fx" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          💱 Döviz & Altın
                        </Link>
                        <Link href="/screener" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          🔍 Hisse Tarama
                        </Link>
                        <Link href="/viop" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          📊 VIOP
                        </Link>
                        <Link href="/heatmap" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          🗺️ Isı Haritası
                        </Link>
                        <Link href="/compare" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          📈 Karşılaştır
                        </Link>
                        <Link href="/watchlist" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          ⭐ Takip Listesi
                        </Link>
                        <Link href="/portfolio" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          💼 Portföy
                        </Link>
                        <Link href="/alerts" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          🔔 Alarmlar
                        </Link>
                        <Link href="/backtest" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          🧪 Backtest
                        </Link>
                        <Link href="/news" className="block px-4 py-2.5 text-slate-300 hover:bg-slate-700 hover:text-white">
                          📰 Haberler
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="min-h-[calc(100vh-4rem)]">{children}</main>

          {/* Footer */}
          <footer className="bg-slate-800 border-t border-slate-700 py-6 sm:py-8">
            <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
              <div className="flex flex-col md:flex-row justify-between items-center text-center md:text-left">
                <div className="text-slate-400 text-sm">
                  &copy; 2026 HisseRadar. Tüm hakları saklıdır.
                </div>
                <div className="mt-3 md:mt-0 text-slate-500 text-xs">
                  <p>
                    Bu platform eğitim amaçlıdır. Yatırım tavsiyesi değildir.
                  </p>
                  <p className="mt-1">
                    Veriler borsapy kütüphanesi ile İş Yatırım, TradingView, KAP, TCMB kaynaklarından alınmaktadır.
                  </p>
                </div>
              </div>
            </div>
          </footer>

          {/* PWA Install Prompt */}
          <PWAInstallPrompt />
        </PWAProvider>
      </body>
    </html>
  );
}
