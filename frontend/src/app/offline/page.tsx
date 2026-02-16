'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { WifiOff, RefreshCw, Home, BarChart3, Briefcase } from 'lucide-react';

export default function OfflinePage() {
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => {
      setIsOnline(true);
      // Online olunca ana sayfaya yönlendir
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    };
    
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        {/* Icon */}
        <div className="w-24 h-24 mx-auto mb-8 bg-gray-800 rounded-full flex items-center justify-center">
          <WifiOff className="w-12 h-12 text-gray-400" />
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-white mb-4">
          Çevrimdışısınız
        </h1>

        {/* Description */}
        <p className="text-gray-400 mb-8">
          İnternet bağlantınız yok gibi görünüyor. Bağlantı sağlandığında sayfa otomatik olarak yenilenecektir.
        </p>

        {/* Status */}
        {isOnline ? (
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mb-8">
            <p className="text-green-400 font-medium flex items-center justify-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              Bağlantı sağlandı, yönlendiriliyorsunuz...
            </p>
          </div>
        ) : (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-8">
            <p className="text-yellow-400 font-medium flex items-center justify-center gap-2">
              <span className="w-2 h-2 bg-yellow-400 rounded-full" />
              Bağlantı bekleniyor...
            </p>
          </div>
        )}

        {/* Retry Button */}
        <button
          onClick={() => window.location.reload()}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-semibold transition mb-4"
        >
          <RefreshCw className="w-5 h-5" />
          Tekrar Dene
        </button>

        {/* Cached Pages */}
        <div className="mt-8">
          <p className="text-gray-500 text-sm mb-4">Önbelleğe alınmış sayfalar:</p>
          <div className="grid grid-cols-3 gap-2">
            <Link
              href="/"
              className="flex flex-col items-center gap-2 p-3 bg-gray-800/50 rounded-xl hover:bg-gray-800 transition"
            >
              <Home className="w-5 h-5 text-gray-400" />
              <span className="text-gray-300 text-xs">Ana Sayfa</span>
            </Link>
            <Link
              href="/analysis"
              className="flex flex-col items-center gap-2 p-3 bg-gray-800/50 rounded-xl hover:bg-gray-800 transition"
            >
              <BarChart3 className="w-5 h-5 text-gray-400" />
              <span className="text-gray-300 text-xs">Analiz</span>
            </Link>
            <Link
              href="/portfolio"
              className="flex flex-col items-center gap-2 p-3 bg-gray-800/50 rounded-xl hover:bg-gray-800 transition"
            >
              <Briefcase className="w-5 h-5 text-gray-400" />
              <span className="text-gray-300 text-xs">Portföy</span>
            </Link>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-8 text-left bg-gray-800/30 rounded-xl p-4">
          <h3 className="text-white font-semibold mb-2 text-sm">💡 İpuçları</h3>
          <ul className="text-gray-400 text-xs space-y-1">
            <li>• WiFi veya mobil veri bağlantınızı kontrol edin</li>
            <li>• Uçak modunun kapalı olduğundan emin olun</li>
            <li>• Yönlendiricinizi yeniden başlatmayı deneyin</li>
            <li>• Daha önce ziyaret ettiğiniz sayfalar önbellekte olabilir</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
