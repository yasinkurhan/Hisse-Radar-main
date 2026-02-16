"""
HisseRadar AI Sinyal Birleştirme Modülü
========================================
Çoklu gösterge sinyallerini yapay zeka yaklaşımıyla birleştirir
Ağırlıklı oylama, güven skorlaması ve ensemble sinyal üretimi
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class SignalType(Enum):
    """Sinyal türleri"""
    STRONG_BUY = "GÜÇLÜ AL"
    BUY = "AL"
    NEUTRAL = "NÖTR"
    SELL = "SAT"
    STRONG_SELL = "GÜÇLÜ SAT"


@dataclass
class IndicatorSignal:
    """Gösterge sinyali veri yapısı"""
    name: str
    signal: SignalType
    strength: float  # 0-100
    weight: float    # Ağırlık
    confidence: float  # Güvenilirlik 0-1
    data: Dict[str, Any] = field(default_factory=dict)


class SignalWeights:
    """
    Gösterge Ağırlıkları
    ====================
    Her göstergenin genel skordaki ağırlığı
    Piyasa koşullarına göre dinamik ayarlanır
    """
    
    # Varsayılan ağırlıklar
    DEFAULT_WEIGHTS = {
        # Trend göstergeleri
        "ichimoku": 0.12,
        "supertrend": 0.08,
        "ma_cross": 0.08,
        "adx": 0.06,
        
        # Momentum göstergeleri
        "rsi": 0.10,
        "macd": 0.10,
        "stochastic": 0.06,
        "momentum_divergence": 0.08,
        
        # Volatilite göstergeleri
        "bollinger": 0.08,
        "atr": 0.04,
        
        # Hacim göstergeleri
        "vwap": 0.06,
        "volume_profile": 0.04,
        "obv": 0.04,
        
        # Formasyon göstergeleri
        "candlestick_patterns": 0.06,
        "chart_patterns": 0.04,
        
        # Risk & Temel
        "risk_adjusted": 0.04,
        "fundamental": 0.04
    }
    
    # Trend piyasası ağırlıkları
    TRENDING_WEIGHTS = {
        "ichimoku": 0.15,
        "supertrend": 0.12,
        "ma_cross": 0.10,
        "adx": 0.10,
        "rsi": 0.08,
        "macd": 0.10,
        "stochastic": 0.05,
        "momentum_divergence": 0.06,
        "bollinger": 0.06,
        "atr": 0.03,
        "vwap": 0.04,
        "volume_profile": 0.03,
        "obv": 0.03,
        "candlestick_patterns": 0.03,
        "chart_patterns": 0.02,
        "risk_adjusted": 0.02,
        "fundamental": 0.02
    }
    
    # Yatay piyasa ağırlıkları
    RANGING_WEIGHTS = {
        "ichimoku": 0.06,
        "supertrend": 0.04,
        "ma_cross": 0.04,
        "adx": 0.04,
        "rsi": 0.14,
        "macd": 0.08,
        "stochastic": 0.12,
        "momentum_divergence": 0.10,
        "bollinger": 0.12,
        "atr": 0.04,
        "vwap": 0.06,
        "volume_profile": 0.06,
        "obv": 0.04,
        "candlestick_patterns": 0.04,
        "chart_patterns": 0.02,
        "risk_adjusted": 0.02,
        "fundamental": 0.02
    }
    
    # Volatil piyasa ağırlıkları
    VOLATILE_WEIGHTS = {
        "ichimoku": 0.08,
        "supertrend": 0.10,
        "ma_cross": 0.06,
        "adx": 0.08,
        "rsi": 0.08,
        "macd": 0.08,
        "stochastic": 0.06,
        "momentum_divergence": 0.08,
        "bollinger": 0.10,
        "atr": 0.08,
        "vwap": 0.06,
        "volume_profile": 0.04,
        "obv": 0.04,
        "candlestick_patterns": 0.04,
        "chart_patterns": 0.02,
        "risk_adjusted": 0.06,
        "fundamental": 0.02
    }
    
    @staticmethod
    def get_weights(market_condition: str = "default") -> Dict[str, float]:
        """Piyasa koşuluna göre ağırlıkları getir"""
        if market_condition == "trending":
            return SignalWeights.TRENDING_WEIGHTS.copy()
        elif market_condition == "ranging":
            return SignalWeights.RANGING_WEIGHTS.copy()
        elif market_condition == "volatile":
            return SignalWeights.VOLATILE_WEIGHTS.copy()
        else:
            return SignalWeights.DEFAULT_WEIGHTS.copy()


class AISignalCombiner:
    """
    AI Sinyal Birleştirici
    =======================
    Tüm gösterge sinyallerini akıllıca birleştirir
    """
    
    # Sinyal değerleri
    SIGNAL_VALUES = {
        SignalType.STRONG_BUY: 100,
        SignalType.BUY: 70,
        SignalType.NEUTRAL: 50,
        SignalType.SELL: 30,
        SignalType.STRONG_SELL: 0
    }
    
    @staticmethod
    def combine_signals(
        signals: List[IndicatorSignal],
        market_condition: str = "default"
    ) -> Dict[str, Any]:
        """
        Sinyalleri birleştir
        
        Args:
            signals: Gösterge sinyalleri listesi
            market_condition: Piyasa koşulu ('trending', 'ranging', 'volatile', 'default')
            
        Returns:
            Birleştirilmiş sinyal ve detaylar
        """
        if not signals:
            return {
                "combined_signal": SignalType.NEUTRAL.value,
                "score": 50,
                "confidence": 0,
                "error": "sinyal_yok"
            }
        
        # Ağırlıkları al
        weights = SignalWeights.get_weights(market_condition)
        
        # Ağırlıklı skor hesapla
        total_weight = 0
        weighted_score = 0
        confidences = []
        
        signal_breakdown = []
        
        for signal in signals:
            indicator_name = signal.name.lower().replace(" ", "_")
            weight = weights.get(indicator_name, 0.05)
            
            # Sinyal değerini al
            signal_value = AISignalCombiner.SIGNAL_VALUES.get(signal.signal, 50)
            
            # Güç ve güvenle ayarla
            adjusted_value = signal_value * (signal.strength / 100) * signal.confidence
            
            weighted_score += adjusted_value * weight
            total_weight += weight
            confidences.append(signal.confidence)
            
            signal_breakdown.append({
                "indicator": signal.name,
                "signal": signal.signal.value,
                "strength": signal.strength,
                "weight": round(weight, 3),
                "contribution": round(adjusted_value * weight, 2)
            })
        
        # Normalize et
        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            final_score = 50
        
        # Ortalama güven
        avg_confidence = np.mean(confidences) if confidences else 0
        
        # Sinyal uyumu (standart sapma düşükse uyum yüksek)
        signal_values = [AISignalCombiner.SIGNAL_VALUES.get(s.signal, 50) for s in signals]
        signal_agreement = 1 - (np.std(signal_values) / 50) if len(signal_values) > 1 else 1
        signal_agreement = max(0, min(1, signal_agreement))
        
        # Final güven = ortalama güven * sinyal uyumu
        final_confidence = avg_confidence * signal_agreement
        
        # Birleşik sinyal belirleme
        combined_signal = AISignalCombiner._score_to_signal(final_score, final_confidence)
        
        # Sinyal gücü
        if final_score >= 80 or final_score <= 20:
            signal_strength = "çok_güçlü"
        elif final_score >= 65 or final_score <= 35:
            signal_strength = "güçlü"
        elif final_score >= 55 or final_score <= 45:
            signal_strength = "orta"
        else:
            signal_strength = "zayıf"
        
        return {
            "combined_signal": combined_signal.value,
            "score": round(final_score, 1),
            "confidence": round(final_confidence * 100, 1),
            "signal_strength": signal_strength,
            "signal_agreement": round(signal_agreement * 100, 1),
            "market_condition": market_condition,
            "signal_count": len(signals),
            "bullish_signals": sum(1 for s in signals if s.signal in [SignalType.BUY, SignalType.STRONG_BUY]),
            "bearish_signals": sum(1 for s in signals if s.signal in [SignalType.SELL, SignalType.STRONG_SELL]),
            "neutral_signals": sum(1 for s in signals if s.signal == SignalType.NEUTRAL),
            "breakdown": signal_breakdown
        }
    
    @staticmethod
    def _score_to_signal(score: float, confidence: float) -> SignalType:
        """Skoru sinyale çevir"""
        # Düşük güvenle daha nötr ol
        if confidence < 0.4:
            if score >= 70:
                return SignalType.BUY
            elif score <= 30:
                return SignalType.SELL
            else:
                return SignalType.NEUTRAL
        
        # Normal değerlendirme
        if score >= 80:
            return SignalType.STRONG_BUY
        elif score >= 60:
            return SignalType.BUY
        elif score <= 20:
            return SignalType.STRONG_SELL
        elif score <= 40:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL


class ConfidenceCalculator:
    """
    Güven Skoru Hesaplayıcı
    =======================
    Her göstergenin güvenilirliğini hesaplar
    """
    
    @staticmethod
    def calculate_indicator_confidence(
        indicator_name: str,
        current_value: float,
        historical_accuracy: float = None,
        market_condition: str = "default",
        data_quality: float = 1.0
    ) -> float:
        """
        Gösterge güven skoru hesapla
        
        Args:
            indicator_name: Gösterge adı
            current_value: Göstergenin mevcut değeri
            historical_accuracy: Tarihsel doğruluk (backtest sonucu)
            market_condition: Piyasa koşulu
            data_quality: Veri kalitesi (0-1)
            
        Returns:
            Güven skoru (0-1)
        """
        base_confidence = 0.5
        
        # 1. Aşırı değerlerde güven artar
        extreme_bonus = ConfidenceCalculator._get_extreme_value_bonus(
            indicator_name, current_value
        )
        
        # 2. Piyasa koşuluna uygunluk
        condition_factor = ConfidenceCalculator._get_condition_factor(
            indicator_name, market_condition
        )
        
        # 3. Tarihsel doğruluk (varsa)
        if historical_accuracy is not None:
            history_factor = historical_accuracy
        else:
            history_factor = 0.6  # Varsayılan
        
        # 4. Veri kalitesi
        quality_factor = data_quality
        
        # Final güven
        confidence = (base_confidence + extreme_bonus) * condition_factor * history_factor * quality_factor
        
        return max(0.1, min(1.0, confidence))
    
    @staticmethod
    def _get_extreme_value_bonus(indicator_name: str, value: float) -> float:
        """Aşırı değer bonusu"""
        indicator = indicator_name.lower()
        
        if "rsi" in indicator:
            if value <= 20 or value >= 80:
                return 0.3
            elif value <= 30 or value >= 70:
                return 0.2
        
        elif "stochastic" in indicator or "stoch" in indicator:
            if value <= 15 or value >= 85:
                return 0.3
            elif value <= 25 or value >= 75:
                return 0.2
        
        elif "bollinger" in indicator or "bb" in indicator:
            # BB position (0-1 arası)
            if value <= 0.1 or value >= 0.9:
                return 0.3
            elif value <= 0.2 or value >= 0.8:
                return 0.2
        
        elif "adx" in indicator:
            if value >= 40:
                return 0.3
            elif value >= 30:
                return 0.2
            elif value < 20:
                return -0.1  # Zayıf trend = düşük güven
        
        return 0
    
    @staticmethod
    def _get_condition_factor(indicator_name: str, market_condition: str) -> float:
        """Piyasa koşuluna uygunluk faktörü"""
        indicator = indicator_name.lower()
        
        # Trend göstergeleri trend piyasasında daha güvenilir
        trend_indicators = ["ichimoku", "supertrend", "ma", "adx", "macd"]
        
        # Momentum göstergeleri yatay piyasada daha güvenilir
        momentum_indicators = ["rsi", "stochastic", "bollinger"]
        
        if market_condition == "trending":
            if any(t in indicator for t in trend_indicators):
                return 1.2
            elif any(m in indicator for m in momentum_indicators):
                return 0.8
        
        elif market_condition == "ranging":
            if any(m in indicator for m in momentum_indicators):
                return 1.2
            elif any(t in indicator for t in trend_indicators):
                return 0.8
        
        elif market_condition == "volatile":
            if "atr" in indicator or "volatility" in indicator:
                return 1.2
            elif "bollinger" in indicator:
                return 1.1
        
        return 1.0


class SignalGenerator:
    """
    Sinyal Üretici
    ==============
    Ham gösterge verilerinden sinyal üretir
    """
    
    @staticmethod
    def generate_rsi_signal(rsi_value: float, rsi_prev: float = None) -> IndicatorSignal:
        """RSI sinyali üret"""
        if rsi_value <= 20:
            signal = SignalType.STRONG_BUY
            strength = 90
        elif rsi_value <= 30:
            signal = SignalType.BUY
            strength = 70
        elif rsi_value >= 80:
            signal = SignalType.STRONG_SELL
            strength = 90
        elif rsi_value >= 70:
            signal = SignalType.SELL
            strength = 70
        else:
            signal = SignalType.NEUTRAL
            strength = 50
        
        # Momentum değişimi (varsa)
        if rsi_prev is not None:
            if rsi_value > rsi_prev and rsi_value < 50:
                strength += 10  # Toparlanma
            elif rsi_value < rsi_prev and rsi_value > 50:
                strength -= 10  # Zayıflama
        
        confidence = ConfidenceCalculator.calculate_indicator_confidence(
            "rsi", rsi_value
        )
        
        return IndicatorSignal(
            name="RSI",
            signal=signal,
            strength=min(100, strength),
            weight=0.10,
            confidence=confidence,
            data={"value": rsi_value}
        )
    
    @staticmethod
    def generate_macd_signal(
        macd: float, signal_line: float, histogram: float, prev_histogram: float = None
    ) -> IndicatorSignal:
        """MACD sinyali üret"""
        strength = 50
        
        if histogram > 0 and macd > signal_line:
            if prev_histogram is not None and histogram > prev_histogram:
                signal = SignalType.STRONG_BUY
                strength = 85
            else:
                signal = SignalType.BUY
                strength = 70
        elif histogram < 0 and macd < signal_line:
            if prev_histogram is not None and histogram < prev_histogram:
                signal = SignalType.STRONG_SELL
                strength = 85
            else:
                signal = SignalType.SELL
                strength = 70
        else:
            signal = SignalType.NEUTRAL
            strength = 50
        
        # Kesişim kontrolü
        if prev_histogram is not None:
            if prev_histogram < 0 and histogram > 0:
                signal = SignalType.STRONG_BUY
                strength = 90
            elif prev_histogram > 0 and histogram < 0:
                signal = SignalType.STRONG_SELL
                strength = 90
        
        confidence = ConfidenceCalculator.calculate_indicator_confidence(
            "macd", abs(histogram)
        )
        
        return IndicatorSignal(
            name="MACD",
            signal=signal,
            strength=strength,
            weight=0.10,
            confidence=confidence,
            data={"macd": macd, "signal": signal_line, "histogram": histogram}
        )
    
    @staticmethod
    def generate_ichimoku_signal(ichimoku_data: Dict[str, Any]) -> IndicatorSignal:
        """Ichimoku sinyali üret"""
        signal_str = ichimoku_data.get("signal", "BEKLE")
        strength = ichimoku_data.get("strength", 0)
        
        # String sinyali enum'a çevir
        if "GÜÇLÜ AL" in signal_str:
            signal = SignalType.STRONG_BUY
        elif "AL" in signal_str:
            signal = SignalType.BUY
        elif "GÜÇLÜ SAT" in signal_str:
            signal = SignalType.STRONG_SELL
        elif "SAT" in signal_str:
            signal = SignalType.SELL
        else:
            signal = SignalType.NEUTRAL
        
        # Güç skorunu normalize et (-100 to 100 -> 0 to 100)
        normalized_strength = (strength + 100) / 2
        
        confidence = ConfidenceCalculator.calculate_indicator_confidence(
            "ichimoku", abs(strength)
        )
        
        return IndicatorSignal(
            name="Ichimoku",
            signal=signal,
            strength=normalized_strength,
            weight=0.12,
            confidence=confidence,
            data=ichimoku_data
        )
    
    @staticmethod
    def generate_bollinger_signal(bb_position: float, price_vs_band: str) -> IndicatorSignal:
        """Bollinger Bands sinyali üret"""
        if bb_position <= 0.1:
            signal = SignalType.STRONG_BUY
            strength = 85
        elif bb_position <= 0.25:
            signal = SignalType.BUY
            strength = 70
        elif bb_position >= 0.9:
            signal = SignalType.STRONG_SELL
            strength = 85
        elif bb_position >= 0.75:
            signal = SignalType.SELL
            strength = 70
        else:
            signal = SignalType.NEUTRAL
            strength = 50
        
        confidence = ConfidenceCalculator.calculate_indicator_confidence(
            "bollinger", bb_position
        )
        
        return IndicatorSignal(
            name="Bollinger",
            signal=signal,
            strength=strength,
            weight=0.08,
            confidence=confidence,
            data={"position": bb_position, "price_vs_band": price_vs_band}
        )
    
    @staticmethod
    def generate_candlestick_signal(pattern_data: Dict[str, Any]) -> IndicatorSignal:
        """Mum formasyonu sinyali üret"""
        signal_str = pattern_data.get("signal", "BEKLE")
        strength = pattern_data.get("strength", 50)
        
        if "GÜÇLÜ AL" in signal_str:
            signal = SignalType.STRONG_BUY
        elif "AL" in signal_str:
            signal = SignalType.BUY
        elif "GÜÇLÜ SAT" in signal_str:
            signal = SignalType.STRONG_SELL
        elif "SAT" in signal_str:
            signal = SignalType.SELL
        else:
            signal = SignalType.NEUTRAL
        
        # Formasyon sayısı ve güvenilirliği
        pattern_count = pattern_data.get("pattern_count", 0)
        confidence = min(0.9, 0.4 + pattern_count * 0.1)
        
        if pattern_data.get("volume_confirmed"):
            confidence *= 1.2
        
        return IndicatorSignal(
            name="Candlestick_Patterns",
            signal=signal,
            strength=strength,
            weight=0.06,
            confidence=min(1.0, confidence),
            data=pattern_data
        )
    
    @staticmethod
    def generate_divergence_signal(divergence_data: Dict[str, Any]) -> IndicatorSignal:
        """Diverjans sinyali üret"""
        divergence_type = divergence_data.get("divergence", "none")
        strength = divergence_data.get("strength", 50)
        
        if divergence_type in ["bullish", "hidden_bullish"]:
            signal = SignalType.BUY
            if strength > 70:
                signal = SignalType.STRONG_BUY
        elif divergence_type in ["bearish", "hidden_bearish"]:
            signal = SignalType.SELL
            if strength > 70:
                signal = SignalType.STRONG_SELL
        else:
            signal = SignalType.NEUTRAL
            strength = 30
        
        # Klasik diverjans daha güvenilir
        confidence = 0.7 if "hidden" not in divergence_type else 0.55
        if divergence_type == "none":
            confidence = 0.3
        
        return IndicatorSignal(
            name="Momentum_Divergence",
            signal=signal,
            strength=strength,
            weight=0.08,
            confidence=confidence,
            data=divergence_data
        )


class ProSignalSystem:
    """
    Pro Sinyal Sistemi
    ==================
    Tüm göstergeleri birleştiren ana sistem
    """
    
    @staticmethod
    def generate_comprehensive_signal(
        indicators: Dict[str, Any],
        market_condition: str = "default"
    ) -> Dict[str, Any]:
        """
        Kapsamlı sinyal üret
        
        Args:
            indicators: Tüm gösterge verileri
            market_condition: Piyasa koşulu
            
        Returns:
            Birleşik sinyal ve tüm detaylar
        """
        signals = []
        
        # RSI
        if "rsi" in indicators:
            rsi_signal = SignalGenerator.generate_rsi_signal(
                indicators["rsi"],
                indicators.get("rsi_prev")
            )
            signals.append(rsi_signal)
        
        # MACD
        if all(k in indicators for k in ["macd", "macd_signal", "macd_histogram"]):
            macd_signal = SignalGenerator.generate_macd_signal(
                indicators["macd"],
                indicators["macd_signal"],
                indicators["macd_histogram"],
                indicators.get("macd_histogram_prev")
            )
            signals.append(macd_signal)
        
        # Ichimoku
        if "ichimoku" in indicators:
            ichimoku_signal = SignalGenerator.generate_ichimoku_signal(
                indicators["ichimoku"]
            )
            signals.append(ichimoku_signal)
        
        # Bollinger
        if "bb_position" in indicators:
            bb_signal = SignalGenerator.generate_bollinger_signal(
                indicators["bb_position"],
                indicators.get("price_vs_bb", "middle")
            )
            signals.append(bb_signal)
        
        # Mum formasyonları
        if "candlestick_patterns" in indicators:
            candle_signal = SignalGenerator.generate_candlestick_signal(
                indicators["candlestick_patterns"]
            )
            signals.append(candle_signal)
        
        # Diverjans
        if "divergence" in indicators:
            div_signal = SignalGenerator.generate_divergence_signal(
                indicators["divergence"]
            )
            signals.append(div_signal)
        
        # Sinyalleri birleştir
        combined = AISignalCombiner.combine_signals(signals, market_condition)
        
        # Ek analizler
        combined["risk_level"] = ProSignalSystem._assess_risk_level(indicators, combined)
        combined["entry_timing"] = ProSignalSystem._assess_entry_timing(indicators, combined)
        combined["recommendation"] = ProSignalSystem._generate_recommendation(combined)
        
        return combined
    
    @staticmethod
    def _assess_risk_level(indicators: Dict, combined: Dict) -> str:
        """Risk seviyesi değerlendir"""
        risk_factors = 0
        
        # Volatilite
        atr_pct = indicators.get("atr_percent", 2)
        if atr_pct > 4:
            risk_factors += 2
        elif atr_pct > 3:
            risk_factors += 1
        
        # Sinyal uyumsuzluğu
        agreement = combined.get("signal_agreement", 100)
        if agreement < 50:
            risk_factors += 2
        elif agreement < 70:
            risk_factors += 1
        
        # Düşük güven
        confidence = combined.get("confidence", 50)
        if confidence < 40:
            risk_factors += 2
        elif confidence < 60:
            risk_factors += 1
        
        if risk_factors >= 4:
            return "çok_yüksek"
        elif risk_factors >= 3:
            return "yüksek"
        elif risk_factors >= 2:
            return "orta"
        else:
            return "düşük"
    
    @staticmethod
    def _assess_entry_timing(indicators: Dict, combined: Dict) -> str:
        """Giriş zamanlaması değerlendir"""
        score = combined.get("score", 50)
        confidence = combined.get("confidence", 50)
        
        # Güçlü sinyal ve yüksek güven
        if score >= 75 and confidence >= 70:
            return "mükemmel"
        elif score >= 65 and confidence >= 60:
            return "iyi"
        elif score <= 25 and confidence >= 70:
            return "mükemmel_satış"
        elif score <= 35 and confidence >= 60:
            return "iyi_satış"
        elif 40 <= score <= 60:
            return "bekle"
        else:
            return "orta"
    
    @staticmethod
    def _generate_recommendation(combined: Dict) -> str:
        """Öneri oluştur"""
        signal = combined.get("combined_signal", "NÖTR")
        confidence = combined.get("confidence", 50)
        risk = combined.get("risk_level", "orta")
        timing = combined.get("entry_timing", "orta")
        
        if "GÜÇLÜ AL" in signal and confidence >= 70 and risk in ["düşük", "orta"]:
            return "Güçlü alım fırsatı! Pozisyon açılabilir."
        elif "AL" in signal and confidence >= 60:
            return "Alım düşünülebilir. Stop-loss ile giriş yapın."
        elif "GÜÇLÜ SAT" in signal and confidence >= 70:
            return "Güçlü satış sinyali! Pozisyondan çıkış önerilir."
        elif "SAT" in signal and confidence >= 60:
            return "Satış düşünülebilir. Pozisyon küçültün."
        elif risk == "çok_yüksek":
            return "Risk çok yüksek! İşlem yapmayın."
        elif timing == "bekle":
            return "Net sinyal yok. Bekleyin."
        else:
            return "Piyasayı izleyin. Henüz net fırsat yok."
