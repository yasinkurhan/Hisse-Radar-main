"""
Gelişmiş Temel Analiz Servisi
==============================
Borsapy kaynaklı finansal veriler ile temel analiz üretir
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

from .cache_service import FundamentalCache
from .borsapy_fetcher import get_borsapy_fetcher


class AdvancedFundamentalService:
    """Gelişmiş temel analiz servisi (borsapy)"""

    def __init__(self):
        self.cache_duration = 86400  # 24 saat

    @staticmethod
    def _clean_symbol(symbol: str) -> str:
        return symbol.upper().strip().replace(".IS", "")

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _safe_period(value: Any) -> str:
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def _table_to_df(self, table: Any) -> pd.DataFrame:
        if not table or not isinstance(table, dict):
            return pd.DataFrame()
        try:
            df = pd.DataFrame(table)
            return df if not df.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def _pick_row(self, df: pd.DataFrame, names: List[str]) -> Optional[pd.Series]:
        if df.empty:
            return None
        lower_map = {str(idx).lower(): idx for idx in df.index}
        for name in names:
            key = lower_map.get(name.lower())
            if key is not None:
                return df.loc[key]
        return None

    def _build_price_summary(self, symbol: str) -> Dict[str, Any]:
        fetcher = get_borsapy_fetcher()
        hist = fetcher.get_history(symbol, period="6mo", interval="1d")
        if hist is None or hist.empty:
            return {
                "current_price": 0,
                "previous_close": 0,
                "open": 0,
                "day_high": 0,
                "day_low": 0,
                "week_52_high": 0,
                "week_52_low": 0,
                "volume": 0,
                "avg_volume": 0,
                "market_cap": None,
                "beta": None,
                "pe_ratio": None,
                "forward_pe": None,
                "peg_ratio": None,
                "dividend_yield": None,
                "dividend_rate": None,
            }

        close_col = "close" if "close" in hist.columns else "Close"
        open_col = "open" if "open" in hist.columns else "Open"
        high_col = "high" if "high" in hist.columns else "High"
        low_col = "low" if "low" in hist.columns else "Low"
        volume_col = "volume" if "volume" in hist.columns else "Volume"

        current_price = self._to_float(hist[close_col].iloc[-1]) or 0
        previous_close = self._to_float(hist[close_col].iloc[-2]) if len(hist) > 1 else current_price

        return {
            "current_price": current_price,
            "previous_close": previous_close or 0,
            "open": self._to_float(hist[open_col].iloc[-1]) or 0,
            "day_high": self._to_float(hist[high_col].iloc[-1]) or 0,
            "day_low": self._to_float(hist[low_col].iloc[-1]) or 0,
            "week_52_high": self._to_float(hist[high_col].max()) or 0,
            "week_52_low": self._to_float(hist[low_col].min()) or 0,
            "volume": self._to_float(hist[volume_col].iloc[-1]) or 0,
            "avg_volume": self._to_float(hist[volume_col].tail(20).mean()) or 0,
            "market_cap": None,
            "beta": None,
            "pe_ratio": None,
            "forward_pe": None,
            "peg_ratio": None,
            "dividend_yield": None,
            "dividend_rate": None,
        }

    def _statement_summary(self, df: pd.DataFrame, key_items: Dict[str, List[str]], period_format: str = "%Y") -> List[Dict[str, Any]]:
        if df.empty:
            return []

        cols = list(df.columns)[:4]
        result = []
        for col in cols:
            period = col.strftime(period_format) if hasattr(col, "strftime") else str(col)
            row = {"period": period}
            for out_key, aliases in key_items.items():
                series = self._pick_row(df, aliases)
                value = self._to_float(series.get(col)) if series is not None and col in series.index else None
                row[out_key] = value
            result.append(row)
        return result

    def _full_statement(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty:
            return []

        cols = list(df.columns)[:4]
        data = []
        for col in cols:
            period = self._safe_period(col)
            values = {}
            for idx in df.index:
                values[str(idx)] = self._to_float(df.loc[idx, col])
            data.append({"period": period, "data": values})
        return data

    def get_full_fundamental_analysis(self, symbol: str) -> Dict[str, Any]:
        """Kapsamlı temel analiz"""
        clean_symbol = self._clean_symbol(symbol)

        cached = FundamentalCache.get_fundamental(clean_symbol)
        if cached:
            return cached

        try:
            fetcher = get_borsapy_fetcher()
            fin = fetcher.get_financials(clean_symbol)
            if fin.get("error"):
                return {"symbol": clean_symbol, "success": False, "error": fin.get("error")}

            income_df = self._table_to_df(fin.get("income_statement"))
            q_income_df = self._table_to_df(fin.get("quarterly_income_statement"))
            balance_df = self._table_to_df(fin.get("balance_sheet"))
            q_balance_df = self._table_to_df(fin.get("quarterly_balance_sheet"))
            cash_df = self._table_to_df(fin.get("cashflow"))

            income_keys = {
                "total_revenue": ["Total Revenue", "Revenue"],
                "gross_profit": ["Gross Profit"],
                "operating_income": ["Operating Income", "Operating Profit"],
                "net_income": ["Net Income", "Net Profit"],
                "ebitda": ["EBITDA"],
                "eps": ["Basic EPS", "EPS"],
            }

            balance_keys = {
                "total_assets": ["Total Assets"],
                "total_liabilities": ["Total Liabilities Net Minority Interest", "Total Liabilities"],
                "total_equity": ["Total Equity Gross Minority Interest", "Total Equity"],
                "cash": ["Cash And Cash Equivalents", "Cash"],
                "total_debt": ["Total Debt"],
                "net_debt": ["Net Debt"],
                "inventory": ["Inventory"],
                "accounts_receivable": ["Accounts Receivable"],
            }

            cash_keys = {
                "operating_cf": ["Operating Cash Flow"],
                "investing_cf": ["Investing Cash Flow"],
                "financing_cf": ["Financing Cash Flow"],
                "free_cf": ["Free Cash Flow"],
                "capex": ["Capital Expenditure"],
            }

            income_summary = self._statement_summary(income_df, income_keys)
            balance_summary = self._statement_summary(balance_df, balance_keys)
            cash_summary = self._statement_summary(cash_df, cash_keys)

            ratios = {
                "profitability": {},
                "liquidity": {},
                "leverage": {},
                "efficiency": {},
                "valuation": {},
            }

            if income_summary:
                latest_income = income_summary[0]
                revenue = latest_income.get("total_revenue")
                gross_profit = latest_income.get("gross_profit")
                net_income = latest_income.get("net_income")
                if revenue and gross_profit:
                    ratios["profitability"]["gross_margin"] = round((gross_profit / revenue) * 100, 2)
                if revenue and net_income:
                    ratios["profitability"]["net_margin"] = round((net_income / revenue) * 100, 2)

            if balance_summary:
                latest_balance = balance_summary[0]
                debt = latest_balance.get("total_debt")
                equity = latest_balance.get("total_equity")
                if debt and equity:
                    ratios["leverage"]["debt_to_equity"] = round((debt / equity) * 100, 2)

            revenue_growth = []
            profit_growth = []
            for item in income_summary:
                period = item.get("period")
                revenue = item.get("total_revenue")
                profit = item.get("net_income")
                if revenue is not None:
                    revenue_growth.append({"period": period, "value": revenue})
                if profit is not None:
                    profit_growth.append({"period": period, "value": profit})

            growth_metrics = {
                "revenue_growth": revenue_growth,
                "profit_growth": profit_growth,
                "yoy_revenue_growth": None,
                "yoy_profit_growth": None,
                "cagr_3y_revenue": None,
            }

            if len(revenue_growth) >= 2 and revenue_growth[1]["value"]:
                growth_metrics["yoy_revenue_growth"] = round(
                    ((revenue_growth[0]["value"] - revenue_growth[1]["value"]) / abs(revenue_growth[1]["value"])) * 100, 2
                )

            if len(profit_growth) >= 2 and profit_growth[1]["value"]:
                growth_metrics["yoy_profit_growth"] = round(
                    ((profit_growth[0]["value"] - profit_growth[1]["value"]) / abs(profit_growth[1]["value"])) * 100, 2
                )

            charts_data = {
                "revenue_trend": [
                    {"period": x["period"], "value": x["value"] / 1_000_000 if x["value"] else 0}
                    for x in reversed(revenue_growth[:4])
                ],
                "profit_trend": [
                    {"period": x["period"], "value": x["value"] / 1_000_000 if x["value"] else 0}
                    for x in reversed(profit_growth[:4])
                ],
                "margin_trend": [
                    {
                        "period": x.get("period"),
                        "gross_margin": round(((x.get("gross_profit") or 0) / (x.get("total_revenue") or 1)) * 100, 2)
                        if x.get("total_revenue")
                        else 0,
                        "net_margin": round(((x.get("net_income") or 0) / (x.get("total_revenue") or 1)) * 100, 2)
                        if x.get("total_revenue")
                        else 0,
                    }
                    for x in reversed(income_summary[:4])
                ],
                "assets_liabilities": [
                    {
                        "period": x.get("period"),
                        "assets": (x.get("total_assets") or 0) / 1_000_000,
                        "liabilities": (x.get("total_liabilities") or 0) / 1_000_000,
                        "equity": (x.get("total_equity") or 0) / 1_000_000,
                    }
                    for x in reversed(balance_summary[:4])
                ],
                "cash_flow_trend": [
                    {
                        "period": x.get("period"),
                        "operating": (x.get("operating_cf") or 0) / 1_000_000,
                        "investing": (x.get("investing_cf") or 0) / 1_000_000,
                        "financing": (x.get("financing_cf") or 0) / 1_000_000,
                    }
                    for x in reversed(cash_summary[:4])
                ],
            }

            result = {
                "symbol": clean_symbol,
                "success": True,
                "company_info": {
                    "name": clean_symbol,
                    "sector": "N/A",
                    "industry": "N/A",
                    "employees": 0,
                    "website": "",
                    "description": "",
                    "market_cap": None,
                    "enterprise_value": None,
                    "currency": "TRY",
                },
                "financial_summary": self._build_price_summary(clean_symbol),
                "income_statement": {
                    "annual": self._full_statement(income_df),
                    "quarterly": self._full_statement(q_income_df),
                    "summary": income_summary,
                },
                "balance_sheet": {
                    "summary": balance_summary,
                    "quarterly": self._full_statement(q_balance_df),
                },
                "cash_flow": {
                    "summary": cash_summary,
                    "annual": self._full_statement(cash_df),
                },
                "ratios": ratios,
                "growth_metrics": growth_metrics,
                "peer_comparison": {
                    "sector": "N/A",
                    "industry": "N/A",
                    "sector_pe": None,
                    "industry_pe": None,
                    "pe_vs_sector": None,
                    "market_cap_rank": None,
                },
                "valuation": {
                    "current_price": self._build_price_summary(clean_symbol).get("current_price", 0),
                    "target_low": None,
                    "target_mean": None,
                    "target_high": None,
                    "upside_potential": None,
                    "analyst_rating": None,
                    "number_of_analysts": 0,
                },
                "charts_data": charts_data,
                "generated_at": datetime.now().isoformat(),
                "data_source": "borsapy",
            }

            FundamentalCache.set_fundamental(clean_symbol, result)
            return result
        except Exception as e:
            return {"symbol": clean_symbol, "success": False, "error": str(e)}

    def get_quick_stats(self, symbol: str) -> Dict[str, Any]:
        """Hızlı temel analiz istatistikleri"""
        try:
            full = self.get_full_fundamental_analysis(symbol)
            if not full.get("success"):
                return {"symbol": self._clean_symbol(symbol), "error": full.get("error", "Veri alınamadı")}

            latest_income = (full.get("income_statement", {}).get("summary") or [{}])[0]
            latest_balance = (full.get("balance_sheet", {}).get("summary") or [{}])[0]
            ratios = full.get("ratios", {})

            return {
                "symbol": self._clean_symbol(symbol),
                "pe_ratio": ratios.get("valuation", {}).get("pe_ratio"),
                "pb_ratio": ratios.get("valuation", {}).get("pb_ratio"),
                "dividend_yield": full.get("financial_summary", {}).get("dividend_yield"),
                "roe": ratios.get("profitability", {}).get("roe"),
                "debt_to_equity": ratios.get("leverage", {}).get("debt_to_equity"),
                "market_cap": full.get("financial_summary", {}).get("market_cap"),
                "beta": full.get("financial_summary", {}).get("beta"),
                "target_price": full.get("valuation", {}).get("target_mean"),
                "recommendation": full.get("valuation", {}).get("analyst_rating"),
                "revenue": latest_income.get("total_revenue"),
                "net_income": latest_income.get("net_income"),
                "equity": latest_balance.get("total_equity"),
                "data_source": "borsapy",
            }
        except Exception:
            return {"symbol": self._clean_symbol(symbol), "error": "Veri alınamadı"}


# Singleton instance
fundamental_service = AdvancedFundamentalService()
