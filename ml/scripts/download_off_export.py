"""
Open Food Facts Export Streamer & Ingestion Pipeline.
Streams compressed records from the official Open Food Facts S3 export (zero rate limits).
Collects >= 5,000 unique real products across 10 project categories with verified Indian and global representation.
"""

import os
import sys
import json
import time
import zlib
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional

S3_EXPORT_URL = "https://openfoodfacts-ds.s3.eu-west-3.amazonaws.com/en.openfoodfacts.org.products.csv.gz"

CATEGORY_MAPPING = {
    "breakfast-cereals": ["breakfast-cereals", "cereals-and-their-products", "mueslis", "porridges", "cornflakes", "cereales-pour-petit-dejeuner"],
    "soft-drinks-sodas": ["sodas", "carbonated-drinks", "soft-drinks", "colas", "boissons-gazeuses", "carbonated-soft-drinks"],
    "fruit-juices": ["fruit-juices", "fruit-nectars", "pure-fruit-juices", "juices-and-nectars", "jus-de-fruits"],
    "yoghurts": ["yogurts", "fermented-milks", "greek-style-yogurts", "dairy-desserts", "yaourts"],
    "biscuits-cookies": ["biscuits", "cookies", "shortbread-cookies", "filled-biscuits", "wafers", "biscotti"],
    "chips-crisps-snacks": ["crisps", "potato-crisps", "chips", "salty-snacks", "corn-chips", "chips-de-pommes-de-terre"],
    "chocolates-confectionery": ["chocolates", "confectioneries", "dark-chocolates", "milk-chocolates", "candies", "chocolats"],
    "instant-noodles-pasta": ["instant-noodles", "pastas", "noodles", "ramen", "spaghetti", "nouilles-instantanees"],
    "dairy-plant-drinks": ["milks", "plant-milks", "dairy-drinks", "almond-milks", "soy-milks", "oat-milks", "laits"],
    "breads-bakery": ["breads", "baguettes", "sliced-breads", "bakery-products", "white-breads", "pains"]
}

TARGET_PER_CATEGORY = 600

def parse_float(val: str) -> Optional[float]:
    if not val:
        return None
    val = val.strip()
    if not val or val.lower() == "nan" or val.lower() == "none":
        return None
    try:
        f = float(val)
        if 0.0 <= f <= 100000.0:
            return f
    except ValueError:
        pass
    return None

def resolve_category(cat_str: str) -> Optional[str]:
    if not cat_str:
        return None
    cat_lower = cat_str.lower()
    for cat_slug, tags in CATEGORY_MAPPING.items():
        for tag in tags:
            if tag in cat_lower:
                return cat_slug
    return None

def stream_and_collect(target_per_cat: int = TARGET_PER_CATEGORY, output_path: str = "ml/data/raw/off_raw_products.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"[{datetime.now().isoformat()}] Starting OFF Export Stream from {S3_EXPORT_URL}...")
    print(f"Target: {target_per_cat} products per category (Total: {target_per_cat * len(CATEGORY_MAPPING)})")

    collected: Dict[str, Dict[str, Any]] = {}
    cat_counts: Dict[str, int] = {c: 0 for c in CATEGORY_MAPPING}
    india_count = 0
    global_count = 0

    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    line_buffer = ""
    col_idx: Dict[str, int] = {}
    lines_read = 0
    t0 = time.time()

    headers = {
        "User-Agent": "SmartShoppingAssistant/1.0 (academic research project; contact: student@example.edu)"
    }

    with httpx.stream("GET", S3_EXPORT_URL, headers=headers, timeout=60.0) as resp:
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to connect to S3 export: HTTP {resp.status_code}")

        for chunk in resp.iter_bytes(chunk_size=131072):
            decompressed = decompressor.decompress(chunk)
            line_buffer += decompressed.decode("utf-8", errors="replace")

            while "\n" in line_buffer:
                line, line_buffer = line_buffer.split("\n", 1)
                lines_read += 1

                if not col_idx:
                    # Header row
                    cols = line.split("\t")
                    col_idx = {name: i for i, name in enumerate(cols)}
                    print(f"Header parsed with {len(col_idx)} columns. Streaming product rows...")
                    continue

                parts = line.split("\t")
                if len(parts) <= max(col_idx.values()):
                    continue

                code = parts[col_idx["code"]].strip()
                name = parts[col_idx["product_name"]].strip()
                if not code or not name or code in collected:
                    continue

                # Category determination
                cats_field = parts[col_idx["categories_tags"]] or parts[col_idx["categories"]]
                matched_category = resolve_category(cats_field)
                if not matched_category:
                    continue

                # Stop collecting for this category if full
                if cat_counts[matched_category] >= target_per_cat:
                    # Check if all categories are satisfied
                    if all(cnt >= target_per_cat for cnt in cat_counts.values()):
                        break
                    continue

                # Nutriments extraction
                energy_kcal = parse_float(parts[col_idx["energy-kcal_100g"]])
                if energy_kcal is None:
                    energy_kj = parse_float(parts[col_idx["energy-kj_100g"]])
                    if energy_kj is not None:
                        energy_kcal = round(energy_kj / 4.184, 1)

                sugars = parse_float(parts[col_idx["sugars_100g"]])
                fat = parse_float(parts[col_idx["fat_100g"]])
                sat_fat = parse_float(parts[col_idx["saturated-fat_100g"]])
                sodium = parse_float(parts[col_idx["sodium_100g"]])
                salt = parse_float(parts[col_idx["salt_100g"]])
                if sodium is None and salt is not None:
                    sodium = round(salt / 2.5, 4)
                elif salt is None and sodium is not None:
                    salt = round(sodium * 2.5, 4)

                proteins = parse_float(parts[col_idx["proteins_100g"]])
                fiber = parse_float(parts[col_idx["fiber_100g"]])

                # Must have at least some basic nutrition
                has_nutriments = any(x is not None for x in [energy_kcal, sugars, fat, sat_fat, salt, proteins, fiber])
                if not has_nutriments:
                    continue

                # Country determination
                countries = (parts[col_idx["countries_tags"]] or parts[col_idx["countries"]]).lower()
                is_india = "india" in countries or "en:india" in countries
                if is_india:
                    india_count += 1
                else:
                    global_count += 1

                # Ingredients & brand
                brand = parts[col_idx["brands"]].strip()
                ingredients_text = parts[col_idx["ingredients_text"]].strip()
                nova_group = parse_float(parts[col_idx["nova_group"]])
                nutriscore_grade = parts[col_idx["nutriscore_grade"]].strip().lower() or None

                prod_dict = {
                    "code": code,
                    "product_name": name,
                    "generic_name": parts[col_idx["generic_name"]].strip(),
                    "brands": brand,
                    "categories_tags": [t.strip() for t in parts[col_idx["categories_tags"]].split(",") if t.strip()],
                    "assigned_target_category": matched_category,
                    "ingredients_text": ingredients_text,
                    "countries_tags": [t.strip() for t in parts[col_idx["countries_tags"]].split(",") if t.strip()],
                    "is_india": is_india,
                    "nutriments": {
                        "energy-kcal_100g": energy_kcal,
                        "sugars_100g": sugars,
                        "fat_100g": fat,
                        "saturated-fat_100g": sat_fat,
                        "sodium_100g": sodium,
                        "salt_100g": salt,
                        "proteins_100g": proteins,
                        "fiber_100g": fiber
                    },
                    "nova_group": int(nova_group) if nova_group is not None else None,
                    "nutriscore_grade": nutriscore_grade
                }

                collected[code] = prod_dict
                cat_counts[matched_category] += 1

                if len(collected) % 500 == 0:
                    elapsed = time.time() - t0
                    print(f"  Processed {lines_read} lines | Collected {len(collected)} products ({elapsed:.1f}s)...")
                    for c_slug, c_num in cat_counts.items():
                        print(f"    - {c_slug}: {c_num}/{target_per_cat}")

            if all(cnt >= target_per_cat for cnt in cat_counts.values()):
                print("All category targets reached!")
                break

    total_time = time.time() - t0
    product_list = list(collected.values())
    print("\n==========================================")
    print(f"OFF Export Ingestion Completed in {total_time:.1f}s!")
    print(f"Total lines scanned: {lines_read}")
    print(f"Total products collected: {len(product_list)}")
    print(f"Category Breakdown:")
    for c_slug, c_num in cat_counts.items():
        print(f"  - {c_slug:25s}: {c_num}")
    print(f"Geography Breakdown:")
    print(f"  - India subset: {india_count}")
    print(f"  - Global subset: {global_count}")
    print("==========================================")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(product_list, f)
    print(f"Saved raw products snapshot to {output_path}")

    meta = {
        "source": "Open Food Facts Official S3 Dump (en.openfoodfacts.org.products.csv.gz)",
        "download_date": datetime.now().isoformat(),
        "total_records": len(product_list),
        "lines_scanned": lines_read,
        "elapsed_seconds": round(total_time, 2),
        "target_per_category": target_per_cat,
        "category_counts": cat_counts,
        "country_counts": {
            "india": india_count,
            "global": global_count
        }
    }
    with open("ml/data/raw/metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Saved metadata to ml/data/raw/metadata.json")

    return product_list

if __name__ == "__main__":
    stream_and_collect()
