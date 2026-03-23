import uvicorn, requests, json
res = requests.post('http://localhost:8000/api/analysis/daily', json={'limit': 1, 'index_filter': 'BIST30'}).json()
print(json.dumps(res.get('all_results', [{}])[0].get('tv_signals', {}), indent=2))

