"""
BorsaPy Veri Çekici Servisi
============================
borsapy kütüphanesi üzerinden BIST hisse, endeks, döviz, kripto,
fon, teknik analiz ve temel analiz verilerini çeker.

Veri Kaynakları: İş Yatırım, TradingView, KAP, TCMB, BtcTurk, TEFAS, doviz.com
"""

import borsapy as bp
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
from cachetools import TTLCache


# ==========================================
# Period Mapping: uygulama period → borsapy
# ==========================================
PERIOD_MAP = {
    "1d": "1d",
    "5d": "5d",
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    "max": "max",
    # borsapy native period'ları da ingilizce'ye çevir
    "1g": "1d",
    "5g": "5d",
    "1ay": "1mo",
    "3ay": "3mo",
    "6ay": "6mo",
}

INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "1d": "1d",
    "1wk": "1d",   # borsapy haftalık yok, günlük alıp resample edilebilir
    "1mo": "1d",
}


class BorsapyFetcher:
    """
    borsapy kütüphanesi üzerinden kapsamlı veri çekme servisi.
    
    Desteklenen varlık sınıfları:
    - Hisse Senedi (Ticker)
    - Endeks (Index)
    - Döviz ve Emtia (FX)
    - Kripto Para (Crypto)
    - Yatırım Fonu (Fund)
    """
    
    def __init__(self):
        self._ticker_cache = TTLCache(maxsize=200, ttl=300)      # 5 dk
        self._info_cache = TTLCache(maxsize=200, ttl=600)         # 10 dk
        self._history_cache = TTLCache(maxsize=500, ttl=300)      # 5 dk
        self._fundamental_cache = TTLCache(maxsize=100, ttl=3600) # 1 saat
    
    # ==========================================
    # Ticker (Hisse) İşlemleri
    # ==========================================
    
    def _get_ticker(self, symbol: str) -> bp.Ticker:
        """Ticker nesnesini cache'li olarak al"""
        symbol = symbol.upper().strip().replace(".IS", "")
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = bp.Ticker(symbol)
        return self._ticker_cache[symbol]
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Güncel fiyat bilgilerini çek (borsapy fast_info).
        
        Returns:
            {price, previous_close, day_high, day_low, volume, market_cap, ...}
        """
        try:
            symbol = symbol.upper().strip().replace(".IS", "")
            ticker = self._get_ticker(symbol)
            fast = ticker.fast_info
            
            return {
                "symbol": symbol,
                "price": getattr(fast, "last_price", None),
                "previous_close": getattr(fast, "previous_close", None),
                "day_high": getattr(fast, "day_high", None),
                "day_low": getattr(fast, "day_low", None),
                "volume": getattr(fast, "volume", None),
                "market_cap": getattr(fast, "market_cap", None),
                "pe_ratio": getattr(fast, "pe_ratio", None),
                "free_float": getattr(fast, "free_float", None),
                "foreign_ratio": getattr(fast, "foreign_ratio", None),
                "fifty_two_week_high": getattr(fast, "year_high", None),
                "fifty_two_week_low": getattr(fast, "year_low", None),
                "name": None,  # info'dan gelecek
            }
        except Exception as e:
            print(f"borsapy fiyat hatası ({symbol}): {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Detaylı hisse bilgisi (borsapy Ticker.info).
        
        Returns:
            Kapsamlı hisse bilgileri: fiyat, sektör, F/K, temettü, vb.
        """
        cache_key = f"info_{symbol}"
        if cache_key in self._info_cache:
            return self._info_cache[cache_key]
        
        try:
            symbol = symbol.upper().strip().replace(".IS", "")
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            result = {
                "symbol": symbol,
                "name": info.get("longName") or info.get("shortName") or symbol,
                "last_price": info.get("last"),
                "previous_close": info.get("previousClose"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "website": info.get("website"),
                "description": info.get("longBusinessSummary"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "beta": info.get("beta"),
                "volume": info.get("volume"),
                "avg_volume": info.get("averageVolume"),
            }
            
            self._info_cache[cache_key] = result
            return result
        except Exception as e:
            print(f"borsapy info hatası ({symbol}): {e}")
            return None
    
    def get_history(
        self,
        symbol: str,
        period: str = "3mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Hisse senedi geçmiş OHLCV verilerini çek.
        
        Args:
            symbol: Hisse sembolü (THYAO, GARAN, vb.)
            period: Veri periyodu (1d, 5d, 1mo, 3mo, 6mo, 1y, max)
            interval: Veri aralığı (1m, 5m, 15m, 30m, 1h, 1d)
        
        Returns:
            DataFrame: Open, High, Low, Close, Volume sütunları
        """
        symbol = symbol.upper().strip().replace(".IS", "")
        bp_period = PERIOD_MAP.get(period, period)
        bp_interval = INTERVAL_MAP.get(interval, interval)
        
        cache_key = f"hist_{symbol}_{bp_period}_{bp_interval}"
        if cache_key in self._history_cache:
            return self._history_cache[cache_key]
        
        try:
            ticker = self._get_ticker(symbol)
            df = ticker.history(period=bp_period, interval=bp_interval)
            
            if df is None or df.empty:
                return None
            
            # Sütun isimlerini standartlaştır (küçük harf)
            df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]
            
            # Gerekli sütunların varlığını doğrula
            required = ["open", "high", "low", "close", "volume"]
            available = [c for c in required if c in df.columns]
            if "close" not in available:
                return None
            
            df = df[available]
            
            # Timezone temizliği
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                df.index = df.index.tz_convert(None)
            
            # NaN temizliği
            df = df.dropna(subset=["close"])
            
            self._history_cache[cache_key] = df
            return df
            
        except Exception as e:
            print(f"borsapy history hatası ({symbol}): {e}")
            return None
    
    def download_multiple(
        self,
        symbols: List[str],
        period: str = "1mo"
    ) -> Optional[pd.DataFrame]:
        """
        Çoklu hisse verisi indir (borsapy.download).
        """
        try:
            clean_symbols = [s.upper().strip().replace(".IS", "") for s in symbols]
            bp_period = PERIOD_MAP.get(period, period)
            df = bp.download(clean_symbols, period=bp_period)
            return df
        except Exception as e:
            print(f"borsapy download hatası: {e}")
            return None
    
    # ==========================================
    # Finansal Tablolar
    # ==========================================
    
    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """
        Finansal tabloları çek: Bilanço, Gelir Tablosu, Nakit Akış.
        """
        cache_key = f"fin_{symbol}"
        if cache_key in self._fundamental_cache:
            return self._fundamental_cache[cache_key]
        
        try:
            symbol = symbol.upper().strip().replace(".IS", "")
            ticker = self._get_ticker(symbol)
            
            result = {
                "symbol": symbol,
                "balance_sheet": None,
                "income_statement": None,
                "cashflow": None,
                "quarterly_balance_sheet": None,
                "quarterly_income_statement": None,
                "quarterly_cashflow": None,
            }
            
            try:
                bs = ticker.balance_sheet
                if bs is not None and not bs.empty:
                    result["balance_sheet"] = bs.to_dict()
            except Exception:
                pass
            
            try:
                inc = ticker.income_stmt
                if inc is not None and not inc.empty:
                    result["income_statement"] = inc.to_dict()
            except Exception:
                pass
            
            try:
                cf = ticker.cashflow
                if cf is not None and not cf.empty:
                    result["cashflow"] = cf.to_dict()
            except Exception:
                pass
            
            try:
                qbs = ticker.quarterly_balance_sheet
                if qbs is not None and not qbs.empty:
                    result["quarterly_balance_sheet"] = qbs.to_dict()
            except Exception:
                pass
            
            try:
                qinc = ticker.quarterly_income_stmt
                if qinc is not None and not qinc.empty:
                    result["quarterly_income_statement"] = qinc.to_dict()
            except Exception:
                pass
            
            try:
                qcf = ticker.quarterly_cashflow
                if qcf is not None and not qcf.empty:
                    result["quarterly_cashflow"] = qcf.to_dict()
            except Exception:
                pass
            
            self._fundamental_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"borsapy finansal tablo hatası ({symbol}): {e}")
            return {"symbol": symbol, "error": str(e)}
    
    def get_dividends(self, symbol: str) -> Optional[Any]:
        """Temettü geçmişi"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.dividends
        except Exception:
            return None
    
    def get_major_holders(self, symbol: str) -> Optional[Any]:
        """Ortaklık yapısı"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.major_holders
        except Exception:
            return None
    
    def get_analyst_targets(self, symbol: str) -> Optional[Dict]:
        """Analist hedef fiyatları"""
        try:
            ticker = self._get_ticker(symbol)
            return {
                "price_targets": ticker.analyst_price_targets,
                "recommendations": ticker.recommendations_summary,
            }
        except Exception:
            return None
    
    def get_kap_news(self, symbol: str) -> Optional[list]:
        """KAP bildirimleri - her zaman list döndürür"""
        try:
            import pandas as pd
            ticker = self._get_ticker(symbol)
            result = ticker.news
            
            if result is None:
                return None
            
            # DataFrame ise dict listesine çevir
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    return None
                return result.to_dict(orient="records")
            elif isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
            else:
                return None
        except Exception as e:
            print(f"borsapy KAP news hatası ({symbol}): {e}")
            return None
    
    # ==========================================
    # Teknik Analiz (borsapy built-in)
    # ==========================================
    
    def get_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """RSI değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.rsi(rsi_period=period)
        except Exception:
            return None
    
    def get_macd(self, symbol: str) -> Optional[Dict[str, float]]:
        """MACD değerlerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.macd()
        except Exception:
            return None
    
    def get_bollinger_bands(self, symbol: str) -> Optional[Dict[str, float]]:
        """Bollinger Bands değerlerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.bollinger_bands()
        except Exception:
            return None
    
    def get_sma(self, symbol: str, period: int = 20) -> Optional[float]:
        """SMA değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.sma(sma_period=period)
        except Exception:
            return None
    
    def get_ema(self, symbol: str, period: int = 12) -> Optional[float]:
        """EMA değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.ema(ema_period=period)
        except Exception:
            return None
    
    def get_stochastic(self, symbol: str) -> Optional[Dict[str, float]]:
        """Stochastic değerlerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.stochastic()
        except Exception:
            return None
    
    def get_atr(self, symbol: str) -> Optional[float]:
        """ATR değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.atr()
        except Exception:
            return None
    
    def get_adx(self, symbol: str) -> Optional[float]:
        """ADX değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.adx()
        except Exception:
            return None
    
    def get_obv(self, symbol: str) -> Optional[float]:
        """OBV değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.obv()
        except Exception:
            return None
    
    def get_vwap(self, symbol: str) -> Optional[float]:
        """VWAP değerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.vwap()
        except Exception:
            return None
    
    def get_supertrend(self, symbol: str) -> Optional[Dict]:
        """Supertrend değerlerini al"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.supertrend()
        except Exception:
            return None
    
    def get_ta_signals(self, symbol: str, interval: str = "1d") -> Optional[Dict]:
        """
        TradingView teknik analiz sinyalleri (AL/SAT/TUT).
        
        Returns:
            {summary: {recommendation, buy, sell, neutral},
             oscillators: {...}, moving_averages: {...}}
        """
        try:
            ticker = self._get_ticker(symbol)
            return ticker.ta_signals(interval=interval)
        except Exception:
            return None
    
    def get_all_ta_signals(self, symbol: str) -> Optional[Dict]:
        """Tüm timeframe'lerdeki teknik sinyaller"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.ta_signals_all_timeframes()
        except Exception:
            return None
    
    def get_history_with_indicators(
        self, symbol: str, period: str = "3mo",
        indicators: Optional[List[str]] = None
    ) -> Optional[pd.DataFrame]:
        """OHLCV + tüm teknik göstergeler tek DataFrame'de"""
        try:
            ticker = self._get_ticker(symbol)
            bp_period = PERIOD_MAP.get(period, period)
            if indicators:
                return ticker.history_with_indicators(period=bp_period, indicators=indicators)
            return ticker.history_with_indicators(period=bp_period)
        except Exception:
            return None
    
    def get_technicals(self, symbol: str, period: str = "1y"):
        """TechnicalAnalyzer nesnesi al"""
        try:
            ticker = self._get_ticker(symbol)
            bp_period = PERIOD_MAP.get(period, period)
            return ticker.technicals(period=bp_period)
        except Exception:
            return None
    
    def get_heikin_ashi(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Heikin Ashi verileri"""
        try:
            ticker = self._get_ticker(symbol)
            bp_period = PERIOD_MAP.get(period, period)
            return ticker.heikin_ashi(period=bp_period)
        except Exception:
            return None
    
    # ==========================================
    # Endeks İşlemleri
    # ==========================================
    
    def get_index_info(self, index_code: str) -> Optional[Dict]:
        """Endeks bilgisi al"""
        try:
            idx = bp.Index(index_code)
            return idx.info
        except Exception:
            return None
    
    def get_index_history(self, index_code: str, period: str = "1ay") -> Optional[pd.DataFrame]:
        """Endeks geçmiş verisi"""
        try:
            idx = bp.Index(index_code)
            bp_period = PERIOD_MAP.get(period, period)
            return idx.history(period=bp_period)
        except Exception:
            return None
    
    def get_index_components(self, index_code: str) -> Optional[List]:
        """Endeks bileşenlerini al"""
        try:
            idx = bp.Index(index_code)
            return idx.components
        except Exception:
            return None
    
    def get_index_component_symbols(self, index_code: str) -> Optional[List[str]]:
        """Endeks sembol listesi"""
        try:
            idx = bp.Index(index_code)
            return idx.component_symbols
        except Exception:
            return None
    
    def get_all_indices(self) -> Optional[List]:
        """Tüm BIST endekslerini listele"""
        try:
            return bp.indices(detailed=True)
        except Exception:
            return None
    
    # ==========================================
    # Döviz ve Emtia (FX)
    # ==========================================
    
    def get_fx_current(self, currency: str) -> Optional[Any]:
        """Güncel döviz kuru"""
        try:
            fx = bp.FX(currency)
            return fx.current
        except Exception:
            return None
    
    def get_fx_history(self, currency: str, period: str = "1ay") -> Optional[pd.DataFrame]:
        """Döviz kuru geçmişi"""
        try:
            fx = bp.FX(currency)
            bp_period = PERIOD_MAP.get(period, period)
            return fx.history(period=bp_period)
        except Exception:
            return None
    
    def get_bank_rates(self, currency: str) -> Optional[Any]:
        """Banka döviz kurları"""
        try:
            fx = bp.FX(currency)
            return fx.bank_rates
        except Exception:
            return None
    
    def get_gold_price(self, gold_type: str = "gram-altin") -> Optional[Any]:
        """Altın fiyatı"""
        try:
            gold = bp.FX(gold_type)
            return gold.current
        except Exception:
            return None
    
    # ==========================================
    # Kripto Para
    # ==========================================
    
    def get_crypto_current(self, pair: str = "BTCTRY") -> Optional[Any]:
        """Güncel kripto fiyatı"""
        try:
            crypto = bp.Crypto(pair)
            return crypto.current
        except Exception:
            return None
    
    def get_crypto_history(self, pair: str, period: str = "1ay") -> Optional[pd.DataFrame]:
        """Kripto geçmiş verisi"""
        try:
            crypto = bp.Crypto(pair)
            bp_period = PERIOD_MAP.get(period, period)
            return crypto.history(period=bp_period)
        except Exception:
            return None
    
    # ==========================================
    # Yatırım Fonları (TEFAS)
    # ==========================================
    
    def get_fund_info(self, fund_code: str) -> Optional[Dict]:
        """Fon bilgisi"""
        try:
            fund = bp.Fund(fund_code)
            return fund.info
        except Exception:
            return None
    
    def get_fund_history(self, fund_code: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Fon geçmiş verisi"""
        try:
            fund = bp.Fund(fund_code)
            bp_period = PERIOD_MAP.get(period, period)
            return fund.history(period=bp_period)
        except Exception:
            return None
    
    def get_fund_allocation(self, fund_code: str) -> Optional[Any]:
        """Fon varlık dağılımı"""
        try:
            fund = bp.Fund(fund_code)
            return fund.allocation
        except Exception:
            return None
    
    def search_funds(self, query: str) -> Optional[Any]:
        """Fon arama"""
        try:
            return bp.search_funds(query)
        except Exception:
            return None
    
    def screen_funds(self, **kwargs) -> Optional[pd.DataFrame]:
        """Fon tarama"""
        try:
            return bp.screen_funds(**kwargs)
        except Exception:
            return None
    
    # ==========================================
    # Hisse Tarama (Screener)
    # ==========================================
    
    def screen_stocks(self, **kwargs) -> Optional[pd.DataFrame]:
        """
        BIST hisselerini kriterlere göre tara.
        
        Şablonlar: high_dividend, low_pe, high_roe, high_upside, vb.
        Filtreler: pe_max, dividend_yield_min, roe_min, pb_max, vb.
        """
        try:
            return bp.screen_stocks(**kwargs)
        except Exception:
            return None
    
    def scan_stocks(self, index: str, condition: str, interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Teknik tarama.
        
        Örnek: scan_stocks("XU030", "rsi < 30 and volume > 1000000")
        """
        try:
            return bp.scan(index, condition, interval=interval)
        except Exception:
            return None
    
    # ==========================================
    # Makro Ekonomi
    # ==========================================
    
    def get_bonds(self) -> Optional[Any]:
        """Devlet tahvili faiz oranları"""
        try:
            return bp.bonds()
        except Exception:
            return None
    
    def get_risk_free_rate(self) -> Optional[float]:
        """Risk-free rate (10Y tahvil)"""
        try:
            return bp.risk_free_rate()
        except Exception:
            return None
    
    def get_inflation(self) -> Optional[Any]:
        """Enflasyon verileri"""
        try:
            enf = bp.Inflation()
            return enf.latest()
        except Exception:
            return None
    
    def get_tcmb_rates(self) -> Optional[Dict]:
        """TCMB faiz oranları"""
        try:
            tcmb = bp.TCMB()
            return {
                "policy_rate": tcmb.policy_rate,
                "overnight": tcmb.overnight,
                "late_liquidity": tcmb.late_liquidity,
            }
        except Exception:
            return None
    
    def get_economic_calendar(self, period: str = "1w", country: str = "TR") -> Optional[Any]:
        """Ekonomik takvim"""
        try:
            return bp.economic_calendar(period=period, country=country)
        except Exception:
            return None
    
    # ==========================================
    # Arama
    # ==========================================
    
    def search(self, query: str) -> Optional[List]:
        """Genel sembol arama"""
        try:
            return bp.search(query)
        except Exception:
            return None
    
    def search_bist(self, query: str) -> Optional[List]:
        """Sadece BIST hisse arama"""
        try:
            return bp.search_bist(query)
        except Exception:
            return None
    
    # ==========================================
    # ETF Sahipliği
    # ==========================================
    
    def get_etf_holders(self, symbol: str) -> Optional[Any]:
        """Uluslararası ETF sahiplik bilgisi"""
        try:
            ticker = self._get_ticker(symbol)
            return ticker.etf_holders
        except Exception:
            return None
    
    # ==========================================
    # Eurobond
    # ==========================================
    
    def get_eurobonds(self, currency: str = None) -> Optional[Any]:
        """Türk devlet eurobondları"""
        try:
            if currency:
                return bp.eurobonds(currency=currency)
            return bp.eurobonds()
        except Exception:
            return None
    
    # ==========================================
    # VIOP (Vadeli İşlem/Opsiyon)
    # ==========================================
    
    def get_viop_futures(self) -> Optional[Any]:
        """Vadeli işlem kontratları"""
        try:
            viop = bp.VIOP()
            return viop.futures
        except Exception:
            return None
    
    def get_viop_options(self) -> Optional[Any]:
        """Opsiyon kontratları"""
        try:
            viop = bp.VIOP()
            return viop.options
        except Exception:
            return None
    
    # ==========================================
    # Şirket Listesi
    # ==========================================
    
    def get_companies(self) -> Optional[Any]:
        """BIST şirketlerini listele"""
        try:
            return bp.companies()
        except Exception:
            return None
    
    def search_companies(self, query: str) -> Optional[Any]:
        """Şirket arama"""
        try:
            return bp.search_companies(query)
        except Exception:
            return None


# ==========================================
# Singleton Instance
# ==========================================

_borsapy_fetcher: Optional[BorsapyFetcher] = None


def get_borsapy_fetcher() -> BorsapyFetcher:
    """BorsapyFetcher singleton instance döndür"""
    global _borsapy_fetcher
    if _borsapy_fetcher is None:
        _borsapy_fetcher = BorsapyFetcher()
    return _borsapy_fetcher
