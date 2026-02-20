/**
 * HisseRadar PWA Utilities
 * Service Worker, Push Notifications, Offline Support
 */

// Service Worker kayıt
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    console.log('[PWA] Service Worker desteklenmiyor');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none'
    });

    console.log('[PWA] Service Worker kayıtlı:', registration.scope);

    // Güncelleme kontrolü
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // Yeni versiyon hazır
            dispatchEvent(new CustomEvent('sw-update-available'));
          }
        });
      }
    });

    return registration;
  } catch (error) {
    console.error('[PWA] Service Worker kayıt hatası:', error);
    return null;
  }
}

// Push notification izni iste
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.log('[PWA] Bildirimler desteklenmiyor');
    return 'denied';
  }

  if (Notification.permission === 'granted') {
    return 'granted';
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission;
  }

  return Notification.permission;
}

// Push subscription oluştur
export async function subscribeToPush(registration: ServiceWorkerRegistration): Promise<PushSubscription | null> {
  try {
    // VAPID public key (gerçek uygulamada .env'den alınmalı)
    const vapidPublicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || 
      'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U';
    
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
    });

    console.log('[PWA] Push subscription oluşturuldu');
    
    // Subscription'ı backend'e gönder
    await savePushSubscription(subscription);
    
    return subscription;
  } catch (error) {
    console.error('[PWA] Push subscription hatası:', error);
    return null;
  }
}

// Base64 to Uint8Array
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  
  return outputArray;
}

// Subscription'ı backend'e kaydet
async function savePushSubscription(subscription: PushSubscription): Promise<void> {
  try {
    await fetch('http://localhost:8001/api/user/push-subscription', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subscription.toJSON())
    });
  } catch (error) {
    console.error('[PWA] Push subscription kaydetme hatası:', error);
  }
}

// Local notification göster
export function showLocalNotification(
  title: string, 
  options?: NotificationOptions
): void {
  if (!('Notification' in window) || Notification.permission !== 'granted') {
    return;
  }

  const defaultOptions: NotificationOptions = {
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    tag: 'hisseradar-local',
    ...options
  };

  new Notification(title, defaultOptions);
}

// Online/Offline durumu
export function isOnline(): boolean {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

// Online/Offline event listener
export function onConnectionChange(callback: (online: boolean) => void): () => void {
  if (typeof window === 'undefined') return () => {};

  const handleOnline = () => callback(true);
  const handleOffline = () => callback(false);

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}

// Install prompt yönetimi
let deferredPrompt: BeforeInstallPromptEvent | null = null;

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function setupInstallPrompt(): void {
  if (typeof window === 'undefined') return;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e as BeforeInstallPromptEvent;
    dispatchEvent(new CustomEvent('pwa-install-available'));
  });
}

export async function promptInstall(): Promise<boolean> {
  if (!deferredPrompt) return false;

  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  deferredPrompt = null;
  
  return outcome === 'accepted';
}

export function canInstall(): boolean {
  return deferredPrompt !== null;
}

// PWA olarak çalışıyor mu?
export function isRunningAsPWA(): boolean {
  if (typeof window === 'undefined') return false;
  
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as any).standalone === true;
}

// Cache temizleme
export async function clearCache(): Promise<void> {
  if ('caches' in window) {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(name => caches.delete(name)));
    console.log('[PWA] Cache temizlendi');
  }
}

// Background sync kaydet
export async function registerBackgroundSync(tag: string): Promise<boolean> {
  if (!('serviceWorker' in navigator) || !('sync' in window)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    await (registration as any).sync.register(tag);
    console.log('[PWA] Background sync kayıtlı:', tag);
    return true;
  } catch (error) {
    console.error('[PWA] Background sync hatası:', error);
    return false;
  }
}

// Offline data kaydet
export async function saveOfflineData(key: string, data: any): Promise<void> {
  try {
    localStorage.setItem(`offline_${key}`, JSON.stringify({
      data,
      timestamp: Date.now()
    }));
  } catch (error) {
    console.error('[PWA] Offline data kaydetme hatası:', error);
  }
}

// Offline data oku
export function getOfflineData<T>(key: string, maxAge?: number): T | null {
  try {
    const stored = localStorage.getItem(`offline_${key}`);
    if (!stored) return null;

    const { data, timestamp } = JSON.parse(stored);
    
    if (maxAge && Date.now() - timestamp > maxAge) {
      localStorage.removeItem(`offline_${key}`);
      return null;
    }

    return data as T;
  } catch (error) {
    return null;
  }
}
