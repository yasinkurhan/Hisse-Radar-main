"""
AI Tahmin API Router
====================
Yapay zeka destekli fiyat tahmini endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.ai_prediction import prediction_service
from ..services.borsapy_fetcher import get_borsapy_fetcher
from ..services.cache_service import PredictionCache

router = APIRouter(prefix="/api/ai", tags=["ai"])

# borsapy fetcher instance
borsapy_fetcher = get_borsapy_fetcher()


@router.get("/predict/{symbol}")
async def predict_price(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30, description="KaÃ§ gÃ¼n ilerisi tahmin edilsin"),
    model: str = Query(default="ensemble", description="Model tipi: linear, prophet, ensemble")
):
    """
    AI destekli fiyat tahmini
    
    - **symbol**: Hisse sembolÃ¼ (Ã¶rn: THYAO)
    - **days**: Tahmin edilecek gÃ¼n sayÄ±sÄ± (1-30)
    - **model**: KullanÄ±lacak ML modeli
    """
    
    # Cache kontrolÃ¼
    cache_key = f"{symbol}_{days}_{model}"
    cached = PredictionCache.get_prediction(cache_key)
    if cached:
        return cached
    
    # Geçmiş verileri al (minimum 90 gün)
    historical = borsapy_fetcher.get_history(symbol, period="6mo")
    
    if historical is None or historical.empty or len(historical) < 30:
        raise HTTPException(
            status_code=400, 
            detail="Yeterli geçmiş veri bulunamadı (minimum 30 gün gerekli)"
        )
    
    # Tahmin yap
    result = prediction_service.predict_price(
        symbol=symbol,
        historical_data=historical,
        days_ahead=days,
        model_type=model
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Tahmin yapÄ±lamadÄ±"))
    
    # AI sinyali ekle
    signal = prediction_service.get_ai_signal(symbol, result)
    result["ai_signal"] = signal
    
    # Cache'e kaydet
    PredictionCache.set_prediction(cache_key, result)
    
    return result


@router.get("/signal/{symbol}")
async def get_ai_signal(symbol: str):
    """
    Hisse iÃ§in AI al/sat sinyali
    
    DÃ¶nen sinyal deÄŸerleri:
    - GÃœÃ‡LÃœ AL: YÃ¼ksek gÃ¼venle al
    - AL: Orta gÃ¼venle al
    - BEKLE: Pozisyon alma
    - SAT: Orta gÃ¼venle sat
    - GÃœÃ‡LÃœ SAT: YÃ¼ksek gÃ¼venle sat
    """
    
    # Ã–nce tahmin yap
    historical = borsapy_fetcher.get_history(symbol, period="6mo")
    
    if historical is None or historical.empty or len(historical) < 30:
        return {
            "symbol": symbol,
            "signal": "BEKLE",
            "strength": 0,
            "reason": "Yeterli veri yok"
        }
    
    result = prediction_service.predict_price(
        symbol=symbol,
        historical_data=historical,
        days_ahead=7,
        model_type="ensemble"
    )
    
    if not result.get("success"):
        return {
            "symbol": symbol,
            "signal": "BEKLE",
            "strength": 0,
            "reason": "Tahmin yapÄ±lamadÄ±"
        }
    
    signal = prediction_service.get_ai_signal(symbol, result)
    signal["symbol"] = symbol
    
    return signal


@router.get("/batch-signals")
async def get_batch_signals(symbols: str = Query(..., description="VirgÃ¼lle ayrÄ±lmÄ±ÅŸ semboller")):
    """
    Birden fazla hisse iÃ§in AI sinyalleri
    
    Ã–rnek: /api/ai/batch-signals?symbols=THYAO,SISE,AKBNK
    """
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:20]  # Max 20
    
    results = []
    for symbol in symbol_list:
        try:
            historical = borsapy_fetcher.get_history(symbol, period="6mo")
            
            if historical is not None and not historical.empty and len(historical) >= 30:
                prediction = prediction_service.predict_price(
                    symbol=symbol,
                    historical_data=historical,
                    days_ahead=7,
                    model_type="ensemble"
                )
                
                if prediction.get("success"):
                    signal = prediction_service.get_ai_signal(symbol, prediction)
                    signal["symbol"] = symbol
                    signal["current_price"] = prediction.get("current_price")
                    signal["target_7d"] = prediction["summary"]["target_price_7d"]
                    results.append(signal)
                else:
                    results.append({
                        "symbol": symbol,
                        "signal": "BEKLE",
                        "strength": 0,
                        "reason": "Analiz yapÄ±lamadÄ±"
                    })
            else:
                results.append({
                    "symbol": symbol,
                    "signal": "BEKLE", 
                    "strength": 0,
                    "reason": "Yetersiz veri"
                })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "signal": "HATA",
                "strength": 0,
                "reason": str(e)
            })
    
    # Sinyale gÃ¶re sÄ±rala
    signal_order = {"GÃœÃ‡LÃœ AL": 0, "AL": 1, "BEKLE": 2, "SAT": 3, "GÃœÃ‡LÃœ SAT": 4, "HATA": 5}
    results.sort(key=lambda x: (signal_order.get(x["signal"], 5), -x.get("strength", 0)))
    
    return {
        "count": len(results),
        "signals": results,
        "summary": {
            "strong_buy": sum(1 for r in results if r["signal"] == "GÃœÃ‡LÃœ AL"),
            "buy": sum(1 for r in results if r["signal"] == "AL"),
            "hold": sum(1 for r in results if r["signal"] == "BEKLE"),
            "sell": sum(1 for r in results if r["signal"] == "SAT"),
            "strong_sell": sum(1 for r in results if r["signal"] == "GÃœÃ‡LÃœ SAT")
        }
    }


@router.get("/model-info")
async def get_model_info():
    """Mevcut AI modelleri hakkÄ±nda bilgi"""
    
    return {
        "models": {
            "linear": {
                "name": "Linear Regression",
                "description": "Basit doÄŸrusal regresyon modeli",
                "speed": "Ã‡ok HÄ±zlÄ±",
                "accuracy": "Orta",
                "best_for": "KÄ±sa vadeli, dÃ¼ÅŸÃ¼k volatiliteli hisseler"
            },
            "ensemble": {
                "name": "Ensemble (Topluluk)",
                "description": "Ridge, Random Forest ve Gradient Boosting kombinasyonu",
                "speed": "HÄ±zlÄ±",
                "accuracy": "YÃ¼ksek",
                "best_for": "Genel kullanÄ±m, dengeli tahminler"
            },
            "prophet": {
                "name": "Facebook Prophet",
                "description": "Zaman serisi tahmini iÃ§in Ã¶zel model",
                "speed": "YavaÅŸ",
                "accuracy": "YÃ¼ksek",
                "best_for": "Mevsimsellik gÃ¶steren hisseler"
            }
        },
        "features_used": [
            "Hareketli Ortalamalar (MA5, MA10, MA20)",
            "RSI (GÃ¶receli GÃ¼Ã§ Endeksi)",
            "Volatilite",
            "Momentum",
            "Gecikmeli Fiyatlar (Lag Features)"
        ],
        "disclaimer": "Bu tahminler yatÄ±rÄ±m tavsiyesi deÄŸildir. TÃ¼m yatÄ±rÄ±m kararlarÄ±nÄ±zÄ± kendi araÅŸtÄ±rmanÄ±za dayanarak verin."
    }
