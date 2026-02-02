"""
SQLite Veritabanı Servisi
=========================
Uygulama verilerini kalıcı olarak saklamak için SQLite veritabanı
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading

# Veritabanı dosya yolu
DB_PATH = Path(__file__).parent.parent / "data" / "hisseradar.db"


class DatabaseService:
    """SQLite veritabanı yönetimi"""
    
    _local = threading.local()
    
    def __init__(self):
        self._ensure_db_exists()
        self._init_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Thread-safe bağlantı al"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _ensure_db_exists(self):
        """Veritabanı dosyasının varlığını kontrol et"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_tables(self):
        """Tabloları oluştur"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Kullanıcılar tablosu (gelecekte auth için)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                settings TEXT DEFAULT '{}'
            )
        ''')
        
        # Varsayılan kullanıcı oluştur
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email) VALUES (1, 'default', 'user@hisseradar.com')
        ''')
        
        # Takip listeleri tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                list_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, list_id)
            )
        ''')
        
        # Takip listesi hisseleri
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watchlist_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                note TEXT DEFAULT '',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id),
                UNIQUE(watchlist_id, symbol)
            )
        ''')
        
        # Portföyler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                portfolio_id TEXT NOT NULL,
                name TEXT NOT NULL,
                initial_capital REAL DEFAULT 100000,
                current_cash REAL DEFAULT 100000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, portfolio_id)
            )
        ''')
        
        # Portföy pozisyonları
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                average_cost REAL NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                UNIQUE(portfolio_id, symbol)
            )
        ''')
        
        # İşlem geçmişi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        ''')
        
        # Fiyat alarmları
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                target_price REAL NOT NULL,
                note TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                triggered_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Fiyat cache tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_cache (
                symbol TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # AI tahmin geçmişi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                prediction_date DATE NOT NULL,
                predicted_price REAL NOT NULL,
                actual_price REAL,
                confidence_score INTEGER,
                model_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, prediction_date)
            )
        ''')
        
        # Hisse temel verileri cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fundamental_cache (
                symbol TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
    
    # ==================== WATCHLIST ====================
    
    def get_or_create_watchlist(self, list_id: str, user_id: int = 1) -> int:
        """Takip listesi al veya oluştur"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM watchlists WHERE user_id = ? AND list_id = ?
        ''', (user_id, list_id))
        
        result = cursor.fetchone()
        if result:
            return result['id']
        
        cursor.execute('''
            INSERT INTO watchlists (user_id, list_id, name) VALUES (?, ?, ?)
        ''', (user_id, list_id, list_id.replace('_', ' ').title()))
        conn.commit()
        
        return cursor.lastrowid
    
    def add_to_watchlist(self, symbol: str, list_id: str = "default", note: str = "") -> bool:
        """Hisseyi takip listesine ekle"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        watchlist_id = self.get_or_create_watchlist(list_id)
        
        try:
            cursor.execute('''
                INSERT INTO watchlist_stocks (watchlist_id, symbol, note)
                VALUES (?, ?, ?)
            ''', (watchlist_id, symbol.upper(), note))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_from_watchlist(self, symbol: str, list_id: str = "default") -> bool:
        """Hisseyi takip listesinden çıkar"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        watchlist_id = self.get_or_create_watchlist(list_id)
        
        cursor.execute('''
            DELETE FROM watchlist_stocks WHERE watchlist_id = ? AND symbol = ?
        ''', (watchlist_id, symbol.upper()))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def get_watchlist(self, list_id: str = "default") -> Dict:
        """Takip listesini getir"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        watchlist_id = self.get_or_create_watchlist(list_id)
        
        cursor.execute('''
            SELECT w.name, ws.symbol, ws.note, ws.added_at
            FROM watchlists w
            LEFT JOIN watchlist_stocks ws ON w.id = ws.watchlist_id
            WHERE w.id = ?
        ''', (watchlist_id,))
        
        rows = cursor.fetchall()
        
        if not rows or rows[0]['symbol'] is None:
            return {"list_id": list_id, "name": list_id.title(), "stocks": []}
        
        return {
            "list_id": list_id,
            "name": rows[0]['name'],
            "stocks": [
                {
                    "symbol": row['symbol'],
                    "note": row['note'],
                    "added_at": row['added_at']
                }
                for row in rows if row['symbol']
            ]
        }
    
    # ==================== PORTFOLIO ====================
    
    def get_or_create_portfolio(self, portfolio_id: str, user_id: int = 1, initial_capital: float = 100000) -> int:
        """Portföy al veya oluştur"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM portfolios WHERE user_id = ? AND portfolio_id = ?
        ''', (user_id, portfolio_id))
        
        result = cursor.fetchone()
        if result:
            return result['id']
        
        cursor.execute('''
            INSERT INTO portfolios (user_id, portfolio_id, name, initial_capital, current_cash)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, portfolio_id, portfolio_id.replace('_', ' ').title(), initial_capital, initial_capital))
        conn.commit()
        
        return cursor.lastrowid
    
    def get_portfolio(self, portfolio_id: str = "default") -> Dict:
        """Portföy bilgilerini getir"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        db_portfolio_id = self.get_or_create_portfolio(portfolio_id)
        
        # Portföy bilgisi
        cursor.execute('''
            SELECT * FROM portfolios WHERE id = ?
        ''', (db_portfolio_id,))
        portfolio = cursor.fetchone()
        
        # Pozisyonlar
        cursor.execute('''
            SELECT symbol, quantity, average_cost FROM portfolio_positions WHERE portfolio_id = ?
        ''', (db_portfolio_id,))
        positions = cursor.fetchall()
        
        return {
            "portfolio_id": portfolio_id,
            "name": portfolio['name'],
            "initial_capital": portfolio['initial_capital'],
            "current_cash": portfolio['current_cash'],
            "positions": [
                {
                    "symbol": pos['symbol'],
                    "quantity": pos['quantity'],
                    "average_cost": pos['average_cost']
                }
                for pos in positions
            ]
        }
    
    def buy_stock(self, symbol: str, quantity: float, price: float, portfolio_id: str = "default") -> Dict:
        """Hisse satın al"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        db_portfolio_id = self.get_or_create_portfolio(portfolio_id)
        total_cost = quantity * price
        
        # Nakit kontrolü
        cursor.execute('SELECT current_cash FROM portfolios WHERE id = ?', (db_portfolio_id,))
        cash = cursor.fetchone()['current_cash']
        
        if cash < total_cost:
            return {"success": False, "error": "Yetersiz bakiye"}
        
        # Nakiti güncelle
        cursor.execute('''
            UPDATE portfolios SET current_cash = current_cash - ? WHERE id = ?
        ''', (total_cost, db_portfolio_id))
        
        # Pozisyon güncelle veya ekle
        cursor.execute('''
            SELECT quantity, average_cost FROM portfolio_positions 
            WHERE portfolio_id = ? AND symbol = ?
        ''', (db_portfolio_id, symbol.upper()))
        
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing['quantity'] + quantity
            new_avg_cost = (existing['quantity'] * existing['average_cost'] + total_cost) / new_quantity
            cursor.execute('''
                UPDATE portfolio_positions SET quantity = ?, average_cost = ?
                WHERE portfolio_id = ? AND symbol = ?
            ''', (new_quantity, new_avg_cost, db_portfolio_id, symbol.upper()))
        else:
            cursor.execute('''
                INSERT INTO portfolio_positions (portfolio_id, symbol, quantity, average_cost)
                VALUES (?, ?, ?, ?)
            ''', (db_portfolio_id, symbol.upper(), quantity, price))
        
        # İşlem kaydı
        cursor.execute('''
            INSERT INTO transactions (portfolio_id, symbol, transaction_type, quantity, price, total_value)
            VALUES (?, ?, 'BUY', ?, ?, ?)
        ''', (db_portfolio_id, symbol.upper(), quantity, price, total_cost))
        
        conn.commit()
        
        return {"success": True, "message": f"{quantity} adet {symbol} alındı"}
    
    def sell_stock(self, symbol: str, quantity: float, price: float, portfolio_id: str = "default") -> Dict:
        """Hisse sat"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        db_portfolio_id = self.get_or_create_portfolio(portfolio_id)
        
        # Pozisyon kontrolü
        cursor.execute('''
            SELECT quantity, average_cost FROM portfolio_positions 
            WHERE portfolio_id = ? AND symbol = ?
        ''', (db_portfolio_id, symbol.upper()))
        
        existing = cursor.fetchone()
        
        if not existing or existing['quantity'] < quantity:
            return {"success": False, "error": "Yetersiz hisse"}
        
        total_value = quantity * price
        
        # Nakiti güncelle
        cursor.execute('''
            UPDATE portfolios SET current_cash = current_cash + ? WHERE id = ?
        ''', (total_value, db_portfolio_id))
        
        # Pozisyon güncelle
        new_quantity = existing['quantity'] - quantity
        if new_quantity > 0:
            cursor.execute('''
                UPDATE portfolio_positions SET quantity = ?
                WHERE portfolio_id = ? AND symbol = ?
            ''', (new_quantity, db_portfolio_id, symbol.upper()))
        else:
            cursor.execute('''
                DELETE FROM portfolio_positions WHERE portfolio_id = ? AND symbol = ?
            ''', (db_portfolio_id, symbol.upper()))
        
        # İşlem kaydı
        profit = (price - existing['average_cost']) * quantity
        cursor.execute('''
            INSERT INTO transactions (portfolio_id, symbol, transaction_type, quantity, price, total_value)
            VALUES (?, ?, 'SELL', ?, ?, ?)
        ''', (db_portfolio_id, symbol.upper(), quantity, price, total_value))
        
        conn.commit()
        
        return {"success": True, "message": f"{quantity} adet {symbol} satıldı", "profit": round(profit, 2)}
    
    # ==================== ALERTS ====================
    
    def add_alert(self, symbol: str, alert_type: str, target_price: float, note: str = "") -> int:
        """Fiyat alarmı ekle"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (symbol, alert_type, target_price, note)
            VALUES (?, ?, ?, ?)
        ''', (symbol.upper(), alert_type, target_price, note))
        conn.commit()
        
        return cursor.lastrowid
    
    def get_active_alerts(self, symbol: str = None) -> List[Dict]:
        """Aktif alarmları getir"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('''
                SELECT * FROM alerts WHERE is_active = 1 AND symbol = ?
            ''', (symbol.upper(),))
        else:
            cursor.execute('SELECT * FROM alerts WHERE is_active = 1')
        
        return [dict(row) for row in cursor.fetchall()]
    
    def trigger_alert(self, alert_id: int):
        """Alarmı tetiklenmiş olarak işaretle"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alerts SET is_active = 0, triggered_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (alert_id,))
        conn.commit()
    
    # ==================== CACHE ====================
    
    def set_price_cache(self, symbol: str, data: Dict):
        """Fiyat verisini cache'e kaydet"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO price_cache (symbol, data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (symbol.upper(), json.dumps(data)))
        conn.commit()
    
    def get_price_cache(self, symbol: str, max_age_seconds: int = 300) -> Optional[Dict]:
        """Cache'den fiyat verisi al"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data, updated_at FROM price_cache 
            WHERE symbol = ? AND updated_at > datetime('now', ?)
        ''', (symbol.upper(), f'-{max_age_seconds} seconds'))
        
        result = cursor.fetchone()
        if result:
            return json.loads(result['data'])
        return None
    
    def set_fundamental_cache(self, symbol: str, data: Dict):
        """Temel veriyi cache'e kaydet"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO fundamental_cache (symbol, data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (symbol.upper(), json.dumps(data)))
        conn.commit()
    
    def get_fundamental_cache(self, symbol: str, max_age_seconds: int = 3600) -> Optional[Dict]:
        """Cache'den temel veri al"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data, updated_at FROM fundamental_cache 
            WHERE symbol = ? AND updated_at > datetime('now', ?)
        ''', (symbol.upper(), f'-{max_age_seconds} seconds'))
        
        result = cursor.fetchone()
        if result:
            return json.loads(result['data'])
        return None
    
    # ==================== AI PREDICTIONS ====================
    
    def save_prediction(self, symbol: str, prediction_date: str, predicted_price: float, 
                       confidence_score: int, model_type: str):
        """AI tahminini kaydet"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO ai_predictions 
            (symbol, prediction_date, predicted_price, confidence_score, model_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol.upper(), prediction_date, predicted_price, confidence_score, model_type))
        conn.commit()
    
    def update_actual_price(self, symbol: str, prediction_date: str, actual_price: float):
        """Gerçekleşen fiyatı güncelle (model doğruluğu için)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ai_predictions SET actual_price = ?
            WHERE symbol = ? AND prediction_date = ?
        ''', (actual_price, symbol.upper(), prediction_date))
        conn.commit()
    
    def get_prediction_accuracy(self, symbol: str = None) -> Dict:
        """Tahmin doğruluğunu hesapla"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT symbol, predicted_price, actual_price,
                   ABS(predicted_price - actual_price) / actual_price * 100 as error_pct
            FROM ai_predictions 
            WHERE actual_price IS NOT NULL
        '''
        
        if symbol:
            query += ' AND symbol = ?'
            cursor.execute(query, (symbol.upper(),))
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        if not results:
            return {"accuracy": None, "samples": 0}
        
        avg_error = sum(row['error_pct'] for row in results) / len(results)
        
        return {
            "accuracy": round(100 - avg_error, 2),
            "avg_error_percent": round(avg_error, 2),
            "samples": len(results)
        }


# Singleton instance
db_service = DatabaseService()
