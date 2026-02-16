"""
HisseRadar Teknik Analiz Servisi
=================================
borsapy kütüphanesi ve DataFrame tabanlı teknik gösterge hesaplamaları.
RSI, MACD, Bollinger Bands, MA, EMA, ADX, OBV, Stochastic, ATR, Supertrend

borsapy built-in teknik analiz fonksiyonları:
- Ticker.rsi(), .macd(), .bollinger_bands(), .sma(), .ema()
- Ticker.stochastic(), .atr(), .adx(), .obv(), .vwap(), .supertrend()
- Ticker.technicals(), .history_with_indicators()
- Ticker.ta_signals() → TradingView AL/SAT/TUT sinyalleri
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from .borsapy_fetcher import get_borsapy_fetcher


class TechnicalAnalyzer:
    """
    Teknik analiz göstergelerini hesaplayan sınıf.
    
    İki kullanım modu:
    1. DataFrame tabanlı: TechnicalAnalyzer(df) → geçmiş OHLCV ile hesaplama
    2. borsapy tabanlı: TechnicalAnalyzer(symbol=...) → doğrudan borsapy API ile
    """
    
    def __init__(self, df: pd.DataFrame = None, symbol: str = None):
        """
        TechnicalAnalyzer başlatıcı.
        
        Args:
            df: OHLCV verilerini içeren DataFrame (open, high, low, close, volume)
            symbol: Hisse sembolü (borsapy API ile doğrudan erişim için)
        """
        self.symbol = symbol
        self._fetcher = get_borsapy_fetcher()
        
        if df is not None:
            self.df = df.copy()
            self._validate_dataframe()
        elif symbol:
            # borsapy'den veri çek
            self.df = self._fetcher.get_history(symbol, period="1y", interval="1d")
            if self.df is None:
                self.df = pd.DataFrame()
        else:
            self.df = pd.DataFrame()
    
    def _validate_dataframe(self) -> None:
        """DataFrame'in gerekli sütunları içerdiğini doğrula"""
        if self.df.empty:
            return
        required_columns = ["close"]
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"DataFrame '{col}' sütununu içermelidir")
    
    # ==========================================
    # RSI (Relative Strength Index)
    # ==========================================
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """
        RSI (Göreceli Güç Endeksi) hesapla.
        
        RSI Yorumlama:
        - > 70: Aşırı alım bölgesi (satış sinyali)
        - < 30: Aşırı satım bölgesi (alış sinyali)
        - 50 civarı: Nötr
        """
        if self.df.empty:
            return pd.Series(dtype=float)
        
        delta = self.df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_rsi_signal(self, rsi_value: float) -> str:
        """RSI değerine göre sinyal döndür"""
        if pd.isna(rsi_value):
            return "Veri Yok"
        elif rsi_value >= 70:
            return "Aşırı Alım"
        elif rsi_value <= 30:
            return "Aşırı Satım"
        elif rsi_value >= 50:
            return "Güçlü"
        else:
            return "Zayıf"
    
    # ==========================================
    # MACD (Moving Average Convergence Divergence)
    # ==========================================
    
    def calculate_macd(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        MACD hesapla.
        
        MACD Yorumlama:
        - MACD > Signal: Yükseliş sinyali
        - MACD < Signal: Düşüş sinyali
        - Histogram pozitif: Momentum yukarı
        """
        if self.df.empty:
            empty = pd.Series(dtype=float)
            return {"macd": empty, "signal": empty, "histogram": empty}
        
        ema_fast = self.df["close"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = self.df["close"].ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    # ==========================================
    # Bollinger Bands
    # ==========================================
    
    def calculate_bollinger_bands(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Bollinger Bantları hesapla.
        
        Bollinger Yorumlama:
        - Fiyat üst banda yakın: Potansiyel direnç, aşırı alım
        - Fiyat alt banda yakın: Potansiyel destek, aşırı satım
        - Bantlar daralıyor: Düşük volatilite, breakout beklentisi
        """
        if self.df.empty:
            empty = pd.Series(dtype=float)
            return {"upper": empty, "middle": empty, "lower": empty}
        
        middle = self.df["close"].rolling(window=period).mean()
        std = self.df["close"].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }
    
    # ==========================================
    # Hareketli Ortalamalar (SMA & EMA)
    # ==========================================
    
    def calculate_sma(self, period: int) -> pd.Series:
        """Basit Hareketli Ortalama (SMA) hesapla."""
        if self.df.empty:
            return pd.Series(dtype=float)
        return self.df["close"].rolling(window=period).mean()
    
    def calculate_ema(self, period: int) -> pd.Series:
        """Üssel Hareketli Ortalama (EMA) hesapla."""
        if self.df.empty:
            return pd.Series(dtype=float)
        return self.df["close"].ewm(span=period, adjust=False).mean()
    
    def calculate_all_moving_averages(self) -> Dict[str, pd.Series]:
        """Yaygın kullanılan tüm hareketli ortalamaları hesapla."""
        return {
            "sma_20": self.calculate_sma(20),
            "sma_50": self.calculate_sma(50),
            "sma_200": self.calculate_sma(200),
            "ema_12": self.calculate_ema(12),
            "ema_26": self.calculate_ema(26),
            "ema_50": self.calculate_ema(50)
        }
    
    # ==========================================
    # Stochastic Oscillator
    # ==========================================
    
    def calculate_stochastic(self, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Stochastic K ve D değerlerini hesapla."""
        if self.df.empty or "high" not in self.df.columns or "low" not in self.df.columns:
            empty = pd.Series(dtype=float)
            return {"k": empty, "d": empty}
        
        low_min = self.df["low"].rolling(window=k_period).min()
        high_max = self.df["high"].rolling(window=k_period).max()
        
        k = 100 * (self.df["close"] - low_min) / (high_max - low_min)
        d = k.rolling(window=d_period).mean()
        
        return {"k": k, "d": d}
    
    # ==========================================
    # ATR (Average True Range)
    # ==========================================
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """ATR hesapla."""
        if self.df.empty or "high" not in self.df.columns or "low" not in self.df.columns:
            return pd.Series(dtype=float)
        
        high_low = self.df["high"] - self.df["low"]
        high_close = np.abs(self.df["high"] - self.df["close"].shift())
        low_close = np.abs(self.df["low"] - self.df["close"].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    # ==========================================
    # borsapy TradingView Sinyalleri
    # ==========================================
    
    def get_ta_signals(self, interval: str = "1d") -> Optional[Dict]:
        """
        TradingView teknik analiz sinyalleri (AL/SAT/TUT).
        borsapy'nin ta_signals() API'sini kullanır.
        
        Returns:
            {summary: {recommendation, buy, sell, neutral},
             oscillators: {...}, moving_averages: {...}}
        """
        if not self.symbol:
            return None
        return self._fetcher.get_ta_signals(self.symbol, interval=interval)
    
    def get_ta_signals_all_timeframes(self) -> Optional[Dict]:
        """Tüm timeframe'lerdeki teknik sinyaller"""
        if not self.symbol:
            return None
        return self._fetcher.get_all_ta_signals(self.symbol)
    
    # ==========================================
    # Tüm Göstergeleri Getir
    # ==========================================
    
    def get_all_indicators(self) -> Dict[str, Any]:
        """
        Tüm teknik göstergeleri hesapla ve döndür.
        """
        if self.df.empty:
            return {
                "rsi": [],
                "macd": [],
                "bollinger": [],
                "moving_averages": [],
                "summary": {"current_price": None, "rsi_value": None, "rsi_signal": "Veri Yok", "macd_signal": "Belirsiz", "trend": "Belirsiz"}
            }
        
        # RSI
        rsi = self.calculate_rsi()
        
        # MACD
        macd = self.calculate_macd()
        
        # Bollinger Bands
        bollinger = self.calculate_bollinger_bands()
        
        # Hareketli Ortalamalar
        mas = self.calculate_all_moving_averages()
        
        # Son değerler için özet
        last_close = self.df["close"].iloc[-1] if len(self.df) > 0 else None
        last_rsi = rsi.iloc[-1] if len(rsi) > 0 else None
        
        # borsapy TradingView sinyallerini de ekle
        ta_signals = None
        if self.symbol:
            ta_signals = self.get_ta_signals()
        
        summary = {
            "current_price": last_close,
            "rsi_value": round(last_rsi, 2) if pd.notna(last_rsi) else None,
            "rsi_signal": self.get_rsi_signal(last_rsi),
            "macd_signal": "Yükseliş" if (len(macd["histogram"]) > 0 and pd.notna(macd["histogram"].iloc[-1]) and macd["histogram"].iloc[-1] > 0) else "Düşüş",
            "trend": self._determine_trend(mas),
            "ta_signals": ta_signals  # TradingView AL/SAT/TUT
        }
        
        return {
            "rsi": self._series_to_list(rsi, "rsi"),
            "macd": self._macd_to_list(macd),
            "bollinger": self._bollinger_to_list(bollinger),
            "moving_averages": self._mas_to_list(mas),
            "summary": summary
        }
    
    def _determine_trend(self, mas: Dict[str, pd.Series]) -> str:
        """Trend yönünü belirle"""
        try:
            last_price = self.df["close"].iloc[-1]
            sma_50 = mas["sma_50"].iloc[-1]
            sma_200 = mas["sma_200"].iloc[-1]
            
            if pd.isna(sma_50) or pd.isna(sma_200):
                return "Belirsiz"
            
            if last_price > sma_50 > sma_200:
                return "Güçlü Yükseliş"
            elif last_price > sma_50:
                return "Yükseliş"
            elif last_price < sma_50 < sma_200:
                return "Güçlü Düşüş"
            elif last_price < sma_50:
                return "Düşüş"
            else:
                return "Yatay"
        except:
            return "Belirsiz"
    
    def _series_to_list(self, series: pd.Series, name: str) -> List[Dict[str, Any]]:
        """Series'i listeye çevir"""
        result = []
        for timestamp, value in series.items():
            if pd.notna(value):
                result.append({
                    "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                    "value": round(float(value), 2)
                })
        return result
    
    def _macd_to_list(self, macd: Dict[str, pd.Series]) -> List[Dict[str, Any]]:
        """MACD verilerini listeye çevir"""
        result = []
        for i in range(len(self.df)):
            timestamp = self.df.index[i]
            result.append({
                "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                "macd": round(float(macd["macd"].iloc[i]), 4) if pd.notna(macd["macd"].iloc[i]) else None,
                "signal": round(float(macd["signal"].iloc[i]), 4) if pd.notna(macd["signal"].iloc[i]) else None,
                "histogram": round(float(macd["histogram"].iloc[i]), 4) if pd.notna(macd["histogram"].iloc[i]) else None
            })
        return result
    
    def _bollinger_to_list(self, bb: Dict[str, pd.Series]) -> List[Dict[str, Any]]:
        """Bollinger verilerini listeye çevir"""
        result = []
        for i in range(len(self.df)):
            timestamp = self.df.index[i]
            result.append({
                "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                "upper": round(float(bb["upper"].iloc[i]), 2) if pd.notna(bb["upper"].iloc[i]) else None,
                "middle": round(float(bb["middle"].iloc[i]), 2) if pd.notna(bb["middle"].iloc[i]) else None,
                "lower": round(float(bb["lower"].iloc[i]), 2) if pd.notna(bb["lower"].iloc[i]) else None
            })
        return result
    
    def _mas_to_list(self, mas: Dict[str, pd.Series]) -> List[Dict[str, Any]]:
        """Hareketli ortalama verilerini listeye çevir"""
        result = []
        for i in range(len(self.df)):
            timestamp = self.df.index[i]
            entry = {
                "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
            }
            for key, series in mas.items():
                value = series.iloc[i]
                entry[key] = round(float(value), 2) if pd.notna(value) else None
            result.append(entry)
        return result
