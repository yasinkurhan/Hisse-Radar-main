"""
Gelişmiş Temel Analiz API Router
=================================
Bilanço, gelir tablosu, finansal oranlar, ETF sahipliği, takvim, TTM, UFRS endpoint'leri
"""

import math
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..services.advanced_fundamental import fundamental_service
from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/fundamental", tags=["fundamental"])


def _clean_for_json(obj):
    """NaN, Inf, Timestamp gibi JSON uyumsuz değerleri temizle"""
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
async def get_fundamental_analysis(symbol: str):
    """
    Kapsamlı temel analiz
    
    İçerir:
    - Şirket bilgileri
    - Gelir tablosu (yıllık ve çeyreklik)
    - Bilanço
    - Nakit akış tablosu
    - Finansal oranlar
    - Büyüme metrikleri
    - Değerleme analizi
    - Grafik verileri
    """
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Temel analiz verisi bulunamadı")
        )
    
    return result


@router.get("/quick/{symbol}")
async def get_quick_fundamental(symbol: str):
    """
    Hızlı temel analiz özeti
    
    Sadece en önemli metrikler:
    - F/K oranı
    - PD/DD oranı
    - Temettü verimi
    - ROE
    - Borç/Özsermaye
    """
    
    return fundamental_service.get_quick_stats(symbol.upper())


@router.get("/income/{symbol}")
async def get_income_statement(symbol: str):
    """Gelir tablosu detayları"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    return {
        "symbol": symbol.upper(),
        "income_statement": result.get("income_statement", {}),
        "growth_metrics": result.get("growth_metrics", {})
    }


@router.get("/balance/{symbol}")
async def get_balance_sheet(symbol: str):
    """Bilanço detayları"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    return {
        "symbol": symbol.upper(),
        "balance_sheet": result.get("balance_sheet", {}),
        "ratios": result.get("ratios", {})
    }


@router.get("/cashflow/{symbol}")
async def get_cash_flow(symbol: str):
    """Nakit akış tablosu"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    return {
        "symbol": symbol.upper(),
        "cash_flow": result.get("cash_flow", {})
    }


@router.get("/ratios/{symbol}")
async def get_financial_ratios(symbol: str):
    """Tüm finansal oranlar"""
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    return {
        "symbol": symbol.upper(),
        "ratios": result.get("ratios", {}),
        "valuation": result.get("valuation", {})
    }


@router.get("/charts/{symbol}")
async def get_chart_data(symbol: str):
    """
    Grafik verileri
    
    Frontend'de görselleştirmek için hazır veri:
    - Gelir trendi
    - Kar trendi
    - Marj trendi
    - Varlık/Borç grafiği
    - Nakit akış grafiği
    """
    
    result = fundamental_service.get_full_fundamental_analysis(symbol.upper())
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Veri bulunamadı")
    
    return {
        "symbol": symbol.upper(),
        "charts": result.get("charts_data", {})
    }


@router.get("/compare")
async def compare_fundamentals(symbols: str):
    """
    Birden fazla hissenin temel analizini karşılaştır
    
    Örnek: /api/fundamental/compare?symbols=THYAO,PGSUS,TAVHL
    """
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:5]  # Max 5
    
    comparisons = []
    for symbol in symbol_list:
        stats = fundamental_service.get_quick_stats(symbol)
        comparisons.append(stats)
    
    # Sıralama bilgileri ekle
    metrics = ["pe_ratio", "pb_ratio", "roe", "dividend_yield"]
    rankings = {}
    
    for metric in metrics:
        values = [(c["symbol"], c.get(metric)) for c in comparisons if c.get(metric) is not None]
        if values:
            if metric in ["pe_ratio", "pb_ratio"]:  # Düşük daha iyi
                sorted_values = sorted(values, key=lambda x: x[1])
            else:  # Yüksek daha iyi
                sorted_values = sorted(values, key=lambda x: x[1], reverse=True)
            
            rankings[metric] = {v[0]: i+1 for i, v in enumerate(sorted_values)}
    
    return {
        "symbols": symbol_list,
        "data": comparisons,
        "rankings": rankings
    }


# ==========================================
# ETF SAHİPLİĞİ
# ==========================================

@router.get("/etf-holders/{symbol}")
def get_etf_holders(symbol: str):
    """
    Hisseyi bünyesinde barındıran uluslararası ETF'ler.
    
    Hangi yabancı ETF'lerin bu hisseyi portföyünde tuttuğunu gösterir.
    """
    try:
        fetcher = get_borsapy_fetcher()
        holders = fetcher.get_etf_holders(symbol.upper())
        
        if holders is None:
            return {
                "symbol": symbol.upper(),
                "holders": [],
                "count": 0,
                "message": "ETF sahiplik verisi bulunamadı"
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
# KURUMSAL TAKVİM & KAZANÇ TARİHLERİ
# ==========================================

@router.get("/calendar/{symbol}")
def get_corporate_calendar(symbol: str):
    """
    Şirket kurumsal takvimi.
    
    İçerir:
    - Temettü tarihleri (ex-date, pay date)
    - Kazanç açıklama tarihleri
    - Diğer kurumsal etkinlikler
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
# TTM (SON 12 AY) FİNANSALLARI
# ==========================================

@router.get("/ttm/{symbol}")
def get_ttm_financials(symbol: str):
    """
    TTM (Trailing Twelve Months / Son 12 Ay) finansal tabloları.
    Not: BIST hisseleri için genellikle veri bulunmaz.
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
            "description": "Son 12 aylık (TTM) toplam finansal veriler"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ANALİST TAHMİNLERİ & ÖNERİLERİ (YENİ - BIST İÇİN ÇALIŞIYOR)
# ==========================================

@router.get("/analyst/{symbol}")
def get_analyst_data(symbol: str):
    """
    Analist hedef fiyatları ve al/sat önerileri.
    
    İçerir:
    - Hedef fiyat (düşük, yüksek, ortalama, medyan)
    - Analist sayısı
    - Öneri dağılımı (strong buy, buy, hold, sell, strong sell)
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
# TEKNİK ANALİZ SİNYALLERİ (YENİ - BIST İÇİN ÇALIŞIYOR)
# ==========================================

@router.get("/ta-signals/{symbol}")
def get_ta_signals(symbol: str, interval: str = "1d"):
    """
    TradingView teknik analiz sinyalleri.
    
    Osilatörler, hareketli ortalamalar ve genel önerilerle
    AL/SAT/NÖTR sinyalleri sağlar.
    
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
    Tüm zaman dilimlerinde teknik analiz sinyalleri (1s, 5dk, 15dk, 1sa, 4sa, günlük, haftalık).
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
# BANKA UFRS FİNANSALLARI
# ==========================================

@router.get("/ufrs/{symbol}")
def get_ufrs_financials(symbol: str):
    """
    UFRS formatında finansal tablolar.
    Not: BIST hisseleri için genellikle veri bulunmaz.
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
            "description": "UFRS (Uluslararası Finansal Raporlama Standartları) formatında tablo"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# HİSSE BÖLÜNMELERİ & AKSİYONLAR
# ==========================================

@router.get("/actions/{symbol}")
def get_corporate_actions(symbol: str):
    """
    Şirket aksiyonları: Temettü ödemeleri ve hisse bölünmeleri.
    Not: BIST hisseleri için genellikle boş döner.
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
