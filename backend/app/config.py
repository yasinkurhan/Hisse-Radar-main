"""
HisseRadar Yapılandırma Dosyası
===============================
Uygulama genelinde kullanılan sabitler ve ayarlar
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # API Ayarları
    APP_NAME: str = "HisseRadar API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "BIST Hisse Analiz Platformu"
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
    
    # yfinance Ayarları
    YFINANCE_SUFFIX: str = ".IS"  # BIST hisseleri için suffix
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Ayarları cache'li olarak döndür"""
    return Settings()


# Sabit değerler
BIST_SUFFIX = ".IS"

# Zaman dilimleri
PERIODS = {
    "1d": "1 Gün",
    "5d": "5 Gün",
    "1mo": "1 Ay",
    "3mo": "3 Ay",
    "6mo": "6 Ay",
    "1y": "1 Yıl",
    "2y": "2 Yıl",
    "5y": "5 Yıl",
    "max": "Tümü"
}

# Aralıklar
INTERVALS = {
    "1m": "1 Dakika",
    "5m": "5 Dakika",
    "15m": "15 Dakika",
    "30m": "30 Dakika",
    "1h": "1 Saat",
    "1d": "1 Gün",
    "1wk": "1 Hafta",
    "1mo": "1 Ay"
}
