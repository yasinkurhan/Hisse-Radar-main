"""
HisseRadar Analiz Servisi
==========================
Günlük ve haftalık teknik analiz yaparak hisse önerileri üretir
borsapy kütüphanesi ile BIST verileri çeker
Haber ve Sentiment Analizi Entegrasyonu ile
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import random
import time
import asyncio

from ..config import get_settings, normalize_symbol
from .smart_scoring import BacktestEngine
from .borsapy_fetcher import get_borsapy_fetcher
from .real_news_service import GoogleNewsService, RealNewsAggregator
from .news_sentiment_service import SentimentAnalyzer

# Global backtest engine instance
_backtest_engine = None

def get_backtest_engine():
    global _backtest_engine
    if _backtest_engine is None:
        _backtest_engine = BacktestEngine()
    return _backtest_engine


class AnalysisService:
    def __init__(self):
        self.settings = get_settings()
        self._load_stock_list()
        self._failed_stocks = []  # Hata alan hisseleri takip et

    def _load_stock_list(self) -> None:
        try:
            data_path = Path(__file__).parent.parent / "data" / "bist_stocks.json"
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._stocks = data.get("stocks", [])
        except FileNotFoundError:
            self._stocks = []

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    def _calculate_macd(self, prices: pd.Series) -> Dict[str, float]:
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        ema12 = prices.ewm(span=12, adjust=False).mean()
        ema26 = prices.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Dict[str, float]:
        if len(prices) < period:
            return {"upper": 0, "middle": 0, "lower": 0, "position": 0.5}
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        current_price = prices.iloc[-1]
        band_width = upper.iloc[-1] - lower.iloc[-1]
        position = (current_price - lower.iloc[-1]) / band_width if band_width > 0 else 0.5
        return {
            "upper": float(upper.iloc[-1]),
            "middle": float(sma.iloc[-1]),
            "lower": float(lower.iloc[-1]),
            "position": float(position)
        }

    def _calculate_moving_averages(self, prices: pd.Series) -> Dict[str, float]:
        result = {}
        for period in [5, 10, 20, 50, 200]:
            if len(prices) >= period:
                result[f"sma{period}"] = float(prices.rolling(window=period).mean().iloc[-1])
                result[f"ema{period}"] = float(prices.ewm(span=period, adjust=False).mean().iloc[-1])
            else:
                result[f"sma{period}"] = None
                result[f"ema{period}"] = None
        return result

    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, float]:
        if len(close) < period:
            return {"k": 50, "d": 50}
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=3).mean()
        return {
            "k": float(k.iloc[-1]) if not pd.isna(k.iloc[-1]) else 50,
            "d": float(d.iloc[-1]) if not pd.isna(d.iloc[-1]) else 50
        }

    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        if len(close) < period + 1:
            return 0
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0

    def _calculate_volume_analysis(self, volume: pd.Series) -> Dict[str, Any]:
        if len(volume) < 20:
            return {"current": 0, "avg20": 0, "ratio": 1}
        avg20 = volume.rolling(window=20).mean().iloc[-1]
        current = volume.iloc[-1]
        ratio = current / avg20 if avg20 > 0 else 1
        return {
            "current": int(current),
            "avg20": int(avg20),
            "ratio": round(float(ratio), 2)
        }

    def _fetch_sentiment_sync(self, symbol: str, stock_name: str = None) -> Dict[str, Any]:
        """Senkron olarak sentiment verisi çek (feedparser ile direkt)"""
        try:
            import feedparser
            from urllib.parse import quote
            
            # bist_stocks.json'dan gelen ismi kullan, yoksa sembolü kullan
            if not stock_name:
                stock_info = next((s for s in self._stocks if s["symbol"] == symbol), None)
                stock_name = stock_info["name"] if stock_info else symbol
            search_query = f"{stock_name} hisse borsa"
            encoded_query = quote(search_query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
            
            # RSS feed'i parse et
            feed = feedparser.parse(url)
            
            if not feed.entries:
                return {
                    "score": 0,
                    "label": "Haber Yok",
                    "news_count": 0,
                    "positive": 0,
                    "negative": 0,
                    "has_data": False
                }
            
            # Basit sentiment analizi
            positive_words = ['yüksel', 'artı', 'kar', 'büyü', 'rekor', 'başarı', 'olumlu', 'güçlü', 'yatırım', 'talep']
            negative_words = ['düş', 'azal', 'zarar', 'kayıp', 'olumsuz', 'risk', 'kriz', 'endişe', 'darbe', 'iptal']
            
            total_score = 0
            positive_count = 0
            negative_count = 0
            news_count = min(len(feed.entries), 10)
            
            for entry in feed.entries[:10]:
                title = entry.get('title', '').lower()
                
                pos = sum(1 for w in positive_words if w in title)
                neg = sum(1 for w in negative_words if w in title)
                
                if pos > neg:
                    positive_count += 1
                    total_score += 0.3
                elif neg > pos:
                    negative_count += 1
                    total_score -= 0.3
            
            avg_score = total_score / news_count if news_count > 0 else 0
            
            if avg_score > 0.1:
                label = "📈 Olumlu"
            elif avg_score < -0.1:
                label = "📉 Olumsuz"
            else:
                label = "➖ Nötr"
            
            return {
                "score": round(avg_score, 3),
                "label": label,
                "news_count": news_count,
                "positive": positive_count,
                "negative": negative_count,
                "has_data": news_count > 0
            }
            
        except Exception as e:
            print(f"Sentiment hatası ({symbol}): {e}")
            return {
                "score": 0,
                "label": "Veri Yok",
                "news_count": 0,
                "positive": 0,
                "negative": 0,
                "has_data": False
            }

    def _calculate_score(self, rsi, macd, bollinger, mas, stochastic, current_price, vol_analysis, sentiment_data: Dict = None) -> int:
        score = 50
        if rsi < 30:
            score += 15
        elif rsi < 40:
            score += 8
        elif rsi > 70:
            score -= 15
        elif rsi > 60:
            score -= 8
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            score += 15
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            score -= 15
        elif macd["histogram"] > 0:
            score += 7
        elif macd["histogram"] < 0:
            score -= 7
        if bollinger["position"] < 0.2:
            score += 10
        elif bollinger["position"] > 0.8:
            score -= 10
        elif bollinger["position"] < 0.4:
            score += 5
        elif bollinger["position"] > 0.6:
            score -= 5
        if mas.get("sma20") and mas.get("sma50"):
            if current_price > mas["sma20"] > mas["sma50"]:
                score += 10
            elif current_price < mas["sma20"] < mas["sma50"]:
                score -= 10
            elif current_price > mas["sma20"]:
                score += 5
            elif current_price < mas["sma20"]:
                score -= 5
        if stochastic["k"] < 20 and stochastic["d"] < 20:
            score += 10
        elif stochastic["k"] > 80 and stochastic["d"] > 80:
            score -= 10
        elif stochastic["k"] < 30:
            score += 5
        elif stochastic["k"] > 70:
            score -= 5
        if vol_analysis["ratio"] > 1.5:
            if score > 50:
                score += 5
            else:
                score -= 5
        
        # SENTIMENT ETKİSİ (Haber Analizi)
        # Sentiment skoru -1 ile +1 arasında, toplam skora %10-15 katkı yapabilir
        if sentiment_data and sentiment_data.get("has_data"):
            sentiment_score = sentiment_data.get("score", 0)
            news_count = sentiment_data.get("news_count", 0)
            
            # Minimum 3 haber varsa sentiment etkisi uygula
            if news_count >= 3:
                # Sentiment etkisi: max ±10 puan
                sentiment_impact = int(sentiment_score * 10)
                
                # Çok güçlü sentiment varsa (>0.3 veya <-0.3) ekstra etki
                if sentiment_score > 0.3:
                    sentiment_impact += 3
                elif sentiment_score < -0.3:
                    sentiment_impact -= 3
                
                # Çok fazla olumlu/olumsuz haber varsa güçlendir
                if sentiment_data.get("positive", 0) >= 5:
                    sentiment_impact += 2
                elif sentiment_data.get("negative", 0) >= 5:
                    sentiment_impact -= 2
                
                score += sentiment_impact
        
        return max(0, min(100, score))

    def _calculate_potential(self, current_price, bollinger, mas, atr, analysis_type: str = "daily") -> Dict[str, Any]:
        """
        Hedef fiyat ve stop loss hesapla
        
        BIST Kurallari:
        - Gunluk tavan/taban limiti: %10
        - Gunluk analiz vadesi: 1 gun (bugun seans kapanisi -> yarin seans kapanisi)
        - Haftalik analiz vadesi: 1 hafta (Cuma kapanisi -> sonraki Cuma kapanisi, Pzt-Cum arasi)
        
        Hesaplama Yontemi:
        - ATR (Average True Range) bazli volatilite hesabi
        - Gunluk: ATR'nin %60-80'i kadar hareket beklentisi (1 gun)
        - Haftalik: ATR * sqrt(5) ile 5 gunluk volatilite tahmini
        """
        
        if analysis_type == "daily":
            # GUNLUK ANALIZ - 1 gun vadeli
            # ATR gunluk ortalama hareket miktarini gosterir
            # Bir sonraki gun icin ATR'nin %60-80'i kadar hareket beklenebilir
            
            if atr > 0:
                atr_percent = (atr / current_price) * 100
                
                # Gunluk hedef: ATR'nin %70'i (konservatif)
                # Momentum gucune gore ayarla
                momentum_factor = 0.7
                if bollinger["position"] < 0.3:  # Oversold - yukari potansiyel yuksek
                    momentum_factor = 0.85
                elif bollinger["position"] > 0.7:  # Overbought - yukari potansiyel dusuk
                    momentum_factor = 0.5
                
                target_pct = atr_percent * momentum_factor
                
                # BIST gunluk limit: max %10
                target_pct = min(target_pct, 10.0)
                
                # Minimum hedef %0.5, cok dusuk hedefler anlamli degil
                target_pct = max(target_pct, 0.5)
                
                # Stop loss: ATR'nin %50'si
                stop_loss_pct = -min(atr_percent * 0.5, 5.0)  # Max %5 stop loss
                stop_loss_pct = max(stop_loss_pct, -10.0)  # BIST taban limiti
                
            else:
                # ATR yoksa varsayilan degerler
                target_pct = 2.0
                stop_loss_pct = -2.0
                
        else:
            # HAFTALIK ANALIZ - 1 hafta vadeli (5 islem gunu)
            # Haftalik volatilite = Gunluk ATR * sqrt(5) ≈ ATR * 2.236
            
            if atr > 0:
                atr_percent = (atr / current_price) * 100
                
                # Haftalik volatilite tahmini
                weekly_volatility = atr_percent * 2.236
                
                # Teknik seviyelerden hedef belirle
                targets = []
                
                # Bollinger ust bant hedefi
                if bollinger["upper"] > current_price:
                    bb_target = ((bollinger["upper"] - current_price) / current_price) * 100
                    if bb_target <= weekly_volatility * 1.5:  # Ulasilabilir mesafede
                        targets.append(bb_target)
                
                # SMA50 hedefi (eger fiyat altindaysa)
                if mas.get("sma50") and mas["sma50"] > current_price:
                    sma_target = ((mas["sma50"] - current_price) / current_price) * 100
                    if sma_target <= weekly_volatility * 1.5:
                        targets.append(sma_target)
                
                # SMA20 hedefi
                if mas.get("sma20") and mas["sma20"] > current_price:
                    sma20_target = ((mas["sma20"] - current_price) / current_price) * 100
                    if sma20_target <= weekly_volatility:
                        targets.append(sma20_target)
                
                # ATR bazli hedef
                atr_target = weekly_volatility * 0.6  # Volatilitenin %60'i
                targets.append(atr_target)
                
                if targets:
                    # En yakin ulasilabilir hedefi sec (ortalama yerine)
                    target_pct = sum(targets) / len(targets)
                else:
                    target_pct = weekly_volatility * 0.5
                
                # Haftalik max hedef: %30 (teorik 5 gun x %10 = %50 ama gercekci degil)
                target_pct = min(target_pct, 30.0)
                target_pct = max(target_pct, 1.0)  # Min %1
                
                # Haftalik stop loss: Volatilitenin %40'i veya max %8
                stop_loss_pct = -min(weekly_volatility * 0.4, 8.0)
                stop_loss_pct = max(stop_loss_pct, -15.0)  # Haftalik max kayip
                
            else:
                target_pct = 5.0
                stop_loss_pct = -4.0
        
        # Hesaplamalari tamamla
        target_price = round(current_price * (1 + target_pct / 100), 2)
        stop_loss_price = round(current_price * (1 + stop_loss_pct / 100), 2)
        
        # Risk/Reward orani
        risk_reward = abs(target_pct / stop_loss_pct) if stop_loss_pct != 0 else 1.0
        
        return {
            "target_percent": round(target_pct, 2),
            "stop_loss_percent": round(stop_loss_pct, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "target_price": target_price,
            "stop_loss_price": stop_loss_price,
            "timeframe": "1 gün" if analysis_type == "daily" else "1 hafta (Pzt-Cum)"
        }

    def _determine_signal(self, score, rsi, macd, bollinger) -> str:
        if score >= 70:
            return "GUCLU_AL"
        elif score >= 60:
            return "AL"
        elif score <= 30:
            return "GUCLU_SAT"
        elif score <= 40:
            return "SAT"
        else:
            return "TUT"

    def _analyze_single_stock(self, symbol: str, period: str = "3mo", interval: str = "1d", analysis_type: str = "daily", retry_count: int = 3, include_sentiment: bool = True) -> Optional[Dict[str, Any]]:
        """Tek bir hisse için analiz yap - retry mekanizması ve sentiment ile"""
        last_error = None
        symbol = normalize_symbol(symbol)
        
        for attempt in range(retry_count):
            try:
                # Her denemede kısa bekleme
                if attempt > 0:
                    time.sleep(0.5 * attempt)
                
                # borsapy ile veri çek
                fetcher = get_borsapy_fetcher()
                df = fetcher.get_history(symbol, period=period, interval=interval)
                
                if df is None or df.empty or len(df) < 20:
                    return None
                
                close = df["close"]
                high = df["high"] if "high" in df.columns else close
                low = df["low"] if "low" in df.columns else close
                volume = df["volume"] if "volume" in df.columns else pd.Series([0] * len(df), index=df.index)
                
                current_price = float(close.iloc[-1])
                prev_close = float(close.iloc[-2]) if len(close) > 1 else current_price
                
                rsi = self._calculate_rsi(close)
                macd = self._calculate_macd(close)
                bollinger = self._calculate_bollinger_bands(close)
                mas = self._calculate_moving_averages(close)
                stochastic = self._calculate_stochastic(high, low, close)
                atr = self._calculate_atr(high, low, close)
                vol_analysis = self._calculate_volume_analysis(volume)
                
                stock_info = next((s for s in self._stocks if s["symbol"] == symbol), {})
                
                # Sentiment verisi çek (opsiyonel - analiz hızı için kapatılabilir)
                sentiment_data = None
                if include_sentiment:
                    try:
                        sentiment_data = self._fetch_sentiment_sync(symbol, stock_name=stock_info.get("name", symbol))
                    except Exception as se:
                        print(f"Sentiment hatası ({symbol}): {se}")
                        sentiment_data = {"has_data": False, "score": 0, "label": "Veri Yok"}
                
                score = self._calculate_score(rsi, macd, bollinger, mas, stochastic, current_price, vol_analysis, sentiment_data)
                potential = self._calculate_potential(current_price, bollinger, mas, atr, analysis_type)
                signal = self._determine_signal(score, rsi, macd, bollinger)
                
                return {
                    "symbol": symbol,
                    "name": stock_info.get("name", symbol),
                    "sector": stock_info.get("sector", ""),
                    "indexes": stock_info.get("indexes", []),
                    "current_price": round(current_price, 2),
                    "change_percent": round(((current_price - prev_close) / prev_close) * 100, 2),
                    "score": score,
                    "signal": signal,
                    "potential": potential,
                    "indicators": {
                        "rsi": round(rsi, 2),
                        "macd": {k: round(v, 4) for k, v in macd.items()},
                        "bollinger": {k: round(v, 4) if isinstance(v, float) else v for k, v in bollinger.items()},
                        "stochastic": {k: round(v, 2) for k, v in stochastic.items()},
                        "atr": round(atr, 4),
                        "volume": vol_analysis
                    },
                    "moving_averages": {k: round(v, 2) if v else None for k, v in mas.items()},
                    "sentiment": sentiment_data if sentiment_data else {"has_data": False, "score": 0, "label": "Veri Yok"}
                }
            except Exception as e:
                last_error = str(e)
                if attempt < retry_count - 1:
                    time.sleep(0.3)
                continue
        
        # Tum denemeler basarisiz
        self._failed_stocks.append({"symbol": symbol, "error": last_error})
        return None

    def _format_stock_for_frontend(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        indicators = stock.get("indicators", {})
        potential = stock.get("potential", {})
        rsi_val = indicators.get("rsi", 50)
        rsi_signal = "AL" if rsi_val < 30 else ("SAT" if rsi_val > 70 else "TUT")
        macd_data = indicators.get("macd", {})
        macd_signal = "AL" if macd_data.get("histogram", 0) > 0 else ("SAT" if macd_data.get("histogram", 0) < 0 else "TUT")
        bb_data = indicators.get("bollinger", {})
        bb_position = bb_data.get("position", 0.5)
        bb_signal = "AL" if bb_position < 0.2 else ("SAT" if bb_position > 0.8 else "TUT")
        mas = stock.get("moving_averages", {})
        current_price = stock.get("current_price", 0)
        sma20 = mas.get("sma20")
        sma50 = mas.get("sma50")
        if sma20 and sma50:
            ma_trend = "yukselis" if current_price > sma20 > sma50 else ("dusus" if current_price < sma20 < sma50 else "yatay")
        else:
            ma_trend = "yatay"
        stoch = indicators.get("stochastic", {})
        stoch_k = stoch.get("k", 50)
        stoch_signal = "AL" if stoch_k < 20 else ("SAT" if stoch_k > 80 else "TUT")
        
        # Sentiment verisi
        sentiment = stock.get("sentiment", {})
        sentiment_score = sentiment.get("score", 0) if sentiment else 0
        sentiment_label = sentiment.get("label", "Veri Yok") if sentiment else "Veri Yok"
        sentiment_signal = "AL" if sentiment_score > 0.2 else ("SAT" if sentiment_score < -0.2 else "TUT")
        
        return {
            "symbol": stock.get("symbol", ""),
            "name": stock.get("name", ""),
            "sector": stock.get("sector", ""),
            "current_price": stock.get("current_price", 0),
            "change_percent": stock.get("change_percent", 0),
            "volume": indicators.get("volume", {}).get("current", 0),
            "avg_volume": indicators.get("volume", {}).get("avg20", 0),
            "volume_ratio": indicators.get("volume", {}).get("ratio", 1),
            "score": stock.get("score", 50),
            "signal": stock.get("signal", "TUT"),
            "signal_strength": "strong" if stock.get("signal", "").startswith("GUCLU") else "normal",
            "indicators": {
                "rsi": rsi_val, "rsi_signal": rsi_signal,
                "macd": macd_data.get("macd", 0), "macd_signal_line": macd_data.get("signal", 0),
                "macd_histogram": macd_data.get("histogram", 0), "macd_signal": macd_signal,
                "bb_position": bb_position, "bb_signal": bb_signal, "ma_trend": ma_trend,
                "stochastic_k": stoch_k, "stochastic_d": stoch.get("d", 50), "stoch_signal": stoch_signal,
                "atr": indicators.get("atr", 0),
                "atr_percent": (indicators.get("atr", 0) / current_price * 100) if current_price > 0 else 0
            },
            "sentiment": {
                "score": round(sentiment_score, 3),
                "label": sentiment_label,
                "signal": sentiment_signal,
                "news_count": sentiment.get("news_count", 0) if sentiment else 0,
                "positive_news": sentiment.get("positive", 0) if sentiment else 0,
                "negative_news": sentiment.get("negative", 0) if sentiment else 0,
                "has_data": sentiment.get("has_data", False) if sentiment else False
            },
            "potential": {
                "target_percent": potential.get("target_percent", 5),
                "stop_loss_percent": abs(potential.get("stop_loss_percent", -5)),
                "risk_reward_ratio": potential.get("risk_reward_ratio", 1),
                "target_price": potential.get("target_price", current_price * 1.05),
                "stop_loss_price": potential.get("stop_loss_price", current_price * 0.95),
                "potential_profit": potential.get("target_percent", 5),
                "potential_loss": abs(potential.get("stop_loss_percent", -5)),
                "timeframe": potential.get("timeframe", "1 gün")
            },
            "reasons": []
        }

    def _record_signals_to_backtest(self, results: List[Dict], analysis_type: str) -> None:
        """Guclu sinyalleri backtest icin kaydet"""
        try:
            backtest = get_backtest_engine()
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Sadece guclu sinyalleri kaydet (score >= 65)
            strong_signals = [r for r in results if r["score"] >= 65 and r["signal"] in ["GUCLU_AL", "AL"]]
            
            # En fazla 10 sinyal kaydet (cok fazla kayit olmasin)
            for r in strong_signals[:10]:
                # Ayni gun ayni hisse icin tekrar kayit yapma
                existing = [s for s in backtest._history.get("signals", []) 
                           if s["symbol"] == r["symbol"] and s["date"] == today]
                if not existing:
                    backtest.record_signal(
                        symbol=r["symbol"],
                        signal=r["signal"],
                        score=r["score"],
                        price=r["current_price"],
                        date=today
                    )
            
            print(f"Backtest icin {min(len(strong_signals), 10)} sinyal kaydedildi")
        except Exception as e:
            print(f"Backtest kayit hatasi: {e}")

    def _analyze_batch(self, stocks: List[Dict], period: str, interval: str, analysis_type: str = "daily", batch_size: int = 50, include_sentiment: bool = False) -> List[Dict[str, Any]]:
        """Hisseleri batch'ler halinde analiz et - rate limit'i asmamak icin"""
        all_results = []
        total = len(stocks)
        
        for i in range(0, total, batch_size):
            batch = stocks[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            print(f"Batch {batch_num}/{total_batches} isleniyor ({len(batch)} hisse)...")
            
            # Her batch icin paralel islem
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._analyze_single_stock, s["symbol"], period, interval, analysis_type, 3, include_sentiment): s["symbol"]
                    for s in batch
                }
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            all_results.append(result)
                    except:
                        pass
            
            # Batch'ler arasi bekleme (rate limit icin)
            if i + batch_size < total:
                time.sleep(0.5)  # 2 saniyeden 0.5 saniyeye dusuruldu
        
        return all_results
    
    def _add_sentiment_to_top_picks(self, results: List[Dict], top_count: int = 20) -> List[Dict]:
        """Sadece en iyi hisseler için sentiment ekle (performans için)"""
        print(f"Top {top_count} hisse için sentiment analizi yapılıyor...")
        
        # İlk top_count hisse için sentiment çek
        for i, stock in enumerate(results[:top_count]):
            try:
                symbol = stock.get("symbol", "")
                name = stock.get("name", symbol)
                sentiment_data = self._fetch_sentiment_sync(symbol, stock_name=name)
                stock["sentiment"] = sentiment_data
                
                # Sentiment varsa skoru güncelle
                if sentiment_data and sentiment_data.get("has_data"):
                    old_score = stock.get("score", 50)
                    sentiment_score = sentiment_data.get("score", 0)
                    news_count = sentiment_data.get("news_count", 0)
                    
                    # Sentiment etkisi hesapla
                    if news_count >= 3:
                        sentiment_impact = int(sentiment_score * 10)
                        if sentiment_score > 0.3:
                            sentiment_impact += 3
                        elif sentiment_score < -0.3:
                            sentiment_impact -= 3
                        
                        new_score = max(0, min(100, old_score + sentiment_impact))
                        stock["score"] = new_score
                        stock["score_before_sentiment"] = old_score
                
                if (i + 1) % 5 == 0:
                    print(f"  Sentiment: {i + 1}/{min(top_count, len(results))} tamamlandı")
                    
            except Exception as e:
                print(f"Sentiment hatası ({stock.get('symbol', '?')}): {e}")
                stock["sentiment"] = {"has_data": False, "score": 0, "label": "Veri Yok"}
        
        # Kalan hisseler için boş sentiment
        for stock in results[top_count:]:
            if "sentiment" not in stock:
                stock["sentiment"] = {"has_data": False, "score": 0, "label": "Henüz Analiz Edilmedi"}
        
        return results

    def run_daily_analysis(self, index_filter: Optional[str] = None, sector_filter: Optional[str] = None, limit: int = 50, include_sentiment: bool = True) -> Dict[str, Any]:
        """Gunluk analiz - Hizli analiz icin optimize edildi, sentiment dahil"""
        self._failed_stocks = []  # Reset failed stocks
        stocks_to_analyze = self._stocks.copy()

        # Filtrele
        if index_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if index_filter in s.get("indexes", [])]
        if sector_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if sector_filter.lower() in s.get("sector", "").lower()]

        # Tum hisseleri analiz et (limit sadece sonuc sayisini sinirlar)

        print(f"Analiz edilecek hisse sayisi: {len(stocks_to_analyze)}")

        # Batch halinde analiz yap - GUNLUK (1 gun vadeli) - sentiment olmadan hızlı
        results = self._analyze_batch(stocks_to_analyze, "3mo", "1d", analysis_type="daily", batch_size=50, include_sentiment=False)
        analyzed = len(results)
        errors = len(self._failed_stocks)

        print(f"Basarili analiz: {analyzed}, Hata: {errors}")
        if self._failed_stocks and len(self._failed_stocks) <= 20:
            print(f"Basarisiz hisseler: {[s['symbol'] for s in self._failed_stocks]}")

        # Skora gore sirala
        results.sort(key=lambda x: x["score"], reverse=True)

        # Frontend formatina donustur
        formatted = [self._format_stock_for_frontend(r) for r in results]
        
        # Top hisseler için sentiment analizi ekle (performans için sadece top 30)
        if include_sentiment:
            formatted = self._add_sentiment_to_top_picks(formatted, top_count=30)
            # Sentiment sonrası tekrar sırala
            formatted.sort(key=lambda x: x["score"], reverse=True)

        # En iyi secimler (AL sinyali verenler)
        # limit=0 ise tum sonuclari dondur
        top_picks = [r for r in formatted if r["score"] >= 55]
        if limit > 0:
            top_picks = top_picks[:limit]

        # Sinyalleri say
        buy_signals = len([r for r in formatted if r["signal"] in ["GUCLU_AL", "AL"]])
        sell_signals = len([r for r in formatted if r["signal"] in ["GUCLU_SAT", "SAT"]])
        strong_buy = len([r for r in formatted if r["signal"] == "GUCLU_AL"])

        # RSI istatistikleri
        rsi_values = [r["indicators"]["rsi"] for r in formatted]
        avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 50
        oversold = len([r for r in rsi_values if r < 30])
        overbought = len([r for r in rsi_values if r > 70])
        
        # Sentiment istatistikleri
        sentiment_scores = [r.get("sentiment", {}).get("score", 0) for r in formatted[:30] if r.get("sentiment", {}).get("has_data")]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        positive_sentiment_count = len([s for s in sentiment_scores if s > 0.1])
        negative_sentiment_count = len([s for s in sentiment_scores if s < -0.1])

        # Piyasa ozeti
        bullish_pct = (buy_signals / analyzed * 100) if analyzed > 0 else 0
        bearish_pct = (sell_signals / analyzed * 100) if analyzed > 0 else 0

        # Guclu sinyalleri backtest icin kaydet
        self._record_signals_to_backtest(formatted, "daily")

        return {
            "analysis_type": "daily",
            "analysis_date": datetime.now().isoformat(),
            "total_analyzed": analyzed,
            "total_stocks": len(stocks_to_analyze),
            "failed_count": errors,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "strong_buy_count": strong_buy,
            "market_summary": {
                "bullish_percent": round(bullish_pct, 1),
                "bearish_percent": round(bearish_pct, 1),
                "neutral_percent": round(100 - bullish_pct - bearish_pct, 1),
                "market_sentiment": "Yukselis Egilimi" if bullish_pct > 50 else ("Dusus Egilimi" if bearish_pct > 50 else "NOTR"),
                "avg_rsi": round(avg_rsi, 1),
                "oversold_count": oversold,
                "overbought_count": overbought,
                "avg_sentiment": round(avg_sentiment, 3) if include_sentiment else None,
                "positive_sentiment_stocks": positive_sentiment_count if include_sentiment else None,
                "negative_sentiment_stocks": negative_sentiment_count if include_sentiment else None
            },
            "top_picks": top_picks,
            "all_results": formatted
        }

    def run_weekly_analysis(self, index_filter: Optional[str] = None, sector_filter: Optional[str] = None, limit: int = 30, include_sentiment: bool = True) -> Dict[str, Any]:
        """Haftalik analiz - Hizli analiz icin optimize edildi, sentiment dahil"""
        self._failed_stocks = []  # Reset failed stocks
        stocks_to_analyze = self._stocks.copy()

        # Filtrele
        if index_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if index_filter in s.get("indexes", [])]
        if sector_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if sector_filter.lower() in s.get("sector", "").lower()]

        # Tum hisseleri analiz et (limit sadece sonuc sayisini sinirlar)

        print(f"Haftalik analiz - hisse sayisi: {len(stocks_to_analyze)}")

        # Batch halinde analiz yap - HAFTALIK (1 hafta vadeli, Pzt-Cum) - sentiment olmadan hızlı
        results = self._analyze_batch(stocks_to_analyze, "6mo", "1wk", analysis_type="weekly", batch_size=50, include_sentiment=False)
        analyzed = len(results)
        errors = len(self._failed_stocks)

        print(f"Haftalik basarili: {analyzed}, Hata: {errors}")
        if self._failed_stocks and len(self._failed_stocks) <= 20:
            print(f"Basarisiz hisseler: {[s['symbol'] for s in self._failed_stocks]}")

        # Skora gore sirala
        results.sort(key=lambda x: x["score"], reverse=True)

        # Frontend formatina donustur
        formatted = [self._format_stock_for_frontend(r) for r in results]
        
        # Top hisseler için sentiment analizi ekle (performans için sadece top 30)
        if include_sentiment:
            formatted = self._add_sentiment_to_top_picks(formatted, top_count=30)
            # Sentiment sonrası tekrar sırala
            formatted.sort(key=lambda x: x["score"], reverse=True)

        # En iyi secimler
        # limit=0 ise tum sonuclari dondur
        top_picks = [r for r in formatted if r["score"] >= 55]
        if limit > 0:
            top_picks = top_picks[:limit]

        # Sinyalleri say
        buy_signals = len([r for r in formatted if r["signal"] in ["GUCLU_AL", "AL"]])
        sell_signals = len([r for r in formatted if r["signal"] in ["GUCLU_SAT", "SAT"]])
        strong_buy = len([r for r in formatted if r["signal"] == "GUCLU_AL"])

        # RSI istatistikleri
        rsi_values = [r["indicators"]["rsi"] for r in formatted]
        avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 50
        oversold = len([r for r in rsi_values if r < 30])
        overbought = len([r for r in rsi_values if r > 70])
        
        # Sentiment istatistikleri
        sentiment_scores = [r.get("sentiment", {}).get("score", 0) for r in formatted[:30] if r.get("sentiment", {}).get("has_data")]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        positive_sentiment_count = len([s for s in sentiment_scores if s > 0.1])
        negative_sentiment_count = len([s for s in sentiment_scores if s < -0.1])

        # Piyasa ozeti
        bullish_pct = (buy_signals / analyzed * 100) if analyzed > 0 else 0
        bearish_pct = (sell_signals / analyzed * 100) if analyzed > 0 else 0

        # Guclu sinyalleri backtest icin kaydet
        self._record_signals_to_backtest(formatted, "weekly")

        return {
            "analysis_type": "weekly",
            "analysis_date": datetime.now().isoformat(),
            "total_analyzed": analyzed,
            "total_stocks": len(stocks_to_analyze),
            "failed_count": errors,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "strong_buy_count": strong_buy,
            "market_summary": {
                "bullish_percent": round(bullish_pct, 1),
                "bearish_percent": round(bearish_pct, 1),
                "neutral_percent": round(100 - bullish_pct - bearish_pct, 1),
                "market_sentiment": "Yukselis Egilimi" if bullish_pct > 50 else ("Dusus Egilimi" if bearish_pct > 50 else "NOTR"),
                "avg_rsi": round(avg_rsi, 1),
                "oversold_count": oversold,
                "overbought_count": overbought,
                "avg_sentiment": round(avg_sentiment, 3) if include_sentiment else None,
                "positive_sentiment_stocks": positive_sentiment_count if include_sentiment else None,
                "negative_sentiment_stocks": negative_sentiment_count if include_sentiment else None
            },
            "top_picks": top_picks,
            "all_results": formatted
        }


_analysis_service: Optional[AnalysisService] = None

def get_analysis_service() -> AnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
