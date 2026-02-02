"""
HisseRadar Fiyat Verileri Router
=================================
Fiyat geçmişi ve OHLCV verileri API'leri
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime

from ..services.data_fetcher import get_data_fetcher
from ..config import PERIODS, INTERVALS


router = APIRouter(prefix="/api/price", tags=["Fiyat Verileri"])


@router.get("/periods")
async def get_available_periods():
    """Kullanılabilir zaman dilimlerini listele"""
    return {
        "periods": PERIODS,
        "intervals": INTERVALS
    }


@router.get("/{symbol}")
async def get_price_history(
    symbol: str,
    period: str = Query("1mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı")
):
    """
    Hisse fiyat geçmişini getir.
    """
    if period not in PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz period. Geçerli değerler: {list(PERIODS.keys())}"
        )

    if interval not in INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz interval. Geçerli değerler: {list(INTERVALS.keys())}"
        )

    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)

    # Boş DataFrame için boş liste dön (404 yerine)
    data = []
    if not df.empty:
        for timestamp, row in df.iterrows():
            data.append({
                "timestamp": timestamp.isoformat(),
                "open": round(float(row["open"]), 2) if "open" in row else None,
                "high": round(float(row["high"]), 2) if "high" in row else None,
                "low": round(float(row["low"]), 2) if "low" in row else None,
                "close": round(float(row["close"]), 2) if "close" in row else None,
                "volume": int(row["volume"]) if "volume" in row else None
            })

    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "period_name": PERIODS[period],
        "interval_name": INTERVALS[interval],
        "data": data,
        "total": len(data),
        "currency": "TRY"
    }


@router.get("/{symbol}/latest")
async def get_latest_price(symbol: str):
    """
    Hissenin en güncel fiyat verisini getir.
    """
    fetcher = get_data_fetcher()
    info = fetcher.get_stock_info(symbol.upper())

    return {
        "symbol": symbol.upper(),
        "current_price": info.get("current_price"),
        "previous_close": info.get("previous_close"),
        "open": info.get("open"),
        "day_high": info.get("day_high"),
        "day_low": info.get("day_low"),
        "change": info.get("change"),
        "change_percent": info.get("change_percent"),
        "volume": info.get("volume"),
        "currency": info.get("currency", "TRY"),
        "timestamp": datetime.now().isoformat(),
        "error": info.get("error")
    }


@router.get("/{symbol}/candles")
async def get_candlestick_data(
    symbol: str,
    period: str = Query("3mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı")
):
    """
    TradingView grafikleri için mum grafiği verilerini getir.
    """
    if period not in PERIODS:
        period = "3mo"

    if interval not in INTERVALS:
        interval = "1d"

    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)

    # Boş DataFrame için boş liste dön
    candles = []
    if not df.empty:
        for timestamp, row in df.iterrows():
            time_val = int(timestamp.timestamp())
            candles.append({
                "time": time_val,
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2)
            })

    return {
        "symbol": symbol.upper(),
        "candles": candles
    }


@router.get("/{symbol}/volume")
async def get_volume_data(
    symbol: str,
    period: str = Query("3mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı")
):
    """
    Hacim verilerini getir (TradingView histogram için).
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)

    volumes = []
    if not df.empty:
        for timestamp, row in df.iterrows():
            time_val = int(timestamp.timestamp())
            close = float(row["close"])
            open_price = float(row["open"])
            color = "rgba(38, 166, 154, 0.5)" if close >= open_price else "rgba(239, 83, 80, 0.5)"

            volumes.append({
                "time": time_val,
                "value": int(row["volume"]) if "volume" in row else 0,
                "color": color
            })

    return {
        "symbol": symbol.upper(),
        "volumes": volumes
    }
