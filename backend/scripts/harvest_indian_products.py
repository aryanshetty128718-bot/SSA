"""
Harvest real Indian packaged foods from in.openfoodfacts.org and world.openfoodfacts.org.
Queries categories: biscuits, noodles, snacks, cereals, beverages, dairy.
Saves records to smart_shopping.db via off_parser and analysis_service.
"""

import sys
import time
import httpx
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, Category, NutritionalInformation, Ingredient, ProductIngredient, ProductCategoryTag, ProductScore
from app.services.off_parser import parse_off_product
from app.services.analysis_service import analysis_service
from app.core.config import settings

SEARCH_TERMS = [
    ("biscuit", "biscuits-cookies", "solid"),
    ("cookies", "biscuits-cookies", "solid"),
    ("rusk", "biscuits-cookies", "solid"),
    ("noodles", "instant-noodles-pasta", "solid"),
    ("maggi", "instant-noodles-pasta", "solid"),
    ("namkeen", "chips-crisps", "solid"),
    ("chips", "chips-crisps", "solid"),
    ("kurkure", "chips-crisps", "solid"),
    ("makhana", "chips-crisps", "solid"),
    ("oats", "breakfast-cereals", "solid"),
    ("muesli", "breakfast-cereals", "solid"),
    ("corn flakes", "breakfast-cereals", "solid"),
    ("juice", "fruit-juices", "beverage"),
    ("lassi", "dairy-plant-drinks", "beverage"),
    ("buttermilk", "dairy-plant-drinks", "beverage"),
    ("milk", "dairy-plant-drinks", "beverage"),
    ("dahi", "yoghurts", "solid"),
    ("curd", "yoghurts", "solid"),
]

def harvest_indian_products(target_count=200):
    db = SessionLocal()
    headers = {"User-Agent": "SmartShoppingAssistant/1.0 (academic; mca-project)"}
    total_added = 0

    print("Beginning Indian packaged food harvesting...")

    for term, cat_slug, p_type in SEARCH_TERMS:
        if total_added >= target_count:
            break

        cat = db.query(Category).filter_by(slug=cat_slug).first()
        if not cat:
            cat = Category(name=cat_slug.replace("-", " ").title(), slug=cat_slug, product_type=p_type)
            db.add(cat)
            db.commit()
            db.refresh(cat)

        url = f"https://in.openfoodfacts.org/cgi/search.pl?search_terms={term}&search_simple=1&action=process&json=1&page_size=25"
        try:
            r = httpx.get(url, headers=headers, timeout=10.0)
            if r.status_code != 200:
                continue
            data = r.json()
            prods = data.get("products", [])
            print(f"[{term}] Found {len(prods)} products on in.openfoodfacts.org")

            for raw in prods:
                code = str(raw.get("code") or "").strip()
                if not code or len(code) < 4:
                    continue

                # Check if already in DB
                existing = db.query(Product).filter_by(barcode=code).first()
                if existing:
                    continue

                try:
                    parsed = parse_off_product({"product": raw, "code": code})
                except Exception:
                    continue

                prod_data = parsed["product"]
                nutr_data = parsed["nutrition"]

                # Ensure minimum completeness
                if prod_data.get("data_completeness_score", 0) < 0.60:
                    continue

                # Consistency check: brand & name
                p_name = prod_data["name"]
                p_brand = prod_data.get("brand") or "Generic"
                if p_name.lower().startswith("coca-cola") and "coca" not in p_brand.lower():
                    continue

                product_obj = Product(
                    barcode=code,
                    name=p_name,
                    brand=p_brand,
                    generic_name=prod_data.get("generic_name"),
                    category_id=cat.id,
                    serving_size=prod_data.get("serving_size"),
                    image_url=prod_data.get("image_url"),
                    packaging=prod_data.get("packaging"),
                    origin_country="India",
                    nova_group=prod_data.get("nova_group"),
                    nutri_score_grade=prod_data.get("nutri_score_grade"),
                    data_completeness_score=prod_data.get("data_completeness_score", 0.0),
                    data_source="open_food_facts",
                    source="openfoodfacts"
                )
                db.add(product_obj)
                db.flush()

                # Add nutrition
                nutr_obj = NutritionalInformation(
                    product_id=product_obj.id,
                    **nutr_data
                )
                db.add(nutr_obj)

                # Add tags
                for depth, tag in enumerate(parsed.get("category_tags", [])):
                    ct = ProductCategoryTag(
                        product_id=product_obj.id,
                        tag=tag,
                        depth=depth
                    )
                    db.add(ct)

                db.commit()

                # Score product
                try:
                    analysis_service.analyze_product(product_obj, db)
                    db.refresh(product_obj)
                    total_added += 1
                except Exception as sc_err:
                    pass

        except Exception as net_err:
            print(f"Network error on {term}: {net_err}")
            continue

    db.close()
    print(f"Completed! Total Indian products harvested and added: {total_added}")

if __name__ == "__main__":
    harvest_indian_products(target_count=200)
