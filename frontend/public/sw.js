// HisseRadar Service Worker v1.2.0 - Forced Update
const CACHE_NAME = 'hisseradar-v1.2';
const RUNTIME_CACHE = 'hisseradar-runtime';

// Önbelleğe alınacak statik dosyalar
const STATIC_ASSETS = [
  '/',
  '/analysis',
  '/portfolio',
  '/watchlist',
  '/heatmap',
  '/compare',
  '/alerts',
  '/backtest',
  '/offline',
  '/manifest.json',
];

// API endpoint'leri için cache stratejisi
const API_CACHE_DURATION = 5 * 60 * 1000; // 5 dakika

// Install event - statik dosyaları önbelleğe al
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Service Worker installed');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Cache failed:', error);
      })
  );
});

// Activate event - eski cache'leri temizle
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - network-first stratejisi
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // POST, PUT, DELETE gibi istekleri Service Worker'dan geçirme — doğrudan ağa bırak
  if (request.method !== 'GET') {
    return;
  }

  // API istekleri için
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstWithCache(request));
    return;
  }

  // Statik dosyalar için cache-first
  if (request.destination === 'image' ||
    request.destination === 'font' ||
    request.destination === 'style' ||
    request.destination === 'script') {
    event.respondWith(cacheFirstWithNetwork(request));
    return;
  }

  // HTML sayfaları için network-first
  if (request.mode === 'navigate') {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }

  // Diğer istekler için network-first
  event.respondWith(networkFirstWithCache(request));
});

// Network-first with cache fallback
async function networkFirstWithCache(request) {
  try {
    const networkResponse = await fetch(request);

    // Başarılı yanıtı cache'e kaydet
    if (networkResponse.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    // Network başarısız, cache'den dene
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Cache'de de yoksa hata döndür
    return new Response(JSON.stringify({
      error: 'Çevrimdışısınız',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Cache-first with network fallback
async function cacheFirstWithNetwork(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    // Placeholder döndür
    return new Response('', { status: 404 });
  }
}

// Network-first with offline page fallback
async function networkFirstWithOffline(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    // Cache'den dene
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Offline sayfasını göster
    const offlineResponse = await caches.match('/offline');
    if (offlineResponse) {
      return offlineResponse;
    }

    // Son çare: basit offline mesajı
    return new Response(`
      <!DOCTYPE html>
      <html lang="tr">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Çevrimdışı - HisseRadar</title>
          <style>
            body {
              font-family: system-ui, -apple-system, sans-serif;
              background: #0f172a;
              color: #f1f5f9;
              display: flex;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              margin: 0;
              text-align: center;
              padding: 20px;
            }
            .container { max-width: 400px; }
            h1 { color: #3b82f6; }
            p { color: #94a3b8; }
            button {
              background: #3b82f6;
              color: white;
              border: none;
              padding: 12px 24px;
              border-radius: 8px;
              font-size: 16px;
              cursor: pointer;
              margin-top: 20px;
            }
            button:hover { background: #2563eb; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>📡 Çevrimdışısınız</h1>
            <p>İnternet bağlantınızı kontrol edin. Bağlantı sağlandığında sayfa otomatik olarak yenilenecektir.</p>
            <button onclick="location.reload()">Tekrar Dene</button>
          </div>
          <script>
            window.addEventListener('online', () => location.reload());
          </script>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// Push notification event
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let data = {
    title: 'HisseRadar',
    body: 'Yeni bildirim',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'hisseradar-notification',
    data: {}
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/icons/icon-192x192.png',
    badge: data.badge || '/icons/badge-72x72.png',
    tag: data.tag,
    data: data.data,
    vibrate: [100, 50, 100],
    actions: data.actions || [
      { action: 'view', title: 'Görüntüle' },
      { action: 'dismiss', title: 'Kapat' }
    ],
    requireInteraction: data.requireInteraction || false
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Açık pencere varsa onu kullan
        for (const client of windowClients) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(urlToOpen);
            return client.focus();
          }
        }
        // Yoksa yeni pencere aç
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-watchlist') {
    event.waitUntil(syncWatchlist());
  }

  if (event.tag === 'sync-portfolio') {
    event.waitUntil(syncPortfolio());
  }
});

// Watchlist senkronizasyonu
async function syncWatchlist() {
  try {
    const cache = await caches.open(RUNTIME_CACHE);
    const pendingData = await cache.match('/pending-watchlist');

    if (pendingData) {
      const data = await pendingData.json();
      // API'ye gönder
      await fetch('/api/user/watchlist/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      // Pending veriyi temizle
      await cache.delete('/pending-watchlist');
    }
  } catch (error) {
    console.error('[SW] Watchlist sync failed:', error);
  }
}

// Portfolio senkronizasyonu
async function syncPortfolio() {
  try {
    const cache = await caches.open(RUNTIME_CACHE);
    const pendingData = await cache.match('/pending-portfolio');

    if (pendingData) {
      const data = await pendingData.json();
      await fetch('/api/user/portfolio/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      await cache.delete('/pending-portfolio');
    }
  } catch (error) {
    console.error('[SW] Portfolio sync failed:', error);
  }
}

// Periodic background sync (Chrome only)
self.addEventListener('periodicsync', (event) => {
  console.log('[SW] Periodic sync:', event.tag);

  if (event.tag === 'update-prices') {
    event.waitUntil(updatePrices());
  }
});

// Fiyat güncelleme
async function updatePrices() {
  try {
    // Takip listesindeki hisselerin fiyatlarını güncelle
    const watchlistResponse = await fetch('/api/user/watchlist');
    const watchlist = await watchlistResponse.json();

    if (watchlist.stocks && watchlist.stocks.length > 0) {
      const symbols = watchlist.stocks.map(s => s.symbol).join(',');
      const pricesResponse = await fetch(`/api/price/batch?symbols=${symbols}`);
      const prices = await pricesResponse.json();

      // Fiyat değişimi varsa bildirim gönder
      checkPriceAlerts(prices);
    }
  } catch (error) {
    console.error('[SW] Price update failed:', error);
  }
}

// Fiyat alarm kontrolü
async function checkPriceAlerts(prices) {
  try {
    const alertsResponse = await fetch('/api/user/alerts');
    const alerts = await alertsResponse.json();

    if (!alerts.alerts) return;

    for (const alert of alerts.alerts) {
      const price = prices.find(p => p.symbol === alert.symbol);
      if (!price) continue;

      let triggered = false;
      let message = '';

      if (alert.type === 'above' && price.currentPrice >= alert.targetPrice) {
        triggered = true;
        message = `${alert.symbol} hedef fiyatın (₺${alert.targetPrice}) üzerine çıktı: ₺${price.currentPrice.toFixed(2)}`;
      } else if (alert.type === 'below' && price.currentPrice <= alert.targetPrice) {
        triggered = true;
        message = `${alert.symbol} hedef fiyatın (₺${alert.targetPrice}) altına düştü: ₺${price.currentPrice.toFixed(2)}`;
      }

      if (triggered) {
        self.registration.showNotification('🔔 Fiyat Alarmı!', {
          body: message,
          icon: '/icons/icon-192x192.png',
          badge: '/icons/badge-72x72.png',
          tag: `alert-${alert.symbol}`,
          data: { url: `/stock/${alert.symbol}` },
          vibrate: [200, 100, 200],
          requireInteraction: true
        });
      }
    }
  } catch (error) {
    console.error('[SW] Alert check failed:', error);
  }
}

console.log('[SW] Service Worker loaded');
