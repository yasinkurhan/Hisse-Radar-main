"""
HisseRadar Teknik Analiz Router
================================
RSI, MACD, Bollinger Bands, MA, EMA API'leri
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from ..services.data_fetcher import get_data_fetcher
from ..services.technical_analysis import TechnicalAnalyzer
from ..config import PERIODS, INTERVALS


router = APIRouter(prefix="/api/technical", tags=["Teknik Analiz"])


@router.get("/{symbol}")
async def get_technical_indicators(
    symbol: str,
    period: str = Query("6mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı")
):
    """
    Tüm teknik göstergeleri getir.
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **period**: Zaman dilimi (varsayılan: 6mo)
    - **interval**: Veri aralığı (varsayılan: 1d)
    
    Dönen göstergeler:
    - RSI (14 periyot)
    - MACD (12, 26, 9)
    - Bollinger Bands (20, 2)
    - SMA (20, 50, 200)
    - EMA (12, 26, 50)
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} için veri bulunamadı"
        )
    
    # Teknik analiz yap
    analyzer = TechnicalAnalyzer(df)
    indicators = analyzer.get_all_indicators()
    
    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        **indicators
    }


@router.get("/{symbol}/rsi")
async def get_rsi(
    symbol: str,
    period: str = Query("6mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı"),
    rsi_period: int = Query(14, ge=2, le=50, description="RSI periyodu")
):
    """
    RSI (Relative Strength Index) göstergesini getir.
    
    RSI Yorumlama:
    - > 70: Aşırı alım bölgesi (satış sinyali olabilir)
    - < 30: Aşırı satım bölgesi (alış sinyali olabilir)
    - 50 civarı: Nötr bölge
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} için veri bulunamadı"
        )
    
    analyzer = TechnicalAnalyzer(df)
    rsi = analyzer.calculate_rsi(period=rsi_period)
    
    # Listeye çevir
    data = []
    for timestamp, value in rsi.items():
        if value is not None and not (isinstance(value, float) and value != value):  # NaN check
            data.append({
                "time": int(timestamp.timestamp()),
                "value": round(float(value), 2)
            })
    
    # Son değer ve sinyal
    last_value = rsi.iloc[-1] if len(rsi) > 0 else None
    signal = analyzer.get_rsi_signal(last_value)
    
    return {
        "symbol": symbol.upper(),
        "indicator": "RSI",
        "period": rsi_period,
        "current_value": round(float(last_value), 2) if last_value else None,
        "signal": signal,
        "data": data,
        "interpretation": {
            "overbought": 70,
            "oversold": 30,
            "neutral": 50
        }
    }


@router.get("/{symbol}/macd")
async def get_macd(
    symbol: str,
    period: str = Query("6mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı"),
    fast_period: int = Query(12, ge=2, le=50, description="Hızlı EMA periyodu"),
    slow_period: int = Query(26, ge=2, le=100, description="Yavaş EMA periyodu"),
    signal_period: int = Query(9, ge=2, le=50, description="Sinyal periyodu")
):
    """
    MACD (Moving Average Convergence Divergence) göstergesini getir.
    
    MACD Yorumlama:
    - MACD çizgisi sinyal çizgisini yukarı keserse: Alış sinyali
    - MACD çizgisi sinyal çizgisini aşağı keserse: Satış sinyali
    - Histogram pozitif: Yukarı momentum
    - Histogram negatif: Aşağı momentum
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} için veri bulunamadı"
        )
    
    analyzer = TechnicalAnalyzer(df)
    macd = analyzer.calculate_macd(
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period
    )
    
    # Listeye çevir
    data = []
    for i, timestamp in enumerate(df.index):
        macd_val = macd["macd"].iloc[i]
        signal_val = macd["signal"].iloc[i]
        hist_val = macd["histogram"].iloc[i]
        
        if macd_val is not None and not (isinstance(macd_val, float) and macd_val != macd_val):
            data.append({
                "time": int(timestamp.timestamp()),
                "macd": round(float(macd_val), 4),
                "signal": round(float(signal_val), 4) if signal_val == signal_val else None,
                "histogram": round(float(hist_val), 4) if hist_val == hist_val else None
            })
    
    # Sinyal belirleme
    last_hist = macd["histogram"].iloc[-1] if len(macd["histogram"]) > 0 else 0
    signal = "Yükseliş" if last_hist > 0 else "Düşüş"
    
    return {
        "symbol": symbol.upper(),
        "indicator": "MACD",
        "settings": {
            "fast": fast_period,
            "slow": slow_period,
            "signal": signal_period
        },
        "current_signal": signal,
        "data": data
    }


@router.get("/{symbol}/bollinger")
async def get_bollinger_bands(
    symbol: str,
    period: str = Query("6mo", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı"),
    bb_period: int = Query(20, ge=5, le=50, description="Bollinger periyodu"),
    std_dev: float = Query(2.0, ge=0.5, le=4.0, description="Standart sapma çarpanı")
):
    """
    Bollinger Bands göstergesini getir.
    
    Bollinger Yorumlama:
    - Fiyat üst banda dokunursa: Potansiyel direnç, aşırı alım
    - Fiyat alt banda dokunursa: Potansiyel destek, aşırı satım
    - Bantlar daralırsa: Volatilite düşük, breakout beklentisi
    - Bantlar genişlerse: Yüksek volatilite
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} için veri bulunamadı"
        )
    
    analyzer = TechnicalAnalyzer(df)
    bb = analyzer.calculate_bollinger_bands(period=bb_period, std_dev=std_dev)
    
    # Listeye çevir
    data = []
    for i, timestamp in enumerate(df.index):
        upper = bb["upper"].iloc[i]
        middle = bb["middle"].iloc[i]
        lower = bb["lower"].iloc[i]
        
        if upper == upper:  # NaN check
            data.append({
                "time": int(timestamp.timestamp()),
                "upper": round(float(upper), 2),
                "middle": round(float(middle), 2),
                "lower": round(float(lower), 2)
            })
    
    # Mevcut pozisyon
    last_close = df["close"].iloc[-1]
    last_upper = bb["upper"].iloc[-1]
    last_lower = bb["lower"].iloc[-1]
    
    if last_close >= last_upper:
        position = "Üst Bant Üzerinde"
    elif last_close <= last_lower:
        position = "Alt Bant Altında"
    else:
        position = "Bantlar Arasında"
    
    return {
        "symbol": symbol.upper(),
        "indicator": "Bollinger Bands",
        "settings": {
            "period": bb_period,
            "std_dev": std_dev
        },
        "current_position": position,
        "data": data
    }


@router.get("/{symbol}/ma")
async def get_moving_averages(
    symbol: str,
    period: str = Query("1y", description="Zaman dilimi"),
    interval: str = Query("1d", description="Veri aralığı")
):
    """
    Hareketli ortalamaları getir (SMA ve EMA).
    
    Hareketli Ortalama Yorumlama:
    - Fiyat > SMA50 > SMA200: Güçlü yükseliş trendi
    - Fiyat < SMA50 < SMA200: Güçlü düşüş trendi
    - Golden Cross (SMA50 > SMA200): Uzun vadeli alış sinyali
    - Death Cross (SMA50 < SMA200): Uzun vadeli satış sinyali
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval=interval)
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} için veri bulunamadı"
        )
    
    analyzer = TechnicalAnalyzer(df)
    mas = analyzer.calculate_all_moving_averages()
    
    # Listeye çevir
    data = []
    for i, timestamp in enumerate(df.index):
        entry = {"time": int(timestamp.timestamp())}
        
        for key, series in mas.items():
            value = series.iloc[i]
            if value == value:  # NaN check
                entry[key] = round(float(value), 2)
            else:
                entry[key] = None
        
        data.append(entry)
    
    # Trend analizi
    trend = analyzer._determine_trend(mas)
    
    # Son değerler
    current = {}
    for key, series in mas.items():
        last_val = series.iloc[-1]
        if last_val == last_val:
            current[key] = round(float(last_val), 2)
    
    return {
        "symbol": symbol.upper(),
        "indicator": "Moving Averages",
        "trend": trend,
        "current_values": current,
        "data": data
    }


@router.get("/{symbol}/summary")
async def get_technical_summary(
    symbol: str,
    period: str = Query("6mo", description="Zaman dilimi")
):
    """
    Teknik analiz özet raporu.
    
    Tüm göstergelerin son değerlerini ve sinyallerini içerir.
    """
    fetcher = get_data_fetcher()
    df = fetcher.get_price_history(symbol.upper(), period=period, interval="1d")
    
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"{symbol} için veri bulunamadı"
        )
    
    analyzer = TechnicalAnalyzer(df)
    
    # RSI
    rsi = analyzer.calculate_rsi()
    last_rsi = rsi.iloc[-1] if len(rsi) > 0 else None
    
    # MACD
    macd = analyzer.calculate_macd()
    last_macd_hist = macd["histogram"].iloc[-1] if len(macd["histogram"]) > 0 else 0
    
    # Bollinger
    bb = analyzer.calculate_bollinger_bands()
    last_close = df["close"].iloc[-1]
    last_upper = bb["upper"].iloc[-1]
    last_lower = bb["lower"].iloc[-1]
    last_middle = bb["middle"].iloc[-1]
    
    # MA
    mas = analyzer.calculate_all_moving_averages()
    trend = analyzer._determine_trend(mas)
    
    # Sinyaller
    signals = []
    
    # RSI sinyali
    if last_rsi and last_rsi > 70:
        signals.append({"indicator": "RSI", "signal": "Satış", "reason": "Aşırı alım bölgesi"})
    elif last_rsi and last_rsi < 30:
        signals.append({"indicator": "RSI", "signal": "Alış", "reason": "Aşırı satım bölgesi"})
    else:
        signals.append({"indicator": "RSI", "signal": "Nötr", "reason": "Normal bölge"})
    
    # MACD sinyali
    if last_macd_hist > 0:
        signals.append({"indicator": "MACD", "signal": "Alış", "reason": "Pozitif momentum"})
    else:
        signals.append({"indicator": "MACD", "signal": "Satış", "reason": "Negatif momentum"})
    
    # Bollinger sinyali
    if last_close >= last_upper:
        signals.append({"indicator": "Bollinger", "signal": "Satış", "reason": "Üst banda temas"})
    elif last_close <= last_lower:
        signals.append({"indicator": "Bollinger", "signal": "Alış", "reason": "Alt banda temas"})
    else:
        signals.append({"indicator": "Bollinger", "signal": "Nötr", "reason": "Bantlar arasında"})
    
    # Trend sinyali
    if "Yükseliş" in trend:
        signals.append({"indicator": "Trend", "signal": "Alış", "reason": trend})
    elif "Düşüş" in trend:
        signals.append({"indicator": "Trend", "signal": "Satış", "reason": trend})
    else:
        signals.append({"indicator": "Trend", "signal": "Nötr", "reason": trend})
    
    # Genel değerlendirme
    buy_signals = sum(1 for s in signals if s["signal"] == "Alış")
    sell_signals = sum(1 for s in signals if s["signal"] == "Satış")
    
    if buy_signals > sell_signals:
        overall = "Alış"
    elif sell_signals > buy_signals:
        overall = "Satış"
    else:
        overall = "Nötr"
    
    return {
        "symbol": symbol.upper(),
        "current_price": round(float(last_close), 2),
        "indicators": {
            "rsi": {
                "value": round(float(last_rsi), 2) if last_rsi else None,
                "signal": analyzer.get_rsi_signal(last_rsi)
            },
            "macd": {
                "histogram": round(float(last_macd_hist), 4) if last_macd_hist else None,
                "signal": "Yükseliş" if last_macd_hist > 0 else "Düşüş"
            },
            "bollinger": {
                "upper": round(float(last_upper), 2),
                "middle": round(float(last_middle), 2),
                "lower": round(float(last_lower), 2),
                "position": "Üst" if last_close >= last_upper else ("Alt" if last_close <= last_lower else "Orta")
            },
            "trend": trend
        },
        "signals": signals,
        "overall_signal": overall,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "neutral_signals": len(signals) - buy_signals - sell_signals
    }
