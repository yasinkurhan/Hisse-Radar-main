"""
HisseRadar Pro Analiz API Endpoint'leri
========================================
Gelişmiş analiz özellikleri için REST API
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
    Hisse için kapsamlı pro analiz
    
    Içerir:
    - Ichimoku Cloud analizi
    - VWAP ve Volume Profile
    - SuperTrend göstergesi
    - Piyasa rejimi tespiti
    - RSI ve MACD diverjansları
    - Mum formasyonları
    - Grafik formasyonları
    - Risk analizi
    - AI birleşik sinyal
    - Pozisyon önerisi
    """
    service = get_pro_analysis_service()
    result = service.get_pro_analysis(symbol.upper(), period)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/market-overview")
async def get_market_overview():
    """
    Piyasa genel görünümü
    
    Içerir:
    - Piyasa genişliği (A/D analizi)
    - Yükselen/düşen oranları
    - Yeni 52 haftalık yüksek/düşükler
    - MA üzerindeki hisse yüzdeleri
    - Sektör performansları
    - Korku & Açgözlülük endeksi
    - Akıllı para analizi
    """
    service = get_pro_analysis_service()
    return service.get_market_overview()


@router.get("/sector-rotation")
async def get_sector_rotation():
    """
    Sektör rotasyonu analizi
    
    Içerir:
    - Sektör performans sıralaması
    - Öncü ve geciken sektörler
    - Rotasyon fazı (erken/geç genişleme, daralma)
    - Ekonomik döngü tahmini
    - Sektör bazlı strateji önerileri
    """
    service = get_pro_analysis_service()
    return service.get_sector_analysis()


@router.get("/risk-report/{symbol}")
async def get_risk_report(symbol: str):
    """
    Detaylı risk raporu
    
    Içerir:
    - Sharpe Ratio
    - Sortino Ratio
    - Maximum Drawdown
    - Value at Risk (VaR) - %95 ve %99
    - Calmar Ratio
    - Beta analizi
    - Volatilite analizi
    - Getiri dağılımı
    - Risk seviyesi ve öneri
    """
    service = get_pro_analysis_service()
    result = service.get_risk_report(symbol.upper())
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/ichimoku/{symbol}")
async def get_ichimoku_analysis(symbol: str):
    """
    Ichimoku Cloud detaylı analizi
    """
    from ..services.yahoo_fetcher import get_yahoo_fetcher
    from ..services.pro_indicators import IchimokuCloud
    from ..config import BIST_SUFFIX
    
    yf_symbol = f"{symbol.upper()}{BIST_SUFFIX}" if not symbol.upper().endswith(BIST_SUFFIX) else symbol.upper()
    
    fetcher = get_yahoo_fetcher()
    df = fetcher.get_history(yf_symbol, period="6mo", interval="1d")
    
    if df is None or len(df) < 52:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    result = IchimokuCloud.calculate(df["High"], df["Low"], df["Close"])
    result["symbol"] = symbol.upper()
    result["current_price"] = round(float(df["Close"].iloc[-1]), 2)
    
    return result


@router.get("/candlestick/{symbol}")
async def get_candlestick_patterns(symbol: str):
    """
    Mum formasyonları analizi
    """
    from ..services.yahoo_fetcher import get_yahoo_fetcher
    from ..services.candlestick_patterns import CandleAnalyzer
    from ..config import BIST_SUFFIX
    
    yf_symbol = f"{symbol.upper()}{BIST_SUFFIX}" if not symbol.upper().endswith(BIST_SUFFIX) else symbol.upper()
    
    fetcher = get_yahoo_fetcher()
    df = fetcher.get_history(yf_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 10:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    result = CandleAnalyzer.full_analysis(
        df["Open"], df["High"], df["Low"], df["Close"], df["Volume"]
    )
    result["symbol"] = symbol.upper()
    result["current_price"] = round(float(df["Close"].iloc[-1]), 2)
    
    return result


@router.get("/divergence/{symbol}")
async def get_divergence_analysis(symbol: str):
    """
    Diverjans analizi (RSI ve MACD)
    """
    from ..services.yahoo_fetcher import get_yahoo_fetcher
    from ..services.pro_indicators import MomentumDivergence
    from ..config import BIST_SUFFIX
    import pandas as pd
    
    yf_symbol = f"{symbol.upper()}{BIST_SUFFIX}" if not symbol.upper().endswith(BIST_SUFFIX) else symbol.upper()
    
    fetcher = get_yahoo_fetcher()
    df = fetcher.get_history(yf_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 30:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    close = df["Close"]
    
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
    from ..services.yahoo_fetcher import get_yahoo_fetcher
    from ..services.pro_indicators import VWAPAnalysis, VolumeProfile
    from ..config import BIST_SUFFIX
    
    yf_symbol = f"{symbol.upper()}{BIST_SUFFIX}" if not symbol.upper().endswith(BIST_SUFFIX) else symbol.upper()
    
    fetcher = get_yahoo_fetcher()
    df = fetcher.get_history(yf_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 20:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    vwap = VWAPAnalysis.calculate(df["High"], df["Low"], df["Close"], df["Volume"], period=20)
    vol_profile = VolumeProfile.calculate(df["High"], df["Low"], df["Close"], df["Volume"], lookback=50)
    
    return {
        "symbol": symbol.upper(),
        "current_price": round(float(df["Close"].iloc[-1]), 2),
        "vwap": vwap,
        "volume_profile": vol_profile
    }


@router.get("/supertrend/{symbol}")
async def get_supertrend(symbol: str):
    """
    SuperTrend göstergesi
    """
    from ..services.yahoo_fetcher import get_yahoo_fetcher
    from ..services.pro_indicators import SuperTrend
    from ..config import BIST_SUFFIX
    
    yf_symbol = f"{symbol.upper()}{BIST_SUFFIX}" if not symbol.upper().endswith(BIST_SUFFIX) else symbol.upper()
    
    fetcher = get_yahoo_fetcher()
    df = fetcher.get_history(yf_symbol, period="3mo", interval="1d")
    
    if df is None or len(df) < 20:
        raise HTTPException(status_code=400, detail="Yetersiz veri")
    
    result = SuperTrend.calculate(df["High"], df["Low"], df["Close"])
    result["symbol"] = symbol.upper()
    result["current_price"] = round(float(df["Close"].iloc[-1]), 2)
    
    return result


@router.get("/fear-greed")
async def get_fear_greed_index():
    """
    Piyasa Korku & Açgözlülük Endeksi
    
    0-25: Aşırı Korku (Alım fırsatı)
    25-45: Korku
    45-55: Nötr
    55-75: Açgözlülük
    75-100: Aşırı Açgözlülük (Satış düşün)
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
async def compare_stocks(symbols: List[str] = Query(..., description="Karşılaştırılacak hisse sembolleri")):
    """
    Birden fazla hisseyi pro analiz ile karşılaştır
    """
    if len(symbols) > 5:
        raise HTTPException(status_code=400, detail="En fazla 5 hisse karşılaştırılabilir")
    
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
    min_confidence: int = Query(60, description="Minimum güven skoru"),
    limit: int = Query(20, description="Maksimum sonuç sayısı")
):
    """
    Güçlü sinyalleri listele
    
    AI sinyal sisteminin yüksek güvenle ürettiği sinyalleri döndürür
    """
    from ..services.analysis_service import get_analysis_service
    
    analysis_service = get_analysis_service()
    daily_result = analysis_service.run_daily_analysis(limit=0)
    
    pro_service = get_pro_analysis_service()
    strong_signals = []
    
    # En yüksek skorlu hisselerden başla
    top_stocks = daily_result.get("all_results", [])[:50]
    
    for stock in top_stocks:
        try:
            pro_analysis = pro_service.get_pro_analysis(stock["symbol"], "3mo")
            
            if "error" in pro_analysis:
                continue
            
            ai_signal = pro_analysis.get("ai_signal", {})
            confidence = ai_signal.get("confidence", 0)
            signal = ai_signal.get("combined_signal", "NÖTR")
            
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
    
    # Güvene göre sırala
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
    Tüm pro göstergelerin açıklamaları
    """
    return {
        "pro_indicators": [
            {
                "name": "Ichimoku Cloud",
                "description": "Japon teknik analiz sistemi. Trend, momentum ve destek/direnç tek göstergede.",
                "components": [
                    "Tenkan-sen: Dönüşüm çizgisi (9 periyot)",
                    "Kijun-sen: Baz çizgisi (26 periyot)",
                    "Senkou Span A/B: Bulut bantları",
                    "Chikou Span: Gecikme spanı"
                ],
                "signals": {
                    "GÜÇLÜ AL": "Fiyat bulut üstünde, TK kesişimi pozitif, bulut yeşil",
                    "AL": "Fiyat bulut üstünde veya TK pozitif kesişim",
                    "SAT": "Fiyat bulut altında veya TK negatif kesişim",
                    "GÜÇLÜ SAT": "Fiyat bulut altında, TK kesişimi negatif, bulut kırmızı"
                }
            },
            {
                "name": "VWAP",
                "description": "Hacim Ağırlıklı Ortalama Fiyat - Kurumsal alım/satım seviyelerini gösterir",
                "usage": "Fiyat VWAP altında = Alım fırsatı, Fiyat VWAP üstünde = Satış baskısı olabilir"
            },
            {
                "name": "Volume Profile",
                "description": "Fiyat seviyelerindeki hacim dağılımı",
                "components": [
                    "POC: En yüksek hacimli seviye",
                    "Value Area: Hacmin %70'inin olduğu bölge",
                    "HVN: Yüksek hacimli bölgeler (destek/direnç)",
                    "LVN: Düşük hacimli bölgeler (hızlı hareket)"
                ]
            },
            {
                "name": "SuperTrend",
                "description": "ATR tabanlı trend takip göstergesi",
                "usage": "Fiyat SuperTrend üstünde = Yükseliş, altında = Düşüş"
            },
            {
                "name": "Momentum Diverjans",
                "description": "RSI/MACD ve fiyat arasındaki uyumsuzluklar",
                "types": [
                    "Klasik Boğa: Fiyat düşük yapıyor, RSI düşük yapmıyor = AL",
                    "Klasik Ayı: Fiyat yüksek yapıyor, RSI yüksek yapmıyor = SAT",
                    "Gizli Boğa: Yükseliş trendi devam sinyali",
                    "Gizli Ayı: Düşüş trendi devam sinyali"
                ]
            },
            {
                "name": "Mum Formasyonları",
                "description": "Japon mum grafik formasyonları",
                "patterns": [
                    "Doji: Kararsızlık",
                    "Hammer: Dip dönüş",
                    "Shooting Star: Tepe dönüş",
                    "Engulfing: Güçlü dönüş",
                    "Morning/Evening Star: Çok güçlü dönüş",
                    "Three White Soldiers/Black Crows: Trend başlangıcı"
                ]
            }
        ],
        "risk_metrics": [
            {
                "name": "Sharpe Ratio",
                "description": "Risk ayarlı getiri ölçümü",
                "interpretation": "> 1.0: İyi, > 2.0: Çok iyi, > 3.0: Mükemmel"
            },
            {
                "name": "Maximum Drawdown",
                "description": "En yüksek noktadan en düşük noktaya düşüş",
                "interpretation": "< %10: Düşük risk, %10-%20: Orta, > %20: Yüksek risk"
            },
            {
                "name": "Value at Risk (VaR)",
                "description": "Belirli güven düzeyinde maksimum kayıp tahmini",
                "interpretation": "%95 VaR %3 = 95 günde 1 gün %3'ten fazla kayıp olabilir"
            },
            {
                "name": "Beta",
                "description": "Hissenin piyasaya göre duyarlılığı",
                "interpretation": "> 1: Piyasadan volatil, < 1: Piyasadan az volatil"
            }
        ],
        "market_analysis": [
            {
                "name": "Piyasa Genişliği",
                "description": "Yükselen vs düşen hisse analizi",
                "usage": "A/D oranı > 1.5 = Güçlü yükseliş, < 0.67 = Güçlü düşüş"
            },
            {
                "name": "Korku & Açgözlülük Endeksi",
                "description": "Piyasa psikolojisi ölçümü (0-100)",
                "interpretation": "< 25: Aşırı korku (alım fırsatı), > 75: Aşırı açgözlülük (dikkat)"
            },
            {
                "name": "Sektör Rotasyonu",
                "description": "Ekonomik döngüdeki faz ve öne çıkan sektörler"
            }
        ]
    }
