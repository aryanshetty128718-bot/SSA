import urllib.request
import urllib.error
import json

base_url = "http://127.0.0.1:8000/api/v1"

barcodes_to_test = [
    ("Local Cached Product (Nutella)", "3017620422003", "GET", "/products/barcode/3017620422003"),
    ("Invalid Check-Digit Barcode", "4006381333932", "GET", "/products/barcode/4006381333932"),
]

for label, bc, method, endpoint in barcodes_to_test:
    url = f"{base_url}{endpoint}"
    print(f"\n=======================================================")
    print(f"TEST: {label} ({bc})")
    print(f"Request: {method} {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"HTTP Status: {resp.status}")
            print(f"Response: {json.dumps(data, indent=2)[:300]}...")
    except urllib.error.HTTPError as e:
        print(f"HTTP Status: {e.code}")
        body = e.read().decode('utf-8')
        try:
            parsed = json.loads(body)
            print(f"Response JSON: {json.dumps(parsed, indent=2)}")
        except Exception:
            print(f"Response Raw: {body}")

print(f"\n=======================================================")
print("TEST: Unknown Valid Barcode in Offline Mode (Mock OFF offline)")
from unittest.mock import patch
import sys; sys.path.insert(0, 'backend')
from app.services.product_service import product_service
from app.db.session import SessionLocal
from app.core.exceptions import ExternalAPIUnavailableError

db = SessionLocal()
with patch.object(product_service.off_client, 'fetch_product', side_effect=ExternalAPIUnavailableError(service="Open Food Facts", detail="Network is unreachable (offline mode)")):
    try:
        product_service.get_by_barcode("8909999999994", db)
        print("UNEXPECTED: Got product!")
    except ExternalAPIUnavailableError as exc:
        print(f"Successfully caught ExternalAPIUnavailableError!")
        print(f"Status code: {exc.status_code}")
        print(f"Exception message: {exc.message}")
db.close()
