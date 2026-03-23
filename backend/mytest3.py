from app.services.borsapy_fetcher import get_borsapy_fetcher
try:
    b = get_borsapy_fetcher()
    res = b.get_ta_signals('TRHOL')
    print('Result:', res)
except Exception as e:
    print('Error:', e)
