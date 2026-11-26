"""
Fetches real Indian food & beverage products from Open Food Facts
using top Indian brands and categories to ensure strong Indian market representation.
Appends unique Indian products to ml/data/raw/off_raw_products.json.
"""

import os
import json
import time
import httpx
from datetime import datetime

INDIAN_QUERIES = [
    # Cereals
    ("breakfast-cereals", ["kellogg's chocos india", "quaker oats india", "bagrry's muesli", "saffola masala oats"]),
    # Sodas
    ("soft-drinks-sodas", ["thums up", "limca", "mirinda india", "frooti fizz", "campa cola", "rasna"]),
    # Juices
    ("fruit-juices", ["real fruit juice", "tropicana india", "paper boat juice", "b natural juice", "maaza"]),
    # Yoghurts
    ("yoghurts", ["amul dahi", "nestle dahi", "mother dairy curd", "epigamia yogurt", "milky mist curd"]),
    # Biscuits
    ("biscuits-cookies", ["parle g", "britannia good day", "sunfeast dark fantasy", "monaco biscuits", "marie gold"]),
    # Chips & Snacks
    ("chips-crisps-snacks", ["kurkure", "lays india", "balaji wafers", "haldiram bhujia", "bingo mad angles", "too yumm"]),
    # Chocolates
    ("chocolates-confectionery", ["cadbury dairy milk india", "amul dark chocolate", "kitkat india", "5 star chocolate"]),
    # Noodles & Pasta
    ("instant-noodles-pasta", ["maggi 2-minute noodles", "yippee noodles", "wai wai noodles", "ching's secret noodles"]),
    # Dairy & Drinks
    ("dairy-plant-drinks", ["amul taaza milk", "amul kool", "cavins milkshake", "raw pressery almond milk", "sofit soya milk"]),
    # Bakery
    ("breads-bakery", ["britannia bread", "harvest gold bread", "modern bread", "english oven bread"])
]

FIELDS = [
    "code", "product_name", "generic_name", "brands", "categories_tags",
    "ingredients_text", "countries_tags", "nutriments", "nova_group", "nutriscore_grade"
]

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
HEADERS = {
    "User-Agent": "SmartShoppingAssistant/1.0 (academic research project; contact: student@example.edu)",
    "Accept": "application/json"
}

def fetch_indian_products():
    raw_path = "ml/data/raw/off_raw_products.json"
    if not os.path.exists(raw_path):
        print(f"File {raw_path} does not exist.")
        return

    with open(raw_path, "r", encoding="utf-8") as f:
        existing = json.load(f)

    existing_codes = {str(p["code"]).strip() for p in existing}
    print(f"Current dataset has {len(existing)} products.")

    added_count = 0
    with httpx.Client(headers=HEADERS, timeout=15.0) as client:
        for cat_slug, queries in INDIAN_QUERIES:
            print(f"Fetching Indian products for {cat_slug}...")
            for q in queries:
                params = {
                    "search_terms": q,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": 20,
                    "page": 1,
                    "fields": ",".join(FIELDS)
                }
                try:
                    resp = client.get(SEARCH_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        products = data.get("products", [])
                        for p in products:
                            code = str(p.get("code", "")).strip()
                            name = p.get("product_name") or p.get("generic_name")
                            nutriments = p.get("nutriments", {})
                            if code and name and nutriments and code not in existing_codes:
                                p["assigned_target_category"] = cat_slug
                                p["is_india"] = True
                                p["countries_tags"] = p.get("countries_tags", []) + ["en:india"]
                                existing.append(p)
                                existing_codes.add(code)
                                added_count += 1
                    time.sleep(0.4)
                except Exception as e:
                    print(f"  Error querying '{q}': {e}")

    print(f"\nAdded {added_count} unique Indian products!")
    print(f"New total dataset size: {len(existing)}")

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(existing, f)
    print(f"Updated {raw_path}")

    # Update metadata
    meta_path = "ml/data/raw/metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    meta["total_records"] = len(existing)
    meta["country_counts"]["india"] = sum(1 for p in existing if p.get("is_india") or "en:india" in p.get("countries_tags", []))
    meta["country_counts"]["global"] = len(existing) - meta["country_counts"]["india"]

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Updated metadata: India count = {meta['country_counts']['india']}, Global count = {meta['country_counts']['global']}")

if __name__ == "__main__":
    fetch_indian_products()
