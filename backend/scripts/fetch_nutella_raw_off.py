import urllib.request
import json

url = "https://world.openfoodfacts.org/api/v2/product/3017620422003.json"
req = urllib.request.Request(url, headers={"User-Agent": "SmartShoppingAssistant/1.0 (MCA Project Integrity Audit)"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        p = data.get("product", {})
        print("Product Name:", p.get("product_name"))
        print("Brands:", p.get("brands"))
        print("Ingredients Text:", p.get("ingredients_text"))
        print("Ingredients Raw:")
        for ing in p.get("ingredients", []):
            print("  ", ing.get("text"), "| id:", ing.get("id"), "| percent_estimate:", ing.get("percent_estimate"), "| percent:", ing.get("percent"))
        print("\nNutriments:")
        for k in ["energy-kcal_100g", "energy-kj_100g", "sugars_100g", "fat_100g", "saturated-fat_100g", "sodium_100g", "salt_100g", "proteins_100g", "fiber_100g", "fruits-vegetables-nuts-estimate-from-ingredients_100g", "fruits-vegetables-legumes-estimate-from-ingredients_100g"]:
            print(f"  {k}: {p.get('nutriments', {}).get(k)}")
        print("\nNutriscore 2023 tags:", p.get("nutriscore_2023_tags"))
        print("Nutriscore grade:", p.get("nutriscore_grade"))
        print("Nutriscore score/points:", p.get("nutriscore_score"))
        print("Nutriscore 2023 data:")
        print(json.dumps(p.get("nutriscore", {}), indent=2))
except Exception as e:
    print("Error fetching Nutella:", e)
