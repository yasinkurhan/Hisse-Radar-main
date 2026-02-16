"""
Kullanici Ozellikleri API Router
================================
Watchlist, Alert, Portfolio endpointleri
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..services.user_features import WatchlistService, AlertService, PortfolioService

router = APIRouter(prefix="/api/user", tags=["user"])

# Servisler
watchlist_service = WatchlistService()
alert_service = AlertService()
portfolio_service = PortfolioService()


# ==================== WATCHLIST ====================

class AddToWatchlistRequest(BaseModel):
    symbol: str
    list_id: str = "default"
    note: str = ""

class CreateWatchlistRequest(BaseModel):
    list_id: str
    name: str

@router.get("/watchlist")
async def get_watchlist(list_id: str = "default"):
    """Takip listesini getir"""
    return watchlist_service.get_watchlist(list_id)

@router.get("/watchlists")
async def get_all_watchlists():
    """Tum takip listelerini getir"""
    return watchlist_service.get_all_watchlists()

@router.post("/watchlist/add")
async def add_to_watchlist(request: AddToWatchlistRequest):
    """Hisseyi takip listesine ekle"""
    success = watchlist_service.add_to_watchlist(request.symbol, request.list_id, request.note)
    if success:
        return {"success": True, "message": f"{request.symbol} takip listesine eklendi"}
    return {"success": False, "message": "Hisse zaten listede"}

@router.post("/watchlist/remove")
async def remove_from_watchlist(symbol: str, list_id: str = "default"):
    """Hisseyi takip listesinden cikar"""
    success = watchlist_service.remove_from_watchlist(symbol, list_id)
    if success:
        return {"success": True, "message": f"{symbol} takip listesinden cikarildi"}
    return {"success": False, "message": "Hisse bulunamadi"}

@router.post("/watchlist/create")
async def create_watchlist(request: CreateWatchlistRequest):
    """Yeni takip listesi olustur"""
    success = watchlist_service.create_watchlist(request.list_id, request.name)
    if success:
        return {"success": True, "message": f"{request.name} olusturuldu"}
    return {"success": False, "message": "Liste zaten mevcut"}


# ==================== ALERTS ====================

class CreateAlertRequest(BaseModel):
    symbol: str
    alert_type: str  # price_above, price_below, signal_change, score_above, score_below
    condition: str = ""
    value: float = 0
    note: str = ""

@router.get("/alerts")
async def get_alerts():
    """Tum alarmlari getir"""
    return {
        "active": alert_service.get_active_alerts(),
        "triggered": alert_service.get_triggered_alerts(20)
    }

@router.post("/alerts/create")
async def create_alert(request: CreateAlertRequest):
    """Yeni alarm olustur"""
    alert = alert_service.create_alert(
        request.symbol, 
        request.alert_type, 
        request.condition, 
        request.value,
        request.note
    )
    return {"success": True, "alert": alert}

@router.post("/alerts/delete")
async def delete_alert(alert_id: str):
    """Alarmi sil"""
    success = alert_service.delete_alert(alert_id)
    return {"success": success}

@router.post("/alerts/reset")
async def reset_alert(alert_id: str):
    """Tetiklenmis alarmi sifirla"""
    success = alert_service.reset_alert(alert_id)
    return {"success": success}


# ==================== PORTFOLIO ====================

class BuyStockRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    portfolio_id: str = "default"

class SellStockRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    portfolio_id: str = "default"

@router.get("/portfolio")
async def get_portfolio(portfolio_id: str = "default"):
    """Portfoyu getir"""
    return portfolio_service.get_portfolio(portfolio_id)

@router.post("/portfolio/buy")
async def buy_stock(request: BuyStockRequest):
    """Hisse al"""
    result = portfolio_service.buy_stock(
        request.symbol,
        request.quantity,
        request.price,
        request.portfolio_id
    )
    return result

@router.post("/portfolio/sell")
async def sell_stock(request: SellStockRequest):
    """Hisse sat"""
    result = portfolio_service.sell_stock(
        request.symbol,
        request.quantity,
        request.price,
        request.portfolio_id
    )
    return result

@router.get("/portfolio/transactions")
async def get_transactions(portfolio_id: str = "default", limit: int = 50):
    """Islem gecmisini getir"""
    return portfolio_service.get_transactions(portfolio_id, limit)

@router.post("/portfolio/reset")
async def reset_portfolio(portfolio_id: str = "default", initial_capital: float = 100000):
    """Portfoyu sifirla"""
    success = portfolio_service.reset_portfolio(portfolio_id, initial_capital)
    return {"success": success}


# ==================== PUSH NOTIFICATIONS ====================

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict
    expirationTime: Optional[int] = None

# Push subscription'ları saklamak için basit in-memory storage (production'da DB kullanılmalı)
push_subscriptions: List[dict] = []

@router.post("/push-subscription")
async def save_push_subscription(request: PushSubscriptionRequest):
    """Push notification subscription kaydet"""
    subscription = {
        "endpoint": request.endpoint,
        "keys": request.keys,
        "expirationTime": request.expirationTime
    }
    
    # Aynı endpoint varsa güncelle
    for i, sub in enumerate(push_subscriptions):
        if sub["endpoint"] == request.endpoint:
            push_subscriptions[i] = subscription
            return {"success": True, "message": "Subscription güncellendi"}
    
    push_subscriptions.append(subscription)
    return {"success": True, "message": "Subscription kaydedildi"}

@router.delete("/push-subscription")
async def delete_push_subscription(endpoint: str):
    """Push notification subscription sil"""
    global push_subscriptions
    push_subscriptions = [s for s in push_subscriptions if s["endpoint"] != endpoint]
    return {"success": True}

@router.get("/push-subscriptions")
async def get_push_subscriptions():
    """Tüm push subscription'ları getir (admin için)"""
    return {"count": len(push_subscriptions), "subscriptions": push_subscriptions}

