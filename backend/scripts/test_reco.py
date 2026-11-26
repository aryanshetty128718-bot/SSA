import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/v1"
uuid = "6db4f071-4e61-4fa6-ba83-fb52d62b9e03"
barcode = "3017620422003"

print("--- Testing /recommendations/{uuid} ---")
try:
    req = urllib.request.Request(f"{base_url}/recommendations/{uuid}")
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read().decode())
        print(f"UUID rec count: {len(d.get('recommendations', []))}")
except Exception as e:
    print(f"UUID failed: {e}")

print("--- Testing /recommendations/{barcode} ---")
try:
    req = urllib.request.Request(f"{base_url}/recommendations/{barcode}")
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read().decode())
        print(f"Barcode rec count: {len(d.get('recommendations', []))}")
except Exception as e:
    print(f"Barcode failed: {e}")
