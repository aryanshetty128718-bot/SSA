import sys
import httpx
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
from app.core.config import settings

headers = {"User-Agent": settings.USER_AGENT}
for code in ["8901719101037", "8901063012226", "8901063012219", "8901719104045"]:
    url = f"{settings.OPEN_FOOD_FACTS_BASE_URL}/api/v2/product/{code}.json"
    try:
        r = httpx.get(url, headers=headers, timeout=10.0)
        print(f"Barcode {code}: Status {r.status_code}")
        if r.status_code == 200:
            p = r.json().get("product", {})
            print(f"  Name: {p.get('product_name')} | Brand: {p.get('brands')} | NS: {p.get('nutriscore_grade')}")
    except Exception as e:
        print(f"Error {code}: {e}")
