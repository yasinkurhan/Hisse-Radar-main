"""
Gelişmiş Temel Analiz API Router
=================================
Bilanço, gelir tablosu ve finansal oranlar endpoint'leri
"""

from fastapi import APIRouter, HTTPException
from ..services.advanced_fundamental import fundamental_service

router = APIRouter(prefix="/api/fundamental", tags=["fundamental"])


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
