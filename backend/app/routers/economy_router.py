"""
Ekonomi ve Makro Veri Router
==============================
borsapy üzerinden tahvil, enflasyon, TCMB, ekonomik takvim, eurobond
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/economy", tags=["Ekonomi & Makro"])


@router.get("/bonds")
async def get_bonds():
    """
    Devlet tahvili faiz oranları.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_bonds()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Tahvil verileri bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "bonds": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-free-rate")
async def get_risk_free_rate():
    """
    Risksiz faiz oranı (10 yıllık tahvil).
    """
    try:
        fetcher = get_borsapy_fetcher()
        rate = fetcher.get_risk_free_rate()
        
        return {
            "risk_free_rate": rate,
            "description": "10 yıllık devlet tahvili faiz oranı",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inflation")
async def get_inflation():
    """
    Güncel enflasyon verileri (TÜFE, ÜFE).
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_inflation()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Enflasyon verileri bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "inflation": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tcmb")
async def get_tcmb_rates():
    """
    TCMB faiz oranları (politika faizi, gecelik, geç likidite).
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_tcmb_rates()
        
        if result is None:
            raise HTTPException(status_code=404, detail="TCMB verileri bulunamadı")
        
        return {
            "tcmb_rates": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar")
async def get_economic_calendar(
    period: str = Query("1w", description="Periyot: 1d, 1w, 2w, 1m"),
    country: str = Query("TR", description="Ülke kodu: TR, US, EU")
):
    """
    Ekonomik takvim (veri açıklama tarihleri).
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_economic_calendar(period=period, country=country)
        
        if result is None:
            return {"events": [], "count": 0}
        
        if hasattr(result, 'to_dict'):
            records = result.to_dict(orient="records")
            for r in records:
                for k, v in r.items():
                    if hasattr(v, 'isoformat'):
                        r[k] = v.isoformat()
        else:
            records = result if isinstance(result, list) else [result]
        
        return {
            "period": period,
            "country": country,
            "events": records,
            "count": len(records),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eurobonds")
async def get_eurobonds(
    currency: Optional[str] = Query(None, description="Para birimi: USD, EUR")
):
    """
    Türk devlet eurobondları.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_eurobonds(currency=currency)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Eurobond verileri bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "currency": currency,
            "eurobonds": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
