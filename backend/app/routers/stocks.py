"""
HisseRadar Hisse Listesi Router
================================
BIST hisse listesi ve arama API'leri
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from ..services.data_fetcher import get_data_fetcher


router = APIRouter(prefix="/api/stocks", tags=["Hisseler"])


@router.get("/")
async def get_stocks(
    sector: Optional[str] = Query(None, description="Sektor filtresi"),
    index: Optional[str] = Query(None, description="Endeks filtresi (BIST30, BIST100, KATILIM)"),
    search: Optional[str] = Query(None, description="Arama sorgusu"),
    limit: int = Query(1000, ge=1, le=1000, description="Maksimum sonuc sayisi")
):
    """
    BIST hisse listesini getir.
    """
    fetcher = get_data_fetcher()

    if search:
        stocks = fetcher.search_stocks(search)
    else:
        stocks = fetcher.get_stock_list(sector=sector, index=index)

    stocks = stocks[:limit]
    sectors = fetcher.get_sectors()
    indexes = fetcher.get_indexes()

    return {
        "stocks": stocks,
        "sectors": sectors,
        "indexes": indexes,
        "total": len(stocks),
        "updated_at": datetime.now().isoformat()
    }


@router.get("/sectors")
async def get_sectors():
    """Tum sektorleri listele"""
    fetcher = get_data_fetcher()
    sectors = fetcher.get_sectors()

    return {
        "sectors": sectors,
        "total": len(sectors)
    }


@router.get("/indexes")
async def get_indexes():
    """Tum endeksleri listele"""
    fetcher = get_data_fetcher()
    indexes = fetcher.get_indexes()

    return {
        "indexes": indexes,
        "total": len(indexes)
    }


@router.get("/{symbol}")
async def get_stock_info(symbol: str):
    """
    Tek bir hissenin detayli bilgilerini getir.
    """
    fetcher = get_data_fetcher()
    info = fetcher.get_stock_info(symbol.upper())

    return info


@router.get("/{symbol}/summary")
async def get_stock_summary(symbol: str):
    """
    Hisse ozet bilgilerini getir.
    """
    fetcher = get_data_fetcher()
    info = fetcher.get_stock_info(symbol.upper())

    return {
        "symbol": info.get("symbol"),
        "name": info.get("name"),
        "current_price": info.get("current_price"),
        "change": info.get("change"),
        "change_percent": info.get("change_percent"),
        "volume": info.get("volume"),
        "market_cap": info.get("market_cap")
    }


@router.post("/batch")
async def get_batch_stocks(symbols: List[str]):
    """
    Birden fazla hissenin bilgilerini toplu getir.
    """
    if len(symbols) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maksimum 20 hisse ayni anda sorgulanabilir"
        )

    fetcher = get_data_fetcher()
    results = fetcher.get_multiple_stocks_info([s.upper() for s in symbols])

    return {
        "stocks": results,
        "total": len(results)
    }
