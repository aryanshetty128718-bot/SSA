import sys
import httpx
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings

def test_off_search(query: str):
    headers = {"User-Agent": settings.USER_AGENT}
    url = f"{settings.OPEN_FOOD_FACTS_BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5,
        "fields": "code,product_name,brands,nutriments,categories_tags,ingredients_text,nutriscore_grade,completeness"
    }
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=10.0)
        print(f"Query '{query}': Status {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("products", [])
            print(f"Found {len(products)} products.")
            for p in products:
                print(f"  Barcode: {p.get('code')} | Name: {p.get('product_name')} | Brand: {p.get('brands')} | NS: {p.get('nutriscore_grade')}")
            return products
    except Exception as e:
        print(f"Error querying OFF: {e}")
        return []

print("Testing OFF connectivity...")
test_off_search("peanut butter")
test_off_search("parle g")
