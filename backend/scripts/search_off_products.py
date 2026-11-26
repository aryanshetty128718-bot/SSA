import httpx
import json

headers = {"User-Agent": "SmartShoppingAssistant/1.0 (MCA Project)"}
for query in ["Britannia", "Parle", "hazelnut cocoa spread", "almond butter"]:
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 4,
        "fields": "code,product_name,brands,nutriments,categories_tags,ingredients_text,nutriscore_grade"
    }
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=12.0)
        if r.status_code == 200:
            prods = r.json().get("products", [])
            print(f"\n--- Query: {query} ({len(prods)} results) ---")
            for p in prods:
                print(f"  Barcode: {p.get('code')} | Name: {p.get('product_name')} | Brand: {p.get('brands')} | NS: {p.get('nutriscore_grade')}")
    except Exception as e:
        print(f"Error for {query}: {e}")
