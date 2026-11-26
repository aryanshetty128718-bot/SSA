import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.scoring.calculator import compute_product_analysis

beverages = [
    ("Sparkling Water", {"sugars_g": 0.0, "energy_kcal": 0.0, "saturated_fat_g": 0.0, "sodium_mg": 5.0}, []),
    ("Diet Cola", {"sugars_g": 0.0, "energy_kcal": 1.0, "saturated_fat_g": 0.0, "sodium_mg": 10.0}, [{"canonical_name": "Aspartame", "ins_number": "INS 951", "is_additive": True}]),
    ("100% Orange Juice", {"sugars_g": 8.8, "energy_kcal": 42.0, "saturated_fat_g": 0.1, "sodium_mg": 2.0}, [{"canonical_name": "Orange juice", "is_whole_grain": False}]),
    ("Regular Cola", {"sugars_g": 10.6, "energy_kcal": 42.0, "saturated_fat_g": 0.0, "sodium_mg": 10.0}, [{"canonical_name": "Carbonated water"}, {"canonical_name": "Sugar"}, {"canonical_name": "Caramel color", "ins_number": "INS 150d", "is_additive": True}]),
    ("Mango Nectar", {"sugars_g": 13.0, "energy_kcal": 55.0, "saturated_fat_g": 0.1, "sodium_mg": 5.0}, [{"canonical_name": "Water"}, {"canonical_name": "Mango pulp"}, {"canonical_name": "Sugar"}])
]

print("=== Beverage Ranking Verification ===")
for name, nutr, ings in beverages:
    res = compute_product_analysis("beverage", nutr, ings)
    print(f"{name:20s}: Overall Score = {res['overall_score']:5.1f} | Band = {res['score_band']}")
