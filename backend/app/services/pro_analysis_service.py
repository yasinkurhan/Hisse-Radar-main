"""
HisseRadar Pro Analiz Servisi
==============================
Tüm gelişmiş analiz modüllerini birleştiren ana servis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time

from ..config import get_settings
from .borsapy_fetcher import get_borsapy_fetcher

# Pro Modüller
from .pro_indicators import (
    IchimokuCloud, VWAPAnalysis, VolumeProfile, 
    MomentumDivergence, SuperTrend, MarketRegime
)
from .candlestick_patterns import CandlestickPatterns, CandleAnalyzer
from .risk_analysis import RiskMetrics, RiskAnalyzer, PositionSizing
from .market_analysis import MarketBreadth, SectorRotation, MarketSentiment, MarketAnalyzer
from .ai_signal_combiner import (
    ProSignalSystem, AISignalCombiner, SignalGenerator, 
    IndicatorSignal, SignalType
)
from .advanced_indicators import AdvancedIndicators, PatternRecognition


def convert_numpy_types(obj):
    """NumPy tiplerini Python tiplerine dönüştür (JSON serialization için)"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj


class ProAnalysisService:
    """
    Pro Analiz Servisi
    ==================
    Gelişmiş teknik analiz, risk yönetimi ve AI sinyal birleştirme
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._load_stock_list()
        self._failed_stocks = []
    
    def _load_stock_list(self) -> None:
        """Hisse listesini yükle"""
        try:
            data_path = Path(__file__).parent.parent / "data" / "bist_stocks.json"
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._stocks = data.get("stocks", [])
        except FileNotFoundError:
            self._stocks = []
    
    def _clean_symbol(self, symbol: str) -> str:
        """Sembolü temizle"""
        return symbol.upper().strip().replace(".IS", "")
    
    def get_pro_analysis(self, symbol: str, period: str = "6mo") -> Dict[str, Any]:
        """
        Tek hisse için kapsamlı pro analiz
        
        Args:
            symbol: Hisse sembolü
            period: Veri periyodu
            
        Returns:
            Tüm pro analiz sonuçları
        """
        try:
            clean_symbol = self._clean_symbol(symbol)
            fetcher = get_borsapy_fetcher()
            
            # Günlük ve haftalık veri al
            df_daily = fetcher.get_history(clean_symbol, period=period, interval="1d")
            
            if df_daily is None or df_daily.empty or len(df_daily) < 50:
                return {"error": "Yetersiz veri", "symbol": symbol}
            
            # DataFrame hazırla
            if df_daily.index.tz is not None:
                df_daily.index = df_daily.index.tz_convert(None)
            
            open_prices = df_daily["open"] if "open" in df_daily.columns else df_daily.get("Open", pd.Series())
            high = df_daily["high"] if "high" in df_daily.columns else df_daily["High"]
            low = df_daily["low"] if "low" in df_daily.columns else df_daily["Low"]
            close = df_daily["close"] if "close" in df_daily.columns else df_daily["Close"]
            volume = df_daily["volume"] if "volume" in df_daily.columns else df_daily["Volume"]
            
            current_price = float(close.iloc[-1])
            
            # 1. ICHIMOKU ANALİZİ
            ichimoku = IchimokuCloud.calculate(high, low, close)
            
            # 2. VWAP ANALİZİ
            vwap = VWAPAnalysis.calculate(high, low, close, volume, period=20)
            
            # 3. HACİM PROFİLİ
            volume_profile = VolumeProfile.calculate(high, low, close, volume, lookback=50)
            
            # 4. SUPERTREND
            supertrend = SuperTrend.calculate(high, low, close)
            
            # 5. PİYASA REJİMİ
            market_regime = MarketRegime.detect(close, high, low, volume)
            
            # 6. RSI VE RSI DİVERJANS
            rsi_series = self._calculate_rsi_series(close)
            rsi_divergence = MomentumDivergence.detect_rsi_divergence(close, rsi_series)
            
            # 7. MACD VE MACD DİVERJANS
            macd_data = self._calculate_macd_series(close)
            macd_divergence = MomentumDivergence.detect_macd_divergence(
                close, macd_data["histogram"]
            )
            
            # 8. MUM FORMASYONLARI
            candlestick_analysis = CandleAnalyzer.full_analysis(
                open_prices, high, low, close, volume
            )
            
            # 9. GELİŞMİŞ GÖSTERGELER
            adx = AdvancedIndicators.calculate_adx(high, low, close)
            fibonacci = AdvancedIndicators.calculate_fibonacci_levels(high, low, close)
            obv = AdvancedIndicators.calculate_obv(close, volume)
            support_resistance = AdvancedIndicators.calculate_support_resistance(high, low, close)
            
            # 10. GRAFİK FORMASYONLARI
            chart_patterns = PatternRecognition.detect_patterns(high, low, close)
            
            # 11. RİSK ANALİZİ
            risk_analysis = RiskAnalyzer.full_risk_analysis(close)
            
            # 12. POZİSYON BOYUTLANDIRMA ÖNERİSİ
            position_advice = self._calculate_position_advice(
                current_price, 
                risk_analysis, 
                support_resistance
            )
            
            # 13. AI SİNYAL BİRLEŞTİRME
            indicators_for_ai = {
                "rsi": float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50,
                "rsi_prev": float(rsi_series.iloc[-2]) if len(rsi_series) > 1 else None,
                "macd": float(macd_data["macd"].iloc[-1]),
                "macd_signal": float(macd_data["signal"].iloc[-1]),
                "macd_histogram": float(macd_data["histogram"].iloc[-1]),
                "macd_histogram_prev": float(macd_data["histogram"].iloc[-2]) if len(macd_data["histogram"]) > 1 else None,
                "ichimoku": ichimoku,
                "bb_position": self._calculate_bb_position(close),
                "candlestick_patterns": candlestick_analysis["patterns"],
                "divergence": rsi_divergence,
                "atr_percent": (self._calculate_atr(high, low, close) / current_price) * 100
            }
            
            # Piyasa koşulunu belirle
            market_condition = self._determine_market_condition(market_regime)
            
            # AI sinyal üret
            ai_signal = ProSignalSystem.generate_comprehensive_signal(
                indicators_for_ai, 
                market_condition
            )
            
            # Hisse bilgisi
            stock_info = next((s for s in self._stocks if s["symbol"] == symbol), {})
            
            result = {
                "symbol": symbol,
                "name": stock_info.get("name", symbol),
                "sector": stock_info.get("sector", ""),
                "current_price": round(current_price, 2),
                "analysis_timestamp": datetime.now().isoformat(),
                
                # AI Birleşik Sinyal
                "ai_signal": ai_signal,
                
                # Pro Göstergeler
                "pro_indicators": {
                    "ichimoku": ichimoku,
                    "vwap": vwap,
                    "volume_profile": volume_profile,
                    "supertrend": supertrend,
                    "market_regime": market_regime
                },
                
                # Diverjans Analizi
                "divergence_analysis": {
                    "rsi_divergence": rsi_divergence,
                    "macd_divergence": macd_divergence
                },
                
                # Mum Analizi
                "candlestick_analysis": candlestick_analysis,
                
                # Gelişmiş Göstergeler
                "advanced_indicators": {
                    "adx": adx,
                    "fibonacci": fibonacci,
                    "obv": obv,
                    "support_resistance": support_resistance
                },
                
                # Grafik Formasyonları
                "chart_patterns": chart_patterns,
                
                # Risk Analizi
                "risk_analysis": risk_analysis,
                
                # Pozisyon Önerisi
                "position_advice": position_advice
            }
            
            return convert_numpy_types(result)
            
        except Exception as e:
            return {
                "error": str(e),
                "symbol": symbol
            }
    
    def _fetch_bulk_history(self, symbols: List[str], period: str = "5d") -> Dict[str, pd.DataFrame]:
        """Toplu veri indir (borsapy)"""
        results: Dict[str, pd.DataFrame] = {}
        fetcher = get_borsapy_fetcher()

        for symbol in symbols:
            clean_symbol = self._clean_symbol(symbol)
            try:
                stock_df = fetcher.get_history(clean_symbol, period=period, interval="1d")
                if stock_df is None or stock_df.empty:
                    continue

                stock_df.columns = [str(c).lower() for c in stock_df.columns]
                results[symbol] = stock_df
            except Exception:
                continue

        return results

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Piyasa genel görünümü
        
        Returns:
            Piyasa genişliği, sektör analizi, duyarlılık
        """
        try:
            # İlk 100 hisse için bulk veri çek
            target_stocks = self._stocks[:100]
            symbols = [s["symbol"] for s in target_stocks]
            
            bulk_data = self._fetch_bulk_history(symbols, period="5d")
            
            stocks_data = []
            
            for stock in target_stocks:
                symbol = stock["symbol"]
                if symbol not in bulk_data:
                    continue
                    
                df = bulk_data[symbol]
                
                try:
                    if len(df) >= 2:
                        c_col = "close" if "close" in df.columns else "Close"
                        v_col = "volume" if "volume" in df.columns else "Volume"
                        
                        current = float(df[c_col].iloc[-1])
                        prev = float(df[c_col].iloc[-2])
                        change_pct = ((current - prev) / prev) * 100
                        
                        vol = float(df[v_col].iloc[-1])
                        avg_vol = float(df[v_col].mean())
                        
                        stocks_data.append({
                            "symbol": symbol,
                            "sector": stock.get("sector", "Diğer"),
                            "current_price": current,
                            "change_percent": change_pct,
                            "volume": vol,
                            "volume_ratio": vol / avg_vol if avg_vol > 0 else 1
                        })
                except Exception:
                    continue
            
            if not stocks_data:
                return {"error": "Veri alınamadı"}
            
            # Piyasa analizi
            market_analysis = MarketAnalyzer.full_market_analysis(stocks_data)
            
            return convert_numpy_types({
                "analysis_timestamp": datetime.now().isoformat(),
                "stocks_analyzed": len(stocks_data),
                **market_analysis
            })
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_sector_analysis(self) -> Dict[str, Any]:
        """Sektör rotasyonu analizi"""
        try:
            # Tüm hisseleri çek
            symbols = [s["symbol"] for s in self._stocks]
            
            # Batch
            batch_size = 100
            all_stocks_data = []
            
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i+batch_size]
                # 3 aylık veri çek (1 ay ve 1 hafta değişimi için)
                bulk_data = self._fetch_bulk_history(batch_symbols, period="3mo")
                
                for symbol in batch_symbols:
                    if symbol not in bulk_data:
                        continue
                        
                    df = bulk_data[symbol]
                    stock_info = next((s for s in self._stocks if s["symbol"] == symbol), {})
                    
                    try:
                        if len(df) >= 2:
                            c_col = "close" if "close" in df.columns else "Close"
                            v_col = "volume" if "volume" in df.columns else "Volume"
                            
                            current = float(df[c_col].iloc[-1])
                            prev_1d = float(df[c_col].iloc[-2])
                            
                            # 1 Haftalık (5 işlem günü)
                            prev_1w = float(df[c_col].iloc[-6]) if len(df) >= 6 else prev_1d
                            
                            # 1 Aylık (22 işlem günü)
                            prev_1m = float(df[c_col].iloc[-22]) if len(df) >= 22 else float(df[c_col].iloc[0])
                            
                            all_stocks_data.append({
                                "symbol": symbol,
                                "sector": stock_info.get("sector", "Diğer"),
                                "change_percent": ((current - prev_1d) / prev_1d) * 100,
                                "change_1w": ((current - prev_1w) / prev_1w) * 100,
                                "change_1m": ((current - prev_1m) / prev_1m) * 100,
                                "volume": float(df[v_col].iloc[-1])
                            })
                    except:
                        continue
            
            if not all_stocks_data:
                return {"error": "Veri alınamadı"}

            return convert_numpy_types(SectorRotation.analyze_sector_performance(all_stocks_data))
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_risk_report(self, symbol: str) -> Dict[str, Any]:
        """
        Detaylı risk raporu
        
        Args:
            symbol: Hisse sembolü
            
        Returns:
            Kapsamlı risk analizi
        """
        try:
            clean_symbol = self._clean_symbol(symbol)
            fetcher = get_borsapy_fetcher()
            df = fetcher.get_history(clean_symbol, period="1y", interval="1d")
            
            if df is None or len(df) < 100:
                return {"error": "Yetersiz veri"}
            
            c_col = "close" if "close" in df.columns else "Close"
            close = df[c_col]
            
            # Risk analizi
            risk_analysis = RiskAnalyzer.full_risk_analysis(close)
            
            # XU100 ile karşılaştırma (Beta hesabı için)
            try:
                xu100_df = fetcher.get_index_history("XU100", period="1y")
                if xu100_df is not None and len(xu100_df) > 100:
                    xu_c_col = "close" if "close" in xu100_df.columns else "Close"
                    market_returns = RiskMetrics.calculate_returns(xu100_df[xu_c_col])
                    stock_returns = RiskMetrics.calculate_returns(close)
                    beta = RiskMetrics.calculate_beta(stock_returns, market_returns)
                    risk_analysis["beta_analysis"] = beta
            except:
                pass
            
            # Pozisyon boyutlandırma önerisi
            current_price = float(close.iloc[-1])
            
            kelly = PositionSizing.kelly_criterion(
                win_rate=0.55,  # Varsayılan
                avg_win=0.08,
                avg_loss=0.05
            )
            
            return convert_numpy_types({
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "risk_analysis": risk_analysis,
                "position_sizing": kelly,
                "analysis_timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return {"error": str(e)}
    
    # Yardımcı metodlar
    def _calculate_rsi_series(self, close: pd.Series, period: int = 14) -> pd.Series:
        """RSI serisi hesapla"""
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd_series(self, close: pd.Series) -> Dict[str, pd.Series]:
        """MACD serisi hesapla"""
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def _calculate_bb_position(self, close: pd.Series, period: int = 20) -> float:
        """Bollinger pozisyonu hesapla"""
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        current = close.iloc[-1]
        band_width = upper.iloc[-1] - lower.iloc[-1]
        if band_width > 0:
            return float((current - lower.iloc[-1]) / band_width)
        return 0.5
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """ATR hesapla"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
    
    def _determine_market_condition(self, regime: Dict) -> str:
        """Piyasa koşulunu belirle"""
        regime_type = regime.get("regime", "karma")
        
        if "yükseliş" in regime_type or "düşüş" in regime_type:
            return "trending"
        elif "volatilite" in regime_type:
            return "volatile"
        elif "yatay" in regime_type:
            return "ranging"
        return "default"
    
    def _calculate_position_advice(
        self, 
        current_price: float, 
        risk_analysis: Dict,
        support_resistance: Dict
    ) -> Dict[str, Any]:
        """Pozisyon önerisi hesapla"""
        
        # Risk seviyesine göre pozisyon büyüklüğü önerisi
        risk_score = risk_analysis.get("risk_score", 50)
        
        if risk_score >= 70:
            position_pct = 2  # Çok riskli = küçük pozisyon
            advice = "Küçük pozisyon veya işlem yapma"
        elif risk_score >= 50:
            position_pct = 5
            advice = "Dikkatli pozisyon al"
        else:
            position_pct = 10
            advice = "Normal pozisyon alınabilir"
        
        # Stop loss önerisi
        nearest_support = support_resistance.get("nearest_support", current_price * 0.95)
        stop_loss = min(nearest_support * 0.98, current_price * 0.92)
        
        # Hedef fiyat önerisi
        nearest_resistance = support_resistance.get("nearest_resistance", current_price * 1.10)
        target = nearest_resistance
        
        risk_reward = (target - current_price) / (current_price - stop_loss) if current_price > stop_loss else 0
        
        return {
            "suggested_position_pct": position_pct,
            "advice": advice,
            "suggested_stop_loss": round(stop_loss, 2),
            "suggested_target": round(target, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "risk_level": risk_analysis.get("risk_level", "orta")
        }


# Singleton instance
_pro_analysis_service: Optional[ProAnalysisService] = None

def get_pro_analysis_service() -> ProAnalysisService:
    global _pro_analysis_service
    if _pro_analysis_service is None:
        _pro_analysis_service = ProAnalysisService()
    return _pro_analysis_service
