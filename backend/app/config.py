"""
HisseRadar Yapılandırma Dosyası
===============================
Uygulama genelinde kullanılan sabitler ve ayarlar
Veri Kaynağı: borsapy (İş Yatırım, TradingView, KAP, TCMB)
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # API Ayarları
    APP_NAME: str = "HisseRadar API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "BIST Hisse Analiz Platformu - borsapy ile güçlendirildi"
    DEBUG: bool = True
    
    # CORS Ayarları - Frontend'in bağlanabilmesi için
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://hisseradar.vercel.app"
    ]
    
    # Cache Ayarları (saniye cinsinden)
    CACHE_TTL_PRICE: int = 300      # 5 dakika - fiyat verileri
    CACHE_TTL_FUNDAMENTAL: int = 3600  # 1 saat - temel analiz
    CACHE_TTL_STOCK_LIST: int = 86400  # 24 saat - hisse listesi
    
    # borsapy Ayarları
    DATA_SOURCE: str = "borsapy"  # Veri kaynağı: borsapy
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Ayarları cache'li olarak döndür"""
    return Settings()


# ==========================================
# Period Mapping (uygulama period → borsapy)
# ==========================================
PERIOD_MAP = {
    "1d": "1g",
    "5d": "5g",
    "1mo": "1ay",
    "3mo": "3ay",
    "6mo": "6ay",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    "max": "max",
}

# Zaman dilimleri (borsapy formatında)
PERIODS = {
    "1g": "1 Gün",
    "5g": "5 Gün",
    "1ay": "1 Ay",
    "3ay": "3 Ay",
    "6ay": "6 Ay",
    "1y": "1 Yıl",
    "2y": "2 Yıl",
    "5y": "5 Yıl",
    "max": "Tümü",
    # Geriye uyumluluk
    "1d": "1 Gün",
    "5d": "5 Gün",
    "1mo": "1 Ay",
    "3mo": "3 Ay",
    "6mo": "6 Ay",
}

# Aralıklar
INTERVALS = {
    "1m": "1 Dakika",
    "5m": "5 Dakika",
    "15m": "15 Dakika",
    "30m": "30 Dakika",
    "1h": "1 Saat",
    "1d": "1 Gün",
}


def normalize_period(period: str) -> str:
    """Period değerini borsapy formatına çevir"""
    return PERIOD_MAP.get(period, period)


def normalize_symbol(symbol: str) -> str:
    """Sembolü temizle (.IS suffix'ini kaldır)"""
    return symbol.upper().strip().replace(".IS", "")
