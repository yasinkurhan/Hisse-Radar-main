"""
HisseRadar Haber & Sentiment Analizi Modülü
============================================
KAP bildirimleri, haberler ve sentiment analizi
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re
import json


class SentimentType(Enum):
    """Sentiment türleri"""
    VERY_POSITIVE = "çok_pozitif"
    POSITIVE = "pozitif"
    NEUTRAL = "nötr"
    NEGATIVE = "negatif"
    VERY_NEGATIVE = "çok_negatif"


@dataclass
class NewsItem:
    """Haber veri yapısı"""
    title: str
    summary: str
    source: str
    date: datetime
    url: str
    sentiment: SentimentType
    sentiment_score: float  # -1 ile 1 arası
    relevance: float  # 0-1 arası
    category: str
    symbol: Optional[str] = None


class SentimentAnalyzer:
    """
    Türkçe Sentiment Analizi
    ========================
    Haber başlıklarını ve içeriklerini analiz eder
    """
    
    # Pozitif kelimeler ve ağırlıkları
    POSITIVE_WORDS = {
        # Güçlü pozitif
        "rekor": 2.0, "tarihi": 1.8, "patlama": 1.5, "sıçrama": 1.5,
        "fırlama": 1.8, "uçuş": 1.5, "zirve": 1.8, "en yüksek": 1.8,
        "devasa": 1.5, "muhteşem": 1.5, "olağanüstü": 1.5,
        
        # Orta pozitif
        "artış": 1.0, "yükseliş": 1.2, "kazanç": 1.0, "kâr": 1.2,
        "büyüme": 1.0, "gelişme": 0.8, "iyileşme": 0.8, "toparlanma": 0.8,
        "pozitif": 0.8, "olumlu": 0.8, "iyi": 0.6, "güçlü": 0.8,
        "başarı": 1.0, "başarılı": 1.0, "verimli": 0.8, "karlı": 1.0,
        
        # Hafif pozitif
        "beklentilerin üzerinde": 1.2, "tahminleri aştı": 1.2,
        "yatırım": 0.6, "genişleme": 0.8, "anlaşma": 0.8,
        "ortaklık": 0.6, "işbirliği": 0.6, "sözleşme": 0.6,
        "ihale": 0.6, "kazandı": 0.8, "aldı": 0.4,
        
        # Finansal pozitif
        "temettü": 0.8, "bedelsiz": 1.0, "sermaye artırımı": 0.6,
        "hisse geri alım": 0.8, "kredi notu yükseldi": 1.2,
        "hedef fiyat yükseldi": 1.0, "al tavsiyesi": 1.2,
    }
    
    # Negatif kelimeler ve ağırlıkları
    NEGATIVE_WORDS = {
        # Güçlü negatif
        "çöküş": -2.0, "kriz": -1.8, "felaket": -2.0, "iflas": -2.0,
        "batık": -1.8, "konkordato": -2.0, "dolandırıcılık": -2.0,
        "soruşturma": -1.5, "suç": -1.8, "ceza": -1.5, "yasak": -1.5,
        
        # Orta negatif
        "düşüş": -1.0, "gerileme": -1.0, "zarar": -1.2, "kayıp": -1.0,
        "daralma": -1.0, "küçülme": -1.0, "kötüleşme": -1.0, "olumsuz": -0.8,
        "negatif": -0.8, "kötü": -0.6, "zayıf": -0.8, "endişe": -0.8,
        "risk": -0.6, "tehlike": -0.8, "belirsizlik": -0.6,
        
        # Hafif negatif
        "beklentilerin altında": -1.2, "hayal kırıklığı": -1.0,
        "erteleme": -0.6, "iptal": -0.8, "durdurma": -0.6,
        "azalma": -0.6, "geriledi": -0.6, "düştü": -0.6,
        
        # Finansal negatif
        "sermaye azaltımı": -0.8, "kredi notu düştü": -1.2,
        "hedef fiyat düştü": -1.0, "sat tavsiyesi": -1.2,
        "borç": -0.4, "faiz": -0.4, "maliyet": -0.4,
    }
    
    # KAP kategorileri ve sentiment etkileri
    KAP_CATEGORIES = {
        "FR": {"name": "Finansal Rapor", "sentiment_modifier": 0},
        "ODA": {"name": "Özel Durum Açıklaması", "sentiment_modifier": 0},
        "BD": {"name": "Bağımsız Denetim", "sentiment_modifier": 0},
        "OZET": {"name": "Özet Bilgi", "sentiment_modifier": 0},
        "IY": {"name": "İç Yönerge", "sentiment_modifier": 0},
        "GK": {"name": "Genel Kurul", "sentiment_modifier": 0.1},
        "TA": {"name": "Temettü Açıklaması", "sentiment_modifier": 0.3},
        "SA": {"name": "Sermaye Artırımı", "sentiment_modifier": 0.2},
        "HALKA_ARZ": {"name": "Halka Arz", "sentiment_modifier": 0.2},
    }
    
    @staticmethod
    def analyze_text(text: str) -> Dict[str, Any]:
        """Metin sentiment analizi"""
        if not text:
            return {
                "sentiment": SentimentType.NEUTRAL,
                "score": 0,
                "confidence": 0,
                "keywords": []
            }
        
        text_lower = text.lower()
        
        total_score = 0
        matched_keywords = []
        
        # Pozitif kelimeleri ara
        for word, weight in SentimentAnalyzer.POSITIVE_WORDS.items():
            if word in text_lower:
                total_score += weight
                matched_keywords.append({"word": word, "weight": weight, "type": "positive"})
        
        # Negatif kelimeleri ara
        for word, weight in SentimentAnalyzer.NEGATIVE_WORDS.items():
            if word in text_lower:
                total_score += weight
                matched_keywords.append({"word": word, "weight": weight, "type": "negative"})
        
        # Normalize et (-1 ile 1 arası)
        if matched_keywords:
            max_possible = max(
                sum(w for w in SentimentAnalyzer.POSITIVE_WORDS.values()),
                abs(sum(w for w in SentimentAnalyzer.NEGATIVE_WORDS.values()))
            )
            normalized_score = max(-1, min(1, total_score / 10))
        else:
            normalized_score = 0
        
        # Sentiment belirle
        sentiment = SentimentAnalyzer._score_to_sentiment(normalized_score)
        
        # Güven skoru (bulunan keyword sayısına göre)
        confidence = min(1, len(matched_keywords) / 5)
        
        return {
            "sentiment": sentiment,
            "score": round(normalized_score, 3),
            "confidence": round(confidence, 2),
            "keywords": matched_keywords
        }
    
    @staticmethod
    def _score_to_sentiment(score: float) -> SentimentType:
        """Skoru sentiment'e çevir"""
        if score >= 0.6:
            return SentimentType.VERY_POSITIVE
        elif score >= 0.2:
            return SentimentType.POSITIVE
        elif score <= -0.6:
            return SentimentType.VERY_NEGATIVE
        elif score <= -0.2:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.NEUTRAL


class KAPService:
    """
    KAP Bildirimleri Servisi
    ========================
    Kamuyu Aydınlatma Platformu verilerini simüle eder
    Gerçek uygulamada KAP API veya web scraping kullanılır
    """
    
    # Örnek KAP bildirimleri (gerçek uygulamada API'den çekilir)
    SAMPLE_KAP_NOTIFICATIONS = {
        "THYAO": [
            {
                "title": "2025 Yılı 4. Çeyrek Finansal Sonuçları",
                "summary": "Şirketimizin 2025 yılı 4. çeyrek net karı bir önceki yılın aynı dönemine göre %45 artışla 28.5 milyar TL olarak gerçekleşmiştir.",
                "date": "2026-01-28",
                "category": "FR",
                "importance": "high"
            },
            {
                "title": "Yeni Uçak Siparişi",
                "summary": "Şirketimiz Airbus ile 50 adet A321neo uçağı için sipariş anlaşması imzalamıştır.",
                "date": "2026-01-25",
                "category": "ODA",
                "importance": "high"
            },
            {
                "title": "Temettü Dağıtım Kararı",
                "summary": "Yönetim Kurulumuz 2025 yılı karından hisse başına brüt 5.50 TL temettü dağıtılmasını Genel Kurul'a teklif etmeye karar vermiştir.",
                "date": "2026-01-20",
                "category": "TA",
                "importance": "high"
            }
        ],
        "SASA": [
            {
                "title": "Üretim Tesisi Yatırımı",
                "summary": "Şirketimiz Adana'da 500 milyon USD yatırım ile yeni polimer üretim tesisi kuracaktır.",
                "date": "2026-01-27",
                "category": "ODA",
                "importance": "high"
            },
            {
                "title": "2025 Yılı Finansal Sonuçları",
                "summary": "Şirketimizin 2025 yılı net karı beklentilerin üzerinde gerçekleşmiştir.",
                "date": "2026-01-26",
                "category": "FR",
                "importance": "medium"
            }
        ],
        "EREGL": [
            {
                "title": "İhracat Rekoru",
                "summary": "Şirketimiz 2025 yılında 8.5 milyar USD ihracat ile sektör rekoru kırmıştır.",
                "date": "2026-01-28",
                "category": "ODA",
                "importance": "high"
            },
            {
                "title": "Çevre Yatırımı",
                "summary": "Karbon salınımını %30 azaltacak yeşil çelik yatırımı başlatılmıştır.",
                "date": "2026-01-22",
                "category": "ODA",
                "importance": "medium"
            }
        ],
        "ASELS": [
            {
                "title": "Yeni Savunma İhalesi Kazanıldı",
                "summary": "Şirketimiz NATO ülkelerine 2 milyar Euro değerinde savunma sistemi ihracatı anlaşması imzalamıştır.",
                "date": "2026-01-29",
                "category": "ODA",
                "importance": "high"
            },
            {
                "title": "Ar-Ge Merkezi Açılışı",
                "summary": "Ankara'da yeni Ar-Ge merkezi hizmete açılmıştır. 1000 mühendis istihdam edilecektir.",
                "date": "2026-01-24",
                "category": "ODA",
                "importance": "medium"
            }
        ],
        "AKBNK": [
            {
                "title": "Kredi Notu Yükseltildi",
                "summary": "Uluslararası kredi derecelendirme kuruluşu Fitch, bankamızın notunu BB+'dan BBB-'ye yükseltmiştir.",
                "date": "2026-01-28",
                "category": "ODA",
                "importance": "high"
            },
            {
                "title": "Dijital Bankacılık Yatırımı",
                "summary": "Bankamız dijital dönüşüm için 500 milyon TL yatırım yapacaktır.",
                "date": "2026-01-23",
                "category": "ODA",
                "importance": "medium"
            }
        ],
        "KCHOL": [
            {
                "title": "Holding Şirketleri Konsolide Kar Artışı",
                "summary": "Holding bünyesindeki şirketlerin konsolide net karı %35 artışla 45 milyar TL olmuştur.",
                "date": "2026-01-27",
                "category": "FR",
                "importance": "high"
            }
        ],
        "TUPRS": [
            {
                "title": "Rafineri Modernizasyon Projesi",
                "summary": "İzmit Rafinerisi'nde 1.5 milyar USD değerinde modernizasyon yatırımı başlatılmıştır.",
                "date": "2026-01-26",
                "category": "ODA",
                "importance": "high"
            }
        ]
    }
    
    @staticmethod
    def get_kap_notifications(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Hisse için KAP bildirimlerini getir"""
        notifications = KAPService.SAMPLE_KAP_NOTIFICATIONS.get(symbol, [])
        
        result = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for notif in notifications:
            notif_date = datetime.strptime(notif["date"], "%Y-%m-%d")
            if notif_date >= cutoff_date:
                # Sentiment analizi yap
                text = f"{notif['title']} {notif['summary']}"
                sentiment = SentimentAnalyzer.analyze_text(text)
                
                # Kategori etkisini ekle
                category_info = SentimentAnalyzer.KAP_CATEGORIES.get(
                    notif["category"], 
                    {"name": "Diğer", "sentiment_modifier": 0}
                )
                
                result.append({
                    **notif,
                    "category_name": category_info["name"],
                    "sentiment": sentiment["sentiment"].value,
                    "sentiment_score": sentiment["score"] + category_info["sentiment_modifier"],
                    "sentiment_keywords": sentiment["keywords"],
                    "source": "KAP"
                })
        
        return sorted(result, key=lambda x: x["date"], reverse=True)
    
    @staticmethod
    def get_latest_kap_all(limit: int = 20) -> List[Dict[str, Any]]:
        """Tüm hisseler için son KAP bildirimlerini getir"""
        all_notifications = []
        
        for symbol, notifications in KAPService.SAMPLE_KAP_NOTIFICATIONS.items():
            for notif in notifications:
                text = f"{notif['title']} {notif['summary']}"
                sentiment = SentimentAnalyzer.analyze_text(text)
                category_info = SentimentAnalyzer.KAP_CATEGORIES.get(
                    notif["category"],
                    {"name": "Diğer", "sentiment_modifier": 0}
                )
                
                all_notifications.append({
                    **notif,
                    "symbol": symbol,
                    "category_name": category_info["name"],
                    "sentiment": sentiment["sentiment"].value,
                    "sentiment_score": sentiment["score"] + category_info["sentiment_modifier"],
                    "source": "KAP"
                })
        
        # Tarihe göre sırala ve limit uygula
        sorted_notifs = sorted(all_notifications, key=lambda x: x["date"], reverse=True)
        return sorted_notifs[:limit]


class NewsService:
    """
    Haber Servisi
    =============
    Finansal haberler (simüle edilmiş)
    """
    
    SAMPLE_NEWS = {
        "THYAO": [
            {
                "title": "THY Avrupa'nın En Büyük Havayolu Şirketi Oldu",
                "summary": "Türk Hava Yolları, yolcu sayısında Lufthansa'yı geçerek Avrupa'nın en büyük havayolu şirketi unvanını aldı.",
                "source": "Bloomberg HT",
                "date": "2026-01-29",
                "url": "#",
                "category": "sektör"
            },
            {
                "title": "THY Hisseleri Yeni Zirve Yaptı",
                "summary": "Rekor açıklayan THY hisseleri güne %5 yükselişle başladı.",
                "source": "Ekonomist",
                "date": "2026-01-28",
                "url": "#",
                "category": "piyasa"
            }
        ],
        "SASA": [
            {
                "title": "SASA Dev Yatırımla Kapasite İkiye Katlıyor",
                "summary": "Petrokimya devi SASA, yeni yatırımlarla üretim kapasitesini ikiye katlayacak.",
                "source": "Dünya",
                "date": "2026-01-28",
                "url": "#",
                "category": "şirket"
            }
        ],
        "ASELS": [
            {
                "title": "ASELSAN'dan Tarihi İhracat",
                "summary": "ASELSAN, NATO ülkelerine 2 milyar Euro'luk savunma sistemi ihraç edecek. Bu, Türk savunma sanayii tarihinin en büyük ihracatı.",
                "source": "AA",
                "date": "2026-01-29",
                "url": "#",
                "category": "şirket"
            }
        ],
        "BIST100": [
            {
                "title": "BIST 100 Tarihi Zirvesini Gördü",
                "summary": "Borsa İstanbul 100 endeksi yabancı girişleriyle 12.500 puanı aştı.",
                "source": "Reuters",
                "date": "2026-01-29",
                "url": "#",
                "category": "piyasa"
            },
            {
                "title": "Merkez Bankası Faiz Kararı",
                "summary": "TCMB politika faizini sabit tuttu, enflasyon görünümü değerlendirildi.",
                "source": "Bloomberg",
                "date": "2026-01-28",
                "url": "#",
                "category": "ekonomi"
            },
            {
                "title": "Yabancı Yatırımcılar Türkiye'ye Dönüyor",
                "summary": "Ocak ayında yabancı yatırımcılar 2 milyar dolarlık hisse senedi aldı.",
                "source": "Financial Times",
                "date": "2026-01-27",
                "url": "#",
                "category": "piyasa"
            }
        ]
    }
    
    @staticmethod
    def get_news(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Hisse için haberleri getir"""
        news_list = NewsService.SAMPLE_NEWS.get(symbol, [])
        
        # Genel piyasa haberlerini de ekle
        general_news = NewsService.SAMPLE_NEWS.get("BIST100", [])
        
        combined = []
        
        for news in news_list:
            sentiment = SentimentAnalyzer.analyze_text(f"{news['title']} {news['summary']}")
            combined.append({
                **news,
                "symbol": symbol,
                "sentiment": sentiment["sentiment"].value,
                "sentiment_score": sentiment["score"],
                "is_direct": True
            })
        
        for news in general_news:
            sentiment = SentimentAnalyzer.analyze_text(f"{news['title']} {news['summary']}")
            combined.append({
                **news,
                "symbol": "BIST100",
                "sentiment": sentiment["sentiment"].value,
                "sentiment_score": sentiment["score"],
                "is_direct": False
            })
        
        return sorted(combined, key=lambda x: x["date"], reverse=True)[:limit]
    
    @staticmethod
    def get_market_news(limit: int = 20) -> List[Dict[str, Any]]:
        """Genel piyasa haberlerini getir"""
        all_news = []
        
        for symbol, news_list in NewsService.SAMPLE_NEWS.items():
            for news in news_list:
                sentiment = SentimentAnalyzer.analyze_text(f"{news['title']} {news['summary']}")
                all_news.append({
                    **news,
                    "symbol": symbol,
                    "sentiment": sentiment["sentiment"].value,
                    "sentiment_score": sentiment["score"]
                })
        
        return sorted(all_news, key=lambda x: x["date"], reverse=True)[:limit]


class MarketSentimentAggregator:
    """
    Piyasa Sentiment Toplayıcı
    ==========================
    Tüm kaynaklardan sentiment'i birleştirir
    """
    
    @staticmethod
    def get_stock_sentiment(symbol: str) -> Dict[str, Any]:
        """Hisse için genel sentiment analizi"""
        # KAP bildirimleri
        kap_notifs = KAPService.get_kap_notifications(symbol, days=30)
        
        # Haberler
        news = NewsService.get_news(symbol, limit=10)
        
        # Sentiment skorlarını topla
        all_scores = []
        
        for notif in kap_notifs:
            all_scores.append({
                "score": notif["sentiment_score"],
                "weight": 1.5 if notif["importance"] == "high" else 1.0,
                "source": "KAP"
            })
        
        for n in news:
            weight = 1.2 if n.get("is_direct") else 0.8
            all_scores.append({
                "score": n["sentiment_score"],
                "weight": weight,
                "source": "Haber"
            })
        
        # Ağırlıklı ortalama
        if all_scores:
            total_weight = sum(s["weight"] for s in all_scores)
            weighted_score = sum(s["score"] * s["weight"] for s in all_scores) / total_weight
        else:
            weighted_score = 0
        
        # Sentiment belirle
        sentiment = SentimentAnalyzer._score_to_sentiment(weighted_score)
        
        # KAP ve haber sayıları
        positive_count = sum(1 for s in all_scores if s["score"] > 0.1)
        negative_count = sum(1 for s in all_scores if s["score"] < -0.1)
        neutral_count = len(all_scores) - positive_count - negative_count
        
        return {
            "symbol": symbol,
            "overall_sentiment": sentiment.value,
            "sentiment_score": round(weighted_score, 3),
            "sentiment_label": MarketSentimentAggregator._get_sentiment_label(sentiment),
            "total_news": len(all_scores),
            "positive_news": positive_count,
            "negative_news": negative_count,
            "neutral_news": neutral_count,
            "kap_count": len(kap_notifs),
            "news_count": len(news),
            "latest_kap": kap_notifs[:3] if kap_notifs else [],
            "latest_news": news[:5] if news else [],
            "sentiment_trend": MarketSentimentAggregator._calculate_trend(all_scores),
            "recommendation": MarketSentimentAggregator._get_recommendation(weighted_score)
        }
    
    @staticmethod
    def _get_sentiment_label(sentiment: SentimentType) -> str:
        """Sentiment için Türkçe etiket"""
        labels = {
            SentimentType.VERY_POSITIVE: "🚀 Çok Olumlu",
            SentimentType.POSITIVE: "📈 Olumlu",
            SentimentType.NEUTRAL: "➖ Nötr",
            SentimentType.NEGATIVE: "📉 Olumsuz",
            SentimentType.VERY_NEGATIVE: "🔻 Çok Olumsuz"
        }
        return labels.get(sentiment, "➖ Nötr")
    
    @staticmethod
    def _calculate_trend(scores: List[Dict]) -> str:
        """Sentiment trendini hesapla"""
        if len(scores) < 2:
            return "stable"
        
        recent = scores[:len(scores)//2]
        older = scores[len(scores)//2:]
        
        recent_avg = sum(s["score"] for s in recent) / len(recent) if recent else 0
        older_avg = sum(s["score"] for s in older) / len(older) if older else 0
        
        diff = recent_avg - older_avg
        
        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"
    
    @staticmethod
    def _get_recommendation(score: float) -> str:
        """Sentiment bazlı öneri"""
        if score >= 0.5:
            return "Haberler çok olumlu. Yatırımcı ilgisi yüksek olabilir."
        elif score >= 0.2:
            return "Olumlu haberler ağırlıkta. Pozitif momentum beklenir."
        elif score <= -0.5:
            return "Olumsuz haberler baskın. Dikkatli olunmalı."
        elif score <= -0.2:
            return "Negatif sentiment mevcut. Gelişmeleri takip edin."
        else:
            return "Haber akışı nötr. Teknik analize odaklanın."


class SocialSentiment:
    """
    Sosyal Medya Sentiment (Simüle)
    ===============================
    Twitter/X, StockTwits vb. sentiment'i
    """
    
    @staticmethod
    def get_social_sentiment(symbol: str) -> Dict[str, Any]:
        """Sosyal medya sentiment'i (simüle)"""
        import random
        
        # Simüle edilmiş veriler
        base_sentiment = random.uniform(-0.3, 0.5)
        
        return {
            "symbol": symbol,
            "twitter_sentiment": round(base_sentiment + random.uniform(-0.1, 0.1), 2),
            "twitter_volume": random.randint(100, 5000),
            "twitter_trend": random.choice(["rising", "stable", "falling"]),
            "stocktwits_sentiment": round(base_sentiment + random.uniform(-0.1, 0.1), 2),
            "stocktwits_volume": random.randint(50, 500),
            "reddit_mentions": random.randint(0, 100),
            "influencer_mentions": random.randint(0, 20),
            "overall_social_score": round(base_sentiment, 2),
            "buzz_level": random.choice(["low", "medium", "high", "viral"])
        }
