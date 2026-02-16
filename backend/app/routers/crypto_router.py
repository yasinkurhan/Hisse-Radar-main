"""
Kripto Para Router
===================
borsapy Crypto modülü üzerinden kripto para verileri (BtcTurk)
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/crypto", tags=["Kripto Para"])


@router.get("/current/{pair}")
async def get_crypto_current(pair: str):
    """
    Güncel kripto para fiyatı.
    
    Örnek: /api/crypto/current/BTCTRY, /api/crypto/current/ETHTRY
    """
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_crypto_current(pair.upper())
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"{pair} kripto verisi bulunamadı")
        
        return {
            "pair": pair.upper(),
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{pair}")
async def get_crypto_history(
    pair: str,
    period: str = Query("1ay", description="Periyot: 1g, 5g, 1ay, 3ay, 6ay, 1y")
):
    """
    Kripto para geçmiş verileri.
    """
    try:
        fetcher = get_borsapy_fetcher()
        df = fetcher.get_crypto_history(pair.upper(), period=period)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"{pair} geçmiş verisi bulunamadı")
        
        records = df.reset_index().to_dict(orient="records")
        for r in records:
            for k, v in r.items():
                if hasattr(v, 'isoformat'):
                    r[k] = v.isoformat()
        
        return {
            "pair": pair.upper(),
            "period": period,
            "count": len(records),
            "data": records,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
