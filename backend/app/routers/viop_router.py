"""
VIOP (Vadeli İşlem ve Opsiyon) Router
========================================
borsapy VIOP modülü üzerinden vadeli işlem ve opsiyon verileri
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/viop", tags=["VIOP"])


@router.get("/futures")
async def get_viop_futures():
    """
    VIOP vadeli işlem kontratları.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_viop_futures()
        
        if result is None:
            raise HTTPException(status_code=404, detail="VIOP vadeli işlem verisi bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "futures": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options")
async def get_viop_options():
    """
    VIOP opsiyon kontratları.
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_viop_options()
        
        if result is None:
            raise HTTPException(status_code=404, detail="VIOP opsiyon verisi bulunamadı")
        
        if hasattr(result, 'to_dict'):
            result = result.to_dict(orient="records")
        
        return {
            "options": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
