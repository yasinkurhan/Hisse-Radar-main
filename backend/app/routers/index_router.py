"""
Endeks Router
==============
borsapy Index modülü üzerinden BIST endeks verileri
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/index", tags=["Endeksler"])


@router.get("/list")
async def get_all_indices():
    """
    Tüm BIST endekslerini listele.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_all_indices()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Endeks listesi bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "indices": result,
            "count": len(result) if isinstance(result, list) else 0,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{index_code}")
async def get_index_info(index_code: str):
    """
    Endeks detay bilgisi.
    
    Örnek: /api/index/XU100, /api/index/XU030, /api/index/XBANK
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_index_info(index_code.upper())
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{index_code} endeks bilgisi bulunamadı")
        
        return {
            "index_code": index_code.upper(),
            "info": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{index_code}/history")
async def get_index_history(
    index_code: str,
    period: str = Query("1ay", description="Periyot: 1g, 5g, 1ay, 3ay, 6ay, 1y")
):
    """
    Endeks geçmiş verileri.
    """
    try:
        fetcher = get_borsapy_fetcher()
        df = fetcher.get_index_history(index_code.upper(), period=period)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"{index_code} geçmiş verisi bulunamadı")
        
        records = df.reset_index().to_dict(orient="records")
        for r in records:
            for k, v in r.items():
                if hasattr(v, 'isoformat'):
                    r[k] = v.isoformat()
        
        return {
            "index_code": index_code.upper(),
            "period": period,
            "count": len(records),
            "data": records,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{index_code}/components")
async def get_index_components(index_code: str):
    """
    Endeks bileşenleri (hisse listesi).
    """
    try:
        fetcher = get_borsapy_fetcher()
        components = fetcher.get_index_components(index_code.upper())
        symbols = fetcher.get_index_component_symbols(index_code.upper())
        
        return {
            "index_code": index_code.upper(),
            "components": components if components else [],
            "symbols": symbols if symbols else [],
            "count": len(symbols) if symbols else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
