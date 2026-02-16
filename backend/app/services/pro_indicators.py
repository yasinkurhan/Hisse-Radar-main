"""
HisseRadar Pro Göstergeler Modülü
==================================
Ichimoku, VWAP, Volume Profile, Momentum Diverjans ve daha fazlası
Profesyonel seviye teknik analiz araçları
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy.signal import argrelextrema
from scipy.stats import linregress


class IchimokuCloud:
    """
    Ichimoku Kinko Hyo (Bir Bakışta Denge Tablosu)
    ================================================
    Japon teknik analiz sistemi - Trend, momentum, destek/direnç tek göstergede
    
    Bileşenler:
    - Tenkan-sen (Dönüşüm Çizgisi): 9 periyot (High+Low)/2
    - Kijun-sen (Baz Çizgisi): 26 periyot (High+Low)/2
    - Senkou Span A (Öncü Span A): (Tenkan + Kijun)/2, 26 periyot ileri
    - Senkou Span B (Öncü Span B): 52 periyot (High+Low)/2, 26 periyot ileri
    - Chikou Span (Gecikme Spanı): Kapanış, 26 periyot geri
    """
    
    @staticmethod
    def calculate(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ) -> Dict[str, Any]:
        """
        Ichimoku göstergelerini hesapla
        
        Args:
            high: Yüksek fiyat serisi
            low: Düşük fiyat serisi
            close: Kapanış fiyat serisi
            tenkan_period: Tenkan-sen periyodu (varsayılan: 9)
            kijun_period: Kijun-sen periyodu (varsayılan: 26)
            senkou_b_period: Senkou Span B periyodu (varsayılan: 52)
            displacement: Bulut öteleme (varsayılan: 26)
            
        Returns:
            Ichimoku değerlerini ve sinyallerini içeren dictionary
        """
        if len(close) < senkou_b_period + displacement:
            return {
                "tenkan_sen": None,
                "kijun_sen": None,
                "senkou_span_a": None,
                "senkou_span_b": None,
                "chikou_span": None,
                "cloud_color": "neutral",
                "signal": "BEKLE",
                "trend": "belirsiz",
                "strength": 0
            }
        
        # Tenkan-sen (Dönüşüm Çizgisi)
        tenkan_high = high.rolling(window=tenkan_period).max()
        tenkan_low = low.rolling(window=tenkan_period).min()
        tenkan_sen = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Baz Çizgisi)
        kijun_high = high.rolling(window=kijun_period).max()
        kijun_low = low.rolling(window=kijun_period).min()
        kijun_sen = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Öncü Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        
        # Senkou Span B (Öncü Span B)
        senkou_high = high.rolling(window=senkou_b_period).max()
        senkou_low = low.rolling(window=senkou_b_period).min()
        senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)
        
        # Chikou Span (Gecikme Spanı)
        chikou_span = close.shift(-displacement)
        
        # Güncel değerler
        current_price = float(close.iloc[-1])
        current_tenkan = float(tenkan_sen.iloc[-1]) if not pd.isna(tenkan_sen.iloc[-1]) else current_price
        current_kijun = float(kijun_sen.iloc[-1]) if not pd.isna(kijun_sen.iloc[-1]) else current_price
        current_span_a = float(senkou_span_a.iloc[-1]) if not pd.isna(senkou_span_a.iloc[-1]) else current_price
        current_span_b = float(senkou_span_b.iloc[-1]) if not pd.isna(senkou_span_b.iloc[-1]) else current_price
        
        # Bulut rengi (yeşil = yükseliş, kırmızı = düşüş)
        cloud_color = "green" if current_span_a > current_span_b else "red"
        cloud_top = max(current_span_a, current_span_b)
        cloud_bottom = min(current_span_a, current_span_b)
        
        # Sinyal analizi
        signal, trend, strength = IchimokuCloud._analyze_signals(
            current_price, current_tenkan, current_kijun,
            current_span_a, current_span_b, cloud_top, cloud_bottom,
            tenkan_sen, kijun_sen
        )
        
        # Bulut kalınlığı (trend gücü göstergesi)
        cloud_thickness = abs(current_span_a - current_span_b)
        cloud_thickness_pct = (cloud_thickness / current_price) * 100
        
        return {
            "tenkan_sen": round(current_tenkan, 2),
            "kijun_sen": round(current_kijun, 2),
            "senkou_span_a": round(current_span_a, 2),
            "senkou_span_b": round(current_span_b, 2),
            "chikou_span": round(float(close.iloc[-1]), 2),
            "cloud_top": round(cloud_top, 2),
            "cloud_bottom": round(cloud_bottom, 2),
            "cloud_color": cloud_color,
            "cloud_thickness_pct": round(cloud_thickness_pct, 2),
            "signal": signal,
            "trend": trend,
            "strength": strength,
            "price_vs_cloud": "above" if current_price > cloud_top else ("below" if current_price < cloud_bottom else "inside"),
            "tk_cross": "bullish" if current_tenkan > current_kijun else "bearish"
        }
    
    @staticmethod
    def _analyze_signals(
        price: float, tenkan: float, kijun: float,
        span_a: float, span_b: float, cloud_top: float, cloud_bottom: float,
        tenkan_series: pd.Series, kijun_series: pd.Series
    ) -> Tuple[str, str, int]:
        """Ichimoku sinyallerini analiz et"""
        
        strength = 0
        signals = []
        
        # 1. Fiyat-Bulut ilişkisi
        if price > cloud_top:
            strength += 20
            signals.append("bullish_cloud")
        elif price < cloud_bottom:
            strength -= 20
            signals.append("bearish_cloud")
        
        # 2. Tenkan-Kijun kesişimi
        if tenkan > kijun:
            strength += 15
            # Altın kesişim kontrolü (son 5 mum)
            if len(tenkan_series) > 5 and len(kijun_series) > 5:
                if tenkan_series.iloc[-5] < kijun_series.iloc[-5]:
                    strength += 10  # Yeni kesişim bonus
                    signals.append("golden_cross")
        else:
            strength -= 15
            if len(tenkan_series) > 5 and len(kijun_series) > 5:
                if tenkan_series.iloc[-5] > kijun_series.iloc[-5]:
                    strength -= 10
                    signals.append("death_cross")
        
        # 3. Fiyat-Kijun ilişkisi
        if price > kijun:
            strength += 10
        else:
            strength -= 10
        
        # 4. Bulut rengi (gelecek trend)
        if span_a > span_b:
            strength += 10
        else:
            strength -= 10
        
        # Sinyal belirleme
        if strength >= 40:
            signal = "GÜÇLÜ AL"
            trend = "güçlü_yükseliş"
        elif strength >= 20:
            signal = "AL"
            trend = "yükseliş"
        elif strength <= -40:
            signal = "GÜÇLÜ SAT"
            trend = "güçlü_düşüş"
        elif strength <= -20:
            signal = "SAT"
            trend = "düşüş"
        else:
            signal = "BEKLE"
            trend = "yatay"
        
        return signal, trend, max(-100, min(100, strength))


class VWAPAnalysis:
    """
    VWAP (Volume Weighted Average Price) Analizi
    =============================================
    Hacim ağırlıklı ortalama fiyat - Kurumsal alım/satım seviyelerini gösterir
    """
    
    @staticmethod
    def calculate(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = None
    ) -> Dict[str, Any]:
        """
        VWAP ve bantlarını hesapla
        
        Args:
            high, low, close: Fiyat serileri
            volume: Hacim serisi
            period: Hesaplama periyodu (None = tüm veri)
            
        Returns:
            VWAP değerleri ve sinyalleri
        """
        if len(close) < 20:
            return {
                "vwap": None,
                "upper_band_1": None,
                "lower_band_1": None,
                "signal": "BEKLE",
                "deviation_pct": 0
            }
        
        # Tipik fiyat
        typical_price = (high + low + close) / 3
        
        # VWAP hesaplama
        if period:
            tp_vol = (typical_price * volume).rolling(window=period).sum()
            vol_sum = volume.rolling(window=period).sum()
        else:
            tp_vol = (typical_price * volume).cumsum()
            vol_sum = volume.cumsum()
        
        vwap = tp_vol / vol_sum
        
        # VWAP Standart Sapma bantları
        squared_diff = ((typical_price - vwap) ** 2 * volume)
        if period:
            variance = squared_diff.rolling(window=period).sum() / vol_sum
        else:
            variance = squared_diff.cumsum() / vol_sum
        
        std_dev = np.sqrt(variance)
        
        current_vwap = float(vwap.iloc[-1])
        current_std = float(std_dev.iloc[-1]) if not pd.isna(std_dev.iloc[-1]) else 0
        current_price = float(close.iloc[-1])
        
        # Bantlar
        upper_band_1 = current_vwap + current_std
        upper_band_2 = current_vwap + (current_std * 2)
        lower_band_1 = current_vwap - current_std
        lower_band_2 = current_vwap - (current_std * 2)
        
        # Fiyatın VWAP'a göre sapması
        deviation_pct = ((current_price - current_vwap) / current_vwap) * 100
        
        # Sinyal belirleme
        if current_price < lower_band_2:
            signal = "GÜÇLÜ AL"
            zone = "aşırı_satım"
        elif current_price < lower_band_1:
            signal = "AL"
            zone = "destek"
        elif current_price > upper_band_2:
            signal = "GÜÇLÜ SAT"
            zone = "aşırı_alım"
        elif current_price > upper_band_1:
            signal = "SAT"
            zone = "direnç"
        else:
            signal = "NÖTR"
            zone = "değer_bölgesi"
        
        return {
            "vwap": round(current_vwap, 2),
            "upper_band_1": round(upper_band_1, 2),
            "upper_band_2": round(upper_band_2, 2),
            "lower_band_1": round(lower_band_1, 2),
            "lower_band_2": round(lower_band_2, 2),
            "deviation_pct": round(deviation_pct, 2),
            "signal": signal,
            "zone": zone,
            "trend": "bullish" if current_price > current_vwap else "bearish"
        }
    
    @staticmethod
    def calculate_anchored_vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        anchor_index: int = None
    ) -> Dict[str, float]:
        """
        Sabitlenmiş VWAP (belirli bir noktadan başlayan)
        Önemli dip/tepe noktalarından hesaplama için kullanılır
        """
        if anchor_index is None:
            # Son 50 günün en düşük noktasından başla
            anchor_index = low.tail(50).idxmin()
        
        # Anchor noktasından itibaren hesapla
        anchor_loc = close.index.get_loc(anchor_index) if anchor_index in close.index else 0
        
        sliced_high = high.iloc[anchor_loc:]
        sliced_low = low.iloc[anchor_loc:]
        sliced_close = close.iloc[anchor_loc:]
        sliced_volume = volume.iloc[anchor_loc:]
        
        typical_price = (sliced_high + sliced_low + sliced_close) / 3
        vwap = (typical_price * sliced_volume).cumsum() / sliced_volume.cumsum()
        
        return {
            "anchored_vwap": round(float(vwap.iloc[-1]), 2),
            "anchor_date": str(anchor_index),
            "days_since_anchor": len(sliced_close)
        }


class VolumeProfile:
    """
    Hacim Profili Analizi
    ======================
    Fiyat seviyelerindeki hacim dağılımını analiz eder
    POC (Point of Control), Value Area gibi önemli seviyeleri tespit eder
    """
    
    @staticmethod
    def calculate(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        num_bins: int = 20,
        lookback: int = 50
    ) -> Dict[str, Any]:
        """
        Hacim profili hesapla
        
        Args:
            high, low, close: Fiyat serileri
            volume: Hacim serisi
            num_bins: Fiyat bölmesi sayısı
            lookback: Geriye bakış periyodu
            
        Returns:
            Hacim profili analizi
        """
        if len(close) < lookback:
            lookback = len(close)
        
        # Son N günü al
        h = high.tail(lookback)
        l = low.tail(lookback)
        c = close.tail(lookback)
        v = volume.tail(lookback)
        
        # Fiyat aralığı
        price_min = float(l.min())
        price_max = float(h.max())
        price_range = price_max - price_min
        
        if price_range == 0:
            return {"error": "Fiyat aralığı sıfır"}
        
        # Fiyat bölmeleri oluştur
        bins = np.linspace(price_min, price_max, num_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # Her bölmedeki hacmi hesapla
        volume_at_price = np.zeros(num_bins)
        
        for i in range(len(c)):
            # Mumun kapsadığı bölmeleri bul
            candle_low = float(l.iloc[i])
            candle_high = float(h.iloc[i])
            candle_volume = float(v.iloc[i])
            
            for j in range(num_bins):
                bin_low = bins[j]
                bin_high = bins[j + 1]
                
                # Mum bu bölmeyle kesişiyor mu?
                if candle_low <= bin_high and candle_high >= bin_low:
                    # Kesişim oranına göre hacim dağıt
                    overlap_low = max(candle_low, bin_low)
                    overlap_high = min(candle_high, bin_high)
                    overlap_ratio = (overlap_high - overlap_low) / (candle_high - candle_low + 0.0001)
                    volume_at_price[j] += candle_volume * overlap_ratio
        
        # POC (Point of Control) - En yüksek hacimli seviye
        poc_index = np.argmax(volume_at_price)
        poc_price = float(bin_centers[poc_index])
        
        # Value Area (Toplam hacmin %70'inin olduğu bölge)
        total_volume = volume_at_price.sum()
        target_volume = total_volume * 0.70
        
        # POC'dan dışarı doğru genişle
        va_low_idx = poc_index
        va_high_idx = poc_index
        current_volume = volume_at_price[poc_index]
        
        while current_volume < target_volume:
            # Aşağı veya yukarı genişle (hangisi daha fazla hacime sahipse)
            expand_low = volume_at_price[va_low_idx - 1] if va_low_idx > 0 else 0
            expand_high = volume_at_price[va_high_idx + 1] if va_high_idx < num_bins - 1 else 0
            
            if expand_low >= expand_high and va_low_idx > 0:
                va_low_idx -= 1
                current_volume += expand_low
            elif va_high_idx < num_bins - 1:
                va_high_idx += 1
                current_volume += expand_high
            else:
                break
        
        va_high = float(bins[va_high_idx + 1])
        va_low = float(bins[va_low_idx])
        
        # High Volume Nodes (Yüksek hacimli bölgeler)
        mean_volume = volume_at_price.mean()
        std_volume = volume_at_price.std()
        hvn_threshold = mean_volume + std_volume
        hvn_indices = np.where(volume_at_price > hvn_threshold)[0]
        hvn_levels = [round(float(bin_centers[i]), 2) for i in hvn_indices]
        
        # Low Volume Nodes (Düşük hacimli bölgeler - potansiyel destek/direnç)
        lvn_threshold = mean_volume - std_volume * 0.5
        lvn_indices = np.where(volume_at_price < lvn_threshold)[0]
        lvn_levels = [round(float(bin_centers[i]), 2) for i in lvn_indices]
        
        current_price = float(c.iloc[-1])
        
        # Sinyal belirleme
        if current_price < va_low:
            signal = "AL"
            zone = "değer_altı"
        elif current_price > va_high:
            signal = "SAT"
            zone = "değer_üstü"
        else:
            signal = "NÖTR"
            zone = "değer_içi"
        
        return {
            "poc": round(poc_price, 2),
            "value_area_high": round(va_high, 2),
            "value_area_low": round(va_low, 2),
            "high_volume_nodes": hvn_levels[:5],  # İlk 5
            "low_volume_nodes": lvn_levels[:5],   # İlk 5
            "current_zone": zone,
            "signal": signal,
            "price_to_poc_pct": round(((current_price - poc_price) / poc_price) * 100, 2),
            "volume_profile_data": {
                "prices": [round(float(p), 2) for p in bin_centers],
                "volumes": [round(float(v), 0) for v in volume_at_price]
            }
        }


class MomentumDivergence:
    """
    Momentum Diverjans Tespiti
    ===========================
    RSI, MACD ve fiyat arasındaki uyumsuzlukları tespit eder
    Güçlü dönüş sinyalleri verir
    """
    
    @staticmethod
    def detect_rsi_divergence(
        close: pd.Series,
        rsi: pd.Series,
        lookback: int = 20
    ) -> Dict[str, Any]:
        """
        RSI diverjansı tespit et
        
        Boğa Diverjansı: Fiyat düşük yapıyor, RSI düşük yapmıyor (AL sinyali)
        Ayı Diverjansı: Fiyat yüksek yapıyor, RSI yüksek yapmıyor (SAT sinyali)
        """
        if len(close) < lookback or len(rsi) < lookback:
            return {"divergence": "none", "signal": "BEKLE", "strength": 0}
        
        price = close.tail(lookback)
        rsi_values = rsi.tail(lookback)
        
        # Yerel dip ve tepeleri bul
        price_arr = price.values
        rsi_arr = rsi_values.values
        
        try:
            # Dipleri bul
            price_lows = argrelextrema(price_arr, np.less, order=3)[0]
            rsi_lows = argrelextrema(rsi_arr, np.less, order=3)[0]
            
            # Tepeleri bul
            price_highs = argrelextrema(price_arr, np.greater, order=3)[0]
            rsi_highs = argrelextrema(rsi_arr, np.greater, order=3)[0]
            
            # Boğa diverjansı kontrolü (son 2 dip)
            if len(price_lows) >= 2 and len(rsi_lows) >= 2:
                # Fiyatta düşen dipler
                if price_arr[price_lows[-1]] < price_arr[price_lows[-2]]:
                    # RSI'da yükselen dipler (klasik boğa diverjansı)
                    if rsi_arr[rsi_lows[-1]] > rsi_arr[rsi_lows[-2]]:
                        strength = abs(rsi_arr[rsi_lows[-1]] - rsi_arr[rsi_lows[-2]])
                        return {
                            "divergence": "bullish",
                            "type": "klasik",
                            "signal": "AL",
                            "strength": round(min(strength * 2, 100), 1),
                            "description": "Klasik Boğa Diverjansı: Fiyat düşerken RSI yükseliyor",
                            "price_points": [float(price_arr[price_lows[-2]]), float(price_arr[price_lows[-1]])],
                            "rsi_points": [float(rsi_arr[rsi_lows[-2]]), float(rsi_arr[rsi_lows[-1]])]
                        }
            
            # Gizli boğa diverjansı (fiyatta yükselen dipler, RSI'da düşen dipler)
            if len(price_lows) >= 2 and len(rsi_lows) >= 2:
                if price_arr[price_lows[-1]] > price_arr[price_lows[-2]]:
                    if rsi_arr[rsi_lows[-1]] < rsi_arr[rsi_lows[-2]]:
                        strength = abs(rsi_arr[rsi_lows[-2]] - rsi_arr[rsi_lows[-1]])
                        return {
                            "divergence": "hidden_bullish",
                            "type": "gizli",
                            "signal": "AL",
                            "strength": round(min(strength * 1.5, 80), 1),
                            "description": "Gizli Boğa Diverjansı: Yükseliş trendi devam sinyali"
                        }
            
            # Ayı diverjansı kontrolü (son 2 tepe)
            if len(price_highs) >= 2 and len(rsi_highs) >= 2:
                # Fiyatta yükselen tepeler
                if price_arr[price_highs[-1]] > price_arr[price_highs[-2]]:
                    # RSI'da düşen tepeler (klasik ayı diverjansı)
                    if rsi_arr[rsi_highs[-1]] < rsi_arr[rsi_highs[-2]]:
                        strength = abs(rsi_arr[rsi_highs[-2]] - rsi_arr[rsi_highs[-1]])
                        return {
                            "divergence": "bearish",
                            "type": "klasik",
                            "signal": "SAT",
                            "strength": round(min(strength * 2, 100), 1),
                            "description": "Klasik Ayı Diverjansı: Fiyat yükselirken RSI düşüyor",
                            "price_points": [float(price_arr[price_highs[-2]]), float(price_arr[price_highs[-1]])],
                            "rsi_points": [float(rsi_arr[rsi_highs[-2]]), float(rsi_arr[rsi_highs[-1]])]
                        }
            
            # Gizli ayı diverjansı
            if len(price_highs) >= 2 and len(rsi_highs) >= 2:
                if price_arr[price_highs[-1]] < price_arr[price_highs[-2]]:
                    if rsi_arr[rsi_highs[-1]] > rsi_arr[rsi_highs[-2]]:
                        strength = abs(rsi_arr[rsi_highs[-1]] - rsi_arr[rsi_highs[-2]])
                        return {
                            "divergence": "hidden_bearish",
                            "type": "gizli",
                            "signal": "SAT",
                            "strength": round(min(strength * 1.5, 80), 1),
                            "description": "Gizli Ayı Diverjansı: Düşüş trendi devam sinyali"
                        }
                        
        except Exception as e:
            pass
        
        return {"divergence": "none", "signal": "BEKLE", "strength": 0}
    
    @staticmethod
    def detect_macd_divergence(
        close: pd.Series,
        macd_histogram: pd.Series,
        lookback: int = 20
    ) -> Dict[str, Any]:
        """MACD histogram diverjansı tespit et"""
        if len(close) < lookback or len(macd_histogram) < lookback:
            return {"divergence": "none", "signal": "BEKLE", "strength": 0}
        
        price = close.tail(lookback)
        hist = macd_histogram.tail(lookback)
        
        price_arr = price.values
        hist_arr = hist.values
        
        try:
            price_lows = argrelextrema(price_arr, np.less, order=3)[0]
            hist_lows = argrelextrema(hist_arr, np.less, order=3)[0]
            price_highs = argrelextrema(price_arr, np.greater, order=3)[0]
            hist_highs = argrelextrema(hist_arr, np.greater, order=3)[0]
            
            # MACD boğa diverjansı
            if len(price_lows) >= 2 and len(hist_lows) >= 2:
                if price_arr[price_lows[-1]] < price_arr[price_lows[-2]]:
                    if hist_arr[hist_lows[-1]] > hist_arr[hist_lows[-2]]:
                        return {
                            "divergence": "bullish",
                            "signal": "AL",
                            "strength": 70,
                            "description": "MACD Boğa Diverjansı"
                        }
            
            # MACD ayı diverjansı
            if len(price_highs) >= 2 and len(hist_highs) >= 2:
                if price_arr[price_highs[-1]] > price_arr[price_highs[-2]]:
                    if hist_arr[hist_highs[-1]] < hist_arr[hist_highs[-2]]:
                        return {
                            "divergence": "bearish",
                            "signal": "SAT",
                            "strength": 70,
                            "description": "MACD Ayı Diverjansı"
                        }
        except:
            pass
        
        return {"divergence": "none", "signal": "BEKLE", "strength": 0}


class ElliottWaveAnalysis:
    """
    Elliott Dalga Analizi (Basitleştirilmiş)
    =========================================
    Dalga yapılarını tespit etmeye çalışır
    """
    
    @staticmethod
    def detect_wave_structure(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        lookback: int = 50
    ) -> Dict[str, Any]:
        """Basit dalga yapısı tespiti"""
        if len(close) < lookback:
            return {"wave": "belirsiz", "position": "unknown"}
        
        price = close.tail(lookback)
        highs = high.tail(lookback).values
        lows = low.tail(lookback).values
        
        try:
            # Önemli pivot noktalarını bul
            high_pivots = argrelextrema(highs, np.greater, order=5)[0]
            low_pivots = argrelextrema(lows, np.less, order=5)[0]
            
            if len(high_pivots) < 2 or len(low_pivots) < 2:
                return {"wave": "belirsiz", "position": "yetersiz_veri"}
            
            # Son hareketin yönü
            last_high = highs[high_pivots[-1]]
            last_low = lows[low_pivots[-1]]
            current_price = float(close.iloc[-1])
            
            # Trend belirleme
            if high_pivots[-1] > low_pivots[-1]:
                # Son pivot bir tepe
                if current_price < last_high * 0.97:
                    trend = "düzeltme"
                    wave_position = "muhtemel_abc"
                else:
                    trend = "yükseliş"
                    wave_position = "muhtemel_5_dalga"
            else:
                # Son pivot bir dip
                if current_price > last_low * 1.03:
                    trend = "toparlanma"
                    wave_position = "muhtemel_1_dalga"
                else:
                    trend = "düşüş"
                    wave_position = "muhtemel_c_dalgası"
            
            return {
                "wave": trend,
                "position": wave_position,
                "pivot_count": len(high_pivots) + len(low_pivots),
                "last_high_pivot": round(float(last_high), 2),
                "last_low_pivot": round(float(last_low), 2)
            }
            
        except:
            return {"wave": "belirsiz", "position": "hesaplama_hatası"}


class SuperTrend:
    """
    SuperTrend Göstergesi
    =====================
    ATR tabanlı trend takip göstergesi
    """
    
    @staticmethod
    def calculate(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 10,
        multiplier: float = 3.0
    ) -> Dict[str, Any]:
        """
        SuperTrend hesapla
        
        Args:
            high, low, close: Fiyat serileri
            period: ATR periyodu
            multiplier: ATR çarpanı
            
        Returns:
            SuperTrend değerleri ve sinyali
        """
        if len(close) < period + 1:
            return {"supertrend": None, "signal": "BEKLE", "trend": "belirsiz"}
        
        # ATR hesapla
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Orta çizgi
        hl2 = (high + low) / 2
        
        # Üst ve alt bantlar
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # SuperTrend hesaplama
        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=int)
        
        supertrend.iloc[period] = upper_band.iloc[period]
        direction.iloc[period] = -1
        
        for i in range(period + 1, len(close)):
            if close.iloc[i] > supertrend.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif close.iloc[i] < supertrend.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
                
                if direction.iloc[i] == 1 and lower_band.iloc[i] > supertrend.iloc[i]:
                    supertrend.iloc[i] = lower_band.iloc[i]
                elif direction.iloc[i] == -1 and upper_band.iloc[i] < supertrend.iloc[i]:
                    supertrend.iloc[i] = upper_band.iloc[i]
        
        current_st = float(supertrend.iloc[-1])
        current_dir = int(direction.iloc[-1])
        current_price = float(close.iloc[-1])
        
        # Trend değişimi kontrolü
        trend_changed = False
        if len(direction) > 2:
            trend_changed = direction.iloc[-1] != direction.iloc[-2]
        
        signal = "AL" if current_dir == 1 else "SAT"
        if trend_changed:
            signal = "GÜÇLÜ " + signal
        
        return {
            "supertrend": round(current_st, 2),
            "direction": "UP" if current_dir == 1 else "DOWN",
            "signal": signal,
            "trend": "yükseliş" if current_dir == 1 else "düşüş",
            "trend_changed": trend_changed,
            "distance_pct": round(((current_price - current_st) / current_st) * 100, 2)
        }


class MarketRegime:
    """
    Piyasa Rejimi Tespiti
    ======================
    Mevcut piyasa koşullarını belirler (trend, yatay, volatil)
    """
    
    @staticmethod
    def detect(
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        volume: pd.Series,
        lookback: int = 20
    ) -> Dict[str, Any]:
        """
        Piyasa rejimini tespit et
        
        Returns:
            Piyasa rejimi analizi
        """
        if len(close) < lookback:
            return {"regime": "belirsiz", "confidence": 0}
        
        price = close.tail(lookback)
        h = high.tail(lookback)
        l = low.tail(lookback)
        vol = volume.tail(lookback)
        
        # 1. Trend gücü (lineer regresyon)
        x = np.arange(len(price))
        slope, intercept, r_value, p_value, std_err = linregress(x, price.values)
        r_squared = r_value ** 2
        trend_strength = r_squared * 100
        
        # Normalize edilmiş eğim (yüzdelik değişim)
        normalized_slope = (slope / price.iloc[0]) * 100
        
        # 2. Volatilite (ATR bazlı)
        tr = pd.concat([h - l, abs(h - close.shift()), abs(l - close.shift())], axis=1).max(axis=1)
        atr = tr.tail(lookback).mean()
        atr_pct = (atr / price.iloc[-1]) * 100
        
        # Tarihsel ATR karşılaştırması
        if len(close) > 50:
            historical_atr = tr.tail(50).mean()
            volatility_ratio = atr / historical_atr
        else:
            volatility_ratio = 1.0
        
        # 3. Hacim trendi
        vol_ma = vol.rolling(window=5).mean()
        vol_trend = "artan" if vol.iloc[-1] > vol_ma.iloc[-5] else "azalan"
        
        # Rejim belirleme
        if trend_strength > 60:
            if normalized_slope > 0.5:
                regime = "güçlü_yükseliş"
                confidence = min(trend_strength + 20, 95)
            elif normalized_slope < -0.5:
                regime = "güçlü_düşüş"
                confidence = min(trend_strength + 20, 95)
            else:
                regime = "zayıf_trend"
                confidence = trend_strength
        elif atr_pct > 4 or volatility_ratio > 1.5:
            regime = "yüksek_volatilite"
            confidence = min(volatility_ratio * 40, 90)
        elif atr_pct < 1.5 and trend_strength < 30:
            regime = "düşük_volatilite_yatay"
            confidence = 70
        else:
            regime = "karma"
            confidence = 50
        
        # Strateji önerisi
        if regime in ["güçlü_yükseliş", "güçlü_düşüş"]:
            strategy = "trend_takip"
        elif regime == "yüksek_volatilite":
            strategy = "kısa_vadeli_swing"
        elif regime == "düşük_volatilite_yatay":
            strategy = "range_trading"
        else:
            strategy = "dikkatli_ol"
        
        return {
            "regime": regime,
            "confidence": round(confidence, 1),
            "trend_strength": round(trend_strength, 1),
            "trend_direction": "up" if normalized_slope > 0 else "down",
            "normalized_slope": round(normalized_slope, 3),
            "volatility_pct": round(atr_pct, 2),
            "volatility_ratio": round(volatility_ratio, 2),
            "volume_trend": vol_trend,
            "suggested_strategy": strategy
        }
