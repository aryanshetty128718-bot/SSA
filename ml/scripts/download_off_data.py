"""
Dataset Downloader for Open Food Facts (OFF)
Collects >= 5,000 real products across 10 project categories with balanced global & Indian representation.
"""

import os
import sys
import time
import json
import httpx
from datetime import datetime
from typing import Dict, List, Any, Set

CATEGORY_CONFIG = [
    {
        "category_slug": "breakfast-cereals",
        "category_name": "Breakfast Cereals",
        "tags": ["breakfast-cereals", "cereals-and-their-products"],
        "target_count": 550
    },
    {
        "category_slug": "soft-drinks-sodas",
        "category_name": "Soft Drinks & Sodas",
        "tags": ["sodas", "carbonated-drinks", "soft-drinks"],
        "target_count": 550
    },
    {
        "category_slug": "fruit-juices",
        "category_name": "Fruit Juices & Nectars",
        "tags": ["fruit-juices", "fruit-nectars", "juices-and-nectars"],
        "target_count": 550
    },
    {
        "category_slug": "yoghurts",
        "category_name": "Yoghurts & Fermented Milk",
        "tags": ["yogurts", "fermented-milks", "dairy-desserts"],
        "target_count": 550
    },
    {
        "category_slug": "biscuits-cookies",
        "category_name": "Biscuits & Cookies",
        "tags": ["biscuits", "cookies", "biscuits-and-cakes"],
        "target_count": 550
    },
    {
        "category_slug": "chips-crisps-snacks",
        "category_name": "Chips & Crisps",
        "tags": ["crisps", "potato-crisps", "chips", "salty-snacks"],
        "target_count": 550
    },
    {
        "category_slug": "chocolates-confectionery",
        "category_name": "Chocolates & Confectionery",
        "tags": ["chocolates", "confectioneries", "dark-chocolates", "milk-chocolates"],
        "target_count": 550
    },
    {
        "category_slug": "instant-noodles-pasta",
        "category_name": "Instant Noodles & Pasta",
        "tags": ["instant-noodles", "pastas", "noodles"],
        "target_count": 550
    },
    {
        "category_slug": "dairy-plant-drinks",
        "category_name": "Dairy & Plant-Based Milk Drinks",
        "tags": ["milks", "plant-milks", "dairy-drinks", "almond-milks", "soy-milks"],
        "target_count": 550
    },
    {
        "category_slug": "breads-bakery",
        "category_name": "Breads & Bakery",
        "tags": ["breads", "baguettes", "sliced-breads", "bakery-products"],
        "target_count": 550
    }
]

FIELDS = [
    "code",
    "product_name",
    "generic_name",
    "brands",
    "categories_tags",
    "ingredients_text",
    "ingredients",
    "nutriments",
    "nova_group",
    "nutriscore_grade",
    "countries_tags"
]

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
HEADERS = {
    "User-Agent": "SmartShoppingAssistant/1.0 (academic research project; contact: student@example.edu)",
    "Accept": "application/json"
}

def fetch_page(client: httpx.Client, tag: str, page: int, country: str = None) -> List[Dict[str, Any]]:
    params = {
        "tagtype_0": "categories",
        "tag_contains_0": "contains",
        "tag_0": tag,
        "action": "process",
        "json": 1,
        "page_size": 100,
        "page": page,
        "fields": ",".join(FIELDS)
    }
    if country:
        params["tagtype_1"] = "countries"
        params["tag_contains_1"] = "contains"
        params["tag_1"] = country

    for attempt in range(3):
        try:
            resp = client.get(SEARCH_URL, params=params, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("products", [])
            elif resp.status_code == 503 or resp.status_code == 429:
                wait_time = 2.0 * (attempt + 1)
                print(f"  [Rate limit / 503] Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  [HTTP {resp.status_code}] on tag={tag}, page={page}")
                break
        except Exception as e:
            print(f"  [Attempt {attempt+1} Error] {e}")
            time.sleep(1.0)
    return []

def main():
    os.makedirs("ml/data/raw", exist_ok=True)
    all_products: Dict[str, Dict[str, Any]] = {}
    category_counts: Dict[str, int] = {c["category_slug"]: 0 for c in CATEGORY_CONFIG}
    country_counts: Dict[str, int] = {"india": 0, "global": 0}

    print(f"[{datetime.now().isoformat()}] Starting OFF Data Collection...")

    with httpx.Client(headers=HEADERS) as client:
        for cat in CATEGORY_CONFIG:
            slug = cat["category_slug"]
            target = cat["target_count"]
            print(f"\nFetching category: {slug} (Target: {target})...")

            # 1. Fetch Indian products first
            for tag in cat["tags"]:
                if category_counts[slug] >= target:
                    break
                for page in range(1, 4):  # up to 300 Indian items
                    prods = fetch_page(client, tag, page, country="en:india")
                    time.sleep(0.5)
                    if not prods:
                        break
                    new_added = 0
                    for p in prods:
                        code = str(p.get("code", "")).strip()
                        name = p.get("product_name") or p.get("generic_name")
                        nutriments = p.get("nutriments", {})
                        if code and name and nutriments and code not in all_products:
                            p["assigned_target_category"] = slug
                            p["fetched_country_subset"] = "india"
                            all_products[code] = p
                            category_counts[slug] += 1
                            country_counts["india"] += 1
                            new_added += 1
                    print(f"  Tag '{tag}' (India) page {page}: {len(prods)} returned, {new_added} new. (Category total: {category_counts[slug]})")
                    if len(prods) < 100 or category_counts[slug] >= target:
                        break

            # 2. Fetch Global products
            for tag in cat["tags"]:
                if category_counts[slug] >= target:
                    break
                for page in range(1, 8):  # up to 700 items
                    prods = fetch_page(client, tag, page, country=None)
                    time.sleep(0.5)
                    if not prods:
                        break
                    new_added = 0
                    for p in prods:
                        code = str(p.get("code", "")).strip()
                        name = p.get("product_name") or p.get("generic_name")
                        nutriments = p.get("nutriments", {})
                        if code and name and nutriments and code not in all_products:
                            p["assigned_target_category"] = slug
                            p["fetched_country_subset"] = "global"
                            all_products[code] = p
                            category_counts[slug] += 1
                            country_counts["global"] += 1
                            new_added += 1
                    print(f"  Tag '{tag}' (Global) page {page}: {len(prods)} returned, {new_added} new. (Category total: {category_counts[slug]})")
                    if len(prods) < 100 or category_counts[slug] >= target:
                        break

    product_list = list(all_products.values())
    total_count = len(product_list)
    print(f"\n==========================================")
    print(f"Data Collection Complete!")
    print(f"Total Unique Products: {total_count}")
    print(f"Category Breakdown:")
    for cat, cnt in category_counts.items():
        print(f"  - {cat}: {cnt}")
    print(f"Regional Breakdown:")
    print(f"  - India subset: {country_counts['india']}")
    print(f"  - Global subset: {country_counts['global']}")
    print(f"==========================================")

    output_path = "ml/data/raw/off_raw_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(product_list, f)
    print(f"Saved raw products to {output_path}")

    # Save metadata
    meta = {
        "collection_date": datetime.now().isoformat(),
        "total_records": total_count,
        "category_counts": category_counts,
        "country_counts": country_counts,
        "endpoint": SEARCH_URL,
        "user_agent": HEADERS["User-Agent"],
        "fields": FIELDS
    }
    with open("ml/data/raw/metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Saved metadata to ml/data/raw/metadata.json")

if __name__ == "__main__":
    main()
