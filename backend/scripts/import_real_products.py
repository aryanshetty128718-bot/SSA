"""
Database Ingestion Script for Real Open Food Facts Products.
Imports cleaned/raw products into the relational database via standard parsers,
normalizing categories, ingredients, nutritional information, and computing/caching scores.
Tags all imported records with source='openfoodfacts'.
"""

import os
import sys
import json
import time
import uuid

# Ensure backend is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models import (
    Product, Category, NutritionalInformation, Ingredient,
    ProductIngredient, ProductCategoryTag, ProductScore
)
from app.services.off_parser import parse_off_product
from app.services.analysis_service import AnalysisService
from app.utils.barcode_validator import validate_barcode, normalize_barcode
from app.core.logging_config import logger

analysis_service = AnalysisService()

BEVERAGE_CATEGORIES = {
    "soft-drinks-sodas",
    "fruit-juices",
    "dairy-plant-drinks"
}

def import_real_data(raw_json_path: str = "ml/data/raw/off_raw_products.json", max_products: int = 10000):
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    if not os.path.exists(raw_json_path):
        print(f"Error: {raw_json_path} does not exist.")
        return

    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    print(f"Loaded {len(raw_items)} raw products from snapshot.")

    db = SessionLocal()
    try:
        # Load existing barcodes to avoid duplicates
        existing_barcodes = {row[0] for row in db.query(Product.barcode).all()}
        print(f"Existing products in DB: {len(existing_barcodes)}")

        # Cache existing categories by slug
        categories = {c.slug: c for c in db.query(Category).all()}

        # Cache existing ingredients by canonical name
        ingredients_cache = {i.canonical_name: i for i in db.query(Ingredient).all()}

        imported_count = 0
        skipped_count = 0
        error_count = 0
        t0 = time.time()

        for idx, item in enumerate(raw_items):
            if imported_count >= max_products:
                print(f"Reached target cap of {max_products} imported real products.")
                break

            code = str(item.get("code", "")).strip()
            if not code or code in existing_barcodes:
                skipped_count += 1
                continue

            # Ensure valid barcode or format
            clean_code = normalize_barcode(code) if code.isdigit() else code
            if clean_code in existing_barcodes:
                skipped_count += 1
                continue

            try:
                # Wrap item in {'code': ..., 'product': item} if not nested
                raw_payload = {"code": clean_code, "status": 1, "product": item} if "product" not in item else item
                parsed = parse_off_product(raw_payload)

                cat_info = parsed["category"]
                cat_slug = cat_info["slug"]
                
                # Prioritize assigned project category
                target_slug = item.get("assigned_target_category")
                if target_slug == "chips-crisps-snacks":
                    target_slug = "chips-crisps"

                if target_slug and target_slug in categories:
                    category = categories[target_slug]
                elif cat_slug in categories:
                    category = categories[cat_slug]
                elif target_slug:
                    p_type = "beverage" if target_slug in BEVERAGE_CATEGORIES else "solid"
                    category = Category(
                        name=target_slug.replace("-", " ").title(),
                        slug=target_slug,
                        product_type=p_type,
                        description=f"Auto-created category {target_slug}"
                    )
                    db.add(category)
                    db.flush()
                    categories[target_slug] = category
                else:
                    category = Category(
                        name=cat_info["name"],
                        slug=cat_slug,
                        product_type=cat_info["product_type"],
                        description=f"Auto-created from OFF tag {cat_slug}"
                    )
                    db.add(category)
                    db.flush()
                    categories[cat_slug] = category

                prod_info = parsed["product"]
                new_product = Product(
                    id=str(uuid.uuid4()),
                    barcode=clean_code,
                    name=prod_info["name"],
                    brand=prod_info["brand"],
                    generic_name=prod_info["generic_name"],
                    category_id=category.id,
                    serving_size=prod_info["serving_size"],
                    image_url=prod_info["image_url"],
                    packaging=prod_info["packaging"],
                    nova_group=prod_info["nova_group"],
                    nutri_score_grade=prod_info["nutri_score_grade"],
                    data_completeness_score=prod_info["data_completeness_score"],
                    data_source="open_food_facts",
                    source="openfoodfacts"
                )
                db.add(new_product)
                db.flush()

                # Nutrition
                nut_info = parsed["nutrition"]
                new_nutrition = NutritionalInformation(
                    id=str(uuid.uuid4()),
                    product_id=new_product.id,
                    energy_kcal=nut_info["energy_kcal"],
                    energy_kj=nut_info["energy_kj"],
                    fat_g=nut_info["fat_g"],
                    saturated_fat_g=nut_info["saturated_fat_g"],
                    trans_fat_g=nut_info["trans_fat_g"],
                    carbohydrates_g=nut_info["carbohydrates_g"],
                    sugars_g=nut_info["sugars_g"],
                    added_sugars_g=nut_info["added_sugars_g"],
                    fiber_g=nut_info["fiber_g"],
                    proteins_g=nut_info["proteins_g"],
                    sodium_mg=nut_info["sodium_mg"],
                    salt_g=nut_info["salt_g"],
                    fruits_vegetables_nuts_colza_walnut_olive_oils_pct=nut_info["fruits_vegetables_nuts_colza_walnut_olive_oils_pct"],
                    basis=nut_info["basis"]
                )
                db.add(new_nutrition)

                # Ingredients
                seen_ing_ids = set()
                for ing_item in parsed["ingredients"]:
                    c_name = ing_item["name"]
                    if c_name not in ingredients_cache:
                        ing_obj = Ingredient(
                            id=str(uuid.uuid4()),
                            canonical_name=c_name,
                            ins_number=ing_item.get("ins_number"),
                            is_additive=ing_item.get("is_additive", False)
                        )
                        db.add(ing_obj)
                        db.flush()
                        ingredients_cache[c_name] = ing_obj
                    else:
                        ing_obj = ingredients_cache[c_name]

                    if ing_obj.id in seen_ing_ids:
                        continue
                    seen_ing_ids.add(ing_obj.id)

                    pi = ProductIngredient(
                        id=str(uuid.uuid4()),
                        product_id=new_product.id,
                        ingredient_id=ing_obj.id,
                        position_order=ing_item["position_order"],
                        estimated_percentage=ing_item.get("estimated_percentage"),
                        is_whole_grain=ing_item.get("is_whole_grain", False)
                    )
                    db.add(pi)

                # Category Tags
                for depth, tag in enumerate(parsed.get("category_tags", [])):
                    ct = ProductCategoryTag(
                        id=str(uuid.uuid4()),
                        product_id=new_product.id,
                        tag=tag,
                        depth=depth
                    )
                    db.add(ct)

                # Analyze and cache score
                analysis_service.analyze_product(new_product, db)

                existing_barcodes.add(clean_code)
                imported_count += 1

                if imported_count % 100 == 0:
                    db.commit()
                    elapsed = time.time() - t0
                    print(f"  Imported {imported_count} real products ({elapsed:.1f}s)...")

            except Exception as e:
                db.rollback()
                error_count += 1
                if error_count <= 5:
                    print(f"  [Error importing item {code}]: {e}")

        db.commit()
        print(f"\n==========================================")
        print(f"Real Data Import Complete!")
        print(f"Successfully Imported: {imported_count} products")
        print(f"Skipped (Duplicates/Incomplete): {skipped_count}")
        print(f"Total Errors: {error_count}")
        print(f"Total Elapsed Time: {time.time()-t0:.1f}s")
        print("==========================================")

        # Report row counts per category and per product type
        print("\n--- Relational Database Inventory Report ---")
        total_prods = db.query(Product).count()
        seed_prods = db.query(Product).filter_by(source="seed").count()
        off_prods = db.query(Product).filter_by(source="openfoodfacts").count()
        print(f"Total Products in Database: {total_prods} (Real OFF: {off_prods}, Seed: {seed_prods})")

        print("\nBreakdown by Product Type:")
        solids_cnt = db.query(Product).join(Category).filter(Category.product_type == "solid").count()
        bev_cnt = db.query(Product).join(Category).filter(Category.product_type == "beverage").count()
        print(f"  - Solid Foods : {solids_cnt}")
        print(f"  - Beverages   : {bev_cnt}")

        print("\nBreakdown by Category:")
        cat_counts = []
        for cat in db.query(Category).all():
            cnt = db.query(Product).filter_by(category_id=cat.id).count()
            if cnt > 0:
                cat_counts.append((cat.name, cat.slug, cat.product_type, cnt))

        cat_counts.sort(key=lambda x: x[3], reverse=True)
        for name, slug, ptype, cnt in cat_counts:
            print(f"  - {name:32s} [{slug:25s}] ({ptype:8s}): {cnt:4d} products")

        print("\nCached Product Scores in Database:")
        scores_cnt = db.query(ProductScore).count()
        print(f"  - Total Cached Scores: {scores_cnt} / {total_prods}")

    finally:
        db.close()

if __name__ == "__main__":
    import_real_data()
