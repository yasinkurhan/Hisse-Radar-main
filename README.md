# HisseRadar 🚀

## BIST Borsa Analiz Platformu

Borsa İstanbul (BIST) hisseleri için kapsamlı teknik ve temel analiz platformu. Öğrenci bütçesine uygun, tamamen ücretsiz ve açık kaynak.

![HisseRadar Banner](https://via.placeholder.com/1200x400/0ea5e9/ffffff?text=HisseRadar+-+BIST+Analiz+Platformu)

## 🌟 Özellikler

### 📈 Fiyat Grafikleri
- TradingView Lightweight Charts ile interaktif mum grafikleri
- Günlük, haftalık, aylık veri görüntüleme
- Hacim göstergesi
- Yakınlaştırma ve kaydırma

### 📊 Teknik Analiz
- **RSI (Relative Strength Index)**: Aşırı alım/satım göstergesi
- **MACD**: Trend ve momentum göstergesi
- **Bollinger Bands**: Volatilite bandları
- **Hareketli Ortalamalar**: SMA20, SMA50, SMA200, EMA12, EMA26
- Otomatik sinyal üretimi

### 📋 Temel Analiz
- **Değerleme**: F/K, PD/DD, F/S, PEG oranları
- **Kârlılık**: ROE, ROA, Kâr marjları
- **Temettü**: Temettü verimi ve dağıtım oranı
- **Bilanço**: Borç/Özkaynak, Cari oran
- Otomatik değerlendirme ve notlar

### 🔍 Diğer
- 100+ BIST hissesi
- Hisse arama ve sektör filtreleme
- Responsive tasarım (mobil uyumlu)
- Gecikmeli veri (15-20 dk)

## 🛠️ Teknoloji Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern, hızlı web framework
- **yfinance** - Yahoo Finance API wrapper
- **pandas** - Veri işleme
- **pandas-ta** - Teknik analiz göstergeleri

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Tip güvenliği
- **Tailwind CSS** - Stil
- **Lightweight Charts** - TradingView grafik kütüphanesi
- **Lucide Icons** - İkonlar

## 📁 Proje Yapısı

```
HisseRadar/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI ana dosya
│   │   ├── config.py            # Yapılandırma
│   │   ├── routers/             # API endpoint'leri
│   │   │   ├── stocks.py        # Hisse listesi
│   │   │   ├── price.py         # Fiyat verileri
│   │   │   ├── technical.py     # Teknik analiz
│   │   │   └── fundamental.py   # Temel analiz
│   │   ├── services/            # İş mantığı
│   │   │   ├── data_fetcher.py
│   │   │   ├── technical_analysis.py
│   │   │   └── fundamental_analysis.py
│   │   ├── models/              # Veri modelleri
│   │   └── data/                # Statik veriler
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js sayfalar
│   │   ├── components/          # React bileşenleri
│   │   ├── lib/                 # Yardımcı fonksiyonlar
│   │   └── types/               # TypeScript tipleri
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

## 🚀 Kurulum

### Gereksinimler
- Python 3.11 veya üzeri
- Node.js 18 veya üzeri
- npm veya yarn

### Backend Kurulumu

```bash
# Backend klasörüne git
cd backend

# Sanal ortam oluştur (önerilir)
python -m venv venv

# Sanal ortamı aktif et
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Sunucuyu başlat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend şimdi http://localhost:8000 adresinde çalışıyor.

API Dokümantasyonu: http://localhost:8000/docs

### Frontend Kurulumu

```bash
# Frontend klasörüne git
cd frontend

# Bağımlılıkları yükle
npm install

# Geliştirme sunucusunu başlat
npm run dev
```

Frontend şimdi http://localhost:3000 adresinde çalışıyor.

## 📡 API Endpoint'leri

### Hisse Listesi
```
GET /api/stocks                    # Tüm hisseler
GET /api/stocks?sector=Bankacılık  # Sektöre göre filtre
GET /api/stocks?search=THY         # Arama
GET /api/stocks/{symbol}           # Hisse detayı
GET /api/stocks/sectors            # Sektör listesi
```

### Fiyat Verileri
```
GET /api/price/{symbol}                      # Fiyat geçmişi
GET /api/price/{symbol}?period=3mo&interval=1d
GET /api/price/{symbol}/candles              # TradingView formatı
GET /api/price/{symbol}/volume               # Hacim verileri
GET /api/price/{symbol}/latest               # Güncel fiyat
```

### Teknik Analiz
```
GET /api/technical/{symbol}           # Tüm göstergeler
GET /api/technical/{symbol}/rsi       # RSI
GET /api/technical/{symbol}/macd      # MACD
GET /api/technical/{symbol}/bollinger # Bollinger Bands
GET /api/technical/{symbol}/ma        # Hareketli Ortalamalar
GET /api/technical/{symbol}/summary   # Özet rapor
```

### Temel Analiz
```
GET /api/fundamental/{symbol}           # Kapsamlı veriler
GET /api/fundamental/{symbol}/valuation # Değerleme oranları
GET /api/fundamental/{symbol}/profitability # Kârlılık
GET /api/fundamental/{symbol}/dividend  # Temettü
GET /api/fundamental/{symbol}/balance   # Bilanço
GET /api/fundamental/{symbol}/summary   # Özet rapor
```

## 💰 Maliyet (Öğrenci Bütçesi)

| Bileşen | Maliyet |
|---------|---------|
| yfinance API | **Ücretsiz** |
| TradingView Charts | **Ücretsiz** (Açık kaynak) |
| Vercel (Frontend) | **Ücretsiz** (Hobby tier) |
| Railway/Render (Backend) | **Ücretsiz** (Free tier) |
| **TOPLAM** | **$0/ay** |

## 🚀 Deploy

### Vercel (Frontend)
1. GitHub'a push edin
2. Vercel'e bağlayın
3. `frontend` klasörünü root olarak seçin
4. Deploy!

### Railway/Render (Backend)
1. GitHub'a push edin
2. Railway veya Render'a bağlayın
3. `backend` klasörünü seçin
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## ⚠️ Yasal Uyarı

Bu platform **eğitim ve bilgilendirme amaçlıdır**. Sunulan veriler ve analizler **yatırım tavsiyesi niteliği taşımaz**. 

- Veriler 15-20 dakika gecikmelidir
- Yatırım kararlarınızı vermeden önce profesyonel danışmanlık alınız
- Geçmiş performans gelecek sonuçları garanti etmez

## 📝 Lisans

MIT License - Özgürce kullanabilir, değiştirebilir ve dağıtabilirsiniz.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📧 İletişim

Sorularınız için issue açabilirsiniz.

---

**HisseRadar** ile yatırım yolculuğunuzda başarılar! 📈🚀
