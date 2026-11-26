"""
Harvest 250+ Indian packaged foods from Open Food Facts API v2 (stable endpoint).
Covers Biscuits, Noodles, Snacks, Cereals, Beverages, Dairy.
"""

import sys
import httpx
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, Category, NutritionalInformation, ProductCategoryTag
from app.services.off_parser import parse_off_product
from app.services.analysis_service import analysis_service

CATEGORIES_TO_HARVEST = [
    ("biscuits", "biscuits-cookies", "solid"),
    ("cookies", "biscuits-cookies", "solid"),
    ("noodles", "instant-noodles-pasta", "solid"),
    ("snacks", "chips-crisps", "solid"),
    ("crisps", "chips-crisps", "solid"),
    ("cereals", "breakfast-cereals", "solid"),
    ("beverages", "soft-drinks-sodas", "beverage"),
    ("fruit-juices", "fruit-juices", "beverage"),
    ("dairy-drinks", "dairy-plant-drinks", "beverage"),
    ("yogurts", "yoghurts", "solid"),
]

def run():
    db = SessionLocal()
    headers = {"User-Agent": "SmartShoppingAssistant/1.0 (academic; mca-project)"}
    total_added = 0

    for off_cat, slug, p_type in CATEGORIES_TO_HARVEST:
        cat = db.query(Category).filter_by(slug=slug).first()
        if not cat:
            cat = Category(name=slug.replace("-", " ").title(), slug=slug, product_type=p_type)
            db.add(cat)
            db.commit()
            db.refresh(cat)

        url = f"https://world.openfoodfacts.org/api/v2/search?categories_tags_en={off_cat}&countries_tags_en=india&page_size=40"
        try:
            r = httpx.get(url, headers=headers, timeout=12.0)
            if r.status_code != 200:
                continue
            data = r.json()
            products = data.get("products", [])
            print(f"[{off_cat}] Retrieved {len(products)} from API")

            for raw in products:
                code = str(raw.get("code") or "").strip()
                if not code or len(code) < 4:
                    continue

                if db.query(Product).filter_by(barcode=code).first():
                    continue

                try:
                    parsed = parse_off_product({"product": raw, "code": code})
                except Exception:
                    continue

                prod_data = parsed["product"]
                nutr_data = parsed["nutrition"]

                if prod_data.get("data_completeness_score", 0) < 0.60:
                    continue

                product_obj = Product(
                    barcode=code,
                    name=prod_data["name"],
                    brand=prod_data.get("brand") or "Generic",
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

                nutr_obj = NutritionalInformation(product_id=product_obj.id, **nutr_data)
                db.add(nutr_obj)

                for depth, tag in enumerate(parsed.get("category_tags", [])):
                    ct = ProductCategoryTag(product_id=product_obj.id, tag=tag, depth=depth)
                    db.add(ct)

                db.commit()

                try:
                    analysis_service.analyze_product(product_obj, db)
                    db.refresh(product_obj)
                    total_added += 1
                except Exception:
                    pass

        except Exception as e:
            print(f"Error on {off_cat}: {e}")

    db.close()
    print(f"Finished API v2 harvesting! Added {total_added} products.")

if __name__ == "__main__":
    run()
