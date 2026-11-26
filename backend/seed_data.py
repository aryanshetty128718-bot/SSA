import sys
import os
import uuid
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal
from app.models import (
    Base, User, Category, Product, NutritionalInformation,
    Ingredient, ProductIngredient, ScoringCriteria
)
from app.utils.barcode_validator import calculate_gs1_check_digit
from app.core.logging_config import logger
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def seed_database():
    db = SessionLocal()
    try:
        logger.info("Starting database seeding...")

        # 1. Seed Users (credentials MUST come from environment variables)
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        demo_email = os.getenv("DEMO_EMAIL")
        demo_password = os.getenv("DEMO_PASSWORD")
        env_mode = os.getenv("ENVIRONMENT", "development").lower()

        if env_mode == "production":
            if not admin_email or not admin_password or admin_password in ("Admin@12345", "admin", "password"):
                logger.error("Production guard: ADMIN_EMAIL and secure ADMIN_PASSWORD must be configured in .env. Refusing to seed with default credentials.")
                sys.exit(1)
            if not demo_email or not demo_password or demo_password in ("Demo@12345", "demo", "password"):
                logger.error("Production guard: DEMO_EMAIL and secure DEMO_PASSWORD must be configured in .env. Refusing to seed with default credentials.")
                sys.exit(1)

        # In non-production, fallback to academic demo credentials only if env vars not provided
        admin_email = admin_email or "admin@smartshopping.local"
        admin_password = admin_password or "Admin@12345"
        demo_email = demo_email or "demo@smartshopping.local"
        demo_password = demo_password or "Demo@12345"

        if db.query(User).count() == 0:
            admin_user = User(
                id=str(uuid.uuid4()),
                email=admin_email,
                hashed_password=hash_password(admin_password),
                full_name="System Administrator",
                role="admin",
                is_active=True
            )
            demo_user = User(
                id=str(uuid.uuid4()),
                email=demo_email,
                hashed_password=hash_password(demo_password),
                full_name="Demo User",
                role="user",
                is_active=True
            )
            db.add_all([admin_user, demo_user])
            db.commit()
            logger.info(f"Seeded 2 users ({admin_email} [admin], {demo_email} [user]).")

        # 2. Seed Categories
        categories_data = [
            {"name": "Breakfast Cereals", "slug": "breakfast-cereals", "product_type": "solid", "description": "Oats, muesli, corn flakes, and granola"},
            {"name": "Soft Drinks & Sodas", "slug": "soft-drinks-sodas", "product_type": "beverage", "description": "Carbonated drinks, colas, lemon sodas"},
            {"name": "Fruit Juices & Smoothies", "slug": "fruit-juices-smoothies", "product_type": "beverage", "description": "Packaged fruit juices, nectars, and fruit drinks"},
            {"name": "Yoghurts & Fermented Dairy", "slug": "yoghurts-fermented-dairy", "product_type": "solid", "description": "Plain yogurt, Greek yogurt, fruit yogurts"},
            {"name": "Biscuits & Cookies", "slug": "biscuits-cookies", "product_type": "solid", "description": "Digestives, cream biscuits, butter cookies, crackers"},
            {"name": "Chips & Savory Snacks", "slug": "chips-savory-snacks", "product_type": "solid", "description": "Potato chips, namkeen, extruded snacks, roasted seeds"},
            {"name": "Chocolates & Confectionery", "slug": "chocolates-confectionery", "product_type": "solid", "description": "Dark chocolates, milk chocolate, candy bars"},
            {"name": "Instant Noodles & Soups", "slug": "instant-noodles-soups", "product_type": "solid", "description": "Ramen, instant noodles, ready-to-eat pasta and soup mixes"},
            {"name": "Dairy & Plant Drinks", "slug": "dairy-plant-drinks", "product_type": "beverage", "description": "Almond milk, soy milk, flavored milks, lassi"},
            {"name": "Breads & Bakery", "slug": "breads-bakery", "product_type": "solid", "description": "Whole wheat bread, multigrain loaf, white bread, buns"}
        ]

        category_map = {}
        for cat in categories_data:
            existing = db.query(Category).filter_by(slug=cat["slug"]).first()
            if not existing:
                cat_obj = Category(
                    name=cat["name"],
                    slug=cat["slug"],
                    product_type=cat["product_type"],
                    description=cat["description"]
                )
                db.add(cat_obj)
                db.flush()
                category_map[cat["slug"]] = cat_obj
            else:
                category_map[cat["slug"]] = existing
        db.commit()
        logger.info(f"Seeded/Verified {len(category_map)} categories.")

        # 3. Seed Global Scoring Criteria
        if db.query(ScoringCriteria).count() == 0:
            criteria_list = [
                # Solid foods thresholds
                ScoringCriteria(product_type="solid", parameter_name="sugars", weight=0.22, low_threshold=5.0, medium_threshold=12.5, high_threshold=22.5, unit="g", polarity="negative"),
                ScoringCriteria(product_type="solid", parameter_name="sodium", weight=0.18, low_threshold=120.0, medium_threshold=300.0, high_threshold=600.0, unit="mg", polarity="negative"),
                ScoringCriteria(product_type="solid", parameter_name="saturated_fat", weight=0.18, low_threshold=1.5, medium_threshold=3.0, high_threshold=5.0, unit="g", polarity="negative"),
                ScoringCriteria(product_type="solid", parameter_name="energy", weight=0.12, low_threshold=150.0, medium_threshold=300.0, high_threshold=450.0, unit="kcal", polarity="negative"),
                ScoringCriteria(product_type="solid", parameter_name="fiber", weight=0.10, low_threshold=2.0, medium_threshold=4.0, high_threshold=6.0, unit="g", polarity="positive"),
                ScoringCriteria(product_type="solid", parameter_name="proteins", weight=0.10, low_threshold=4.0, medium_threshold=8.0, high_threshold=12.0, unit="g", polarity="positive"),
                ScoringCriteria(product_type="solid", parameter_name="ingredient_quality", weight=0.05, low_threshold=40.0, medium_threshold=70.0, high_threshold=100.0, unit="score", polarity="positive"),
                ScoringCriteria(product_type="solid", parameter_name="additives", weight=0.05, low_threshold=0.0, medium_threshold=1.0, high_threshold=3.0, unit="deductions", polarity="negative"),
                
                # Beverage thresholds (per 100ml)
                ScoringCriteria(product_type="beverage", parameter_name="sugars", weight=0.50, low_threshold=1.0, medium_threshold=3.0, high_threshold=5.0, unit="g", polarity="negative"),
                ScoringCriteria(product_type="beverage", parameter_name="sodium", weight=0.0, low_threshold=120.0, medium_threshold=200.0, high_threshold=300.0, unit="mg", polarity="negative"),
                ScoringCriteria(product_type="beverage", parameter_name="saturated_fat", weight=0.0, low_threshold=0.75, medium_threshold=1.5, high_threshold=2.5, unit="g", polarity="negative"),
                ScoringCriteria(product_type="beverage", parameter_name="energy", weight=0.20, low_threshold=15.0, medium_threshold=25.0, high_threshold=35.0, unit="kcal", polarity="negative"),
                ScoringCriteria(product_type="beverage", parameter_name="fiber", weight=0.0, low_threshold=1.0, medium_threshold=2.0, high_threshold=2.5, unit="g", polarity="positive"),
                ScoringCriteria(product_type="beverage", parameter_name="proteins", weight=0.0, low_threshold=1.5, medium_threshold=3.0, high_threshold=4.0, unit="g", polarity="positive"),
                ScoringCriteria(product_type="beverage", parameter_name="ingredient_quality", weight=0.15, low_threshold=40.0, medium_threshold=70.0, high_threshold=100.0, unit="score", polarity="positive"),
                ScoringCriteria(product_type="beverage", parameter_name="additives", weight=0.15, low_threshold=0.0, medium_threshold=1.0, high_threshold=3.0, unit="deductions", polarity="negative")
            ]
            db.add_all(criteria_list)
            db.commit()
            logger.info("Seeded 15 scoring criteria records.")

        # 4. Seed Canonical Ingredients & Additives
        raw_ingredients = [
            ("Whole Rolled Oats", None, False, None, "100% natural unrefined whole grain cereal"),
            ("Whole Wheat Flour", None, False, None, "Stone-ground unrefined whole wheat flour"),
            ("Refined Wheat Flour", None, False, None, "Refined flour (Maida) with bran and germ removed"),
            ("Sugar", None, False, None, "Crystalline sucrose"),
            ("Brown Sugar", None, False, None, "Unrefined cane sugar with molasses"),
            ("Honey", None, False, None, "Natural bee honey"),
            ("High Fructose Corn Syrup", None, False, None, "Refined liquid sweetener"),
            ("Almonds", None, False, None, "Nutrient-dense tree nut rich in healthy fats and protein"),
            ("Peanuts", None, False, None, "Legume rich in protein and unsaturated fats"),
            ("Sunflower Oil", None, False, None, "Refined vegetable oil rich in unsaturated fats"),
            ("Palm Oil", None, False, None, "Vegetable oil high in saturated fatty acids"),
            ("Extra Virgin Olive Oil", None, False, None, "Cold pressed monounsaturated olive oil"),
            ("Milk Solids", None, False, None, "Concentrated dairy solids containing lactose and casein"),
            ("Skimmed Milk", None, False, None, "Fluid dairy milk with cream removed"),
            ("Cocoa Butter", None, False, None, "Natural vegetable fat extracted from cocoa beans"),
            ("Cocoa Solids", None, False, None, "Defatted non-fat solids of the cocoa bean"),
            ("Iodised Salt", None, False, None, "Sodium chloride fortified with potassium iodate"),
            ("Water", None, False, None, "Purified potable water"),
            ("Carbonated Water", None, False, None, "Potable water charged with carbon dioxide"),
            ("Apple Juice Concentrate", None, False, None, "Concentrated clarified fruit juice"),
            ("Orange Juice Concentrate", None, False, None, "Pure citrus juice reduction"),
            ("Live Probiotic Cultures", None, False, None, "Beneficial yogurt bacteria (Lactobacillus bulgaricus)"),
            ("Potato Flakes", None, False, None, "Dehydrated potato starch"),
            ("Green Tea Extract", None, False, None, "Natural polyphenol rich tea extract"),
            ("Soy Lecithin", "INS 322", True, "emulsifier", "Plant derived lipid emulsifier; generally recognized as safe"),
            ("Citric Acid", "INS 330", True, "acidity_regulator", "Naturally occurring organic fruit acid; safe"),
            ("Tartrazine", "INS 102", True, "color", "Synthetic yellow azo dye; requires attention in sensitive individuals"),
            ("Sunset Yellow FCF", "INS 110", True, "color", "Synthetic petroleum-derived orange dye"),
            ("Aspartame", "INS 951", True, "sweetener", "Non-nutritive artificial intense sweetener"),
            ("Acesulfame Potassium", "INS 950", True, "sweetener", "Calorie-free artificial sweetener"),
            ("Sucralose", "INS 955", True, "sweetener", "Zero calorie chlorinated sugar derivative"),
            ("Monosodium Glutamate", "INS 621", True, "flavor_enhancer", "Sodium salt of glutamic acid producing savory umami flavor"),
            ("Sodium Benzoate", "INS 211", True, "preservative", "Antimicrobial food preservative widely used in beverages"),
            ("Guar Gum", "INS 412", True, "stabilizer", "Natural polysaccharide thickening agent from guar beans"),
            ("Xanthan Gum", "INS 415", True, "stabilizer", "Microbially fermented polysaccharide thickener"),
            ("Caramel IV", "INS 150d", True, "color", "Sulfite ammonia caramel color commonly used in dark colas")
        ]

        ingredient_map = {}
        for name, ins, is_add, add_type, note in raw_ingredients:
            existing = db.query(Ingredient).filter_by(canonical_name=name).first()
            if not existing:
                ing = Ingredient(
                    id=str(uuid.uuid4()),
                    canonical_name=name,
                    ins_number=ins,
                    is_additive=is_add,
                    additive_type=add_type,
                    health_note=note
                )
                db.add(ing)
                db.flush()
                ingredient_map[name] = ing
            else:
                ingredient_map[name] = existing
        db.commit()
        logger.info(f"Seeded/Verified {len(ingredient_map)} canonical ingredients.")

        # 5. Seed 42 Realistic Products Across 10 Categories
        # Products include realistic solid and beverage items, including some with intentionally None values
        products_data = [
            # --- Breakfast Cereals (5) ---
            {
                "barcode": "8901058852891",
                "name": "Traditional Rolled Oats 100% Wholegrain",
                "brand": "PureHarvest",
                "category": "breakfast-cereals",
                "serving_size": "40g",
                "nova_group": 1,
                "nutri_score": "A",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 389.0, "fat_g": 6.9, "saturated_fat_g": 1.2, "carbohydrates_g": 66.3, "sugars_g": 1.0, "fiber_g": 10.6, "proteins_g": 16.9, "sodium_mg": 5.0, "salt_g": 0.01, "basis": "per 100g"},
                "ingredients": [("Whole Rolled Oats", 1, True, False)]
            },
            {
                "barcode": "8901058852892",
                "name": "Crunchy Almond & Honey Granola",
                "brand": "NatureBake",
                "category": "breakfast-cereals",
                "serving_size": "50g",
                "nova_group": 3,
                "nutri_score": "C",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 445.0, "fat_g": 16.0, "saturated_fat_g": 2.5, "carbohydrates_g": 62.0, "sugars_g": 18.5, "fiber_g": 6.8, "proteins_g": 10.2, "sodium_mg": 140.0, "salt_g": 0.35, "basis": "per 100g"},
                "ingredients": [("Whole Rolled Oats", 1, True, False), ("Almonds", 2, False, False), ("Honey", 3, False, False), ("Sunflower Oil", 4, False, False)]
            },
            {
                "barcode": "8901058852893",
                "name": "Sugar Frosted Flakes Breakfast Cereal",
                "brand": "SweetMorning",
                "category": "breakfast-cereals",
                "serving_size": "30g",
                "nova_group": 4,
                "nutri_score": "D",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 385.0, "fat_g": 0.8, "saturated_fat_g": 0.2, "carbohydrates_g": 87.0, "sugars_g": 37.0, "fiber_g": 2.0, "proteins_g": 5.0, "sodium_mg": 480.0, "salt_g": 1.2, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Sugar", 2, False, False), ("Iodised Salt", 3, False, False)]
            },
            {
                "barcode": "8901058852894",
                "name": "Artisan Fruit & Nut Swiss Muesli",
                "brand": "AlpineNature",
                "category": "breakfast-cereals",
                "serving_size": "45g",
                "nova_group": 2,
                "nutri_score": "B",
                "completeness": 0.88,  # Missing trans fat & added sugars intentionally
                "nutrition": {"energy_kcal": 370.0, "fat_g": 7.5, "saturated_fat_g": 1.1, "carbohydrates_g": 64.0, "sugars_g": 12.0, "fiber_g": 8.0, "proteins_g": 11.5, "sodium_mg": 25.0, "salt_g": 0.06, "basis": "per 100g"},
                "ingredients": [("Whole Rolled Oats", 1, True, False), ("Whole Wheat Flour", 2, True, False), ("Almonds", 3, False, False)]
            },
            {
                "barcode": "8901058852895",
                "name": "Double Choco Crunch Cereal Bites",
                "brand": "KidsZone",
                "category": "breakfast-cereals",
                "serving_size": "35g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 0.75,  # Missing fiber intentionally
                "nutrition": {"energy_kcal": 418.0, "fat_g": 9.5, "saturated_fat_g": 4.8, "carbohydrates_g": 75.0, "sugars_g": 34.0, "proteins_g": 6.8, "sodium_mg": 380.0, "salt_g": 0.95, "basis": "per 100g"},
                "ingredients": [("Sugar", 1, False, False), ("Refined Wheat Flour", 2, False, False), ("Cocoa Powder", 3, False, False), ("Palm Oil", 4, False, False)]
            },

            # --- Soft Drinks & Sodas (5) ---
            {
                "barcode": "8901058852896",
                "name": "Classic Carbonated Cola Beverage",
                "brand": "SparkleFizz",
                "category": "soft-drinks-sodas",
                "serving_size": "250ml",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 44.0, "fat_g": 0.0, "saturated_fat_g": 0.0, "carbohydrates_g": 11.0, "sugars_g": 10.9, "fiber_g": 0.0, "proteins_g": 0.0, "sodium_mg": 12.0, "salt_g": 0.03, "basis": "per 100ml"},
                "ingredients": [("Carbonated Water", 1, False, False), ("Sugar", 2, False, False), ("Caramel IV", 3, False, True), ("Citric Acid", 4, False, True)]
            },
            {
                "barcode": "8901058852897",
                "name": "Diet Cola Zero Sugar Refresh",
                "brand": "SparkleFizz",
                "category": "soft-drinks-sodas",
                "serving_size": "250ml",
                "nova_group": 4,
                "nutri_score": "C",  # 2023 Nutri-Score caps diet soda at C due to artificial sweetener penalty
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 0.8, "fat_g": 0.0, "saturated_fat_g": 0.0, "carbohydrates_g": 0.1, "sugars_g": 0.0, "fiber_g": 0.0, "proteins_g": 0.0, "sodium_mg": 28.0, "salt_g": 0.07, "basis": "per 100ml"},
                "ingredients": [("Carbonated Water", 1, False, False), ("Caramel IV", 2, False, True), ("Aspartame", 3, False, True), ("Acesulfame Potassium", 4, False, True)]
            },
            {
                "barcode": "8901058852898",
                "name": "Sparkling Mineral Spring Water with Lemon Essence",
                "brand": "AlpineWater",
                "category": "soft-drinks-sodas",
                "serving_size": "330ml",
                "nova_group": 1,
                "nutri_score": "A",  # Water is standard A
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 0.0, "fat_g": 0.0, "saturated_fat_g": 0.0, "carbohydrates_g": 0.0, "sugars_g": 0.0, "fiber_g": 0.0, "proteins_g": 0.0, "sodium_mg": 4.0, "salt_g": 0.01, "basis": "per 100ml"},
                "ingredients": [("Carbonated Water", 1, False, False)]
            },
            {
                "barcode": "8901058852899",
                "name": "Clear Lemon Lime Carbonated Soda",
                "brand": "CitrusJoy",
                "category": "soft-drinks-sodas",
                "serving_size": "300ml",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 0.85,  # Missing protein & fat declaration
                "nutrition": {"energy_kcal": 42.0, "carbohydrates_g": 10.5, "sugars_g": 10.5, "sodium_mg": 18.0, "salt_g": 0.045, "basis": "per 100ml"},
                "ingredients": [("Carbonated Water", 1, False, False), ("Sugar", 2, False, False), ("Citric Acid", 3, False, True), ("Sodium Benzoate", 4, False, True)]
            },
            {
                "barcode": "8901058852900",
                "name": "Orange Blast Sweetened Carbonated Drink",
                "brand": "SunGlow",
                "category": "soft-drinks-sodas",
                "serving_size": "250ml",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 52.0, "fat_g": 0.0, "saturated_fat_g": 0.0, "carbohydrates_g": 13.0, "sugars_g": 12.8, "fiber_g": 0.0, "proteins_g": 0.0, "sodium_mg": 24.0, "salt_g": 0.06, "basis": "per 100ml"},
                "ingredients": [("Carbonated Water", 1, False, False), ("Sugar", 2, False, False), ("Sunset Yellow FCF", 3, False, True), ("Citric Acid", 4, False, True)]
            },

            # --- Fruit Juices & Smoothies (4) ---
            {
                "barcode": "8901058852901",
                "name": "100% Pure Pressed Orange Juice",
                "brand": "GroveFresh",
                "category": "fruit-juices-smoothies",
                "serving_size": "200ml",
                "nova_group": 1,
                "nutri_score": "C",  # Juices contain natural sugars but no added sugar
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 45.0, "fat_g": 0.2, "saturated_fat_g": 0.0, "carbohydrates_g": 9.8, "sugars_g": 8.5, "fiber_g": 0.8, "proteins_g": 0.7, "sodium_mg": 2.0, "salt_g": 0.005, "fruits_vegetables_nuts_colza_walnut_olive_oils_pct": 100.0, "basis": "per 100ml"},
                "ingredients": [("Orange Juice Concentrate", 1, False, False), ("Water", 2, False, False)]
            },
            {
                "barcode": "8901058852902",
                "name": "Mango Nectar Sweetened Fruit Drink",
                "brand": "TropicalSip",
                "category": "fruit-juices-smoothies",
                "serving_size": "200ml",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 62.0, "fat_g": 0.1, "saturated_fat_g": 0.0, "carbohydrates_g": 15.2, "sugars_g": 14.8, "fiber_g": 0.4, "proteins_g": 0.3, "sodium_mg": 35.0, "salt_g": 0.08, "basis": "per 100ml"},
                "ingredients": [("Water", 1, False, False), ("Sugar", 2, False, False), ("Citric Acid", 3, False, True), ("Sunset Yellow FCF", 4, False, True)]
            },
            {
                "barcode": "8901058852903",
                "name": "Cold-Pressed Apple & Beetroot Nutrient Drink",
                "brand": "PureVital",
                "category": "fruit-juices-smoothies",
                "serving_size": "250ml",
                "nova_group": 1,
                "nutri_score": "B",
                "completeness": 0.88,  # Missing saturated fat
                "nutrition": {"energy_kcal": 38.0, "fat_g": 0.1, "carbohydrates_g": 8.6, "sugars_g": 7.2, "fiber_g": 1.5, "proteins_g": 0.8, "sodium_mg": 18.0, "salt_g": 0.045, "fruits_vegetables_nuts_colza_walnut_olive_oils_pct": 100.0, "basis": "per 100ml"},
                "ingredients": [("Apple Juice Concentrate", 1, False, False), ("Water", 2, False, False)]
            },
            {
                "barcode": "8901058852904",
                "name": "Mixed Berry Artificial Fruit Punch",
                "brand": "FlavorBlast",
                "category": "fruit-juices-smoothies",
                "serving_size": "200ml",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 0.70,  # Missing fiber & saturated fat
                "nutrition": {"energy_kcal": 58.0, "carbohydrates_g": 14.5, "sugars_g": 14.0, "proteins_g": 0.1, "sodium_mg": 45.0, "salt_g": 0.11, "basis": "per 100ml"},
                "ingredients": [("Water", 1, False, False), ("High Fructose Corn Syrup", 2, False, False), ("Citric Acid", 3, False, True), ("Tartrazine", 4, False, True)]
            },

            # --- Yoghurts & Fermented Dairy (4) ---
            {
                "barcode": "8901058852905",
                "name": "Authentic Plain Greek Yoghurt High Protein",
                "brand": "HellenicDairy",
                "category": "yoghurts-fermented-dairy",
                "serving_size": "150g",
                "nova_group": 1,
                "nutri_score": "A",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 75.0, "fat_g": 2.0, "saturated_fat_g": 1.2, "carbohydrates_g": 3.8, "sugars_g": 3.6, "fiber_g": 0.0, "proteins_g": 10.5, "sodium_mg": 45.0, "salt_g": 0.11, "basis": "per 100g"},
                "ingredients": [("Skimmed Milk", 1, False, False), ("Live Probiotic Cultures", 2, False, False)]
            },
            {
                "barcode": "8901058852906",
                "name": "Sweet Strawberry Flavoured Dessert Yoghurt",
                "brand": "BerryYum",
                "category": "yoghurts-fermented-dairy",
                "serving_size": "125g",
                "nova_group": 4,
                "nutri_score": "C",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 115.0, "fat_g": 3.2, "saturated_fat_g": 2.1, "carbohydrates_g": 18.0, "sugars_g": 16.5, "fiber_g": 0.3, "proteins_g": 3.5, "sodium_mg": 65.0, "salt_g": 0.16, "basis": "per 100g"},
                "ingredients": [("Milk Solids", 1, False, False), ("Sugar", 2, False, False), ("Live Probiotic Cultures", 3, False, False), ("Citric Acid", 4, False, True)]
            },
            {
                "barcode": "8901058852907",
                "name": "Zero Added Sugar Probiotic Natural Dahi",
                "brand": "VedaDairy",
                "category": "yoghurts-fermented-dairy",
                "serving_size": "100g",
                "nova_group": 1,
                "nutri_score": "A",
                "completeness": 0.88,  # Missing fiber (expected for dairy)
                "nutrition": {"energy_kcal": 60.0, "fat_g": 3.0, "saturated_fat_g": 1.8, "carbohydrates_g": 4.2, "sugars_g": 4.2, "proteins_g": 4.0, "sodium_mg": 50.0, "salt_g": 0.125, "basis": "per 100g"},
                "ingredients": [("Skimmed Milk", 1, False, False), ("Live Probiotic Cultures", 2, False, False)]
            },
            {
                "barcode": "8901058852908",
                "name": "Mango Cream Indulgent Greek Yoghurt",
                "brand": "VelvetLush",
                "category": "yoghurts-fermented-dairy",
                "serving_size": "100g",
                "nova_group": 3,
                "nutri_score": "C",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 130.0, "fat_g": 5.5, "saturated_fat_g": 3.6, "carbohydrates_g": 14.5, "sugars_g": 13.0, "fiber_g": 0.2, "proteins_g": 6.0, "sodium_mg": 55.0, "salt_g": 0.14, "basis": "per 100g"},
                "ingredients": [("Milk Solids", 1, False, False), ("Sugar", 2, False, False), ("Live Probiotic Cultures", 3, False, False)]
            },

            # --- Biscuits & Cookies (4) ---
            {
                "barcode": "8901058852909",
                "name": "100% Whole Wheat Fibre Digestive Biscuit",
                "brand": "NutriChoice",
                "category": "biscuits-cookies",
                "serving_size": "25g",
                "nova_group": 3,
                "nutri_score": "C",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 450.0, "fat_g": 16.5, "saturated_fat_g": 3.8, "carbohydrates_g": 65.0, "sugars_g": 14.0, "fiber_g": 6.5, "proteins_g": 9.2, "sodium_mg": 320.0, "salt_g": 0.8, "basis": "per 100g"},
                "ingredients": [("Whole Wheat Flour", 1, True, False), ("Sunflower Oil", 2, False, False), ("Brown Sugar", 3, False, False)]
            },
            {
                "barcode": "8901058852910",
                "name": "Chocolate Vanilla Double Cream Sandwich Biscuit",
                "brand": "ChocoTreat",
                "category": "biscuits-cookies",
                "serving_size": "30g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 510.0, "fat_g": 24.0, "saturated_fat_g": 11.5, "carbohydrates_g": 68.0, "sugars_g": 38.0, "fiber_g": 1.5, "proteins_g": 4.8, "sodium_mg": 410.0, "salt_g": 1.02, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Sugar", 2, False, False), ("Palm Oil", 3, False, False), ("Soy Lecithin", 4, False, True)]
            },
            {
                "barcode": "8901058852911",
                "name": "Oat & Roasted Almond Crisp Cookies",
                "brand": "GoldenOat",
                "category": "biscuits-cookies",
                "serving_size": "20g",
                "nova_group": 3,
                "nutri_score": "C",
                "completeness": 0.85,  # Missing trans fat
                "nutrition": {"energy_kcal": 465.0, "fat_g": 18.0, "saturated_fat_g": 4.2, "carbohydrates_g": 62.0, "sugars_g": 16.5, "fiber_g": 5.5, "proteins_g": 8.5, "sodium_mg": 280.0, "salt_g": 0.7, "basis": "per 100g"},
                "ingredients": [("Whole Rolled Oats", 1, True, False), ("Almonds", 2, False, False), ("Brown Sugar", 3, False, False)]
            },
            {
                "barcode": "8901058852912",
                "name": "Golden Butter Salted Tea Crackers",
                "brand": "TeaTime",
                "category": "biscuits-cookies",
                "serving_size": "25g",
                "nova_group": 3,
                "nutri_score": "D",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 485.0, "fat_g": 20.5, "saturated_fat_g": 9.8, "carbohydrates_g": 66.0, "sugars_g": 6.5, "fiber_g": 2.2, "proteins_g": 8.0, "sodium_mg": 780.0, "salt_g": 1.95, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Palm Oil", 2, False, False), ("Iodised Salt", 3, False, False)]
            },

            # --- Chips & Savory Snacks (4) ---
            {
                "barcode": "8901058852913",
                "name": "Slow Roasted Salt & Pepper Foxnuts (Makhana)",
                "brand": "SuperBite",
                "category": "chips-savory-snacks",
                "serving_size": "30g",
                "nova_group": 2,
                "nutri_score": "B",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 390.0, "fat_g": 9.5, "saturated_fat_g": 1.2, "carbohydrates_g": 68.0, "sugars_g": 0.5, "fiber_g": 7.5, "proteins_g": 11.0, "sodium_mg": 220.0, "salt_g": 0.55, "basis": "per 100g"},
                "ingredients": [("Sunflower Oil", 1, False, False), ("Iodised Salt", 2, False, False)]
            },
            {
                "barcode": "8901058852914",
                "name": "Classic Salted Deep Fried Potato Crisps",
                "brand": "CrispyLays",
                "category": "chips-savory-snacks",
                "serving_size": "30g",
                "nova_group": 3,
                "nutri_score": "D",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 545.0, "fat_g": 35.0, "saturated_fat_g": 14.5, "carbohydrates_g": 52.0, "sugars_g": 1.0, "fiber_g": 3.8, "proteins_g": 6.5, "sodium_mg": 580.0, "salt_g": 1.45, "basis": "per 100g"},
                "ingredients": [("Potato Flakes", 1, False, False), ("Palm Oil", 2, False, False), ("Iodised Salt", 3, False, False)]
            },
            {
                "barcode": "8901058852915",
                "name": "Spicy Masala Extruded Corn Puffs",
                "brand": "KurkureTreat",
                "category": "chips-savory-snacks",
                "serving_size": "28g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 560.0, "fat_g": 38.0, "saturated_fat_g": 16.0, "carbohydrates_g": 48.0, "sugars_g": 3.5, "fiber_g": 2.0, "proteins_g": 5.8, "sodium_mg": 890.0, "salt_g": 2.22, "basis": "per 100g"},
                "ingredients": [("Corn Flour", 1, False, False), ("Palm Oil", 2, False, False), ("Iodised Salt", 3, False, False), ("Monosodium Glutamate", 4, False, True), ("Citric Acid", 5, False, True)]
            },
            {
                "barcode": "8901058852916",
                "name": "Baked Beetroot & Sweet Potato Crisps",
                "brand": "TerraGreens",
                "category": "chips-savory-snacks",
                "serving_size": "35g",
                "nova_group": 3,
                "nutri_score": "C",
                "completeness": 0.85,  # Missing sugar details
                "nutrition": {"energy_kcal": 420.0, "fat_g": 14.0, "saturated_fat_g": 1.8, "carbohydrates_g": 64.0, "fiber_g": 8.0, "proteins_g": 5.5, "sodium_mg": 310.0, "salt_g": 0.77, "basis": "per 100g"},
                "ingredients": [("Extra Virgin Olive Oil", 1, False, False), ("Iodised Salt", 2, False, False)]
            },

            # --- Chocolates & Confectionery (4) ---
            {
                "barcode": "8901058852917",
                "name": "Single Origin 85% Dark Cocoa Chocolate",
                "brand": "NoirPrestige",
                "category": "chocolates-confectionery",
                "serving_size": "20g",
                "nova_group": 3,
                "nutri_score": "D",  # Dark chocolate has high saturated fat from cocoa butter, but very low sugar
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 580.0, "fat_g": 46.0, "saturated_fat_g": 28.0, "carbohydrates_g": 22.0, "sugars_g": 12.0, "fiber_g": 11.5, "proteins_g": 9.5, "sodium_mg": 15.0, "salt_g": 0.04, "basis": "per 100g"},
                "ingredients": [("Cocoa Solids", 1, False, False), ("Cocoa Butter", 2, False, False), ("Brown Sugar", 3, False, False)]
            },
            {
                "barcode": "8901058852918",
                "name": "Creamy Caramel Milk Chocolate Candy Bar",
                "brand": "DairyMelt",
                "category": "chocolates-confectionery",
                "serving_size": "45g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 535.0, "fat_g": 31.0, "saturated_fat_g": 18.5, "carbohydrates_g": 58.0, "sugars_g": 54.0, "fiber_g": 1.8, "proteins_g": 6.5, "sodium_mg": 160.0, "salt_g": 0.4, "basis": "per 100g"},
                "ingredients": [("Sugar", 1, False, False), ("Milk Solids", 2, False, False), ("Cocoa Butter", 3, False, False), ("Palm Oil", 4, False, False), ("Soy Lecithin", 5, False, True)]
            },
            {
                "barcode": "8901058852919",
                "name": "Whole Roasted Almond Silk Milk Chocolate",
                "brand": "CadenceSilk",
                "category": "chocolates-confectionery",
                "serving_size": "30g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 0.88,  # Missing fiber
                "nutrition": {"energy_kcal": 550.0, "fat_g": 35.0, "saturated_fat_g": 16.0, "carbohydrates_g": 50.0, "sugars_g": 44.0, "proteins_g": 8.8, "sodium_mg": 110.0, "salt_g": 0.28, "basis": "per 100g"},
                "ingredients": [("Sugar", 1, False, False), ("Almonds", 2, False, False), ("Milk Solids", 3, False, False), ("Cocoa Solids", 4, False, False)]
            },
            {
                "barcode": "8901058852920",
                "name": "Intense 70% Dark Chocolate with Orange Zest",
                "brand": "ArtisanCacao",
                "category": "chocolates-confectionery",
                "serving_size": "25g",
                "nova_group": 3,
                "nutri_score": "D",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 560.0, "fat_g": 40.0, "saturated_fat_g": 24.0, "carbohydrates_g": 34.0, "sugars_g": 26.0, "fiber_g": 8.5, "proteins_g": 7.5, "sodium_mg": 10.0, "salt_g": 0.025, "basis": "per 100g"},
                "ingredients": [("Cocoa Solids", 1, False, False), ("Sugar", 2, False, False), ("Cocoa Butter", 3, False, False)]
            },

            # --- Instant Noodles & Soups (4) ---
            {
                "barcode": "8901058852921",
                "name": "Steamed Millet & Buckwheat Healthy Noodles",
                "brand": "AncientGrain",
                "category": "instant-noodles-soups",
                "serving_size": "70g",
                "nova_group": 3,
                "nutri_score": "B",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 360.0, "fat_g": 3.5, "saturated_fat_g": 0.8, "carbohydrates_g": 72.0, "sugars_g": 2.5, "fiber_g": 8.5, "proteins_g": 12.0, "sodium_mg": 480.0, "salt_g": 1.2, "basis": "per 100g"},
                "ingredients": [("Whole Wheat Flour", 1, True, False), ("Sunflower Oil", 2, False, False), ("Iodised Salt", 3, False, False)]
            },
            {
                "barcode": "8901058852922",
                "name": "Classic Masala Deep Fried Instant Noodles",
                "brand": "QuickMeal",
                "category": "instant-noodles-soups",
                "serving_size": "70g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 470.0, "fat_g": 21.0, "saturated_fat_g": 10.5, "carbohydrates_g": 62.0, "sugars_g": 3.0, "fiber_g": 3.2, "proteins_g": 8.5, "sodium_mg": 1150.0, "salt_g": 2.88, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Palm Oil", 2, False, False), ("Iodised Salt", 3, False, False), ("Monosodium Glutamate", 4, False, True), ("Guar Gum", 5, False, True)]
            },
            {
                "barcode": "8901058852923",
                "name": "Korean Extra Spicy Cheese Hot Ramen",
                "brand": "SamyangTaste",
                "category": "instant-noodles-soups",
                "serving_size": "140g",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 510.0, "fat_g": 24.5, "saturated_fat_g": 12.0, "carbohydrates_g": 64.0, "sugars_g": 7.5, "fiber_g": 2.8, "proteins_g": 9.2, "sodium_mg": 1420.0, "salt_g": 3.55, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Palm Oil", 2, False, False), ("Sugar", 3, False, False), ("Monosodium Glutamate", 4, False, True)]
            },
            {
                "barcode": "8901058852924",
                "name": "100% Brown Rice Vermicelli Plain",
                "brand": "GreenPlatter",
                "category": "instant-noodles-soups",
                "serving_size": "50g",
                "nova_group": 1,
                "nutri_score": "A",
                "completeness": 0.88,  # Missing sugar
                "nutrition": {"energy_kcal": 355.0, "fat_g": 2.2, "saturated_fat_g": 0.4, "carbohydrates_g": 76.0, "fiber_g": 5.0, "proteins_g": 7.8, "sodium_mg": 12.0, "salt_g": 0.03, "basis": "per 100g"},
                "ingredients": [("Water", 1, False, False)]
            },

            # --- Dairy & Plant Drinks (4) ---
            {
                "barcode": "8901058852925",
                "name": "Unsweetened Pure California Almond Milk",
                "brand": "SilkMeadow",
                "category": "dairy-plant-drinks",
                "serving_size": "240ml",
                "nova_group": 3,
                "nutri_score": "B",  # Beverage without added sugar
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 22.0, "fat_g": 1.8, "saturated_fat_g": 0.2, "carbohydrates_g": 0.5, "sugars_g": 0.1, "fiber_g": 0.5, "proteins_g": 0.9, "sodium_mg": 58.0, "salt_g": 0.145, "basis": "per 100ml"},
                "ingredients": [("Water", 1, False, False), ("Almonds", 2, False, False), ("Guar Gum", 3, False, True), ("Iodised Salt", 4, False, False)]
            },
            {
                "barcode": "8901058852926",
                "name": "Rich Chocolate Flavoured Sweetened Milk",
                "brand": "MooTreat",
                "category": "dairy-plant-drinks",
                "serving_size": "200ml",
                "nova_group": 4,
                "nutri_score": "D",  # High liquid sugar in beverage
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 82.0, "fat_g": 2.8, "saturated_fat_g": 1.8, "carbohydrates_g": 11.5, "sugars_g": 10.8, "fiber_g": 0.4, "proteins_g": 3.2, "sodium_mg": 68.0, "salt_g": 0.17, "basis": "per 100ml"},
                "ingredients": [("Skimmed Milk", 1, False, False), ("Sugar", 2, False, False), ("Cocoa Powder", 3, False, False), ("Guar Gum", 4, False, True)]
            },
            {
                "barcode": "8901058852927",
                "name": "Traditional Plain Salted Spiced Buttermilk",
                "brand": "DesiAmrit",
                "category": "dairy-plant-drinks",
                "serving_size": "200ml",
                "nova_group": 1,
                "nutri_score": "B",
                "completeness": 0.88,  # Missing fiber (expected for dairy)
                "nutrition": {"energy_kcal": 28.0, "fat_g": 1.2, "saturated_fat_g": 0.8, "carbohydrates_g": 2.2, "sugars_g": 2.0, "proteins_g": 2.1, "sodium_mg": 180.0, "salt_g": 0.45, "basis": "per 100ml"},
                "ingredients": [("Water", 1, False, False), ("Live Probiotic Cultures", 2, False, False), ("Iodised Salt", 3, False, False)]
            },
            {
                "barcode": "8901058852928",
                "name": "Sweet Mango Flavoured Cream Lassi Drink",
                "brand": "RoyalPunjab",
                "category": "dairy-plant-drinks",
                "serving_size": "200ml",
                "nova_group": 4,
                "nutri_score": "E",
                "completeness": 0.85,  # Missing saturated fat
                "nutrition": {"energy_kcal": 95.0, "fat_g": 3.5, "carbohydrates_g": 13.8, "sugars_g": 13.2, "proteins_g": 2.5, "sodium_mg": 60.0, "salt_g": 0.15, "basis": "per 100ml"},
                "ingredients": [("Milk Solids", 1, False, False), ("Sugar", 2, False, False), ("Sunset Yellow FCF", 3, False, True)]
            },

            # --- Breads & Bakery (4) ---
            {
                "barcode": "8901058852929",
                "name": "100% Whole Wheat Stoneground Bread",
                "brand": "BakerCraft",
                "category": "breads-bakery",
                "serving_size": "50g",
                "nova_group": 3,
                "nutri_score": "A",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 245.0, "fat_g": 2.5, "saturated_fat_g": 0.5, "carbohydrates_g": 44.0, "sugars_g": 3.8, "fiber_g": 7.2, "proteins_g": 9.8, "sodium_mg": 380.0, "salt_g": 0.95, "basis": "per 100g"},
                "ingredients": [("Whole Wheat Flour", 1, True, False), ("Water", 2, False, False), ("Sunflower Oil", 3, False, False), ("Iodised Salt", 4, False, False)]
            },
            {
                "barcode": "8901058852930",
                "name": "Ultra Soft Refined White Sandwich Bread",
                "brand": "DailyLoaf",
                "category": "breads-bakery",
                "serving_size": "45g",
                "nova_group": 4,
                "nutri_score": "C",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 265.0, "fat_g": 3.0, "saturated_fat_g": 0.8, "carbohydrates_g": 51.0, "sugars_g": 5.5, "fiber_g": 2.0, "proteins_g": 7.5, "sodium_mg": 490.0, "salt_g": 1.22, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Water", 2, False, False), ("Sugar", 3, False, False), ("Palm Oil", 4, False, False), ("Iodised Salt", 5, False, False)]
            },
            {
                "barcode": "8901058852931",
                "name": "Artisan Sourdough Rye & Spelt Loaf",
                "brand": "LevainHouse",
                "category": "breads-bakery",
                "serving_size": "50g",
                "nova_group": 2,
                "nutri_score": "A",
                "completeness": 1.0,
                "nutrition": {"energy_kcal": 230.0, "fat_g": 1.8, "saturated_fat_g": 0.3, "carbohydrates_g": 45.0, "sugars_g": 1.5, "fiber_g": 6.8, "proteins_g": 9.0, "sodium_mg": 340.0, "salt_g": 0.85, "basis": "per 100g"},
                "ingredients": [("Whole Wheat Flour", 1, True, False), ("Water", 2, False, False), ("Iodised Salt", 3, False, False)]
            },
            {
                "barcode": "8901058852932",
                "name": "Sweet Fruit & Raisin Bakery Buns",
                "brand": "SweetBakes",
                "category": "breads-bakery",
                "serving_size": "60g",
                "nova_group": 4,
                "nutri_score": "D",
                "completeness": 0.85,  # Missing saturated fat
                "nutrition": {"energy_kcal": 310.0, "fat_g": 6.5, "carbohydrates_g": 56.0, "sugars_g": 22.0, "fiber_g": 2.5, "proteins_g": 6.5, "sodium_mg": 350.0, "salt_g": 0.88, "basis": "per 100g"},
                "ingredients": [("Refined Wheat Flour", 1, False, False), ("Sugar", 2, False, False), ("Palm Oil", 3, False, False)]
            }
        ]

        # Ensure valid GS1 Mod-10 barcodes for all seeded products
        for idx, pdata in enumerate(products_data, start=1):
            prefix = f"89010588{idx:04d}"
            pdata["barcode"] = prefix + str(calculate_gs1_check_digit(prefix))

        # Clear existing seeded products to ensure clean update
        db.query(Product).filter(Product.source == "seed").delete()
        db.commit()

        # Insert products, nutrition, and product-ingredients
        seeded_products_count = 0
        for pdata in products_data:
            existing_prod = db.query(Product).filter_by(barcode=pdata["barcode"]).first()
            if not existing_prod:
                cat_obj = category_map[pdata["category"]]
                prod = Product(
                    id=str(uuid.uuid4()),
                    barcode=pdata["barcode"],
                    name=pdata["name"],
                    brand=pdata["brand"],
                    category_id=cat_obj.id,
                    serving_size=pdata["serving_size"],
                    nova_group=pdata.get("nova_group"),
                    nutri_score_grade=pdata.get("nutri_score"),
                    data_completeness_score=pdata["completeness"],
                    data_source="local_seed",
                    source="seed"
                )
                db.add(prod)
                db.flush()

                # Add Nutrition
                nut = pdata["nutrition"]
                nut_obj = NutritionalInformation(
                    id=str(uuid.uuid4()),
                    product_id=prod.id,
                    energy_kcal=nut.get("energy_kcal"),
                    energy_kj=nut.get("energy_kj"),
                    fat_g=nut.get("fat_g"),
                    saturated_fat_g=nut.get("saturated_fat_g"),
                    trans_fat_g=nut.get("trans_fat_g"),
                    carbohydrates_g=nut.get("carbohydrates_g"),
                    sugars_g=nut.get("sugars_g"),
                    added_sugars_g=nut.get("added_sugars_g"),
                    fiber_g=nut.get("fiber_g"),
                    proteins_g=nut.get("proteins_g"),
                    sodium_mg=nut.get("sodium_mg"),
                    salt_g=nut.get("salt_g"),
                    fruits_vegetables_nuts_colza_walnut_olive_oils_pct=nut.get("fruits_vegetables_nuts_colza_walnut_olive_oils_pct"),
                    basis=nut.get("basis", "per 100g")
                )
                db.add(nut_obj)

                # Link Ingredients
                for item in pdata["ingredients"]:
                    ing_name = item[0]
                    pos = item[1]
                    is_wg = item[2]
                    is_all = item[3]
                    if ing_name in ingredient_map:
                        pi = ProductIngredient(
                            id=str(uuid.uuid4()),
                            product_id=prod.id,
                            ingredient_id=ingredient_map[ing_name].id,
                            position_order=pos,
                            is_whole_grain=is_wg,
                            is_allergen=is_all
                        )
                        db.add(pi)

                seeded_products_count += 1

        db.commit()
        logger.info(f"Seeded {seeded_products_count} products with nutrition and ingredient relations.")

        total_prods = db.query(Product).count()
        logger.info(f"Total products in database: {total_prods}")

    except Exception as e:
        db.rollback()
        logger.exception(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
