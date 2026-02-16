"""
Hisse Tarama (Screener) Router
================================
borsapy screen_stocks ve scan modülleri üzerinden hisse tarama
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/screener", tags=["Hisse Tarama"])


@router.get("/stocks")
async def screen_stocks(
    template: Optional[str] = Query(None, description="Şablon: high_dividend, low_pe, high_roe, high_upside, growth, value, momentum"),
    pe_max: Optional[float] = Query(None, description="Maks F/K oranı"),
    pe_min: Optional[float] = Query(None, description="Min F/K oranı"),
    pb_max: Optional[float] = Query(None, description="Maks PD/DD oranı"),
    dividend_yield_min: Optional[float] = Query(None, description="Min temettü verimi (%)"),
    roe_min: Optional[float] = Query(None, description="Min ROE (%)"),
    market_cap_min: Optional[float] = Query(None, description="Min piyasa değeri"),
    market_cap_max: Optional[float] = Query(None, description="Maks piyasa değeri"),
    sector: Optional[str] = Query(None, description="Sektör filtresi"),
    index: Optional[str] = Query(None, description="Endeks filtresi: XU030, XU050, XU100")
):
    """
    BIST hisselerini temel analiz kriterlerine göre tara.
    
    Hazır şablonlar:
    - **high_dividend**: Yüksek temettü veren hisseler
    - **low_pe**: Düşük F/K oranına sahip hisseler
    - **high_roe**: Yüksek ROE'li hisseler
    - **high_upside**: Yüksek yükseliş potansiyelli hisseler
    - **growth**: Büyüme hisseleri
    - **value**: Değer hisseleri
    - **momentum**: Momentum hisseleri
    """
    try:
        fetcher = get_borsapy_fetcher()
        kwargs = {}
        
        if template:
            kwargs["template"] = template
        if pe_max is not None:
            kwargs["pe_max"] = pe_max
        if pe_min is not None:
            kwargs["pe_min"] = pe_min
        if pb_max is not None:
            kwargs["pb_max"] = pb_max
        if dividend_yield_min is not None:
            kwargs["dividend_yield_min"] = dividend_yield_min
        if roe_min is not None:
            kwargs["roe_min"] = roe_min
        if market_cap_min is not None:
            kwargs["market_cap_min"] = market_cap_min
        if market_cap_max is not None:
            kwargs["market_cap_max"] = market_cap_max
        if sector:
            kwargs["sector"] = sector
        if index:
            kwargs["index"] = index
        
        result = fetcher.screen_stocks(**kwargs)
        
        if result is None or (hasattr(result, 'empty') and result.empty):
            return {"filters": kwargs, "results": [], "count": 0}
        
        if hasattr(result, 'to_dict'):
            records = result.to_dict(orient="records")
        else:
            records = result if isinstance(result, list) else [result]
        
        return {
            "filters": kwargs,
            "results": records,
            "count": len(records),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan")
async def scan_stocks(
    index: str = Query("XU100", description="Endeks: XU030, XU050, XU100"),
    condition: str = Query(..., description="Tarama koşulu, ör: 'rsi < 30 and volume > 1000000'"),
    interval: str = Query("1d", description="Zaman aralığı: 1m, 5m, 15m, 30m, 1h, 1d")
):
    """
    Teknik analiz koşullarına göre hisse tarama.
    
    Örnek koşullar:
    - `rsi < 30` - Aşırı satım bölgesindeki hisseler
    - `rsi > 70` - Aşırı alım bölgesindeki hisseler
    - `macd > signal` - MACD yukarı kesişli hisseler
    - `close > sma200` - 200 günlük ortalamanın üstündekiler
    - `volume > 1000000` - Yüksek hacimli hisseler
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.scan_stocks(index=index, condition=condition, interval=interval)
        
        if result is None or (hasattr(result, 'empty') and result.empty):
            return {
                "index": index,
                "condition": condition,
                "interval": interval,
                "results": [],
                "count": 0
            }
        
        if hasattr(result, 'to_dict'):
            records = result.to_dict(orient="records")
        else:
            records = result if isinstance(result, list) else [result]
        
        return {
            "index": index,
            "condition": condition,
            "interval": interval,
            "results": records,
            "count": len(records),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
