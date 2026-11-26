import sys
import time
import httpx
from typing import List, Dict, Any

sys.path.insert(0, "backend")

from app.db.session import SessionLocal
from app.models.product import Product
from app.services.off_parser import parse_off_product
from app.services.product_service import ProductService
from app.services.analysis_service import AnalysisService
from app.core.logging_config import logger

THIN_CATEGORIES = [
    ("noodles", "Instant Noodles"),
    ("chocolates", "Chocolates & Confectionery"),
    ("sodas", "Soft Drinks & Sodas"),
    ("breads", "Breads & Bakery"),
    ("fruit-juices", "Fruit Juices"),
    ("yogurts", "Yoghurts & Fermented Dairy")
]

FIELDS = [
    "code", "product_name", "product_name_en", "generic_name", "brands",
    "image_url", "image_front_url", "categories_tags", "categories",
    "ingredients_text", "ingredients", "allergens_tags", "quantity",
    "serving_size", "nutriments", "nova_group", "nutriscore_grade",
    "countries_tags", "origins_tags"
]

def import_category(tag: str, label: str, db, max_items: int = 10):
    url = "https://world.openfoodfacts.org/api/v2/search"
    headers = {"User-Agent": "SmartShoppingAssistant/1.0 (academic demo; contact: admin@smartshopping.local)"}
    params = {
        "countries_tags_en": "india",
        "categories_tags_en": tag,
        "fields": ",".join(FIELDS),
        "page_size": max_items,
        "json": "1"
    }

    print(f"\n--- Searching OFF for Indian products in {label} ({tag}) ---")
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=12.0)
        if resp.status_code != 200:
            print(f"Failed to fetch {tag}: HTTP {resp.status_code}")
            return 0
        data = resp.json()
        products = data.get("products", [])
        print(f"Retrieved {len(products)} products from OFF.")
    except Exception as e:
        print(f"Exception during request for {tag}: {e}")
        return 0

    ps = ProductService()
    analyzer = AnalysisService()
    imported_count = 0

    for raw_p in products:
        code = str(raw_p.get("code") or "").strip()
        if not code:
            continue

        # Check if already in DB
        existing = db.query(Product).filter_by(barcode=code).first()
        if existing:
            continue

        # Check if has nutrition data
        nutr = raw_p.get("nutriments")
        if not nutr or not isinstance(nutr, dict) or ("energy_100g" not in nutr and "energy-kcal_100g" not in nutr):
            continue

        # Set origin_country if missing
        if "origins_tags" not in raw_p or not raw_p["origins_tags"]:
            raw_p["origins_tags"] = ["en:india"]

        try:
            parsed = parse_off_product({"product": raw_p, "code": code})
            if not parsed.get("origin_country"):
                parsed["origin_country"] = "India"
            
            prod = ps.persist_parsed_product(parsed, db)
            if prod:
                analyzer.analyze_product(prod, db)
                db.commit()
                imported_count += 1
                print(f"  + Imported: [{code}] {prod.name} ({prod.brand or 'N/A'})")
        except Exception as err:
            db.rollback()
            continue

    return imported_count

def main():
    db = SessionLocal()
    total_added = 0
    try:
        for tag, label in THIN_CATEGORIES:
            added = import_category(tag, label, db, max_items=12)
            total_added += added
            time.sleep(1.0) # Polite to OFF API
    finally:
        db.close()

    print(f"\nImport finished! Total new Indian products added: {total_added}")

if __name__ == "__main__":
    main()
