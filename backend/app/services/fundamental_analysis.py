"""
HisseRadar Temel Analiz Servisi
================================
F/K, PD/DD, piyasa değeri, bilanço özeti gibi temel verileri çeker
"""

import yfinance as yf
from typing import Dict, Any, Optional
from datetime import datetime
from cachetools import TTLCache

from ..config import BIST_SUFFIX, get_settings


class FundamentalAnalyzer:
    """
    Temel analiz verilerini çeken ve işleyen sınıf.
    yfinance API'sinden şirket finansal verilerini alır.
    """
    
    def __init__(self):
        """FundamentalAnalyzer başlatıcı"""
        self.settings = get_settings()
        self._cache = TTLCache(maxsize=100, ttl=self.settings.CACHE_TTL_FUNDAMENTAL)
    
    def _get_yf_symbol(self, symbol: str) -> str:
        """Sembolü yfinance formatına çevir"""
        symbol = symbol.upper().strip()
        if not symbol.endswith(BIST_SUFFIX):
            return f"{symbol}{BIST_SUFFIX}"
        return symbol
    
    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """
        Hisse için temel analiz verilerini getir.
        
        Temel Analiz Metrikleri:
        
        DEĞERLEME ORANLARI:
        - F/K (P/E): Fiyat/Kazanç - Düşük değer ucuzluk gösterir
        - PD/DD (P/B): Piyasa Değeri/Defter Değeri - <1 ise defter değerinin altında
        - F/S (P/S): Fiyat/Satış - Sektör ortalamasıyla karşılaştırılmalı
        
        KÂRLILIK ORANLARI:
        - ROE: Özkaynak Kârlılığı - >%15 iyi kabul edilir
        - ROA: Aktif Kârlılık - Varlık kullanım etkinliği
        - Kâr Marjı: Net kâr/Gelir - Yüksek değer iyidir
        
        Args:
            symbol: Hisse sembolü (örn: THYAO)
            
        Returns:
            Temel analiz verilerini içeren dictionary
        """
        cache_key = f"fundamental_{symbol}"
        
        # Cache kontrolü
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            yf_symbol = self._get_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            # Temel verileri çıkar
            result = {
                "symbol": symbol,
                "company_name": info.get("longName") or info.get("shortName", symbol),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "website": info.get("website"),
                "description": info.get("longBusinessSummary"),
                
                # Fiyat Verileri
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose"),
                "open": info.get("open"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
                "50_day_average": info.get("fiftyDayAverage"),
                "200_day_average": info.get("twoHundredDayAverage"),
                
                # Değerleme Oranları
                "pe_ratio": self._safe_round(info.get("trailingPE")),
                "forward_pe": self._safe_round(info.get("forwardPE")),
                "pb_ratio": self._safe_round(info.get("priceToBook")),
                "ps_ratio": self._safe_round(info.get("priceToSalesTrailing12Months")),
                "peg_ratio": self._safe_round(info.get("pegRatio")),
                "enterprise_to_revenue": self._safe_round(info.get("enterpriseToRevenue")),
                "enterprise_to_ebitda": self._safe_round(info.get("enterpriseToEbitda")),
                
                # Piyasa Verileri
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "volume": info.get("volume"),
                "average_volume": info.get("averageVolume"),
                "average_volume_10d": info.get("averageVolume10days"),
                
                # Kârlılık Oranları
                "profit_margin": self._to_percentage(info.get("profitMargins")),
                "operating_margin": self._to_percentage(info.get("operatingMargins")),
                "gross_margin": self._to_percentage(info.get("grossMargins")),
                "ebitda_margin": self._to_percentage(info.get("ebitdaMargins")),
                "roe": self._to_percentage(info.get("returnOnEquity")),
                "roa": self._to_percentage(info.get("returnOnAssets")),
                
                # Temettü Bilgileri
                "dividend_yield": self._to_percentage(info.get("dividendYield")),
                "dividend_rate": info.get("dividendRate"),
                "payout_ratio": self._to_percentage(info.get("payoutRatio")),
                "ex_dividend_date": self._format_timestamp(info.get("exDividendDate")),
                
                # Bilanço Verileri
                "total_revenue": info.get("totalRevenue"),
                "revenue_per_share": self._safe_round(info.get("revenuePerShare")),
                "total_cash": info.get("totalCash"),
                "total_cash_per_share": self._safe_round(info.get("totalCashPerShare")),
                "total_debt": info.get("totalDebt"),
                "debt_to_equity": self._safe_round(info.get("debtToEquity")),
                "current_ratio": self._safe_round(info.get("currentRatio")),
                "quick_ratio": self._safe_round(info.get("quickRatio")),
                "book_value": self._safe_round(info.get("bookValue")),
                
                # Hisse Verileri
                "shares_outstanding": info.get("sharesOutstanding"),
                "float_shares": info.get("floatShares"),
                "shares_short": info.get("sharesShort"),
                "short_ratio": self._safe_round(info.get("shortRatio")),
                
                # Büyüme Verileri
                "earnings_growth": self._to_percentage(info.get("earningsGrowth")),
                "revenue_growth": self._to_percentage(info.get("revenueGrowth")),
                "earnings_quarterly_growth": self._to_percentage(info.get("earningsQuarterlyGrowth")),
                
                # EPS Verileri
                "trailing_eps": self._safe_round(info.get("trailingEps")),
                "forward_eps": self._safe_round(info.get("forwardEps")),
                
                # Beta
                "beta": self._safe_round(info.get("beta")),
                
                # Tarihler
                "updated_at": datetime.now().isoformat()
            }
            
            # Analiz özeti ekle
            result["analysis_summary"] = self._generate_analysis_summary(result)
            
            # Cache'e kaydet
            self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"Hata: {symbol} temel analiz verisi alınamadı - {str(e)}")
            return {
                "symbol": symbol,
                "error": str(e),
                "updated_at": datetime.now().isoformat()
            }
    
    def _safe_round(self, value: Any, decimals: int = 2) -> Optional[float]:
        """Güvenli yuvarlama"""
        if value is None:
            return None
        try:
            return round(float(value), decimals)
        except (ValueError, TypeError):
            return None
    
    def _to_percentage(self, value: Any) -> Optional[float]:
        """Değeri yüzdeye çevir"""
        if value is None:
            return None
        try:
            return round(float(value) * 100, 2)
        except (ValueError, TypeError):
            return None
    
    def _format_timestamp(self, timestamp: Any) -> Optional[str]:
        """Unix timestamp'i tarihe çevir"""
        if timestamp is None:
            return None
        try:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError):
            return None
    
    def _format_large_number(self, value: Any) -> Optional[str]:
        """Büyük sayıları okunabilir formata çevir"""
        if value is None:
            return None
        try:
            value = float(value)
            if value >= 1e12:
                return f"{value/1e12:.2f}T"
            elif value >= 1e9:
                return f"{value/1e9:.2f}B"
            elif value >= 1e6:
                return f"{value/1e6:.2f}M"
            elif value >= 1e3:
                return f"{value/1e3:.2f}K"
            else:
                return f"{value:.2f}"
        except (ValueError, TypeError):
            return None
    
    def _generate_analysis_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Temel analiz verilerinden özet ve değerlendirme oluştur.
        
        Returns:
            Analiz özeti ve öneriler
        """
        summary = {
            "valuation": "Belirsiz",
            "profitability": "Belirsiz",
            "growth": "Belirsiz",
            "dividend": "Belirsiz",
            "overall": "Nötr",
            "notes": []
        }
        
        # Değerleme Analizi
        pe = data.get("pe_ratio")
        pb = data.get("pb_ratio")
        
        if pe is not None:
            if pe < 0:
                summary["valuation"] = "Zarar"
                summary["notes"].append("Şirket zararda (Negatif F/K)")
            elif pe < 10:
                summary["valuation"] = "Ucuz"
                summary["notes"].append(f"F/K oranı düşük ({pe})")
            elif pe < 20:
                summary["valuation"] = "Normal"
            elif pe < 30:
                summary["valuation"] = "Pahalı"
                summary["notes"].append(f"F/K oranı yüksek ({pe})")
            else:
                summary["valuation"] = "Çok Pahalı"
                summary["notes"].append(f"F/K oranı çok yüksek ({pe})")
        
        if pb is not None and pb < 1:
            summary["notes"].append(f"Defter değerinin altında işlem görüyor (PD/DD: {pb})")
        
        # Kârlılık Analizi
        roe = data.get("roe")
        profit_margin = data.get("profit_margin")
        
        if roe is not None:
            if roe > 20:
                summary["profitability"] = "Mükemmel"
                summary["notes"].append(f"Yüksek özkaynak kârlılığı (ROE: %{roe})")
            elif roe > 15:
                summary["profitability"] = "İyi"
            elif roe > 10:
                summary["profitability"] = "Orta"
            elif roe > 0:
                summary["profitability"] = "Zayıf"
            else:
                summary["profitability"] = "Zarar"
        
        # Büyüme Analizi
        revenue_growth = data.get("revenue_growth")
        earnings_growth = data.get("earnings_growth")
        
        if revenue_growth is not None:
            if revenue_growth > 20:
                summary["growth"] = "Yüksek Büyüme"
                summary["notes"].append(f"Güçlü gelir büyümesi (%{revenue_growth})")
            elif revenue_growth > 10:
                summary["growth"] = "Büyüme"
            elif revenue_growth > 0:
                summary["growth"] = "Yavaş Büyüme"
            else:
                summary["growth"] = "Küçülme"
                summary["notes"].append(f"Gelirler düşüşte (%{revenue_growth})")
        
        # Temettü Analizi
        dividend_yield = data.get("dividend_yield")
        
        if dividend_yield is not None:
            if dividend_yield > 5:
                summary["dividend"] = "Yüksek Temettü"
                summary["notes"].append(f"Cazip temettü verimi (%{dividend_yield})")
            elif dividend_yield > 2:
                summary["dividend"] = "Orta Temettü"
            elif dividend_yield > 0:
                summary["dividend"] = "Düşük Temettü"
            else:
                summary["dividend"] = "Temettü Yok"
        
        # Genel Değerlendirme
        scores = {
            "Ucuz": 2, "Normal": 1, "Pahalı": -1, "Çok Pahalı": -2,
            "Mükemmel": 2, "İyi": 1, "Orta": 0, "Zayıf": -1, "Zarar": -2,
            "Yüksek Büyüme": 2, "Büyüme": 1, "Yavaş Büyüme": 0, "Küçülme": -2,
            "Yüksek Temettü": 2, "Orta Temettü": 1, "Düşük Temettü": 0
        }
        
        total_score = 0
        for key in ["valuation", "profitability", "growth", "dividend"]:
            total_score += scores.get(summary[key], 0)
        
        if total_score >= 4:
            summary["overall"] = "Güçlü Al"
        elif total_score >= 2:
            summary["overall"] = "Al"
        elif total_score >= -1:
            summary["overall"] = "Tut"
        elif total_score >= -3:
            summary["overall"] = "Azalt"
        else:
            summary["overall"] = "Sat"
        
        return summary
    
    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """
        Detaylı finansal tabloları getir.
        
        Args:
            symbol: Hisse sembolü
            
        Returns:
            Gelir tablosu, bilanço ve nakit akış tablosu
        """
        try:
            yf_symbol = self._get_yf_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            result = {
                "symbol": symbol,
                "income_statement": None,
                "balance_sheet": None,
                "cash_flow": None
            }
            
            # Gelir Tablosu
            try:
                income = ticker.income_stmt
                if income is not None and not income.empty:
                    result["income_statement"] = income.to_dict()
            except:
                pass
            
            # Bilanço
            try:
                balance = ticker.balance_sheet
                if balance is not None and not balance.empty:
                    result["balance_sheet"] = balance.to_dict()
            except:
                pass
            
            # Nakit Akış
            try:
                cash = ticker.cashflow
                if cash is not None and not cash.empty:
                    result["cash_flow"] = cash.to_dict()
            except:
                pass
            
            return result
            
        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e)
            }


# Singleton instance
_fundamental_analyzer: Optional[FundamentalAnalyzer] = None


def get_fundamental_analyzer() -> FundamentalAnalyzer:
    """FundamentalAnalyzer singleton instance'ı döndür"""
    global _fundamental_analyzer
    if _fundamental_analyzer is None:
        _fundamental_analyzer = FundamentalAnalyzer()
    return _fundamental_analyzer
