"""
Backtest API Router
===================
Gecmis sinyal performansi ve istatistikleri
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.smart_scoring import BacktestEngine, MarketConditionAnalyzer
from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

@router.post("/dynamic")
async def run_dynamic_backtest(request_body: Dict[str, Any] = Body(...)):
    """
    Kullanicinin ReactFlow uzerinden gonderdigi JSON kural setini isler.
    Ornek bir ruleset:
    {
       "symbol": "THYAO",
       "logic_tree": { ... }
    }
    """
    symbol = request_body.get("symbol", "")
    logic_tree = request_body.get("logic_tree", {})
    
    if not symbol or not logic_tree:
        raise HTTPException(status_code=400, detail="Symbol ve logic_tree gereklidir.")
        
    # TODO: Backend engine burada logic_tree'yi parse edip geriye test sonuclari dondurmelidir.
    return {
        "status": "success",
        "symbol": symbol,
        "message": "Dinamik backtest basariyla calistirildi! (Mock Yanit)",
        "results": {
           "total_return": "15%",
           "win_rate": "60%",
           "trade_count": 12
        }
    }

# Servis
backtest_engine = BacktestEngine()


def get_current_prices(symbols: list) -> dict:
    """Sembollerin güncel fiyatlarını al (borsapy ile)"""
    prices = {}
    if not symbols:
        return prices

    fetcher = get_borsapy_fetcher()
    for symbol in symbols:
        try:
            clean_symbol = symbol.replace('.IS', '').upper()
            stock_df = fetcher.get_history(clean_symbol, period="5d", interval="1d")
            if stock_df is None or stock_df.empty:
                continue

            c_col = "close" if "close" in stock_df.columns else "Close"
            if c_col in stock_df.columns:
                prices[symbol] = float(stock_df[c_col].iloc[-1])
        except Exception:
            continue
        
    return prices


@router.get("/performance")
def get_performance():
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
def get_active_signals():
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
def get_recent_results(limit: int = 20):
    """Son sonuclanan sinyalleri getir"""
    return backtest_engine.get_recent_results(limit)


@router.get("/refresh")
def refresh_signals():
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
def get_market_condition():
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
        # borsapy ile XU100 endeks verisi al
        fetcher = get_borsapy_fetcher()
        df = fetcher.get_index_history("XU100", period="3ay")
        
        if df is None or df.empty:
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


@router.get("/symbol-breakdown")
def get_symbol_breakdown():
    """Hisse bazli performans dokumu"""
    return backtest_engine.get_symbol_breakdown()


@router.get("/exit-reasons")
def get_exit_reasons():
    """Cikis sebebine gore analiz"""
    return backtest_engine.get_exit_reason_breakdown()


@router.get("/historical/{symbol}")
def run_historical_backtest(symbol: str, period: str = "1y"):
    """
    Belirli bir hisse icin gecmis veri uzerinde backtest yap.
    Analiz servisinin teknik indikatörlerini kullanarak gercek sinyal uretir.
    """
    from ..services.analysis_service import get_analysis_service

    fetcher = get_borsapy_fetcher()
    clean = symbol.replace(".IS", "").upper()

    period_map = {"3ay": "3ay", "6ay": "6ay", "1y": "1y", "2y": "2y"}
    borsapy_period = period_map.get(period, "1y")

    df = fetcher.get_history(clean, period=borsapy_period, interval="1d")
    if df is None or df.empty or len(df) < 80:
        return {"error": f"{symbol} icin yeterli veri bulunamadi", "rows": len(df) if df is not None else 0}

    # DataFrame sutun adlarini normalize et
    df.columns = [c.lower() for c in df.columns]
    if "close" not in df.columns:
        return {"error": "Fiyat verisi eksik"}

    svc = get_analysis_service()

    def signal_func(data):
        """analysis_service'in teknik analizini kullanarak sinyal uret"""
        if len(data) < 30:
            return "TUT", 50
        close = list(data["close"].astype(float))
        high  = list(data["high"].astype(float))  if "high"  in data.columns else close
        low   = list(data["low"].astype(float))   if "low"   in data.columns else close
        volume = list(data["volume"].astype(float)) if "volume" in data.columns else [0]*len(close)

        ta = svc._calculate_technical_indicators(close, high, low, volume)
        if not ta:
            return "TUT", 50
        score = svc._calculate_score(
            ta.get("rsi", 50), ta.get("macd", {}), ta.get("bollinger", {}),
            ta.get("stochastic", {}), ta.get("moving_averages", {}),
            close[-1], ta.get("volume_analysis", {}),
            weekly_trend=None, relative_strength=None
        )
        signal = "GUCLU_AL" if score >= 70 else "AL" if score >= 55 else \
                 "GUCLU_SAT" if score <= 25 else "SAT" if score <= 38 else "TUT"
        return signal, score

    result = backtest_engine.run_historical_backtest(clean, df, signal_func)
    result["symbol"] = clean
    result["period"] = period
    return result
