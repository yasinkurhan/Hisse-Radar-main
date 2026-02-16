"""
Yatırım Fonu (TEFAS) Router
==============================
borsapy Fund modülü üzerinden yatırım fonu verileri
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/fund", tags=["Yatırım Fonları"])


@router.get("/info/{code}")
async def get_fund_info(code: str):
    """
    Yatırım fonu detay bilgisi.
    
    Örnek: /api/fund/info/AAK, /api/fund/info/TI2
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_fund_info(code.upper())
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{code} fon bilgisi bulunamadı")
        
        return {
            "fund_code": code.upper(),
            "info": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{code}")
async def get_fund_history(
    code: str,
    period: str = Query("1ay", description="Periyot: 1g, 5g, 1ay, 3ay, 6ay, 1y")
):
    """
    Fon fiyat geçmişi.
    """
    try:
        fetcher = get_borsapy_fetcher()
        df = fetcher.get_fund_history(code.upper(), period=period)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"{code} geçmiş verisi bulunamadı")
        
        records = df.reset_index().to_dict(orient="records")
        for r in records:
            for k, v in r.items():
                if hasattr(v, 'isoformat'):
                    r[k] = v.isoformat()
        
        return {
            "fund_code": code.upper(),
            "period": period,
            "count": len(records),
            "data": records,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocation/{code}")
async def get_fund_allocation(code: str):
    """
    Fon varlık dağılımı.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_fund_allocation(code.upper())
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{code} varlık dağılımı bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "fund_code": code.upper(),
            "allocation": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_funds(q: str = Query(..., description="Fon arama sorgusu")):
    """
    Yatırım fonu arama.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.search_funds(q)
        
        if result is None:
            return {"query": q, "results": [], "count": 0}
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "query": q,
            "results": result if isinstance(result, list) else [result],
            "count": len(result) if isinstance(result, list) else 1,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screen")
async def screen_funds(
    min_return: Optional[float] = Query(None, description="Min getiri (%)"),
    max_risk: Optional[float] = Query(None, description="Max risk"),
    fund_type: Optional[str] = Query(None, description="Fon tipi")
):
    """
    Yatırım fonu tarama.
    """
    try:
        fetcher = get_borsapy_fetcher()
        kwargs = {}
        if min_return is not None:
            kwargs["min_return"] = min_return
        if max_risk is not None:
            kwargs["max_risk"] = max_risk
        if fund_type is not None:
            kwargs["fund_type"] = fund_type
        
        result = fetcher.screen_funds(**kwargs)
        
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
