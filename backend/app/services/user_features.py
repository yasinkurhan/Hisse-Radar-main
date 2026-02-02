"""
Kullanici Ozellikleri - Watchlist, Alarm, Portfoy
=================================================
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class WatchlistService:
    """Kullanici takip listesi yonetimi"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(Path(__file__).parent.parent / "data" / "watchlists.json")
        self._data = self._load_data()
    
    def _load_data(self) -> Dict:
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"default": {"name": "Takip Listem", "stocks": [], "created": datetime.now().isoformat()}}
    
    def _save_data(self):
        try:
            Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Watchlist kayit hatasi: {e}")
    
    def get_watchlist(self, list_id: str = "default") -> Dict[str, Any]:
        """Takip listesini getir"""
        return self._data.get(list_id, {"stocks": []})
    
    def get_all_watchlists(self) -> Dict[str, Any]:
        """Tum takip listelerini getir"""
        return self._data
    
    def add_to_watchlist(self, symbol: str, list_id: str = "default", note: str = "") -> bool:
        """Hisseyi takip listesine ekle"""
        if list_id not in self._data:
            self._data[list_id] = {"name": list_id, "stocks": [], "created": datetime.now().isoformat()}
        
        # Zaten varsa ekleme
        existing = [s for s in self._data[list_id]["stocks"] if s["symbol"] == symbol]
        if existing:
            return False
        
        self._data[list_id]["stocks"].append({
            "symbol": symbol,
            "added_date": datetime.now().isoformat(),
            "added_price": None,  # Frontend'den gelecek
            "note": note,
            "alerts": []
        })
        self._save_data()
        return True
    
    def remove_from_watchlist(self, symbol: str, list_id: str = "default") -> bool:
        """Hisseyi takip listesinden cikar"""
        if list_id not in self._data:
            return False
        
        original_len = len(self._data[list_id]["stocks"])
        self._data[list_id]["stocks"] = [s for s in self._data[list_id]["stocks"] if s["symbol"] != symbol]
        
        if len(self._data[list_id]["stocks"]) < original_len:
            self._save_data()
            return True
        return False
    
    def update_stock_note(self, symbol: str, note: str, list_id: str = "default") -> bool:
        """Hisse notunu guncelle"""
        if list_id not in self._data:
            return False
        
        for stock in self._data[list_id]["stocks"]:
            if stock["symbol"] == symbol:
                stock["note"] = note
                stock["updated"] = datetime.now().isoformat()
                self._save_data()
                return True
        return False
    
    def create_watchlist(self, list_id: str, name: str) -> bool:
        """Yeni takip listesi olustur"""
        if list_id in self._data:
            return False
        
        self._data[list_id] = {
            "name": name,
            "stocks": [],
            "created": datetime.now().isoformat()
        }
        self._save_data()
        return True
    
    def delete_watchlist(self, list_id: str) -> bool:
        """Takip listesini sil"""
        if list_id == "default" or list_id not in self._data:
            return False
        
        del self._data[list_id]
        self._save_data()
        return True


class AlertService:
    """Fiyat ve sinyal alarmlari"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(Path(__file__).parent.parent / "data" / "alerts.json")
        self._alerts = self._load_alerts()
    
    def _load_alerts(self) -> List[Dict]:
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def _save_alerts(self):
        try:
            Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self._alerts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Alert kayit hatasi: {e}")
    
    def create_alert(self, symbol: str, alert_type: str, condition: str, value: float, note: str = "") -> Dict:
        """
        Yeni alarm olustur
        alert_type: 'price_above', 'price_below', 'signal_change', 'score_above', 'score_below'
        """
        alert = {
            "id": f"{symbol}_{alert_type}_{datetime.now().timestamp()}",
            "symbol": symbol,
            "alert_type": alert_type,
            "condition": condition,
            "value": value,
            "note": note,
            "created": datetime.now().isoformat(),
            "status": "active",
            "triggered": False,
            "triggered_at": None
        }
        self._alerts.append(alert)
        self._save_alerts()
        return alert
    
    def check_alerts(self, current_data: Dict[str, Dict]) -> List[Dict]:
        """
        Alarmlari kontrol et
        current_data: {symbol: {"price": x, "signal": y, "score": z}}
        """
        triggered = []
        
        for alert in self._alerts:
            if alert["status"] != "active":
                continue
            
            symbol = alert["symbol"]
            if symbol not in current_data:
                continue
            
            data = current_data[symbol]
            should_trigger = False
            message = ""
            
            if alert["alert_type"] == "price_above":
                if data.get("price", 0) >= alert["value"]:
                    should_trigger = True
                    message = f"{symbol} fiyati {alert['value']} TL uzerine cikti: {data['price']} TL"
            
            elif alert["alert_type"] == "price_below":
                if data.get("price", 0) <= alert["value"]:
                    should_trigger = True
                    message = f"{symbol} fiyati {alert['value']} TL altina dustu: {data['price']} TL"
            
            elif alert["alert_type"] == "score_above":
                if data.get("score", 0) >= alert["value"]:
                    should_trigger = True
                    message = f"{symbol} skoru {alert['value']} uzerine cikti: {data['score']}"
            
            elif alert["alert_type"] == "score_below":
                if data.get("score", 0) <= alert["value"]:
                    should_trigger = True
                    message = f"{symbol} skoru {alert['value']} altina dustu: {data['score']}"
            
            elif alert["alert_type"] == "signal_change":
                if data.get("signal") in ["GUCLU_AL", "AL"] and alert["condition"] == "buy":
                    should_trigger = True
                    message = f"{symbol} AL sinyali verdi!"
                elif data.get("signal") in ["GUCLU_SAT", "SAT"] and alert["condition"] == "sell":
                    should_trigger = True
                    message = f"{symbol} SAT sinyali verdi!"
            
            if should_trigger:
                alert["triggered"] = True
                alert["triggered_at"] = datetime.now().isoformat()
                alert["status"] = "triggered"
                triggered.append({
                    "alert": alert,
                    "message": message,
                    "data": data
                })
        
        if triggered:
            self._save_alerts()
        
        return triggered
    
    def get_active_alerts(self) -> List[Dict]:
        """Aktif alarmlari getir"""
        return [a for a in self._alerts if a["status"] == "active"]
    
    def get_triggered_alerts(self, limit: int = 50) -> List[Dict]:
        """Tetiklenmis alarmlari getir"""
        triggered = [a for a in self._alerts if a["status"] == "triggered"]
        triggered.sort(key=lambda x: x.get("triggered_at", ""), reverse=True)
        return triggered[:limit]
    
    def delete_alert(self, alert_id: str) -> bool:
        """Alarmi sil"""
        original_len = len(self._alerts)
        self._alerts = [a for a in self._alerts if a["id"] != alert_id]
        
        if len(self._alerts) < original_len:
            self._save_alerts()
            return True
        return False
    
    def reset_alert(self, alert_id: str) -> bool:
        """Tetiklenmis alarmi sifirla"""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["status"] = "active"
                alert["triggered"] = False
                alert["triggered_at"] = None
                self._save_alerts()
                return True
        return False


class PortfolioService:
    """Sanal portfoy yonetimi"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(Path(__file__).parent.parent / "data" / "portfolios.json")
        self._data = self._load_data()
    
    def _load_data(self) -> Dict:
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {
                "default": {
                    "name": "Ana Portfoy",
                    "initial_capital": 100000,
                    "cash": 100000,
                    "positions": [],
                    "transactions": [],
                    "created": datetime.now().isoformat()
                }
            }
    
    def _save_data(self):
        try:
            Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Portfolio kayit hatasi: {e}")
    
    def get_portfolio(self, portfolio_id: str = "default") -> Dict[str, Any]:
        """Portfoyu getir"""
        return self._data.get(portfolio_id, {})
    
    def buy_stock(self, symbol: str, quantity: int, price: float, portfolio_id: str = "default") -> Dict[str, Any]:
        """Hisse al"""
        if portfolio_id not in self._data:
            return {"success": False, "error": "Portfoy bulunamadi"}
        
        portfolio = self._data[portfolio_id]
        total_cost = quantity * price
        
        if portfolio["cash"] < total_cost:
            return {"success": False, "error": "Yetersiz bakiye"}
        
        # Nakit dusur
        portfolio["cash"] -= total_cost
        
        # Pozisyon guncelle veya ekle
        existing = next((p for p in portfolio["positions"] if p["symbol"] == symbol), None)
        
        if existing:
            # Ortalama maliyet hesapla
            total_qty = existing["quantity"] + quantity
            total_value = (existing["quantity"] * existing["avg_cost"]) + total_cost
            existing["avg_cost"] = total_value / total_qty
            existing["quantity"] = total_qty
        else:
            portfolio["positions"].append({
                "symbol": symbol,
                "quantity": quantity,
                "avg_cost": price,
                "first_buy": datetime.now().isoformat()
            })
        
        # Islem kaydet
        portfolio["transactions"].append({
            "type": "buy",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total": total_cost,
            "date": datetime.now().isoformat()
        })
        
        self._save_data()
        return {"success": True, "message": f"{symbol} {quantity} adet {price} TL'den alindi"}
    
    def sell_stock(self, symbol: str, quantity: int, price: float, portfolio_id: str = "default") -> Dict[str, Any]:
        """Hisse sat"""
        if portfolio_id not in self._data:
            return {"success": False, "error": "Portfoy bulunamadi"}
        
        portfolio = self._data[portfolio_id]
        position = next((p for p in portfolio["positions"] if p["symbol"] == symbol), None)
        
        if not position:
            return {"success": False, "error": "Pozisyon bulunamadi"}
        
        if position["quantity"] < quantity:
            return {"success": False, "error": "Yetersiz miktar"}
        
        total_revenue = quantity * price
        profit = (price - position["avg_cost"]) * quantity
        
        # Nakit artir
        portfolio["cash"] += total_revenue
        
        # Pozisyon guncelle
        position["quantity"] -= quantity
        
        # Pozisyon bittiyse sil
        if position["quantity"] == 0:
            portfolio["positions"] = [p for p in portfolio["positions"] if p["symbol"] != symbol]
        
        # Islem kaydet
        portfolio["transactions"].append({
            "type": "sell",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total": total_revenue,
            "profit": round(profit, 2),
            "date": datetime.now().isoformat()
        })
        
        self._save_data()
        return {"success": True, "message": f"{symbol} {quantity} adet {price} TL'den satildi. Kar/Zarar: {profit:.2f} TL"}
    
    def get_portfolio_value(self, current_prices: Dict[str, float], portfolio_id: str = "default") -> Dict[str, Any]:
        """Portfoy degerini hesapla"""
        if portfolio_id not in self._data:
            return {"error": "Portfoy bulunamadi"}
        
        portfolio = self._data[portfolio_id]
        
        positions_value = 0
        positions_detail = []
        total_profit = 0
        
        for pos in portfolio["positions"]:
            symbol = pos["symbol"]
            current_price = current_prices.get(symbol, pos["avg_cost"])
            market_value = pos["quantity"] * current_price
            cost_basis = pos["quantity"] * pos["avg_cost"]
            profit = market_value - cost_basis
            profit_pct = (profit / cost_basis * 100) if cost_basis > 0 else 0
            
            positions_value += market_value
            total_profit += profit
            
            positions_detail.append({
                "symbol": symbol,
                "quantity": pos["quantity"],
                "avg_cost": round(pos["avg_cost"], 2),
                "current_price": round(current_price, 2),
                "market_value": round(market_value, 2),
                "profit": round(profit, 2),
                "profit_pct": round(profit_pct, 2)
            })
        
        total_value = portfolio["cash"] + positions_value
        total_return = total_value - portfolio["initial_capital"]
        total_return_pct = (total_return / portfolio["initial_capital"] * 100)
        
        return {
            "portfolio_id": portfolio_id,
            "name": portfolio["name"],
            "cash": round(portfolio["cash"], 2),
            "positions_value": round(positions_value, 2),
            "total_value": round(total_value, 2),
            "initial_capital": portfolio["initial_capital"],
            "total_return": round(total_return, 2),
            "total_return_pct": round(total_return_pct, 2),
            "positions": positions_detail,
            "position_count": len(portfolio["positions"])
        }
    
    def get_transactions(self, portfolio_id: str = "default", limit: int = 50) -> List[Dict]:
        """Islem gecmisini getir"""
        if portfolio_id not in self._data:
            return []
        
        transactions = self._data[portfolio_id].get("transactions", [])
        transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
        return transactions[:limit]
    
    def reset_portfolio(self, portfolio_id: str = "default", initial_capital: float = 100000) -> bool:
        """Portfoyu sifirla"""
        if portfolio_id not in self._data:
            return False
        
        self._data[portfolio_id] = {
            "name": self._data[portfolio_id].get("name", "Portfoy"),
            "initial_capital": initial_capital,
            "cash": initial_capital,
            "positions": [],
            "transactions": [],
            "created": datetime.now().isoformat()
        }
        self._save_data()
        return True
