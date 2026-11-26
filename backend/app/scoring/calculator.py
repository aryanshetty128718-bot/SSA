import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from app.scoring.sub_scores import (
    calculate_negative_subscore,
    calculate_positive_subscore,
    calculate_ingredient_quality_subscore,
    calculate_additive_subscore
)
from app.scoring.renormalizer import renormalize_weights
from app.scoring.nutri_score_2023 import (
    calculate_nutri_score_solid,
    calculate_nutri_score_beverage
)
from app.scoring.explanations import (
    generate_parameter_explanations,
    generate_pros_and_cons
)

_DEFAULTS_PATH = Path(__file__).parent / "criteria_defaults.json"
with open(_DEFAULTS_PATH, "r", encoding="utf-8") as f:
    CRITERIA_DEFAULTS = json.load(f)

def compute_product_analysis(
    product_type: str,
    nutriments: Dict[str, Optional[float]],
    ingredients: List[Dict[str, Any]],
    nova_group: Optional[int] = None,
    criteria_override: Optional[Dict[str, Any]] = None,
    is_water: bool = False
) -> Dict[str, Any]:
    """
    Pure Python scoring orchestrator.
    No database queries, no ML models.
    Computes:
    - 0-100 continuous project score with dynamic weight renormalization
    - Official Nutri-Score 2023 points and letter grade
    - Granular per-parameter explanations and evidence-backed pros/cons
    """
    clean_type = "beverage" if product_type == "beverage" else "solid"
    criteria = criteria_override or CRITERIA_DEFAULTS.get(clean_type, {})
    params_def = criteria.get("parameters", {})

    # Extract nutrient values (safely treating missing as None)
    sugars_g = nutriments.get("sugars_g")
    sodium_mg = nutriments.get("sodium_mg")
    salt_g = nutriments.get("salt_g")
    saturated_fat_g = nutriments.get("saturated_fat_g")
    energy_kcal = nutriments.get("energy_kcal")
    energy_kj = nutriments.get("energy_kj")
    fiber_g = nutriments.get("fiber_g")
    proteins_g = nutriments.get("proteins_g")
    fruits_veg_pct = nutriments.get("fruits_vegetables_nuts_colza_walnut_olive_oils_pct")

    # If energy_kj is missing but energy_kcal is present: 1 kcal = 4.184 kJ
    if energy_kj is None and energy_kcal is not None:
        energy_kj = energy_kcal * 4.184

    # If salt_g is missing but sodium_mg is present: salt = sodium_mg * 2.5 / 1000
    if salt_g is None and sodium_mg is not None:
        salt_g = (sodium_mg * 2.5) / 1000.0
    elif sodium_mg is None and salt_g is not None:
        sodium_mg = (salt_g * 1000.0) / 2.5

    # 1. Compute Sub-Scores (0-100)
    sub_scores = {}
    baseline_weights = {}

    for param_name, defn in params_def.items():
        baseline_weights[param_name] = defn.get("weight", 0.1)

        if param_name == "sugars":
            sub_scores[param_name] = calculate_negative_subscore(sugars_g, defn.get("t_low", 5.0), defn.get("t_high", 22.5))
        elif param_name == "sodium":
            sub_scores[param_name] = calculate_negative_subscore(sodium_mg, defn.get("t_low", 120.0), defn.get("t_high", 600.0))
        elif param_name == "saturated_fat":
            sub_scores[param_name] = calculate_negative_subscore(saturated_fat_g, defn.get("t_low", 1.5), defn.get("t_high", 5.0))
        elif param_name == "energy":
            sub_scores[param_name] = calculate_negative_subscore(energy_kcal, defn.get("t_low", 150.0), defn.get("t_high", 450.0))
        elif param_name == "fiber":
            sub_scores[param_name] = calculate_positive_subscore(fiber_g, defn.get("t_target", 6.0))
        elif param_name == "proteins":
            sub_scores[param_name] = calculate_positive_subscore(proteins_g, defn.get("t_target", 12.0))
        elif param_name == "ingredient_quality":
            sub_scores[param_name] = calculate_ingredient_quality_subscore(ingredients, nova_group, fruits_veg_pct)
        elif param_name == "additives":
            additive_score, additive_reasons = calculate_additive_subscore(ingredients)
            sub_scores[param_name] = additive_score

    # Additive reasons for pros/cons
    _, additive_reasons = calculate_additive_subscore(ingredients)

    # 2. Renormalize Weights & Compute Overall Continuous Project Score
    overall_score, renormalized_weights, confidence_score, confidence_level, missing_params = renormalize_weights(
        sub_scores=sub_scores,
        baseline_weights=baseline_weights,
        min_weight_threshold=0.40
    )

    # 2.1 Scientific High-Sugar Cap Rule (Version 1.1.0)
    # Rationale: Under UK FSA, WHO, and Nutri-Score standards, a product with severe excess sugar
    # (red traffic light zone: >=22.5g/100g for solid, >=5.0g/100ml for beverage) cannot be
    # promoted into "Moderate" or "Healthy Choice" merely due to absence of fat or additives.
    # Exemption: Products whose sugar is naturally derived from dried fruits (dates, raisins, figs, prunes, etc.)
    # or pure honey without added refined/free sugars (cane sugar, glucose, corn syrup, etc.) are exempt.
    sugar_caps = criteria.get("sugar_caps", {})
    t_severe = sugar_caps.get("severe_threshold", 5.0 if clean_type == "beverage" else 30.0)
    max_severe = sugar_caps.get("severe_max_score", 39.0)
    t_high = sugar_caps.get("high_threshold", 5.0 if clean_type == "beverage" else 22.5)
    max_high = sugar_caps.get("high_max_score", 39.0 if clean_type == "beverage" else 48.0)

    # Check natural sugar exemption
    natural_fruit_keywords = ["date", "dates", "raisin", "raisins", "fig", "figs", "prune", "prunes", "apricot", "apricots", "currant", "currants", "sultana", "sultanas", "honey"]
    added_sugar_keywords = ["sugar", "sucre", "cane sugar", "glucose", "fructose", "corn syrup", "dextrose", "maltodextrin", "invert sugar", "syrup", "molasses"]
    
    is_natural_fruit_sugar_exempt = False
    if ingredients:
        ing_texts = [str(ing.get("name") or ing.get("text", "")).lower() for ing in ingredients]
        all_ing_str = " ".join(ing_texts)
        has_natural_fruits = any(kw in all_ing_str for kw in natural_fruit_keywords)
        has_added_refined_sugars = any(kw in all_ing_str for kw in added_sugar_keywords)
        if has_natural_fruits and not has_added_refined_sugars:
            is_natural_fruit_sugar_exempt = True

    sugar_cap_applied = False
    if overall_score is not None and sugars_g is not None and not is_natural_fruit_sugar_exempt:
        if sugars_g >= t_severe and overall_score > max_severe:
            overall_score = max_severe
            sugar_cap_applied = True
        elif sugars_g >= t_high and overall_score > max_high:
            overall_score = max_high
            sugar_cap_applied = True

    # 2.2 Saturated Fat Cap Rule (Version 1.2.0)
    # Severe saturated fat (>=10.0g for solid, >=5.0g for beverage) caps score at <= 48.0 (Moderate band)
    if overall_score is not None and saturated_fat_g is not None:
        t_sat_fat_severe = 5.0 if clean_type == "beverage" else 10.0
        if saturated_fat_g >= t_sat_fat_severe and overall_score > 48.0:
            overall_score = 48.0

    # Score classification band
    if overall_score is not None:
        if overall_score >= 70.0:
            score_band = "Healthy Choice"
            badge_color = "green"
        elif overall_score >= 40.0:
            score_band = "Moderate"
            badge_color = "amber"
        else:
            score_band = "Less Healthy"
            badge_color = "red"
    else:
        score_band = "Insufficient Data"
        badge_color = "gray"

    # 3. Official Nutri-Score 2023 Reference Calculation
    has_sweeteners = any("sweetener" in r.lower() for r in additive_reasons)
    if clean_type == "beverage":
        ns_pts, ns_grade, ns_breakdown = calculate_nutri_score_beverage(
            energy_kj=energy_kj,
            sugars_g=sugars_g,
            saturated_fat_g=saturated_fat_g,
            salt_g=salt_g,
            fiber_g=fiber_g,
            proteins_g=proteins_g,
            fruits_veg_pct=fruits_veg_pct,
            has_sweeteners=has_sweeteners,
            is_water=is_water
        )
    else:
        ns_pts, ns_grade, ns_breakdown = calculate_nutri_score_solid(
            energy_kj=energy_kj,
            sugars_g=sugars_g,
            saturated_fat_g=saturated_fat_g,
            salt_g=salt_g,
            fiber_g=fiber_g,
            proteins_g=proteins_g,
            fruits_veg_pct=fruits_veg_pct
        )

    # 4. Granular Explanations & Pros/Cons
    param_explanations = generate_parameter_explanations(
        sub_scores=sub_scores,
        nutriments=nutriments,
        weights=renormalized_weights,
        criteria=criteria
    )
    pros, cons = generate_pros_and_cons(
        sub_scores=sub_scores,
        nutriments=nutriments,
        additive_reasons=additive_reasons,
        product_type=clean_type,
        criteria=criteria
    )

    return {
        "scoring_framework": {
            "name": "Proposed Project Nutritional Scoring Framework",
            "type": clean_type,
            "version": "1.1.0",
            "disclaimer": "Academic MCA project proposed framework, not an official statutory standard."
        },
        "overall_score": overall_score,
        "score_band": score_band,
        "badge_color": badge_color,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "missing_parameters": missing_params,
        "sub_scores": sub_scores,
        "effective_weights": renormalized_weights,
        "parameter_explanations": param_explanations,
        "pros": pros,
        "cons": cons,
        "official_reference": {
            "standard_name": "Nutri-Score 2023 (Santé publique France)",
            "points": ns_pts,
            "grade": ns_grade.upper(),
            "breakdown": ns_breakdown,
            "label": "Official Validated Reference Standard"
        }
    }
