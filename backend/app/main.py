"""
HisseRadar API - Ana Uygulama
==============================
BIST Hisse Analiz Platformu Backend

Gelistirici: HisseRadar Team
Versiyon: 2.0.0
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from .config import get_settings
from .routers import stocks_router, price_router, technical_router, fundamental_router
from .routers.analysis import router as analysis_router
from .routers.user_router import router as user_router
from .routers.backtest_router import router as backtest_router
from .routers.chart_router import router as chart_router
from .routers.filter_router import router as filter_router
from .routers.pro_analysis_router import router as pro_analysis_router
from .routers.news_router import router as news_router
from .routers.ai_router import router as ai_router
from .routers.fundamental_router import router as advanced_fundamental_router
from .routers.kap_router import router as kap_router
from .routers.fx_router import router as fx_router
from .routers.crypto_router import router as crypto_router
from .routers.fund_router import router as fund_router
from .routers.screener_router import router as screener_router
from .routers.economy_router import router as economy_router
from .routers.viop_router import router as viop_router
from .routers.index_router import router as index_router


# Ayarlari yukle
settings = get_settings()

# FastAPI uygulamasini olustur
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## HisseRadar API v2.0

    Borsa Istanbul (BIST) hisseleri icin kapsamli analiz platformu.
    
    **Veri Kaynagi:** borsapy kutuphanesi (Is Yatirim, TradingView, KAP, TCMB, BtcTurk, TEFAS, doviz.com)

    ### Ozellikler:

    * **Hisse Listesi** - BIST'te islem goren 500+ hisseyi listele ve ara
    * **Fiyat Verileri** - Gunluk, haftalik, aylik fiyat gecmisi
    * **Teknik Analiz** - RSI, MACD, Bollinger, ADX, Fibonacci, OBV, Supertrend, VWAP
    * **Temel Analiz** - F/K, PD/DD, ROE, Temettu, Bilanco verileri
    * **Formasyon Tespiti** - Cift dip/tepe, omuz-bas-omuz, ucgen
    * **Akilli Skorlama** - Sektore ve piyasa kosuluna gore dinamik skor
    * **Backtest** - Gecmis sinyal performansi takibi
    * **Watchlist** - Kullanici takip listeleri
    * **Alarmlar** - Fiyat ve sinyal alarmlari
    * **Portfoy** - Sanal portfoy simulasyonu
    * **Doviz & Emtia** - Canli doviz kurlari, altin fiyatlari, banka kurlari
    * **Kripto Para** - BtcTurk uzerinden kripto verileri
    * **Yatirim Fonlari** - TEFAS fon verileri ve tarama
    * **Endeksler** - BIST endeks verileri ve bilesenleri
    * **Hisse Tarama** - 50+ kriter ile gelismis tarama (Screener)
    * **Ekonomi** - Tahvil, enflasyon, TCMB, ekonomik takvim, eurobond
    * **VIOP** - Vadeli islem ve opsiyon verileri
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS ayarlari - Frontend'in baglanabilmesi icin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gelistirme icin tum originlere izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Istek suresi middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Her istegin islenme suresini header'a ekle"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2)) + "ms"
    return response


# Hata yakalama
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Genel hata yakalayici"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Sunucu hatasi",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


# Router'lari ekle
app.include_router(stocks_router)
app.include_router(price_router)
app.include_router(technical_router)
app.include_router(fundamental_router)
app.include_router(analysis_router)
app.include_router(user_router)
app.include_router(backtest_router)
app.include_router(chart_router)
app.include_router(filter_router)
app.include_router(pro_analysis_router)
app.include_router(news_router)
app.include_router(ai_router)
app.include_router(advanced_fundamental_router)
app.include_router(kap_router)
app.include_router(fx_router)
app.include_router(crypto_router)
app.include_router(fund_router)
app.include_router(screener_router)
app.include_router(economy_router)
app.include_router(viop_router)
app.include_router(index_router)


# Ana endpoint'ler
@app.get("/", tags=["Genel"])
async def root():
    """
    API kok endpoint'i.
    API hakkinda temel bilgileri dondurur.
    """
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "description": "BIST Hisse Analiz Platformu - borsapy ile Gelismis Teknik ve Temel Analiz",
        "docs": "/docs",
        "data_source": "borsapy (Is Yatirim, TradingView, KAP, TCMB, BtcTurk, TEFAS)",
        "features": [
            "500+ BIST hissesi analizi",
            "Gelismis teknik gostergeler (ADX, Fibonacci, OBV, Supertrend, VWAP)",
            "TradingView teknik sinyalleri (AL/SAT/TUT)",
            "Formasyon tespiti",
            "Akilli skorlama sistemi",
            "Backtest ve performans takibi",
            "Watchlist ve alarmlar",
            "Sanal portfoy",
            "Doviz & Emtia (TCMB, doviz.com)",
            "Kripto para (BtcTurk)",
            "Yatirim fonlari (TEFAS)",
            "BIST endeksleri ve bilesenleri",
            "Gelismis hisse tarama (50+ kriter)",
            "Ekonomi: tahvil, enflasyon, TCMB faiz",
            "VIOP vadeli islem ve opsiyon",
            "PRO: Ichimoku Cloud analizi",
            "PRO: VWAP ve Volume Profile",
            "PRO: Momentum diverjans tespiti",
            "PRO: 25+ mum formasyonu",
            "PRO: Risk metrikleri (Sharpe, VaR, Beta)",
            "PRO: Piyasa genislik analizi",
            "PRO: Sektor rotasyonu",
            "PRO: AI sinyal birlesimi"
        ],
        "endpoints": {
            "stocks": "/api/stocks",
            "price": "/api/price",
            "technical": "/api/technical",
            "fundamental": "/api/fundamental",
            "analysis": "/api/analysis",
            "user": "/api/user",
            "backtest": "/api/backtest",
            "pro": "/api/pro",
            "fx": "/api/fx",
            "crypto": "/api/crypto",
            "fund": "/api/fund",
            "index": "/api/index",
            "screener": "/api/screener",
            "economy": "/api/economy",
            "viop": "/api/viop"
        }
    }


@app.get("/health", tags=["Genel"])
async def health_check():
    """
    Saglik kontrolu endpoint'i.
    API'nin calisir durumda oldugunu dogrular.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api", tags=["Genel"])
async def api_info():
    """
    API bilgi endpoint'i.
    Kullanilabilir tum endpoint'leri listeler.
    """
    return {
        "version": "2.0.0",
        "data_source": "borsapy",
        "endpoints": [
            {
                "path": "/api/stocks",
                "description": "Hisse listesi ve arama",
                "methods": ["GET"]
            },
            {
                "path": "/api/stocks/{symbol}",
                "description": "Hisse detay bilgisi",
                "methods": ["GET"]
            },
            {
                "path": "/api/price/{symbol}",
                "description": "Fiyat gecmisi (OHLCV)",
                "methods": ["GET"]
            },
            {
                "path": "/api/technical/{symbol}",
                "description": "Tum teknik gostergeler",
                "methods": ["GET"]
            },
            {
                "path": "/api/analysis/daily",
                "description": "Gunluk analiz - bir sonraki gun icin oneriler",
                "methods": ["POST"]
            },
            {
                "path": "/api/analysis/weekly",
                "description": "Haftalik analiz - bir sonraki hafta icin oneriler",
                "methods": ["POST"]
            },
            {
                "path": "/api/user/watchlist",
                "description": "Kullanici takip listesi",
                "methods": ["GET", "POST"]
            },
            {
                "path": "/api/user/alerts",
                "description": "Fiyat ve sinyal alarmlari",
                "methods": ["GET", "POST"]
            },
            {
                "path": "/api/user/portfolio",
                "description": "Sanal portfoy yonetimi",
                "methods": ["GET", "POST"]
            },
            {
                "path": "/api/backtest/performance",
                "description": "Sinyal performans istatistikleri",
                "methods": ["GET"]
            },
            {
                "path": "/api/backtest/market-condition",
                "description": "Genel piyasa kosulu analizi",
                "methods": ["GET"]
            },
            {
                "path": "/api/fx/current/{currency}",
                "description": "Guncel doviz kurlari",
                "methods": ["GET"]
            },
            {
                "path": "/api/crypto/current/{pair}",
                "description": "Kripto para fiyatlari",
                "methods": ["GET"]
            },
            {
                "path": "/api/fund/info/{code}",
                "description": "Yatirim fonu bilgileri (TEFAS)",
                "methods": ["GET"]
            },
            {
                "path": "/api/index/{code}",
                "description": "BIST endeks verileri",
                "methods": ["GET"]
            },
            {
                "path": "/api/screener/stocks",
                "description": "Gelismis hisse tarama",
                "methods": ["GET"]
            },
            {
                "path": "/api/economy/bonds",
                "description": "Tahvil faiz oranlari",
                "methods": ["GET"]
            },
            {
                "path": "/api/economy/tcmb",
                "description": "TCMB faiz oranlari",
                "methods": ["GET"]
            },
            {
                "path": "/api/viop/futures",
                "description": "VIOP vadeli islem verileri",
                "methods": ["GET"]
            }
        ]
    }


# Uygulama baslatma
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


