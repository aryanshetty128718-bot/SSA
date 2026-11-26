"""
Fetches real Indian food & beverage products directly from in.openfoodfacts.org.
Parses all nutrition, ingredients, and categories, and merges them into ml/data/raw/off_raw_products.json.
"""

import os
import json
import time
import httpx
from datetime import datetime

CATEGORY_TAGS = [
    ("breakfast-cereals", ["breakfast-cereals"]),
    ("soft-drinks-sodas", ["sodas", "carbonated-drinks"]),
    ("fruit-juices", ["fruit-juices"]),
    ("yoghurts", ["yogurts", "fermented-milks"]),
    ("biscuits-cookies", ["biscuits", "cookies"]),
    ("chips-crisps-snacks", ["crisps", "salty-snacks"]),
    ("chocolates-confectionery", ["chocolates"]),
    ("instant-noodles-pasta", ["pastas", "noodles"]),
    ("dairy-plant-drinks", ["milks", "dairy-drinks"]),
    ("breads-bakery", ["breads"])
]

FIELDS = [
    "code", "product_name", "generic_name", "brands", "categories_tags",
    "ingredients_text", "countries_tags", "nutriments", "nova_group", "nutriscore_grade"
]

HEADERS = {
    "User-Agent": "SmartShoppingAssistant/1.0 (academic research project; contact: student@example.edu)",
    "Accept": "application/json"
}

def parse_nutrient(nutr_dict, key, fallback=None, factor=1.0):
    if not isinstance(nutr_dict, dict):
        return None
    val = nutr_dict.get(f"{key}_100g") or nutr_dict.get(key)
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    if fallback:
        fb_val = nutr_dict.get(f"{fallback}_100g") or nutr_dict.get(fallback)
        if fb_val is not None:
            try:
                return round(float(fb_val) * factor, 4)
            except (ValueError, TypeError):
                pass
    return None

def main():
    raw_path = "ml/data/raw/off_raw_products.json"
    with open(raw_path, "r", encoding="utf-8") as f:
        existing = json.load(f)

    existing_codes = {str(p["code"]).strip() for p in existing}
    print(f"Loaded existing dataset with {len(existing)} products.")

    added_indian = 0
    with httpx.Client(headers=HEADERS, timeout=12.0) as client:
        for cat_slug, tags in CATEGORY_TAGS:
            print(f"Fetching Indian products for {cat_slug}...")
            for tag in tags:
                for page in range(1, 3):  # 2 pages of 20 = 40 products
                    url = "https://in.openfoodfacts.org/cgi/search.pl"
                    params = {
                        "tagtype_0": "categories",
                        "tag_contains_0": "contains",
                        "tag_0": tag,
                        "action": "process",
                        "json": 1,
                        "page_size": 20,
                        "page": page,
                        "fields": ",".join(FIELDS)
                    }
                    try:
                        r = client.get(url, params=params)
                        if r.status_code == 200:
                            data = r.json()
                            products = data.get("products", [])
                            for p in products:
                                code = str(p.get("code", "")).strip()
                                name = p.get("product_name") or p.get("generic_name")
                                nutriments = p.get("nutriments", {})
                                if code and name and nutriments and code not in existing_codes:
                                    # Format nutriments cleanly
                                    clean_nutr = {
                                        "energy-kcal_100g": parse_nutrient(nutriments, "energy-kcal", fallback="energy-kj", factor=1.0/4.184),
                                        "sugars_100g": parse_nutrient(nutriments, "sugars"),
                                        "fat_100g": parse_nutrient(nutriments, "fat"),
                                        "saturated-fat_100g": parse_nutrient(nutriments, "saturated-fat"),
                                        "sodium_100g": parse_nutrient(nutriments, "sodium", fallback="salt", factor=1.0/2.5),
                                        "salt_100g": parse_nutrient(nutriments, "salt", fallback="sodium", factor=2.5),
                                        "proteins_100g": parse_nutrient(nutriments, "proteins"),
                                        "fiber_100g": parse_nutrient(nutriments, "fiber")
                                    }
                                    
                                    has_any = any(v is not None for v in clean_nutr.values())
                                    if not has_any:
                                        continue

                                    prod_dict = {
                                        "code": code,
                                        "product_name": name.strip(),
                                        "generic_name": p.get("generic_name", "").strip(),
                                        "brands": p.get("brands", "").strip(),
                                        "categories_tags": p.get("categories_tags", []),
                                        "assigned_target_category": cat_slug,
                                        "ingredients_text": p.get("ingredients_text", "").strip(),
                                        "countries_tags": list(set(p.get("countries_tags", []) + ["en:india"])),
                                        "is_india": True,
                                        "nutriments": clean_nutr,
                                        "nova_group": p.get("nova_group"),
                                        "nutriscore_grade": str(p.get("nutriscore_grade", "")).lower() if p.get("nutriscore_grade") else None
                                    }
                                    existing.append(prod_dict)
                                    existing_codes.add(code)
                                    added_indian += 1
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"  Error on tag {tag} page {page}: {e}")
                        time.sleep(1.0)

    print(f"\nSuccessfully added {added_indian} Indian products to dataset!")
    print(f"New total records: {len(existing)}")

    # Save merged dataset
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(existing, f)
    print(f"Updated raw products saved to {raw_path}")

    # Update metadata
    meta_path = "ml/data/raw/metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    india_total = sum(1 for p in existing if p.get("is_india") or "en:india" in p.get("countries_tags", []))
    meta["total_records"] = len(existing)
    meta["country_counts"]["india"] = india_total
    meta["country_counts"]["global"] = len(existing) - india_total

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Updated metadata: Indian products = {india_total}, Global products = {meta['country_counts']['global']}")

if __name__ == "__main__":
    main()
