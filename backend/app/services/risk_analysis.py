"""
HisseRadar Risk Analizi Modülü
===============================
Sharpe Ratio, Maximum Drawdown, Value at Risk (VaR), Beta ve daha fazlası
Profesyonel risk yönetimi araçları
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats


class RiskMetrics:
    """
    Risk Metrikleri Hesaplama Sınıfı
    =================================
    Portföy ve hisse bazında risk analizi
    """
    
    # Risk-free rate (TCMB faiz oranı tahmini - yıllık)
    RISK_FREE_RATE = 0.45  # %45 (Türkiye için yüksek faiz ortamı)
    TRADING_DAYS = 252  # Yıllık işlem günü
    
    @staticmethod
    def calculate_returns(prices: pd.Series, period: str = "daily") -> pd.Series:
        """
        Getiri hesapla
        
        Args:
            prices: Fiyat serisi
            period: 'daily', 'weekly', 'monthly'
        """
        if period == "daily":
            return prices.pct_change().dropna()
        elif period == "weekly":
            return prices.resample('W').last().pct_change().dropna()
        elif period == "monthly":
            return prices.resample('M').last().pct_change().dropna()
        return prices.pct_change().dropna()
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = None,
        annualize: bool = True
    ) -> Dict[str, float]:
        """
        Sharpe Oranı Hesapla
        ====================
        Risk ayarlı getiri ölçümü
        
        Sharpe = (Rp - Rf) / σp
        
        Yorumlama:
        - > 1.0: İyi
        - > 2.0: Çok iyi
        - > 3.0: Mükemmel
        - < 0: Negatif getiri
        
        Args:
            returns: Getiri serisi
            risk_free_rate: Risksiz faiz oranı (yıllık)
            annualize: Yıllıklaştır
            
        Returns:
            Sharpe oranı ve bileşenleri
        """
        if len(returns) < 5:
            return {"sharpe_ratio": 0, "interpretation": "yetersiz_veri"}
        
        rf = risk_free_rate if risk_free_rate else RiskMetrics.RISK_FREE_RATE
        
        # Günlük risksiz getiri
        daily_rf = rf / RiskMetrics.TRADING_DAYS
        
        # Ortalama günlük getiri
        mean_return = returns.mean()
        
        # Getiri volatilitesi (standart sapma)
        std_return = returns.std()
        
        if std_return == 0:
            return {"sharpe_ratio": 0, "interpretation": "sıfır_volatilite"}
        
        # Günlük Sharpe
        daily_sharpe = (mean_return - daily_rf) / std_return
        
        # Yıllıklaştırılmış Sharpe
        if annualize:
            sharpe = daily_sharpe * np.sqrt(RiskMetrics.TRADING_DAYS)
        else:
            sharpe = daily_sharpe
        
        # Yorumlama
        if sharpe >= 3:
            interpretation = "mükemmel"
        elif sharpe >= 2:
            interpretation = "çok_iyi"
        elif sharpe >= 1:
            interpretation = "iyi"
        elif sharpe >= 0.5:
            interpretation = "orta"
        elif sharpe >= 0:
            interpretation = "zayıf"
        else:
            interpretation = "negatif"
        
        # Yıllıklaştırılmış getiri ve volatilite
        annualized_return = mean_return * RiskMetrics.TRADING_DAYS
        annualized_volatility = std_return * np.sqrt(RiskMetrics.TRADING_DAYS)
        
        return {
            "sharpe_ratio": round(sharpe, 3),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "annualized_volatility_pct": round(annualized_volatility * 100, 2),
            "daily_return_pct": round(mean_return * 100, 4),
            "daily_volatility_pct": round(std_return * 100, 4),
            "interpretation": interpretation,
            "risk_free_rate_used": rf
        }
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = None,
        target_return: float = 0
    ) -> Dict[str, float]:
        """
        Sortino Oranı Hesapla
        =====================
        Sadece aşağı yönlü riski dikkate alan Sharpe alternatifi
        
        Sortino = (Rp - Rt) / Downside Deviation
        
        Sharpe'dan farkı: Sadece negatif getiriler risk olarak kabul edilir
        """
        if len(returns) < 5:
            return {"sortino_ratio": 0, "interpretation": "yetersiz_veri"}
        
        rf = risk_free_rate if risk_free_rate else RiskMetrics.RISK_FREE_RATE
        daily_rf = rf / RiskMetrics.TRADING_DAYS
        
        mean_return = returns.mean()
        
        # Downside deviation (sadece negatif sapmalar)
        negative_returns = returns[returns < target_return]
        if len(negative_returns) == 0:
            downside_deviation = 0.0001  # Sıfıra bölme engeli
        else:
            downside_deviation = np.sqrt(np.mean(negative_returns ** 2))
        
        # Sortino oranı
        sortino = (mean_return - daily_rf) / downside_deviation * np.sqrt(RiskMetrics.TRADING_DAYS)
        
        # Yorumlama
        if sortino >= 3:
            interpretation = "mükemmel"
        elif sortino >= 2:
            interpretation = "çok_iyi"
        elif sortino >= 1:
            interpretation = "iyi"
        elif sortino >= 0:
            interpretation = "orta"
        else:
            interpretation = "zayıf"
        
        return {
            "sortino_ratio": round(sortino, 3),
            "downside_deviation_pct": round(downside_deviation * 100 * np.sqrt(RiskMetrics.TRADING_DAYS), 2),
            "interpretation": interpretation
        }
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> Dict[str, Any]:
        """
        Maximum Drawdown (MDD) Hesapla
        ==============================
        En yüksek noktadan en düşük noktaya düşüş
        
        MDD = (Tepe - Dip) / Tepe
        
        Yorumlama:
        - < %10: Düşük risk
        - %10-%20: Orta risk
        - %20-%30: Yüksek risk
        - > %30: Çok yüksek risk
        """
        if len(prices) < 5:
            return {"max_drawdown_pct": 0, "interpretation": "yetersiz_veri"}
        
        # Kümülatif maksimum
        rolling_max = prices.expanding().max()
        
        # Drawdown serisi
        drawdowns = (prices - rolling_max) / rolling_max
        
        # Maximum drawdown
        max_dd = drawdowns.min()
        max_dd_pct = abs(max_dd) * 100
        
        # MDD tarihleri
        max_dd_idx = drawdowns.idxmin()
        peak_idx = prices.loc[:max_dd_idx].idxmax()
        
        # Toparlanma süresi (varsa)
        recovery_idx = None
        peak_value = prices.loc[peak_idx]
        after_trough = prices.loc[max_dd_idx:]
        recovered = after_trough[after_trough >= peak_value]
        if len(recovered) > 0:
            recovery_idx = recovered.index[0]
        
        # Güncel drawdown
        current_dd = drawdowns.iloc[-1]
        current_dd_pct = abs(current_dd) * 100
        
        # Yorumlama
        if max_dd_pct < 10:
            interpretation = "düşük_risk"
        elif max_dd_pct < 20:
            interpretation = "orta_risk"
        elif max_dd_pct < 30:
            interpretation = "yüksek_risk"
        else:
            interpretation = "çok_yüksek_risk"
        
        return {
            "max_drawdown_pct": round(max_dd_pct, 2),
            "current_drawdown_pct": round(current_dd_pct, 2),
            "peak_date": str(peak_idx) if peak_idx else None,
            "trough_date": str(max_dd_idx) if max_dd_idx else None,
            "recovery_date": str(recovery_idx) if recovery_idx else None,
            "peak_price": round(float(prices.loc[peak_idx]), 2) if peak_idx else None,
            "trough_price": round(float(prices.loc[max_dd_idx]), 2) if max_dd_idx else None,
            "interpretation": interpretation,
            "is_recovered": recovery_idx is not None,
            "in_drawdown": current_dd_pct > 5
        }
    
    @staticmethod
    def calculate_var(
        returns: pd.Series,
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        method: str = "historical"
    ) -> Dict[str, float]:
        """
        Value at Risk (VaR) Hesapla
        ===========================
        Belirli bir güven düzeyinde maksimum kayıp tahmini
        
        Args:
            returns: Getiri serisi
            confidence_level: Güven düzeyi (0.95 = %95)
            time_horizon: Zaman ufku (gün)
            method: 'historical', 'parametric', 'monte_carlo'
            
        Returns:
            VaR değerleri
        """
        if len(returns) < 30:
            return {"var_pct": 0, "interpretation": "yetersiz_veri"}
        
        if method == "historical":
            # Tarihi VaR - gerçek dağılımı kullan
            var = np.percentile(returns, (1 - confidence_level) * 100)
            
        elif method == "parametric":
            # Parametrik VaR - normal dağılım varsayımı
            mean = returns.mean()
            std = returns.std()
            z_score = stats.norm.ppf(1 - confidence_level)
            var = mean + z_score * std
            
        elif method == "monte_carlo":
            # Monte Carlo VaR
            mean = returns.mean()
            std = returns.std()
            simulations = np.random.normal(mean, std, 10000)
            var = np.percentile(simulations, (1 - confidence_level) * 100)
        else:
            var = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Zaman ufkuna göre ölçekle
        var_scaled = var * np.sqrt(time_horizon)
        var_pct = abs(var_scaled) * 100
        
        # Conditional VaR (Expected Shortfall)
        cvar = returns[returns <= var].mean()
        cvar_pct = abs(cvar) * 100 if not pd.isna(cvar) else var_pct * 1.2
        
        # Yorumlama
        if var_pct < 2:
            interpretation = "düşük_risk"
        elif var_pct < 4:
            interpretation = "orta_risk"
        elif var_pct < 6:
            interpretation = "yüksek_risk"
        else:
            interpretation = "çok_yüksek_risk"
        
        return {
            "var_pct": round(var_pct, 2),
            "cvar_pct": round(cvar_pct, 2),
            "confidence_level": confidence_level,
            "time_horizon_days": time_horizon,
            "method": method,
            "interpretation": interpretation,
            "explanation": f"%{confidence_level*100:.0f} güvenle {time_horizon} günde maksimum %{var_pct:.2f} kayıp beklenir"
        }
    
    @staticmethod
    def calculate_beta(
        stock_returns: pd.Series,
        market_returns: pd.Series
    ) -> Dict[str, float]:
        """
        Beta Katsayısı Hesapla
        ======================
        Hissenin piyasaya göre duyarlılığı
        
        Beta = Cov(Ri, Rm) / Var(Rm)
        
        Yorumlama:
        - Beta > 1: Piyasadan daha volatil
        - Beta = 1: Piyasa ile aynı hareket
        - Beta < 1: Piyasadan daha az volatil
        - Beta < 0: Piyasa ile ters yönlü
        """
        if len(stock_returns) < 20 or len(market_returns) < 20:
            return {"beta": 1, "interpretation": "yetersiz_veri"}
        
        # Serileri hizala
        aligned = pd.concat([stock_returns, market_returns], axis=1).dropna()
        if len(aligned) < 20:
            return {"beta": 1, "interpretation": "yetersiz_veri"}
        
        stock_ret = aligned.iloc[:, 0]
        market_ret = aligned.iloc[:, 1]
        
        # Kovaryans ve varyans
        covariance = stock_ret.cov(market_ret)
        market_variance = market_ret.var()
        
        if market_variance == 0:
            return {"beta": 1, "interpretation": "sıfır_varyans"}
        
        beta = covariance / market_variance
        
        # R-squared (determinasyon katsayısı)
        correlation = stock_ret.corr(market_ret)
        r_squared = correlation ** 2
        
        # Alpha (Jensen's Alpha)
        expected_return = stock_ret.mean()
        market_expected = market_ret.mean()
        rf_daily = RiskMetrics.RISK_FREE_RATE / RiskMetrics.TRADING_DAYS
        alpha = expected_return - rf_daily - beta * (market_expected - rf_daily)
        alpha_annualized = alpha * RiskMetrics.TRADING_DAYS
        
        # Yorumlama
        if beta > 1.5:
            interpretation = "çok_agresif"
        elif beta > 1.2:
            interpretation = "agresif"
        elif beta > 0.8:
            interpretation = "piyasa_paraleli"
        elif beta > 0.5:
            interpretation = "defansif"
        elif beta > 0:
            interpretation = "çok_defansif"
        else:
            interpretation = "ters_yönlü"
        
        return {
            "beta": round(beta, 3),
            "alpha_annualized_pct": round(alpha_annualized * 100, 2),
            "r_squared": round(r_squared, 3),
            "correlation": round(correlation, 3),
            "interpretation": interpretation,
            "volatility_comparison": "piyasadan_yüksek" if beta > 1 else "piyasadan_düşük"
        }
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        prices: pd.Series
    ) -> Dict[str, float]:
        """
        Calmar Oranı
        ============
        Getiri / Maximum Drawdown
        
        Yüksek değer daha iyi risk-getiri dengesi
        """
        mdd_result = RiskMetrics.calculate_max_drawdown(prices)
        mdd = mdd_result["max_drawdown_pct"] / 100
        
        if mdd == 0:
            return {"calmar_ratio": 0, "interpretation": "hesaplanamadı"}
        
        annualized_return = returns.mean() * RiskMetrics.TRADING_DAYS
        calmar = annualized_return / mdd
        
        if calmar >= 3:
            interpretation = "mükemmel"
        elif calmar >= 2:
            interpretation = "çok_iyi"
        elif calmar >= 1:
            interpretation = "iyi"
        elif calmar >= 0.5:
            interpretation = "orta"
        else:
            interpretation = "zayıf"
        
        return {
            "calmar_ratio": round(calmar, 3),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "max_drawdown_pct": round(mdd * 100, 2),
            "interpretation": interpretation
        }


class RiskAnalyzer:
    """
    Risk Analizi Ana Sınıfı
    =======================
    Tüm risk metriklerini birleştirir
    """
    
    @staticmethod
    def full_risk_analysis(
        prices: pd.Series,
        market_prices: pd.Series = None,
        volume: pd.Series = None
    ) -> Dict[str, Any]:
        """
        Kapsamlı risk analizi
        
        Args:
            prices: Hisse fiyat serisi
            market_prices: Piyasa endeks fiyatları (opsiyonel)
            volume: Hacim serisi (opsiyonel)
            
        Returns:
            Tüm risk metrikleri
        """
        returns = RiskMetrics.calculate_returns(prices)
        
        # Temel risk metrikleri
        sharpe = RiskMetrics.calculate_sharpe_ratio(returns)
        sortino = RiskMetrics.calculate_sortino_ratio(returns)
        max_dd = RiskMetrics.calculate_max_drawdown(prices)
        var_95 = RiskMetrics.calculate_var(returns, 0.95)
        var_99 = RiskMetrics.calculate_var(returns, 0.99)
        calmar = RiskMetrics.calculate_calmar_ratio(returns, prices)
        
        # Beta (piyasa verisi varsa)
        if market_prices is not None and len(market_prices) > 20:
            market_returns = RiskMetrics.calculate_returns(market_prices)
            beta_analysis = RiskMetrics.calculate_beta(returns, market_returns)
        else:
            beta_analysis = {"beta": 1, "interpretation": "piyasa_verisi_yok"}
        
        # Volatilite analizi
        volatility = RiskAnalyzer._analyze_volatility(returns)
        
        # Getiri dağılımı
        distribution = RiskAnalyzer._analyze_return_distribution(returns)
        
        # Risk skoru (0-100)
        risk_score = RiskAnalyzer._calculate_risk_score(
            sharpe, max_dd, var_95, volatility
        )
        
        return {
            "risk_score": risk_score,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "var_95": var_95,
            "var_99": var_99,
            "calmar_ratio": calmar,
            "beta_analysis": beta_analysis,
            "volatility": volatility,
            "return_distribution": distribution,
            "risk_level": RiskAnalyzer._get_risk_level(risk_score),
            "recommendation": RiskAnalyzer._get_risk_recommendation(risk_score, max_dd, sharpe)
        }
    
    @staticmethod
    def _analyze_volatility(returns: pd.Series) -> Dict[str, Any]:
        """Volatilite detaylı analizi"""
        if len(returns) < 20:
            return {"level": "belirsiz", "annualized_pct": 0}
        
        # Günlük volatilite
        daily_vol = returns.std()
        
        # Yıllıklaştırılmış volatilite
        annual_vol = daily_vol * np.sqrt(RiskMetrics.TRADING_DAYS)
        annual_vol_pct = annual_vol * 100
        
        # Volatilite trendi (son 20 vs önceki 20)
        if len(returns) >= 40:
            recent_vol = returns.tail(20).std()
            older_vol = returns.iloc[-40:-20].std()
            vol_trend = "artıyor" if recent_vol > older_vol * 1.1 else (
                "azalıyor" if recent_vol < older_vol * 0.9 else "stabil"
            )
        else:
            vol_trend = "belirsiz"
        
        # Volatilite seviyesi (BIST için)
        if annual_vol_pct > 60:
            level = "çok_yüksek"
        elif annual_vol_pct > 40:
            level = "yüksek"
        elif annual_vol_pct > 25:
            level = "orta"
        else:
            level = "düşük"
        
        return {
            "daily_pct": round(daily_vol * 100, 4),
            "annualized_pct": round(annual_vol_pct, 2),
            "level": level,
            "trend": vol_trend
        }
    
    @staticmethod
    def _analyze_return_distribution(returns: pd.Series) -> Dict[str, Any]:
        """Getiri dağılımı analizi"""
        if len(returns) < 20:
            return {"skewness": 0, "kurtosis": 0}
        
        # Çarpıklık (skewness)
        skewness = returns.skew()
        
        # Basıklık (kurtosis)
        kurtosis = returns.kurtosis()
        
        # Normal dağılım testi (Jarque-Bera)
        try:
            jb_stat, jb_pvalue = stats.jarque_bera(returns.dropna())
            is_normal = jb_pvalue > 0.05
        except:
            jb_stat, jb_pvalue = 0, 1
            is_normal = True
        
        # Yorumlama
        skew_interpretation = "pozitif_çarpık" if skewness > 0.5 else (
            "negatif_çarpık" if skewness < -0.5 else "simetrik"
        )
        
        kurtosis_interpretation = "kalın_kuyruk" if kurtosis > 3 else (
            "ince_kuyruk" if kurtosis < -1 else "normal"
        )
        
        return {
            "skewness": round(skewness, 3),
            "kurtosis": round(kurtosis, 3),
            "skew_interpretation": skew_interpretation,
            "kurtosis_interpretation": kurtosis_interpretation,
            "is_normal_distribution": is_normal,
            "jarque_bera_pvalue": round(jb_pvalue, 4),
            "positive_days_pct": round((returns > 0).mean() * 100, 1),
            "negative_days_pct": round((returns < 0).mean() * 100, 1)
        }
    
    @staticmethod
    def _calculate_risk_score(
        sharpe: Dict, max_dd: Dict, var: Dict, volatility: Dict
    ) -> int:
        """
        Genel risk skoru hesapla (0-100)
        0 = En düşük risk, 100 = En yüksek risk
        """
        score = 50  # Başlangıç
        
        # Sharpe etkisi
        sr = sharpe.get("sharpe_ratio", 0)
        if sr >= 2:
            score -= 15
        elif sr >= 1:
            score -= 10
        elif sr >= 0:
            score -= 5
        elif sr < 0:
            score += 15
        
        # MDD etkisi
        mdd = max_dd.get("max_drawdown_pct", 20)
        if mdd > 30:
            score += 20
        elif mdd > 20:
            score += 10
        elif mdd > 10:
            score += 5
        else:
            score -= 10
        
        # VaR etkisi
        var_val = var.get("var_pct", 3)
        if var_val > 5:
            score += 15
        elif var_val > 3:
            score += 5
        elif var_val < 2:
            score -= 10
        
        # Volatilite etkisi
        vol = volatility.get("annualized_pct", 30)
        if vol > 50:
            score += 15
        elif vol > 35:
            score += 5
        elif vol < 20:
            score -= 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def _get_risk_level(score: int) -> str:
        """Risk seviyesi belirleme"""
        if score >= 75:
            return "çok_yüksek"
        elif score >= 55:
            return "yüksek"
        elif score >= 40:
            return "orta"
        elif score >= 25:
            return "düşük"
        else:
            return "çok_düşük"
    
    @staticmethod
    def _get_risk_recommendation(
        risk_score: int, max_dd: Dict, sharpe: Dict
    ) -> str:
        """Risk bazlı öneri"""
        sr = sharpe.get("sharpe_ratio", 0)
        mdd = max_dd.get("max_drawdown_pct", 20)
        
        if risk_score >= 70:
            return "Yüksek risk! Pozisyon büyüklüğünü küçük tutun veya stop-loss kullanın."
        elif risk_score >= 50 and sr < 0.5:
            return "Risk-getiri dengesi zayıf. Daha iyi fırsatları bekleyin."
        elif mdd > 25 and max_dd.get("in_drawdown", False):
            return "Hisse ciddi düşüşte. Ortalama düşürme riskli olabilir."
        elif sr >= 1.5 and risk_score < 50:
            return "İyi risk-getiri profili. Pozisyon alınabilir."
        elif sr >= 1:
            return "Kabul edilebilir risk. Dikkatli pozisyon alınabilir."
        else:
            return "Orta risk seviyesi. Normal pozisyon büyüklüğü uygun."


class PositionSizing:
    """
    Pozisyon Büyüklüğü Hesaplama
    ============================
    Risk bazlı pozisyon boyutlandırma
    """
    
    @staticmethod
    def kelly_criterion(
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Dict[str, float]:
        """
        Kelly Kriterionu
        ================
        Optimal pozisyon büyüklüğü
        
        Kelly % = W - [(1-W) / R]
        W = Kazanma oranı
        R = Kazanç/Kayıp oranı
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return {"kelly_pct": 0, "recommendation": "hesaplanamadı"}
        
        r = abs(avg_win / avg_loss)
        w = win_rate
        
        kelly = w - ((1 - w) / r)
        
        # Yarım Kelly (daha konservatif)
        half_kelly = kelly / 2
        
        # Sınırla
        kelly = max(0, min(1, kelly))
        half_kelly = max(0, min(0.5, half_kelly))
        
        return {
            "kelly_pct": round(kelly * 100, 2),
            "half_kelly_pct": round(half_kelly * 100, 2),
            "win_rate": round(win_rate * 100, 1),
            "reward_risk_ratio": round(r, 2),
            "recommendation": f"Portföyün %{half_kelly*100:.1f}'i ile pozisyon al (yarım Kelly)"
        }
    
    @staticmethod
    def fixed_risk_position(
        account_size: float,
        risk_per_trade_pct: float,
        entry_price: float,
        stop_loss_price: float
    ) -> Dict[str, float]:
        """
        Sabit Risk Pozisyon Boyutlandırma
        =================================
        Her işlemde sabit yüzde risk
        """
        risk_amount = account_size * (risk_per_trade_pct / 100)
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return {"shares": 0, "position_value": 0, "error": "stop_loss_geçersiz"}
        
        shares = int(risk_amount / price_risk)
        position_value = shares * entry_price
        position_pct = (position_value / account_size) * 100
        
        return {
            "shares": shares,
            "position_value": round(position_value, 2),
            "position_pct": round(position_pct, 2),
            "max_loss": round(risk_amount, 2),
            "risk_per_share": round(price_risk, 2),
            "recommendation": f"{shares} adet hisse al (portföyün %{position_pct:.1f}'i)"
        }
    
    @staticmethod
    def volatility_adjusted_position(
        account_size: float,
        target_volatility_pct: float,
        stock_volatility_pct: float,
        current_price: float
    ) -> Dict[str, float]:
        """
        Volatilite Ayarlı Pozisyon
        ==========================
        Volatilite bazlı pozisyon boyutlandırma
        """
        if stock_volatility_pct == 0:
            return {"shares": 0, "error": "volatilite_sıfır"}
        
        # Hedef volatilite / Hisse volatilitesi
        vol_adjustment = target_volatility_pct / stock_volatility_pct
        
        # Pozisyon büyüklüğü
        position_value = account_size * vol_adjustment
        position_value = min(position_value, account_size * 0.25)  # Max %25
        
        shares = int(position_value / current_price)
        actual_position_pct = (shares * current_price / account_size) * 100
        
        return {
            "shares": shares,
            "position_value": round(shares * current_price, 2),
            "position_pct": round(actual_position_pct, 2),
            "volatility_adjustment": round(vol_adjustment, 2),
            "stock_volatility_pct": round(stock_volatility_pct, 2),
            "target_volatility_pct": target_volatility_pct
        }
