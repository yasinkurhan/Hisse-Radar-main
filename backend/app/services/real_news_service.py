"""
HisseRadar Gerçek Haber Servisi
================================
Google News RSS ve diğer ücretsiz kaynaklardan gerçek haberler
"""

import feedparser
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import quote
import re
import html
from .news_sentiment_service import SentimentAnalyzer, SentimentType


class GoogleNewsService:
    """
    Google News RSS Servisi
    =======================
    Ücretsiz ve yasal haber çekme
    """
    
    BASE_URL = "https://news.google.com/rss/search"
    
    # Hisse isimleri (arama için)
    STOCK_NAMES = {
        "THYAO": "Türk Hava Yolları THY",
        "SASA": "SASA Polyester",
        "EREGL": "Ereğli Demir Çelik",
        "ASELS": "ASELSAN",
        "AKBNK": "Akbank",
        "GARAN": "Garanti Bankası",
        "YKBNK": "Yapı Kredi",
        "KCHOL": "Koç Holding",
        "SAHOL": "Sabancı Holding",
        "TUPRS": "Tüpraş",
        "FROTO": "Ford Otosan",
        "TOASO": "Tofaş",
        "BIMAS": "BİM Mağazaları",
        "MGROS": "Migros",
        "TCELL": "Turkcell",
        "TTKOM": "Türk Telekom",
        "EKGYO": "Emlak Konut GYO",
        "PGSUS": "Pegasus",
        "TAVHL": "TAV Havalimanları",
        "VESTL": "Vestel",
        "ARCLK": "Arçelik",
        "KORDS": "Kordsa",
        "PETKM": "Petkim",
        "SISE": "Şişecam",
        "ENKAI": "Enka İnşaat",
        "KOZAL": "Koza Altın",
        "KOZAA": "Koza Anadolu Metal",
        "DOHOL": "Doğan Holding",
        "HEKTS": "Hektaş",
        "OYAKC": "Oyak Çimento",
        "ISCTR": "İş Bankası",
        "VAKBN": "Vakıfbank",
        "HALKB": "Halkbank",
        "BJKAS": "Beşiktaş",
        "FENER": "Fenerbahçe",
        "GSRAY": "Galatasaray",
        "TSKB": "TSKB",
        "ALARK": "Alarko Holding",
        "AEFES": "Anadolu Efes",
        "ULKER": "Ülker",
        "TTRAK": "Türk Traktör",
        "OTKAR": "Otokar",
        "ISGYO": "İş GYO",
    }
    
    @staticmethod
    def _clean_html(text: str) -> str:
        """HTML etiketlerini temizle"""
        # HTML entities decode
        text = html.unescape(text)
        # HTML taglarını kaldır
        text = re.sub(r'<[^>]+>', '', text)
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Tarihi parse et"""
        try:
            # feedparser zaten parsed time veriyor
            if hasattr(date_str, 'tm_year'):
                dt = datetime(*date_str[:6])
                return dt.strftime("%Y-%m-%d %H:%M")
            return date_str
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    @staticmethod
    async def fetch_news(symbol: str, limit: int = 10, stock_name: str = None) -> List[Dict[str, Any]]:
        """
        Hisse için Google News'den haber çek
        """
        # Arama terimi oluştur — dışarıdan gelen isim öncelikli, yoksa sözlükten
        if not stock_name:
            stock_name = GoogleNewsService.STOCK_NAMES.get(symbol, symbol)
        search_query = f"{stock_name} hisse borsa"
        
        # URL oluştur
        encoded_query = quote(search_query)
        url = f"{GoogleNewsService.BASE_URL}?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
        
        try:
            # RSS feed'i parse et
            feed = feedparser.parse(url)
            
            news_list = []
            for entry in feed.entries[:limit]:
                title = GoogleNewsService._clean_html(entry.get('title', ''))
                summary = GoogleNewsService._clean_html(entry.get('summary', entry.get('description', '')))
                
                # Source'u title'dan çıkar (genelde " - Kaynak" formatında)
                source = "Google News"
                if ' - ' in title:
                    parts = title.rsplit(' - ', 1)
                    if len(parts) == 2:
                        title = parts[0]
                        source = parts[1]
                
                # Tarih
                pub_date = entry.get('published_parsed', entry.get('updated_parsed'))
                date_str = GoogleNewsService._parse_date(pub_date) if pub_date else datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Sentiment analizi
                full_text = f"{title} {summary}"
                sentiment_result = SentimentAnalyzer.analyze_text(full_text)
                
                news_list.append({
                    "title": title,
                    "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                    "source": source,
                    "date": date_str,
                    "url": entry.get('link', '#'),
                    "symbol": symbol,
                    "sentiment": sentiment_result["sentiment"].value,
                    "sentiment_score": sentiment_result["score"],
                    "keywords": sentiment_result.get("keywords", [])[:3],
                    "is_real": True
                })
            
            return news_list
            
        except Exception as e:
            print(f"Google News hatası ({symbol}): {e}")
            return []
    
    @staticmethod
    async def fetch_market_news(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Genel borsa haberleri çek
        """
        search_queries = [
            "Borsa İstanbul BIST",
            "BIST 100 endeks",
            "Türkiye ekonomi borsa",
        ]
        
        all_news = []
        
        for query in search_queries:
            encoded_query = quote(query)
            url = f"{GoogleNewsService.BASE_URL}?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
            
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:limit // len(search_queries)]:
                    title = GoogleNewsService._clean_html(entry.get('title', ''))
                    summary = GoogleNewsService._clean_html(entry.get('summary', ''))
                    
                    source = "Google News"
                    if ' - ' in title:
                        parts = title.rsplit(' - ', 1)
                        if len(parts) == 2:
                            title = parts[0]
                            source = parts[1]
                    
                    pub_date = entry.get('published_parsed')
                    date_str = GoogleNewsService._parse_date(pub_date) if pub_date else datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    full_text = f"{title} {summary}"
                    sentiment_result = SentimentAnalyzer.analyze_text(full_text)
                    
                    all_news.append({
                        "title": title,
                        "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                        "source": source,
                        "date": date_str,
                        "url": entry.get('link', '#'),
                        "symbol": "BIST",
                        "category": "piyasa",
                        "sentiment": sentiment_result["sentiment"].value,
                        "sentiment_score": sentiment_result["score"],
                        "is_real": True
                    })
                    
            except Exception as e:
                print(f"Market news hatası: {e}")
                continue
        
        # Tarihe göre sırala ve limit uygula
        all_news.sort(key=lambda x: x["date"], reverse=True)
        return all_news[:limit]


class FinansHaberService:
    """
    Finans Haber Siteleri RSS
    =========================
    Ekonomi ve finans haberleri
    """
    
    RSS_FEEDS = {
        "bloomberght": {
            "url": "https://www.bloomberght.com/rss",
            "name": "Bloomberg HT"
        },
        "dunya": {
            "url": "https://www.dunya.com/rss",
            "name": "Dünya Gazetesi"
        },
        "ekonomist": {
            "url": "https://www.ekonomist.com.tr/feed",
            "name": "Ekonomist"
        }
    }
    
    @staticmethod
    async def fetch_from_rss(feed_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """RSS feed'den haber çek"""
        if feed_key not in FinansHaberService.RSS_FEEDS:
            return []
        
        feed_info = FinansHaberService.RSS_FEEDS[feed_key]
        
        try:
            feed = feedparser.parse(feed_info["url"])
            
            news_list = []
            for entry in feed.entries[:limit]:
                title = html.unescape(entry.get('title', ''))
                summary = html.unescape(entry.get('summary', entry.get('description', '')))
                summary = re.sub(r'<[^>]+>', '', summary)
                
                pub_date = entry.get('published_parsed')
                if pub_date:
                    date_str = datetime(*pub_date[:6]).strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                full_text = f"{title} {summary}"
                sentiment_result = SentimentAnalyzer.analyze_text(full_text)
                
                news_list.append({
                    "title": title,
                    "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                    "source": feed_info["name"],
                    "date": date_str,
                    "url": entry.get('link', '#'),
                    "sentiment": sentiment_result["sentiment"].value,
                    "sentiment_score": sentiment_result["score"],
                    "is_real": True
                })
            
            return news_list
            
        except Exception as e:
            print(f"RSS hatası ({feed_key}): {e}")
            return []
    
    @staticmethod
    async def fetch_all_finance_news(limit: int = 30) -> List[Dict[str, Any]]:
        """Tüm finans RSS kaynaklarından haber çek"""
        all_news = []
        
        for feed_key in FinansHaberService.RSS_FEEDS.keys():
            news = await FinansHaberService.fetch_from_rss(feed_key, limit // 3)
            all_news.extend(news)
        
        # Tarihe göre sırala
        all_news.sort(key=lambda x: x["date"], reverse=True)
        return all_news[:limit]


class RealNewsAggregator:
    """
    Gerçek Haber Toplayıcı
    ======================
    Tüm kaynaklardan haberleri birleştirir
    """
    
    @staticmethod
    async def get_stock_news(symbol: str, limit: int = 15) -> Dict[str, Any]:
        """Hisse için tüm kaynaklardan haber topla"""
        
        # Google News'den hisse haberleri
        google_news = await GoogleNewsService.fetch_news(symbol, limit)
        
        # Genel piyasa haberleri de ekle
        market_news = await GoogleNewsService.fetch_market_news(5)
        
        # Birleştir
        all_news = google_news + [n for n in market_news if n not in google_news]
        
        # Sentiment hesapla
        if all_news:
            avg_sentiment = sum(n["sentiment_score"] for n in all_news) / len(all_news)
            positive = sum(1 for n in all_news if n["sentiment_score"] > 0.1)
            negative = sum(1 for n in all_news if n["sentiment_score"] < -0.1)
        else:
            avg_sentiment = 0
            positive = 0
            negative = 0
        
        # Sentiment label
        if avg_sentiment > 0.3:
            label = "🚀 Çok Olumlu"
        elif avg_sentiment > 0.1:
            label = "📈 Olumlu"
        elif avg_sentiment < -0.3:
            label = "🔻 Çok Olumsuz"
        elif avg_sentiment < -0.1:
            label = "📉 Olumsuz"
        else:
            label = "➖ Nötr"
        
        return {
            "symbol": symbol,
            "total_news": len(all_news),
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": label,
            "positive_news": positive,
            "negative_news": negative,
            "neutral_news": len(all_news) - positive - negative,
            "news": all_news[:limit],
            "source": "Google News + RSS",
            "is_real_data": True,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    @staticmethod
    async def get_market_summary() -> Dict[str, Any]:
        """Piyasa geneli haber özeti"""
        
        # Genel piyasa haberleri
        market_news = await GoogleNewsService.fetch_market_news(20)
        
        # Finans haberleri
        finance_news = await FinansHaberService.fetch_all_finance_news(15)
        
        # Birleştir (duplicate'leri kaldır)
        seen_titles = set()
        all_news = []
        
        for news in market_news + finance_news:
            title_key = news["title"][:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_news.append(news)
        
        # Tarihe göre sırala
        all_news.sort(key=lambda x: x["date"], reverse=True)
        
        # Sentiment hesapla
        if all_news:
            avg_sentiment = sum(n["sentiment_score"] for n in all_news) / len(all_news)
            positive = sum(1 for n in all_news if n["sentiment_score"] > 0.1)
            negative = sum(1 for n in all_news if n["sentiment_score"] < -0.1)
        else:
            avg_sentiment = 0
            positive = 0
            negative = 0
        
        return {
            "market_sentiment_score": round(avg_sentiment, 3),
            "market_sentiment_label": "Olumlu" if avg_sentiment > 0.1 else "Olumsuz" if avg_sentiment < -0.1 else "Nötr",
            "total_news": len(all_news),
            "positive_news": positive,
            "negative_news": negative,
            "neutral_news": len(all_news) - positive - negative,
            "news": all_news[:30],
            "sources": ["Google News", "Bloomberg HT", "Dünya", "Ekonomist"],
            "is_real_data": True,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    @staticmethod
    async def get_multiple_stocks_sentiment(symbols: List[str]) -> List[Dict[str, Any]]:
        """Birden fazla hisse için sentiment"""
        results = []
        
        for symbol in symbols:
            try:
                news_data = await GoogleNewsService.fetch_news(symbol, 5)
                
                if news_data:
                    avg_sentiment = sum(n["sentiment_score"] for n in news_data) / len(news_data)
                else:
                    avg_sentiment = 0
                
                if avg_sentiment > 0.3:
                    label = "🚀 Çok Olumlu"
                elif avg_sentiment > 0.1:
                    label = "📈 Olumlu"
                elif avg_sentiment < -0.3:
                    label = "🔻 Çok Olumsuz"
                elif avg_sentiment < -0.1:
                    label = "📉 Olumsuz"
                else:
                    label = "➖ Nötr"
                
                results.append({
                    "symbol": symbol,
                    "sentiment_score": round(avg_sentiment, 3),
                    "sentiment_label": label,
                    "news_count": len(news_data),
                    "latest_headline": news_data[0]["title"] if news_data else None
                })
            except Exception as e:
                print(f"Sentiment hatası ({symbol}): {e}")
                results.append({
                    "symbol": symbol,
                    "sentiment_score": 0,
                    "sentiment_label": "➖ Veri Yok",
                    "news_count": 0,
                    "latest_headline": None
                })
        
        # Skora göre sırala
        results.sort(key=lambda x: x["sentiment_score"], reverse=True)
        return results
