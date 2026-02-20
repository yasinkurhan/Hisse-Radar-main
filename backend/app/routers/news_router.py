"""
HisseRadar Haber & Sentiment API Router
=======================================
borsapy KAP verileri + Google News RSS üzerinden gerçek haberler
Background fetcher ile TÜM BIST hisselerinin KAP bildirimleri toplanır.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.news_sentiment_service import (
    KAPService as SampleKAPService,
    NewsService,
    MarketSentimentAggregator,
    SentimentAnalyzer,
    SocialSentiment
)
from ..services.real_news_service import (
    GoogleNewsService,
    FinansHaberService,
    RealNewsAggregator
)
from ..services.borsapy_fetcher import get_borsapy_fetcher
from ..services.kap_background_fetcher import get_background_fetcher

router = APIRouter(prefix="/api/news", tags=["news-sentiment"])


@router.get("/kap")
async def get_all_kap_notifications(
    limit: int = Query(100, ge=1, le=500, description="Maksimum bildirim sayısı"),
    days: int = Query(90, ge=1, le=365, description="Son kaç günün haberleri"),
    symbol: str = Query(None, description="Sembol filtresi (opsiyonel)"),
    refresh: bool = Query(False, description="Arka planda yenileme tetikle")
):
    """
    Tüm BIST hisseleri için KAP bildirimlerini getir.
    
    Veriler arka planda periyodik olarak toplanır (her 30 dk).
    - refresh=False: DB'den anında yanıt (hızlı)
    - refresh=True: DB'den yanıt + arka planda yenileme tetikle
    - symbol: Opsiyonel sembol filtresi  
    """
    from ..services.kap_news_service import get_kap_service
    
    try:
        kap_service = get_kap_service()
        bg_fetcher = get_background_fetcher()
        
        # refresh=True ise arka plan yenilemeyi tetikle
        bg_status = None
        if refresh:
            result = await bg_fetcher.trigger_refresh()
            bg_status = result
        
        # Her zaman DB'den hızlı yanıt döndür
        if symbol:
            # Tek sembol filtresi
            db_news = kap_service.get_news_for_symbol(symbol.upper(), limit=limit, days=days)
        else:
            # Tüm haberler
            db_news = kap_service.get_all_recent_news(limit=limit, days=days)
        
        # Background durumu
        collection_info = bg_fetcher.get_status()
        
        return {
            "total": len(db_news),
            "notifications": db_news,
            "source": "database",
            "collection_status": collection_info,
            "background_triggered": refresh,
            "message": f"DB'den {len(db_news)} KAP bildirimi getirildi" + (
                " (arka planda yenileme başlatıldı)" if refresh and bg_status and bg_status.get("status") == "started" else ""
            ) + (
                f" (yenileme zaten devam ediyor: %{collection_info['percent']})" if refresh and bg_status and bg_status.get("status") == "already_running" else ""
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kap/collection-status")
async def get_kap_collection_status():
    """KAP arka plan toplama durumunu döndür"""
    bg_fetcher = get_background_fetcher()
    return bg_fetcher.get_status()


@router.post("/kap/collect")
async def collect_kap_news():
    """
    Tüm BIST hisseleri için KAP haberlerini toplu çek ve DB'ye kaydet.
    Background fetcher'ı tetikler.
    """
    bg_fetcher = get_background_fetcher()
    result = await bg_fetcher.trigger_refresh()
    return result


@router.get("/kap/collect/status")
async def get_collection_status():
    """KAP toplama işleminin durumunu döner"""
    bg_fetcher = get_background_fetcher()
    return bg_fetcher.get_status()


@router.get("/kap/sentiment")
async def get_kap_sentiment_summary(
    days: int = Query(30, ge=1, le=365, description="Son kaç günün verisi"),
    min_news: int = Query(1, ge=1, description="Minimum haber sayısı")
):
    """
    Hisse bazlı KAP sentiment özeti.
    Her hisse için: toplam haber, pozitif/negatif/nötr sayısı, ortalama skor.
    """
    from ..services.kap_news_service import get_kap_service
    
    try:
        kap_service = get_kap_service()
        summary = kap_service.get_sentiment_summary(days=days, min_news=min_news)
        
        # Genel istatistik
        total_positive = sum(1 for s in summary if s["overall_sentiment"] == "positive")
        total_negative = sum(1 for s in summary if s["overall_sentiment"] == "negative")
        total_neutral = sum(1 for s in summary if s["overall_sentiment"] == "neutral")
        
        return {
            "total_stocks": len(summary),
            "overall": {
                "positive": total_positive,
                "negative": total_negative,
                "neutral": total_neutral
            },
            "stocks": summary,
            "period_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kap/stats")
async def get_kap_statistics():
    """KAP haber istatistikleri ve toplama geçmişi"""
    from ..services.kap_news_service import get_kap_service, get_news_collector
    
    try:
        kap_service = get_kap_service()
        collector = get_news_collector()
        
        stats = kap_service.get_news_statistics()
        history = collector.get_collection_history(days=7)
        
        return {
            **stats,
            "collection_history": history,
            "collection_status": get_background_fetcher().get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kap/{symbol}")
async def get_kap_notifications(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Kaç günlük bildirim")
):
    """
    Hisse için KAP bildirimlerini getir (borsapy - gerçek veri)
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **days**: Son kaç günün bildirimleri (varsayılan: 30)
    """
    try:
        symbol = symbol.upper().strip().replace(".IS", "")
        fetcher = get_borsapy_fetcher()
        
        # borsapy üzerinden gerçek KAP haberlerini çek
        raw_news = fetcher.get_kap_news(symbol)
        
        notifications = []
        if raw_news is not None:
            # DataFrame ise dict listesine çevir
            import pandas as pd
            if isinstance(raw_news, pd.DataFrame):
                if not raw_news.empty:
                    items = raw_news.to_dict(orient="records")
                else:
                    items = []
            elif isinstance(raw_news, list):
                items = raw_news
            else:
                items = [raw_news] if raw_news else []
            
            for item in items:
                if isinstance(item, dict):
                    # borsapy sütunları: Date, Title, URL (büyük harf)
                    title = item.get("Title") or item.get("title") or item.get("text") or "KAP Bildirimi"
                    date_val = item.get("Date") or item.get("date") or item.get("time") or ""
                    link = item.get("URL") or item.get("url") or item.get("link") or ""
                    
                    # Sentiment analizi
                    sentiment = SentimentAnalyzer.analyze_text(title)
                    
                    notifications.append({
                        "title": title,
                        "summary": item.get("summary") or title,
                        "date": str(date_val),
                        "url": link,
                        "source": "KAP",
                        "category": _determine_kap_category(title),
                        "sentiment": sentiment["sentiment"].value,
                        "sentiment_score": sentiment["score"],
                        "importance": "high" if any(k in title.lower() for k in ["bilanço", "temettü", "kar", "sermaye", "finansal"]) else "medium"
                    })
        
        # Eğer borsapy'den veri gelemediyse, örnek verilere fallback
        if not notifications:
            notifications = SampleKAPService.get_kap_notifications(symbol, days)
        
        return {
            "symbol": symbol,
            "total": len(notifications),
            "notifications": notifications,
            "source": "borsapy/KAP" if (raw_news is not None and (not hasattr(raw_news, 'empty') or not raw_news.empty)) else "sample"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{symbol}")
async def get_stock_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50, description="Maksimum haber sayısı")
):
    """
    Hisse için haberleri getir
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **limit**: Maksimum haber sayısı (varsayılan: 10)
    """
    try:
        symbol = symbol.upper()
        news = NewsService.get_news(symbol, limit)
        
        return {
            "symbol": symbol,
            "total": len(news),
            "news": news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market")
async def get_market_news(
    limit: int = Query(20, ge=1, le=100, description="Maksimum haber sayısı")
):
    """
    Genel piyasa haberlerini getir
    """
    try:
        news = NewsService.get_market_news(limit)
        
        return {
            "total": len(news),
            "news": news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{symbol}")
async def get_stock_sentiment(symbol: str):
    """
    Hisse için sentiment analizi
    
    KAP bildirimleri ve haberlerden birleşik sentiment
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    """
    try:
        symbol = symbol.upper()
        sentiment = MarketSentimentAggregator.get_stock_sentiment(symbol)
        
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/{symbol}")
async def get_social_sentiment(symbol: str):
    """
    Hisse için sosyal medya sentiment'i
    
    Twitter, StockTwits, Reddit vb. sentiment
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    """
    try:
        symbol = symbol.upper()
        sentiment = SocialSentiment.get_social_sentiment(symbol)
        
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_text_sentiment(text: str = Query(..., min_length=5, description="Analiz edilecek metin")):
    """
    Metin için sentiment analizi
    
    Verilen metni analiz edip sentiment skoru döner
    """
    try:
        result = SentimentAnalyzer.analyze_text(text)
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiment": result["sentiment"].value,
            "score": result["score"],
            "confidence": result["confidence"],
            "keywords": result["keywords"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_market_sentiment_summary():
    """
    Piyasa geneli sentiment özeti
    """
    try:
        # En popüler hisseler için sentiment
        popular_symbols = ["THYAO", "SASA", "EREGL", "ASELS", "AKBNK", "KCHOL", "TUPRS"]
        
        sentiments = []
        for symbol in popular_symbols:
            try:
                sentiment = MarketSentimentAggregator.get_stock_sentiment(symbol)
                sentiments.append({
                    "symbol": symbol,
                    "sentiment": sentiment["overall_sentiment"],
                    "score": sentiment["sentiment_score"],
                    "label": sentiment["sentiment_label"],
                    "news_count": sentiment["total_news"]
                })
            except:
                continue
        
        # Genel piyasa sentiment'i
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments) if sentiments else 0
        
        positive_count = sum(1 for s in sentiments if s["score"] > 0.1)
        negative_count = sum(1 for s in sentiments if s["score"] < -0.1)
        
        return {
            "market_sentiment_score": round(avg_score, 3),
            "market_sentiment_label": "Olumlu" if avg_score > 0.1 else "Olumsuz" if avg_score < -0.1 else "Nötr",
            "positive_stocks": positive_count,
            "negative_stocks": negative_count,
            "total_analyzed": len(sentiments),
            "stocks": sorted(sentiments, key=lambda x: x["score"], reverse=True),
            "latest_kap": SampleKAPService.get_latest_kap_all(5),
            "latest_news": NewsService.get_market_news(5)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GERÇEK HABER ENDPOINTLERİ ====================

@router.get("/real/stock/{symbol}")
async def get_real_stock_news(
    symbol: str,
    limit: int = Query(15, ge=1, le=50, description="Maksimum haber sayısı")
):
    """
    🔴 GERÇEK HABERLER - Google News'den hisse haberleri
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **limit**: Maksimum haber sayısı (varsayılan: 15)
    """
    try:
        symbol = symbol.upper()
        result = await RealNewsAggregator.get_stock_news(symbol, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/real/market")
async def get_real_market_news():
    """
    🔴 GERÇEK HABERLER - Piyasa geneli haberler
    
    Google News + Finans RSS kaynaklarından
    """
    try:
        result = await RealNewsAggregator.get_market_summary()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/real/sentiment")
async def get_real_multi_sentiment(
    symbols: str = Query("THYAO,SASA,EREGL,ASELS,AKBNK", description="Virgülle ayrılmış semboller")
):
    """
    🔴 GERÇEK HABERLER - Birden fazla hisse sentiment analizi
    
    - **symbols**: Virgülle ayrılmış semboller (örn: THYAO,SASA,EREGL)
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        result = await RealNewsAggregator.get_multiple_stocks_sentiment(symbol_list)
        return {
            "total": len(result),
            "stocks": result,
            "is_real_data": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/real/finance")
async def get_finance_news(
    limit: int = Query(20, ge=1, le=50, description="Maksimum haber sayısı")
):
    """
    🔴 GERÇEK HABERLER - Finans siteleri RSS
    
    Bloomberg HT, Dünya, Ekonomist vb.
    """
    try:
        news = await FinansHaberService.fetch_all_finance_news(limit)
        return {
            "total": len(news),
            "news": news,
            "sources": ["Bloomberg HT", "Dünya", "Ekonomist"],
            "is_real_data": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== YARDIMCI FONKSİYONLAR ====================

def _determine_kap_category(title: str) -> str:
    """KAP bildirim başlığından kategori belirle"""
    title_lower = title.lower()
    if any(w in title_lower for w in ["finansal", "bilanço", "gelir tablosu", "mali tablo"]):
        return "FR"
    elif any(w in title_lower for w in ["özel durum", "açıklama", "bildiri"]):
        return "ODA"
    elif any(w in title_lower for w in ["genel kurul", "toplantı"]):
        return "GENEL_KURUL"
    elif any(w in title_lower for w in ["temettü", "kar payı", "kâr payı", "dağıtım"]):
        return "TEMETTÜ"
    elif any(w in title_lower for w in ["sermaye", "artırım", "bedelli", "bedelsiz"]):
        return "SERMAYE"
    elif any(w in title_lower for w in ["ortaklık", "hisse", "pay devir"]):
        return "ORTAKLIK"
    elif any(w in title_lower for w in ["yönetim", "atama", "görev", "istifa"]):
        return "YONETIM"
    else:
        return "DIGER"
