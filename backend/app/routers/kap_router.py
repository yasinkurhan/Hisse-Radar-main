"""
KAP Haber API Router
=====================
KAP haberleri ve günlük haber toplama endpoint'leri
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, List
from datetime import datetime
from ..services.kap_news_service import get_kap_service, get_news_collector

router = APIRouter(prefix="/api/kap", tags=["kap-news"])


@router.get("/news/{symbol}")
async def get_symbol_news(
    symbol: str,
    limit: int = Query(default=50, ge=1, le=200),
    days: int = Query(default=90, ge=1, le=365)
):
    """
    Belirli bir hisse için KAP haberlerini getir
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **limit**: Maksimum haber sayısı
    - **days**: Kaç günlük haber getirilsin
    """
    kap_service = get_kap_service()
    
    # Önce veritabanından kontrol et
    db_news = kap_service.get_news_for_symbol(symbol, limit, days)
    
    # Eğer hiç haber yoksa veya çok eskiyse yeni çek
    if not db_news or len(db_news) < 3:
        try:
            # Yeni haberleri çek
            fresh_news = await kap_service.fetch_kap_news_for_symbol(symbol)
            if fresh_news:
                kap_service.save_news_to_db(fresh_news)
                db_news = kap_service.get_news_for_symbol(symbol, limit, days)
        except Exception as e:
            print(f"Haber çekme hatası: {e}")
    
    # Sentiment özeti hesapla
    if db_news:
        avg_sentiment = sum(n["sentiment_score"] for n in db_news) / len(db_news)
        positive = sum(1 for n in db_news if n["sentiment_label"] == "positive")
        negative = sum(1 for n in db_news if n["sentiment_label"] == "negative")
    else:
        avg_sentiment = 0
        positive = 0
        negative = 0
    
    return {
        "symbol": symbol,
        "total_news": len(db_news),
        "sentiment_score": round(avg_sentiment, 3),
        "positive_news": positive,
        "negative_news": negative,
        "neutral_news": len(db_news) - positive - negative,
        "news": db_news,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


@router.get("/news")
async def get_all_recent_news(
    limit: int = Query(default=50, ge=1, le=200),
    days: int = Query(default=7, ge=1, le=30)
):
    """
    Tüm hisselerin son haberlerini getir
    """
    kap_service = get_kap_service()
    news = kap_service.get_all_recent_news(limit, days)
    
    return {
        "total_news": len(news),
        "days": days,
        "news": news,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


@router.get("/statistics")
async def get_news_statistics():
    """
    Haber istatistikleri
    """
    kap_service = get_kap_service()
    return kap_service.get_news_statistics()


@router.post("/collect")
async def start_news_collection(background_tasks: BackgroundTasks):
    """
    Günlük haber toplama işlemini başlat (arka planda çalışır)
    """
    collector = get_news_collector()
    
    # Arka planda çalıştır
    background_tasks.add_task(collector.run_daily_collection)
    
    return {
        "status": "started",
        "message": "Haber toplama işlemi arka planda başlatıldı",
        "total_symbols": len(collector.all_symbols),
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@router.post("/collect/{symbol}")
async def collect_news_for_symbol(symbol: str):
    """
    Tek bir hisse için haber topla
    """
    kap_service = get_kap_service()
    
    try:
        news = await kap_service.fetch_kap_news_for_symbol(symbol)
        saved = kap_service.save_news_to_db(news)
        
        return {
            "symbol": symbol,
            "status": "success",
            "fetched": len(news),
            "saved": saved,
            "news": news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection-history")
async def get_collection_history(days: int = Query(default=30, ge=1, le=365)):
    """
    Haber toplama geçmişi
    """
    collector = get_news_collector()
    history = collector.get_collection_history(days)
    
    return {
        "total_collections": len(history),
        "history": history
    }


@router.get("/symbols-with-news")
async def get_symbols_with_news():
    """
    Haberi olan hisselerin listesi
    """
    kap_service = get_kap_service()
    stats = kap_service.get_news_statistics()
    
    return {
        "total_symbols": len(stats.get("top_symbols", [])),
        "symbols": stats.get("top_symbols", [])
    }


@router.get("/important")
async def get_important_news(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=30)
):
    """
    Önemli haberleri getir (yüksek öncelikli kategoriler)
    """
    kap_service = get_kap_service()
    all_news = kap_service.get_all_recent_news(limit * 3, days)
    
    # Sadece yüksek önemli haberleri filtrele
    important_news = [
        n for n in all_news 
        if n.get("importance") == "high" or abs(n.get("sentiment_score", 0)) > 0.3
    ]
    
    return {
        "total_news": len(important_news[:limit]),
        "news": important_news[:limit],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


@router.get("/sentiment-summary")
async def get_sentiment_summary(symbols: str = Query(default="", description="Virgülle ayrılmış semboller")):
    """
    Birden fazla hisse için sentiment özeti
    """
    kap_service = get_kap_service()
    
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
    else:
        # Varsayılan olarak en aktif hisseler
        symbol_list = ["THYAO", "SASA", "EREGL", "ASELS", "AKBNK", "GARAN", "YKBNK", "KCHOL"]
    
    results = []
    for symbol in symbol_list:
        news = kap_service.get_news_for_symbol(symbol, limit=10, days=7)
        
        if news:
            avg_sentiment = sum(n["sentiment_score"] for n in news) / len(news)
            latest = news[0]["title"] if news else None
        else:
            avg_sentiment = 0
            latest = None
        
        if avg_sentiment > 0.2:
            label = "📈 Olumlu"
        elif avg_sentiment < -0.2:
            label = "📉 Olumsuz"
        else:
            label = "➖ Nötr"
        
        results.append({
            "symbol": symbol,
            "news_count": len(news),
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": label,
            "latest_headline": latest
        })
    
    # Sentiment'e göre sırala
    results.sort(key=lambda x: x["sentiment_score"], reverse=True)
    
    return {
        "total_symbols": len(results),
        "results": results,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
