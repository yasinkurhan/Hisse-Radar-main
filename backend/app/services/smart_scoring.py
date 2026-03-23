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
    
    # Sektor bazli agirliklar (news_sentiment eklendi)
    SECTOR_WEIGHTS = {
        "Banka": {"rsi": 0.13, "macd": 0.17, "bollinger": 0.10, "ma": 0.13, "stoch": 0.09, "volume": 0.09, "adx": 0.09, "fundamental": 0.10, "news_sentiment": 0.10},
        "Holding": {"rsi": 0.13, "macd": 0.13, "bollinger": 0.13, "ma": 0.13, "stoch": 0.09, "volume": 0.09, "adx": 0.09, "fundamental": 0.10, "news_sentiment": 0.11},
        "Teknoloji": {"rsi": 0.17, "macd": 0.17, "bollinger": 0.13, "ma": 0.08, "stoch": 0.09, "volume": 0.13, "adx": 0.05, "fundamental": 0.05, "news_sentiment": 0.13},
        "Insaat": {"rsi": 0.13, "macd": 0.13, "bollinger": 0.13, "ma": 0.13, "stoch": 0.09, "volume": 0.09, "adx": 0.09, "fundamental": 0.10, "news_sentiment": 0.11},
        "Enerji": {"rsi": 0.08, "macd": 0.13, "bollinger": 0.10, "ma": 0.17, "stoch": 0.09, "volume": 0.09, "adx": 0.09, "fundamental": 0.13, "news_sentiment": 0.12},
        "default": {"rsi": 0.13, "macd": 0.13, "bollinger": 0.13, "ma": 0.13, "stoch": 0.09, "volume": 0.09, "adx": 0.09, "fundamental": 0.10, "news_sentiment": 0.11}
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
        patterns: List[Dict] = None,
        news_sentiment_score: float = 0.0
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
        
        # Haber/Sentiment skoru (news_sentiment_score: -1 ile +1 arasi)
        # Olumlu haberler = yuksek skor, olumsuz haberler = dusuk skor
        if news_sentiment_score != 0:
            # -1..+1 arasini 0..100 arasina ceviriyoruz
            ns_score = 50 + (news_sentiment_score * 40)  # -1->10, 0->50, +1->90
            ns_score = max(10, min(90, ns_score))
        else:
            ns_score = 50  # Haber yoksa notr
        score_breakdown["news_sentiment"] = {"score": round(ns_score, 1), "weight": weights["news_sentiment"]}
        
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
        """Gelismis performans istatistiklerini hesapla"""
        completed = [s for s in self._history["signals"] if s["status"] == "completed"]

        if not completed:
            return

        total = len(completed)
        profits = [s["profit_pct"] for s in completed]
        winners = [s for s in completed if s["profit_pct"] > 0]
        losers  = [s for s in completed if s["profit_pct"] <= 0]

        win_rate   = (len(winners) / total) * 100 if total > 0 else 0
        avg_profit = sum(profits) / total if total > 0 else 0
        avg_win    = sum(s["profit_pct"] for s in winners) / len(winners) if winners else 0
        avg_loss   = sum(s["profit_pct"] for s in losers)  / len(losers)  if losers  else 0

        # Profit Factor = toplam kazanç / toplam kayıp (mutlak değer)
        gross_win  = sum(s["profit_pct"] for s in winners) if winners else 0
        gross_loss = abs(sum(s["profit_pct"] for s in losers)) if losers else 0
        profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else 0

        # Expectancy = (WinRate * AvgWin) + (LossRate * AvgLoss)
        loss_rate  = 1 - (win_rate / 100)
        expectancy = round((win_rate / 100) * avg_win + loss_rate * avg_loss, 2)

        # Sharpe Orani (risk-free %0 varsayimi)
        if len(profits) > 1:
            mean_r = avg_profit
            std_r  = float(np.std(profits))
            sharpe = round(mean_r / std_r, 2) if std_r > 0 else 0
        else:
            sharpe = 0

        # Maksimum Drawdown (Sabit Pozisyon Büyüklüğü: Kasanın %10'u 1 işleme)
        capital = 100.0
        peak = capital
        max_dd = 0.0
        equity_curve = [100.0]
        
        for p in profits:
            # Aşırı yüksek hatalı verileri filtrele
            if p < -50 or p > 300:
                continue 
                
            # Her işleme kasanın %10'u ayrılıyor (10 birim sermaye riski)
            trade_profit = 10.0 * (p / 100.0)
            capital += trade_profit
            
            equity_curve.append(round(capital, 2))
            
            if capital > peak:
                peak = capital
            
            if peak > 0:
                dd = (peak - capital) / peak * 100
                if dd > max_dd:
                    max_dd = round(dd, 2)
                    
        final_capital = round(capital, 2)
        total_return  = round(capital - 100.0, 2)

        # Sinyal tipine gore
        al_signals  = [s for s in completed if s["signal"] in ["GUCLU_AL", "AL"]]
        sat_signals = [s for s in completed if s["signal"] in ["GUCLU_SAT", "SAT"]]
        guclu_al    = [s for s in completed if s["signal"] == "GUCLU_AL"]

        al_win_rate      = (len([s for s in al_signals  if s["profit_pct"] > 0]) / len(al_signals)  * 100) if al_signals  else 0
        sat_win_rate     = (len([s for s in sat_signals if s["profit_pct"] > 0]) / len(sat_signals) * 100) if sat_signals else 0
        guclu_al_win     = (len([s for s in guclu_al    if s["profit_pct"] > 0]) / len(guclu_al)    * 100) if guclu_al    else 0

        # Skor bazli performans
        high_score = [s for s in completed if s["score"] >= 70]
        mid_score  = [s for s in completed if 50 <= s["score"] < 70]
        low_score  = [s for s in completed if s["score"] < 50]

        high_score_win = (len([s for s in high_score if s["profit_pct"] > 0]) / len(high_score) * 100) if high_score else 0
        mid_score_win  = (len([s for s in mid_score  if s["profit_pct"] > 0]) / len(mid_score)  * 100) if mid_score  else 0
        low_score_win  = (len([s for s in low_score  if s["profit_pct"] > 0]) / len(low_score)  * 100) if low_score  else 0

        # Cikis nedenine gore
        kar_al_count    = len([s for s in completed if s.get("exit_reason") == "kar_al"])
        zarar_kes_count = len([s for s in completed if s.get("exit_reason") == "zarar_kes"])
        zaman_count     = len([s for s in completed if s.get("exit_reason") == "zaman_asimi"])

        # Ortalama elde tutma suresi
        days_list = [s.get("days_held", 0) for s in completed if s.get("days_held")]
        avg_days  = round(sum(days_list) / len(days_list), 1) if days_list else 0

        # Aylik performans
        monthly = {}
        for s in completed:
            exit_d = s.get("exit_date", "")
            if exit_d and len(exit_d) >= 7:
                month_key = exit_d[:7]  # "2025-03"
                if month_key not in monthly:
                    monthly[month_key] = []
                monthly[month_key].append(s["profit_pct"])
        monthly_summary = [
            {"month": k, "avg_profit": round(sum(v)/len(v), 2), "trade_count": len(v),
             "win_count": len([x for x in v if x > 0])}
            for k, v in sorted(monthly.items())
        ]

        # Hisse bazli ozet (ilk 10)
        symbol_map = {}
        for s in completed:
            sym = s["symbol"]
            if sym not in symbol_map:
                symbol_map[sym] = []
            symbol_map[sym].append(s["profit_pct"])
        symbol_perf = sorted(
            [{"symbol": k, "trades": len(v),
              "avg_profit": round(sum(v)/len(v), 2),
              "win_rate": round(len([x for x in v if x > 0])/len(v)*100, 1)}
             for k, v in symbol_map.items()],
            key=lambda x: x["avg_profit"], reverse=True
        )

        self._history["performance"] = {
            # Temel
            "total_signals": total,
            "win_rate": round(win_rate, 1),
            "avg_profit": round(avg_profit, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            # Ileri metrikler
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "sharpe_ratio": sharpe,
            "max_drawdown": round(max_dd, 2),
            "total_return": total_return,
            "final_capital_100k": round(final_capital * 1000, 0),  # 100K TL baslangic
            # Sinyal turu
            "al_win_rate": round(al_win_rate, 1),
            "sat_win_rate": round(sat_win_rate, 1),
            "guclu_al_win_rate": round(guclu_al_win, 1),
            "high_score_win_rate": round(high_score_win, 1),
            "mid_score_win_rate": round(mid_score_win, 1),
            "low_score_win_rate": round(low_score_win, 1),
            # Cikis nedenler
            "kar_al_count": kar_al_count,
            "zarar_kes_count": zarar_kes_count,
            "zaman_asimi_count": zaman_count,
            # Ek istatistik
            "avg_days_held": avg_days,
            "equity_curve": equity_curve[-60:],  # Son 60 islem
            "monthly_performance": monthly_summary[-12:],  # Son 12 ay
            "top_symbols": symbol_perf[:10],
            "worst_symbols": symbol_perf[-5:] if len(symbol_perf) >= 5 else [],
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

    def get_symbol_breakdown(self) -> List[Dict]:
        """Hisse bazli performans dokumu"""
        completed = [s for s in self._history["signals"] if s["status"] == "completed"]
        symbol_map: Dict[str, List] = {}
        for s in completed:
            sym = s["symbol"]
            if sym not in symbol_map:
                symbol_map[sym] = []
            symbol_map[sym].append(s)

        result = []
        for sym, trades in symbol_map.items():
            profits = [t["profit_pct"] for t in trades]
            winners = [p for p in profits if p > 0]
            result.append({
                "symbol": sym,
                "total_trades": len(trades),
                "win_count": len(winners),
                "win_rate": round(len(winners) / len(trades) * 100, 1),
                "avg_profit": round(sum(profits) / len(profits), 2),
                "total_profit": round(sum(profits), 2),
                "best_trade": round(max(profits), 2),
                "worst_trade": round(min(profits), 2),
                "avg_days": round(sum(t.get("days_held", 0) for t in trades) / len(trades), 1),
                "last_signal": sorted(trades, key=lambda x: x.get("exit_date", ""))[-1].get("exit_date", "")
            })

        result.sort(key=lambda x: x["total_profit"], reverse=True)
        return result

    def get_exit_reason_breakdown(self) -> Dict[str, Any]:
        """Cikis sebebine gore analiz"""
        completed = [s for s in self._history["signals"] if s["status"] == "completed"]
        reasons = {}
        for s in completed:
            r = s.get("exit_reason", "bilinmiyor")
            if r not in reasons:
                reasons[r] = {"count": 0, "profits": []}
            reasons[r]["count"] += 1
            reasons[r]["profits"].append(s["profit_pct"])

        breakdown = {}
        for r, data in reasons.items():
            profits = data["profits"]
            breakdown[r] = {
                "count": data["count"],
                "avg_profit": round(sum(profits) / len(profits), 2),
                "win_rate": round(len([p for p in profits if p > 0]) / len(profits) * 100, 1),
                "total_profit": round(sum(profits), 2)
            }
        return breakdown
    
    def run_historical_backtest(self, symbol: str, df: pd.DataFrame, signal_func) -> Dict[str, Any]:
        """
        Gecmis veri uzerinde backtest yap
        signal_func: Fiyat verisini alip sinyal ureten fonksiyon
        """
        if len(df) < 60:
            return {"error": "Yetersiz veri"}
        
        trades = []
        position = None
        
        # Son 200 gunu test et (ilk 60 gun indikat�rler i�in)
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
        BIST100 verisine gore genel piyasa kosulunu belirle.
        Frontend'in beklediği format: condition(bullish/bearish/neutral),
        trend, volatility, recommendation, details(rsi, trend_direction, above_sma20, above_sma50)
        """
        if len(bist100_data) < 50:
            return {
                "condition": "neutral",
                "trend": "Yatay",
                "volatility": "Normal",
                "recommendation": "Yetersiz veri, dikkatli olun.",
                "details": {"rsi": 50, "trend_direction": "neutral", "above_sma20": False, "above_sma50": False}
            }

        close = bist100_data["Close"]

        # Son 20/50 gün SMA
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        current = close.iloc[-1]

        # Son 10 günlük momentum
        momentum = ((current - close.iloc[-10]) / close.iloc[-10]) * 100

        # RSI hesapla (14 periyot)
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        last_loss = loss.iloc[-1]
        last_gain = gain.iloc[-1]
        if last_loss == 0:
            rsi = 100.0
        else:
            rs = last_gain / last_loss
            rsi = 100 - (100 / (1 + rs))

        # Volatilite (son 20 günlük std / ort)
        volatility_pct = (close.pct_change().rolling(20).std().iloc[-1] or 0) * 100
        if volatility_pct > 2:
            volatility = "Yüksek"
        elif volatility_pct > 1:
            volatility = "Orta"
        else:
            volatility = "Düşük"

        # Piyasa koşulu ve trend
        if current > sma20 > sma50 and momentum > 2:
            condition = "bullish"
            trend = "Güçlü Yükseliş"
            trend_direction = "up"
            recommendation = "Piyasa güçlü yükseliş trendinde. AL sinyallerine daha yüksek güven."
        elif current < sma20 < sma50 and momentum < -2:
            condition = "bearish"
            trend = "Güçlü Düşüş"
            trend_direction = "down"
            recommendation = "Piyasa güçlü düşüş trendinde. Yeni AL pozisyonlarından kaçının."
        elif current > sma20:
            condition = "bullish"
            trend = "Hafif Yükseliş"
            trend_direction = "up"
            recommendation = "Piyasa hafif pozitif. Seçici AL fırsatları değerlendirilebilir."
        elif current < sma20:
            condition = "bearish"
            trend = "Hafif Düşüş"
            trend_direction = "down"
            recommendation = "Piyasa zayıf seyirde. Dikkatli olun, stop-loss seviyelerine uyun."
        else:
            condition = "neutral"
            trend = "Yatay"
            trend_direction = "neutral"
            recommendation = "Piyasa yatay seyrediyor. Net bir yön oluşana kadar bekleyin."

        return {
            "condition": condition,
            "trend": trend,
            "volatility": volatility,
            "recommendation": recommendation,
            "details": {
                "rsi": round(float(rsi), 1),
                "trend_direction": trend_direction,
                "above_sma20": bool(current > sma20),
                "above_sma50": bool(current > sma50)
            }
        }
