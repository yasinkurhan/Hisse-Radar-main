"""
HisseRadar Haber & Sentiment API Router
=======================================
Google News RSS ve diğer ücretsiz kaynaklardan GERÇEK haberler
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.news_sentiment_service import (
    KAPService,
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

router = APIRouter(prefix="/api/news", tags=["news-sentiment"])


@router.get("/kap/{symbol}")
async def get_kap_notifications(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Kaç günlük bildirim")
):
    """
    Hisse için KAP bildirimlerini getir
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **days**: Son kaç günün bildirimleri (varsayılan: 30)
    """
    try:
        symbol = symbol.upper()
        notifications = KAPService.get_kap_notifications(symbol, days)
        
        return {
            "symbol": symbol,
            "total": len(notifications),
            "notifications": notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kap")
async def get_all_kap_notifications(
    limit: int = Query(20, ge=1, le=100, description="Maksimum bildirim sayısı")
):
    """
    Tüm hisseler için son KAP bildirimlerini getir
    """
    try:
        notifications = KAPService.get_latest_kap_all(limit)
        
        return {
            "total": len(notifications),
            "notifications": notifications
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
            "latest_kap": KAPService.get_latest_kap_all(5),
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
