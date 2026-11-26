import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/v1"

def fetch(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

print("--- 1. GET /products/3017620422003 ---")
st, data = fetch(f"{base_url}/products/3017620422003")
print("Status:", st)
if st == 200:
    print(json.dumps(data, indent=2)[:800])

print("\n--- 2. GET /products/3017620422003/analysis ---")
st2, data2 = fetch(f"{base_url}/products/3017620422003/analysis")
print("Status:", st2)
if st2 == 200:
    print("Keys in analysis:", list(data2.keys()))
    if 'product' in data2:
        print("Keys in data2['product']:", list(data2['product'].keys()))
        print("data2['product']['nutritional_information']:", data2['product'].get('nutritional_information'))
        print("data2['product']['ingredients']:", data2['product'].get('ingredients'))
    for k in ['nutritional_breakdown', 'ingredient_analysis', 'additives']:
        if k in data2:
            print(f"data2[{k}]:", data2[k])

print("\n--- 3. GET /recommendations/3017620422003 ---")
st3, data3 = fetch(f"{base_url}/recommendations/3017620422003")
print("Status:", st3)
if st3 == 200:
    print("Rec count:", len(data3) if isinstance(data3, list) else data3.get('recommendations', []))
    print("Rec response:", json.dumps(data3, indent=2)[:800])
