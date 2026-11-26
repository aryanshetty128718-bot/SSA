import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.scoring.calculator import compute_product_analysis

# Test with modified criteria
crit_override = {
    "product_type": "beverage",
    "parameters": {
        "sugars": {"weight": 0.40, "t_low": 1.0, "t_high": 5.0},
        "saturated_fat": {"weight": 0.15, "t_low": 0.75, "t_high": 2.5},
        "energy": {"weight": 0.15, "t_low": 15.0, "t_high": 35.0},
        "ingredient_quality": {"weight": 0.15},
        "additives": {"weight": 0.15}
    }
}

beverages = [
    ("Sparkling Water", {"sugars_g": 0.0, "energy_kcal": 0.0, "saturated_fat_g": 0.0, "sodium_mg": 5.0}, []),
    ("Diet Cola", {"sugars_g": 0.0, "energy_kcal": 1.0, "saturated_fat_g": 0.0, "sodium_mg": 10.0}, [{"canonical_name": "Aspartame", "ins_number": "INS 951", "is_additive": True}]),
    ("100% Orange Juice", {"sugars_g": 8.8, "energy_kcal": 42.0, "saturated_fat_g": 0.1, "sodium_mg": 2.0}, [{"canonical_name": "Orange juice", "is_whole_grain": False}]),
    ("Regular Cola", {"sugars_g": 10.6, "energy_kcal": 42.0, "saturated_fat_g": 0.0, "sodium_mg": 10.0}, [{"canonical_name": "Carbonated water"}, {"canonical_name": "Sugar"}, {"canonical_name": "Caramel color", "ins_number": "INS 150d", "is_additive": True}]),
    ("Mango Nectar", {"sugars_g": 13.0, "energy_kcal": 55.0, "saturated_fat_g": 0.1, "sodium_mg": 5.0}, [{"canonical_name": "Water"}, {"canonical_name": "Mango pulp"}, {"canonical_name": "Sugar"}]),
    ("Coconut Cream 20% SatFat", {"sugars_g": 0.0, "energy_kcal": 297.0, "saturated_fat_g": 14.0, "sodium_mg": 50.0}, [])
]

for name, nutr, ings in beverages:
    res = compute_product_analysis("beverage", nutr, ings, criteria_override=crit_override)
    print(f"{name:26s}: Overall Score = {res['overall_score']:5.1f} | Band = {res['score_band']}")
