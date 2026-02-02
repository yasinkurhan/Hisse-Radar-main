"""
HisseRadar Temel Analiz Router
===============================
F/K, PD/DD, bilanço ve finansal veriler API'leri
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..services.fundamental_analysis import get_fundamental_analyzer


router = APIRouter(prefix="/api/fundamental", tags=["Temel Analiz"])


@router.get("/{symbol}")
async def get_fundamental_data(symbol: str):
    """
    Hisse için kapsamlı temel analiz verilerini getir.
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    
    Dönen veriler:
    - Şirket bilgileri
    - Değerleme oranları (F/K, PD/DD, F/S)
    - Kârlılık oranları (ROE, ROA, kâr marjı)
    - Temettü bilgileri
    - Bilanço verileri
    - Analiz özeti ve değerlendirme
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    # Veri kontrolü - hata varsa ve anlamlı veri yoksa minimal veri döndür
    has_valid_data = (
        data.get("company_name") or 
        data.get("current_price") or 
        data.get("market_cap") or
        data.get("pe_ratio")
    )
    
    if "error" in data and not has_valid_data:
        # Hata durumunda minimal veri döndür (404 yerine)
        return {
            "symbol": symbol.upper(),
            "company_name": f"{symbol.upper()}",
            "sector": "Bilinmiyor",
            "industry": None,
            "error_message": f"{symbol} için temel analiz verisi bulunamadı",
            "analysis_summary": {
                "valuation": "Belirsiz",
                "profitability": "Belirsiz", 
                "growth": "Belirsiz",
                "dividend": "Belirsiz",
                "overall": "Veri Yok",
                "notes": ["Yahoo Finance'dan veri alınamadı. Lütfen daha sonra tekrar deneyin."]
            }
        }
    
    return data


@router.get("/{symbol}/valuation")
async def get_valuation_ratios(symbol: str):
    """
    Değerleme oranlarını getir.
    
    - F/K (P/E): Fiyat / Kazanç - Hissenin kaç yıllık kârına denk olduğunu gösterir
    - PD/DD (P/B): Piyasa Değeri / Defter Değeri - 1'in altı ucuz kabul edilir
    - F/S (P/S): Fiyat / Satış - Gelire göre değerleme
    - PEG: F/K / Büyüme - 1'in altı cazip
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
                "label": "F/K (Fiyat/Kazanç)",
                "description": "Hissenin kaç yıllık kârına eşdeğer olduğunu gösterir",
                "interpretation": get_pe_interpretation(data.get("pe_ratio"))
            },
            "forward_pe": {
                "value": data.get("forward_pe"),
                "label": "İleriye Dönük F/K",
                "description": "Gelecek kazanç tahminlerine göre F/K"
            },
            "pb_ratio": {
                "value": data.get("pb_ratio"),
                "label": "PD/DD (Piyasa D./Defter D.)",
                "description": "1'in altında ise defter değerinin altında işlem görüyor",
                "interpretation": get_pb_interpretation(data.get("pb_ratio"))
            },
            "ps_ratio": {
                "value": data.get("ps_ratio"),
                "label": "F/S (Fiyat/Satış)",
                "description": "Her 1 TL satış için ödenen fiyat"
            },
            "peg_ratio": {
                "value": data.get("peg_ratio"),
                "label": "PEG Oranı",
                "description": "F/K'nın büyümeye oranı, 1'in altı cazip",
                "interpretation": get_peg_interpretation(data.get("peg_ratio"))
            },
            "enterprise_to_ebitda": {
                "value": data.get("enterprise_to_ebitda"),
                "label": "EV/EBITDA",
                "description": "Şirket değeri / FAVÖK"
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
async def get_profitability_ratios(symbol: str):
    """
    Kârlılık oranlarını getir.
    
    - ROE: Özkaynak Kârlılığı - %15 üzeri iyi
    - ROA: Aktif Kârlılık - Varlık kullanım etkinliği
    - Kâr Marjı: Net kâr / Gelir
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "profitability": {
            "roe": {
                "value": data.get("roe"),
                "label": "ROE (Özkaynak Kârlılığı)",
                "description": "Her 100 TL özkaynak için kazanılan kâr",
                "benchmark": "%15 üzeri iyi kabul edilir",
                "interpretation": get_roe_interpretation(data.get("roe"))
            },
            "roa": {
                "value": data.get("roa"),
                "label": "ROA (Aktif Kârlılık)",
                "description": "Her 100 TL varlık için kazanılan kâr",
                "benchmark": "%5 üzeri iyi kabul edilir"
            },
            "profit_margin": {
                "value": data.get("profit_margin"),
                "label": "Net Kâr Marjı",
                "description": "Her 100 TL gelirden kalan net kâr"
            },
            "operating_margin": {
                "value": data.get("operating_margin"),
                "label": "Faaliyet Kâr Marjı",
                "description": "Faaliyet kârı / Gelir"
            },
            "gross_margin": {
                "value": data.get("gross_margin"),
                "label": "Brüt Kâr Marjı",
                "description": "Brüt kâr / Gelir"
            }
        }
    }


@router.get("/{symbol}/dividend")
async def get_dividend_info(symbol: str):
    """
    Temettü bilgilerini getir.
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "dividend": {
            "dividend_yield": {
                "value": data.get("dividend_yield"),
                "label": "Temettü Verimi",
                "description": "Yıllık temettü / Hisse fiyatı",
                "interpretation": get_dividend_interpretation(data.get("dividend_yield"))
            },
            "dividend_rate": {
                "value": data.get("dividend_rate"),
                "label": "Yıllık Temettü",
                "description": "Hisse başı yıllık temettü tutarı (TL)"
            },
            "payout_ratio": {
                "value": data.get("payout_ratio"),
                "label": "Temettü Dağıtım Oranı",
                "description": "Net kârın ne kadarı temettü olarak dağıtılıyor"
            },
            "ex_dividend_date": {
                "value": data.get("ex_dividend_date"),
                "label": "Temettü Hak Ediş Tarihi",
                "description": "Bu tarihten önce almış olmalısınız"
            }
        }
    }


@router.get("/{symbol}/balance")
async def get_balance_sheet_summary(symbol: str):
    """
    Bilanço özetini getir.
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
                "label": "Toplam Borç",
                "formatted": format_large_number(data.get("total_debt"))
            },
            "total_revenue": {
                "value": data.get("total_revenue"),
                "label": "Toplam Gelir",
                "formatted": format_large_number(data.get("total_revenue"))
            },
            "debt_to_equity": {
                "value": data.get("debt_to_equity"),
                "label": "Borç/Özkaynak",
                "description": "1'in altı tercih edilir"
            },
            "current_ratio": {
                "value": data.get("current_ratio"),
                "label": "Cari Oran",
                "description": "Kısa vadeli borçları ödeme kapasitesi, 1.5+ iyi"
            },
            "quick_ratio": {
                "value": data.get("quick_ratio"),
                "label": "Asit-Test Oranı",
                "description": "Stoklar hariç likidite oranı"
            },
            "book_value": {
                "value": data.get("book_value"),
                "label": "Hisse Başı Defter Değeri",
                "description": "Şirket tasfiye edilse hisse başı değer"
            }
        },
        "shares": {
            "shares_outstanding": {
                "value": data.get("shares_outstanding"),
                "label": "Toplam Hisse Sayısı",
                "formatted": format_large_number(data.get("shares_outstanding"))
            },
            "float_shares": {
                "value": data.get("float_shares"),
                "label": "Halka Açık Hisse",
                "formatted": format_large_number(data.get("float_shares"))
            }
        }
    }


@router.get("/{symbol}/growth")
async def get_growth_metrics(symbol: str):
    """
    Büyüme metriklerini getir.
    """
    analyzer = get_fundamental_analyzer()
    data = analyzer.get_fundamental_data(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "company_name": data.get("company_name"),
        "growth": {
            "revenue_growth": {
                "value": data.get("revenue_growth"),
                "label": "Gelir Büyümesi (YoY)",
                "description": "Yıllık gelir artışı"
            },
            "earnings_growth": {
                "value": data.get("earnings_growth"),
                "label": "Kâr Büyümesi (YoY)",
                "description": "Yıllık kâr artışı"
            },
            "earnings_quarterly_growth": {
                "value": data.get("earnings_quarterly_growth"),
                "label": "Çeyreklik Kâr Büyümesi",
                "description": "Son çeyrek kâr artışı"
            }
        },
        "eps": {
            "trailing_eps": {
                "value": data.get("trailing_eps"),
                "label": "Hisse Başı Kazanç (TTM)",
                "description": "Son 12 ayın hisse başı kazancı"
            },
            "forward_eps": {
                "value": data.get("forward_eps"),
                "label": "Tahmini HBK",
                "description": "Gelecek 12 ay için beklenen HBK"
            }
        }
    }


@router.get("/{symbol}/summary")
async def get_fundamental_summary(symbol: str):
    """
    Temel analiz özet raporu.
    
    Tüm önemli metriklerin özeti ve genel değerlendirme.
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


# Yardımcı fonksiyonlar
def get_pe_interpretation(pe: Optional[float]) -> str:
    if pe is None:
        return "Veri yok"
    if pe < 0:
        return "Şirket zararda"
    if pe < 10:
        return "Ucuz - Düşük değerleme"
    if pe < 20:
        return "Normal - Makul değerleme"
    if pe < 30:
        return "Pahalı - Yüksek beklenti"
    return "Çok pahalı - Dikkatli olun"


def get_pb_interpretation(pb: Optional[float]) -> str:
    if pb is None:
        return "Veri yok"
    if pb < 1:
        return "Defter değerinin altında - Potansiyel fırsat"
    if pb < 3:
        return "Normal aralıkta"
    return "Yüksek - Prim ile işlem görüyor"


def get_peg_interpretation(peg: Optional[float]) -> str:
    if peg is None:
        return "Veri yok"
    if peg < 1:
        return "Cazip - Büyümeye göre ucuz"
    if peg < 2:
        return "Normal"
    return "Pahalı - Büyümeye göre yüksek fiyat"


def get_roe_interpretation(roe: Optional[float]) -> str:
    if roe is None:
        return "Veri yok"
    if roe > 20:
        return "Mükemmel - Çok yüksek kârlılık"
    if roe > 15:
        return "İyi - Sağlıklı kârlılık"
    if roe > 10:
        return "Orta - Kabul edilebilir"
    if roe > 0:
        return "Zayıf - Düşük kârlılık"
    return "Negatif - Zarar"


def get_dividend_interpretation(div_yield: Optional[float]) -> str:
    if div_yield is None or div_yield == 0:
        return "Temettü ödemiyor"
    if div_yield > 5:
        return "Yüksek temettü - Gelir yatırımcıları için cazip"
    if div_yield > 2:
        return "Orta temettü"
    return "Düşük temettü"


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
