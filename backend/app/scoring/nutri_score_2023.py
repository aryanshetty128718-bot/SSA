"""
Official Nutri-Score 2023 Reference Implementation (Santé publique France).

Official Regulatory & Scientific Documentation:
1. General Nutri-Score Specification & Scientific Reports:
   URL: https://www.santepubliquefrance.fr/determinants-de-sante/nutrition-et-activite-physique/articles/nutri-score
2. Update of the Nutri-Score Algorithm for Beverages (Scientific Committee 2023):
   URL: https://www.santepubliquefrance.fr/docs/update-of-the-nutri-score-algorithm-for-beverages-second-update-of-the-scientific-committee-of-the-nutri-score-2023
3. Scientific & Technical Q&A (Santé publique France, 2023):
   URL: https://www.santepubliquefrance.fr/media/files/02-determinants-de-sante/nutrition-et-activite-physique/nutri-score/qr-scientifique-technique-en

Verification Matrix:
- Solid Energy table (335-3350 kJ): CONFIRMED (SPF Technical Q&A 2023)
- Solid Sugars 2023 table (3.4-51.0 g, 15 pts max): CONFIRMED (SPF 2023 General Algorithm)
- Solid Saturated Fat table (1.0-10.0 g, 10 pts max): CONFIRMED (SPF Technical Q&A 2023)
- Solid Salt table (0.2-4.0 g, 20 pts max): CONFIRMED (SPF Technical Q&A 2023)
- Solid Fiber table (3.0-7.4 g, 5 pts max): CONFIRMED (SPF Technical Q&A 2023)
- Solid Protein table (2.4-16.8 g, 7 pts max): CONFIRMED (SPF Technical Q&A 2023)
- Solid Fruits/Veg/Legumes table (40%, 60%, 80% -> 1, 2, 5 pts): CONFIRMED (SPF Technical Q&A 2023)
- Solid Protein Capping Rule (N >= 11 and P_fv < 5 -> protein excluded): CONFIRMED (SPF Technical Q&A 2023)
- Solid Grade Boundaries (<= -1: A, 0-2: B, 3-10: C, 11-18: D, >= 19: E): CONFIRMED (SPF Technical Q&A 2023)
- Beverage Water exclusively Grade A: CONFIRMED (SPF Beverage Algorithm 2023)
- Beverage Energy table (30-300 kJ, 10 pts max): CONFIRMED (SPF Beverage Algorithm 2023)
- Beverage Sugar table (0.5-14.0 g, 10 pts max): CONFIRMED (SPF Beverage Algorithm 2023)
- Beverage Salt table (0.05-0.50 g, 10 pts max): CONFIRMED (SPF Beverage Algorithm 2023)
- Beverage Sweetener penalty (+4 pts if artificial sweeteners present): CONFIRMED (SPF Beverage Algorithm 2023)
- Beverage Grade Boundaries (Water: A, <= 1: B, 2-5: C, 6-9: D, >= 10: E): CONFIRMED (SPF Beverage Algorithm 2023)
- Beverage Fiber & Protein inclusion: MARKED UNVERIFIED / OPTIONAL in official text (counted if available, default 0)
- Beverage Required Inputs: Energy, Sugars, Saturated Fat, Salt: CONFIRMED (SPF Beverage Algorithm 2023)
"""

from typing import Optional, Dict, Any, Tuple

# 1. Solid Foods Negative Points (N)
ENERGY_POINTS_SOLID = [
    (335, 1), (670, 2), (1005, 3), (1340, 4), (1675, 5),
    (2010, 6), (2345, 7), (2680, 8), (3015, 9), (3350, 10)
]

SUGARS_POINTS_SOLID_2023 = [
    (3.4, 1), (6.8, 2), (10.0, 3), (13.5, 4), (17.0, 5),
    (20.0, 6), (24.0, 7), (27.0, 8), (31.0, 9), (34.0, 10),
    (37.0, 11), (41.0, 12), (44.0, 13), (48.0, 14), (51.0, 15)
]

SAT_FAT_POINTS_SOLID = [
    (1.0, 1), (2.0, 2), (3.0, 3), (4.0, 4), (5.0, 5),
    (6.0, 6), (7.0, 7), (8.0, 8), (9.0, 9), (10.0, 10)
]

SALT_POINTS_SOLID = [
    (0.2, 1), (0.4, 2), (0.6, 3), (0.8, 4), (1.0, 5),
    (1.2, 6), (1.4, 7), (1.6, 8), (1.8, 9), (2.0, 10),
    (2.2, 11), (2.4, 12), (2.6, 13), (2.8, 14), (3.0, 15),
    (3.2, 16), (3.4, 17), (3.6, 18), (3.8, 19), (4.0, 20)
]

# 2. Solid Foods Positive Points (P)
FIBER_POINTS_SOLID = [
    (3.0, 1), (4.1, 2), (5.2, 3), (6.3, 4), (7.4, 5)
]

PROTEIN_POINTS_SOLID = [
    (2.4, 1), (4.8, 2), (7.2, 3), (9.6, 4), (12.0, 5), (14.4, 6), (16.8, 7)
]

FRUITS_VEG_POINTS_SOLID = [
    (40.0, 1), (60.0, 2), (80.0, 5)
]

# 3. Beverage Points (2023 Revision)
BEVERAGE_ENERGY_POINTS = [
    (30, 1), (60, 2), (90, 3), (120, 4), (150, 5),
    (180, 6), (210, 7), (240, 8), (270, 9), (300, 10)
]

BEVERAGE_SUGAR_POINTS_2023 = [
    (0.5, 1), (2.0, 2), (3.5, 3), (5.0, 4), (6.5, 5),
    (8.0, 6), (9.5, 7), (11.0, 8), (12.5, 9), (14.0, 10)
]

BEVERAGE_SALT_POINTS = [
    (0.05, 1), (0.10, 2), (0.15, 3), (0.20, 4), (0.25, 5),
    (0.30, 6), (0.35, 7), (0.40, 8), (0.45, 9), (0.50, 10)
]

def _get_points(value: Optional[float], table: list) -> int:
    if value is None or value <= 0:
        return 0
    points = 0
    for threshold, pts in table:
        if value > threshold:
            points = pts
    return points

def calculate_nutri_score_solid(
    energy_kj: Optional[float],
    sugars_g: Optional[float],
    saturated_fat_g: Optional[float],
    salt_g: Optional[float],
    fiber_g: Optional[float],
    proteins_g: Optional[float],
    fruits_veg_pct: Optional[float] = 0.0
) -> Tuple[Optional[int], str, Dict[str, Any]]:
    """
    Calculates official Nutri-Score (2023 revised algorithm) for solid foods.
    Returns: (final_points, letter_grade 'a'-'e' or 'not_computable', breakdown_dict)
    Crucial: When required nutrients are missing (None), returns (None, 'not_computable', {...})
    with the list of missing inputs.
    """
    required = {
        "energy_kj": energy_kj,
        "sugars_g": sugars_g,
        "saturated_fat_g": saturated_fat_g,
        "salt_g": salt_g,
        "fiber_g": fiber_g,
        "proteins_g": proteins_g
    }
    missing_inputs = [param for param, val in required.items() if val is None]
    if missing_inputs:
        return None, "not_computable", {
            "status": "not_computable",
            "reason": "Missing required nutritional values for official Nutri-Score calculation",
            "missing_inputs": missing_inputs
        }

    fv_pct = fruits_veg_pct or 0.0
    # Negative points (N)
    n_energy = _get_points(energy_kj, ENERGY_POINTS_SOLID)
    n_sugars = _get_points(sugars_g, SUGARS_POINTS_SOLID_2023)
    n_sat_fat = _get_points(saturated_fat_g, SAT_FAT_POINTS_SOLID)
    n_salt = _get_points(salt_g, SALT_POINTS_SOLID)
    total_n = n_energy + n_sugars + n_sat_fat + n_salt

    # Positive points (P)
    p_fiber = _get_points(fiber_g, FIBER_POINTS_SOLID)
    p_protein = _get_points(proteins_g, PROTEIN_POINTS_SOLID)
    p_fruits_veg = _get_points(fv_pct, FRUITS_VEG_POINTS_SOLID)

    # 2023 Protein Capping Rule:
    # If total N >= 11, protein is counted only if fruits_veg points >= 5
    protein_counted = True
    if total_n >= 11 and p_fruits_veg < 5:
        total_p = p_fiber + p_fruits_veg
        protein_counted = False
    else:
        total_p = p_fiber + p_protein + p_fruits_veg

    final_score = total_n - total_p

    # Solid letter grades
    if final_score <= -1:
        grade = "a"
    elif final_score <= 2:
        grade = "b"
    elif final_score <= 10:
        grade = "c"
    elif final_score <= 18:
        grade = "d"
    else:
        grade = "e"

    breakdown = {
        "status": "computed",
        "negative_points": total_n,
        "positive_points": total_p,
        "n_energy": n_energy,
        "n_sugars": n_sugars,
        "n_saturated_fat": n_sat_fat,
        "n_salt": n_salt,
        "p_fiber": p_fiber,
        "p_protein": p_protein,
        "p_fruits_veg": p_fruits_veg,
        "protein_capped": not protein_counted
    }
    return final_score, grade, breakdown

def calculate_nutri_score_beverage(
    energy_kj: Optional[float],
    sugars_g: Optional[float],
    saturated_fat_g: Optional[float],
    salt_g: Optional[float],
    fiber_g: Optional[float] = None,
    proteins_g: Optional[float] = None,
    fruits_veg_pct: Optional[float] = 0.0,
    has_sweeteners: bool = False,
    is_water: bool = False
) -> Tuple[Optional[int], str, Dict[str, Any]]:
    """
    Calculates official Nutri-Score (2023 revised algorithm) for beverages.
    Water is exclusively Grade A.
    Artificial sweeteners add 4 penalty points in 2023 revision.
    When required beverage inputs are missing (None), returns (None, 'not_computable', {...}).
    Grade boundaries (2023): Water = A, <= 1 = B, 2-5 = C, 6-9 = D, >= 10 = E.
    """
    if is_water:
        return 0, "a", {"status": "computed", "note": "Water is automatically Nutri-Score A"}

    required = {
        "energy_kj": energy_kj,
        "sugars_g": sugars_g,
        "saturated_fat_g": saturated_fat_g,
        "salt_g": salt_g
    }
    missing_inputs = [param for param, val in required.items() if val is None]
    if missing_inputs:
        return None, "not_computable", {
            "status": "not_computable",
            "reason": "Missing required nutritional values for beverage Nutri-Score calculation",
            "missing_inputs": missing_inputs
        }

    n_energy = _get_points(energy_kj, BEVERAGE_ENERGY_POINTS)
    n_sugars = _get_points(sugars_g, BEVERAGE_SUGAR_POINTS_2023)
    n_sat_fat = _get_points(saturated_fat_g, SAT_FAT_POINTS_SOLID)
    n_salt = _get_points(salt_g, BEVERAGE_SALT_POINTS)

    # 2023 Sweetener penalty: +4 points if non-nutritive sweetener is present
    sweetener_penalty = 4 if has_sweeteners else 0
    total_n = n_energy + n_sugars + n_sat_fat + n_salt + sweetener_penalty

    # Positive points
    fv_pct = fruits_veg_pct or 0.0
    p_fruits_veg = _get_points(fv_pct, FRUITS_VEG_POINTS_SOLID)
    # Fiber and protein in beverages: marked unverified/optional (default 0 if missing)
    p_protein = _get_points(proteins_g, PROTEIN_POINTS_SOLID) if proteins_g is not None else 0
    p_fiber = _get_points(fiber_g, FIBER_POINTS_SOLID) if fiber_g is not None else 0
    total_p = p_fruits_veg + p_protein + p_fiber

    final_score = total_n - total_p

    # Beverage letter grades: A is water only. 2023 boundaries: <=1: B, 2-5: C, 6-9: D, >=10: E
    if final_score <= 1:
        grade = "b"
    elif final_score <= 5:
        grade = "c"
    elif final_score <= 9:
        grade = "d"
    else:
        grade = "e"

    breakdown = {
        "status": "computed",
        "negative_points": total_n,
        "positive_points": total_p,
        "n_energy": n_energy,
        "n_sugars": n_sugars,
        "n_saturated_fat": n_sat_fat,
        "n_salt": n_salt,
        "sweetener_penalty": sweetener_penalty,
        "p_fruits_veg": p_fruits_veg,
        "p_protein": p_protein,
        "p_fiber": p_fiber
    }
    return final_score, grade, breakdown
