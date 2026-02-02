"""
Yahoo Finance API Direct Fetcher
================================
yfinance yerine dogrudan Yahoo Finance API kullanan veri cekici
"""

import requests
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class YahooFinanceFetcher:
    """Yahoo Finance API'den dogrudan veri ceken sinif"""
    
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    def get_history(self, symbol: str, period: str = "3mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Hisse senedi gecmis verilerini cek
        
        Args:
            symbol: Hisse sembolü (örn: THYAO.IS)
            period: Veri periyodu (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Veri aralığı (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            pandas DataFrame veya None
        """
        try:
            url = f"{self.BASE_URL}/{symbol}"
            params = {
                "interval": interval,
                "range": period,
                "includePrePost": "false",
                "events": "div,splits"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"{symbol}: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
                print(f"{symbol}: No chart data")
                return None
            
            result = data["chart"]["result"][0]
            
            if "timestamp" not in result or not result["timestamp"]:
                print(f"{symbol}: No timestamp data")
                return None
            
            timestamps = result["timestamp"]
            indicators = result.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            adjclose = indicators.get("adjclose", [{}])
            
            # DataFrame olustur
            df = pd.DataFrame({
                "Open": quote.get("open", []),
                "High": quote.get("high", []),
                "Low": quote.get("low", []),
                "Close": quote.get("close", []),
                "Volume": quote.get("volume", []),
                "Adj Close": adjclose[0].get("adjclose", quote.get("close", [])) if adjclose else quote.get("close", [])
            }, index=pd.to_datetime(timestamps, unit='s'))
            
            df.index.name = "Date"
            
            # None degerleri temizle
            df = df.dropna()
            
            return df
            
        except requests.exceptions.Timeout:
            print(f"{symbol}: Timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"{symbol}: Request error - {e}")
            return None
        except Exception as e:
            print(f"{symbol}: Error - {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Guncel fiyat bilgilerini cek"""
        try:
            url = f"{self.BASE_URL}/{symbol}"
            params = {"interval": "1d", "range": "1d"}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
                return None
            
            meta = data["chart"]["result"][0].get("meta", {})
            
            return {
                "symbol": symbol,
                "price": meta.get("regularMarketPrice"),
                "previous_close": meta.get("previousClose") or meta.get("chartPreviousClose"),
                "currency": meta.get("currency"),
                "exchange": meta.get("exchangeName"),
                "name": meta.get("longName") or meta.get("shortName"),
                "market_time": meta.get("regularMarketTime"),
                "day_high": meta.get("regularMarketDayHigh"),
                "day_low": meta.get("regularMarketDayLow"),
                "volume": meta.get("regularMarketVolume"),
                "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
            }
            
        except Exception as e:
            print(f"{symbol}: Price fetch error - {e}")
            return None
    
    def get_historical_prices(self, symbol: str, period: str = "3mo") -> Optional[list]:
        """
        AI tahmin için uygun formatta geçmiş fiyat verileri
        
        Args:
            symbol: Hisse sembolü
            period: Veri periyodu
        
        Returns:
            List[Dict] formatında fiyat verileri
        """
        # Symbol temizleme - .IS varsa tekrar ekleme
        clean_symbol = symbol.replace(".IS", "").replace(".is", "")
        full_symbol = f"{clean_symbol}.IS"
        
        df = self.get_history(full_symbol, period=period, interval="1d")
        
        if df is None or df.empty:
            return None
        
        # AI için uygun formata dönüştür
        result = []
        for date, row in df.iterrows():
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]) if pd.notna(row["Open"]) else 0,
                "high": float(row["High"]) if pd.notna(row["High"]) else 0,
                "low": float(row["Low"]) if pd.notna(row["Low"]) else 0,
                "close": float(row["Close"]) if pd.notna(row["Close"]) else 0,
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0
            })
        
        return result


# Global instance
_fetcher: Optional[YahooFinanceFetcher] = None


def get_yahoo_fetcher() -> YahooFinanceFetcher:
    """Singleton fetcher instance dondur"""
    global _fetcher
    if _fetcher is None:
        _fetcher = YahooFinanceFetcher()
    return _fetcher
