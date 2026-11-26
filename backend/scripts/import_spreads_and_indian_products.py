"""
Import real spreads (peanut butter, almond butter, hazelnut spreads) and
real Indian biscuits (Britannia Bourbon, Marie Gold, Good Day) from Open Food Facts API.
Stores them in smart_shopping.db under source = 'openfoodfacts',
normalizes ingredients, category tags, and computes ProductScore.
"""

import sys
import json
import httpx
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, Category, NutritionalInformation, Ingredient, ProductIngredient, ProductCategoryTag, ProductScore
from app.services.off_parser import parse_off_product
from app.services.analysis_service import analysis_service
from app.core.config import settings

def get_or_create_category(db, name: str, slug: str, product_type: str = "solid") -> Category:
    cat = db.query(Category).filter_by(slug=slug).first()
    if not cat:
        cat = Category(
            name=name,
            slug=slug,
            product_type=product_type,
            description=f"{name} food products"
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat

def import_barcodes(barcodes):
    db = SessionLocal()
    headers = {"User-Agent": settings.USER_AGENT}
    imported = []

    # Ensure sweet-spreads-nut-butters category exists
    spread_cat = get_or_create_category(
        db,
        name="Sweet Spreads & Nut Butters",
        slug="sweet-spreads-nut-butters",
        product_type="solid"
    )

    biscuit_cat = db.query(Category).filter_by(slug="biscuits-cookies").first()
    if not biscuit_cat:
        biscuit_cat = get_or_create_category(db, "Biscuits & Cookies", "biscuits-cookies", "solid")

    for code in barcodes:
        print(f"Fetching {code} from Open Food Facts...")
        url = f"{settings.OPEN_FOOD_FACTS_BASE_URL}/api/v2/product/{code}.json"
        try:
            r = httpx.get(url, headers=headers, timeout=12.0)
            if r.status_code != 200:
                print(f"  [!] HTTP {r.status_code} for {code}")
                continue

            raw_json = r.json()
            try:
                parsed = parse_off_product(raw_json)
            except Exception as parse_err:
                print(f"  [!] Parse rejected {code}: {parse_err}")
                continue

            prod_data = parsed["product"]
            nutr_data = parsed["nutrition"]
            tags = parsed.get("category_tags", [])

            # Determine category: check if spread, biscuit, or beverage
            name_lower = prod_data["name"].lower()
            is_spread = any(w in name_lower for w in ["tartiner", "butter", "spread", "beurre", "peanut", "hazelnut", "cacahuète", "noisette"]) or any("spread" in t for t in tags)
            is_beverage = any(w in name_lower for w in ["cola", "drink", "soda", "beverage", "water"]) or any("beverage" in t or "soda" in t for t in tags)

            if is_spread:
                target_cat = spread_cat
            elif is_beverage:
                target_cat = db.query(Category).filter_by(slug="soft-drinks-sodas").first() or spread_cat
            else:
                target_cat = biscuit_cat

            # Check if product exists in DB
            prod = db.query(Product).filter_by(barcode=prod_data["barcode"]).first()
            if not prod:
                prod = Product(
                    barcode=prod_data["barcode"],
                    name=prod_data["name"],
                    brand=prod_data["brand"],
                    category_id=target_cat.id,
                    serving_size=prod_data["serving_size"],
                    image_url=prod_data["image_url"],
                    packaging=prod_data["packaging"],
                    origin_country=prod_data.get("origin_country"),
                    nova_group=prod_data["nova_group"],
                    nutri_score_grade=prod_data["nutri_score_grade"],
                    data_completeness_score=prod_data["data_completeness_score"],
                    data_source="open_food_facts",
                    source="openfoodfacts"
                )
                db.add(prod)
                db.commit()
                db.refresh(prod)
            else:
                prod.name = prod_data["name"]
                prod.category_id = target_cat.id
                prod.source = "openfoodfacts"
                db.commit()

            # Insert nutrition
            nutr = db.query(NutritionalInformation).filter_by(product_id=prod.id).first()
            if not nutr:
                nutr = NutritionalInformation(
                    product_id=prod.id,
                    energy_kcal=nutr_data.get("energy_kcal"),
                    energy_kj=nutr_data.get("energy_kj"),
                    fat_g=nutr_data.get("fat_g"),
                    saturated_fat_g=nutr_data.get("saturated_fat_g"),
                    carbohydrates_g=nutr_data.get("carbohydrates_g"),
                    sugars_g=nutr_data.get("sugars_g"),
                    fiber_g=nutr_data.get("fiber_g"),
                    proteins_g=nutr_data.get("proteins_g"),
                    sodium_mg=nutr_data.get("sodium_mg"),
                    salt_g=nutr_data.get("salt_g"),
                    fruits_vegetables_nuts_colza_walnut_olive_oils_pct=nutr_data.get("fruits_veg_pct"),
                    basis="100ml" if target_cat.product_type == "beverage" else "100g"
                )
                db.add(nutr)
                db.commit()

            # Insert Category Tags
            existing_tags = {ct.tag for ct in prod.category_tags}
            for depth, tag in enumerate(tags[:10]):
                if tag not in existing_tags:
                    db.add(ProductCategoryTag(product_id=prod.id, tag=tag, depth=depth))
            db.commit()

            # Run Analysis Service to score and cache
            analysis_service.analyze_product(prod, db)
            db.refresh(prod)
            imported.append(prod)
            print(f"  [+] Stored {prod.name} ({prod.barcode}) | Category: {target_cat.name} | Score: {prod.product_score.overall_project_score if prod.product_score else 'N/A'}")

        except Exception as e:
            print(f"  [-] Error importing {code}: {e}")

    db.close()
    return imported

if __name__ == "__main__":
    targets = [
        # Spreads (Peanut butter, Hazelnut spreads, Almond butters)
        "3608580124047",  # Andros Be Nuts Pâte à tartiner
        "3327272107259",  # Menguy's Beurre de cacahuètes
        "20474478",       # Mcennedy Peanut Butter
        "4056489424925",  # Maribel Smooth Peanut Butter
        "3564700010991",  # Pâte à tartiner noisettes cacao
        "5410126006957",  # Lotus Biscoff Spread
        "3033710065967",  # Danette chocolat spread
        "3017620422003",  # Nutella (update category)
        # Real Indian Biscuits from Open Food Facts
        "8901063139329",  # Britannia Bourbon
        "8901063162914",  # Britannia Marie Gold Biscuit
        "8901063092853",  # Britannia Good Day Cashew Cookie
        # Real Coca-Cola
        "5449000000996",  # Coca-Cola Original Taste (ensure in soft drinks)
        "5449000000439",  # Coca-Cola Can
    ]
    import_barcodes(targets)
