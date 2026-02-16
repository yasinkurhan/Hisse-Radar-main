"""
KAP Haber Servisi
==================
Kamuyu Aydınlatma Platformu (KAP) haberlerini çeken ve işleyen servis
Her gün tüm hisselerin KAP bildirimleri toplanır
"""

import aiohttp
import asyncio
import json
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import quote

# Sentiment analizi için
# Sentiment analizi için
from .news_sentiment_service import SentimentAnalyzer


class KAPService:
    """
    KAP (Kamuyu Aydınlatma Platformu) Haber Servisi
    ================================================
    Tüm BIST hisselerinin önemli duyurularını toplar
    """
    
    # KAP kategorileri ve önem seviyeleri
    CATEGORY_IMPORTANCE = {
        "FR": {"name": "Finansal Rapor", "importance": "high", "score": 3},
        "ODA": {"name": "Özel Durum Açıklaması", "importance": "high", "score": 3},
        "HABERLER": {"name": "Şirket Haberleri", "importance": "medium", "score": 2},
        "GENEL_KURUL": {"name": "Genel Kurul", "importance": "medium", "score": 2},
        "TEMETTÜ": {"name": "Kar Payı/Temettü", "importance": "high", "score": 3},
        "SERMAYE": {"name": "Sermaye Artırımı", "importance": "high", "score": 3},
        "ORTAKLIK": {"name": "Ortaklık Yapısı", "importance": "medium", "score": 2},
        "YONETIM": {"name": "Yönetim Değişikliği", "importance": "medium", "score": 2},
        "DIGER": {"name": "Diğer", "importance": "low", "score": 1}
    }
    
    # Önemli anahtar kelimeler (sentiment için) - ARTIK news_sentiment_service.py dosyasında yönetiliyor
    # SentimentAnalyzer sınıfı kullanılıyor.
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "kap_news.db")
        self._init_database()
    
    def _init_database(self):
        """SQLite veritabanını oluştur"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # KAP haberleri tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kap_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                category TEXT,
                importance TEXT DEFAULT 'medium',
                publish_date TEXT NOT NULL,
                url TEXT,
                sentiment_score REAL DEFAULT 0,
                sentiment_label TEXT DEFAULT 'neutral',
                source TEXT DEFAULT 'KAP',
                is_processed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, title, publish_date)
            )
        ''')
        
        # Günlük haber toplama durumu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_collection_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_date TEXT NOT NULL,
                total_symbols INTEGER DEFAULT 0,
                total_news INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(collection_date)
            )
        ''')
        
        # Hisse bazlı haber sayısı (index için)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kap_symbol ON kap_news(symbol)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kap_date ON kap_news(publish_date)
        ''')
        
        conn.commit()
        conn.close()
    
    def _analyze_sentiment(self, title: str, summary: str = "") -> Dict[str, Any]:
        """Haber sentiment analizi (Gelişmiş)"""
        text = f"{title} {summary}"
        
        # Gelişmiş SentimentAnalyzer kullan
        result = SentimentAnalyzer.analyze_text(text)
        
        return {
            "score": result["score"],
            "label": result["sentiment"].value,
            "confidence": result["confidence"],
            "positive_keywords": len([k for k in result["keywords"] if k["type"] == "positive"]),
            "negative_keywords": len([k for k in result["keywords"] if k["type"] == "negative"])
        }
    
    def _categorize_news(self, title: str) -> str:
        """Haber kategorisi belirle"""
        title_lower = title.lower()
        
        if any(w in title_lower for w in ["finansal tablo", "bilanço", "gelir tablosu", "faaliyet raporu"]):
            return "FR"
        elif any(w in title_lower for w in ["özel durum", "açıklama", "bildiri"]):
            return "ODA"
        elif any(w in title_lower for w in ["genel kurul", "toplantı"]):
            return "GENEL_KURUL"
        elif any(w in title_lower for w in ["temettü", "kar payı", "kâr payı", "dağıtım"]):
            return "TEMETTÜ"
        elif any(w in title_lower for w in ["sermaye", "artırım", "bedelli", "bedelsiz"]):
            return "SERMAYE"
        elif any(w in title_lower for w in ["ortaklık", "hisse", "pay"]):
            return "ORTAKLIK"
        elif any(w in title_lower for w in ["yönetim", "atama", "görev", "istifa"]):
            return "YONETIM"
        else:
            return "DIGER"
    
    async def fetch_kap_news_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Tek bir hisse için gerçek KAP haberlerini çek (borsapy üzerinden)
        """
        try:
            from .borsapy_fetcher import get_borsapy_fetcher
            fetcher = get_borsapy_fetcher()
            
            news_list = fetcher.get_kap_news(symbol)
            
            if not news_list:
                return []
                
            processed_news = []
            
            for news_item in news_list:
                # borsapy sütunları: Title/title, Date/date, URL/url
                title = (news_item.get('Title') or news_item.get('title') 
                         or news_item.get('text') or "KAP Bildirimi")
                date_val = (news_item.get('Date') or news_item.get('date') 
                           or news_item.get('time') or datetime.now())
                link = (news_item.get('URL') or news_item.get('url') 
                       or news_item.get('link') or "")
                
                # Tarih formatlama
                if isinstance(date_val, (int, float)):
                    news_date = datetime.fromtimestamp(date_val)
                elif isinstance(date_val, str):
                    try:
                        if "." in date_val:
                            try:
                                news_date = datetime.strptime(date_val, "%d.%m.%Y %H:%M:%S")
                            except ValueError:
                                news_date = datetime.strptime(date_val.split(" ")[0], "%d.%m.%Y")
                        else:
                            news_date = datetime.strptime(date_val[:10], "%Y-%m-%d")
                    except:
                        news_date = datetime.now()
                else:
                    news_date = date_val if isinstance(date_val, datetime) else datetime.now()
                
                # Kategoriyi belirle
                category = self._categorize_news(title)
                cat_info = self.CATEGORY_IMPORTANCE.get(category, self.CATEGORY_IMPORTANCE["DIGER"])
                
                # Duygu analizi yap (kendi keyword-based analizi kullan)
                sentiment = self._analyze_sentiment(title)
                
                processed_news.append({
                    "symbol": symbol,
                    "title": title,
                    "summary": title,
                    "source": "KAP",
                    "url": link,
                    "publish_date": news_date.isoformat(),
                    "category": category,
                    "importance": cat_info.get("name", "Diğer"),
                    "importance_score": cat_info["score"],
                    "sentiment_score": sentiment["score"],
                    "sentiment_label": sentiment["label"]
                })
            
            return processed_news
            
        except Exception as e:
            print(f"KAP haber çekme hatası ({symbol}): {e}")
            return []
    
    def save_news_to_db(self, news_list: List[Dict[str, Any]]) -> int:
        """Haberleri veritabanına kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        for news in news_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO kap_news 
                    (symbol, title, summary, category, importance, publish_date, url, 
                     sentiment_score, sentiment_label, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    news["symbol"],
                    news["title"],
                    news.get("summary", ""),
                    news.get("category", "DIGER"),
                    news.get("importance", "low"),
                    news["publish_date"],
                    news.get("url", ""),
                    news.get("sentiment_score", 0),
                    news.get("sentiment_label", "neutral"),
                    news.get("source", "KAP")
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                    
            except Exception as e:
                print(f"Haber kayıt hatası: {e}")
                continue
        
        conn.commit()
        conn.close()
        return saved_count
    
    def get_news_for_symbol(self, symbol: str, limit: int = 20, days: int = 30) -> List[Dict[str, Any]]:
        """Veritabanından hisse haberlerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT symbol, title, summary, category, importance, publish_date, 
                   url, sentiment_score, sentiment_label, source
            FROM kap_news
            WHERE symbol = ? AND publish_date >= ?
            ORDER BY publish_date DESC
            LIMIT ?
        ''', (symbol, cutoff_date, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        news_list = []
        for row in rows:
            news_list.append({
                "symbol": row[0],
                "title": row[1],
                "summary": row[2],
                "category": row[3],
                "category_name": self.CATEGORY_IMPORTANCE.get(row[3], {}).get("name", "Diğer"),
                "importance": row[4],
                "publish_date": row[5],
                "url": row[6],
                "sentiment_score": row[7],
                "sentiment_label": row[8],
                "source": row[9]
            })
        
        return news_list
    
    def get_all_recent_news(self, limit: int = 100, days: int = 7) -> List[Dict[str, Any]]:
        """Tüm hisselerin son haberlerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT symbol, title, summary, category, importance, publish_date, 
                   url, sentiment_score, sentiment_label, source
            FROM kap_news
            WHERE publish_date >= ?
            ORDER BY publish_date DESC
            LIMIT ?
        ''', (cutoff_date, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        news_list = []
        for row in rows:
            news_list.append({
                "symbol": row[0],
                "title": row[1],
                "summary": row[2],
                "category": row[3],
                "category_name": self.CATEGORY_IMPORTANCE.get(row[3], {}).get("name", "Diğer"),
                "importance": row[4],
                "publish_date": row[5],
                "url": row[6],
                "sentiment_score": row[7],
                "sentiment_label": row[8],
                "source": row[9]
            })
        
        return news_list
    
    def get_news_statistics(self) -> Dict[str, Any]:
        """Haber istatistikleri"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Toplam haber sayısı
        cursor.execute('SELECT COUNT(*) FROM kap_news')
        total = cursor.fetchone()[0]
        
        # Bugünkü haberler
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute('SELECT COUNT(*) FROM kap_news WHERE publish_date LIKE ?', (f"{today}%",))
        today_count = cursor.fetchone()[0]
        
        # Hisse başına haber sayısı
        cursor.execute('''
            SELECT symbol, COUNT(*) as count 
            FROM kap_news 
            GROUP BY symbol 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_symbols = cursor.fetchall()
        
        # Sentiment dağılımı
        cursor.execute('''
            SELECT sentiment_label, COUNT(*) as count 
            FROM kap_news 
            GROUP BY sentiment_label
        ''')
        sentiment_dist = cursor.fetchall()
        
        # Kategori dağılımı
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM kap_news 
            GROUP BY category 
            ORDER BY count DESC
        ''')
        category_dist = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_news": total,
            "today_news": today_count,
            "top_symbols": [{"symbol": s[0], "count": s[1]} for s in top_symbols],
            "sentiment_distribution": {s[0]: s[1] for s in sentiment_dist},
            "category_distribution": {c[0]: c[1] for c in category_dist}
        }
    
    def get_sentiment_summary(self, days: int = 30, min_news: int = 1) -> List[Dict[str, Any]]:
        """Hisse bazlı KAP sentiment özeti"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as total_news,
                AVG(sentiment_score) as avg_sentiment,
                SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                MAX(publish_date) as latest_news_date,
                GROUP_CONCAT(DISTINCT category) as categories
            FROM kap_news
            WHERE publish_date >= ?
            GROUP BY symbol
            HAVING COUNT(*) >= ?
            ORDER BY avg_sentiment DESC
        ''', (cutoff_date, min_news))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            avg_sent = row[2] or 0
            if avg_sent > 0.15:
                overall = "positive"
            elif avg_sent < -0.15:
                overall = "negative"
            else:
                overall = "neutral"
            
            results.append({
                "symbol": row[0],
                "total_news": row[1],
                "avg_sentiment": round(avg_sent, 3),
                "overall_sentiment": overall,
                "positive_count": row[3],
                "negative_count": row[4],
                "neutral_count": row[5],
                "latest_news_date": row[6],
                "categories": row[7].split(",") if row[7] else []
            })
        
        return results


class DailyNewsCollector:
    """
    Günlük Haber Toplayıcı
    ======================
    Her gün belirli saatte tüm hisselerin haberlerini toplar
    """
    
    def __init__(self, kap_service: KAPService = None):
        self.kap_service = kap_service or KAPService()
        self.all_symbols = self._load_all_symbols()
    
    def _load_all_symbols(self) -> List[str]:
        """Tüm BIST hisselerini yükle"""
        try:
            stocks_path = Path(__file__).parent.parent / "data" / "bist_stocks.json"
            with open(stocks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [s["symbol"] for s in data.get("stocks", [])]
        except:
            # Varsayılan olarak en aktif hisseler
            return [
                "THYAO", "SASA", "EREGL", "ASELS", "AKBNK", "GARAN", "YKBNK",
                "KCHOL", "SAHOL", "TUPRS", "FROTO", "TOASO", "BIMAS", "MGROS",
                "TCELL", "TTKOM", "EKGYO", "PGSUS", "TAVHL", "VESTL", "ARCLK",
                "SISE", "ENKAI", "KOZAL", "ISCTR", "VAKBN", "HALKB", "PETKM"
            ]
    
    async def collect_news_for_batch(self, symbols: List[str], batch_size: int = 10) -> Dict[str, int]:
        """Grup halinde hisse haberleri topla (paralel)"""
        import concurrent.futures
        
        results = {"success": 0, "error": 0, "total_news": 0}
        
        def _fetch_and_process(symbol: str) -> tuple:
            """Senkron wrapper: tek hisse fetch + DB kaydet"""
            try:
                from app.services.borsapy_fetcher import get_borsapy_fetcher
                import pandas as pd
                fetcher = get_borsapy_fetcher()
                
                raw_news = fetcher.get_kap_news(symbol)
                if not raw_news:
                    return (symbol, 0, None)
                
                processed = []
                for item in raw_news:
                    title = (item.get('Title') or item.get('title') 
                             or item.get('text') or "KAP Bildirimi")
                    date_val = (item.get('Date') or item.get('date') 
                               or item.get('time') or "")
                    link = (item.get('URL') or item.get('url') 
                           or item.get('link') or "")
                    
                    # Tarih formatlama
                    news_date = datetime.now()
                    if isinstance(date_val, str) and date_val:
                        try:
                            if "." in date_val:
                                try:
                                    news_date = datetime.strptime(date_val, "%d.%m.%Y %H:%M:%S")
                                except ValueError:
                                    news_date = datetime.strptime(date_val.split(" ")[0], "%d.%m.%Y")
                            elif "-" in date_val:
                                news_date = datetime.strptime(date_val[:10], "%Y-%m-%d")
                        except:
                            pass
                    
                    category = self.kap_service._categorize_news(title)
                    sentiment = self.kap_service._analyze_sentiment(title)
                    cat_info = self.kap_service.CATEGORY_IMPORTANCE.get(category, {})
                    
                    processed.append({
                        "symbol": symbol,
                        "title": title,
                        "summary": title,
                        "source": "KAP",
                        "url": link,
                        "publish_date": news_date.isoformat(),
                        "category": category,
                        "importance": cat_info.get("name", "Diğer"),
                        "sentiment_score": sentiment["score"],
                        "sentiment_label": sentiment["label"]
                    })
                
                saved = self.kap_service.save_news_to_db(processed)
                return (symbol, saved, None)
            except Exception as e:
                return (symbol, 0, str(e))
        
        # Batch'ler halinde paralel çalıştır
        loop = asyncio.get_event_loop()
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            # Batch içindeki sembolleri paralel çek
            tasks = [loop.run_in_executor(None, _fetch_and_process, sym) for sym in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for symbol, saved, error in batch_results:
                if error:
                    results["error"] += 1
                else:
                    results["success"] += 1
                    results["total_news"] += saved
            
            print(f"Batch {batch_num}/{total_batches} tamamlandı: {len(batch)} hisse, {sum(r[1] for r in batch_results)} haber")
            
            # Batch arası kısa bekleme (rate limiting)
            if i + batch_size < len(symbols):
                await asyncio.sleep(0.5)
        
        return results
    
    async def run_daily_collection(self) -> Dict[str, Any]:
        """Günlük haber toplama işlemini çalıştır"""
        start_time = datetime.now()
        collection_date = start_time.strftime("%Y-%m-%d")
        
        print(f"=== Günlük haber toplama başladı: {collection_date} ===")
        print(f"Toplam {len(self.all_symbols)} hisse taranacak")
        
        # Haberleri topla
        results = await self.collect_news_for_batch(self.all_symbols, batch_size=10)
        
        # Süreyi hesapla
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log kaydet
        conn = sqlite3.connect(self.kap_service.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO news_collection_log 
            (collection_date, total_symbols, total_news, success_count, error_count, duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            collection_date,
            len(self.all_symbols),
            results["total_news"],
            results["success"],
            results["error"],
            duration,
            "completed"
        ))
        
        conn.commit()
        conn.close()
        
        summary = {
            "date": collection_date,
            "total_symbols": len(self.all_symbols),
            "news_collected": results["total_news"],
            "success_count": results["success"],
            "error_count": results["error"],
            "duration_seconds": round(duration, 2),
            "status": "completed"
        }
        
        print(f"=== Günlük haber toplama tamamlandı ===")
        print(f"Süre: {duration:.1f} saniye")
        print(f"Toplanan haber: {results['total_news']}")
        
        return summary
    
    def get_collection_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Haber toplama geçmişi"""
        conn = sqlite3.connect(self.kap_service.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT collection_date, total_symbols, total_news, success_count, 
                   error_count, duration_seconds, status
            FROM news_collection_log
            WHERE collection_date >= ?
            ORDER BY collection_date DESC
        ''', (cutoff_date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "date": row[0],
                "total_symbols": row[1],
                "total_news": row[2],
                "success_count": row[3],
                "error_count": row[4],
                "duration_seconds": row[5],
                "status": row[6]
            }
            for row in rows
        ]


# Global servisler
_kap_service: Optional[KAPService] = None
_news_collector: Optional[DailyNewsCollector] = None


def get_kap_service() -> KAPService:
    """KAP servisi singleton"""
    global _kap_service
    if _kap_service is None:
        _kap_service = KAPService()
    return _kap_service


def get_news_collector() -> DailyNewsCollector:
    """Haber toplayıcı singleton"""
    global _news_collector
    if _news_collector is None:
        _news_collector = DailyNewsCollector()
    return _news_collector
