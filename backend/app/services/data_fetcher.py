"""
HisseRadar Veri Cekme Servisi
==============================
Yahoo Finance API kullanarak BIST hisse verilerini ceker
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from cachetools import TTLCache
import json
from pathlib import Path
import time

from ..config import BIST_SUFFIX, get_settings
from .yahoo_fetcher import get_yahoo_fetcher


class DataFetcher:
    def __init__(self):
        self.settings = get_settings()
        self._price_cache = TTLCache(maxsize=100, ttl=self.settings.CACHE_TTL_PRICE)
        self._info_cache = TTLCache(maxsize=100, ttl=self.settings.CACHE_TTL_FUNDAMENTAL)
        self._stock_list_cache = TTLCache(maxsize=1, ttl=self.settings.CACHE_TTL_STOCK_LIST)
        self._load_stock_list()

    def _load_stock_list(self) -> None:
        try:
            data_path = Path(__file__).parent.parent / "data" / "bist_stocks.json"
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._stocks = data.get("stocks", [])
                self._sectors = data.get("sectors", [])
                self._indexes = data.get("indexes", [])
        except FileNotFoundError:
            print("Uyari: bist_stocks.json bulunamadi")
            self._stocks = []
            self._sectors = []
            self._indexes = []

    def _get_yf_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().strip()
        if not symbol.endswith(BIST_SUFFIX):
            return f"{symbol}{BIST_SUFFIX}"
        return symbol

    def _get_stock_from_list(self, symbol: str) -> Optional[Dict[str, Any]]:
        symbol = symbol.upper().strip()
        for stock in self._stocks:
            if stock.get("symbol", "").upper() == symbol:
                return stock
        return None

    def get_stock_list(self, sector: Optional[str] = None, index: Optional[str] = None) -> List[Dict[str, Any]]:
        stocks = self._stocks.copy()
        if sector:
            stocks = [s for s in stocks if s.get("sector") == sector]
        if index:
            stocks = [s for s in stocks if index in s.get("indexes", [])]
        return stocks

    def get_sectors(self) -> List[str]:
        return self._sectors.copy()

    def get_indexes(self) -> List[Dict[str, str]]:
        return self._indexes.copy()

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        cache_key = f"info_{symbol}"
        if cache_key in self._info_cache:
            return self._info_cache[cache_key]

        local_stock = self._get_stock_from_list(symbol)

        result = {
            "symbol": symbol,
            "name": local_stock.get("name", symbol) if local_stock else symbol,
            "sector": local_stock.get("sector") if local_stock else None,
            "indexes": local_stock.get("indexes", []) if local_stock else [],
            "industry": None,
            "current_price": None,
            "previous_close": None,
            "open": None,
            "day_high": None,
            "day_low": None,
            "volume": None,
            "market_cap": None,
            "currency": "TRY",
            "exchange": "IST",
            "change": None,
            "change_percent": None
        }

        try:
            yf_symbol = self._get_yf_symbol(symbol)
            fetcher = get_yahoo_fetcher()
            
            # Guncel fiyat bilgisi al
            price_info = fetcher.get_current_price(yf_symbol)
            
            if price_info:
                result["current_price"] = price_info.get("price")
                result["previous_close"] = price_info.get("previous_close")
                result["day_high"] = price_info.get("day_high")
                result["day_low"] = price_info.get("day_low")
                result["volume"] = price_info.get("volume")
                
                if price_info.get("name"):
                    result["name"] = price_info.get("name")
                
                if result["current_price"] and result["previous_close"]:
                    change = result["current_price"] - result["previous_close"]
                    change_percent = (change / result["previous_close"]) * 100
                    result["change"] = round(change, 2)
                    result["change_percent"] = round(change_percent, 2)
            
            # Eger guncel fiyat alinamadiysa, gecmis veriden dene
            if not result["current_price"]:
                hist = fetcher.get_history(yf_symbol, period="5d", interval="1d")
                
                if hist is not None and not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]

                    result["current_price"] = float(latest["Close"])
                    result["previous_close"] = float(prev["Close"])
                    result["open"] = float(latest["Open"])
                    result["day_high"] = float(latest["High"])
                    result["day_low"] = float(latest["Low"])
                    result["volume"] = int(latest["Volume"])

                    if result["current_price"] and result["previous_close"]:
                        change = result["current_price"] - result["previous_close"]
                        change_percent = (change / result["previous_close"]) * 100
                        result["change"] = round(change, 2)
                        result["change_percent"] = round(change_percent, 2)

            self._info_cache[cache_key] = result
            return result

        except Exception as e:
            error_msg = str(e)
            print(f"Hata: {symbol} - {error_msg}")
            result["error"] = error_msg
            return result

    def get_price_history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        cache_key = f"price_{symbol}_{period}_{interval}"

        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        try:
            yf_symbol = self._get_yf_symbol(symbol)
            fetcher = get_yahoo_fetcher()
            df = fetcher.get_history(yf_symbol, period=period, interval=interval)

            if df is None or df.empty:
                print(f"Uyari: {symbol} icin veri bulunamadi")
                return pd.DataFrame()

            # Timezone bilgisini kaldir
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)

            # Sutun isimlerini kucuk harfe cevir
            df.columns = df.columns.str.lower()

            # Sadece gerekli sutunlari al
            columns_to_keep = ["open", "high", "low", "close", "volume"]
            df = df[[col for col in columns_to_keep if col in df.columns]]

            self._price_cache[cache_key] = df
            return df

        except Exception as e:
            print(f"Hata: {symbol} fiyat verisi - {str(e)}")
            return pd.DataFrame()

    def get_multiple_stocks_info(self, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        for symbol in symbols:
            info = self.get_stock_info(symbol)
            results.append(info)
            time.sleep(0.2)
        return results

    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        query = query.upper().strip()
        results = []
        for stock in self._stocks:
            symbol = stock.get("symbol", "").upper()
            name = stock.get("name", "").upper()
            if query in symbol or query in name:
                results.append(stock)
        return results[:20]


_data_fetcher: Optional[DataFetcher] = None


def get_data_fetcher() -> DataFetcher:
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher
