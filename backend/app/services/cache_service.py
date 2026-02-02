"""
Cache Servisi
=============
In-memory ve disk cache sistemi
Redis benzeri işlevsellik (Redis opsiyonel)
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable
from functools import wraps
import threading
from pathlib import Path

# Redis opsiyonel import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class InMemoryCache:
    """Basit in-memory cache"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            if item['expires_at'] < time.time():
                del self._cache[key]
                return None
            
            return item['value']
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Cache'e veri kaydet"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + (ttl or self.default_ttl),
                'created_at': time.time()
            }
            return True
    
    def delete(self, key: str) -> bool:
        """Cache'den veri sil"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> int:
        """Tüm cache'i temizle"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    def cleanup(self) -> int:
        """Süresi dolmuş verileri temizle"""
        with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._cache.items() if v['expires_at'] < now]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Cache istatistikleri"""
        with self._lock:
            now = time.time()
            active = sum(1 for v in self._cache.values() if v['expires_at'] >= now)
            return {
                'total_keys': len(self._cache),
                'active_keys': active,
                'expired_keys': len(self._cache) - active
            }


class CacheService:
    """Ana cache servisi - Redis veya In-Memory"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = None
        self.memory_cache = InMemoryCache()
        
        # Redis bağlantısı dene
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                print("[Cache] Redis bağlantısı başarılı")
            except Exception as e:
                print(f"[Cache] Redis bağlantısı başarısız, in-memory kullanılıyor: {e}")
                self.redis_client = None
    
    @property
    def is_redis(self) -> bool:
        return self.redis_client is not None
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den veri al"""
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except:
                pass
        
        return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Cache'e veri kaydet"""
        if self.redis_client:
            try:
                return self.redis_client.setex(key, ttl, json.dumps(value))
            except:
                pass
        
        return self.memory_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Cache'den veri sil"""
        if self.redis_client:
            try:
                return self.redis_client.delete(key) > 0
            except:
                pass
        
        return self.memory_cache.delete(key)
    
    def get_or_set(self, key: str, factory: Callable, ttl: int = 300) -> Any:
        """Cache'de varsa al, yoksa üret ve kaydet"""
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def clear_pattern(self, pattern: str) -> int:
        """Pattern'e uyan keyleri sil"""
        count = 0
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            except:
                pass
        
        # In-memory için basit pattern matching
        keys_to_delete = [k for k in list(self.memory_cache._cache.keys()) 
                        if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            self.memory_cache.delete(key)
            count += 1
        
        return count


# Decorator for caching function results
def cached(ttl: int = 300, key_prefix: str = None):
    """Cache decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache key oluştur
            prefix = key_prefix or func.__name__
            key_parts = [prefix] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Cache'den al
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Hesapla ve cache'e kaydet
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Async decorator for caching
def async_cached(ttl: int = 300, key_prefix: str = None):
    """Async cache decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            key_parts = [prefix] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Price-specific cache helpers
class PriceCache:
    """Fiyat verileri için özel cache"""
    
    PREFIX = "price:"
    DEFAULT_TTL = 60  # 1 dakika
    
    @classmethod
    def get_price(cls, symbol: str) -> Optional[Dict]:
        return cache_service.get(f"{cls.PREFIX}{symbol.upper()}")
    
    @classmethod
    def set_price(cls, symbol: str, data: Dict, ttl: int = None):
        cache_service.set(f"{cls.PREFIX}{symbol.upper()}", data, ttl or cls.DEFAULT_TTL)
    
    @classmethod
    def get_batch(cls, symbols: list) -> Dict[str, Optional[Dict]]:
        return {s: cls.get_price(s) for s in symbols}
    
    @classmethod
    def set_batch(cls, data: Dict[str, Dict], ttl: int = None):
        for symbol, price_data in data.items():
            cls.set_price(symbol, price_data, ttl)


# Analysis cache helpers
class AnalysisCache:
    """Analiz sonuçları için cache"""
    
    PREFIX = "analysis:"
    DEFAULT_TTL = 300  # 5 dakika
    
    @classmethod
    def get_analysis(cls, symbol: str) -> Optional[Dict]:
        return cache_service.get(f"{cls.PREFIX}{symbol.upper()}")
    
    @classmethod
    def set_analysis(cls, symbol: str, data: Dict, ttl: int = None):
        cache_service.set(f"{cls.PREFIX}{symbol.upper()}", data, ttl or cls.DEFAULT_TTL)
    
    @classmethod
    def invalidate(cls, symbol: str):
        cache_service.delete(f"{cls.PREFIX}{symbol.upper()}")


# AI Prediction cache
class PredictionCache:
    """AI tahmin sonuçları için cache"""
    
    PREFIX = "prediction:"
    DEFAULT_TTL = 3600  # 1 saat
    
    @classmethod
    def get_prediction(cls, symbol: str) -> Optional[Dict]:
        return cache_service.get(f"{cls.PREFIX}{symbol.upper()}")
    
    @classmethod
    def set_prediction(cls, symbol: str, data: Dict, ttl: int = None):
        cache_service.set(f"{cls.PREFIX}{symbol.upper()}", data, ttl or cls.DEFAULT_TTL)


# Fundamental data cache
class FundamentalCache:
    """Temel analiz verileri için cache"""
    
    PREFIX = "fundamental:"
    DEFAULT_TTL = 86400  # 24 saat (temel veriler sık değişmez)
    
    @classmethod
    def get_fundamental(cls, symbol: str) -> Optional[Dict]:
        return cache_service.get(f"{cls.PREFIX}{symbol.upper()}")
    
    @classmethod
    def set_fundamental(cls, symbol: str, data: Dict, ttl: int = None):
        cache_service.set(f"{cls.PREFIX}{symbol.upper()}", data, ttl or cls.DEFAULT_TTL)


# Singleton instance
cache_service = CacheService()
