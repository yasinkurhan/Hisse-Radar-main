"""
HisseRadar Pydantic Şemaları
============================
API istekleri ve yanıtları için veri modelleri
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==========================================
# HISSE MODELLERI
# ==========================================

class StockBase(BaseModel):
    """Temel hisse bilgisi"""
    symbol: str = Field(..., description="Hisse sembolü (örn: THYAO)")
    name: str = Field(..., description="Şirket adı")
    sector: Optional[str] = Field(None, description="Sektör")


class StockInfo(StockBase):
    """Detaylı hisse bilgisi"""
    current_price: Optional[float] = Field(None, description="Güncel fiyat")
    change_percent: Optional[float] = Field(None, description="Değişim yüzdesi")
    volume: Optional[int] = Field(None, description="İşlem hacmi")
    market_cap: Optional[float] = Field(None, description="Piyasa değeri")


class StockListResponse(BaseModel):
    """Hisse listesi yanıtı"""
    stocks: List[StockInfo]
    total: int
    updated_at: datetime


# ==========================================
# FİYAT VERİLERİ MODELLERİ
# ==========================================

class OHLCV(BaseModel):
    """Tek bir fiyat verisi (Open, High, Low, Close, Volume)"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceDataResponse(BaseModel):
    """Fiyat verileri yanıtı"""
    symbol: str
    period: str
    interval: str
    data: List[OHLCV]
    currency: str = "TRY"


# ==========================================
# TEKNİK ANALİZ MODELLERİ
# ==========================================

class RSIData(BaseModel):
    """RSI göstergesi"""
    timestamp: datetime
    value: float
    signal: str = Field(..., description="Aşırı alım/satım sinyali")


class MACDData(BaseModel):
    """MACD göstergesi"""
    timestamp: datetime
    macd: float
    signal: float
    histogram: float


class BollingerData(BaseModel):
    """Bollinger Bands"""
    timestamp: datetime
    upper: float
    middle: float
    lower: float


class MovingAverageData(BaseModel):
    """Hareketli ortalamalar"""
    timestamp: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None


class TechnicalIndicatorsResponse(BaseModel):
    """Teknik analiz yanıtı"""
    symbol: str
    period: str
    rsi: List[Dict[str, Any]]
    macd: List[Dict[str, Any]]
    bollinger: List[Dict[str, Any]]
    moving_averages: List[Dict[str, Any]]
    summary: Dict[str, Any]


# ==========================================
# TEMEL ANALİZ MODELLERİ
# ==========================================

class FundamentalData(BaseModel):
    """Temel analiz verileri"""
    symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Değerleme oranları
    pe_ratio: Optional[float] = Field(None, description="Fiyat/Kazanç (F/K)")
    pb_ratio: Optional[float] = Field(None, description="Piyasa Değeri/Defter Değeri (PD/DD)")
    ps_ratio: Optional[float] = Field(None, description="Fiyat/Satış")
    peg_ratio: Optional[float] = Field(None, description="F/K / Büyüme")
    
    # Piyasa verileri
    market_cap: Optional[float] = Field(None, description="Piyasa değeri")
    enterprise_value: Optional[float] = Field(None, description="Şirket değeri")
    
    # Kârlılık oranları
    profit_margin: Optional[float] = Field(None, description="Kâr marjı")
    operating_margin: Optional[float] = Field(None, description="Faaliyet marjı")
    roe: Optional[float] = Field(None, description="Özkaynak kârlılığı")
    roa: Optional[float] = Field(None, description="Aktif kârlılık")
    
    # Temettü
    dividend_yield: Optional[float] = Field(None, description="Temettü verimi")
    dividend_rate: Optional[float] = Field(None, description="Temettü oranı")
    
    # Bilanço
    total_revenue: Optional[float] = Field(None, description="Toplam gelir")
    total_debt: Optional[float] = Field(None, description="Toplam borç")
    total_cash: Optional[float] = Field(None, description="Toplam nakit")
    
    # Hisse verileri
    shares_outstanding: Optional[float] = Field(None, description="Dolaşımdaki hisse")
    float_shares: Optional[float] = Field(None, description="Halka açık hisse")
    
    # 52 hafta verileri
    week_52_high: Optional[float] = Field(None, description="52 hafta en yüksek")
    week_52_low: Optional[float] = Field(None, description="52 hafta en düşük")
    
    # Beta
    beta: Optional[float] = Field(None, description="Beta katsayısı")


class FundamentalResponse(BaseModel):
    """Temel analiz yanıtı"""
    data: FundamentalData
    updated_at: datetime


# ==========================================
# GENEL YANITLAR
# ==========================================

class ErrorResponse(BaseModel):
    """Hata yanıtı"""
    error: str
    detail: Optional[str] = None
    code: int


class HealthResponse(BaseModel):
    """Sağlık kontrolü yanıtı"""
    status: str
    version: str
    timestamp: datetime
