"""
HisseRadar Temel Analiz Servisi
================================
borsapy kütüphanesi ile F/K, PD/DD, piyasa değeri, bilanço özeti çeker.
Veri Kaynağı: İş Yatırım, KAP
"""

from typing import Dict, Any, Optional
from datetime import datetime
from cachetools import TTLCache

from ..config import get_settings, normalize_symbol
from .borsapy_fetcher import get_borsapy_fetcher


class FundamentalAnalyzer:
    """
    Temel analiz verilerini çeken ve işleyen sınıf.
    borsapy API'sinden şirket finansal verilerini alır.
    """
    
    def __init__(self):
        """FundamentalAnalyzer başlatıcı"""
        self.settings = get_settings()
        self._cache = TTLCache(maxsize=100, ttl=self.settings.CACHE_TTL_FUNDAMENTAL)
        self._fetcher = get_borsapy_fetcher()
    
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
        """
        symbol = normalize_symbol(symbol)
        cache_key = f"fundamental_{symbol}"
        
        # Cache kontrolü
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # borsapy ile hisse bilgisi al
            info = self._fetcher.get_stock_info(symbol) or {}
            
            # Temel verileri çıkar
            result = {
                "symbol": symbol,
                "company_name": info.get("name", symbol),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "website": info.get("website"),
                "description": info.get("description"),
                
                # Fiyat Verileri
                "current_price": info.get("last_price"),
                "previous_close": info.get("previous_close"),
                "open": None,
                "day_high": None,
                "day_low": None,
                "week_52_high": info.get("52_week_high"),
                "week_52_low": info.get("52_week_low"),
                "50_day_average": None,
                "200_day_average": None,
                
                # Değerleme Oranları
                "pe_ratio": self._safe_round(info.get("pe_ratio")),
                "forward_pe": self._safe_round(info.get("forward_pe")),
                "pb_ratio": self._safe_round(info.get("pb_ratio")),
                "ps_ratio": None,
                "peg_ratio": None,
                "enterprise_to_revenue": None,
                "enterprise_to_ebitda": None,
                
                # Piyasa Verileri
                "market_cap": info.get("market_cap"),
                "enterprise_value": None,
                "volume": info.get("volume"),
                "average_volume": info.get("avg_volume"),
                "average_volume_10d": None,
                
                # Kârlılık Oranları
                "profit_margin": None,
                "operating_margin": None,
                "gross_margin": None,
                "ebitda_margin": None,
                "roe": None,
                "roa": None,
                
                # Temettü Bilgileri
                "dividend_yield": self._to_percentage(info.get("dividend_yield")),
                "dividend_rate": None,
                "payout_ratio": None,
                "ex_dividend_date": None,
                
                # Bilanço Verileri
                "total_revenue": None,
                "revenue_per_share": None,
                "total_cash": None,
                "total_cash_per_share": None,
                "total_debt": None,
                "debt_to_equity": None,
                "current_ratio": None,
                "quick_ratio": None,
                "book_value": None,
                
                # Hisse Verileri
                "shares_outstanding": None,
                "float_shares": None,
                "shares_short": None,
                "short_ratio": None,
                
                # Büyüme Verileri
                "earnings_growth": None,
                "revenue_growth": None,
                "earnings_quarterly_growth": None,
                
                # EPS Verileri
                "trailing_eps": None,
                "forward_eps": None,
                
                # Beta
                "beta": self._safe_round(info.get("beta")),
                
                # Tarihler
                "updated_at": datetime.now().isoformat()
            }
            
            # Finansal tablolardan ek veri çek
            try:
                financials = self._fetcher.get_financials(symbol)
                if financials and not financials.get("error"):
                    # Gelir tablosundan kârlılık hesapla
                    income = financials.get("income_statement")
                    balance = financials.get("balance_sheet")
                    
                    if income:
                        self._extract_profitability(result, income)
                    
                    if balance:
                        self._extract_balance_sheet(result, balance)
            except Exception:
                pass
            
            # Temettü bilgisi
            try:
                dividends = self._fetcher.get_dividends(symbol)
                if dividends is not None and hasattr(dividends, '__len__') and len(dividends) > 0:
                    result["has_dividend_history"] = True
            except Exception:
                pass
            
            # Analist hedefleri
            try:
                targets = self._fetcher.get_analyst_targets(symbol)
                if targets:
                    result["analyst_targets"] = targets.get("price_targets")
                    result["recommendations"] = targets.get("recommendations")
            except Exception:
                pass
            
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
    
    def _extract_profitability(self, result: Dict, income: Dict) -> None:
        """Gelir tablosundan kârlılık metriklerini çıkar"""
        try:
            # En güncel dönemin verilerini al
            if isinstance(income, dict):
                # İlk sütun en güncel dönem
                cols = list(income.keys())
                if cols:
                    latest = income[cols[0]] if isinstance(income[cols[0]], dict) else {}
                    revenue = latest.get("Total Revenue") or latest.get("TotalRevenue")
                    net_income = latest.get("Net Income") or latest.get("NetIncome")
                    gross_profit = latest.get("Gross Profit") or latest.get("GrossProfit")
                    operating_income = latest.get("Operating Income") or latest.get("OperatingIncome")
                    
                    if revenue and net_income:
                        result["profit_margin"] = self._safe_round((net_income / revenue) * 100)
                        result["total_revenue"] = revenue
                    if revenue and operating_income:
                        result["operating_margin"] = self._safe_round((operating_income / revenue) * 100)
                    if revenue and gross_profit:
                        result["gross_margin"] = self._safe_round((gross_profit / revenue) * 100)
        except Exception:
            pass
    
    def _extract_balance_sheet(self, result: Dict, balance: Dict) -> None:
        """Bilançodan verileri çıkar"""
        try:
            if isinstance(balance, dict):
                cols = list(balance.keys())
                if cols:
                    latest = balance[cols[0]] if isinstance(balance[cols[0]], dict) else {}
                    
                    total_equity = latest.get("Stockholders Equity") or latest.get("Total Equity Gross Minority Interest")
                    total_debt_val = latest.get("Total Debt") or latest.get("TotalDebt")
                    total_assets = latest.get("Total Assets") or latest.get("TotalAssets")
                    current_assets = latest.get("Current Assets") or latest.get("CurrentAssets")
                    current_liabilities = latest.get("Current Liabilities") or latest.get("CurrentLiabilities")
                    cash = latest.get("Cash And Cash Equivalents") or latest.get("CashAndCashEquivalents")
                    
                    if total_debt_val and total_equity and total_equity != 0:
                        result["debt_to_equity"] = self._safe_round(total_debt_val / total_equity)
                    if total_debt_val:
                        result["total_debt"] = total_debt_val
                    if cash:
                        result["total_cash"] = cash
                    if current_assets and current_liabilities and current_liabilities != 0:
                        result["current_ratio"] = self._safe_round(current_assets / current_liabilities)
                    
                    # ROE hesapla
                    if total_equity and total_equity != 0 and result.get("total_revenue"):
                        # Net gelir zaten profit_margin'den hesaplanabilir
                        pass
        except Exception:
            pass
    
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
            val = float(value)
            # Zaten yüzde olarak geliyorsa (>1) doğrudan döndür
            if abs(val) > 1:
                return round(val, 2)
            return round(val * 100, 2)
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
        elif profit_margin is not None:
            if profit_margin > 15:
                summary["profitability"] = "İyi"
            elif profit_margin > 5:
                summary["profitability"] = "Orta"
            elif profit_margin > 0:
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
        """
        symbol = normalize_symbol(symbol)
        try:
            return self._fetcher.get_financials(symbol)
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
