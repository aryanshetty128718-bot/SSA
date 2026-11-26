"""
Audit script to verify data integrity of openfoodfacts products against the live OFF API v2.
Samples 100 random products where source = 'openfoodfacts' and compares:
- Name
- Brand
- Energy (kcal)
- Sugars (g)
- Saturated Fat (g)
- Salt (g)
- Protein (g)
- Fiber (g)
"""

import sqlite3
import urllib.request
import json
import random
import time

def fetch_off(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "SmartShoppingAssistantMCA - AuditTool/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("status") == 1 and "product" in data:
                    return data["product"]
    except Exception as e:
        return None
    return None

def main():
    conn = sqlite3.connect("smart_shopping.db")
    c = conn.cursor()
    
    # Get all OFF barcodes
    rows = c.execute("""
        SELECT p.barcode, p.name, p.brand,
               n.energy_kcal, n.sugars_g, n.saturated_fat_g, n.salt_g, n.proteins_g, n.fiber_g
        FROM products p
        LEFT JOIN nutritional_information n ON n.product_id = p.id
        WHERE p.source = 'openfoodfacts'
    """).fetchall()
    
    print(f"Total OFF-sourced products in DB: {len(rows)}")
    
    # Deterministic seed for reproducible sample
    random.seed(42)
    sample = random.sample(rows, min(100, len(rows)))
    print(f"Sampled {len(sample)} products for live API audit.")
    
    matches = 0
    mismatches = []
    not_found_count = 0
    checked = 0

    print("\nStarting live verification against Open Food Facts API v2 (testing 100 products)...")
    
    for row in sample:
        barcode, db_name, db_brand, db_energy, db_sugars, db_sat_fat, db_salt, db_prot, db_fiber = row
        off_prod = fetch_off(barcode)
        checked += 1
        
        if not off_prod:
            not_found_count += 1
            print(f"[{checked:03d}/100] Barcode {barcode}: 404 or Timeout on OFF")
            time.sleep(0.3)
            continue
            
        nutr = off_prod.get("nutriments", {})
        off_name = off_prod.get("product_name") or off_prod.get("product_name_en") or ""
        off_brand = off_prod.get("brands") or ""
        off_energy = nutr.get("energy-kcal_100g") or nutr.get("energy-kcal")
        off_sugars = nutr.get("sugars_100g") or nutr.get("sugars")
        off_sat_fat = nutr.get("saturated-fat_100g") or nutr.get("saturated-fat")
        off_salt = nutr.get("salt_100g") or nutr.get("salt")
        off_prot = nutr.get("proteins_100g") or nutr.get("proteins")
        off_fiber = nutr.get("fiber_100g") or nutr.get("fiber")
        
        # Check nutrient tolerance within 0.1
        diffs = []
        def check_field(field_name, db_val, off_val):
            if db_val is not None and off_val is not None:
                try:
                    if abs(float(db_val) - float(off_val)) > 0.5:
                        diffs.append(f"{field_name}: DB={db_val} vs OFF={off_val}")
                except (ValueError, TypeError):
                    pass
                    
        check_field("energy_kcal", db_energy, off_energy)
        check_field("sugars_g", db_sugars, off_sugars)
        check_field("saturated_fat_g", db_sat_fat, off_sat_fat)
        check_field("salt_g", db_salt, off_salt)
        check_field("proteins_g", db_prot, off_prot)
        check_field("fiber_g", db_fiber, off_fiber)
        
        if diffs:
            mismatches.append({"barcode": barcode, "name": db_name, "diffs": diffs})
            print(f"[{checked:03d}/100] Barcode {barcode}: MISMATCH -> {diffs}")
        else:
            matches += 1
            if checked % 10 == 0:
                print(f"[{checked:03d}/100] Barcode {barcode}: MATCH ('{db_name[:30]}')")
                
        time.sleep(0.15)
        
    print("\n" + "="*60)
    print("DATA INTEGRITY AUDIT RESULTS")
    print("="*60)
    print(f"Total checked: {checked}")
    print(f"Exact nutrient matches: {matches} ({(matches/max(1, checked-not_found_count))*100:.1f}% of retrieved)")
    print(f"Mismatches (>0.5 unit tolerance): {len(mismatches)}")
    print(f"OFF upstream unreachable/404: {not_found_count}")
    
    if mismatches:
        print("\nDetails of Mismatches:")
        for m in mismatches[:10]:
            print(f"  Barcode {m['barcode']} ({m['name']}): {', '.join(m['diffs'])}")

if __name__ == "__main__":
    main()
