"""
GeliÅŸmiÅŸ Temel Analiz API Router
=================================
BilanÃ§o, gelir tablosu, finansal oranlar, ETF sahipliÄŸi, takvim, TTM, UFRS endpoint'leri
"""

import math
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..services.advanced_fundamental import fundamental_service
from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/fundamental", tags=["fundamental"])


def _clean_for_json(obj):
    """NaN, Inf, Timestamp gibi JSON uyumsuz deÄŸerleri temizle"""
    import pandas as pd
    import numpy as np
    
    if obj is None:
        return None
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat() if not pd.isna(obj) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_for_json(item) for item in obj]
    if isinstance(obj, (pd.Series,)):
        return _clean_for_json(obj.to_dict())
    if isinstance(obj, (pd.DataFrame,)):
        return _clean_for_json(obj.to_dict(orient="records"))
    return obj


@router.get("/analysis/{symbol}")
def get_fundamental_analysis(symbol: str):
    """
    KapsamlÄ± temel analiz
    
    Ä°Ã§erir:
    - Åirket bilgileri
    - Gelir tablosu (yÄ±llÄ±k ve Ã§eyreklik)
    - BilanÃ§o
    - Nakit akÄ±ÅŸ tablosu
    - Finansal oranlar
    - BÃ¼yÃ¼me metrikleri
    - DeÄŸerleme analizi
    - Grafik verileri
    """
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Temel analiz verisi bulunamadÄ±")
        )
    
    return result


@router.get("/quick/{symbol}")
def get_quick_fundamental(symbol: str):
    """
    HÄ±zlÄ± temel analiz Ã¶zeti
    
    Sadece en Ã¶nemli metrikler:
    - F/K oranÄ±
    - PD/DD oranÄ±
    - TemettÃ¼ verimi
    - ROE
    - BorÃ§/Ã–zsermaye
    """
    
    return fundamental_service.get_quick_stats(symbol.upper())


@router.get("/income/{symbol}")
def get_income_statement(symbol: str):
    """Gelir tablosu detaylarÄ±"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadÄ±")
    
    return {
        "symbol": symbol.upper(),
        "income_statement": result.get("income_statement", {}),
        "growth_metrics": result.get("growth_metrics", {})
    }


@router.get("/balance/{symbol}")
def get_balance_sheet(symbol: str):
    """BilanÃ§o detaylarÄ±"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadÄ±")
    
    return {
        "symbol": symbol.upper(),
        "balance_sheet": result.get("balance_sheet", {}),
        "ratios": result.get("ratios", {})
    }


@router.get("/cashflow/{symbol}")
def get_cash_flow(symbol: str):
    """Nakit akÄ±ÅŸ tablosu"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadÄ±")
    
    return {
        "symbol": symbol.upper(),
        "cash_flow": result.get("cash_flow", {})
    }


@router.get("/ratios/{symbol}")
def get_financial_ratios(symbol: str):
    """TÃ¼m finansal oranlar"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadÄ±")
    
    return {
        "symbol": symbol.upper(),
        "ratios": result.get("ratios", {}),
        "valuation": result.get("valuation", {})
    }


@router.get("/charts/{symbol}")
def get_chart_data(symbol: str):
    """
    Grafik verileri
    
    Frontend'de gÃ¶rselleÅŸtirmek iÃ§in hazÄ±r veri:
    - Gelir trendi
    - Kar trendi
    - Marj trendi
    - VarlÄ±k/BorÃ§ grafiÄŸi
    - Nakit akÄ±ÅŸ grafiÄŸi
    """
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadÄ±")
    
    return {
        "symbol": symbol.upper(),
        "charts": result.get("charts_data", {})
    }


@router.get("/compare")
def compare_fundamentals(symbols: str):
    """
    Birden fazla hissenin temel analizini karÅŸÄ±laÅŸtÄ±r
    
    Ã–rnek: /api/fundamental/compare?symbols=THYAO,PGSUS,TAVHL
    """
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:5]  # Max 5
    
    comparisons = []
    for symbol in symbol_list:
        stats = fundamental_service.get_quick_stats(symbol)
        comparisons.append(stats)
    
    # SÄ±ralama bilgileri ekle
    metrics = ["pe_ratio", "pb_ratio", "roe", "dividend_yield"]
    rankings = {}
    
    for metric in metrics:
        values = [(c["symbol"], c.get(metric)) for c in comparisons if c.get(metric) is not None]
        if values:
            if metric in ["pe_ratio", "pb_ratio"]:  # DÃ¼ÅŸÃ¼k daha iyi
                sorted_values = sorted(values, key=lambda x: x[1])
            else:  # YÃ¼ksek daha iyi
                sorted_values = sorted(values, key=lambda x: x[1], reverse=True)
            
            rankings[metric] = {v[0]: i+1 for i, v in enumerate(sorted_values)}
    
    return {
        "symbols": symbol_list,
        "data": comparisons,
        "rankings": rankings
    }


# ==========================================
# ETF SAHÄ°PLÄ°ÄÄ°
# ==========================================

@router.get("/etf-holders/{symbol}")
def get_etf_holders(symbol: str):
    """
    Hisseyi bÃ¼nyesinde barÄ±ndÄ±ran uluslararasÄ± ETF'ler.
    
    Hangi yabancÄ± ETF'lerin bu hisseyi portfÃ¶yÃ¼nde tuttuÄŸunu gÃ¶sterir.
    """
    try:
        fetcher = get_borsapy_fetcher()
        holders = fetcher.get_etf_holders(symbol.upper())
        
        if holders is None:
            return {
                "symbol": symbol.upper(),
                "holders": [],
                "count": 0,
                "message": "ETF sahiplik verisi bulunamadÄ±"
            }
        
        holder_list = holders if isinstance(holders, list) else [holders]
        
        return _clean_for_json({
            "symbol": symbol.upper(),
            "holders": holder_list,
            "count": len(holder_list)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# KURUMSAL TAKVÄ°M & KAZANÃ‡ TARÄ°HLERÄ°
# ==========================================

@router.get("/calendar/{symbol}")
def get_corporate_calendar(symbol: str):
    """
    Åirket kurumsal takvimi.
    
    Ä°Ã§erir:
    - TemettÃ¼ tarihleri (ex-date, pay date)
    - KazanÃ§ aÃ§Ä±klama tarihleri
    - DiÄŸer kurumsal etkinlikler
    """
    try:
        fetcher = get_borsapy_fetcher()
        calendar = fetcher.get_calendar(symbol.upper())
        earnings = fetcher.get_earnings_dates(symbol.upper())
        
        return _clean_for_json({
            "symbol": symbol.upper(),
            "calendar": calendar,
            "earnings_dates": earnings,
            "has_calendar": calendar is not None,
            "has_earnings": earnings is not None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# TTM (SON 12 AY) FÄ°NANSALLARI
# ==========================================

@router.get("/ttm/{symbol}")
def get_ttm_financials(symbol: str):
    """
    TTM (Trailing Twelve Months / Son 12 Ay) finansal tablolarÄ±.
    Not: BIST hisseleri iÃ§in genellikle veri bulunmaz.
    """
    try:
        fetcher = get_borsapy_fetcher()
        ttm = fetcher.get_ttm_financials(symbol.upper())
        
        if ttm.get("error"):
            raise HTTPException(status_code=404, detail=ttm["error"])
        
        has_data = any(v is not None for k, v in ttm.items() if k != "symbol")
        
        return _clean_for_json({
            **ttm,
            "has_data": has_data,
            "description": "Son 12 aylÄ±k (TTM) toplam finansal veriler"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ANALÄ°ST TAHMÄ°NLERÄ° & Ã–NERÄ°LERÄ° (YENÄ° - BIST Ä°Ã‡Ä°N Ã‡ALIÅIYOR)
# ==========================================

@router.get("/analyst/{symbol}")
def get_analyst_data(symbol: str):
    """
    Analist hedef fiyatlarÄ± ve al/sat Ã¶nerileri.
    
    Ä°Ã§erir:
    - Hedef fiyat (dÃ¼ÅŸÃ¼k, yÃ¼ksek, ortalama, medyan)
    - Analist sayÄ±sÄ±
    - Ã–neri daÄŸÄ±lÄ±mÄ± (strong buy, buy, hold, sell, strong sell)
    """
    try:
        fetcher = get_borsapy_fetcher()
        data = fetcher.get_analyst_data(symbol.upper())
        
        if data.get("error"):
            raise HTTPException(status_code=404, detail=data["error"])
        
        has_data = data.get("price_targets") is not None or data.get("recommendations_summary") is not None
        
        return _clean_for_json({
            **data,
            "has_data": has_data,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# TEKNÄ°K ANALÄ°Z SÄ°NYALLERÄ° (YENÄ° - BIST Ä°Ã‡Ä°N Ã‡ALIÅIYOR)
# ==========================================

@router.get("/ta-signals/{symbol}")
def get_ta_signals(symbol: str, interval: str = "1d"):
    """
    TradingView teknik analiz sinyalleri.
    
    OsilatÃ¶rler, hareketli ortalamalar ve genel Ã¶nerilerle
    AL/SAT/NÃ–TR sinyalleri saÄŸlar.
    
    interval parametreleri: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1W, 1M
    """
    try:
        fetcher = get_borsapy_fetcher()
        data = fetcher.get_ta_signals(symbol.upper(), interval=interval)
        
        if data.get("error"):
            raise HTTPException(status_code=404, detail=data["error"])
        
        return _clean_for_json(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ta-signals-all/{symbol}")
def get_ta_signals_all_timeframes(symbol: str):
    """
    TÃ¼m zaman dilimlerinde teknik analiz sinyalleri (1s, 5dk, 15dk, 1sa, 4sa, gÃ¼nlÃ¼k, haftalÄ±k).
    """
    try:
        fetcher = get_borsapy_fetcher()
        data = fetcher.get_ta_signals_all_timeframes(symbol.upper())
        
        if data.get("error"):
            raise HTTPException(status_code=404, detail=data["error"])
        
        return _clean_for_json(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# BANKA UFRS FÄ°NANSALLARI
# ==========================================

@router.get("/ufrs/{symbol}")
def get_ufrs_financials(symbol: str):
    """
    UFRS formatÄ±nda finansal tablolar.
    Not: BIST hisseleri iÃ§in genellikle veri bulunmaz.
    """
    try:
        fetcher = get_borsapy_fetcher()
        ufrs = fetcher.get_ufrs_financials(symbol.upper())
        
        if ufrs.get("error"):
            raise HTTPException(status_code=404, detail=ufrs["error"])
        
        has_data = any(v is not None for k, v in ufrs.items() if k != "symbol")
        
        return _clean_for_json({
            **ufrs,
            "has_data": has_data,
            "description": "UFRS (UluslararasÄ± Finansal Raporlama StandartlarÄ±) formatÄ±nda tablo"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# HÄ°SSE BÃ–LÃœNMELERÄ° & AKSÄ°YONLAR
# ==========================================

@router.get("/actions/{symbol}")
def get_corporate_actions(symbol: str):
    """
    Åirket aksiyonlarÄ±: TemettÃ¼ Ã¶demeleri ve hisse bÃ¶lÃ¼nmeleri.
    Not: BIST hisseleri iÃ§in genellikle boÅŸ dÃ¶ner.
    """
    try:
        fetcher = get_borsapy_fetcher()
        actions = fetcher.get_actions(symbol.upper())
        splits = fetcher.get_splits(symbol.upper())
        isin = fetcher.get_isin(symbol.upper())
        
        return _clean_for_json({
            "symbol": symbol.upper(),
            "isin": isin,
            "actions": actions,
            "splits": splits,
            "has_actions": actions is not None,
            "has_splits": splits is not None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
