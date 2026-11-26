"""
Data Preprocessing & Category Mapping Pipeline for Open Food Facts Dataset.
Extracts text and nutrient features, maps OFF categories to the 10 project categories,
handles missing values rigorously, and prevents target leakage.
"""

import os
import re
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

CATEGORY_MAPPING_RULES = {
    "breakfast-cereals": [
        "en:breakfast-cereals", "en:cereals-and-their-products", "en:mueslis", "en:porridges", "en:cornflakes"
    ],
    "soft-drinks-sodas": [
        "en:sodas", "en:carbonated-drinks", "en:soft-drinks", "en:colas", "en:carbonated-soft-drinks"
    ],
    "fruit-juices": [
        "en:fruit-juices", "en:fruit-nectars", "en:pure-fruit-juices", "en:juices-and-nectars", "en:orange-juices"
    ],
    "yoghurts": [
        "en:yogurts", "en:fermented-milks", "en:greek-style-yogurts", "en:drinkable-yogurts", "en:dairy-desserts"
    ],
    "biscuits-cookies": [
        "en:biscuits", "en:cookies", "en:shortbread-cookies", "en:filled-biscuits", "en:wafers"
    ],
    "chips-crisps-snacks": [
        "en:crisps", "en:potato-crisps", "en:chips", "en:salty-snacks", "en:corn-chips", "en:appetizers"
    ],
    "chocolates-confectionery": [
        "en:chocolates", "en:confectioneries", "en:dark-chocolates", "en:milk-chocolates", "en:candies"
    ],
    "instant-noodles-pasta": [
        "en:instant-noodles", "en:pastas", "en:noodles", "en:ramen", "en:spaghetti"
    ],
    "dairy-plant-drinks": [
        "en:milks", "en:plant-milks", "en:dairy-drinks", "en:almond-milks", "en:soy-milks", "en:oat-milks"
    ],
    "breads-bakery": [
        "en:breads", "en:baguettes", "en:sliced-breads", "en:bakery-products", "en:white-breads"
    ]
}

def clean_text(text: Optional[str]) -> str:
    if not text or not isinstance(text, str):
        return ""
    # Normalize whitespace, remove URLs, strip punctuation noise
    t = re.sub(r"https?://\S+", "", text)
    t = re.sub(r"[_*#\[\]\(\)\{\}]", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t

def extract_nutrient(nutriments: Dict[str, Any], key: str, fallback_key: Optional[str] = None, conversion_factor: float = 1.0) -> Optional[float]:
    if not isinstance(nutriments, dict):
        return None
    val = nutriments.get(f"{key}_100g")
    if val is None:
        val = nutriments.get(key)
    if val is not None:
        try:
            fval = float(val)
            if 0.0 <= fval <= 100000.0:  # basic sanity
                return fval
        except (ValueError, TypeError):
            pass

    if fallback_key:
        fb_val = nutriments.get(f"{fallback_key}_100g")
        if fb_val is None:
            fb_val = nutriments.get(fallback_key)
        if fb_val is not None:
            try:
                fval = float(fb_val) * conversion_factor
                if 0.0 <= fval <= 100000.0:
                    return fval
            except (ValueError, TypeError):
                pass
    return None

def process_raw_dataset(raw_path: str = "ml/data/raw/off_raw_products.json", output_dir: str = "ml/data/processed") -> pd.DataFrame:
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_products = json.load(f)

    print(f"Loaded {len(raw_products)} raw products.")

    records = []
    dropped_count = 0
    dropped_reasons = {"missing_name": 0, "no_nutriments": 0, "no_category": 0}

    for p in raw_products:
        code = str(p.get("code", "")).strip()
        name = p.get("product_name") or p.get("product_name_en") or p.get("generic_name")
        if not name or not isinstance(name, str) or not name.strip():
            dropped_count += 1
            dropped_reasons["missing_name"] += 1
            continue

        nutriments = p.get("nutriments", {})
        if not nutriments or not isinstance(nutriments, dict):
            dropped_count += 1
            dropped_reasons["no_nutriments"] += 1
            continue

        # Target Category Resolution (from pre-assigned target or tag hierarchy)
        target_category = p.get("assigned_target_category")
        if not target_category:
            cat_tags = p.get("categories_tags", [])
            for cat_slug, tags in CATEGORY_MAPPING_RULES.items():
                if any(t in cat_tags for t in tags):
                    target_category = cat_slug
                    break

        if not target_category:
            dropped_count += 1
            dropped_reasons["no_category"] += 1
            continue

        # Extract Nutrients (Missing = None, never 0.0!)
        energy_kcal = extract_nutrient(nutriments, "energy-kcal", fallback_key="energy-kj", conversion_factor=1.0/4.184)
        sugars = extract_nutrient(nutriments, "sugars")
        fat = extract_nutrient(nutriments, "fat")
        saturated_fat = extract_nutrient(nutriments, "saturated-fat")
        sodium = extract_nutrient(nutriments, "sodium", fallback_key="salt", conversion_factor=1.0/2.5)
        salt = extract_nutrient(nutriments, "salt", fallback_key="sodium", conversion_factor=2.5)
        proteins = extract_nutrient(nutriments, "proteins")
        fiber = extract_nutrient(nutriments, "fiber")

        # Text features for ML: product name, brand, ingredients (LEAKAGE PREVENTION: never include categories_tags)
        brand = p.get("brands") or ""
        ingredients_text = p.get("ingredients_text") or ""
        
        name_clean = clean_text(name)
        brand_clean = clean_text(brand)
        ing_clean = clean_text(ingredients_text)

        combined_text = f"{name_clean} {brand_clean} {ing_clean}".strip()

        # Countries
        countries = p.get("countries_tags", [])
        is_india = "en:india" in countries or p.get("fetched_country_subset") == "india"

        records.append({
            "code": code,
            "product_name": name.strip(),
            "brand": brand.strip(),
            "category": target_category,
            "text_features": combined_text,
            "energy_kcal_100g": energy_kcal,
            "sugars_100g": sugars,
            "fat_100g": fat,
            "saturated_fat_100g": saturated_fat,
            "sodium_100g": sodium,
            "salt_100g": salt,
            "proteins_100g": proteins,
            "fiber_100g": fiber,
            "nova_group": p.get("nova_group"),
            "nutriscore_grade": str(p.get("nutriscore_grade", "")).lower() if p.get("nutriscore_grade") else None,
            "is_india": is_india
        })

    df = pd.DataFrame(records)
    os.makedirs(output_dir, exist_ok=True)
    out_csv = os.path.join(output_dir, "products_cleaned.csv")
    df.to_csv(out_csv, index=False)

    print("\n=== Data Preprocessing Summary ===")
    print(f"Total raw products: {len(raw_products)}")
    print(f"Cleaned products retained: {len(df)}")
    print(f"Dropped records: {dropped_count} {dropped_reasons}")
    print("\nCategory Distribution:")
    print(df["category"].value_counts())
    print(f"\nIndian Products: {df['is_india'].sum()} ({df['is_india'].mean()*100:.1f}%)")
    print(f"Global Products: {(~df['is_india']).sum()} ({(~df['is_india']).mean()*100:.1f}%)")

    print("\nMissing Nutrient Rates:")
    nutr_cols = ["energy_kcal_100g", "sugars_100g", "fat_100g", "saturated_fat_100g", "sodium_100g", "proteins_100g", "fiber_100g"]
    for c in nutr_cols:
        missing_cnt = df[c].isna().sum()
        missing_pct = df[c].isna().mean() * 100
        print(f"  - {c}: {missing_cnt} missing ({missing_pct:.1f}%)")

    # Save summary stats
    stats = {
        "total_records": len(df),
        "category_distribution": df["category"].value_counts().to_dict(),
        "indian_products_count": int(df["is_india"].sum()),
        "global_products_count": int((~df["is_india"]).sum()),
        "missing_nutrient_rates_pct": {c: round(float(df[c].isna().mean() * 100), 2) for c in nutr_cols}
    }
    with open(os.path.join(output_dir, "data_summary.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return df

if __name__ == "__main__":
    process_raw_dataset()
