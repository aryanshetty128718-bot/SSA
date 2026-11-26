import urllib.request
import json
import sqlite3

barcode = "0012700158042"

print(f"--- 1. Querying Live Open Food Facts API for barcode {barcode} ---")
url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
req = urllib.request.Request(url, headers={"User-Agent": "SmartShoppingAssistant/1.0 (MCA Project Eval)"})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        off_data = json.loads(r.read().decode('utf-8'))
        p = off_data.get("product", {})
        print("OFF product found:", p.get("product_name"), "| Brand:", p.get("brands"))
        nutr = p.get("nutriments", {})
        print("OFF Nutriments snippet:")
        for k in ["energy-kcal_100g", "sugars_100g", "saturated-fat_100g", "sodium_100g", "proteins_100g", "fiber_100g", "carbohydrates_100g"]:
            print(f"  {k}: {nutr.get(k)}")
        print("OFF nutriscore_2023_tags:", p.get("nutriscore_2023_tags"))
        print("OFF nutriscore_grade:", p.get("nutriscore_grade"))
except Exception as e:
    print("Could not query OFF live:", e)

print(f"\n--- 2. Database Record for {barcode} ---")
conn = sqlite3.connect('smart_shopping.db')
c = conn.cursor()
c.execute("""
    SELECT p.barcode, p.name, p.brand, p.source, p.data_completeness_score, ps.overall_project_score, ps.confidence_score, ps.official_nutri_score_grade
    FROM products p
    LEFT JOIN product_scores ps ON p.id = ps.product_id
    WHERE p.barcode = ?
""", (barcode,))
row = c.fetchone()
print("DB Product row:", row)

c.execute("SELECT * FROM nutritional_information WHERE product_id = (SELECT id FROM products WHERE barcode = ?)", (barcode,))
print("DB Nutrition:", c.fetchone())
conn.close()

print(f"\n--- 3. API Analysis Endpoint for {barcode} ---")
try:
    with urllib.request.urlopen(f"http://127.0.0.1:8000/api/v1/products/{barcode}/analysis") as r:
        an = json.loads(r.read().decode('utf-8'))
        print("Score:", an.get("overall_project_score"))
        print("Confidence:", an.get("confidence_score"), an.get("confidence_level"))
        print("Missing parameters:", an.get("missing_parameters"))
        print("Official reference:", an.get("official_reference"))
        print("Sub scores:", an.get("sub_scores"))
except Exception as e:
    print("API analysis error:", e)
