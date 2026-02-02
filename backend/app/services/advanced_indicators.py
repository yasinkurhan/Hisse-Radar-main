"""
Gelismis Teknik Gostergeler Modulu
===================================
ADX, Fibonacci, OBV, Destek/Direnc, Formasyonlar
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy.signal import argrelextrema


class AdvancedIndicators:
    """Gelismis teknik gostergeler"""
    
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, float]:
        """
        ADX (Average Directional Index) - Trend gucu gostergesi
        ADX > 25: Guclu trend
        ADX < 20: Zayif trend veya yatay piyasa
        """
        if len(close) < period + 1:
            return {"adx": 25, "plus_di": 25, "minus_di": 25, "trend_strength": "zayif"}
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        plus_dm = high.diff()
        minus_dm = low.diff().abs() * -1
        
        plus_dm = plus_dm.where((plus_dm > minus_dm.abs()) & (plus_dm > 0), 0)
        minus_dm = minus_dm.abs().where((minus_dm.abs() > plus_dm) & (minus_dm < 0), 0)
        
        # Smoothed values
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
        adx = dx.rolling(window=period).mean()
        
        adx_val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 25
        plus_di_val = float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else 25
        minus_di_val = float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 25
        
        # Trend gucu
        if adx_val > 40:
            trend_strength = "cok_guclu"
        elif adx_val > 25:
            trend_strength = "guclu"
        elif adx_val > 20:
            trend_strength = "orta"
        else:
            trend_strength = "zayif"
        
        return {
            "adx": round(adx_val, 2),
            "plus_di": round(plus_di_val, 2),
            "minus_di": round(minus_di_val, 2),
            "trend_strength": trend_strength,
            "trend_direction": "yukari" if plus_di_val > minus_di_val else "asagi"
        }
    
    @staticmethod
    def calculate_fibonacci_levels(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, Any]:
        """
        Fibonacci Retracement seviyeleri
        Son 50 gunluk en yuksek ve en dusuk noktalar arasinda
        """
        if len(close) < 50:
            return {"levels": {}, "current_zone": "belirsiz"}
        
        recent_high = high.tail(50).max()
        recent_low = low.tail(50).min()
        diff = recent_high - recent_low
        current_price = float(close.iloc[-1])
        
        levels = {
            "0": round(recent_low, 2),
            "23.6": round(recent_low + diff * 0.236, 2),
            "38.2": round(recent_low + diff * 0.382, 2),
            "50": round(recent_low + diff * 0.5, 2),
            "61.8": round(recent_low + diff * 0.618, 2),
            "78.6": round(recent_low + diff * 0.786, 2),
            "100": round(recent_high, 2)
        }
        
        # Fiyatin hangi bolge arasinda oldugunu bul
        zone = "belirsiz"
        if current_price <= levels["23.6"]:
            zone = "0-23.6 (Guclu destek)"
        elif current_price <= levels["38.2"]:
            zone = "23.6-38.2 (Destek)"
        elif current_price <= levels["50"]:
            zone = "38.2-50 (Orta)"
        elif current_price <= levels["61.8"]:
            zone = "50-61.8 (Direnc)"
        elif current_price <= levels["78.6"]:
            zone = "61.8-78.6 (Guclu direnc)"
        else:
            zone = "78.6-100 (Tepe bolgesi)"
        
        return {
            "levels": levels,
            "current_zone": zone,
            "high": round(recent_high, 2),
            "low": round(recent_low, 2)
        }
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> Dict[str, Any]:
        """
        OBV (On Balance Volume) - Hacim/fiyat iliskisi
        OBV yukselirken fiyat dusuyorsa: Pozitif sapma (alim firsati)
        OBV duserken fiyat yukseliyorsa: Negatif sapma (satis firsati)
        """
        if len(close) < 20:
            return {"obv": 0, "obv_signal": "notr", "divergence": "yok"}
        
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = 0
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        # OBV trendi (son 10 gun)
        obv_sma = obv.rolling(window=10).mean()
        current_obv = float(obv.iloc[-1])
        obv_sma_val = float(obv_sma.iloc[-1])
        
        # Sapma kontrolu (son 5 gun)
        price_change = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100
        obv_change = (obv.iloc[-1] - obv.iloc[-5]) / (abs(obv.iloc[-5]) + 1) * 100
        
        divergence = "yok"
        if price_change < -2 and obv_change > 5:
            divergence = "pozitif_sapma"  # Alim firsati
        elif price_change > 2 and obv_change < -5:
            divergence = "negatif_sapma"  # Satis firsati
        
        obv_signal = "notr"
        if current_obv > obv_sma_val * 1.05:
            obv_signal = "guclu_alim"
        elif current_obv > obv_sma_val:
            obv_signal = "alim"
        elif current_obv < obv_sma_val * 0.95:
            obv_signal = "guclu_satis"
        elif current_obv < obv_sma_val:
            obv_signal = "satis"
        
        return {
            "obv": int(current_obv),
            "obv_sma": int(obv_sma_val),
            "obv_signal": obv_signal,
            "divergence": divergence
        }
    
    @staticmethod
    def calculate_support_resistance(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, Any]:
        """
        Destek ve Direnc seviyeleri
        Pivot noktalarindan hesaplar
        """
        if len(close) < 20:
            return {"supports": [], "resistances": [], "nearest_support": 0, "nearest_resistance": 0}
        
        current_price = float(close.iloc[-1])
        
        # Son 50 gunluk pivot noktalari bul
        window = min(50, len(close))
        highs = high.tail(window).values
        lows = low.tail(window).values
        
        # Yerel maksimum ve minimumlar
        try:
            local_max_idx = argrelextrema(highs, np.greater, order=5)[0]
            local_min_idx = argrelextrema(lows, np.less, order=5)[0]
            
            resistances = sorted([float(highs[i]) for i in local_max_idx if highs[i] > current_price])[:3]
            supports = sorted([float(lows[i]) for i in local_min_idx if lows[i] < current_price], reverse=True)[:3]
        except:
            # Fallback: basit hesaplama
            resistances = [float(high.tail(20).max())]
            supports = [float(low.tail(20).min())]
        
        nearest_resistance = resistances[0] if resistances else current_price * 1.05
        nearest_support = supports[0] if supports else current_price * 0.95
        
        # Destek/direnc mesafesi
        resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
        support_distance = ((current_price - nearest_support) / current_price) * 100
        
        return {
            "supports": [round(s, 2) for s in supports],
            "resistances": [round(r, 2) for r in resistances],
            "nearest_support": round(nearest_support, 2),
            "nearest_resistance": round(nearest_resistance, 2),
            "support_distance_pct": round(support_distance, 2),
            "resistance_distance_pct": round(resistance_distance, 2)
        }


class PatternRecognition:
    """Formasyon Tespiti"""
    
    @staticmethod
    def detect_patterns(high: pd.Series, low: pd.Series, close: pd.Series) -> List[Dict[str, Any]]:
        """Tum formasyonlari tespit et"""
        patterns = []
        
        # Cift Dip
        double_bottom = PatternRecognition._detect_double_bottom(low, close)
        if double_bottom:
            patterns.append(double_bottom)
        
        # Cift Tepe
        double_top = PatternRecognition._detect_double_top(high, close)
        if double_top:
            patterns.append(double_top)
        
        # Omuz Bas Omuz
        hns = PatternRecognition._detect_head_shoulders(high, close)
        if hns:
            patterns.append(hns)
        
        # Ucgen
        triangle = PatternRecognition._detect_triangle(high, low, close)
        if triangle:
            patterns.append(triangle)
        
        return patterns
    
    @staticmethod
    def _detect_double_bottom(low: pd.Series, close: pd.Series) -> Optional[Dict[str, Any]]:
        """Cift Dip formasyonu - Yukselis sinyali"""
        if len(close) < 30:
            return None
        
        recent_low = low.tail(30)
        min_idx = recent_low.idxmin()
        min_val = recent_low[min_idx]
        
        # Benzer dusuk seviye ara (+-3%)
        tolerance = min_val * 0.03
        similar_lows = recent_low[(recent_low >= min_val - tolerance) & (recent_low <= min_val + tolerance)]
        
        if len(similar_lows) >= 2:
            # Iki dip arasinda en az 5 gun olmali
            idx_list = list(similar_lows.index)
            if len(idx_list) >= 2:
                first_idx = recent_low.index.get_loc(idx_list[0])
                last_idx = recent_low.index.get_loc(idx_list[-1])
                if last_idx - first_idx >= 5:
                    current_price = float(close.iloc[-1])
                    if current_price > min_val * 1.02:  # Dipten yukari kirildi
                        return {
                            "pattern": "cift_dip",
                            "signal": "AL",
                            "strength": "guclu",
                            "description": f"Cift dip formasyonu: {round(min_val, 2)} TL seviyesinde destek",
                            "target": round(min_val * 1.10, 2)
                        }
        return None
    
    @staticmethod
    def _detect_double_top(high: pd.Series, close: pd.Series) -> Optional[Dict[str, Any]]:
        """Cift Tepe formasyonu - Dusus sinyali"""
        if len(close) < 30:
            return None
        
        recent_high = high.tail(30)
        max_idx = recent_high.idxmax()
        max_val = recent_high[max_idx]
        
        # Benzer yuksek seviye ara (+-3%)
        tolerance = max_val * 0.03
        similar_highs = recent_high[(recent_high >= max_val - tolerance) & (recent_high <= max_val + tolerance)]
        
        if len(similar_highs) >= 2:
            idx_list = list(similar_highs.index)
            if len(idx_list) >= 2:
                first_idx = recent_high.index.get_loc(idx_list[0])
                last_idx = recent_high.index.get_loc(idx_list[-1])
                if last_idx - first_idx >= 5:
                    current_price = float(close.iloc[-1])
                    if current_price < max_val * 0.98:  # Tepeden asagi kirildi
                        return {
                            "pattern": "cift_tepe",
                            "signal": "SAT",
                            "strength": "guclu",
                            "description": f"Cift tepe formasyonu: {round(max_val, 2)} TL seviyesinde direnc",
                            "target": round(max_val * 0.90, 2)
                        }
        return None
    
    @staticmethod
    def _detect_head_shoulders(high: pd.Series, close: pd.Series) -> Optional[Dict[str, Any]]:
        """Omuz-Bas-Omuz formasyonu"""
        if len(close) < 40:
            return None
        
        recent = high.tail(40)
        
        try:
            # Yerel maksimumlar bul
            values = recent.values
            local_max_idx = argrelextrema(values, np.greater, order=3)[0]
            
            if len(local_max_idx) >= 3:
                # Son 3 tepe
                peaks = [values[i] for i in local_max_idx[-3:]]
                
                # Orta tepe en yuksek olmali (bas)
                if peaks[1] > peaks[0] and peaks[1] > peaks[2]:
                    # Omuzlar benzer seviyede olmali (+-5%)
                    if abs(peaks[0] - peaks[2]) / peaks[0] < 0.05:
                        current_price = float(close.iloc[-1])
                        neckline = min(peaks[0], peaks[2]) * 0.95
                        
                        if current_price < neckline:
                            return {
                                "pattern": "omuz_bas_omuz",
                                "signal": "SAT",
                                "strength": "cok_guclu",
                                "description": "Omuz-Bas-Omuz formasyonu tamamlandi",
                                "target": round(neckline * 0.90, 2)
                            }
        except:
            pass
        
        return None
    
    @staticmethod
    def _detect_triangle(high: pd.Series, low: pd.Series, close: pd.Series) -> Optional[Dict[str, Any]]:
        """Ucgen formasyonu"""
        if len(close) < 20:
            return None
        
        recent_high = high.tail(20)
        recent_low = low.tail(20)
        
        # Son 20 gunluk trend
        high_slope = (recent_high.iloc[-1] - recent_high.iloc[0]) / 20
        low_slope = (recent_low.iloc[-1] - recent_low.iloc[0]) / 20
        
        # Daralan ucgen: yuksekler dusuyor, dusukler yukseliyor
        if high_slope < 0 and low_slope > 0:
            range_start = recent_high.iloc[0] - recent_low.iloc[0]
            range_end = recent_high.iloc[-1] - recent_low.iloc[-1]
            
            if range_end < range_start * 0.6:  # Range %40 daraldi
                return {
                    "pattern": "simetrik_ucgen",
                    "signal": "BEKLE",
                    "strength": "orta",
                    "description": "Simetrik ucgen - kirilim bekleniyor",
                    "target": None
                }
        
        # Yukari ucgen: yuksekler sabit, dusukler yukseliyor
        elif abs(high_slope) < 0.5 and low_slope > 0.5:
            return {
                "pattern": "yukari_ucgen",
                "signal": "AL",
                "strength": "orta",
                "description": "Yukari ucgen - yukari kirilim bekleniyor",
                "target": round(float(recent_high.max()) * 1.05, 2)
            }
        
        # Asagi ucgen
        elif high_slope < -0.5 and abs(low_slope) < 0.5:
            return {
                "pattern": "asagi_ucgen",
                "signal": "SAT",
                "strength": "orta",
                "description": "Asagi ucgen - asagi kirilim bekleniyor",
                "target": round(float(recent_low.min()) * 0.95, 2)
            }
        
        return None


class FundamentalAnalysis:
    """Temel Analiz Modulu"""
    
    @staticmethod
    def get_fundamentals(ticker) -> Dict[str, Any]:
        """Yahoo Finance'den temel verileri al"""
        try:
            info = ticker.info
            
            # F/K Orani
            pe_ratio = info.get('trailingPE') or info.get('forwardPE')
            
            # PD/DD Orani
            pb_ratio = info.get('priceToBook')
            
            # Piyasa Degeri
            market_cap = info.get('marketCap', 0)
            
            # Temettü Verimi
            dividend_yield = info.get('dividendYield', 0)
            if dividend_yield:
                dividend_yield = dividend_yield * 100
            
            # 52 haftalik yuksek/dusuk
            fifty_two_high = info.get('fiftyTwoWeekHigh', 0)
            fifty_two_low = info.get('fiftyTwoWeekLow', 0)
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            
            # 52 haftalik pozisyon
            if fifty_two_high and fifty_two_low and current_price:
                fifty_two_range = fifty_two_high - fifty_two_low
                fifty_two_position = ((current_price - fifty_two_low) / fifty_two_range * 100) if fifty_two_range > 0 else 50
            else:
                fifty_two_position = 50
            
            # Değerleme skoru
            valuation_score = FundamentalAnalysis._calculate_valuation_score(pe_ratio, pb_ratio, dividend_yield, fifty_two_position)
            
            return {
                "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
                "pb_ratio": round(pb_ratio, 2) if pb_ratio else None,
                "market_cap": market_cap,
                "market_cap_formatted": FundamentalAnalysis._format_market_cap(market_cap),
                "dividend_yield": round(dividend_yield, 2) if dividend_yield else 0,
                "fifty_two_week_high": round(fifty_two_high, 2) if fifty_two_high else None,
                "fifty_two_week_low": round(fifty_two_low, 2) if fifty_two_low else None,
                "fifty_two_week_position": round(fifty_two_position, 1),
                "valuation_score": valuation_score,
                "valuation_signal": "ucuz" if valuation_score > 60 else ("pahali" if valuation_score < 40 else "normal")
            }
        except Exception as e:
            return {
                "pe_ratio": None,
                "pb_ratio": None,
                "market_cap": 0,
                "market_cap_formatted": "-",
                "dividend_yield": 0,
                "fifty_two_week_high": None,
                "fifty_two_week_low": None,
                "fifty_two_week_position": 50,
                "valuation_score": 50,
                "valuation_signal": "belirsiz"
            }
    
    @staticmethod
    def _calculate_valuation_score(pe: float, pb: float, dividend: float, position: float) -> int:
        """Degerlenme skoru hesapla (0-100, yuksek = ucuz)"""
        score = 50
        
        # F/K değerlendirmesi (BIST için)
        if pe:
            if pe < 5:
                score += 15
            elif pe < 10:
                score += 10
            elif pe < 15:
                score += 5
            elif pe > 30:
                score -= 15
            elif pe > 20:
                score -= 10
        
        # PD/DD değerlendirmesi
        if pb:
            if pb < 1:
                score += 15
            elif pb < 1.5:
                score += 10
            elif pb < 2:
                score += 5
            elif pb > 4:
                score -= 15
            elif pb > 3:
                score -= 10
        
        # Temettü
        if dividend:
            if dividend > 8:
                score += 10
            elif dividend > 5:
                score += 5
            elif dividend > 3:
                score += 2
        
        # 52 haftalık pozisyon (düşükse ucuz)
        if position < 30:
            score += 10
        elif position < 50:
            score += 5
        elif position > 80:
            score -= 10
        elif position > 60:
            score -= 5
        
        return max(0, min(100, score))
    
    @staticmethod
    def _format_market_cap(value: int) -> str:
        """Piyasa değerini formatla"""
        if not value:
            return "-"
        if value >= 1e12:
            return f"{value/1e12:.1f}T TL"
        elif value >= 1e9:
            return f"{value/1e9:.1f}B TL"
        elif value >= 1e6:
            return f"{value/1e6:.1f}M TL"
        return f"{value:,.0f} TL"
