# HisseRadar Nedir? 📊

## Kısaca Özet

**HisseRadar**, Borsa İstanbul'daki (BIST) hisse senetlerini analiz eden ücretsiz bir web uygulamasıdır.

## Ne İşe Yarar?

### 🎯 Ana Amaç
Bireysel yatırımcılara ve öğrencilere, profesyonel seviyede hisse analiz araçlarını **ücretsiz** sunmak.

### 💡 Temel İşlevler

#### 1. **Hisse Takibi** 📈
- BIST'te işlem gören 500+ hisseyi listeler
- Hisse fiyatlarını ve değişimlerini gösterir
- Sektörlere göre gruplandırma
- Hızlı arama ve filtreleme

#### 2. **Teknik Analiz** 📊
Grafikler üzerinde otomatik sinyal üretir:
- **RSI**: Aşırı alım/satım bölgelerini gösterir
- **MACD**: Trend yönünü belirler
- **Bollinger Bantları**: Volatilite seviyelerini ölçer
- **Hareketli Ortalamalar**: Destek/direnç seviyelerini gösterir
- **Mum Formasyonları**: Grafik desenlerini tespit eder
- **Fibonacci**: Fiyat hedeflerini hesaplar

**Ne söyler?** → "AL", "SAT", "BEKLE" sinyalleri verir

#### 3. **Temel Analiz** 💰
Şirket mali durumunu değerlendirir:
- **F/K Oranı**: Hisse pahalı mı, ucuz mu?
- **PD/DD**: Şirket değeri ne kadar?
- **ROE/ROA**: Ne kadar karlı?
- **Temettü Verimi**: Ne kadar temettü veriyor?
- **Borçluluk**: Şirket çok borçlu mu?

**Ne söyler?** → Hisse "değerli", "makul" veya "pahalı"

#### 4. **Akıllı Özellikler** 🤖
- **Watchlist (İzleme Listesi)**: Takip ettiğiniz hisseleri kaydedin
- **Alarmlar**: Fiyat hedefleriniz geldiğinde bildirim
- **Portföy Takibi**: Sanal portföyünüzü yönetin
- **Backtest**: Geçmiş sinyallerin ne kadar tuttuğunu görün
- **AI Tahminleri**: Yapay zeka destekli fiyat öngörüleri
- **Haberler**: KAP duyuruları ve piyasa haberleri

#### 5. **PRO Özellikler** ⭐
- İleri seviye teknik göstergeler (Ichimoku, VWAP)
- Risk analizi (Sharpe Ratio, VaR, Beta)
- Sektor rotasyonu analizi
- Detaylı momentum göstergeleri

## Kimler Kullanabilir?

✅ **Öğrenciler** - Borsa öğrenmek isteyenler  
✅ **Bireysel Yatırımcılar** - Kendi analizini yapmak isteyenler  
✅ **Hobiciler** - Borsa takip etmek isteyenler  
✅ **Geliştiriciler** - Açık kaynak proje arayan yazılımcılar  

## Nasıl Çalışır?

```
1. Kullanıcı hisse sembolü seçer (örn: THYAO, AKBNK, ASELS)
   ↓
2. Uygulama Yahoo Finance'den güncel verileri çeker
   ↓
3. Backend (Python) teknik ve temel analizleri yapar
   ↓
4. Frontend (React/Next.js) sonuçları grafiklerle gösterir
   ↓
5. Kullanıcı AL/SAT/BEKLE sinyali alır
```

## Neden Kullanılır?

### ❌ Geleneksel Yol (Manuel Analiz)
- Excel'de manuel hesaplama → **Zaman kaybı**
- Birden fazla siteyi kontrol etme → **Dağınık bilgi**
- Grafik çizme ve yorumlama → **Hata riski**
- Sürekli fiyat takibi → **Zahmetli**

### ✅ HisseRadar ile
- **Otomatik** hesaplama ve sinyal üretimi
- **Tek platformda** tüm bilgiler
- **Doğru** teknik göstergeler
- **Alarmlar** ile otomatik takip

## Hangi Verileri Kullanır?

📊 **Veri Kaynağı**: Yahoo Finance (yfinance API)  
⏱️ **Gecikme**: 15-20 dakika (ücretsiz veri)  
💰 **Maliyet**: 0 TL/ay (tamamen ücretsiz)  

## Teknoloji Nedir?

### Backend (Arka Plan)
- **Python** - Programlama dili
- **FastAPI** - Web API framework
- **pandas** - Veri işleme
- **pandas-ta** - Teknik analiz kütüphanesi

### Frontend (Kullanıcı Arayüzü)
- **Next.js** - React web framework
- **TypeScript** - Tip güvenliği
- **TradingView Charts** - Profesyonel grafikler
- **Tailwind CSS** - Modern tasarım

## Sınırlamalar

⚠️ **Önemli Uyarılar**:
- Veriler 15-20 dakika gecikmelidir
- Bu bir **yatırım tavsiyesi değildir**
- Eğitim ve bilgilendirme amaçlıdır
- Gerçek yatırım kararlarınızda profesyonel danışmanlık alın

## Ücretsiz mi?

✅ **%100 Ücretsiz**
- Kayıt ücreti yok
- Abonelik ücreti yok
- Gizli ücret yok
- Açık kaynak (MIT Lisansı)

## Örnek Kullanım Senaryosu

**Senaryo**: THYAO hissesini analiz etmek istiyorsunuz

1. **Arama** → "THYAO" yazın
2. **Grafiği İnceleyin** → Fiyat hareketlerini görün
3. **Teknik Göstergelere Bakın**:
   - RSI = 72 → **Aşırı alım bölgesi** ⚠️
   - MACD = Düşüş sinyali → **SAT** 🔴
   - Bollinger = Üst bantta → **Geri çekilme olabilir**
4. **Temel Verileri İnceleyin**:
   - F/K = 8.5 → **Sektör ortalamasının altında** ✅
   - ROE = 15% → **İyi karlılık** ✅
   - Borç/Özkaynak = 0.6 → **Makul seviye** ✅
5. **Karar**:
   - Teknik: SAT sinyali
   - Temel: Değerli
   - **Sonuç**: Fiyat düşerse AL fırsatı olabilir 💡

## Nasıl Başlanır?

### Kullanıcı Olarak
1. Uygulamayı açın (web tarayıcısında)
2. Hisse arayın
3. Analizleri inceleyin
4. Watchlist'e ekleyin
5. Alarm kurun

### Geliştirici Olarak
1. Repoyu klonlayın
2. Backend'i başlatın (Python)
3. Frontend'i başlatın (Node.js)
4. Kodlamaya başlayın

Detaylı kurulum için ana [README.md](README.md) dosyasına bakın.

## Sorular?

**S: Gerçek zamanlı veri var mı?**  
C: Hayır, 15-20 dakika gecikme var (ücretsiz API limiti).

**S: Mobil uygulama var mı?**  
C: Web sitesi mobil uyumlu, tarayıcıdan kullanılabilir.

**S: Hangi hisseler destekleniyor?**  
C: BIST'te işlem gören tüm hisseler (500+).

**S: Verilerim güvende mi?**  
C: Tüm veriler tarayıcınızda saklanır, sunucuda tutulmaz.

**S: Nasıl katkıda bulunabilirim?**  
C: GitHub'dan issue açabilir veya pull request gönderebilirsiniz.

---

## İletişim

Daha fazla bilgi için ana [README.md](README.md) dosyasını inceleyin veya GitHub'da issue açın.

**HisseRadar** ile mutlu analizler! 📈🚀
