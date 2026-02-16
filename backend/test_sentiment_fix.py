"""Test: Her hisse icin farkli haberler dondugunu dogrula"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.services.analysis_service import AnalysisService

svc = AnalysisService()
print(f"Toplam hisse sayisi: {len(svc._stocks)}")

# Analiz sayfasinda gozuken bazi hisseler
test_symbols = ["POLTK", "THYAO", "SUNTK", "UFUK", "GENIL", "VERUS"]

for symbol in test_symbols:
    stock_info = next((s for s in svc._stocks if s["symbol"] == symbol), None)
    name = stock_info["name"] if stock_info else symbol
    result = svc._fetch_sentiment_sync(symbol)
    print(f"{symbol:8s} ({name:30s}) -> score={result['score']:+.3f}, count={result['news_count']}, label={result['label']}, has_data={result['has_data']}")
