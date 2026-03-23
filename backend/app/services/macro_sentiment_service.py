"""
HisseRadar Makro & Gündem Sentiment Servisi
============================================
Küresel jeopolitik olaylar, Türkiye ekonomisi, merkez bankası kararları,
emtia fiyatları ve döviz hareketlerini analiz ederek BIST üzerindeki
makro etkiyi ölçer.

Veri kaynakları: Google News RSS (ücretsiz, API key gerektirmez)
"""

import asyncio
import aiohttp
import feedparser
import re
import html
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import quote


# ─── MAKRO GÜNDEM ARAMA SORGULARI ──────────────────────────────────────────────
MACRO_QUERIES = [
    # Jeopolitik Riskler
    {
        "id": "geopolitical_war",
        "query": "savaş çatışma ateşkes yaptırım",
        "category": "Jeopolitik Risk",
        "base_impact": -0.6,
        "bist_sectors": ["savunma", "enerji", "ticaret"],
        "icon": "⚔️"
    },
    {
        "id": "middle_east",
        "query": "iran israel abd orta doğu gerilim",
        "category": "Orta Doğu",
        "base_impact": -0.7,
        "bist_sectors": ["enerji", "petrol", "ulaşım"],
        "icon": "🌍"
    },
    {
        "id": "russia_ukraine",
        "query": "rusya ukrayna savaş doğalgaz enerji",
        "category": "Rusya-Ukrayna",
        "base_impact": -0.5,
        "bist_sectors": ["enerji", "tahıl", "çelik"],
        "icon": "🇷🇺"
    },
    # Türkiye Ekonomisi
    {
        "id": "turkey_economy_positive",
        "query": "Türkiye ekonomi büyüme ihracat yatırım reform",
        "category": "Türkiye Ekonomi",
        "base_impact": 0.5,
        "bist_sectors": ["genel"],
        "icon": "🇹🇷"
    },
    {
        "id": "turkey_economy_negative",
        "query": "Türkiye enflasyon kur faiz baskı",
        "category": "Türkiye Makro",
        "base_impact": -0.4,
        "bist_sectors": ["bankacılık", "tüketim"],
        "icon": "📉"
    },
    # Merkez Bankaları
    {
        "id": "tcmb",
        "query": "TCMB merkez bankası faiz kararı para politikası",
        "category": "TCMB",
        "base_impact": 0.0,
        "bist_sectors": ["bankacılık", "gayrimenkul"],
        "icon": "🏦"
    },
    {
        "id": "fed_ecb",
        "query": "Fed ECB faiz artırım düşürme para politikası",
        "category": "Küresel MB",
        "base_impact": -0.2,
        "bist_sectors": ["bankacılık", "genel"],
        "icon": "🏛️"
    },
    # Emtia & Enerji
    {
        "id": "oil_energy",
        "query": "petrol Brent ham fiyat OPEC enerji",
        "category": "Enerji & Emtia",
        "base_impact": 0.0,
        "bist_sectors": ["enerji", "petrokimya", "taşımacılık"],
        "icon": "🛢️"
    },
    # Küresel Piyasalar
    {
        "id": "global_recession",
        "query": "resesyon kriz küresel piyasa çöküş korku",
        "category": "Küresel Risk",
        "base_impact": -0.6,
        "bist_sectors": ["genel"],
        "icon": "🌐"
    },
    {
        "id": "bist_positive",
        "query": "borsa istanbul BIST yükseliş rekor alım",
        "category": "BIST Akışı",
        "base_impact": 0.3,
        "bist_sectors": ["genel"],
        "icon": "📈"
    },
    {
        "id": "bist_negative",
        "query": "borsa istanbul BIST düşüş satış çıkış baskı",
        "category": "BIST Akışı",
        "base_impact": -0.3,
        "bist_sectors": ["genel"],
        "icon": "📉"
    },
    # Döviz
    {
        "id": "usd_try",
        "query": "dolar TL kur değer kaybı değer kazanımı",
        "category": "Döviz",
        "base_impact": 0.0,
        "bist_sectors": ["ihracatçılar", "ithalatçılar"],
        "icon": "💱"
    },
]

# ─── BIST ETKİ KELİMELERİ ──────────────────────────────────────────────────────
BIST_POSITIVE_TRIGGERS = {
    # Küresel olumlu
    "ateşkes": 0.8, "barış": 0.7, "anlaşma sağlandı": 0.7, "gerilim azaldı": 0.6,
    "müzakere başladı": 0.5,
    # Türkiye olumlu
    "büyüme hızlandı": 0.7, "ihracat arttı": 0.6, "yatırım geldi": 0.6,
    "reform paketi": 0.6, "enflasyon düştü": 0.7, "cari açık daraldı": 0.5,
    "kredi notu artırıldı": 0.8, "kredi notu yükseltildi": 0.8,
    "yabancı yatırım": 0.6, "net alım": 0.5,
    # Piyasa olumlu
    "rekor kırdı": 0.7, "tarihi zirve": 0.7, "güçlü başladı": 0.5,
    "yükseldi": 0.4, "pozitif ayrıştı": 0.5, "risk iştahı arttı": 0.6,
    "fed faiz indirdi": 0.6, "faiz indirimi": 0.5,
    # Enerji / emtia olumlu (Türkiye için)
    "petrol düştü": 0.5, "doğalgaz ucuzladı": 0.5, "emtia fiyatları geriledi": 0.4,
    "dolar geriledi": 0.5, "TL değer kazandı": 0.5,
}

BIST_NEGATIVE_TRIGGERS = {
    # Jeopolitik
    "savaş": -0.7, "çatışma": -0.6, "füze": -0.7, "bombardıman": -0.8,
    "yaptırım": -0.7, "ambargo": -0.7, "tehdit": -0.5, "gerilim tırmandı": -0.7,
    "saldırı": -0.6, "kriz": -0.5,
    # Türkiye olumsuz
    "enflasyon yükseldi": -0.6, "kur yükseldi": -0.5, "dolar yükseldi": -0.5,
    "faiz artırıldı": -0.4, "ekonomi küçüldü": -0.7, "cari açık büyüdü": -0.4,
    "kredi notu düşürüldü": -0.8, "riskli": -0.4, "baskı altında": -0.5,
    "satış baskısı": -0.6, "yabancı çıkışı": -0.6, "net satış": -0.5,
    # Küresel olumsuz
    "resesyon": -0.7, "çöküş": -0.8, "panik": -0.7, "korku endeksi": -0.6,
    "piyasalar çöktü": -0.8, "büyük düşüş": -0.7, "rekor düşük": -0.6,
    "fed faiz artırdı": -0.5, "merkez bankası sıkılaştırma": -0.4,
    # Enerji olumsuz (Türkiye için)
    "petrol yükseldi": -0.4, "doğalgaz fiyatı arttı": -0.4,
    "enerji krizi": -0.6, "arz kesintisi": -0.5,
}

# ─── MAKRO GÜNDEM KATEGORISINE GÖRE BIST ETKİSİ AÇIKLAMASI ────────────────────
IMPACT_EXPLANATIONS = {
    "Jeopolitik Risk": {
        "negative": "Bölgesel çatışmalar yabancı sermaye çıkışını tetikliyor, BIST'te satış baskısı oluşturuyor.",
        "neutral": "Jeopolitik gelişmeler izleniyor, sınırlı etki bekleniyor.",
        "positive": "Gerilimin azalması risk iştahını artırıyor, BIST'e sermaye girişi bekleniyor."
    },
    "Orta Doğu": {
        "negative": "Orta Doğu gerilimi petrol fiyatlarını yukarı itiyor, Türkiye'nin enerji ithalat maliyeti artıyor.",
        "neutral": "Bölgesel gelişmeler sınırlı BIST etkisi yaratıyor.",
        "positive": "Bölgede çatışmanın durması enerji fiyatlarını düşürüyor, Türkiye ekonomisi için olumlu."
    },
    "TCMB": {
        "negative": "Faiz artışı borçlanma maliyetlerini yükseltiyor, büyüme beklentisi zayıflıyor.",
        "neutral": "Para politikası değişmedi, mevcut koşullar devam ediyor.",
        "positive": "Faiz indirimi likiditeyi artırıyor, yatırım ortamı iyileşiyor."
    },
    "Küresel MB": {
        "negative": "Küresel sıkılaşma gelişen piyasalardan çıkış yarattı, BIST üzerinde baskı var.",
        "neutral": "Küresel merkez bankalarının tutumu beklentilerle uyumlu.",
        "positive": "Gevşeme sinyalleri risk iştahını canlandırıyor, gelişen piyasalara sermaye akıyor."
    },
    "Enerji & Emtia": {
        "negative": "Yüksek enerji fiyatları Türkiye'nin cari açığını büyütüyor, enflasyon baskısı artıyor.",
        "neutral": "Emtia fiyatlarında kayda değer harekat yok.",
        "positive": "Enerji fiyatlarındaki gerileme Türkiye'nin ithalat faturasını düşürüyor."
    },
    "Döviz": {
        "negative": "TL değer kaybı ithalat maliyetlerini artırıyor, enflasyon baskısı yaratıyor.",
        "neutral": "Döviz kurlarında belirgin bir hareket gözlemlenmiyor.",
        "positive": "TL'nin değer kazanması enflasyon beklentilerini düşürüyor."
    },
    "BIST Akışı": {
        "negative": "BIST'te genel satış baskısı var, yabancı yatırımcı çıkışı görülüyor.",
        "neutral": "BIST nötr bir seyir izliyor.",
        "positive": "BIST'te güçlü alım var, yabancı yatırımcı ilgisi artıyor."
    },
    "Küresel Risk": {
        "negative": "Küresel resesyon korkusu gelişen piyasaları baskılıyor, BIST de etkileniyor.",
        "neutral": "Küresel büyüme endişeleri mevcut ama sınırlı etkisi var.",
        "positive": "Resesyon endişeleri azalıyor, küresel büyüme görünümü iyileşiyor."
    },
    "Türkiye Ekonomi": {
        "negative": "Türkiye makro verileri hayal kırıklığı yarattı.",
        "neutral": "Türkiye ekonomik verileri beklentilere uygun geldi.",
        "positive": "Türkiye'nin güçlü büyüme performansı yabancı yatırımcı güvenini artırıyor."
    },
    "Türkiye Makro": {
        "negative": "Enflasyon ve kur baskısı BIST'teki şirketlerin maliyet yapısını zorluyor.",
        "neutral": "Türkiye makro ortamı mevcut fiyatlamalarla uyumlu görünüyor.",
        "positive": "Enflasyonla mücadelede olumlu ilerleme, piyasa güveni artıyor."
    },
    "Rusya-Ukrayna": {
        "negative": "Çatışmanın devamı enerji ve gıda fiyatlarını yüksek tutuyor, Türkiye etkileniyor.",
        "neutral": "Cephe hattında kayda değer değişiklik yok.",
        "positive": "Müzakere sinyalleri enerji piyasalarında rahatlama sağlıyor."
    },
}


class MacroSentimentService:
    """
    Makro Gündem Sentiment Servisi

    Küresel ve yerel haber akışlarını analiz ederek BIST üzerindeki
    makro etkiyi ölçer ve yatırımcılara bağlam sağlar.
    """

    _cache: Optional[Dict[str, Any]] = None
    _cache_time: Optional[datetime] = None
    CACHE_MINUTES = 30

    @classmethod
    async def get_macro_sentiment(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """Ana metod: makro sentiment analizini döndür (30 dk cache'li)"""
        now = datetime.now()
        if (
            not force_refresh
            and cls._cache is not None
            and cls._cache_time is not None
            and (now - cls._cache_time).total_seconds() < cls.CACHE_MINUTES * 60
        ):
            return cls._cache

        result = await cls._fetch_and_analyze()
        cls._cache = result
        cls._cache_time = now
        return result

    @classmethod
    async def _fetch_and_analyze(cls) -> Dict[str, Any]:
        """Haberleri çek, analiz et, BIST etkisini hesapla"""
        all_headlines: List[Dict[str, Any]] = []

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20),
            headers={"User-Agent": "Mozilla/5.0 (compatible; HisseRadar/1.0)"}
        ) as session:
            tasks = [cls._fetch_query(session, q) for q in MACRO_QUERIES]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for query_cfg, items in zip(MACRO_QUERIES, results):
            if isinstance(items, Exception):
                continue
            for item in items:
                item["query_id"] = query_cfg["id"]
                item["category"] = query_cfg["category"]
                item["icon"] = query_cfg["icon"]
                all_headlines.append(item)

        # Tekrarlı başlıkları temizle (benzer başlıklar)
        all_headlines = cls._deduplicate(all_headlines)

        # Her habere BIST etki skoru ver
        scored = [cls._score_headline(h) for h in all_headlines]

        # Kategoriye göre grupla
        by_category = cls._group_by_category(scored)

        # Genel makro skor hesapla
        macro_score, confidence = cls._compute_macro_score(scored)

        # Risk ve pozitif faktörleri ayır
        risk_factors = [h for h in scored if h["bist_impact_score"] < -0.25]
        positive_factors = [h for h in scored if h["bist_impact_score"] > 0.25]
        neutral_factors = [h for h in scored if -0.25 <= h["bist_impact_score"] <= 0.25]

        # Sırala
        risk_factors.sort(key=lambda x: x["bist_impact_score"])
        positive_factors.sort(key=lambda x: x["bist_impact_score"], reverse=True)

        # Genel etki etiketi
        macro_label, macro_color, bist_impact = cls._label_macro(macro_score)

        # Öneri metni
        recommendation = cls._generate_recommendation(
            macro_score, risk_factors, positive_factors, by_category
        )

        return {
            "macro_score": round(macro_score, 3),
            "macro_label": macro_label,
            "macro_color": macro_color,
            "bist_impact": bist_impact,
            "confidence": round(confidence, 2),
            "recommendation": recommendation,
            "risk_factors": risk_factors[:8],
            "positive_factors": positive_factors[:6],
            "neutral_factors": neutral_factors[:4],
            "by_category": by_category,
            "total_headlines": len(scored),
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cache_valid_until": (
                datetime.now() + timedelta(minutes=cls.CACHE_MINUTES)
            ).strftime("%H:%M"),
        }

    @staticmethod
    async def _fetch_query(
        session: aiohttp.ClientSession, query_cfg: Dict
    ) -> List[Dict[str, Any]]:
        """Google News RSS'ten belirli bir sorgu için haberleri çek"""
        q = quote(query_cfg["query"])
        url = (
            f"https://news.google.com/rss/search"
            f"?q={q}&hl=tr&gl=TR&ceid=TR:tr"
        )
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                text = await resp.text()

            feed = feedparser.parse(text)
            items = []
            cutoff = datetime.now() - timedelta(days=7)

            for entry in feed.entries[:10]:
                title = _clean_html(entry.get("title", ""))
                summary = _clean_html(entry.get("summary", ""))
                source = entry.get("source", {}).get("title", "Bilinmeyen")
                pub = _parse_date(entry.get("published_parsed"))

                if pub and pub < cutoff:
                    continue

                items.append({
                    "title": title,
                    "summary": summary[:200] if summary else "",
                    "source": source,
                    "date": pub.strftime("%Y-%m-%d %H:%M") if pub else "",
                    "url": entry.get("link", ""),
                    "age_hours": (
                        (datetime.now() - pub).total_seconds() / 3600
                        if pub else 168
                    ),
                })
            return items
        except Exception:
            return []

    @staticmethod
    def _score_headline(item: Dict[str, Any]) -> Dict[str, Any]:
        """Tek bir haberin BIST etki skorunu hesapla"""
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()

        pos_score = 0.0
        neg_score = 0.0
        matched_keywords: List[str] = []

        for phrase, weight in BIST_POSITIVE_TRIGGERS.items():
            if phrase in text:
                pos_score += weight
                matched_keywords.append(f"+{phrase}")

        for phrase, weight in BIST_NEGATIVE_TRIGGERS.items():
            if phrase in text:
                neg_score += abs(weight)
                matched_keywords.append(f"-{phrase}")

        raw = pos_score - neg_score
        # Normalize
        bist_score = math.tanh(raw / 2.0)

        # Taze haberlere daha fazla ağırlık ver
        age_h = item.get("age_hours", 48)
        freshness = max(0.3, 1.0 - age_h / 168)  # 1 hafta içinde doğrusal azalım

        weighted_score = bist_score * freshness

        # İnsan-okunabilir etki
        if weighted_score >= 0.3:
            impact_label = "Olumlu"
            impact_color = "green"
        elif weighted_score >= 0.1:
            impact_label = "Hafif Olumlu"
            impact_color = "emerald"
        elif weighted_score <= -0.3:
            impact_label = "Olumsuz"
            impact_color = "red"
        elif weighted_score <= -0.1:
            impact_label = "Hafif Olumsuz"
            impact_color = "orange"
        else:
            impact_label = "Nötr"
            impact_color = "gray"

        return {
            **item,
            "bist_impact_score": round(weighted_score, 3),
            "impact_label": impact_label,
            "impact_color": impact_color,
            "matched_keywords": matched_keywords[:5],
        }

    @staticmethod
    def _compute_macro_score(
        scored: List[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """Ağırlıklı ortalama makro skor"""
        if not scored:
            return 0.0, 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for item in scored:
            # Taze haberlere fazla ağırlık
            age_h = item.get("age_hours", 48)
            weight = max(0.2, 1.0 - age_h / 168)
            # Güçlü sinyallere ekstra ağırlık
            abs_score = abs(item["bist_impact_score"])
            if abs_score > 0.3:
                weight *= 1.5

            weighted_sum += item["bist_impact_score"] * weight
            total_weight += weight

        macro_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        # Confidence: ne kadar haberin anlamlı sinyal verdiğine dair
        meaningful = sum(1 for s in scored if abs(s["bist_impact_score"]) > 0.1)
        confidence = min(1.0, meaningful / max(len(scored), 1))

        return macro_score, confidence

    @staticmethod
    def _label_macro(score: float) -> Tuple[str, str, str]:
        """Skor → etiket, renk, BIST etki yönü"""
        if score >= 0.4:
            return "Çok Olumlu", "emerald", "positive"
        elif score >= 0.15:
            return "Olumlu", "green", "positive"
        elif score >= -0.15:
            return "Nötr", "gray", "neutral"
        elif score >= -0.4:
            return "Riskli", "orange", "negative"
        else:
            return "Çok Riskli", "red", "negative"

    @staticmethod
    def _group_by_category(
        scored: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Kategoriye göre grupla ve özet çıkar"""
        groups: Dict[str, List[Dict]] = {}
        for item in scored:
            cat = item.get("category", "Diğer")
            groups.setdefault(cat, []).append(item)

        result = {}
        for cat, items in groups.items():
            scores = [i["bist_impact_score"] for i in items]
            avg = sum(scores) / len(scores)
            # Kategorinin genel yönü
            if avg >= 0.1:
                direction = "positive"
            elif avg <= -0.1:
                direction = "negative"
            else:
                direction = "neutral"
            # Açıklama
            exp_map = IMPACT_EXPLANATIONS.get(cat, {})
            explanation = exp_map.get(direction, "")
            # En güncel haberler
            fresh = sorted(items, key=lambda x: x.get("age_hours", 999))[:3]
            result[cat] = {
                "avg_score": round(avg, 3),
                "direction": direction,
                "count": len(items),
                "explanation": explanation,
                "top_headlines": [{"title": h["title"], "source": h["source"], "date": h["date"], "impact": h["impact_label"]} for h in fresh],
                "icon": items[0].get("icon", "📰") if items else "📰",
            }
        return result

    @staticmethod
    def _generate_recommendation(
        macro_score: float,
        risk_factors: List[Dict],
        positive_factors: List[Dict],
        by_category: Dict[str, Dict],
    ) -> str:
        """BIST gündem tabanlı yatırımcı tavsiyesi metni oluştur"""
        lines = []

        # Ana ton
        if macro_score <= -0.4:
            lines.append(
                "⚠️ Makro gündem BIST açısından yüksek risk içeriyor. "
                "Jeopolitik gerilimler ve/veya makroekonomik baskılar "
                "yabancı sermaye çıkışını tetikleyebilir."
            )
        elif macro_score <= -0.15:
            lines.append(
                "🔶 Gündem BIST üzerinde olumsuz baskı oluşturuyor. "
                "Portföy koruması öne çıkabilir."
            )
        elif macro_score >= 0.4:
            lines.append(
                "✅ Makro gündem BIST açısından oldukça destekleyici görünüyor. "
                "Risk iştahı yüksek, yabancı sermaye girişi hızlanabilir."
            )
        elif macro_score >= 0.15:
            lines.append(
                "🟢 Gündem BIST için nispeten olumlu. Seçici alımlar öne çıkabilir."
            )
        else:
            lines.append(
                "⚪ Gündem görece nötr. Büyük yönsel hareketler için katalizör az."
            )

        # Risk faktörü ekle
        if risk_factors:
            top_risk = risk_factors[0]["title"][:80]
            lines.append(f"Öne çıkan risk: \"{top_risk}\"")

        # Olumlu faktör ekle
        if positive_factors:
            top_pos = positive_factors[0]["title"][:80]
            lines.append(f"Olumlu gelişme: \"{top_pos}\"")

        # Sektörel tavsiye
        sector_advices = []
        geo_cat = by_category.get("Jeopolitik Risk", {})
        if geo_cat.get("direction") == "negative":
            sector_advices.append("savunma/güvenlik hisselerini izleyin")
        energy_cat = by_category.get("Enerji & Emtia", {})
        if energy_cat.get("direction") == "negative":
            sector_advices.append("enerji ithalatçısı sektörler (CAL, AYGAZ, TUPRS) baskı altında olabilir")
        elif energy_cat.get("direction") == "positive":
            sector_advices.append("enerji fiyatlarının gerilemesi Türkiye ekonomisi için maliyet avantajı sağlar")
        tcmb_cat = by_category.get("TCMB", {})
        if tcmb_cat.get("direction") == "positive":
            sector_advices.append("faiz indirimi beklentisi bankacılık ve GYO sektörünü destekleyebilir")

        if sector_advices:
            lines.append("Sektör notu: " + "; ".join(sector_advices[:2]) + ".")

        return " ".join(lines)

    @staticmethod
    def _deduplicate(headlines: List[Dict]) -> List[Dict]:
        """Çok benzer başlıkları filtrele"""
        seen: List[str] = []
        unique = []
        for h in headlines:
            title_words = set(h["title"].lower().split())
            is_dup = False
            for s in seen:
                s_words = set(s.lower().split())
                overlap = len(title_words & s_words) / max(len(title_words | s_words), 1)
                if overlap > 0.6:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(h)
                seen.append(h["title"])
        return unique


# ─── YARDIMCI FONKSİYONLAR ──────────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(parsed_time) -> Optional[datetime]:
    try:
        if parsed_time and hasattr(parsed_time, "tm_year"):
            return datetime(*parsed_time[:6])
    except Exception:
        pass
    return None


# ─── Singleton getter ──────────────────────────────────────────────────────────

_instance: Optional[MacroSentimentService] = None


def get_macro_service() -> MacroSentimentService:
    global _instance
    if _instance is None:
        _instance = MacroSentimentService()
    return _instance
