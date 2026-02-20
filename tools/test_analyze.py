import requests
import json

q = "SELECT * FROM products WHERE name ILIKE '%phone%';"
payload = q.strip()
if payload.endswith(';'):
    payload = payload[:-1].strip()

print('Query sent:', payload)
try:
    r = requests.post('http://localhost:8000/analyze', json={'query': payload}, timeout=30)
    print('STATUS', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print('RESPONSE TEXT:', r.text)
except Exception as e:
    print('ERROR:', e)
