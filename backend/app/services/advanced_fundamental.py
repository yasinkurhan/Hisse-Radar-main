"""
Gelişmiş Temel Analiz Servisi
==============================
Bilanço, gelir tablosu, nakit akışı analizi ve görselleştirme
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .cache_service import FundamentalCache


class AdvancedFundamentalService:
    """Gelişmiş temel analiz servisi"""
    
    def __init__(self):
        self.cache_duration = 86400  # 24 saat
    
    def get_full_fundamental_analysis(self, symbol: str) -> Dict:
        """Kapsamlı temel analiz"""
        
        # Symbol temizleme - .IS varsa tekrar ekleme
        clean_symbol = symbol.replace(".IS", "").replace(".is", "")
        
        # Cache kontrolü
        cached = FundamentalCache.get_fundamental(clean_symbol)
        if cached:
            return cached
        
        try:
            ticker = yf.Ticker(f"{clean_symbol}.IS")
            
            result = {
                "symbol": symbol,
                "success": True,
                "company_info": self._get_company_info(ticker),
                "financial_summary": self._get_financial_summary(ticker),
                "income_statement": self._get_income_statement(ticker),
                "balance_sheet": self._get_balance_sheet(ticker),
                "cash_flow": self._get_cash_flow(ticker),
                "ratios": self._calculate_ratios(ticker),
                "growth_metrics": self._calculate_growth(ticker),
                "peer_comparison": self._get_peer_comparison(ticker, symbol),
                "valuation": self._get_valuation_metrics(ticker),
                "charts_data": self._prepare_charts_data(ticker),
                "generated_at": datetime.now().isoformat()
            }
            
            # Cache'e kaydet
            FundamentalCache.set_fundamental(symbol, result)
            
            return result
            
        except Exception as e:
            return {
                "symbol": symbol,
                "success": False,
                "error": str(e)
            }
    
    def _get_company_info(self, ticker) -> Dict:
        """Şirket bilgileri"""
        try:
            info = ticker.info
            return {
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "employees": info.get("fullTimeEmployees", 0),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else "",
                "market_cap": info.get("marketCap", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "currency": info.get("currency", "TRY")
            }
        except:
            return {}
    
    def _get_financial_summary(self, ticker) -> Dict:
        """Finansal özet"""
        try:
            info = ticker.info
            return {
                "current_price": info.get("currentPrice", 0),
                "previous_close": info.get("previousClose", 0),
                "open": info.get("open", 0),
                "day_high": info.get("dayHigh", 0),
                "day_low": info.get("dayLow", 0),
                "week_52_high": info.get("fiftyTwoWeekHigh", 0),
                "week_52_low": info.get("fiftyTwoWeekLow", 0),
                "volume": info.get("volume", 0),
                "avg_volume": info.get("averageVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "beta": info.get("beta", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "peg_ratio": info.get("pegRatio", 0),
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "dividend_rate": info.get("dividendRate", 0)
            }
        except:
            return {}
    
    def _get_income_statement(self, ticker) -> Dict:
        """Gelir tablosu"""
        try:
            # Yıllık
            annual = ticker.financials
            # Çeyreklik
            quarterly = ticker.quarterly_financials
            
            def process_statement(df):
                if df is None or df.empty:
                    return []
                
                result = []
                for col in df.columns[:4]:  # Son 4 dönem
                    period_data = {
                        "period": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col),
                        "data": {}
                    }
                    for idx in df.index:
                        val = df.loc[idx, col]
                        period_data["data"][str(idx)] = float(val) if pd.notna(val) else None
                    result.append(period_data)
                return result
            
            # Önemli kalemler
            key_items = {
                "Total Revenue": "total_revenue",
                "Gross Profit": "gross_profit",
                "Operating Income": "operating_income",
                "Net Income": "net_income",
                "EBITDA": "ebitda",
                "Basic EPS": "eps"
            }
            
            summary = []
            if annual is not None and not annual.empty:
                for col in annual.columns[:4]:
                    item = {"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col)}
                    for orig_name, new_name in key_items.items():
                        if orig_name in annual.index:
                            val = annual.loc[orig_name, col]
                            item[new_name] = float(val) if pd.notna(val) else None
                        else:
                            item[new_name] = None
                    summary.append(item)
            
            return {
                "annual": process_statement(annual),
                "quarterly": process_statement(quarterly),
                "summary": summary
            }
        except:
            return {"annual": [], "quarterly": [], "summary": []}
    
    def _get_balance_sheet(self, ticker) -> Dict:
        """Bilanço"""
        try:
            annual = ticker.balance_sheet
            quarterly = ticker.quarterly_balance_sheet
            
            key_items = {
                "Total Assets": "total_assets",
                "Total Liabilities Net Minority Interest": "total_liabilities",
                "Total Equity Gross Minority Interest": "total_equity",
                "Cash And Cash Equivalents": "cash",
                "Total Debt": "total_debt",
                "Net Debt": "net_debt",
                "Inventory": "inventory",
                "Accounts Receivable": "accounts_receivable"
            }
            
            summary = []
            if annual is not None and not annual.empty:
                for col in annual.columns[:4]:
                    item = {"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col)}
                    for orig_name, new_name in key_items.items():
                        if orig_name in annual.index:
                            val = annual.loc[orig_name, col]
                            item[new_name] = float(val) if pd.notna(val) else None
                        else:
                            item[new_name] = None
                    summary.append(item)
            
            return {"summary": summary}
        except:
            return {"summary": []}
    
    def _get_cash_flow(self, ticker) -> Dict:
        """Nakit akış tablosu"""
        try:
            annual = ticker.cashflow
            
            key_items = {
                "Operating Cash Flow": "operating_cf",
                "Investing Cash Flow": "investing_cf",
                "Financing Cash Flow": "financing_cf",
                "Free Cash Flow": "free_cf",
                "Capital Expenditure": "capex"
            }
            
            summary = []
            if annual is not None and not annual.empty:
                for col in annual.columns[:4]:
                    item = {"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col)}
                    for orig_name, new_name in key_items.items():
                        if orig_name in annual.index:
                            val = annual.loc[orig_name, col]
                            item[new_name] = float(val) if pd.notna(val) else None
                        else:
                            item[new_name] = None
                    summary.append(item)
            
            return {"summary": summary}
        except:
            return {"summary": []}
    
    def _calculate_ratios(self, ticker) -> Dict:
        """Finansal oranlar"""
        try:
            info = ticker.info
            bs = ticker.balance_sheet
            inc = ticker.financials
            
            ratios = {
                "profitability": {},
                "liquidity": {},
                "leverage": {},
                "efficiency": {},
                "valuation": {}
            }
            
            # Karlılık oranları
            if inc is not None and not inc.empty:
                col = inc.columns[0]
                revenue = inc.loc["Total Revenue", col] if "Total Revenue" in inc.index else None
                gross_profit = inc.loc["Gross Profit", col] if "Gross Profit" in inc.index else None
                net_income = inc.loc["Net Income", col] if "Net Income" in inc.index else None
                
                if revenue and gross_profit:
                    ratios["profitability"]["gross_margin"] = round(float(gross_profit / revenue * 100), 2)
                if revenue and net_income:
                    ratios["profitability"]["net_margin"] = round(float(net_income / revenue * 100), 2)
            
            # Likidite oranları
            if bs is not None and not bs.empty:
                col = bs.columns[0]
                
                current_assets = bs.loc["Current Assets", col] if "Current Assets" in bs.index else None
                current_liabilities = bs.loc["Current Liabilities", col] if "Current Liabilities" in bs.index else None
                inventory = bs.loc["Inventory", col] if "Inventory" in bs.index else 0
                
                if current_assets and current_liabilities:
                    ratios["liquidity"]["current_ratio"] = round(float(current_assets / current_liabilities), 2)
                    ratios["liquidity"]["quick_ratio"] = round(float((current_assets - (inventory or 0)) / current_liabilities), 2)
            
            # Kaldıraç oranları
            ratios["leverage"]["debt_to_equity"] = info.get("debtToEquity", None)
            
            # Değerleme oranları
            ratios["valuation"]["pe_ratio"] = info.get("trailingPE", None)
            ratios["valuation"]["pb_ratio"] = info.get("priceToBook", None)
            ratios["valuation"]["ps_ratio"] = info.get("priceToSalesTrailing12Months", None)
            ratios["valuation"]["ev_ebitda"] = info.get("enterpriseToEbitda", None)
            
            # ROE, ROA
            ratios["profitability"]["roe"] = info.get("returnOnEquity", None)
            if ratios["profitability"]["roe"]:
                ratios["profitability"]["roe"] = round(ratios["profitability"]["roe"] * 100, 2)
            
            ratios["profitability"]["roa"] = info.get("returnOnAssets", None)
            if ratios["profitability"]["roa"]:
                ratios["profitability"]["roa"] = round(ratios["profitability"]["roa"] * 100, 2)
            
            return ratios
        except:
            return {}
    
    def _calculate_growth(self, ticker) -> Dict:
        """Büyüme metrikleri"""
        try:
            inc = ticker.financials
            
            growth = {
                "revenue_growth": [],
                "profit_growth": [],
                "yoy_revenue_growth": None,
                "yoy_profit_growth": None,
                "cagr_3y_revenue": None
            }
            
            if inc is not None and len(inc.columns) >= 2:
                revenues = []
                profits = []
                
                for col in inc.columns[:4]:
                    if "Total Revenue" in inc.index:
                        rev = inc.loc["Total Revenue", col]
                        if pd.notna(rev):
                            revenues.append({"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col), "value": float(rev)})
                    
                    if "Net Income" in inc.index:
                        profit = inc.loc["Net Income", col]
                        if pd.notna(profit):
                            profits.append({"period": col.strftime("%Y") if hasattr(col, 'strftime') else str(col), "value": float(profit)})
                
                growth["revenue_growth"] = revenues
                growth["profit_growth"] = profits
                
                # YoY büyüme
                if len(revenues) >= 2 and revenues[1]["value"] != 0:
                    growth["yoy_revenue_growth"] = round((revenues[0]["value"] - revenues[1]["value"]) / abs(revenues[1]["value"]) * 100, 2)
                
                if len(profits) >= 2 and profits[1]["value"] != 0:
                    growth["yoy_profit_growth"] = round((profits[0]["value"] - profits[1]["value"]) / abs(profits[1]["value"]) * 100, 2)
                
                # 3 yıllık CAGR
                if len(revenues) >= 4 and revenues[3]["value"] > 0:
                    growth["cagr_3y_revenue"] = round(((revenues[0]["value"] / revenues[3]["value"]) ** (1/3) - 1) * 100, 2)
            
            return growth
        except:
            return {}
    
    def _get_peer_comparison(self, ticker, symbol: str) -> Dict:
        """Sektör karşılaştırması"""
        try:
            info = ticker.info
            
            return {
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "sector_pe": info.get("sectorPE", None),
                "industry_pe": info.get("industryPE", None),
                "pe_vs_sector": None,  # Hesaplanabilir
                "market_cap_rank": None  # API'den alınabilir
            }
        except:
            return {}
    
    def _get_valuation_metrics(self, ticker) -> Dict:
        """Değerleme metrikleri"""
        try:
            info = ticker.info
            
            current_price = info.get("currentPrice", 0)
            target_mean = info.get("targetMeanPrice", 0)
            
            upside = None
            if current_price and target_mean:
                upside = round((target_mean - current_price) / current_price * 100, 2)
            
            return {
                "current_price": current_price,
                "target_low": info.get("targetLowPrice", None),
                "target_mean": target_mean,
                "target_high": info.get("targetHighPrice", None),
                "upside_potential": upside,
                "analyst_rating": info.get("recommendationKey", None),
                "number_of_analysts": info.get("numberOfAnalystOpinions", 0)
            }
        except:
            return {}
    
    def _prepare_charts_data(self, ticker) -> Dict:
        """Grafik verileri hazırla"""
        try:
            inc = ticker.financials
            bs = ticker.balance_sheet
            cf = ticker.cashflow
            
            charts = {
                "revenue_trend": [],
                "profit_trend": [],
                "margin_trend": [],
                "assets_liabilities": [],
                "cash_flow_trend": []
            }
            
            # Gelir ve Kar trendi
            if inc is not None and not inc.empty:
                for col in reversed(list(inc.columns[:4])):
                    period = col.strftime("%Y") if hasattr(col, 'strftime') else str(col)
                    
                    revenue = inc.loc["Total Revenue", col] if "Total Revenue" in inc.index else None
                    gross_profit = inc.loc["Gross Profit", col] if "Gross Profit" in inc.index else None
                    net_income = inc.loc["Net Income", col] if "Net Income" in inc.index else None
                    
                    if revenue and pd.notna(revenue):
                        charts["revenue_trend"].append({
                            "period": period,
                            "value": float(revenue) / 1_000_000  # Milyon TL
                        })
                    
                    if net_income and pd.notna(net_income):
                        charts["profit_trend"].append({
                            "period": period,
                            "value": float(net_income) / 1_000_000
                        })
                    
                    if revenue and gross_profit and pd.notna(revenue) and pd.notna(gross_profit):
                        gross_margin = float(gross_profit / revenue * 100)
                        net_margin = float(net_income / revenue * 100) if net_income and pd.notna(net_income) else 0
                        charts["margin_trend"].append({
                            "period": period,
                            "gross_margin": round(gross_margin, 2),
                            "net_margin": round(net_margin, 2)
                        })
            
            # Varlık/Borç grafiği
            if bs is not None and not bs.empty:
                for col in reversed(list(bs.columns[:4])):
                    period = col.strftime("%Y") if hasattr(col, 'strftime') else str(col)
                    
                    assets = bs.loc["Total Assets", col] if "Total Assets" in bs.index else None
                    liabilities = bs.loc["Total Liabilities Net Minority Interest", col] if "Total Liabilities Net Minority Interest" in bs.index else None
                    equity = bs.loc["Total Equity Gross Minority Interest", col] if "Total Equity Gross Minority Interest" in bs.index else None
                    
                    if assets and pd.notna(assets):
                        charts["assets_liabilities"].append({
                            "period": period,
                            "assets": float(assets) / 1_000_000,
                            "liabilities": float(liabilities) / 1_000_000 if liabilities and pd.notna(liabilities) else 0,
                            "equity": float(equity) / 1_000_000 if equity and pd.notna(equity) else 0
                        })
            
            # Nakit akış grafiği
            if cf is not None and not cf.empty:
                for col in reversed(list(cf.columns[:4])):
                    period = col.strftime("%Y") if hasattr(col, 'strftime') else str(col)
                    
                    operating = cf.loc["Operating Cash Flow", col] if "Operating Cash Flow" in cf.index else None
                    investing = cf.loc["Investing Cash Flow", col] if "Investing Cash Flow" in cf.index else None
                    financing = cf.loc["Financing Cash Flow", col] if "Financing Cash Flow" in cf.index else None
                    
                    if operating and pd.notna(operating):
                        charts["cash_flow_trend"].append({
                            "period": period,
                            "operating": float(operating) / 1_000_000,
                            "investing": float(investing) / 1_000_000 if investing and pd.notna(investing) else 0,
                            "financing": float(financing) / 1_000_000 if financing and pd.notna(financing) else 0
                        })
            
            return charts
        except:
            return {}
    
    def get_quick_stats(self, symbol: str) -> Dict:
        """Hızlı temel analiz istatistikleri"""
        try:
            # Symbol temizleme
            clean_symbol = symbol.replace(".IS", "").replace(".is", "")
            ticker = yf.Ticker(f"{clean_symbol}.IS")
            info = ticker.info
            
            return {
                "symbol": clean_symbol,
                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else 0,
                "roe": round(info.get("returnOnEquity", 0) * 100, 2) if info.get("returnOnEquity") else None,
                "debt_to_equity": info.get("debtToEquity"),
                "market_cap": info.get("marketCap"),
                "beta": info.get("beta"),
                "target_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey")
            }
        except:
            return {"symbol": symbol, "error": "Veri alınamadı"}


# Singleton instance
fundamental_service = AdvancedFundamentalService()
