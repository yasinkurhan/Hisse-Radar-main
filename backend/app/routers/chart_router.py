# -*- coding: utf-8 -*-
"""
Chart Router - Grafik ve Görselleştirme Endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.chart_service import chart_service

router = APIRouter(
    prefix="/api/charts",
    tags=["Grafikler"]
)


@router.get("/ohlc/{symbol}")
async def get_ohlc_data(
    symbol: str,
    period: str = Query("3mo", description="Veri periyodu: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1d", description="Veri aralığı: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo")
):
    """
    Mum grafikleri için OHLC (Open, High, Low, Close) verileri
    
    - **symbol**: Hisse sembolü (örn: ASELS)
    - **period**: Veri periyodu (varsayılan: 3mo)
    - **interval**: Veri aralığı (varsayılan: 1d)
    
    Dönen veriler:
    - OHLC verileri (candlestick chart için)
    - RSI, MACD, Bollinger Bands, Moving Averages
    - Hisse bilgileri
    """
    result = chart_service.get_ohlc_data(symbol, period, interval)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Veri bulunamadı"))
    
    return result


@router.get("/sector-heatmap")
async def get_sector_heatmap():
    """
    Sektör bazlı ısı haritası verileri
    
    Her sektör için:
    - Ortalama değişim yüzdesi
    - Sektördeki hisse sayısı
    - En çok değişen hisseler
    """
    result = chart_service.get_sector_heatmap()
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Heatmap verisi alınamadı"))
    
    return result


@router.get("/compare")
async def get_comparison_data(
    symbols: str = Query(..., description="Karşılaştırılacak hisseler (virgülle ayrılmış): ASELS,THYAO,BIMAS"),
    period: str = Query("1y", description="Karşılaştırma periyodu: 1mo, 3mo, 6mo, 1y, 2y, 5y")
):
    """
    Birden fazla hisse için performans karşılaştırması
    
    - **symbols**: Virgülle ayrılmış hisse sembolleri
    - **period**: Karşılaştırma periyodu
    
    Tüm hisseler 100 bazında normalize edilir (ilk gün = 100)
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="En az 2 hisse seçmelisiniz")
    
    if len(symbol_list) > 10:
        raise HTTPException(status_code=400, detail="En fazla 10 hisse karşılaştırabilirsiniz")
    
    result = chart_service.get_comparison_data(symbol_list, period)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Karşılaştırma verisi alınamadı"))
    
    return result


@router.get("/quick-stats/{symbol}")
async def get_quick_stats(symbol: str):
    """
    Hızlı hisse istatistikleri (dashboard için)
    """
    result = chart_service.get_ohlc_data(symbol, period="1mo", interval="1d")
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Veri bulunamadı"))
    
    # Sadece özet bilgileri döndür
    ohlc = result.get("ohlc", [])
    indicators = result.get("indicators", {})
    
    # Son değerler
    last_rsi = None
    if indicators.get("rsi"):
        for item in reversed(indicators["rsi"]):
            if item.get("value") is not None:
                last_rsi = item["value"]
                break
    
    last_macd = None
    if indicators.get("macd", {}).get("histogram"):
        for item in reversed(indicators["macd"]["histogram"]):
            if item.get("value") is not None:
                last_macd = item["value"]
                break
    
    return {
        "success": True,
        "symbol": symbol,
        "info": result.get("info"),
        "stats": {
            "rsi": last_rsi,
            "macdHistogram": last_macd,
            "dataPoints": len(ohlc),
            "period": "1mo"
        }
    }
