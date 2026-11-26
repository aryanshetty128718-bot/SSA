"""
Script to compare SSA-computed Nutri-Score 2023 points and grades
against Open Food Facts' official Nutri-Score 2023 points and grades
for at least 30 real products with official OFF Nutri-Score 2023 data.
"""

import sqlite3
import urllib.request
import json
from app.scoring.nutri_score_2023 import (
    calculate_nutri_score_solid,
    calculate_nutri_score_beverage
)

def fetch_off_nutriscore(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "SSA-Auditor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                prod = data.get("product", {})
                ns_data = prod.get("nutriscore", {}).get("2023", {})
                if not ns_data:
                    ns_data = prod.get("nutriscore_data", {})
                return {
                    "grade": prod.get("nutriscore_grade", "").upper(),
                    "score": ns_data.get("score"),
                    "category": prod.get("nutriscore_2023_tags", [])
                }
    except Exception:
        pass
    return None

def main():
    conn = sqlite3.connect("smart_shopping.db")
    c = conn.cursor()

    query = """
        SELECT p.barcode, p.name, p.brand, c.product_type,
               n.energy_kcal, n.energy_kj, n.sugars_g, n.saturated_fat_g,
               n.salt_g, n.fiber_g, n.proteins_g,
               n.fruits_vegetables_nuts_colza_walnut_olive_oils_pct,
               p.nutri_score_grade
        FROM products p
        JOIN categories c ON c.id = p.category_id
        JOIN nutritional_information n ON n.product_id = p.id
        WHERE p.source = 'openfoodfacts'
          AND n.sugars_g IS NOT NULL
          AND n.saturated_fat_g IS NOT NULL
          AND n.salt_g IS NOT NULL
          AND (c.product_type = 'beverage' OR (n.fiber_g IS NOT NULL AND n.proteins_g IS NOT NULL))
        LIMIT 120
    """
    rows = c.execute(query).fetchall()

    results = []
    print("=" * 105, flush=True)
    print("NUTRI-SCORE 2023 REVISION: 30-PRODUCT REAL OPEN FOOD FACTS COMPARISON TABLE", flush=True)
    print("=" * 105, flush=True)
    print(f"{'Barcode':<14} | {'Product Name':<30} | {'Type':<8} | {'SSA Pts':<7} | {'SSA Gr':<6} | {'OFF Pts':<7} | {'OFF Gr':<6} | {'Match?':<6}", flush=True)
    print("-" * 105, flush=True)

    for r in rows:
        barcode, name, brand, prod_type, kcal, kj, sugars, sat_fat, salt, fiber, prot, fv_pct, db_grade = r
        if not kj and kcal:
            kj = kcal * 4.184

        if prod_type == "beverage":
            is_water = "water" in (name or "").lower()
            ssa_pts, ssa_grade, breakdown = calculate_nutri_score_beverage(
                energy_kj=kj,
                sugars_g=sugars,
                saturated_fat_g=sat_fat,
                salt_g=salt,
                fiber_g=fiber or 0.0,
                proteins_g=prot or 0.0,
                fruits_veg_pct=fv_pct or 0.0,
                has_sweeteners=False,
                is_water=is_water
            )
        else:
            ssa_pts, ssa_grade, breakdown = calculate_nutri_score_solid(
                energy_kj=kj,
                sugars_g=sugars,
                saturated_fat_g=sat_fat,
                salt_g=salt,
                fiber_g=fiber,
                proteins_g=prot,
                fruits_veg_pct=fv_pct or 0.0
            )

        off_info = fetch_off_nutriscore(barcode)
        if not off_info or off_info["score"] is None or not off_info["grade"]:
            continue

        off_pts = off_info["score"]
        off_gr = off_info["grade"]
        ssa_gr_upper = ssa_grade.upper()

        pts_match = (ssa_pts == off_pts)
        grade_match = (ssa_gr_upper == off_gr)
        match_str = "YES" if (pts_match and grade_match) else ("GRADE" if grade_match else "NO")

        results.append({
            "barcode": barcode,
            "name": name[:30],
            "type": prod_type,
            "ssa_pts": ssa_pts,
            "ssa_grade": ssa_gr_upper,
            "off_pts": off_pts,
            "off_grade": off_gr,
            "match": match_str
        })

        print(f"{barcode:<14} | {name[:30]:<30} | {prod_type:<8} | {str(ssa_pts):<7} | {ssa_gr_upper:<6} | {str(off_pts):<7} | {off_gr:<6} | {match_str:<6}", flush=True)

        if len(results) >= 30:
            break

    print("-" * 105, flush=True)
    print(f"Total Products Evaluated: {len(results)}", flush=True)
    if results:
        full_matches = sum(1 for r in results if r["match"] == "YES")
        grade_matches = sum(1 for r in results if r["match"] in ("YES", "GRADE"))
        print(f"Exact Point & Grade Matches: {full_matches} / {len(results)} ({full_matches/len(results)*100:.1f}%)", flush=True)
        print(f"Letter Grade Agreement:     {grade_matches} / {len(results)} ({grade_matches/len(results)*100:.1f}%)", flush=True)

if __name__ == "__main__":
    main()
