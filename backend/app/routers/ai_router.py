"""
AI Tahmin API Router
====================
Yapay zeka destekli fiyat tahmini endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.ai_prediction import prediction_service
from ..services.yahoo_fetcher import get_yahoo_fetcher
from ..services.cache_service import PredictionCache

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Yahoo fetcher instance
yahoo_fetcher = get_yahoo_fetcher()


@router.get("/predict/{symbol}")
async def predict_price(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30, description="Kaç gün ilerisi tahmin edilsin"),
    model: str = Query(default="ensemble", description="Model tipi: linear, prophet, ensemble")
):
    """
    AI destekli fiyat tahmini
    
    - **symbol**: Hisse sembolü (örn: THYAO)
    - **days**: Tahmin edilecek gün sayısı (1-30)
    - **model**: Kullanılacak ML modeli
    """
    
    # Cache kontrolü
    cache_key = f"{symbol}_{days}_{model}"
    cached = PredictionCache.get_prediction(cache_key)
    if cached:
        return cached
    
    # Geçmiş verileri al (minimum 90 gün)
    historical = yahoo_fetcher.get_historical_prices(symbol, period="6mo")
    
    if not historical or len(historical) < 30:
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
        raise HTTPException(status_code=500, detail=result.get("error", "Tahmin yapılamadı"))
    
    # AI sinyali ekle
    signal = prediction_service.get_ai_signal(symbol, result)
    result["ai_signal"] = signal
    
    # Cache'e kaydet
    PredictionCache.set_prediction(cache_key, result)
    
    return result


@router.get("/signal/{symbol}")
async def get_ai_signal(symbol: str):
    """
    Hisse için AI al/sat sinyali
    
    Dönen sinyal değerleri:
    - GÜÇLÜ AL: Yüksek güvenle al
    - AL: Orta güvenle al
    - BEKLE: Pozisyon alma
    - SAT: Orta güvenle sat
    - GÜÇLÜ SAT: Yüksek güvenle sat
    """
    
    # Önce tahmin yap
    historical = yahoo_fetcher.get_historical_prices(symbol, period="6mo")
    
    if not historical or len(historical) < 30:
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
            "reason": "Tahmin yapılamadı"
        }
    
    signal = prediction_service.get_ai_signal(symbol, result)
    signal["symbol"] = symbol
    
    return signal


@router.get("/batch-signals")
async def get_batch_signals(symbols: str = Query(..., description="Virgülle ayrılmış semboller")):
    """
    Birden fazla hisse için AI sinyalleri
    
    Örnek: /api/ai/batch-signals?symbols=THYAO,SISE,AKBNK
    """
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")][:20]  # Max 20
    
    results = []
    for symbol in symbol_list:
        try:
            historical = yahoo_fetcher.get_historical_prices(symbol, period="6mo")
            
            if historical and len(historical) >= 30:
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
                        "reason": "Analiz yapılamadı"
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
    
    # Sinyale göre sırala
    signal_order = {"GÜÇLÜ AL": 0, "AL": 1, "BEKLE": 2, "SAT": 3, "GÜÇLÜ SAT": 4, "HATA": 5}
    results.sort(key=lambda x: (signal_order.get(x["signal"], 5), -x.get("strength", 0)))
    
    return {
        "count": len(results),
        "signals": results,
        "summary": {
            "strong_buy": sum(1 for r in results if r["signal"] == "GÜÇLÜ AL"),
            "buy": sum(1 for r in results if r["signal"] == "AL"),
            "hold": sum(1 for r in results if r["signal"] == "BEKLE"),
            "sell": sum(1 for r in results if r["signal"] == "SAT"),
            "strong_sell": sum(1 for r in results if r["signal"] == "GÜÇLÜ SAT")
        }
    }


@router.get("/model-info")
async def get_model_info():
    """Mevcut AI modelleri hakkında bilgi"""
    
    return {
        "models": {
            "linear": {
                "name": "Linear Regression",
                "description": "Basit doğrusal regresyon modeli",
                "speed": "Çok Hızlı",
                "accuracy": "Orta",
                "best_for": "Kısa vadeli, düşük volatiliteli hisseler"
            },
            "ensemble": {
                "name": "Ensemble (Topluluk)",
                "description": "Ridge, Random Forest ve Gradient Boosting kombinasyonu",
                "speed": "Hızlı",
                "accuracy": "Yüksek",
                "best_for": "Genel kullanım, dengeli tahminler"
            },
            "prophet": {
                "name": "Facebook Prophet",
                "description": "Zaman serisi tahmini için özel model",
                "speed": "Yavaş",
                "accuracy": "Yüksek",
                "best_for": "Mevsimsellik gösteren hisseler"
            }
        },
        "features_used": [
            "Hareketli Ortalamalar (MA5, MA10, MA20)",
            "RSI (Göreceli Güç Endeksi)",
            "Volatilite",
            "Momentum",
            "Gecikmeli Fiyatlar (Lag Features)"
        ],
        "disclaimer": "Bu tahminler yatırım tavsiyesi değildir. Tüm yatırım kararlarınızı kendi araştırmanıza dayanarak verin."
    }
