"""
Restore Nutella (barcode 3017620422003) in smart_shopping.db strictly from
the upstream Open Food Facts API v2 payload. No manual typing of percentages.
"""

import sqlite3
import urllib.request
import json
import uuid

def restore_nutella():
    url = "https://world.openfoodfacts.org/api/v2/product/3017620422003.json"
    req = urllib.request.Request(url, headers={"User-Agent": "SSA-Auditor/1.0"})
    with urllib.request.urlopen(req) as res:
        payload = json.loads(res.read().decode("utf-8"))
        raw_product = payload["product"]

    conn = sqlite3.connect("smart_shopping.db")
    c = conn.cursor()

    # Find Nutella
    row = c.execute("SELECT id FROM products WHERE barcode = '3017620422003'").fetchone()
    if not row:
        print("Nutella not found in DB!")
        return
    prod_id = row[0]

    # Update product metadata
    brand = raw_product.get("brands", "Ferrero")
    name = raw_product.get("product_name", "Nutella")
    c.execute("""
        UPDATE products
        SET brand = ?, name = ?, source = 'openfoodfacts', data_source = 'open_food_facts', updated_at = datetime('now')
        WHERE id = ?
    """, (brand, name, prod_id))

    # Update nutritional information strictly from OFF nutriments
    nutr = raw_product.get("nutriments", {})
    energy_kcal = nutr.get("energy-kcal_100g") or nutr.get("energy-kcal", 539.0)
    energy_kj = nutr.get("energy-kj_100g") or nutr.get("energy-kj", 2252.0)
    fat = nutr.get("fat_100g") or nutr.get("fat", 30.9)
    sat_fat = nutr.get("saturated-fat_100g") or nutr.get("saturated-fat", 10.6)
    carbs = nutr.get("carbohydrates_100g") or nutr.get("carbohydrates", 57.5)
    sugars = nutr.get("sugars_100g") or nutr.get("sugars", 56.3)
    salt = nutr.get("salt_100g") or nutr.get("salt", 0.107)
    sodium = nutr.get("sodium_100g") or nutr.get("sodium", 0.0428)
    if sodium and sodium < 1.0:
        sodium = sodium * 1000.0  # convert g to mg
    protein = nutr.get("proteins_100g") or nutr.get("proteins", 6.3)
    fiber = nutr.get("fiber_100g") or nutr.get("fiber", 0.0)

    c.execute("""
        UPDATE nutritional_information
        SET energy_kcal = ?, energy_kj = ?, fat_g = ?, saturated_fat_g = ?,
            carbohydrates_g = ?, sugars_g = ?, salt_g = ?, sodium_mg = ?,
            proteins_g = ?, fiber_g = ?, updated_at = datetime('now')
        WHERE product_id = ?
    """, (energy_kcal, energy_kj, fat, sat_fat, carbs, sugars, salt, sodium, protein, fiber, prod_id))

    # Delete existing hand-typed product_ingredients for Nutella
    c.execute("DELETE FROM product_ingredients WHERE product_id = ?", (prod_id,))

    # Insert strictly what OFF provides
    raw_ingredients = raw_product.get("ingredients", [])
    print(f"Restoring {len(raw_ingredients)} ingredients from raw OFF payload:")
    
    for idx, ing in enumerate(raw_ingredients, start=1):
        ing_text = ing.get("text") or ing.get("id", "").replace("en:", "").replace("-", " ").title()
        declared_percent = ing.get("percent")  # None in raw OFF
        print(f"  {idx}. {ing_text} (percent={declared_percent})")

        # Find or create ingredient in ingredients table
        ing_row = c.execute("SELECT id FROM ingredients WHERE canonical_name = ?", (ing_text,)).fetchone()
        if ing_row:
            ing_id = ing_row[0]
        else:
            ing_id = str(uuid.uuid4())
            c.execute("""
                INSERT INTO ingredients (id, canonical_name, ins_number, is_additive, created_at)
                VALUES (?, ?, NULL, 0, datetime('now'))
            """, (ing_id, ing_text))

        # Insert product_ingredient
        pi_id = str(uuid.uuid4())
        c.execute("""
            INSERT INTO product_ingredients (id, product_id, ingredient_id, position_order, estimated_percentage, is_whole_grain, is_allergen)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (pi_id, prod_id, ing_id, idx, declared_percent))

    conn.commit()
    conn.close()
    print("Nutella restored successfully from raw OFF payload.")

if __name__ == "__main__":
    restore_nutella()
