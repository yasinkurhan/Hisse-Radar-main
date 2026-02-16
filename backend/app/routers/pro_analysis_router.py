"""
HisseRadar Pro Analiz API Endpoint'leri
========================================
GeliÅŸmiÅŸ analiz Ã¶zellikleri iÃ§in REST API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from ..services.pro_analysis_service import get_pro_analysis_service


router = APIRouter(prefix="/api/pro", tags=["Pro Analiz"])


@router.get("/analysis/{symbol}")
async def get_pro_analysis(
    symbol: str,
    period: str = Query("6mo", description="Veri periyodu (3mo, 6mo, 1y)")
):
    """
    Hisse iÃ§in kapsamlÄ± pro analiz
    
    IÃ§erir:
    - Ichimoku Cloud analizi
    - VWAP ve Volume Profile
    - SuperTrend gÃ¶stergesi
    - Piyasa rejimi tespiti
    - RSI ve MACD diverjanslarÄ±
    - Mum formasyonlarÄ±
    - Grafik formasyonlarÄ±
    - Risk analizi
    - AI birleÅŸik sinyal
    - Pozisyon Ã¶nerisi
    """
    service = get_pro_analysis_service()
    result = service.get_pro_analysis(symbol.upper(), period)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/market-overview")
async def get_market_overview():
    """
    Piyasa genel gÃ¶rÃ¼nÃ¼mÃ¼
    
    IÃ§erir:
    - Piyasa geniÅŸliÄŸi (A/D analizi)
    - YÃ¼kselen/dÃ¼ÅŸen oranlarÄ±
    - Yeni 52 haftalÄ±k yÃ¼ksek/dÃ¼ÅŸÃ¼kler
    - MA Ã¼zerindeki hisse yÃ¼zdeleri
    - SektÃ¶r performanslarÄ±
    - Korku & AÃ§gÃ¶zlÃ¼lÃ¼k endeksi
    - AkÄ±llÄ± para analizi
    """
    service = get_pro_analysis_service()
    return service.get_market_overview()


@router.get("/sector-rotation")
async def get_sector_rotation():
    """
    SektÃ¶r rotasyonu analizi
    
    IÃ§erir:
    - SektÃ¶r performans sÄ±ralamasÄ±
    - Ã–ncÃ¼ ve geciken sektÃ¶rler
    - Rotasyon fazÄ± (erken/geÃ§ geniÅŸleme, daralma)
    - Ekonomik dÃ¶ngÃ¼ tahmini
    - SektÃ¶r bazlÄ± strateji Ã¶nerileri
    """
    service = get_pro_analysis_service()
    return service.get_sector_analysis()


@router.get("/risk-report/{symbol}")
async def get_risk_report(symbol: str):
    """
    DetaylÄ± risk raporu
    
    IÃ§erir:
    - Sharpe Ratio
    - Sortino Ratio
    - Maximum Drawdown
    - Value at Risk (VaR) - %95 ve %99
    - Calmar Ratio
    - Beta analizi
    - Volatilite analizi
    - Getiri daÄŸÄ±lÄ±mÄ±
    - Risk seviyesi ve Ã¶neri
    """
    service = get_pro_analysis_service()
    result = service.get_risk_report(symbol.upper())
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/ichimoku/{symbol}")
async def get_ichimoku_analysis(symbol: str):
    """
    Ichimoku Cloud detaylÄ± analizi
    """
    from ..services.borsapy_fetcher import get_borsapy_fetcher
    from ..services.pro_indicators import IchimokuCloud
    
    
    clean_symbol = symbol.upper().replace(".IS", "")
    
    fetcher = get_borsapy_fetcher()
    df = fetcher.get_history(clean_symbol, period="6mo", interval="1d")
    
    if df is None or len(df) < 52:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    result = IchimokuCloud.calculate(df["high"], df["low"], df["close"])
    result["symbol"] = symbol.upper()
    result["current_price"] = round(float(df["close"].iloc[-1]), 2)
    
    return result


@router.get("/candlestick/{symbol}")
async def get_candlestick_patterns(symbol: str):
    """
    Mum formasyonlarÄ± analizi
    """
    from ..services.borsapy_fetcher import get_borsapy_fetcher
    from ..services.candlestick_patterns import CandleAnalyzer
    
    
    clean_symbol = symbol.upper().replace(".IS", "")
    
    fetcher = get_borsapy_fetcher()
    df = fetcher.get_history(clean_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 10:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    result = CandleAnalyzer.full_analysis(
        df["open"], df["high"], df["low"], df["close"], df["volume"]
    )
    result["symbol"] = symbol.upper()
    result["current_price"] = round(float(df["close"].iloc[-1]), 2)
    
    return result


@router.get("/divergence/{symbol}")
async def get_divergence_analysis(symbol: str):
    """
    Diverjans analizi (RSI ve MACD)
    """
    from ..services.borsapy_fetcher import get_borsapy_fetcher
    from ..services.pro_indicators import MomentumDivergence
    
    import pandas as pd
    
    clean_symbol = symbol.upper().replace(".IS", "")
    
    fetcher = get_borsapy_fetcher()
    df = fetcher.get_history(clean_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 30:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    close = df["close"]
    
    # RSI hesapla
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD hesapla
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_histogram = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    
    rsi_div = MomentumDivergence.detect_rsi_divergence(close, rsi)
    macd_div = MomentumDivergence.detect_macd_divergence(close, macd_histogram)
    
    return {
        "symbol": symbol.upper(),
        "current_price": round(float(close.iloc[-1]), 2),
        "current_rsi": round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else 50,
        "rsi_divergence": rsi_div,
        "macd_divergence": macd_div
    }


@router.get("/vwap/{symbol}")
async def get_vwap_analysis(symbol: str):
    """
    VWAP ve Volume Profile analizi
    """
    from ..services.borsapy_fetcher import get_borsapy_fetcher
    from ..services.pro_indicators import VWAPAnalysis, VolumeProfile
    
    
    clean_symbol = symbol.upper().replace(".IS", "")
    
    fetcher = get_borsapy_fetcher()
    df = fetcher.get_history(clean_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 20:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    vwap = VWAPAnalysis.calculate(df["high"], df["low"], df["close"], df["volume"], period=20)
    vol_profile = VolumeProfile.calculate(df["high"], df["low"], df["close"], df["volume"], lookback=50)
    
    return {
        "symbol": symbol.upper(),
        "current_price": round(float(df["close"].iloc[-1]), 2),
        "vwap": vwap,
        "volume_profile": vol_profile
    }


@router.get("/supertrend/{symbol}")
async def get_supertrend(symbol: str):
    """
    SuperTrend gÃ¶stergesi
    """
    from ..services.borsapy_fetcher import get_borsapy_fetcher
    from ..services.pro_indicators import SuperTrend
    
    
    clean_symbol = symbol.upper().replace(".IS", "")
    
    fetcher = get_borsapy_fetcher()
    df = fetcher.get_history(clean_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 20:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    result = SuperTrend.calculate(df["high"], df["low"], df["close"])
    result["symbol"] = symbol.upper()
    result["current_price"] = round(float(df["close"].iloc[-1]), 2)
    
    return result


@router.get("/fear-greed")
async def get_fear_greed_index():
    """
    Piyasa Korku & AÃ§gÃ¶zlÃ¼lÃ¼k Endeksi
    
    0-25: AÅŸÄ±rÄ± Korku (AlÄ±m fÄ±rsatÄ±)
    25-45: Korku
    45-55: NÃ¶tr
    55-75: AÃ§gÃ¶zlÃ¼lÃ¼k
    75-100: AÅŸÄ±rÄ± AÃ§gÃ¶zlÃ¼lÃ¼k (SatÄ±ÅŸ dÃ¼ÅŸÃ¼n)
    """
    service = get_pro_analysis_service()
    result = service.get_market_overview()
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "fear_greed_index": result.get("sentiment", {}).get("fear_greed_index", 50),
        "sentiment": result.get("sentiment", {}),
        "market_breadth": result.get("market_breadth", {}),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/compare")
async def compare_stocks(symbols: List[str] = Query(..., description="KarÅŸÄ±laÅŸtÄ±rÄ±lacak hisse sembolleri")):
    """
    Birden fazla hisseyi pro analiz ile karÅŸÄ±laÅŸtÄ±r
    """
    if len(symbols) > 5:
        raise HTTPException(status_code=400, detail="En fazla 5 hisse karÅŸÄ±laÅŸtÄ±rÄ±labilir")
    
    service = get_pro_analysis_service()
    results = []
    
    for symbol in symbols:
        analysis = service.get_pro_analysis(symbol.upper(), "3mo")
        if "error" not in analysis:
            results.append({
                "symbol": symbol.upper(),
                "ai_signal": analysis.get("ai_signal", {}),
                "risk_score": analysis.get("risk_analysis", {}).get("risk_score", 50),
                "ichimoku_signal": analysis.get("pro_indicators", {}).get("ichimoku", {}).get("signal", "BEKLE"),
                "supertrend_signal": analysis.get("pro_indicators", {}).get("supertrend", {}).get("signal", "BEKLE"),
                "candlestick_signal": analysis.get("candlestick_analysis", {}).get("overall_signal", "BEKLE")
            })
    
    return {
        "comparison": results,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/signals/strong")
async def get_strong_signals(
    signal_type: str = Query("all", description="'buy', 'sell' veya 'all'"),
    min_confidence: int = Query(60, description="Minimum gÃ¼ven skoru"),
    limit: int = Query(20, description="Maksimum sonuÃ§ sayÄ±sÄ±")
):
    """
    GÃ¼Ã§lÃ¼ sinyalleri listele
    
    AI sinyal sisteminin yÃ¼ksek gÃ¼venle Ã¼rettiÄŸi sinyalleri dÃ¶ndÃ¼rÃ¼r
    """
    from ..services.analysis_service import get_analysis_service
    
    analysis_service = get_analysis_service()
    daily_result = analysis_service.run_daily_analysis(limit=0)
    
    pro_service = get_pro_analysis_service()
    strong_signals = []
    
    # En yÃ¼ksek skorlu hisselerden baÅŸla
    top_stocks = daily_result.get("all_results", [])[:50]
    
    for stock in top_stocks:
        try:
            pro_analysis = pro_service.get_pro_analysis(stock["symbol"], "3mo")
            
            if "error" in pro_analysis:
                continue
            
            ai_signal = pro_analysis.get("ai_signal", {})
            confidence = ai_signal.get("confidence", 0)
            signal = ai_signal.get("combined_signal", "NÃ–TR")
            
            if confidence >= min_confidence:
                if signal_type == "all":
                    should_include = True
                elif signal_type == "buy" and "AL" in signal:
                    should_include = True
                elif signal_type == "sell" and "SAT" in signal:
                    should_include = True
                else:
                    should_include = False
                
                if should_include:
                    strong_signals.append({
                        "symbol": stock["symbol"],
                        "name": stock.get("name", ""),
                        "current_price": stock.get("current_price", 0),
                        "change_percent": stock.get("change_percent", 0),
                        "ai_signal": signal,
                        "confidence": confidence,
                        "score": ai_signal.get("score", 50),
                        "risk_level": pro_analysis.get("risk_analysis", {}).get("risk_level", "orta"),
                        "recommendation": ai_signal.get("recommendation", "")
                    })
            
            if len(strong_signals) >= limit:
                break
                
        except Exception:
            continue
    
    # GÃ¼vene gÃ¶re sÄ±rala
    strong_signals.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "signals": strong_signals[:limit],
        "total_found": len(strong_signals),
        "filter": {
            "signal_type": signal_type,
            "min_confidence": min_confidence
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/indicators-info")
async def get_indicators_info():
    """
    TÃ¼m pro gÃ¶stergelerin aÃ§Ä±klamalarÄ±
    """
    return {
        "pro_indicators": [
            {
                "name": "Ichimoku Cloud",
                "description": "Japon teknik analiz sistemi. Trend, momentum ve destek/direnÃ§ tek gÃ¶stergede.",
                "components": [
                    "Tenkan-sen: DÃ¶nÃ¼ÅŸÃ¼m Ã§izgisi (9 periyot)",
                    "Kijun-sen: Baz Ã§izgisi (26 periyot)",
                    "Senkou Span A/B: Bulut bantlarÄ±",
                    "Chikou Span: Gecikme spanÄ±"
                ],
                "signals": {
                    "GÃœÃ‡LÃœ AL": "Fiyat bulut Ã¼stÃ¼nde, TK kesiÅŸimi pozitif, bulut yeÅŸil",
                    "AL": "Fiyat bulut Ã¼stÃ¼nde veya TK pozitif kesiÅŸim",
                    "SAT": "Fiyat bulut altÄ±nda veya TK negatif kesiÅŸim",
                    "GÃœÃ‡LÃœ SAT": "Fiyat bulut altÄ±nda, TK kesiÅŸimi negatif, bulut kÄ±rmÄ±zÄ±"
                }
            },
            {
                "name": "VWAP",
                "description": "Hacim AÄŸÄ±rlÄ±klÄ± Ortalama Fiyat - Kurumsal alÄ±m/satÄ±m seviyelerini gÃ¶sterir",
                "usage": "Fiyat VWAP altÄ±nda = AlÄ±m fÄ±rsatÄ±, Fiyat VWAP Ã¼stÃ¼nde = SatÄ±ÅŸ baskÄ±sÄ± olabilir"
            },
            {
                "name": "Volume Profile",
                "description": "Fiyat seviyelerindeki hacim daÄŸÄ±lÄ±mÄ±",
                "components": [
                    "POC: En yÃ¼ksek hacimli seviye",
                    "Value Area: Hacmin %70'inin olduÄŸu bÃ¶lge",
                    "HVN: YÃ¼ksek hacimli bÃ¶lgeler (destek/direnÃ§)",
                    "LVN: DÃ¼ÅŸÃ¼k hacimli bÃ¶lgeler (hÄ±zlÄ± hareket)"
                ]
            },
            {
                "name": "SuperTrend",
                "description": "ATR tabanlÄ± trend takip gÃ¶stergesi",
                "usage": "Fiyat SuperTrend Ã¼stÃ¼nde = YÃ¼kseliÅŸ, altÄ±nda = DÃ¼ÅŸÃ¼ÅŸ"
            },
            {
                "name": "Momentum Diverjans",
                "description": "RSI/MACD ve fiyat arasÄ±ndaki uyumsuzluklar",
                "types": [
                    "Klasik BoÄŸa: Fiyat dÃ¼ÅŸÃ¼k yapÄ±yor, RSI dÃ¼ÅŸÃ¼k yapmÄ±yor = AL",
                    "Klasik AyÄ±: Fiyat yÃ¼ksek yapÄ±yor, RSI yÃ¼ksek yapmÄ±yor = SAT",
                    "Gizli BoÄŸa: YÃ¼kseliÅŸ trendi devam sinyali",
                    "Gizli AyÄ±: DÃ¼ÅŸÃ¼ÅŸ trendi devam sinyali"
                ]
            },
            {
                "name": "Mum FormasyonlarÄ±",
                "description": "Japon mum grafik formasyonlarÄ±",
                "patterns": [
                    "Doji: KararsÄ±zlÄ±k",
                    "Hammer: Dip dÃ¶nÃ¼ÅŸ",
                    "Shooting Star: Tepe dÃ¶nÃ¼ÅŸ",
                    "Engulfing: GÃ¼Ã§lÃ¼ dÃ¶nÃ¼ÅŸ",
                    "Morning/Evening Star: Ã‡ok gÃ¼Ã§lÃ¼ dÃ¶nÃ¼ÅŸ",
                    "Three White Soldiers/Black Crows: Trend baÅŸlangÄ±cÄ±"
                ]
            }
        ],
        "risk_metrics": [
            {
                "name": "Sharpe Ratio",
                "description": "Risk ayarlÄ± getiri Ã¶lÃ§Ã¼mÃ¼",
                "interpretation": "> 1.0: Ä°yi, > 2.0: Ã‡ok iyi, > 3.0: MÃ¼kemmel"
            },
            {
                "name": "Maximum Drawdown",
                "description": "En yÃ¼ksek noktadan en dÃ¼ÅŸÃ¼k noktaya dÃ¼ÅŸÃ¼ÅŸ",
                "interpretation": "< %10: DÃ¼ÅŸÃ¼k risk, %10-%20: Orta, > %20: YÃ¼ksek risk"
            },
            {
                "name": "Value at Risk (VaR)",
                "description": "Belirli gÃ¼ven dÃ¼zeyinde maksimum kayÄ±p tahmini",
                "interpretation": "%95 VaR %3 = 95 gÃ¼nde 1 gÃ¼n %3'ten fazla kayÄ±p olabilir"
            },
            {
                "name": "Beta",
                "description": "Hissenin piyasaya gÃ¶re duyarlÄ±lÄ±ÄŸÄ±",
                "interpretation": "> 1: Piyasadan volatil, < 1: Piyasadan az volatil"
            }
        ],
        "market_analysis": [
            {
                "name": "Piyasa GeniÅŸliÄŸi",
                "description": "YÃ¼kselen vs dÃ¼ÅŸen hisse analizi",
                "usage": "A/D oranÄ± > 1.5 = GÃ¼Ã§lÃ¼ yÃ¼kseliÅŸ, < 0.67 = GÃ¼Ã§lÃ¼ dÃ¼ÅŸÃ¼ÅŸ"
            },
            {
                "name": "Korku & AÃ§gÃ¶zlÃ¼lÃ¼k Endeksi",
                "description": "Piyasa psikolojisi Ã¶lÃ§Ã¼mÃ¼ (0-100)",
                "interpretation": "< 25: AÅŸÄ±rÄ± korku (alÄ±m fÄ±rsatÄ±), > 75: AÅŸÄ±rÄ± aÃ§gÃ¶zlÃ¼lÃ¼k (dikkat)"
            },
            {
                "name": "SektÃ¶r Rotasyonu",
                "description": "Ekonomik dÃ¶ngÃ¼deki faz ve Ã¶ne Ã§Ä±kan sektÃ¶rler"
            }
        ]
    }
