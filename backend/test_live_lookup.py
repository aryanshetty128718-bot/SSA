import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal
from app.services.product_service import product_service
from app.api.v1.products import format_product_detail
from app.models import Product, NutritionalInformation, Category, ProductIngredient

def live_lookup(barcode: str = "3017620422003"):
    db = SessionLocal()
    try:
        print(f"=== Performing Live Open Food Facts Lookup for Barcode: {barcode} ===")
        
        # Check if already in DB
        existing = db.query(Product).filter_by(barcode=barcode).first()
        if existing:
            print(f"Product already exists in DB. Deleting to test fresh live fetch...")
            db.delete(existing)
            db.commit()

        # Call product service which hits Open Food Facts v2
        product = product_service.get_by_barcode(barcode=barcode, db=db)
        
        print("\n=== LIVE LOOKUP SUCCESSFUL! STORED RECORD DETAILS ===")
        print(f"ID:                      {product.id}")
        print(f"Barcode:                 {product.barcode}")
        print(f"Product Name:            {product.name}")
        print(f"Brand:                   {product.brand}")
        print(f"Generic Name:            {product.generic_name}")
        print(f"Source:                  {product.source}")
        print(f"Data Source:             {product.data_source}")
        print(f"NOVA Processing Group:   {product.nova_group}")
        print(f"Nutri-Score Grade:       {product.nutri_score_grade}")
        print(f"Data Completeness Score: {product.data_completeness_score} (1.0 = 100%)")
        print(f"Serving Size:            {product.serving_size}")
        print(f"Image URL:               {product.image_url}")
        
        print("\n--- CATEGORY ---")
        if product.category:
            print(f"Name:         {product.category.name}")
            print(f"Slug:         {product.category.slug}")
            print(f"Product Type: {product.category.product_type}")

        print("\n--- NUTRITIONAL INFORMATION ---")
        if product.nutrition:
            n = product.nutrition
            print(f"Basis:            {n.basis}")
            print(f"Energy:           {n.energy_kcal} kcal ({n.energy_kj} kJ)")
            print(f"Fat:              {n.fat_g} g")
            print(f"Saturated Fat:    {n.saturated_fat_g} g")
            print(f"Carbohydrates:    {n.carbohydrates_g} g")
            print(f"Sugars:           {n.sugars_g} g")
            print(f"Fiber:            {n.fiber_g} g")
            print(f"Proteins:         {n.proteins_g} g")
            print(f"Sodium:           {n.sodium_mg} mg")
            print(f"Salt:             {n.salt_g} g")

        print("\n--- INGREDIENTS (Top 10 Normalized) ---")
        for pi in product.product_ingredients[:10]:
            print(f"  #{pi.position_order}: {pi.ingredient.canonical_name} (Additive: {pi.ingredient.is_additive}, Whole Grain: {pi.is_whole_grain})")

        print("\n=== Record Verified in Local Relational Database ===")
        return product

    finally:
        db.close()

if __name__ == "__main__":
    live_lookup("3017620422003")
