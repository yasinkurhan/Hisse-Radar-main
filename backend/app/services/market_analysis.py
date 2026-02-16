"""
HisseRadar Piyasa Analizi Modülü
=================================
Piyasa genişlik analizi, sektör rotasyonu, piyasa duyarlılığı
BIST genel durum değerlendirmesi
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class MarketBreadth:
    """
    Piyasa Genişlik Analizi
    =======================
    Piyasanın genel sağlığını ve yönünü ölçer
    """
    
    @staticmethod
    def calculate_advance_decline(
        stocks_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Yükselen/Düşen Hisse Analizi
        ============================
        
        A/D Line (Advance/Decline Line):
        - Yükselen hisse sayısı - Düşen hisse sayısı
        - Pozitif = Piyasa genişliyor
        - Negatif = Piyasa daralıyor
        """
        advancing = 0
        declining = 0
        unchanged = 0
        
        total_volume_up = 0
        total_volume_down = 0
        
        for stock in stocks_data:
            change = stock.get("change_percent", 0)
            volume = stock.get("volume", 0)
            
            if change > 0.1:
                advancing += 1
                total_volume_up += volume
            elif change < -0.1:
                declining += 1
                total_volume_down += volume
            else:
                unchanged += 1
        
        total = advancing + declining + unchanged
        
        if total == 0:
            return {"error": "veri_yok"}
        
        # A/D oranı
        ad_ratio = advancing / (declining + 0.1)
        
        # A/D çizgisi değeri
        ad_line = advancing - declining
        
        # McClellan Oscillator benzeri
        ad_pct = (advancing - declining) / total * 100
        
        # Hacim bazlı A/D
        if total_volume_down > 0:
            volume_ad_ratio = total_volume_up / total_volume_down
        else:
            volume_ad_ratio = 10 if total_volume_up > 0 else 1
        
        # Piyasa genişliği yorumu
        if ad_ratio > 2:
            breadth = "çok_güçlü_yükseliş"
            market_signal = "GÜÇLÜ AL"
        elif ad_ratio > 1.5:
            breadth = "güçlü_yükseliş"
            market_signal = "AL"
        elif ad_ratio > 1:
            breadth = "hafif_yükseliş"
            market_signal = "NÖTR"
        elif ad_ratio > 0.67:
            breadth = "hafif_düşüş"
            market_signal = "NÖTR"
        elif ad_ratio > 0.5:
            breadth = "güçlü_düşüş"
            market_signal = "SAT"
        else:
            breadth = "çok_güçlü_düşüş"
            market_signal = "GÜÇLÜ SAT"
        
        return {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "total": total,
            "ad_line": ad_line,
            "ad_ratio": round(ad_ratio, 2),
            "ad_percent": round(ad_pct, 1),
            "volume_ad_ratio": round(volume_ad_ratio, 2),
            "breadth": breadth,
            "market_signal": market_signal,
            "bullish_percent": round(advancing / total * 100, 1),
            "bearish_percent": round(declining / total * 100, 1)
        }
    
    @staticmethod
    def calculate_new_highs_lows(
        stocks_data: List[Dict[str, Any]],
        lookback_days: int = 52
    ) -> Dict[str, Any]:
        """
        Yeni Yüksek/Düşük Analizi
        =========================
        52 haftalık yüksek/düşük yapan hisse sayıları
        """
        new_highs = 0
        new_lows = 0
        near_high = 0  # %5 içinde
        near_low = 0   # %5 içinde
        
        for stock in stocks_data:
            current = stock.get("current_price", 0)
            high_52 = stock.get("week_52_high", 0)
            low_52 = stock.get("week_52_low", 0)
            
            if current <= 0 or high_52 <= 0 or low_52 <= 0:
                continue
            
            # Yeni yüksek kontrolü
            if current >= high_52 * 0.99:
                new_highs += 1
            elif current >= high_52 * 0.95:
                near_high += 1
            
            # Yeni düşük kontrolü
            if current <= low_52 * 1.01:
                new_lows += 1
            elif current <= low_52 * 1.05:
                near_low += 1
        
        total_signals = new_highs + new_lows + near_high + near_low
        
        # NH-NL oranı
        nh_nl_ratio = new_highs / (new_lows + 0.1)
        
        # Yorumlama
        if nh_nl_ratio > 3:
            trend = "güçlü_boğa_piyasası"
            signal = "GÜÇLÜ AL"
        elif nh_nl_ratio > 1.5:
            trend = "boğa_piyasası"
            signal = "AL"
        elif nh_nl_ratio > 0.67:
            trend = "yatay_piyasa"
            signal = "NÖTR"
        elif nh_nl_ratio > 0.33:
            trend = "ayı_piyasası"
            signal = "SAT"
        else:
            trend = "güçlü_ayı_piyasası"
            signal = "GÜÇLÜ SAT"
        
        return {
            "new_52_week_highs": new_highs,
            "new_52_week_lows": new_lows,
            "near_52_week_high": near_high,
            "near_52_week_low": near_low,
            "nh_nl_ratio": round(nh_nl_ratio, 2),
            "trend": trend,
            "signal": signal
        }
    
    @staticmethod
    def calculate_percent_above_ma(
        stocks_data: List[Dict[str, Any]],
        ma_periods: List[int] = [20, 50, 200]
    ) -> Dict[str, Any]:
        """
        MA Üzerindeki Hisse Yüzdesi
        ===========================
        Hisselerin kaçının belirli MA'ların üzerinde olduğu
        """
        results = {}
        
        for period in ma_periods:
            above_count = 0
            below_count = 0
            
            for stock in stocks_data:
                current = stock.get("current_price", 0)
                ma_value = stock.get(f"sma{period}") or stock.get(f"ma_{period}", 0)
                
                if current > 0 and ma_value > 0:
                    if current > ma_value:
                        above_count += 1
                    else:
                        below_count += 1
            
            total = above_count + below_count
            if total > 0:
                pct_above = (above_count / total) * 100
            else:
                pct_above = 50
            
            results[f"above_sma{period}"] = {
                "count": above_count,
                "percent": round(pct_above, 1)
            }
        
        # Genel trend yorumu
        pct_200 = results.get("above_sma200", {}).get("percent", 50)
        pct_50 = results.get("above_sma50", {}).get("percent", 50)
        pct_20 = results.get("above_sma20", {}).get("percent", 50)
        
        if pct_200 > 70 and pct_50 > 60:
            overall_trend = "güçlü_yükseliş_trendi"
        elif pct_200 > 50 and pct_50 > 50:
            overall_trend = "yükseliş_trendi"
        elif pct_200 < 30 and pct_50 < 40:
            overall_trend = "güçlü_düşüş_trendi"
        elif pct_200 < 50 and pct_50 < 50:
            overall_trend = "düşüş_trendi"
        else:
            overall_trend = "karışık_piyasa"
        
        # Kısa vadeli momentum
        if pct_20 > 70:
            short_term = "aşırı_alım"
        elif pct_20 > 50:
            short_term = "güçlü"
        elif pct_20 < 30:
            short_term = "aşırı_satım"
        else:
            short_term = "zayıf"
        
        results["overall_trend"] = overall_trend
        results["short_term_momentum"] = short_term
        
        return results


class SectorRotation:
    """
    Sektör Rotasyonu Analizi
    ========================
    Hangi sektörlerin öne çıktığını ve rotasyon trendlerini tespit eder
    """
    
    # BIST sektör tanımları
    SECTORS = {
        "Banka": ["AKBNK", "GARAN", "ISCTR", "YKBNK", "HALKB", "VAKBN", "QNBFB", "TSKB"],
        "Holding": ["SAHOL", "KCHOL", "KOZAL", "TAVHL", "DOHOL", "ANHYT", "ECZYT"],
        "Sanayi": ["EREGL", "KRDMD", "KARTN", "CEMTS", "ASELS", "TOASO", "FROTO", "OTKAR"],
        "Teknoloji": ["ASELS", "LOGO", "INDES", "ESCOM", "ARENA", "NETAS", "KFEIN"],
        "Perakende": ["BIMAS", "MGROS", "SOKM", "BIZIM", "MAVI", "VAKKO"],
        "Enerji": ["TUPRS", "AKSEN", "AYEN", "ZOREN", "AKSA", "AKENR"],
        "Telekomünikasyon": ["TCELL", "TTKOM", "TURK"],
        "İnşaat": ["ENKAI", "EKGYO", "ISGYO", "KLGYO"],
        "Havacılık": ["THYAO", "PGSUS", "TAVHL"],
        "Gıda": ["ULKER", "TATGD", "BANVT", "CCOLA", "AEFES"],
        "Tekstil": ["KORDS", "ARCLK", "VESBE"]
    }
    
    @staticmethod
    def analyze_sector_performance(
        stocks_data: List[Dict[str, Any]],
        period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Sektör performans analizi
        
        Args:
            stocks_data: Hisse verileri listesi
            period: 'daily', 'weekly', 'monthly'
        """
        sector_performance = defaultdict(lambda: {
            "stocks": [],
            "total_change": 0,
            "total_change_1w": 0,
            "total_change_1m": 0,
            "count": 0,
            "volume": 0,
            "advancing": 0,
            "declining": 0
        })
        
        # Hisseleri sektörlere ayır
        for stock in stocks_data:
            symbol = stock.get("symbol", "").replace(".IS", "")
            change = stock.get("change_percent", 0)
            change_1w = stock.get("change_1w", change) # Fallback to 1d
            change_1m = stock.get("change_1m", change) # Fallback to 1d
            volume = stock.get("volume", 0)
            
            # Sektör bul
            sector = "Diğer"
            for sec_name, sec_symbols in SectorRotation.SECTORS.items():
                if symbol in sec_symbols:
                    sector = sec_name
                    break
            
            sector_performance[sector]["stocks"].append(symbol)
            sector_performance[sector]["total_change"] += change
            sector_performance[sector]["total_change_1w"] += change_1w
            sector_performance[sector]["total_change_1m"] += change_1m
            sector_performance[sector]["count"] += 1
            sector_performance[sector]["volume"] += volume
            
            if change > 0:
                sector_performance[sector]["advancing"] += 1
            else:
                sector_performance[sector]["declining"] += 1
        
        # Sektör ortalamalarını hesapla
        sector_results = []
        total_market_1w = 0
        total_sectors = 0
        
        for sector, data in sector_performance.items():
            if data["count"] > 0:
                avg_change = data["total_change"] / data["count"]
                avg_change_1w = data["total_change_1w"] / data["count"]
                avg_change_1m = data["total_change_1m"] / data["count"]
                
                breadth = data["advancing"] / (data["count"]) * 100
                
                # Sektör gücü skoru
                strength_score = (avg_change * 10) + (breadth - 50)
                
                sector_results.append({
                    "sector": sector,
                    "avg_change_pct": round(avg_change, 2),
                    "performance_1d": round(avg_change, 2),
                    "performance_1w": round(avg_change_1w, 2),
                    "performance_1m": round(avg_change_1m, 2),
                    "stock_count": data["count"],
                    "total_volume": data["volume"],
                    "advancing": data["advancing"],
                    "declining": data["declining"],
                    "breadth_pct": round(breadth, 1),
                    "strength_score": round(strength_score, 1),
                    "stocks": data["stocks"][:5]  # İlk 5 hisse
                })
                
                total_market_1w += avg_change_1w
                total_sectors += 1
        
        # Relative Strength hesapla (1 haftalık performansa göre)
        avg_market_1w = total_market_1w / total_sectors if total_sectors > 0 else 0
        
        for s in sector_results:
            # RS = (Sector 1W - Market 1W) / 10
            # -1 ile 1 arasına normalize etmeye çalışıyoruz
            rs = (s["performance_1w"] - avg_market_1w) / 10
            s["relative_strength"] = round(rs, 2)
        
        # Performansa göre sırala
        sector_results.sort(key=lambda x: x["strength_score"], reverse=True)
        
        # En güçlü ve en zayıf sektörler
        leading_sectors = sector_results[:3]
        lagging_sectors = sector_results[-3:]
        
        # Rotasyon analizi
        rotation_signal = SectorRotation._analyze_rotation_phase(sector_results)
        
        return {
            "sectors": sector_results,
            "leading_sectors": leading_sectors,
            "lagging_sectors": lagging_sectors,
            "rotation_phase": rotation_signal["phase"],
            "rotation_signal": rotation_signal["signal"],
            "market_cycle": rotation_signal["cycle"],
            "analysis_period": period
        }
    
    @staticmethod
    def _analyze_rotation_phase(sector_results: List[Dict]) -> Dict[str, str]:
        """
        Sektör rotasyon fazı analizi
        
        Ekonomik döngü fazları:
        1. Erken Toparlanma: Teknoloji, Tüketici
        2. Orta Genişleme: Sanayi, Malzeme
        3. Geç Genişleme: Enerji, Temel Tüketim
        4. Erken Daralma: Sağlık, Defansif
        5. Geç Daralma: Holding, Nakit
        """
        # Sektör güç haritası
        sector_strength = {s["sector"]: s["strength_score"] for s in sector_results}
        
        # Döngüsel vs Defansif
        cyclical_sectors = ["Sanayi", "Teknoloji", "Havacılık", "İnşaat"]
        defensive_sectors = ["Gıda", "Telekomünikasyon", "Perakende"]
        
        cyclical_strength = sum(
            sector_strength.get(s, 0) for s in cyclical_sectors
        ) / len(cyclical_sectors)
        
        defensive_strength = sum(
            sector_strength.get(s, 0) for s in defensive_sectors
        ) / len(defensive_sectors)
        
        # Banka ve holding (ekonomik barometreler)
        financial_strength = (
            sector_strength.get("Banka", 0) + sector_strength.get("Holding", 0)
        ) / 2
        
        # Faz belirleme
        if cyclical_strength > 20 and financial_strength > 10:
            phase = "erken_genişleme"
            signal = "GÜÇLÜ AL"
            cycle = "Risk-on: Döngüsel hisselere yönel"
        elif cyclical_strength > 0 and financial_strength > 0:
            phase = "orta_genişleme"
            signal = "AL"
            cycle = "Büyüme devam ediyor"
        elif defensive_strength > cyclical_strength and cyclical_strength < 0:
            phase = "erken_daralma"
            signal = "DİKKATLİ OL"
            cycle = "Defansif sektörlere geç"
        elif defensive_strength > 0 and cyclical_strength < -10:
            phase = "geç_daralma"
            signal = "SAT"
            cycle = "Risk-off: Nakit pozisyonunu artır"
        elif cyclical_strength < -20:
            phase = "dip_oluşumu"
            signal = "BEKLE"
            cycle = "Dip yakın olabilir"
        else:
            phase = "karışık"
            signal = "NÖTR"
            cycle = "Net yön yok"
        
        return {
            "phase": phase,
            "signal": signal,
            "cycle": cycle,
            "cyclical_strength": round(cyclical_strength, 1),
            "defensive_strength": round(defensive_strength, 1),
            "financial_strength": round(financial_strength, 1)
        }
    
    @staticmethod
    def calculate_relative_strength(
        sector_returns: Dict[str, float],
        market_return: float
    ) -> Dict[str, Any]:
        """
        Sektör Göreceli Güç
        ===================
        Sektör performansının piyasaya göre karşılaştırması
        """
        relative_strength = {}
        
        for sector, ret in sector_returns.items():
            rs = ret - market_return
            
            if rs > 5:
                signal = "güçlü_outperform"
            elif rs > 2:
                signal = "outperform"
            elif rs < -5:
                signal = "güçlü_underperform"
            elif rs < -2:
                signal = "underperform"
            else:
                signal = "market_perform"
            
            relative_strength[sector] = {
                "sector_return": round(ret, 2),
                "relative_strength": round(rs, 2),
                "signal": signal
            }
        
        return relative_strength


class MarketSentiment:
    """
    Piyasa Duyarlılığı Analizi
    ==========================
    Korku/Açgözlülük ve piyasa psikolojisi ölçümleri
    """
    
    @staticmethod
    def calculate_fear_greed_index(
        market_data: Dict[str, Any],
        breadth_data: Dict[str, Any],
        volatility: float,
        put_call_ratio: float = None
    ) -> Dict[str, Any]:
        """
        Korku & Açgözlülük Endeksi (0-100)
        ==================================
        0-25: Aşırı Korku
        25-45: Korku
        45-55: Nötr
        55-75: Açgözlülük
        75-100: Aşırı Açgözlülük
        """
        scores = []
        components = {}
        
        # 1. Piyasa momentum (RSI bazlı)
        avg_rsi = market_data.get("avg_rsi", 50)
        if avg_rsi >= 70:
            momentum_score = 80
        elif avg_rsi >= 60:
            momentum_score = 65
        elif avg_rsi <= 30:
            momentum_score = 20
        elif avg_rsi <= 40:
            momentum_score = 35
        else:
            momentum_score = 50
        scores.append(momentum_score)
        components["market_momentum"] = momentum_score
        
        # 2. Piyasa genişliği
        breadth_pct = breadth_data.get("bullish_percent", 50)
        if breadth_pct >= 70:
            breadth_score = 80
        elif breadth_pct >= 60:
            breadth_score = 65
        elif breadth_pct <= 30:
            breadth_score = 20
        elif breadth_pct <= 40:
            breadth_score = 35
        else:
            breadth_score = 50
        scores.append(breadth_score)
        components["market_breadth"] = breadth_score
        
        # 3. Volatilite (VIX benzeri - ters ilişki)
        if volatility >= 40:
            vol_score = 15
        elif volatility >= 30:
            vol_score = 30
        elif volatility <= 15:
            vol_score = 80
        elif volatility <= 20:
            vol_score = 65
        else:
            vol_score = 50
        scores.append(vol_score)
        components["volatility"] = vol_score
        
        # 4. Yeni yüksek/düşük oranı
        nh_nl_ratio = breadth_data.get("nh_nl_ratio", 1)
        if nh_nl_ratio >= 3:
            nhnl_score = 85
        elif nh_nl_ratio >= 1.5:
            nhnl_score = 70
        elif nh_nl_ratio <= 0.33:
            nhnl_score = 15
        elif nh_nl_ratio <= 0.67:
            nhnl_score = 30
        else:
            nhnl_score = 50
        scores.append(nhnl_score)
        components["new_highs_lows"] = nhnl_score
        
        # 5. Put/Call oranı (varsa)
        if put_call_ratio is not None:
            if put_call_ratio >= 1.2:
                pc_score = 20  # Aşırı korku
            elif put_call_ratio >= 1:
                pc_score = 35
            elif put_call_ratio <= 0.6:
                pc_score = 80  # Aşırı açgözlülük
            elif put_call_ratio <= 0.8:
                pc_score = 65
            else:
                pc_score = 50
            scores.append(pc_score)
            components["put_call_ratio"] = pc_score
        
        # Genel endeks
        fear_greed_index = np.mean(scores)
        
        # Duyarlılık seviyesi
        if fear_greed_index >= 75:
            sentiment = "aşırı_açgözlülük"
            signal = "UYARI: Satış düşün"
            color = "red"
        elif fear_greed_index >= 55:
            sentiment = "açgözlülük"
            signal = "DİKKATLİ OL"
            color = "orange"
        elif fear_greed_index <= 25:
            sentiment = "aşırı_korku"
            signal = "FIRSAT: Alım düşün"
            color = "green"
        elif fear_greed_index <= 45:
            sentiment = "korku"
            signal = "Potansiyel fırsat"
            color = "lightgreen"
        else:
            sentiment = "nötr"
            signal = "Bekle ve gör"
            color = "gray"
        
        return {
            "fear_greed_index": round(fear_greed_index, 1),
            "sentiment": sentiment,
            "signal": signal,
            "color": color,
            "components": components,
            "interpretation": f"Piyasa şu an {sentiment} modunda"
        }
    
    @staticmethod
    def analyze_smart_money(
        stocks_data: List[Dict[str, Any]],
        index_change: float
    ) -> Dict[str, Any]:
        """
        Akıllı Para Analizi
        ===================
        Kurumsal yatırımcı davranışlarını tahmin et
        """
        # Yüksek hacimli hareketler
        high_volume_up = 0
        high_volume_down = 0
        normal_volume_up = 0
        normal_volume_down = 0
        
        for stock in stocks_data:
            change = stock.get("change_percent", 0)
            vol_ratio = stock.get("volume_ratio", 1)
            
            if vol_ratio > 2:  # Normalin 2 katından fazla hacim
                if change > 1:
                    high_volume_up += 1
                elif change < -1:
                    high_volume_down += 1
            else:
                if change > 0:
                    normal_volume_up += 1
                elif change < 0:
                    normal_volume_down += 1
        
        # Akıllı para göstergesi
        if high_volume_up > high_volume_down * 1.5:
            smart_money_signal = "kurumsal_alım"
            interpretation = "Yüksek hacimle alım görülüyor - Kurumsal ilgi var"
        elif high_volume_down > high_volume_up * 1.5:
            smart_money_signal = "kurumsal_satış"
            interpretation = "Yüksek hacimle satış - Kurumsal çıkış olabilir"
        elif high_volume_up > 0 and index_change < 0:
            smart_money_signal = "biriktirme"
            interpretation = "Düşen piyasada alım - Biriktirme olabilir"
        elif high_volume_down > 0 and index_change > 0:
            smart_money_signal = "dağıtım"
            interpretation = "Yükselen piyasada satış - Dağıtım olabilir"
        else:
            smart_money_signal = "belirsiz"
            interpretation = "Net kurumsal hareket görülmüyor"
        
        return {
            "signal": smart_money_signal,
            "interpretation": interpretation,
            "high_volume_buys": high_volume_up,
            "high_volume_sells": high_volume_down,
            "normal_volume_buys": normal_volume_up,
            "normal_volume_sells": normal_volume_down
        }


class MarketAnalyzer:
    """
    Piyasa Analizi Ana Sınıfı
    =========================
    Tüm piyasa analizlerini birleştirir
    """
    
    @staticmethod
    def full_market_analysis(
        stocks_data: List[Dict[str, Any]],
        index_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Kapsamlı piyasa analizi
        
        Args:
            stocks_data: Tüm hisse verileri
            index_data: Endeks verileri (opsiyonel)
        """
        # Piyasa genişliği
        breadth = MarketBreadth.calculate_advance_decline(stocks_data)
        
        # Yeni yüksek/düşükler
        nh_nl = MarketBreadth.calculate_new_highs_lows(stocks_data)
        
        # MA üzerindeki hisseler
        ma_analysis = MarketBreadth.calculate_percent_above_ma(stocks_data)
        
        # Sektör analizi
        sector_analysis = SectorRotation.analyze_sector_performance(stocks_data)
        
        # Duyarlılık
        avg_rsi = np.mean([s.get("rsi", 50) for s in stocks_data if s.get("rsi")])
        volatility = np.mean([s.get("atr_percent", 2) for s in stocks_data if s.get("atr_percent")])
        
        market_data = {"avg_rsi": avg_rsi}
        breadth_with_nhnl = {**breadth, "nh_nl_ratio": nh_nl.get("nh_nl_ratio", 1)}
        
        sentiment = MarketSentiment.calculate_fear_greed_index(
            market_data, breadth_with_nhnl, volatility
        )
        
        # Akıllı para
        index_change = index_data.get("change_percent", 0) if index_data else 0
        smart_money = MarketSentiment.analyze_smart_money(stocks_data, index_change)
        
        # Genel piyasa sinyali
        overall_signal = MarketAnalyzer._calculate_overall_signal(
            breadth, nh_nl, sentiment, sector_analysis
        )
        
        return {
            "market_breadth": breadth,
            "new_highs_lows": nh_nl,
            "ma_analysis": ma_analysis,
            "sector_analysis": sector_analysis,
            "sentiment": sentiment,
            "smart_money": smart_money,
            "overall_signal": overall_signal,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def _calculate_overall_signal(
        breadth: Dict, nh_nl: Dict, sentiment: Dict, sector: Dict
    ) -> Dict[str, Any]:
        """Genel piyasa sinyali hesapla"""
        scores = []
        
        # Breadth skoru
        ad_ratio = breadth.get("ad_ratio", 1)
        if ad_ratio > 1.5:
            scores.append(80)
        elif ad_ratio > 1:
            scores.append(60)
        elif ad_ratio < 0.67:
            scores.append(20)
        else:
            scores.append(40)
        
        # NH-NL skoru
        nhnl_ratio = nh_nl.get("nh_nl_ratio", 1)
        if nhnl_ratio > 2:
            scores.append(80)
        elif nhnl_ratio > 1:
            scores.append(60)
        elif nhnl_ratio < 0.5:
            scores.append(20)
        else:
            scores.append(40)
        
        # Sentiment skoru
        fg_index = sentiment.get("fear_greed_index", 50)
        scores.append(fg_index)
        
        # Sektör skoru
        rotation_signal = sector.get("rotation_signal", "NÖTR")
        if "AL" in rotation_signal:
            scores.append(70)
        elif "SAT" in rotation_signal:
            scores.append(30)
        else:
            scores.append(50)
        
        # Genel skor
        overall_score = np.mean(scores)
        
        if overall_score >= 70:
            signal = "GÜÇLÜ AL"
            recommendation = "Piyasa güçlü - Pozisyon artırılabilir"
        elif overall_score >= 55:
            signal = "AL"
            recommendation = "Piyasa olumlu - Seçici alım yapılabilir"
        elif overall_score <= 30:
            signal = "GÜÇLÜ SAT"
            recommendation = "Piyasa zayıf - Risk azalt"
        elif overall_score <= 45:
            signal = "SAT"
            recommendation = "Piyasa olumsuz - Dikkatli ol"
        else:
            signal = "NÖTR"
            recommendation = "Piyasa kararsız - Bekle"
        
        return {
            "signal": signal,
            "score": round(overall_score, 1),
            "recommendation": recommendation
        }
