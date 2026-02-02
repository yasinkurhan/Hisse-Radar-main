"""
HisseRadar GeliÅŸmiÅŸ Filtreleme Router
=====================================
Ã‡oklu filtre, kayÄ±tlÄ± filtreler ve screener API'leri
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel
import json
import os

router = APIRouter(prefix="/api/filters", tags=["Filtreleme"])

# Hisse verileri
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bist_stocks.json")

def load_stocks():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("stocks", []) if isinstance(data, dict) else data

# KayÄ±tlÄ± filtre modeli
class SavedFilter(BaseModel):
    name: str
    description: Optional[str] = None
    filters: dict

# Filtre parametreleri modeli
class FilterParams(BaseModel):
    # Endeks filtreleri
    indices: Optional[List[str]] = None  # BIST30, BIST100, KATILIM
    
    # SektÃ¶r filtreleri
    sectors: Optional[List[str]] = None
    
    # Fiyat filtreleri
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    
    # DeÄŸiÅŸim filtreleri
    min_change: Optional[float] = None
    max_change: Optional[float] = None
    
    # Hacim filtreleri
    min_volume: Optional[int] = None
    volume_ratio_min: Optional[float] = None  # Ort. hacme gÃ¶re oran
    
    # Teknik gÃ¶sterge filtreleri
    rsi_min: Optional[float] = None
    rsi_max: Optional[float] = None
    rsi_signal: Optional[str] = None  # oversold, overbought, neutral
    
    macd_signal: Optional[str] = None  # bullish, bearish
    
    bb_position: Optional[str] = None  # below_lower, above_upper, middle
    
    ma_trend: Optional[str] = None  # bullish, bearish
    
    # Sinyal filtreleri
    signals: Optional[List[str]] = None  # GUCLU_AL, AL, TUT, SAT, GUCLU_SAT
    
    # Skor filtreleri
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    
    # Potansiyel filtreleri
    min_target_percent: Optional[float] = None
    min_risk_reward: Optional[float] = None


@router.get("/sectors")
async def get_sectors():
    """Mevcut sektÃ¶rleri listele"""
    stocks = load_stocks()
    sectors = set()
    for stock in stocks:
        if stock.get("sector"):
            sectors.add(stock["sector"])
    return {
        "success": True,
        "sectors": sorted(list(sectors)),
        "count": len(sectors)
    }


@router.get("/indices")
async def get_indices():
    """Mevcut endeksleri listele"""
    stocks = load_stocks()
    indices = {
        "BIST30": 0,
        "BIST100": 0,
        "KATILIM": 0,
        "DIGER": 0
    }
    
    for stock in stocks:
        tags = stock.get("tags", [])
        if "BIST30" in tags:
            indices["BIST30"] += 1
        if "BIST100" in tags:
            indices["BIST100"] += 1
        if "KATILIM" in tags:
            indices["KATILIM"] += 1
        if not any(t in tags for t in ["BIST30", "BIST100", "KATILIM"]):
            indices["DIGER"] += 1
    
    return {
        "success": True,
        "indices": [
            {"name": "BIST30", "count": indices["BIST30"], "description": "En likit 30 hisse"},
            {"name": "BIST100", "count": indices["BIST100"], "description": "En bÃ¼yÃ¼k 100 hisse"},
            {"name": "KATILIM", "count": indices["KATILIM"], "description": "KatÄ±lÄ±m endeksi hisseleri"},
            {"name": "DIGER", "count": indices["DIGER"], "description": "DiÄŸer BIST hisseleri"}
        ]
    }


@router.get("/presets")
async def get_preset_filters():
    """HazÄ±r filtre ÅŸablonlarÄ±"""
    return {
        "success": True,
        "presets": [
            {
                "id": "strong_buy",
                "name": "GÃ¼Ã§lÃ¼ Al Sinyalleri",
                "description": "GÃ¼Ã§lÃ¼ al sinyali veren hisseler",
                "icon": "ğŸš€",
                "filters": {
                    "signals": ["GUCLU_AL"],
                    "min_score": 70
                }
            },
            {
                "id": "oversold_bounce",
                "name": "AÅŸÄ±rÄ± SatÄ±m Toparlanma",
                "description": "RSI aÅŸÄ±rÄ± satÄ±mda, toparlanma potansiyeli",
                "icon": "ğŸ“ˆ",
                "filters": {
                    "rsi_max": 35,
                    "macd_signal": "bullish",
                    "volume_ratio_min": 1.2
                }
            },
            {
                "id": "breakout",
                "name": "KÄ±rÄ±lma AdaylarÄ±",
                "description": "Bollinger Ã¼st bandÄ±na yakÄ±n, hacim artÄ±ÅŸÄ±",
                "icon": "ğŸ’¥",
                "filters": {
                    "bb_position": "above_upper",
                    "volume_ratio_min": 1.5,
                    "ma_trend": "bullish"
                }
            },
            {
                "id": "high_momentum",
                "name": "YÃ¼ksek Momentum",
                "description": "GÃ¼Ã§lÃ¼ trend ve momentum",
                "icon": "âš¡",
                "filters": {
                    "rsi_min": 50,
                    "rsi_max": 70,
                    "macd_signal": "bullish",
                    "ma_trend": "bullish"
                }
            },
            {
                "id": "value_pick",
                "name": "DeÄŸer FÄ±rsatlarÄ±",
                "description": "DÃ¼ÅŸÃ¼k fiyatlÄ±, potansiyelli hisseler",
                "icon": "ğŸ’",
                "filters": {
                    "max_price": 50,
                    "min_target_percent": 15,
                    "min_risk_reward": 2
                }
            },
            {
                "id": "blue_chip_buy",
                "name": "Blue Chip Al",
                "description": "BIST30 hisselerinde al sinyalleri",
                "icon": "ğŸ¦",
                "filters": {
                    "indices": ["BIST30"],
                    "signals": ["GUCLU_AL", "AL"]
                }
            },
            {
                "id": "katilim_buy",
                "name": "KatÄ±lÄ±m Endeksi Al",
                "description": "Faizsiz yatÄ±rÄ±m uyumlu al sinyalleri",
                "icon": "ğŸŒ™",
                "filters": {
                    "indices": ["KATILIM"],
                    "signals": ["GUCLU_AL", "AL"]
                }
            },
            {
                "id": "high_volume",
                "name": "YÃ¼ksek Hacim",
                "description": "OrtalamanÄ±n 2x Ã¼stÃ¼ hacim",
                "icon": "ğŸ“Š",
                "filters": {
                    "volume_ratio_min": 2.0
                }
            },
            {
                "id": "sell_signals",
                "name": "SatÄ±ÅŸ Sinyalleri",
                "description": "Dikkat! Sat sinyali veren hisseler",
                "icon": "âš ï¸",
                "filters": {
                    "signals": ["SAT", "GUCLU_SAT"]
                }
            },
            {
                "id": "low_risk",
                "name": "DÃ¼ÅŸÃ¼k Risk",
                "description": "YÃ¼ksek R/R oranÄ±, kontrollÃ¼ risk",
                "icon": "ğŸ›¡ï¸",
                "filters": {
                    "min_risk_reward": 2.5,
                    "signals": ["GUCLU_AL", "AL"]
                }
            }
        ]
    }


@router.post("/apply")
async def apply_filters(params: FilterParams):
    """
    GeliÅŸmiÅŸ filtreleri uygula
    
    Bu endpoint analiz sonuÃ§larÄ±nÄ± filtreler.
    Ã–nce /api/analysis/daily Ã§alÄ±ÅŸtÄ±rÄ±lmalÄ±.
    """
    # Bu endpoint frontend'de filtreleme yapmak iÃ§in parametre yapÄ±sÄ±nÄ± dÃ¶ner
    # GerÃ§ek filtreleme client-side yapÄ±lacak Ã§Ã¼nkÃ¼ analiz sonuÃ§larÄ± frontend'de
    return {
        "success": True,
        "message": "Filtreler baÅŸarÄ±yla uygulandÄ±",
        "applied_filters": params.dict(exclude_none=True)
    }


@router.get("/stats")
async def get_filter_stats():
    """Filtre iÃ§in hisse istatistikleri"""
    stocks = load_stocks()
    
    # SektÃ¶r daÄŸÄ±lÄ±mÄ±
    sector_counts = {}
    for stock in stocks:
        sector = stock.get("sector", "DiÄŸer")
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
    
    # Fiyat aralÄ±klarÄ±
    price_ranges = {
        "0-10 TL": 0,
        "10-25 TL": 0,
        "25-50 TL": 0,
        "50-100 TL": 0,
        "100-500 TL": 0,
        "500+ TL": 0
    }
    
    return {
        "success": True,
        "total_stocks": len(stocks),
        "sector_distribution": sector_counts,
        "price_ranges": price_ranges,
        "available_filters": [
            "indices", "sectors", "price", "change", "volume",
            "rsi", "macd", "bollinger", "ma_trend", "signals", "score"
        ]
    }
