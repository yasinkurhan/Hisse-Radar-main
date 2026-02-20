"""
KAP Background Fetcher
=======================
Tüm BIST hisselerinin KAP bildirimlerini arka planda toplar.
- Uygulama başlangıcında otomatik çalışır
- Her 30 dakikada bir yeniler
- Paralel isteklerle 529 hisseyi ~7 dakikada tarar
- Durum bilgisi API üzerinden takip edilebilir
"""

import asyncio
import json
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class KAPBackgroundFetcher:
    """Arka plan KAP haber toplayıcı"""
    
    def __init__(self):
        self.is_running = False
        self.progress = 0
        self.total_symbols = 0
        self.fetched_count = 0
        self.error_count = 0
        self.total_news = 0
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.last_error: Optional[str] = None
        self.cycle_count = 0
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._all_symbols: List[str] = []
        self._max_workers = 20
        self._batch_size = 25
        self._interval_seconds = 1800  # 30 dakika
    
    def _load_all_symbols(self) -> List[str]:
        """Tüm BIST sembollerini yükle"""
        try:
            stocks_path = Path(__file__).parent.parent / "data" / "bist_stocks.json"
            with open(stocks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                symbols = [s["symbol"] for s in data.get("stocks", [])]
                print(f"[KAP Background] {len(symbols)} sembol yüklendi")
                return symbols
        except Exception as e:
            print(f"[KAP Background] Sembol yükleme hatası: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Mevcut toplama durumunu döndür"""
        return {
            "is_running": self.is_running,
            "progress": self.progress,
            "total_symbols": self.total_symbols,
            "fetched_count": self.fetched_count,
            "error_count": self.error_count,
            "total_news_collected": self.total_news,
            "percent": round((self.progress / self.total_symbols * 100) if self.total_symbols > 0 else 0, 1),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cycle_count": self.cycle_count,
            "last_error": self.last_error,
            "interval_minutes": self._interval_seconds // 60,
            "total_symbols_loaded": len(self._all_symbols)
        }
    
    def _fetch_single_symbol(self, symbol: str) -> Dict[str, Any]:
        """Tek bir sembolün KAP haberlerini çek (senkron - thread içinde çalışır)"""
        try:
            from .borsapy_fetcher import get_borsapy_fetcher
            from .kap_news_service import get_kap_service
            
            fetcher = get_borsapy_fetcher()
            kap_service = get_kap_service()
            
            raw_news = fetcher.get_kap_news(symbol, force_refresh=True)
            
            if raw_news is None:
                return {"symbol": symbol, "count": 0, "error": None}
            
            # DataFrame ise dict listesine çevir
            if isinstance(raw_news, pd.DataFrame):
                if raw_news.empty:
                    return {"symbol": symbol, "count": 0, "error": None}
                items = raw_news.to_dict(orient="records")
            elif isinstance(raw_news, list):
                items = raw_news
            else:
                items = [raw_news] if raw_news else []
            
            # Haberleri işle
            processed = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                title = item.get("Title") or item.get("title") or item.get("text") or "KAP Bildirimi"
                date_val = item.get("Date") or item.get("date") or item.get("time") or ""
                link = item.get("URL") or item.get("url") or item.get("link") or ""
                
                # Tarihi ISO formatına dönüştür
                iso_date = kap_service._normalize_date_to_iso(date_val)
                
                # Sentiment ve kategori analizi
                sentiment = kap_service._analyze_sentiment(title)
                category = kap_service._categorize_news(title)
                cat_info = kap_service.CATEGORY_IMPORTANCE.get(category, {})
                
                processed.append({
                    "symbol": symbol,
                    "title": title,
                    "summary": title,
                    "publish_date": iso_date,
                    "url": link,
                    "source": "KAP",
                    "category": category,
                    "importance": cat_info.get("importance", "medium"),
                    "sentiment_score": sentiment["score"],
                    "sentiment_label": sentiment["label"]
                })
            
            # DB'ye kaydet
            saved = 0
            if processed:
                saved = kap_service.save_news_to_db(processed)
            
            return {"symbol": symbol, "count": saved, "total": len(processed), "error": None}
            
        except Exception as e:
            return {"symbol": symbol, "count": 0, "error": str(e)}
    
    async def _run_single_cycle(self):
        """Tek bir toplama döngüsü çalıştır"""
        if self.is_running:
            print("[KAP Background] Zaten çalışıyor, atlıyorum")
            return
        
        self.is_running = True
        self.progress = 0
        self.fetched_count = 0
        self.error_count = 0
        self.total_news = 0
        self.started_at = datetime.now().isoformat()
        self.completed_at = None
        self.last_error = None
        
        if not self._all_symbols:
            self._all_symbols = self._load_all_symbols()
        
        self.total_symbols = len(self._all_symbols)
        print(f"[KAP Background] Döngü #{self.cycle_count + 1} başlıyor - {self.total_symbols} sembol")
        
        start_time = time.time()
        loop = asyncio.get_event_loop()
        
        # Batch'ler halinde paralel çalıştır
        for i in range(0, self.total_symbols, self._batch_size):
            if self._stop_event.is_set():
                print("[KAP Background] Durdurma sinyali alındı")
                break
            
            batch = self._all_symbols[i:i + self._batch_size]
            batch_num = i // self._batch_size + 1
            total_batches = (self.total_symbols + self._batch_size - 1) // self._batch_size
            
            # Thread pool ile paralel fetch
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                tasks = [
                    loop.run_in_executor(executor, self._fetch_single_symbol, sym)
                    for sym in batch
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Sonuçları işle
            for result in results:
                self.progress += 1
                if isinstance(result, Exception):
                    self.error_count += 1
                    self.last_error = str(result)
                elif isinstance(result, dict):
                    if result.get("error"):
                        self.error_count += 1
                        self.last_error = result["error"]
                    else:
                        self.fetched_count += 1
                        self.total_news += result.get("count", 0)
            
            # Her 5 batch'te bir log
            if batch_num % 5 == 0 or batch_num == total_batches:
                elapsed = time.time() - start_time
                print(f"[KAP Background] Batch {batch_num}/{total_batches} - "
                      f"{self.progress}/{self.total_symbols} sembol - "
                      f"{self.total_news} yeni haber - {elapsed:.0f}sn")
            
            # Batch arası kısa bekleme (rate limiting)
            if i + self._batch_size < self.total_symbols:
                await asyncio.sleep(0.3)
        
        elapsed = time.time() - start_time
        self.completed_at = datetime.now().isoformat()
        self.is_running = False
        self.cycle_count += 1
        
        print(f"[KAP Background] Döngü #{self.cycle_count} tamamlandı - "
              f"{self.fetched_count}/{self.total_symbols} başarılı, "
              f"{self.error_count} hata, "
              f"{self.total_news} yeni haber, "
              f"{elapsed:.1f}sn")
    
    async def start(self):
        """Background fetcher'ı başlat (periyodik)"""
        print(f"[KAP Background] Başlatılıyor... (her {self._interval_seconds // 60} dakikada bir)")
        self._stop_event.clear()
        self._all_symbols = self._load_all_symbols()
        
        async def _periodic_loop():
            while not self._stop_event.is_set():
                try:
                    await self._run_single_cycle()
                except Exception as e:
                    print(f"[KAP Background] Döngü hatası: {e}")
                    self.is_running = False
                    self.last_error = str(e)
                
                # Sonraki döngüyü bekle (veya stop sinyali)
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._interval_seconds
                    )
                    # Stop sinyali alındı
                    break
                except asyncio.TimeoutError:
                    # Normal timeout, sonraki döngüye devam
                    continue
        
        self._task = asyncio.create_task(_periodic_loop())
    
    async def stop(self):
        """Background fetcher'ı durdur"""
        print("[KAP Background] Durduruluyor...")
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.is_running = False
        print("[KAP Background] Durduruldu")
    
    async def trigger_refresh(self):
        """Manuel yenileme tetikle (mevcut çalışmıyorsa)"""
        if self.is_running:
            return {"status": "already_running", **self.get_status()}
        
        # Yeni döngü başlat
        asyncio.create_task(self._run_single_cycle())
        return {"status": "started", **self.get_status()}


# Singleton instance
_background_fetcher: Optional[KAPBackgroundFetcher] = None


def get_background_fetcher() -> KAPBackgroundFetcher:
    """Background fetcher singleton"""
    global _background_fetcher
    if _background_fetcher is None:
        _background_fetcher = KAPBackgroundFetcher()
    return _background_fetcher
