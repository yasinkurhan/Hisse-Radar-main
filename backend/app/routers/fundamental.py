"""
HisseRadar Temel Analiz Router
===============================
F/K, PD/DD, bilanÃ§o ve finansal veriler API'leri
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..services.fundamental_analysis import get_fundamental_analyzer


router = APIRouter(prefix="/api/fundamental", tags=["Temel Analiz"])


@router.get("/{symbol}")
def get_fundamental_data(symbol: str):
    """
    Hisse iÃ§in kapsamlÄ± temel analiz verilerini getir.
    
    - **symbol**: Hisse sembolÃ¼ (Ã¶rn: THYAO)
    
    DÃ¶nen veriler:
    - Åirket bilgileri
    - DeÄŸerleme oranlarÄ± (F/K, PD/DD, F/S)
    - KÃ¢rlÄ±lÄ±k oranlarÄ± (ROE, ROA, kÃ¢r marjÄ±)
    - TemettÃ¼ bilgileri
    - BilanÃ§o verileri
    - Analiz Ã¶zeti ve deÄŸerlendirme
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    # Veri kontrolÃ¼ - hata varsa ve anlamlÄ± veri yoksa minimal veri dÃ¶ndÃ¼r
    has_valid_data = (
        data.get("company_name") or 
        data.get("current_price") or 
        data.get("market_cap") or
        data.get("pe_ratio")
    )
    
    if "error" in data and not has_valid_data:
        # Hata durumunda minimal veri dÃ¶ndÃ¼r (404 yerine)
        return {
            "symbol": symbol.upper(),
            "company_name": f"{symbol.upper()}",
            "sector": "Bilinmiyor",
            "industry": None,
            "error_message": f"{symbol} iÃ§in temel analiz verisi bulunamadÄ±",
            "analysis_summary": {
                "valuation": "Belirsiz",
                "profitability": "Belirsiz", 
                "growth": "Belirsiz",
                "dividend": "Belirsiz",
                "overall": "Veri Yok",
                "notes": ["Yahoo Finance'dan veri alÄ±namadÄ±. LÃ¼tfen daha sonra tekrar deneyin."]
            }
        }
    
    return data


@router.get("/{symbol}/valuation")
def get_valuation_ratios(symbol: str):
    """
    DeÄŸerleme oranlarÄ±nÄ± getir.
    
    - F/K (P/E): Fiyat / KazanÃ§ - Hissenin kaÃ§ yÄ±llÄ±k kÃ¢rÄ±na denk olduÄŸunu gÃ¶sterir
    - PD/DD (P/B): Piyasa DeÄŸeri / Defter DeÄŸeri - 1'in altÄ± ucuz kabul edilir
    - F/S (P/S): Fiyat / SatÄ±ÅŸ - Gelire gÃ¶re deÄŸerleme
    - PEG: F/K / BÃ¼yÃ¼me - 1'in altÄ± cazip
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "current_price": data.get("current_price"),
        "valuation": {
            "pe_ratio": {
                "value": data.get("pe_ratio"),
                "label": "F/K (Fiyat/KazanÃ§)",
                "description": "Hissenin kaÃ§ yÄ±llÄ±k kÃ¢rÄ±na eÅŸdeÄŸer olduÄŸunu gÃ¶sterir",
                "interpretation": get_pe_interpretation(data.get("pe_ratio"))
            },
            "forward_pe": {
                "value": data.get("forward_pe"),
                "label": "Ä°leriye DÃ¶nÃ¼k F/K",
                "description": "Gelecek kazanÃ§ tahminlerine gÃ¶re F/K"
            },
            "pb_ratio": {
                "value": data.get("pb_ratio"),
                "label": "PD/DD (Piyasa D./Defter D.)",
                "description": "1'in altÄ±nda ise defter deÄŸerinin altÄ±nda iÅŸlem gÃ¶rÃ¼yor",
                "interpretation": get_pb_interpretation(data.get("pb_ratio"))
            },
            "ps_ratio": {
                "value": data.get("ps_ratio"),
                "label": "F/S (Fiyat/SatÄ±ÅŸ)",
                "description": "Her 1 TL satÄ±ÅŸ iÃ§in Ã¶denen fiyat"
            },
            "peg_ratio": {
                "value": data.get("peg_ratio"),
                "label": "PEG OranÄ±",
                "description": "F/K'nÄ±n bÃ¼yÃ¼meye oranÄ±, 1'in altÄ± cazip",
                "interpretation": get_peg_interpretation(data.get("peg_ratio"))
            },
            "enterprise_to_ebitda": {
                "value": data.get("enterprise_to_ebitda"),
                "label": "EV/EBITDA",
                "description": "Åirket deÄŸeri / FAVÃ–K"
            }
        },
        "market_data": {
            "market_cap": data.get("market_cap"),
            "enterprise_value": data.get("enterprise_value"),
            "week_52_high": data.get("week_52_high"),
            "week_52_low": data.get("week_52_low")
        }
    }


@router.get("/{symbol}/profitability")
def get_profitability_ratios(symbol: str):
    """
    KÃ¢rlÄ±lÄ±k oranlarÄ±nÄ± getir.
    
    - ROE: Ã–zkaynak KÃ¢rlÄ±lÄ±ÄŸÄ± - %15 Ã¼zeri iyi
    - ROA: Aktif KÃ¢rlÄ±lÄ±k - VarlÄ±k kullanÄ±m etkinliÄŸi
    - KÃ¢r MarjÄ±: Net kÃ¢r / Gelir
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "profitability": {
            "roe": {
                "value": data.get("roe"),
                "label": "ROE (Ã–zkaynak KÃ¢rlÄ±lÄ±ÄŸÄ±)",
                "description": "Her 100 TL Ã¶zkaynak iÃ§in kazanÄ±lan kÃ¢r",
                "benchmark": "%15 Ã¼zeri iyi kabul edilir",
                "interpretation": get_roe_interpretation(data.get("roe"))
            },
            "roa": {
                "value": data.get("roa"),
                "label": "ROA (Aktif KÃ¢rlÄ±lÄ±k)",
                "description": "Her 100 TL varlÄ±k iÃ§in kazanÄ±lan kÃ¢r",
                "benchmark": "%5 Ã¼zeri iyi kabul edilir"
            },
            "profit_margin": {
                "value": data.get("profit_margin"),
                "label": "Net KÃ¢r MarjÄ±",
                "description": "Her 100 TL gelirden kalan net kÃ¢r"
            },
            "operating_margin": {
                "value": data.get("operating_margin"),
                "label": "Faaliyet KÃ¢r MarjÄ±",
                "description": "Faaliyet kÃ¢rÄ± / Gelir"
            },
            "gross_margin": {
                "value": data.get("gross_margin"),
                "label": "BrÃ¼t KÃ¢r MarjÄ±",
                "description": "BrÃ¼t kÃ¢r / Gelir"
            }
        }
    }


@router.get("/{symbol}/dividend")
def get_dividend_info(symbol: str):
    """
    TemettÃ¼ bilgilerini getir.
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "dividend": {
            "dividend_yield": {
                "value": data.get("dividend_yield"),
                "label": "TemettÃ¼ Verimi",
                "description": "YÄ±llÄ±k temettÃ¼ / Hisse fiyatÄ±",
                "interpretation": get_dividend_interpretation(data.get("dividend_yield"))
            },
            "dividend_rate": {
                "value": data.get("dividend_rate"),
                "label": "YÄ±llÄ±k TemettÃ¼",
                "description": "Hisse baÅŸÄ± yÄ±llÄ±k temettÃ¼ tutarÄ± (TL)"
            },
            "payout_ratio": {
                "value": data.get("payout_ratio"),
                "label": "TemettÃ¼ DaÄŸÄ±tÄ±m OranÄ±",
                "description": "Net kÃ¢rÄ±n ne kadarÄ± temettÃ¼ olarak daÄŸÄ±tÄ±lÄ±yor"
            },
            "ex_dividend_date": {
                "value": data.get("ex_dividend_date"),
                "label": "TemettÃ¼ Hak EdiÅŸ Tarihi",
                "description": "Bu tarihten Ã¶nce almÄ±ÅŸ olmalÄ±sÄ±nÄ±z"
            }
        }
    }


@router.get("/{symbol}/balance")
def get_balance_sheet_summary(symbol: str):
    """
    BilanÃ§o Ã¶zetini getir.
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "balance_sheet": {
            "total_cash": {
                "value": data.get("total_cash"),
                "label": "Toplam Nakit",
                "formatted": format_large_number(data.get("total_cash"))
            },
            "total_debt": {
                "value": data.get("total_debt"),
                "label": "Toplam BorÃ§",
                "formatted": format_large_number(data.get("total_debt"))
            },
            "total_revenue": {
                "value": data.get("total_revenue"),
                "label": "Toplam Gelir",
                "formatted": format_large_number(data.get("total_revenue"))
            },
            "debt_to_equity": {
                "value": data.get("debt_to_equity"),
                "label": "BorÃ§/Ã–zkaynak",
                "description": "1'in altÄ± tercih edilir"
            },
            "current_ratio": {
                "value": data.get("current_ratio"),
                "label": "Cari Oran",
                "description": "KÄ±sa vadeli borÃ§larÄ± Ã¶deme kapasitesi, 1.5+ iyi"
            },
            "quick_ratio": {
                "value": data.get("quick_ratio"),
                "label": "Asit-Test OranÄ±",
                "description": "Stoklar hariÃ§ likidite oranÄ±"
            },
            "book_value": {
                "value": data.get("book_value"),
                "label": "Hisse BaÅŸÄ± Defter DeÄŸeri",
                "description": "Åirket tasfiye edilse hisse baÅŸÄ± deÄŸer"
            }
        },
        "shares": {
            "shares_outstanding": {
                "value": data.get("shares_outstanding"),
                "label": "Toplam Hisse SayÄ±sÄ±",
                "formatted": format_large_number(data.get("shares_outstanding"))
            },
            "float_shares": {
                "value": data.get("float_shares"),
                "label": "Halka AÃ§Ä±k Hisse",
                "formatted": format_large_number(data.get("float_shares"))
            }
        }
    }


@router.get("/{symbol}/growth")
def get_growth_metrics(symbol: str):
    """
    BÃ¼yÃ¼me metriklerini getir.
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "growth": {
            "revenue_growth": {
                "value": data.get("revenue_growth"),
                "label": "Gelir BÃ¼yÃ¼mesi (YoY)",
                "description": "YÄ±llÄ±k gelir artÄ±ÅŸÄ±"
            },
            "earnings_growth": {
                "value": data.get("earnings_growth"),
                "label": "KÃ¢r BÃ¼yÃ¼mesi (YoY)",
                "description": "YÄ±llÄ±k kÃ¢r artÄ±ÅŸÄ±"
            },
            "earnings_quarterly_growth": {
                "value": data.get("earnings_quarterly_growth"),
                "label": "Ã‡eyreklik KÃ¢r BÃ¼yÃ¼mesi",
                "description": "Son Ã§eyrek kÃ¢r artÄ±ÅŸÄ±"
            }
        },
        "eps": {
            "trailing_eps": {
                "value": data.get("trailing_eps"),
                "label": "Hisse BaÅŸÄ± KazanÃ§ (TTM)",
                "description": "Son 12 ayÄ±n hisse baÅŸÄ± kazancÄ±"
            },
            "forward_eps": {
                "value": data.get("forward_eps"),
                "label": "Tahmini HBK",
                "description": "Gelecek 12 ay iÃ§in beklenen HBK"
            }
        }
    }


@router.get("/{symbol}/summary")
def get_fundamental_summary(symbol: str):
    """
    Temel analiz Ã¶zet raporu.
    
    TÃ¼m Ã¶nemli metriklerin Ã¶zeti ve genel deÄŸerlendirme.
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "sector": data.get("sector"),
        "industry": data.get("industry"),
        "current_price": data.get("current_price"),
        "key_metrics": {
            "pe_ratio": data.get("pe_ratio"),
            "pb_ratio": data.get("pb_ratio"),
            "roe": data.get("roe"),
            "profit_margin": data.get("profit_margin"),
            "dividend_yield": data.get("dividend_yield"),
            "debt_to_equity": data.get("debt_to_equity"),
            "revenue_growth": data.get("revenue_growth")
        },
        "market_data": {
            "market_cap": data.get("market_cap"),
            "market_cap_formatted": format_large_number(data.get("market_cap")),
            "volume": data.get("volume"),
            "week_52_high": data.get("week_52_high"),
            "week_52_low": data.get("week_52_low"),
            "beta": data.get("beta")
        },
        "analysis_summary": data.get("analysis_summary")
    }


# YardÄ±mcÄ± fonksiyonlar
def get_pe_interpretation(pe: Optional[float]) -> str:
    if pe is None:
        return "Veri yok"
    if pe < 0:
        return "Åirket zararda"
    if pe < 10:
        return "Ucuz - DÃ¼ÅŸÃ¼k deÄŸerleme"
    if pe < 20:
        return "Normal - Makul deÄŸerleme"
    if pe < 30:
        return "PahalÄ± - YÃ¼ksek beklenti"
    return "Ã‡ok pahalÄ± - Dikkatli olun"


def get_pb_interpretation(pb: Optional[float]) -> str:
    if pb is None:
        return "Veri yok"
    if pb < 1:
        return "Defter deÄŸerinin altÄ±nda - Potansiyel fÄ±rsat"
    if pb < 3:
        return "Normal aralÄ±kta"
    return "YÃ¼ksek - Prim ile iÅŸlem gÃ¶rÃ¼yor"


def get_peg_interpretation(peg: Optional[float]) -> str:
    if peg is None:
        return "Veri yok"
    if peg < 1:
        return "Cazip - BÃ¼yÃ¼meye gÃ¶re ucuz"
    if peg < 2:
        return "Normal"
    return "PahalÄ± - BÃ¼yÃ¼meye gÃ¶re yÃ¼ksek fiyat"


def get_roe_interpretation(roe: Optional[float]) -> str:
    if roe is None:
        return "Veri yok"
    if roe > 20:
        return "MÃ¼kemmel - Ã‡ok yÃ¼ksek kÃ¢rlÄ±lÄ±k"
    if roe > 15:
        return "Ä°yi - SaÄŸlÄ±klÄ± kÃ¢rlÄ±lÄ±k"
    if roe > 10:
        return "Orta - Kabul edilebilir"
    if roe > 0:
        return "ZayÄ±f - DÃ¼ÅŸÃ¼k kÃ¢rlÄ±lÄ±k"
    return "Negatif - Zarar"


def get_dividend_interpretation(div_yield: Optional[float]) -> str:
    if div_yield is None or div_yield == 0:
        return "TemettÃ¼ Ã¶demiyor"
    if div_yield > 5:
        return "YÃ¼ksek temettÃ¼ - Gelir yatÄ±rÄ±mcÄ±larÄ± iÃ§in cazip"
    if div_yield > 2:
        return "Orta temettÃ¼"
    return "DÃ¼ÅŸÃ¼k temettÃ¼"


def format_large_number(value) -> Optional[str]:
    if value is None:
        return None
    try:
        value = float(value)
        if value >= 1e12:
            return f"{value/1e12:.2f} Trilyon TL"
        elif value >= 1e9:
            return f"{value/1e9:.2f} Milyar TL"
        elif value >= 1e6:
            return f"{value/1e6:.2f} Milyon TL"
        else:
            return f"{value:,.0f} TL"
    except:
        return None
