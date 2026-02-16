"""
Döviz ve Emtia Router
======================
borsapy FX modülü üzerinden döviz kurları, altın fiyatları ve banka kurları
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/fx", tags=["Döviz & Emtia"])


@router.get("/current/{currency}")
async def get_fx_current(currency: str):
    """
    Güncel döviz kuru bilgisi.
    
    Örnek: /api/fx/current/USD, /api/fx/current/EUR, /api/fx/current/GBP
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_fx_current(currency.upper())
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{currency} döviz kuru bulunamadı")
        
        return {
            "currency": currency.upper(),
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{currency}")
async def get_fx_history(
    currency: str,
    period: str = Query("1ay", description="Periyot: 1g, 5g, 1ay, 3ay, 6ay, 1y")
):
    """
    Döviz kuru geçmiş verileri.
    """
    try:
        fetcher = get_borsapy_fetcher()
        df = fetcher.get_fx_history(currency.upper(), period=period)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"{currency} geçmiş verisi bulunamadı")
        
        records = df.reset_index().to_dict(orient="records")
        # datetime nesnelerini string'e çevir
        for r in records:
            for k, v in r.items():
                if hasattr(v, 'isoformat'):
                    r[k] = v.isoformat()
        
        return {
            "currency": currency.upper(),
            "period": period,
            "count": len(records),
            "data": records,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bank-rates/{currency}")
async def get_bank_rates(currency: str):
    """
    Banka döviz alış/satış kurları.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_bank_rates(currency.upper())
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{currency} banka kurları bulunamadı")
        
        # DataFrame ise dict'e çevir
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "currency": currency.upper(),
            "bank_rates": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gold")
async def get_gold_prices(
    gold_type: str = Query("gram-altin", description="gram-altin, ceyrek-altin, yarim-altin, tam-altin, cumhuriyet-altini, ons-altin")
):
    """
    Altın fiyatları.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_gold_price(gold_type)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{gold_type} fiyatı bulunamadı")
        
        return {
            "gold_type": gold_type,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
