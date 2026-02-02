"""
HisseRadar Teknik Analiz Servisi
=================================
RSI, MACD, Bollinger Bands, MA, EMA gibi teknik göstergeleri hesaplar
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    HAS_PANDAS_TA = False
    print("Uyarı: pandas_ta yüklü değil, manuel hesaplama kullanılacak")


class TechnicalAnalyzer:
    """
    Teknik analiz göstergelerini hesaplayan sınıf.
    pandas_ta kütüphanesi varsa kullanır, yoksa manuel hesaplama yapar.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        TechnicalAnalyzer başlatıcı.
        
        Args:
            df: OHLCV verilerini içeren DataFrame (open, high, low, close, volume)
        """
        self.df = df.copy()
        self._validate_dataframe()
    
    def _validate_dataframe(self) -> None:
        """DataFrame'in gerekli sütunları içerdiğini doğrula"""
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
        
        Args:
            period: RSI periyodu (varsayılan: 14)
            
        Returns:
            RSI değerlerini içeren Series
        """
        if HAS_PANDAS_TA:
            return ta.rsi(self.df["close"], length=period)
        
        # Manuel RSI hesaplama
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
        - Histogram negatif: Momentum aşağı
        
        Args:
            fast_period: Hızlı EMA periyodu (varsayılan: 12)
            slow_period: Yavaş EMA periyodu (varsayılan: 26)
            signal_period: Sinyal çizgisi periyodu (varsayılan: 9)
            
        Returns:
            MACD, Signal ve Histogram değerlerini içeren dictionary
        """
        if HAS_PANDAS_TA:
            macd_df = ta.macd(
                self.df["close"],
                fast=fast_period,
                slow=slow_period,
                signal=signal_period
            )
            return {
                "macd": macd_df.iloc[:, 0],
                "signal": macd_df.iloc[:, 1],
                "histogram": macd_df.iloc[:, 2]
            }
        
        # Manuel MACD hesaplama
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
        - Bantlar genişliyor: Yüksek volatilite
        
        Args:
            period: SMA periyodu (varsayılan: 20)
            std_dev: Standart sapma çarpanı (varsayılan: 2)
            
        Returns:
            Upper, Middle, Lower bantları içeren dictionary
        """
        if HAS_PANDAS_TA:
            bb_df = ta.bbands(self.df["close"], length=period, std=std_dev)
            return {
                "upper": bb_df.iloc[:, 2],
                "middle": bb_df.iloc[:, 1],
                "lower": bb_df.iloc[:, 0]
            }
        
        # Manuel Bollinger hesaplama
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
        """
        Basit Hareketli Ortalama (SMA) hesapla.
        
        Args:
            period: SMA periyodu
            
        Returns:
            SMA değerlerini içeren Series
        """
        if HAS_PANDAS_TA:
            return ta.sma(self.df["close"], length=period)
        
        return self.df["close"].rolling(window=period).mean()
    
    def calculate_ema(self, period: int) -> pd.Series:
        """
        Üssel Hareketli Ortalama (EMA) hesapla.
        
        Args:
            period: EMA periyodu
            
        Returns:
            EMA değerlerini içeren Series
        """
        if HAS_PANDAS_TA:
            return ta.ema(self.df["close"], length=period)
        
        return self.df["close"].ewm(span=period, adjust=False).mean()
    
    def calculate_all_moving_averages(self) -> Dict[str, pd.Series]:
        """
        Yaygın kullanılan tüm hareketli ortalamaları hesapla.
        
        Returns:
            Tüm MA değerlerini içeren dictionary
        """
        return {
            "sma_20": self.calculate_sma(20),
            "sma_50": self.calculate_sma(50),
            "sma_200": self.calculate_sma(200),
            "ema_12": self.calculate_ema(12),
            "ema_26": self.calculate_ema(26),
            "ema_50": self.calculate_ema(50)
        }
    
    # ==========================================
    # Tüm Göstergeleri Getir
    # ==========================================
    
    def get_all_indicators(self) -> Dict[str, Any]:
        """
        Tüm teknik göstergeleri hesapla ve döndür.
        
        Returns:
            Tüm göstergeleri içeren dictionary
        """
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
        
        summary = {
            "current_price": last_close,
            "rsi_value": round(last_rsi, 2) if pd.notna(last_rsi) else None,
            "rsi_signal": self.get_rsi_signal(last_rsi),
            "macd_signal": "Yükseliş" if macd["histogram"].iloc[-1] > 0 else "Düşüş",
            "trend": self._determine_trend(mas)
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
