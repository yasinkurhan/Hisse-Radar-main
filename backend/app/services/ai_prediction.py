"""
AI Fiyat Tahmin Servisi
=======================
Machine Learning ile hisse fiyat tahmini
- Prophet (Facebook) modeli
- Linear Regression
- LSTM (opsiyonel)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Sklearn imports
try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler, PolynomialFeatures
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Prophet import (optional)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class PricePredictionService:
    """AI destekli fiyat tahmin servisi"""
    
    def __init__(self):
        self.models_cache = {}
        self.predictions_cache = {}
        self.cache_duration = 3600  # 1 saat
    
    def predict_price(
        self, 
        symbol: str, 
        historical_data: List[Dict],
        days_ahead: int = 7,
        model_type: str = "ensemble"
    ) -> Dict:
        """
        Hisse fiyatı tahmini yap
        
        Args:
            symbol: Hisse sembolü
            historical_data: Geçmiş fiyat verileri [{date, open, high, low, close, volume}, ...]
            days_ahead: Kaç gün ilerisi tahmin edilecek
            model_type: "linear", "prophet", "ensemble"
        
        Returns:
            Tahmin sonuçları
        """
        
        if not historical_data or len(historical_data) < 30:
            return {
                "success": False,
                "error": "Yeterli geçmiş veri yok (minimum 30 gün gerekli)",
                "symbol": symbol
            }
        
        # DataFrame oluştur
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # Tahmin yap
        try:
            if model_type == "prophet" and PROPHET_AVAILABLE:
                predictions = self._predict_with_prophet(df, days_ahead)
            elif model_type == "linear" or not SKLEARN_AVAILABLE:
                predictions = self._predict_with_linear(df, days_ahead)
            else:
                predictions = self._predict_with_ensemble(df, days_ahead)
            
            # Teknik göstergeler hesapla
            current_price = float(df['close'].iloc[-1])
            avg_prediction = np.mean([p['predicted_price'] for p in predictions])
            
            # Trend analizi
            trend = "yükseliş" if avg_prediction > current_price else "düşüş"
            change_percent = ((avg_prediction - current_price) / current_price) * 100
            
            # Güven skoru hesapla
            confidence = self._calculate_confidence(df, predictions)
            
            return {
                "success": True,
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "predictions": predictions,
                "summary": {
                    "trend": trend,
                    "expected_change_percent": round(change_percent, 2),
                    "target_price_7d": round(avg_prediction, 2),
                    "confidence_score": confidence,
                    "model_used": model_type
                },
                "support_resistance": self._calculate_support_resistance(df),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }
    
    def _predict_with_linear(self, df: pd.DataFrame, days_ahead: int) -> List[Dict]:
        """Linear Regression ile tahmin"""
        
        # Feature engineering
        df['day_num'] = range(len(df))
        df['ma_5'] = df['close'].rolling(5).mean()
        df['ma_20'] = df['close'].rolling(20).mean()
        df['volatility'] = df['close'].rolling(10).std()
        
        # NaN'ları temizle
        df_clean = df.dropna()
        
        # Features
        features = ['day_num', 'ma_5', 'ma_20', 'volatility']
        X = df_clean[features].values
        y = df_clean['close'].values
        
        # Model eğit
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        
        # Gelecek günler için tahmin
        predictions = []
        last_date = df['date'].iloc[-1]
        last_day_num = df['day_num'].iloc[-1]
        
        # Son değerleri al
        last_ma_5 = df['ma_5'].iloc[-1]
        last_ma_20 = df['ma_20'].iloc[-1]
        last_volatility = df['volatility'].iloc[-1]
        last_close = df['close'].iloc[-1]
        
        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            
            # Basit feature tahminleri
            future_day = last_day_num + i
            future_ma_5 = last_ma_5 + (last_close - last_ma_5) * 0.1 * i
            future_ma_20 = last_ma_20 + (last_close - last_ma_20) * 0.05 * i
            
            X_future = np.array([[future_day, future_ma_5, future_ma_20, last_volatility]])
            pred_price = model.predict(X_future)[0]
            
            # Güven aralığı
            std = last_volatility * np.sqrt(i)
            lower = pred_price - 1.96 * std
            upper = pred_price + 1.96 * std
            
            predictions.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "predicted_price": round(float(pred_price), 2),
                "lower_bound": round(float(max(lower, 0)), 2),
                "upper_bound": round(float(upper), 2),
                "confidence_interval": "95%"
            })
            
            last_close = pred_price
        
        return predictions
    
    def _predict_with_prophet(self, df: pd.DataFrame, days_ahead: int) -> List[Dict]:
        """Facebook Prophet ile tahmin"""
        
        # Prophet formatı
        prophet_df = df[['date', 'close']].rename(columns={'date': 'ds', 'close': 'y'})
        
        # Model oluştur ve eğit
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(prophet_df)
        
        # Gelecek tahminleri
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        # Son N gün tahminleri al
        predictions = []
        for _, row in forecast.tail(days_ahead).iterrows():
            predictions.append({
                "date": row['ds'].strftime("%Y-%m-%d"),
                "predicted_price": round(float(row['yhat']), 2),
                "lower_bound": round(float(max(row['yhat_lower'], 0)), 2),
                "upper_bound": round(float(row['yhat_upper']), 2),
                "confidence_interval": "80%"
            })
        
        return predictions
    
    def _predict_with_ensemble(self, df: pd.DataFrame, days_ahead: int) -> List[Dict]:
        """Ensemble (birden fazla model) ile tahmin"""
        
        # Feature engineering
        df = df.copy()
        df['day_num'] = range(len(df))
        df['ma_5'] = df['close'].rolling(5).mean()
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_20'] = df['close'].rolling(20).mean()
        df['rsi'] = self._calculate_rsi(df['close'])
        df['volatility'] = df['close'].rolling(10).std()
        df['momentum'] = df['close'].diff(5)
        df['price_change'] = df['close'].pct_change()
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
        
        df_clean = df.dropna()
        
        if len(df_clean) < 20:
            return self._predict_with_linear(df, days_ahead)
        
        # Features
        feature_cols = ['day_num', 'ma_5', 'ma_10', 'ma_20', 'rsi', 'volatility', 
                       'momentum', 'close_lag_1', 'close_lag_2', 'close_lag_3', 'close_lag_5']
        
        X = df_clean[feature_cols].values
        y = df_clean['close'].values
        
        # Scaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Multiple models
        models = {
            'ridge': Ridge(alpha=1.0),
            'rf': RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42),
            'gb': GradientBoostingRegressor(n_estimators=50, max_depth=5, random_state=42)
        }
        
        # Eğit
        for model in models.values():
            model.fit(X_scaled, y)
        
        # Tahmin
        predictions = []
        last_date = df['date'].iloc[-1]
        last_row = df_clean.iloc[-1].copy()
        
        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            
            # Feature'ları güncelle
            future_features = self._prepare_future_features(last_row, i, df_clean)
            X_future = scaler.transform([future_features])
            
            # Her modelden tahmin al
            preds = [model.predict(X_future)[0] for model in models.values()]
            
            # Ağırlıklı ortalama
            weights = [0.2, 0.4, 0.4]  # ridge, rf, gb
            ensemble_pred = np.average(preds, weights=weights)
            
            # Güven aralığı
            std = np.std(preds) + last_row['volatility'] * np.sqrt(i) * 0.5
            lower = ensemble_pred - 1.96 * std
            upper = ensemble_pred + 1.96 * std
            
            predictions.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "predicted_price": round(float(ensemble_pred), 2),
                "lower_bound": round(float(max(lower, 0)), 2),
                "upper_bound": round(float(upper), 2),
                "confidence_interval": "95%"
            })
            
            # Sonraki iterasyon için güncelle
            last_row['close'] = ensemble_pred
            last_row['day_num'] += 1
        
        return predictions
    
    def _prepare_future_features(self, last_row, days_ahead: int, df: pd.DataFrame) -> List[float]:
        """Gelecek için feature'ları hazırla"""
        
        # Basit extrapolation
        trend = (df['close'].iloc[-1] - df['close'].iloc[-5]) / 5
        
        return [
            last_row['day_num'] + days_ahead,
            last_row['ma_5'] + trend * days_ahead * 0.5,
            last_row['ma_10'] + trend * days_ahead * 0.3,
            last_row['ma_20'] + trend * days_ahead * 0.2,
            min(max(last_row['rsi'], 30), 70),  # RSI ortalamaya döner
            last_row['volatility'],
            trend,
            last_row['close'],
            last_row['close_lag_1'],
            last_row['close_lag_2'],
            last_row['close_lag_3']
        ]
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI hesapla"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_confidence(self, df: pd.DataFrame, predictions: List[Dict]) -> int:
        """Tahmin güven skoru hesapla (0-100)"""
        
        # Volatilite bazlı skor (düşük volatilite = yüksek güven)
        volatility = df['close'].pct_change().std()
        vol_score = max(0, 100 - volatility * 1000)
        
        # Trend tutarlılığı skoru
        ma_5 = df['close'].rolling(5).mean().iloc[-1]
        ma_20 = df['close'].rolling(20).mean().iloc[-1]
        current = df['close'].iloc[-1]
        
        trend_aligned = (current > ma_5 > ma_20) or (current < ma_5 < ma_20)
        trend_score = 80 if trend_aligned else 50
        
        # Veri yeterliliği skoru
        data_score = min(100, len(df) / 2)
        
        # Tahmin tutarlılığı
        pred_changes = [predictions[i]['predicted_price'] - predictions[i-1]['predicted_price'] 
                       for i in range(1, len(predictions))]
        pred_consistency = 100 - min(100, np.std(pred_changes) * 10)
        
        # Toplam skor
        final_score = int(vol_score * 0.3 + trend_score * 0.3 + data_score * 0.2 + pred_consistency * 0.2)
        
        return min(95, max(20, final_score))
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Destek ve direnç seviyelerini hesapla"""
        
        recent = df.tail(60)
        
        # Pivot noktaları
        high = recent['high'].max()
        low = recent['low'].min()
        close = recent['close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        
        return {
            "pivot": round(pivot, 2),
            "resistance_1": round(r1, 2),
            "resistance_2": round(r2, 2),
            "support_1": round(s1, 2),
            "support_2": round(s2, 2),
            "52_week_high": round(float(df['high'].tail(252).max()), 2),
            "52_week_low": round(float(df['low'].tail(252).min()), 2)
        }
    
    def get_ai_signal(self, symbol: str, prediction_result: Dict) -> Dict:
        """AI tabanlı al/sat sinyali üret"""
        
        if not prediction_result.get('success'):
            return {"signal": "BEKLE", "strength": 0, "reason": "Tahmin yapılamadı"}
        
        summary = prediction_result['summary']
        support_resistance = prediction_result['support_resistance']
        current_price = prediction_result['current_price']
        
        change_pct = summary['expected_change_percent']
        confidence = summary['confidence_score']
        
        # Sinyal belirleme
        if change_pct > 5 and confidence > 60:
            signal = "GÜÇLÜ AL"
            strength = min(100, int(change_pct * 10 + confidence * 0.5))
        elif change_pct > 2 and confidence > 50:
            signal = "AL"
            strength = min(80, int(change_pct * 8 + confidence * 0.3))
        elif change_pct < -5 and confidence > 60:
            signal = "GÜÇLÜ SAT"
            strength = min(100, int(abs(change_pct) * 10 + confidence * 0.5))
        elif change_pct < -2 and confidence > 50:
            signal = "SAT"
            strength = min(80, int(abs(change_pct) * 8 + confidence * 0.3))
        else:
            signal = "BEKLE"
            strength = 50
        
        # Destek/direnç kontrolü
        near_support = current_price <= support_resistance['support_1'] * 1.02
        near_resistance = current_price >= support_resistance['resistance_1'] * 0.98
        
        reason = f"7 günlük tahmin: %{change_pct:+.1f}, Güven: %{confidence}"
        if near_support:
            reason += " | Destek seviyesinde"
        if near_resistance:
            reason += " | Direnç seviyesinde"
        
        return {
            "signal": signal,
            "strength": strength,
            "reason": reason,
            "target_price": summary['target_price_7d'],
            "stop_loss": round(support_resistance['support_1'] * 0.98, 2),
            "take_profit": round(support_resistance['resistance_1'], 2)
        }


# Singleton instance
prediction_service = PricePredictionService()
