import urllib.request
import json
import sys

test_barcodes = [
    '3017620422003', # Nutella
    '0011110849250', # Penne Rigate
    '8901058852431', # Maggi 2-Minute Noodles
    '8901030999948', # Red Label Tea
    '0028400064057', # Lay's Classic Potato Chips
    '0049000000443', # Coca Cola
    '8000500310427', # Barilla Spaghetti
]

print(f"Testing {len(test_barcodes)} diverse products across backend APIs...\n")

for bc in test_barcodes:
    print(f"==================================================")
    print(f"Barcode: {bc}")
    print(f"==================================================")

    # 1. Product details
    try:
        req = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/products/barcode/{bc}")
        with urllib.request.urlopen(req) as r:
            prod = json.loads(r.read())
            pname = prod.get("name")
            pbrand = prod.get("brand")
            nutr = prod.get("nutrition") or {}
            ings = prod.get("ingredients") or []
            print(f"1. /products/barcode/{bc}:")
            print(f"   Name: {pname} | Brand: {pbrand}")
            print(f"   Nutrition: energy={nutr.get('energy_kcal')} kcal, sugars={nutr.get('sugars_g')} g, fat={nutr.get('fat_g')} g")
            print(f"   Ingredients Count: {len(ings)} -> {[i.get('ingredient_name') for i in ings[:4]]}")
    except Exception as e:
        print(f"1. /products/barcode/{bc} ERROR: {e}")

    # 2. Product Analysis
    try:
        req = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/analysis/{bc}")
        with urllib.request.urlopen(req) as r:
            ana = json.loads(r.read())
            score = ana.get("overall_project_score")
            grade = ana.get("official_reference", {}).get("grade")
            nutr = ana.get("nutrition") or {}
            ings = ana.get("ingredients") or []
            print(f"2. /analysis/{bc}:")
            print(f"   Project Score: {score} | Nutri-Score: {grade}")
            print(f"   Nutrition attached: {bool(nutr)} (sugars={nutr.get('sugars_g')} g)")
            print(f"   Ingredients attached: {len(ings)} items")
    except Exception as e:
        print(f"2. /analysis/{bc} ERROR: {e}")

    # 3. Recommendations
    try:
        req = urllib.request.Request(f"http://127.0.0.1:8000/api/v1/recommendations/{bc}")
        with urllib.request.urlopen(req) as r:
            recs = json.loads(r.read())
            alt_list = recs.get("recommendations") or []
            print(f"3. /recommendations/{bc}:")
            print(f"   Alternatives Count: {len(alt_list)}")
            for idx, alt in enumerate(alt_list[:3], 1):
                print(f"   [{idx}] {alt.get('name')} ({alt.get('brand')})")
                print(f"       Tier: {alt.get('tier')} | Badge: {alt.get('tier_badge')}")
                print(f"       Score: {alt.get('overall_score')} (+{alt.get('score_improvement')} improvement)")
                print(f"       Ingredient Sim: {alt.get('ingredient_similarity')} | Nutrient Sim: {alt.get('nutrient_similarity')}")
    except Exception as e:
        print(f"3. /recommendations/{bc} ERROR: {e}")
    print()
