"""
Backtest API Router
===================
Gecmis sinyal performansi ve istatistikleri
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..services.smart_scoring import BacktestEngine, MarketConditionAnalyzer
from ..services.yahoo_fetcher import get_yahoo_fetcher
import yfinance as yf

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Servis
backtest_engine = BacktestEngine()


def get_current_prices(symbols: list) -> dict:
    """Sembollerin guncel fiyatlarini al"""
    prices = {}
    fetcher = get_yahoo_fetcher()
    
    for symbol in symbols:
        try:
            # Sembol formatini ayarla
            search_symbol = f"{symbol}.IS" if not symbol.endswith(".IS") else symbol
            
            # Guvenilir olmasi icin 5 gunluk veri iste, sonuncuyu al
            hist = fetcher.get_history(search_symbol, period="5d", interval="1d")
            
            if hist is not None and not hist.empty:
                prices[symbol] = float(hist['Close'].iloc[-1])
            else:
                print(f"Fiyat bulunamadi: {symbol}")
        except Exception as e:
            print(f"Fiyat cekme hatasi {symbol}: {e}")
            continue
    return prices


@router.get("/performance")
async def get_performance():
    """Genel sinyal performans istatistiklerini getir"""
    # Once aktif sinyalleri guncelle
    active_signals = backtest_engine.get_active_signals()
    if active_signals:
        symbols = list(set(s["symbol"] for s in active_signals))
        current_prices = get_current_prices(symbols)
        if current_prices:
            backtest_engine.update_signals(current_prices)
    
    return backtest_engine.get_performance_stats()


@router.get("/active-signals")
async def get_active_signals():
    """Aktif (henuz sonuclanmamis) sinyalleri getir"""
    # Once guncelle
    active_signals = backtest_engine.get_active_signals()
    if active_signals:
        symbols = list(set(s["symbol"] for s in active_signals))
        current_prices = get_current_prices(symbols)
        if current_prices:
            backtest_engine.update_signals(current_prices)
    
    return backtest_engine.get_active_signals()


@router.get("/recent-results")
async def get_recent_results(limit: int = 20):
    """Son sonuclanan sinyalleri getir"""
    return backtest_engine.get_recent_results(limit)


@router.get("/refresh")
async def refresh_signals():
    """Tum aktif sinyalleri manuel olarak guncelle"""
    active_signals = backtest_engine.get_active_signals()
    if not active_signals:
        return {"message": "Aktif sinyal yok", "updated": 0}
    
    symbols = list(set(s["symbol"] for s in active_signals))
    current_prices = get_current_prices(symbols)
    
    if current_prices:
        backtest_engine.update_signals(current_prices)
        return {
            "message": "Sinyaller guncellendi",
            "updated": len(current_prices),
            "symbols": list(current_prices.keys())
        }
    
    return {"message": "Fiyat alinamadi", "updated": 0}


@router.get("/market-condition")
async def get_market_condition():
    """Genel piyasa kosulunu analiz et (BIST100 bazli)"""
    # Default response
    default_response = {
        "condition": "neutral",
        "trend": "Yatay",
        "volatility": "Normal",
        "recommendation": "Piyasa verisi alınamadı, dikkatli olun.",
        "details": {
            "rsi": 50,
            "trend_direction": "neutral",
            "above_sma20": False,
            "above_sma50": False
        }
    }
    
    try:
        import asyncio
        # XU100 (BIST100) verisini al - timeout ile
        xu100 = yf.Ticker("XU100.IS")
        df = xu100.history(period="3mo", interval="1d")
        
        if df.empty:
            return default_response
        
        result = MarketConditionAnalyzer.analyze_market_condition(df)
        return result
    except Exception as e:
        print(f"Market condition hatası: {e}")
        return default_response


class RecordSignalRequest(BaseModel):
    symbol: str
    signal: str
    score: int
    price: float

@router.post("/record-signal")
async def record_signal(request: RecordSignalRequest):
    """Yeni sinyali backtest icin kaydet"""
    backtest_engine.record_signal(
        request.symbol,
        request.signal,
        request.score,
        request.price
    )
    return {"success": True, "message": f"{request.symbol} sinyali kaydedildi"}
