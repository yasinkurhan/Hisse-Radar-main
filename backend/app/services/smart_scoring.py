"""
Backtesting ve Akilli Skor Sistemi
===================================
Gecmis sinyal performansi ve dinamik skorlama
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class SmartScoring:
    """Akilli Skor Sistemi - Dinamik agirliklar ve sektor bazli degerlenirme"""
    
    # Sektor bazli agirliklar
    SECTOR_WEIGHTS = {
        "Banka": {"rsi": 0.15, "macd": 0.20, "bollinger": 0.10, "ma": 0.15, "stoch": 0.10, "volume": 0.10, "adx": 0.10, "fundamental": 0.10},
        "Holding": {"rsi": 0.15, "macd": 0.15, "bollinger": 0.15, "ma": 0.15, "stoch": 0.10, "volume": 0.10, "adx": 0.10, "fundamental": 0.10},
        "Teknoloji": {"rsi": 0.20, "macd": 0.20, "bollinger": 0.15, "ma": 0.10, "stoch": 0.10, "volume": 0.15, "adx": 0.05, "fundamental": 0.05},
        "Insaat": {"rsi": 0.15, "macd": 0.15, "bollinger": 0.15, "ma": 0.15, "stoch": 0.10, "volume": 0.10, "adx": 0.10, "fundamental": 0.10},
        "Enerji": {"rsi": 0.10, "macd": 0.15, "bollinger": 0.10, "ma": 0.20, "stoch": 0.10, "volume": 0.10, "adx": 0.10, "fundamental": 0.15},
        "default": {"rsi": 0.15, "macd": 0.15, "bollinger": 0.15, "ma": 0.15, "stoch": 0.10, "volume": 0.10, "adx": 0.10, "fundamental": 0.10}
    }
    
    # Piyasa kosulu carpanlari
    MARKET_MULTIPLIERS = {
        "bull": {"rsi_oversold_bonus": 1.5, "macd_bullish_bonus": 1.3, "volume_bonus": 1.2},
        "bear": {"rsi_oversold_bonus": 0.8, "macd_bullish_bonus": 0.7, "volume_bonus": 0.9},
        "neutral": {"rsi_oversold_bonus": 1.0, "macd_bullish_bonus": 1.0, "volume_bonus": 1.0}
    }
    
    @staticmethod
    def calculate_smart_score(
        indicators: Dict[str, Any],
        sector: str = "",
        market_condition: str = "neutral",
        fundamental_score: int = 50,
        adx_data: Dict = None,
        patterns: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Akilli skor hesaplama
        - Sektore gore agirlik
        - Piyasa kosuluna gore ayarlama
        - Temel analiz entegrasyonu
        - Formasyon bonusu
        """
        # Sektor agirliklarini al
        weights = SmartScoring.SECTOR_WEIGHTS.get(sector, SmartScoring.SECTOR_WEIGHTS["default"])
        multipliers = SmartScoring.MARKET_MULTIPLIERS.get(market_condition, SmartScoring.MARKET_MULTIPLIERS["neutral"])
        
        # Baz skor
        base_score = 50
        score_breakdown = {}
        
        # RSI skoru (0-100)
        rsi = indicators.get("rsi", 50)
        if rsi < 30:
            rsi_score = 80 * multipliers["rsi_oversold_bonus"]
        elif rsi < 40:
            rsi_score = 65
        elif rsi > 70:
            rsi_score = 20
        elif rsi > 60:
            rsi_score = 35
        else:
            rsi_score = 50
        score_breakdown["rsi"] = {"score": round(rsi_score, 1), "weight": weights["rsi"]}
        
        # MACD skoru
        macd_hist = indicators.get("macd_histogram", 0)
        macd_val = indicators.get("macd", 0)
        macd_signal = indicators.get("macd_signal_line", 0)
        
        if macd_hist > 0 and macd_val > macd_signal:
            macd_score = 80 * multipliers["macd_bullish_bonus"]
        elif macd_hist > 0:
            macd_score = 65
        elif macd_hist < 0 and macd_val < macd_signal:
            macd_score = 20
        elif macd_hist < 0:
            macd_score = 35
        else:
            macd_score = 50
        score_breakdown["macd"] = {"score": round(macd_score, 1), "weight": weights["macd"]}
        
        # Bollinger skoru
        bb_position = indicators.get("bb_position", 0.5)
        if bb_position < 0.2:
            bb_score = 80
        elif bb_position < 0.4:
            bb_score = 65
        elif bb_position > 0.8:
            bb_score = 20
        elif bb_position > 0.6:
            bb_score = 35
        else:
            bb_score = 50
        score_breakdown["bollinger"] = {"score": round(bb_score, 1), "weight": weights["bollinger"]}
        
        # MA trend skoru
        ma_trend = indicators.get("ma_trend", "yatay")
        if ma_trend == "yukselis":
            ma_score = 75
        elif ma_trend == "dusus":
            ma_score = 25
        else:
            ma_score = 50
        score_breakdown["ma"] = {"score": round(ma_score, 1), "weight": weights["ma"]}
        
        # Stochastic skoru
        stoch_k = indicators.get("stochastic_k", 50)
        if stoch_k < 20:
            stoch_score = 80
        elif stoch_k < 30:
            stoch_score = 65
        elif stoch_k > 80:
            stoch_score = 20
        elif stoch_k > 70:
            stoch_score = 35
        else:
            stoch_score = 50
        score_breakdown["stoch"] = {"score": round(stoch_score, 1), "weight": weights["stoch"]}
        
        # Hacim skoru
        volume_ratio = indicators.get("volume_ratio", 1)
        if volume_ratio > 2:
            volume_score = 70 * multipliers["volume_bonus"]
        elif volume_ratio > 1.5:
            volume_score = 60
        elif volume_ratio < 0.5:
            volume_score = 35
        else:
            volume_score = 50
        score_breakdown["volume"] = {"score": round(volume_score, 1), "weight": weights["volume"]}
        
        # ADX skoru (trend gucu)
        if adx_data:
            adx = adx_data.get("adx", 25)
            trend_dir = adx_data.get("trend_direction", "yatay")
            
            if adx > 25 and trend_dir == "yukari":
                adx_score = 75
            elif adx > 25 and trend_dir == "asagi":
                adx_score = 25
            elif adx > 20:
                adx_score = 50
            else:
                adx_score = 40  # Zayif trend = daha az guvenilir sinyal
        else:
            adx_score = 50
        score_breakdown["adx"] = {"score": round(adx_score, 1), "weight": weights["adx"]}
        
        # Temel analiz skoru
        score_breakdown["fundamental"] = {"score": fundamental_score, "weight": weights["fundamental"]}
        
        # Agirlikli toplam
        weighted_score = sum(
            score_breakdown[key]["score"] * score_breakdown[key]["weight"]
            for key in score_breakdown
        )
        
        # Formasyon bonusu
        pattern_bonus = 0
        if patterns:
            for p in patterns:
                if p.get("signal") == "AL" and p.get("strength") == "cok_guclu":
                    pattern_bonus += 10
                elif p.get("signal") == "AL" and p.get("strength") == "guclu":
                    pattern_bonus += 7
                elif p.get("signal") == "AL":
                    pattern_bonus += 4
                elif p.get("signal") == "SAT" and p.get("strength") == "cok_guclu":
                    pattern_bonus -= 10
                elif p.get("signal") == "SAT" and p.get("strength") == "guclu":
                    pattern_bonus -= 7
                elif p.get("signal") == "SAT":
                    pattern_bonus -= 4
        
        final_score = max(0, min(100, int(weighted_score + pattern_bonus)))
        
        # Guven seviyesi (ADX + hacim bazli)
        confidence = "orta"
        if adx_data and adx_data.get("adx", 0) > 25 and volume_ratio > 1.2:
            confidence = "yuksek"
        elif adx_data and adx_data.get("adx", 0) < 20 or volume_ratio < 0.7:
            confidence = "dusuk"
        
        return {
            "score": final_score,
            "breakdown": score_breakdown,
            "pattern_bonus": pattern_bonus,
            "confidence": confidence,
            "market_condition": market_condition
        }


class BacktestEngine:
    """Backtesting Motoru - Gecmis sinyal performansini olc"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(Path(__file__).parent.parent / "data" / "backtest_history.json")
        self._history = self._load_history()
    
    def _load_history(self) -> Dict:
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"signals": [], "performance": {}}
    
    def _save_history(self):
        try:
            Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Backtest kayit hatasi: {e}")
    
    def record_signal(self, symbol: str, signal: str, score: int, price: float, date: str = None):
        """Yeni sinyal kaydet"""
        record = {
            "symbol": symbol,
            "signal": signal,
            "score": score,
            "entry_price": price,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "status": "active",
            "exit_price": None,
            "exit_date": None,
            "profit_pct": None
        }
        self._history["signals"].append(record)
        self._save_history()
    
    def update_signals(self, current_prices: Dict[str, float]):
        """Aktif sinyalleri guncelle ve sonuclandirilmis olanlari isaretle"""
        updated = False
        
        for signal in self._history["signals"]:
            if signal["status"] != "active":
                continue
            
            symbol = signal["symbol"]
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            entry_price = signal["entry_price"]
            signal_type = signal["signal"]
            entry_date = datetime.strptime(signal["date"], "%Y-%m-%d")
            days_held = (datetime.now() - entry_date).days
            
            # Kar/zarar hesapla
            if signal_type in ["GUCLU_AL", "AL"]:
                profit_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SAT sinyali
                profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Otomatik cikis kurallari
            should_exit = False
            exit_reason = ""
            
            # 1. Kar al (%10)
            if profit_pct >= 10:
                should_exit = True
                exit_reason = "kar_al"
            # 2. Zarar kes (%7)
            elif profit_pct <= -7:
                should_exit = True
                exit_reason = "zarar_kes"
            # 3. Zaman asimi (30 gun)
            elif days_held >= 30:
                should_exit = True
                exit_reason = "zaman_asimi"
            
            if should_exit:
                signal["status"] = "completed"
                signal["exit_price"] = current_price
                signal["exit_date"] = datetime.now().strftime("%Y-%m-%d")
                signal["profit_pct"] = round(profit_pct, 2)
                signal["exit_reason"] = exit_reason
                signal["days_held"] = days_held
                updated = True
        
        if updated:
            self._save_history()
            self._calculate_performance()
    
    def _calculate_performance(self):
        """Genel performans istatistiklerini hesapla"""
        completed = [s for s in self._history["signals"] if s["status"] == "completed"]
        
        if not completed:
            return
        
        total = len(completed)
        winners = [s for s in completed if s["profit_pct"] > 0]
        losers = [s for s in completed if s["profit_pct"] <= 0]
        
        win_rate = (len(winners) / total) * 100 if total > 0 else 0
        avg_profit = sum(s["profit_pct"] for s in completed) / total if total > 0 else 0
        avg_win = sum(s["profit_pct"] for s in winners) / len(winners) if winners else 0
        avg_loss = sum(s["profit_pct"] for s in losers) / len(losers) if losers else 0
        
        # Sinyal tipine gore
        al_signals = [s for s in completed if s["signal"] in ["GUCLU_AL", "AL"]]
        sat_signals = [s for s in completed if s["signal"] in ["GUCLU_SAT", "SAT"]]
        
        al_win_rate = (len([s for s in al_signals if s["profit_pct"] > 0]) / len(al_signals) * 100) if al_signals else 0
        sat_win_rate = (len([s for s in sat_signals if s["profit_pct"] > 0]) / len(sat_signals) * 100) if sat_signals else 0
        
        # Skor bazli performans
        high_score = [s for s in completed if s["score"] >= 70]
        mid_score = [s for s in completed if 50 <= s["score"] < 70]
        low_score = [s for s in completed if s["score"] < 50]
        
        high_score_win = (len([s for s in high_score if s["profit_pct"] > 0]) / len(high_score) * 100) if high_score else 0
        
        self._history["performance"] = {
            "total_signals": total,
            "win_rate": round(win_rate, 1),
            "avg_profit": round(avg_profit, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "al_win_rate": round(al_win_rate, 1),
            "sat_win_rate": round(sat_win_rate, 1),
            "high_score_win_rate": round(high_score_win, 1),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        self._save_history()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Performans istatistiklerini getir"""
        return self._history.get("performance", {})
    
    def get_active_signals(self) -> List[Dict]:
        """Aktif sinyalleri getir"""
        return [s for s in self._history["signals"] if s["status"] == "active"]
    
    def get_recent_results(self, limit: int = 20) -> List[Dict]:
        """Son sonuclanan sinyalleri getir"""
        completed = [s for s in self._history["signals"] if s["status"] == "completed"]
        completed.sort(key=lambda x: x.get("exit_date", ""), reverse=True)
        return completed[:limit]
    
    def run_historical_backtest(self, symbol: str, df: pd.DataFrame, signal_func) -> Dict[str, Any]:
        """
        Gecmis veri uzerinde backtest yap
        signal_func: Fiyat verisini alip sinyal ureten fonksiyon
        """
        if len(df) < 60:
            return {"error": "Yetersiz veri"}
        
        trades = []
        position = None
        
        # Son 200 gunu test et (ilk 60 gun indikatörler için)
        test_start = 60
        
        for i in range(test_start, len(df) - 5):
            # Bu noktaya kadar olan veriyle sinyal uret
            historical_data = df.iloc[:i+1]
            
            try:
                signal, score = signal_func(historical_data)
            except:
                continue
            
            current_price = float(df.iloc[i]["Close"])
            
            # Pozisyon yonetimi
            if position is None and signal in ["GUCLU_AL", "AL"]:
                position = {
                    "entry_idx": i,
                    "entry_price": current_price,
                    "signal": signal,
                    "score": score
                }
            elif position is not None:
                entry_price = position["entry_price"]
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                days_held = i - position["entry_idx"]
                
                # Cikis kontrol
                should_exit = False
                if profit_pct >= 10:  # Kar al
                    should_exit = True
                elif profit_pct <= -7:  # Zarar kes
                    should_exit = True
                elif days_held >= 20:  # Max sure
                    should_exit = True
                elif signal in ["GUCLU_SAT", "SAT"]:  # Ters sinyal
                    should_exit = True
                
                if should_exit:
                    trades.append({
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "profit_pct": round(profit_pct, 2),
                        "days_held": days_held,
                        "score": position["score"]
                    })
                    position = None
        
        # Sonuclari hesapla
        if not trades:
            return {"total_trades": 0, "win_rate": 0}
        
        winners = [t for t in trades if t["profit_pct"] > 0]
        total_profit = sum(t["profit_pct"] for t in trades)
        
        return {
            "symbol": symbol,
            "total_trades": len(trades),
            "winning_trades": len(winners),
            "win_rate": round(len(winners) / len(trades) * 100, 1),
            "total_profit": round(total_profit, 2),
            "avg_profit": round(total_profit / len(trades), 2),
            "avg_days_held": round(sum(t["days_held"] for t in trades) / len(trades), 1),
            "best_trade": max(t["profit_pct"] for t in trades),
            "worst_trade": min(t["profit_pct"] for t in trades),
            "trades": trades[-10:]  # Son 10 islem
        }


class MarketConditionAnalyzer:
    """Piyasa Kosulu Analizcisi"""
    
    @staticmethod
    def analyze_market_condition(bist100_data: pd.DataFrame) -> Dict[str, Any]:
        """
        BIST100 verisine gore genel piyasa kosulunu belirle
        """
        if len(bist100_data) < 50:
            return {"condition": "neutral", "strength": 50, "description": "Yetersiz veri"}
        
        close = bist100_data["Close"]
        
        # Son 20 gunluk trend
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        current = close.iloc[-1]
        
        # Son 10 gunluk momentum
        momentum = ((current - close.iloc[-10]) / close.iloc[-10]) * 100
        
        # Karar
        if current > sma20 > sma50 and momentum > 2:
            condition = "bull"
            strength = min(80, 50 + momentum * 3)
            description = "Guclu yukselis trendi"
        elif current < sma20 < sma50 and momentum < -2:
            condition = "bear"
            strength = max(20, 50 + momentum * 3)
            description = "Guclu dusus trendi"
        elif current > sma20:
            condition = "bull"
            strength = 60
            description = "Hafif yukselis trendi"
        elif current < sma20:
            condition = "bear"
            strength = 40
            description = "Hafif dusus trendi"
        else:
            condition = "neutral"
            strength = 50
            description = "Yatay piyasa"
        
        return {
            "condition": condition,
            "strength": round(strength),
            "description": description,
            "momentum_10d": round(momentum, 2),
            "above_sma20": bool(current > sma20),
            "above_sma50": bool(current > sma50)
        }
