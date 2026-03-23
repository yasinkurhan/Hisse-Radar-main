import requests, json; r=requests.post('http://localhost:8001/api/analysis/daily', json={'limit':1}); print('tv:', r.json()['all_results'][0].get('tv_signals'))
