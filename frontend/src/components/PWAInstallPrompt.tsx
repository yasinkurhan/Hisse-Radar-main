'use client';

import { useState, useEffect } from 'react';
import { X, Download, Smartphone, Bell, Wifi, WifiOff } from 'lucide-react';
import { usePWA } from './PWAProvider';

export default function PWAInstallPrompt() {
  const { 
    canInstallPWA, 
    installPWA, 
    isPWA, 
    isOnline,
    notificationPermission,
    enableNotifications,
    updateAvailable,
    reloadForUpdate
  } = usePWA();

  const [showInstallBanner, setShowInstallBanner] = useState(false);
  const [showOfflineToast, setShowOfflineToast] = useState(false);
  const [showUpdateToast, setShowUpdateToast] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Install banner göster
  useEffect(() => {
    if (canInstallPWA && !isPWA && !dismissed) {
      const timer = setTimeout(() => {
        const lastDismissed = localStorage.getItem('pwa-install-dismissed');
        if (!lastDismissed || Date.now() - parseInt(lastDismissed) > 7 * 24 * 60 * 60 * 1000) {
          setShowInstallBanner(true);
        }
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [canInstallPWA, isPWA, dismissed]);

  // Offline toast
  useEffect(() => {
    if (!isOnline) {
      setShowOfflineToast(true);
    } else {
      setShowOfflineToast(false);
    }
  }, [isOnline]);

  // Update toast
  useEffect(() => {
    if (updateAvailable) {
      setShowUpdateToast(true);
    }
  }, [updateAvailable]);

  const handleInstall = async () => {
    const success = await installPWA();
    if (success) {
      setShowInstallBanner(false);
    }
  };

  const handleDismiss = () => {
    setShowInstallBanner(false);
    setDismissed(true);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  const handleEnableNotifications = async () => {
    await enableNotifications();
  };

  return (
    <>
      {/* Install Banner */}
      {showInstallBanner && (
        <div className="fixed bottom-0 inset-x-0 z-50 p-4 sm:p-6 animate-slide-up">
          <div className="max-w-md mx-auto bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-2xl overflow-hidden">
            <div className="p-4 sm:p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center shrink-0">
                  <Smartphone className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-white font-bold text-lg">HisseRadar'ı Yükle</h3>
                  <p className="text-white/80 text-sm mt-1">
                    Ana ekrana ekle, offline kullan, bildirim al!
                  </p>
                </div>
                <button 
                  onClick={handleDismiss}
                  className="text-white/60 hover:text-white p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex gap-3 mt-4">
                <button
                  onClick={handleInstall}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition"
                >
                  <Download className="w-5 h-5" />
                  Yükle
                </button>
                <button
                  onClick={handleDismiss}
                  className="px-4 py-2.5 text-white/80 hover:text-white font-medium"
                >
                  Daha Sonra
                </button>
              </div>
            </div>

            {/* Özellikler */}
            <div className="bg-black/20 px-4 sm:px-6 py-3 flex items-center justify-center gap-6 text-white/70 text-xs">
              <span className="flex items-center gap-1">
                <Wifi className="w-4 h-4" /> Offline
              </span>
              <span className="flex items-center gap-1">
                <Bell className="w-4 h-4" /> Bildirimler
              </span>
              <span className="flex items-center gap-1">
                <Download className="w-4 h-4" /> Hızlı Erişim
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Notification Permission Banner (PWA içinde) */}
      {isPWA && notificationPermission === 'default' && (
        <div className="fixed top-4 inset-x-4 z-50 sm:top-6 sm:right-6 sm:left-auto sm:w-80">
          <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-xl p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center shrink-0">
                <Bell className="w-5 h-5 text-blue-400" />
              </div>
              <div className="flex-1">
                <h4 className="text-white font-semibold text-sm">Bildirimleri Aç</h4>
                <p className="text-gray-400 text-xs mt-1">
                  Fiyat alarmları ve önemli güncellemeler için
                </p>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={handleEnableNotifications}
                    className="px-3 py-1.5 bg-blue-500 text-white text-xs rounded-lg font-medium hover:bg-blue-600"
                  >
                    İzin Ver
                  </button>
                  <button
                    onClick={() => {}}
                    className="px-3 py-1.5 text-gray-400 text-xs hover:text-white"
                  >
                    Sonra
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Offline Toast */}
      {showOfflineToast && (
        <div className="fixed top-4 inset-x-4 z-50 sm:top-6 sm:left-1/2 sm:-translate-x-1/2 sm:w-auto">
          <div className="bg-yellow-500 text-yellow-900 rounded-xl shadow-lg px-4 py-3 flex items-center gap-3">
            <WifiOff className="w-5 h-5 shrink-0" />
            <span className="font-medium text-sm">Çevrimdışı moddasınız</span>
          </div>
        </div>
      )}

      {/* Update Toast */}
      {showUpdateToast && (
        <div className="fixed bottom-4 inset-x-4 z-50 sm:bottom-6 sm:right-6 sm:left-auto sm:w-80">
          <div className="bg-green-500 text-white rounded-xl shadow-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Download className="w-5 h-5" />
                <span className="font-medium text-sm">Yeni sürüm mevcut!</span>
              </div>
              <button
                onClick={reloadForUpdate}
                className="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium"
              >
                Güncelle
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
