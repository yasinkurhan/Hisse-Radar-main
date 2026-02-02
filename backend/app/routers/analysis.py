"""
HisseRadar Analiz Router
=========================
Gunluk ve haftalik analiz API'leri
Haber ve Sentiment Analizi Entegrasyonu ile
"""

from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from datetime import datetime

from ..services.analysis_service import get_analysis_service


router = APIRouter(prefix="/api/analysis", tags=["Analiz"])


@router.post("/daily")
async def run_daily_analysis(
    index_filter: Optional[str] = Query(None, description="Endeks filtresi (BIST30, BIST100, KATILIM)"),
    sector_filter: Optional[str] = Query(None, description="Sektor filtresi"),
    limit: int = Query(50, ge=0, le=600, description="Maksimum oneri sayisi (0=tum hisseler)"),
    include_sentiment: bool = Query(True, description="Haber sentiment analizi dahil edilsin mi")
):
    """
    Gunluk analiz baslat.
    
    BIST hisselerini teknik gostergelerle analiz ederek
    bir sonraki gun icin alim/satim onerileri uretir.
    
    Kullanilan gostergeler:
    - RSI (14 gunluk)
    - MACD (12, 26, 9)
    - Bollinger Bantlari (20 gunluk)
    - Hareketli Ortalamalar (SMA/EMA 5, 10, 20, 50, 200)
    - Stochastic Oscillator (14 gunluk)
    - ATR (14 gunluk)
    - Hacim Analizi
    - Haber Sentiment Analizi (Google News + RSS)
    """
    service = get_analysis_service()
    result = service.run_daily_analysis(
        index_filter=index_filter,
        sector_filter=sector_filter,
        limit=limit,
        include_sentiment=include_sentiment
    )
    return result


@router.post("/weekly")
async def run_weekly_analysis(
    index_filter: Optional[str] = Query(None, description="Endeks filtresi (BIST30, BIST100, KATILIM)"),
    sector_filter: Optional[str] = Query(None, description="Sektor filtresi"),
    limit: int = Query(30, ge=0, le=600, description="Maksimum oneri sayisi (0=tum hisseler)"),
    include_sentiment: bool = Query(True, description="Haber sentiment analizi dahil edilsin mi")
):
    """
    Haftalik analiz baslat.
    
    BIST hisselerini haftalik verilerle analiz ederek
    bir sonraki hafta icin alim/satim onerileri uretir.
    
    Kullanilan gostergeler:
    - RSI (14 haftalik)
    - MACD (12, 26, 9)
    - Bollinger Bantlari (20 haftalik)
    - Hareketli Ortalamalar (SMA/EMA)
    - Stochastic Oscillator
    - ATR
    - Hacim Analizi
    - Haber Sentiment Analizi (Google News + RSS)
    """
    service = get_analysis_service()
    result = service.run_weekly_analysis(
        index_filter=index_filter,
        sector_filter=sector_filter,
        limit=limit,
        include_sentiment=include_sentiment
    )
    return result


@router.get("/indicators")
async def get_indicator_info():
    """
    Kullanilan teknik gostergelerin aciklamalarini dondur.
    """
    return {
        "indicators": [
            {
                "name": "RSI (Relative Strength Index)",
                "description": "Asiri alim/satim durumunu olcer. 30 alti asiri satim (AL sinyali), 70 ustu asiri alim (SAT sinyali).",
                "period": "14 gun/hafta"
            },
            {
                "name": "MACD",
                "description": "Momentum gostergesi. MACD cizgisi sinyal cizgisini yukari keserse AL, asagi keserse SAT.",
                "parameters": "12, 26, 9"
            },
            {
                "name": "Bollinger Bantlari",
                "description": "Fiyat volatilitesini olcer. Alt banda yakin AL, ust banda yakin SAT firsati.",
                "period": "20 gun/hafta, 2 standart sapma"
            },
            {
                "name": "Hareketli Ortalamalar (SMA/EMA)",
                "description": "Trend yonunu belirler. Fiyat ortalamanin ustunde yukari trend, altinda asagi trend.",
                "periods": "5, 10, 20, 50, 200"
            },
            {
                "name": "Stochastic Oscillator",
                "description": "Momentum gostergesi. 20 alti asiri satim, 80 ustu asiri alim.",
                "period": "14 gun/hafta"
            },
            {
                "name": "ATR (Average True Range)",
                "description": "Volatilite gostergesi. Stop loss ve hedef fiyat hesaplamada kullanilir.",
                "period": "14 gun/hafta"
            },
            {
                "name": "Hacim Analizi",
                "description": "Islem hacmini 20 gunluk ortalama ile karsilastirir. Yuksek hacim trendi destekler.",
                "period": "20 gun"
            },
            {
                "name": "Haber Sentiment Analizi",
                "description": "Google News ve finans sitelerinden haber toplayarak duygu analizi yapar. Olumlu haberler skoru arttirir, olumsuz haberler dusurur.",
                "sources": "Google News, Bloomberg HT, Dunya Gazetesi, Ekonomist"
            }
        ],
        "scoring": {
            "description": "Her hisse 0-100 arasi puanlanir",
            "ranges": {
                "70-100": "GUCLU AL - Yuksek potansiyelli firsat",
                "60-69": "AL - Iyi firsat",
                "41-59": "TUT - Notr, bekle",
                "31-40": "SAT - Risk var",
                "0-30": "GUCLU SAT - Yuksek risk"
            },
            "sentiment_impact": "Haber sentiment analizi toplam skora %10-15 etki edebilir"
        }
    }
