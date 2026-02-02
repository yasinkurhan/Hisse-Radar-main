import requests
import time

print('Analiz baslatiliyor...')
start = time.time()

r = requests.post('http://localhost:8000/api/analysis/daily', json={'limit': 30}, timeout=900)
elapsed = time.time() - start

if r.status_code == 200:
    data = r.json()
    print(f'Sure: {round(elapsed, 1)} saniye')
    print(f'Toplam hisse: {data.get("total_stocks", 0)}')
    print(f'Analiz edilen: {data.get("total_analyzed", 0)}')
    print(f'Basarisiz: {data.get("failed_count", 0)}')
    print(f'AL sinyali: {data.get("buy_signals", 0)}')
    print(f'SAT sinyali: {data.get("sell_signals", 0)}')
else:
    print(f'Hata: {r.status_code}')
