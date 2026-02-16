# -*- coding: utf-8 -*-
"""
Grafik ve Görselleştirme Servisi
Mum grafikleri, teknik göstergeler ve sektör analizleri için veri sağlar
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

from .borsapy_fetcher import get_borsapy_fetcher


class ChartService:
    """Grafik verileri için servis sınıfı"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    def get_ohlc_data(self, symbol: str, period: str = "3mo", interval: str = "1d") -> Dict[str, Any]:
        """
        Mum grafikleri için OHLC verileri
        
        Args:
            symbol: Hisse sembolü (örn: ASELS)
            period: Veri periyodu (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Veri aralığı (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo)
        
        Returns:
            OHLC verileri ve teknik göstergeler
        """
        try:
            # borsapy ile .IS suffix gerekmez
            clean_symbol = symbol.replace(".IS", "").upper()
            fetcher = get_borsapy_fetcher()
            
            # Veriyi çek
            df = fetcher.get_history(clean_symbol, period=period, interval=interval)
            
            if df is None or df.empty:
                return {"success": False, "error": "Veri bulunamadı"}
            
            # OHLC verilerini hazırla
            ohlc_data = []
            for idx, row in df.iterrows():
                ohlc_data.append({
                    "time": int(idx.timestamp()),
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(float(row.get("open", 0)), 2),
                    "high": round(float(row.get("high", 0)), 2),
                    "low": round(float(row.get("low", 0)), 2),
                    "close": round(float(row["close"]), 2),
                    "volume": int(row.get("volume", 0))
                })
            
            # Teknik göstergeleri hesapla
            indicators = self._calculate_indicators(df)
            
            # Hisse bilgisi - borsapy'den al
            price_info = fetcher.get_current_price(clean_symbol)
            
            stock_info = {
                "symbol": symbol,
                "name": price_info.get("name", symbol) if price_info else symbol,
                "sector": "Bilinmiyor",
                "currency": price_info.get("currency", "TRY") if price_info else "TRY",
                "currentPrice": round(float(df["close"].iloc[-1]), 2),
                "previousClose": round(float(df["close"].iloc[-2]), 2) if len(df) > 1 else round(float(df["close"].iloc[-1]), 2),
                "change": round(float(df["close"].iloc[-1] - df["close"].iloc[-2]), 2) if len(df) > 1 else 0,
                "changePercent": round(((df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]) * 100, 2) if len(df) > 1 else 0,
                "dayHigh": round(float(df["high"].iloc[-1]), 2) if "high" in df.columns else 0,
                "dayLow": round(float(df["low"].iloc[-1]), 2) if "low" in df.columns else 0,
                "volume": int(df["volume"].iloc[-1]) if "volume" in df.columns else 0,
                "avgVolume": int(df["volume"].mean()) if "volume" in df.columns else 0,
                "marketCap": 0,
                "fiftyTwoWeekHigh": price_info.get("fifty_two_week_high", 0) if price_info else 0,
                "fiftyTwoWeekLow": price_info.get("fifty_two_week_low", 0) if price_info else 0
            }
            
            return {
                "success": True,
                "symbol": symbol,
                "info": stock_info,
                "ohlc": ohlc_data,
                "indicators": indicators,
                "period": period,
                "interval": interval,
                "dataPoints": len(ohlc_data)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, List]:
        """Teknik göstergeleri hesapla"""
        indicators = {}
        
        close = df["close"]
        high = df["high"] if "high" in df.columns else close
        low = df["low"] if "low" in df.columns else close
        volume = df["volume"] if "volume" in df.columns else pd.Series([0] * len(df), index=df.index)
        
        # RSI (14 günlük)
        rsi = self._calculate_rsi(close, 14)
        indicators["rsi"] = [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                            for i, v in enumerate(rsi)]
        
        # MACD
        macd_line, signal_line, histogram = self._calculate_macd(close)
        indicators["macd"] = {
            "macd": [{"time": int(df.index[i].timestamp()), "value": round(v, 4) if not pd.isna(v) else None} 
                    for i, v in enumerate(macd_line)],
            "signal": [{"time": int(df.index[i].timestamp()), "value": round(v, 4) if not pd.isna(v) else None} 
                      for i, v in enumerate(signal_line)],
            "histogram": [{"time": int(df.index[i].timestamp()), "value": round(v, 4) if not pd.isna(v) else None} 
                         for i, v in enumerate(histogram)]
        }
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close)
        indicators["bollinger"] = {
            "upper": [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                     for i, v in enumerate(bb_upper)],
            "middle": [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                      for i, v in enumerate(bb_middle)],
            "lower": [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                     for i, v in enumerate(bb_lower)]
        }
        
        # Moving Averages
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        
        indicators["sma20"] = [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                              for i, v in enumerate(sma_20)]
        indicators["sma50"] = [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                              for i, v in enumerate(sma_50)]
        indicators["ema12"] = [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                              for i, v in enumerate(ema_12)]
        indicators["ema26"] = [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                              for i, v in enumerate(ema_26)]
        
        # Stochastic Oscillator
        stoch_k, stoch_d = self._calculate_stochastic(high, low, close)
        indicators["stochastic"] = {
            "k": [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                 for i, v in enumerate(stoch_k)],
            "d": [{"time": int(df.index[i].timestamp()), "value": round(v, 2) if not pd.isna(v) else None} 
                 for i, v in enumerate(stoch_d)]
        }
        
        # Volume SMA
        vol_sma = volume.rolling(window=20).mean()
        indicators["volumeSma"] = [{"time": int(df.index[i].timestamp()), "value": int(v) if not pd.isna(v) else None} 
                                   for i, v in enumerate(vol_sma)]
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI hesapla"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD hesapla"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """Bollinger Bands hesapla"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                              k_period: int = 14, d_period: int = 3):
        """Stochastic Oscillator hesapla"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        return stoch_k, stoch_d
    
    def get_sector_heatmap(self) -> Dict[str, Any]:
        """Sektör bazlı ısı haritası verileri"""
        try:
            # Veritabanından hisseleri oku
            json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'bist_stocks.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks = data.get('stocks', [])
            fetcher = get_borsapy_fetcher()
            
            # Sektörlere göre grupla
            sector_data = {}
            
            for stock in stocks[:100]:  # İlk 100 hisse için
                symbol = stock['symbol']
                sector = stock.get('sector', 'Diğer')
                
                if sector not in sector_data:
                    sector_data[sector] = {
                        "name": sector,
                        "stocks": [],
                        "totalChange": 0,
                        "stockCount": 0
                    }
                
                try:
                    hist = fetcher.get_history(symbol, period="5d", interval="1d")
                    
                    if hist is not None and len(hist) >= 2:
                        current = hist["close"].iloc[-1]
                        previous = hist["close"].iloc[-2]
                        change = ((current - previous) / previous) * 100
                        
                        sector_data[sector]["stocks"].append({
                            "symbol": symbol,
                            "name": stock.get('name', symbol),
                            "price": round(current, 2),
                            "change": round(change, 2)
                        })
                        sector_data[sector]["totalChange"] += change
                        sector_data[sector]["stockCount"] += 1
                        
                except Exception:
                    continue
            
            # Sektör ortalamalarını hesapla
            heatmap_data = []
            for sector_name, sector_info in sector_data.items():
                if sector_info["stockCount"] > 0:
                    avg_change = sector_info["totalChange"] / sector_info["stockCount"]
                    heatmap_data.append({
                        "sector": sector_name,
                        "avgChange": round(avg_change, 2),
                        "stockCount": sector_info["stockCount"],
                        "stocks": sorted(sector_info["stocks"], key=lambda x: x["change"], reverse=True)[:10]
                    })
            
            # Değişime göre sırala
            heatmap_data.sort(key=lambda x: x["avgChange"], reverse=True)
            
            return {
                "success": True,
                "sectors": heatmap_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_comparison_data(self, symbols: List[str], period: str = "1y") -> Dict[str, Any]:
        """Birden fazla hisse için karşılaştırma verileri"""
        try:
            stocks_data = []
            fetcher = get_borsapy_fetcher()
            
            for symbol in symbols:
                try:
                    hist = fetcher.get_history(symbol, period=period, interval="1d")
                    
                    if hist is None or hist.empty:
                        continue
                    
                    # İlk değeri 100 kabul ederek normalize et
                    first_close = float(hist["close"].iloc[0])
                    last_close = float(hist["close"].iloc[-1])
                    
                    # Volatilite hesapla (günlük getirilerin standart sapması * sqrt(252))
                    daily_returns = hist["close"].pct_change().dropna()
                    volatility = float(daily_returns.std() * np.sqrt(252) * 100) if len(daily_returns) > 0 else 0
                    
                    # Max Drawdown hesapla
                    cumulative = (1 + daily_returns).cumprod()
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = float(drawdown.min() * 100) if len(drawdown) > 0 else 0
                    
                    # Veri hazırla
                    data_points = []
                    for idx, row in hist.iterrows():
                        close_val = float(row["close"])
                        normalized_val = (close_val / first_close) * 100
                        data_points.append({
                            "time": int(idx.timestamp()),
                            "date": idx.strftime("%Y-%m-%d"),
                            "value": round(close_val, 2),
                            "normalizedValue": round(normalized_val, 2)
                        })
                    
                    # Hisse bilgisini al
                    price_info = fetcher.get_current_price(symbol)
                    stock_name = price_info.get("name", symbol) if price_info else symbol
                    
                    stocks_data.append({
                        "symbol": symbol,
                        "name": stock_name,
                        "data": data_points,
                        "startPrice": round(first_close, 2),
                        "endPrice": round(last_close, 2),
                        "totalReturn": round(((last_close - first_close) / first_close) * 100, 2),
                        "volatility": round(volatility, 2),
                        "maxDrawdown": round(max_drawdown, 2),
                        "minPrice": round(float(hist["low"].min()), 2) if "low" in hist.columns else round(float(hist["close"].min()), 2),
                        "maxPrice": round(float(hist["high"].max()), 2) if "high" in hist.columns else round(float(hist["close"].max()), 2)
                    })
                    
                except Exception as e:
                    print(f"Hata ({symbol}): {str(e)}")
                    continue
            
            return {
                "success": True,
                "period": period,
                "symbols": symbols,
                "stocks": stocks_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
chart_service = ChartService()
