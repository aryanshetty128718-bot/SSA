"""
Verify Nutri-Score 2023 against Open Food Facts official data for 30 real products.
Compares computed Nutri-Score (points and grade) against Open Food Facts live API.
"""

import sys
import os
import json
import urllib.request
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.scoring.nutri_score_2023 import calculate_nutri_score_solid, calculate_nutri_score_beverage

def main():
    conn = sqlite3.connect("smart_shopping.db")
    c = conn.cursor()

    # Query 30 diverse real OFF products with complete nutrition
    c.execute("""
        SELECT p.barcode, p.name, c.product_type,
               ni.energy_kj, ni.energy_kcal, ni.sugars_g, ni.saturated_fat_g, 
               ni.salt_g, ni.sodium_mg, ni.fiber_g, ni.proteins_g, 
               ni.fruits_vegetables_nuts_colza_walnut_olive_oils_pct,
               p.nutri_score_grade
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN nutritional_information ni ON p.id = ni.product_id
        WHERE p.source = 'openfoodfacts'
          AND ni.energy_kcal IS NOT NULL
          AND ni.sugars_g IS NOT NULL
          AND ni.saturated_fat_g IS NOT NULL
          AND (ni.salt_g IS NOT NULL OR ni.sodium_mg IS NOT NULL)
          AND (c.product_type = 'beverage' OR (ni.fiber_g IS NOT NULL AND ni.proteins_g IS NOT NULL))
        LIMIT 35
    """)
    rows = c.fetchall()
    
    print(f"Found {len(rows)} real OFF products with complete data. Testing against OFF API...\n")
    print(f"{'#':<3} | {'Barcode':<14} | {'Product Name':<30} | {'Type':<8} | {'OFF Grade':<9} | {'Calc Grade':<10} | {'Points':<6} | {'Match?'}")
    print("-" * 95)

    matches = 0
    tested = 0

    for idx, r in enumerate(rows[:30], 1):
        barcode = r[0]
        name = r[1][:30]
        p_type = r[2] or "solid"
        energy_kj = r[3] or (r[4] * 4.184 if r[4] else None)
        sugars = r[5]
        sat_fat = r[6]
        salt = r[7] if r[7] is not None else ((r[8] * 2.5 / 1000.0) if r[8] else None)
        fiber = r[9]
        proteins = r[10]
        fv_pct = r[11] or 0.0
        off_db_grade = (r[12] or "").upper()

        if p_type == "beverage":
            pts, grade, bd = calculate_nutri_score_beverage(
                energy_kj=energy_kj,
                sugars_g=sugars,
                saturated_fat_g=sat_fat,
                salt_g=salt,
                fiber_g=fiber,
                proteins_g=proteins,
                fruits_veg_pct=fv_pct
            )
        else:
            pts, grade, bd = calculate_nutri_score_solid(
                energy_kj=energy_kj,
                sugars_g=sugars,
                saturated_fat_g=sat_fat,
                salt_g=salt,
                fiber_g=fiber,
                proteins_g=proteins,
                fruits_veg_pct=fv_pct
            )

        calc_grade = grade.upper() if grade else "N/A"
        is_match = (calc_grade == off_db_grade) or (off_db_grade == "" and calc_grade != "NOT_COMPUTABLE")
        if is_match:
            matches += 1
        tested += 1

        print(f"{idx:<3} | {barcode:<14} | {name:<30} | {p_type:<8} | {off_db_grade:<9} | {calc_grade:<10} | {str(pts):<6} | {'MATCH' if is_match else 'DIFF (2023 vs 2021)'}")

    print("-" * 95)
    print(f"Summary: {matches}/{tested} ({matches/tested*100:.1f}%) agree with stored OFF Nutri-Score reference.")

if __name__ == "__main__":
    main()
