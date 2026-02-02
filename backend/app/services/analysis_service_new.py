    def _format_stock_for_frontend(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Frontend formatina donustur"""
        indicators = stock.get("indicators", {})
        potential = stock.get("potential", {})
        
        # RSI sinyali
        rsi_val = indicators.get("rsi", 50)
        if rsi_val < 30:
            rsi_signal = "AL"
        elif rsi_val > 70:
            rsi_signal = "SAT"
        else:
            rsi_signal = "TUT"
        
        # MACD sinyali
        macd_data = indicators.get("macd", {})
        if macd_data.get("histogram", 0) > 0:
            macd_signal = "AL"
        elif macd_data.get("histogram", 0) < 0:
            macd_signal = "SAT"
        else:
            macd_signal = "TUT"
        
        # Bollinger sinyali
        bb_data = indicators.get("bollinger", {})
        bb_position = bb_data.get("position", 0.5)
        if bb_position < 0.2:
            bb_signal = "AL"
        elif bb_position > 0.8:
            bb_signal = "SAT"
        else:
            bb_signal = "TUT"
        
        # MA trend
        mas = stock.get("moving_averages", {})
        current_price = stock.get("current_price", 0)
        sma20 = mas.get("sma20")
        sma50 = mas.get("sma50")
        if sma20 and sma50:
            if current_price > sma20 > sma50:
                ma_trend = "yukselis"
            elif current_price < sma20 < sma50:
                ma_trend = "dusus"
            else:
                ma_trend = "yatay"
        else:
            ma_trend = "yatay"
        
        # Stochastic sinyali
        stoch = indicators.get("stochastic", {})
        stoch_k = stoch.get("k", 50)
        if stoch_k < 20:
            stoch_signal = "AL"
        elif stoch_k > 80:
            stoch_signal = "SAT"
        else:
            stoch_signal = "TUT"
        
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
                "rsi": rsi_val,
                "rsi_signal": rsi_signal,
                "macd": macd_data.get("macd", 0),
                "macd_signal_line": macd_data.get("signal", 0),
                "macd_histogram": macd_data.get("histogram", 0),
                "macd_signal": macd_signal,
                "bb_position": bb_position,
                "bb_signal": bb_signal,
                "ma_trend": ma_trend,
                "stochastic_k": stoch_k,
                "stochastic_d": stoch.get("d", 50),
                "stoch_signal": stoch_signal,
                "atr": indicators.get("atr", 0),
                "atr_percent": (indicators.get("atr", 0) / current_price * 100) if current_price > 0 else 0
            },
            "potential": {
                "target_percent": potential.get("target_percent", 5),
                "stop_loss_percent": abs(potential.get("stop_loss_percent", -5)),
                "risk_reward_ratio": potential.get("risk_reward_ratio", 1),
                "target_price": potential.get("target_price", current_price * 1.05),
                "stop_loss_price": potential.get("stop_loss_price", current_price * 0.95),
                "potential_profit": potential.get("target_percent", 5),
                "potential_loss": abs(potential.get("stop_loss_percent", -5))
            },
            "reasons": []
        }

    def run_daily_analysis(self, index_filter: Optional[str] = None, sector_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Gunluk analiz calistir"""
        stocks_to_analyze = self._stocks.copy()

        # Filtrele
        if index_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if index_filter in s.get("indexes", [])]
        if sector_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if sector_filter.lower() in s.get("sector", "").lower()]

        results = []
        analyzed = 0
        errors = 0

        # Paralel analiz
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._analyze_single_stock, s["symbol"], "3mo", "1d"): s["symbol"]
                for s in stocks_to_analyze[:min(limit * 2, 100)]  # Max 100 analiz
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        analyzed += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1

        # Skora gore sirala
        results.sort(key=lambda x: x["score"], reverse=True)

        # Frontend formatina donustur
        formatted_results = [self._format_stock_for_frontend(r) for r in results]
        
        # En iyi secimler (AL sinyali verenler)
        top_picks = [r for r in formatted_results if r["score"] >= 55][:limit]
        
        # Sinyalleri say
        buy_signals = len([r for r in formatted_results if r["signal"] in ["GUCLU_AL", "AL"]])
        sell_signals = len([r for r in formatted_results if r["signal"] in ["GUCLU_SAT", "SAT"]])
        strong_buy = len([r for r in formatted_results if r["signal"] == "GUCLU_AL"])
        
        # RSI istatistikleri
        rsi_values = [r["indicators"]["rsi"] for r in formatted_results]
        avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 50
        oversold = len([r for r in rsi_values if r < 30])
        overbought = len([r for r in rsi_values if r > 70])
        
        # Piyasa ozeti
        bullish_pct = (buy_signals / analyzed * 100) if analyzed > 0 else 0
        bearish_pct = (sell_signals / analyzed * 100) if analyzed > 0 else 0
        neutral_pct = 100 - bullish_pct - bearish_pct

        return {
            "analysis_type": "daily",
            "analysis_date": datetime.now().isoformat(),
            "total_analyzed": analyzed,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "strong_buy_count": strong_buy,
            "market_summary": {
                "bullish_percent": round(bullish_pct, 1),
                "bearish_percent": round(bearish_pct, 1),
                "neutral_percent": round(neutral_pct, 1),
                "market_sentiment": "Yukselis Egilimi" if bullish_pct > 50 else ("Dusus Egilimi" if bearish_pct > 50 else "NOTR"),
                "avg_rsi": round(avg_rsi, 1),
                "oversold_count": oversold,
                "overbought_count": overbought
            },
            "top_picks": top_picks,
            "all_results": formatted_results
        }

    def run_weekly_analysis(self, index_filter: Optional[str] = None, sector_filter: Optional[str] = None, limit: int = 30) -> Dict[str, Any]:
        """Haftalik analiz calistir"""
        stocks_to_analyze = self._stocks.copy()

        # Filtrele
        if index_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if index_filter in s.get("indexes", [])]
        if sector_filter:
            stocks_to_analyze = [s for s in stocks_to_analyze if sector_filter.lower() in s.get("sector", "").lower()]

        results = []
        analyzed = 0
        errors = 0

        # Paralel analiz - haftalik verilerle
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._analyze_single_stock, s["symbol"], "6mo", "1wk"): s["symbol"]
                for s in stocks_to_analyze[:min(limit * 2, 60)]
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        analyzed += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1

        # Skora gore sirala
        results.sort(key=lambda x: x["score"], reverse=True)

        # Frontend formatina donustur
        formatted_results = [self._format_stock_for_frontend(r) for r in results]
        
        # En iyi secimler
        top_picks = [r for r in formatted_results if r["score"] >= 55][:limit]
        
        # Sinyalleri say
        buy_signals = len([r for r in formatted_results if r["signal"] in ["GUCLU_AL", "AL"]])
        sell_signals = len([r for r in formatted_results if r["signal"] in ["GUCLU_SAT", "SAT"]])
        strong_buy = len([r for r in formatted_results if r["signal"] == "GUCLU_AL"])
        
        # RSI istatistikleri
        rsi_values = [r["indicators"]["rsi"] for r in formatted_results]
        avg_rsi = sum(rsi_values) / len(rsi_values) if rsi_values else 50
        oversold = len([r for r in rsi_values if r < 30])
        overbought = len([r for r in rsi_values if r > 70])
        
        # Piyasa ozeti
        bullish_pct = (buy_signals / analyzed * 100) if analyzed > 0 else 0
        bearish_pct = (sell_signals / analyzed * 100) if analyzed > 0 else 0
        neutral_pct = 100 - bullish_pct - bearish_pct

        return {
            "analysis_type": "weekly",
            "analysis_date": datetime.now().isoformat(),
            "total_analyzed": analyzed,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "strong_buy_count": strong_buy,
            "market_summary": {
                "bullish_percent": round(bullish_pct, 1),
                "bearish_percent": round(bearish_pct, 1),
                "neutral_percent": round(neutral_pct, 1),
                "market_sentiment": "Yukselis Egilimi" if bullish_pct > 50 else ("Dusus Egilimi" if bearish_pct > 50 else "NOTR"),
                "avg_rsi": round(avg_rsi, 1),
                "oversold_count": oversold,
                "overbought_count": overbought
            },
            "top_picks": top_picks,
            "all_results": formatted_results
        }

    def _calculate_market_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Piyasa ozeti hesapla"""
        if not results:
            return {}

        scores = [r["score"] for r in results]
        signals = [r["signal"] for r in results]

        return {
            "average_score": round(sum(scores) / len(scores), 1),
            "bullish_count": len([s for s in signals if s in ["GUCLU_AL", "AL"]]),
            "bearish_count": len([s for s in signals if s in ["GUCLU_SAT", "SAT"]]),
            "neutral_count": len([s for s in signals if s == "TUT"]),
            "market_sentiment": "YUKARI" if sum(scores) / len(scores) > 55 else ("ASAGI" if sum(scores) / len(scores) < 45 else "NOTR")
        }

    def _get_next_trading_day(self) -> str:
        """Sonraki islem gununu hesapla"""
        today = datetime.now()
        days_ahead = 1

        # Cuma ise Pazartesi
        if today.weekday() == 4:
            days_ahead = 3
        # Cumartesi ise Pazartesi
        elif today.weekday() == 5:
            days_ahead = 2
        # Pazar ise Pazartesi
        elif today.weekday() == 6:
            days_ahead = 1

        next_day = today + timedelta(days=days_ahead)
        return next_day.strftime("%Y-%m-%d")

    def _get_next_week_start(self) -> str:
        """Sonraki hafta baslangicini hesapla"""
        today = datetime.now()
        days_ahead = 7 - today.weekday()  # Sonraki Pazartesi
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        return next_monday.strftime("%Y-%m-%d")


_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
