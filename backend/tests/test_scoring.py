import pytest
from app.scoring.calculator import compute_product_analysis
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

def test_negative_subscore_boundaries():
    # Solid sugar: t_low=5.0, t_high=22.5
    # 0g -> 100
    assert calculate_negative_subscore(0.0, 5.0, 22.5) == 100.0
    # t_low (5.0g) -> exactly 70.0
    assert calculate_negative_subscore(5.0, 5.0, 22.5) == 70.0
    # midpoint between t_low and t_high (13.75g) -> 55.0
    assert calculate_negative_subscore(13.75, 5.0, 22.5) == 55.0
    # t_high (22.5g) -> exactly 40.0
    assert calculate_negative_subscore(22.5, 5.0, 22.5) == 40.0
    # extreme sugar (60g) -> decaying towards 0 (< 10)
    score_extreme = calculate_negative_subscore(60.0, 5.0, 22.5)
    assert 0.0 <= score_extreme < 10.0

def test_none_vs_zero_distinction():
    # Crucial rule: None is missing data, 0 is an actual zero value!
    assert calculate_negative_subscore(None, 5.0, 22.5) is None
    assert calculate_negative_subscore(0.0, 5.0, 22.5) == 100.0

    assert calculate_positive_subscore(None, 6.0) is None
    assert calculate_positive_subscore(0.0, 6.0) == 0.0

def test_positive_subscore_boundaries():
    # Fiber: t_target=6.0
    assert calculate_positive_subscore(0.0, 6.0) == 0.0
    assert calculate_positive_subscore(6.0, 6.0) == 100.0
    # Values above target are capped at 100.0
    assert calculate_positive_subscore(12.0, 6.0) == 100.0

def test_renormalization_sums_to_one():
    # Case with some missing parameters
    sub_scores = {
        "sugars": 65.0,
        "sodium": 80.0,
        "saturated_fat": None,  # Missing
        "energy": 70.0,
        "fiber": None,          # Missing
        "proteins": 85.0,
        "ingredient_quality": 75.0,
        "additives": 90.0
    }
    baseline_weights = {
        "sugars": 0.22,
        "sodium": 0.18,
        "saturated_fat": 0.18,
        "energy": 0.12,
        "fiber": 0.10,
        "proteins": 0.10,
        "ingredient_quality": 0.05,
        "additives": 0.05
    }
    score, re_weights, conf_score, conf_level, missing = renormalize_weights(sub_scores, baseline_weights)
    
    assert score is not None
    assert "saturated_fat" in missing
    assert "fiber" in missing
    assert len(re_weights) == 6
    # Total sum of renormalized weights must be exactly 1.0 (within float precision)
    assert round(sum(re_weights.values()), 4) == 1.0000
    assert conf_score == 0.72  # 1.0 - 0.18 - 0.10
    assert conf_level == "Medium"

def test_all_missing_input_rejection():
    # When all or almost all parameters are None
    sub_scores = {k: None for k in ["sugars", "sodium", "saturated_fat", "energy", "fiber", "proteins"]}
    baseline_weights = {"sugars": 0.22, "sodium": 0.18, "saturated_fat": 0.18, "energy": 0.12, "fiber": 0.10, "proteins": 0.10}
    score, re_weights, conf_score, conf_level, missing = renormalize_weights(sub_scores, baseline_weights)
    
    assert score is None
    assert re_weights == {}
    assert conf_score == 0.0
    assert conf_level == "Low"

def test_beverage_vs_solid_thresholds():
    # 8g of sugar:
    # In Solid food (t_low=5.0, t_high=22.5), 8g is moderate (Amber, score ~ 64.8)
    solid_res = compute_product_analysis(
        product_type="solid",
        nutriments={"sugars_g": 8.0, "sodium_mg": 50.0, "saturated_fat_g": 1.0, "energy_kcal": 120.0, "proteins_g": 3.0, "fiber_g": 2.0},
        ingredients=[]
    )
    # In Beverage (t_low=2.5, t_high=11.25), 8g is high liquid sugar (Amber-Red boundary, lower score)
    bev_res = compute_product_analysis(
        product_type="beverage",
        nutriments={"sugars_g": 8.0, "sodium_mg": 50.0, "saturated_fat_g": 1.0, "energy_kcal": 120.0, "proteins_g": 3.0, "fiber_g": 2.0},
        ingredients=[]
    )
    assert solid_res["sub_scores"]["sugars"] > bev_res["sub_scores"]["sugars"]

def test_high_sugar_high_fiber_product():
    # A product like a whole-grain granola bar or dried fruit bar:
    # High in sugar (30g) but high in dietary fiber (8g) and protein (10g)
    res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 30.0,
            "fiber_g": 8.0,
            "proteins_g": 10.0,
            "saturated_fat_g": 2.0,
            "sodium_mg": 100.0,
            "energy_kcal": 380.0
        },
        ingredients=[
            {"name": "Whole Rolled Oats", "position_order": 1, "is_whole_grain": True},
            {"name": "Honey", "position_order": 2},
            {"name": "Almonds", "position_order": 3}
        ]
    )
    assert res["sub_scores"]["sugars"] < 40.0  # Sugar is penalized
    assert res["sub_scores"]["fiber"] == 100.0  # Fiber is rewarded
    assert res["sub_scores"]["proteins"] > 80.0 # Protein is rewarded
    # Both pro and con must be generated with evidence
    pro_params = [p["parameter"] for p in res["pros"]]
    con_params = [c["parameter"] for c in res["cons"]]
    assert "fiber" in pro_params
    assert "sugars" in con_params

def test_nutri_score_solid_protein_capping():
    # Solid product with very high negative points (total N >= 11) and low fruit/veg
    # Energy: 2200 kJ (6 pts), Sugars: 35g (10 pts) -> N >= 16
    # Proteins: 15g (6 pts) should be CAPPED (excluded)
    pts, grade, breakdown = calculate_nutri_score_solid(
        energy_kj=2200.0,
        sugars_g=35.0,
        saturated_fat_g=8.0,
        salt_g=1.5,
        fiber_g=2.0,
        proteins_g=15.0,
        fruits_veg_pct=0.0
    )
    assert breakdown["protein_capped"] is True
    assert breakdown["p_protein"] == 6
    assert breakdown["positive_points"] == breakdown["p_fiber"]  # Protein omitted from total_p

def test_nutri_score_beverage_sweetener_penalty():
    # Diet soda: 0 energy, 0 sugar, but has non-nutritive sweetener
    pts_clean, grade_clean, _ = calculate_nutri_score_beverage(
        energy_kj=5.0, sugars_g=0.0, saturated_fat_g=0.0, salt_g=0.02, fiber_g=0.0, proteins_g=0.0, has_sweeteners=False
    )
    pts_sweetened, grade_sweetened, _ = calculate_nutri_score_beverage(
        energy_kj=5.0, sugars_g=0.0, saturated_fat_g=0.0, salt_g=0.02, fiber_g=0.0, proteins_g=0.0, has_sweeteners=True
    )
    # Sweetened soda receives +4 penalty points in 2023 algorithm
    assert pts_sweetened == pts_clean + 4
    assert grade_clean == "b"
    assert grade_sweetened == "c"

def test_absent_fiber_regression():
    # Verifies that when fiber is missing (None), sub_score is None and completeness reflects it
    res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 10.0,
            "fiber_g": None,  # absent
            "proteins_g": 5.0,
            "saturated_fat_g": 2.0,
            "sodium_mg": 200.0,
            "energy_kcal": 250.0
        },
        ingredients=[]
    )
    assert res["sub_scores"]["fiber"] is None
    assert "fiber" in res["missing_parameters"]
    assert res["confidence_score"] == 0.90  # 1.0 - 0.10 fiber weight

def test_all_eight_parameters_scored_when_data_present():
    """Requirement 1: Ensures all 8 parameters are scored and weighted when data is provided."""
    res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 12.0,
            "sodium_mg": 150.0,
            "saturated_fat_g": 2.0,
            "energy_kcal": 300.0,
            "fiber_g": 4.0,
            "proteins_g": 8.0
        },
        ingredients=[
            {"canonical_name": "Wheat", "position_order": 1, "is_whole_grain": True},
            {"canonical_name": "Citric Acid", "ins_number": "INS 330", "is_additive": True}
        ]
    )
    expected_8 = {"sugars", "sodium", "saturated_fat", "energy", "fiber", "proteins", "ingredient_quality", "additives"}
    assert set(res["sub_scores"].keys()) == expected_8
    for param in expected_8:
        assert res["sub_scores"][param] is not None, f"Parameter {param} must not be None when data is present"
        assert param in res["effective_weights"], f"Parameter {param} must be weighted"
        assert res["effective_weights"][param] > 0.0, f"Parameter {param} must have positive weight"
    assert round(sum(res["effective_weights"].values()), 4) == 1.0000
    assert res["confidence_score"] == 1.000
    assert res["confidence_level"] == "High"
    assert len(res["missing_parameters"]) == 0

def test_cola_has_high_sugar_con():
    """Requirement 1: Verifies that cola has a high-sugar con."""
    res = compute_product_analysis(
        product_type="beverage",
        nutriments={
            "sugars_g": 10.9,
            "energy_kcal": 44.0,
            "saturated_fat_g": 0.0,
            "sodium_mg": 12.0
        },
        ingredients=[]
    )
    con_params = [c["parameter"] for c in res["cons"]]
    assert "sugars" in con_params
    sugar_con = next(c for c in res["cons"] if c["parameter"] == "sugars")
    assert "High Sugar Content" in sugar_con["title"]
    assert "10.9g per 100ml" in sugar_con["evidence"]
    """Requirement 1: Ensures all 8 parameters are scored and weighted when data is provided."""
    res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 12.0,
            "sodium_mg": 150.0,
            "saturated_fat_g": 2.0,
            "energy_kcal": 300.0,
            "fiber_g": 4.0,
            "proteins_g": 8.0
        },
        ingredients=[
            {"canonical_name": "Wheat", "position_order": 1, "is_whole_grain": True},
            {"canonical_name": "Citric Acid", "ins_number": "INS 330", "is_additive": True}
        ]
    )
    expected_8 = {"sugars", "sodium", "saturated_fat", "energy", "fiber", "proteins", "ingredient_quality", "additives"}
    assert set(res["sub_scores"].keys()) == expected_8
    for param in expected_8:
        assert res["sub_scores"][param] is not None, f"Parameter {param} must not be None when data is present"
        assert param in res["effective_weights"], f"Parameter {param} must be weighted"
        assert res["effective_weights"][param] > 0.0, f"Parameter {param} must have positive weight"
    assert round(sum(res["effective_weights"].values()), 4) == 1.0000
    assert res["confidence_score"] == 1.000
    assert res["confidence_level"] == "High"
    assert len(res["missing_parameters"]) == 0

def test_nutri_score_missing_inputs_returns_not_computable():
    """Requirement 3: Verifies that missing required inputs return not_computable instead of zero-fallbacks."""
    # Missing fiber and saturated fat in solid
    pts, grade, breakdown = calculate_nutri_score_solid(
        energy_kj=1500.0,
        sugars_g=15.0,
        saturated_fat_g=None,  # Missing!
        salt_g=0.5,
        fiber_g=None,          # Missing!
        proteins_g=5.0
    )
    assert pts is None
    assert grade == "not_computable"
    assert breakdown["status"] == "not_computable"
    assert "saturated_fat_g" in breakdown["missing_inputs"]
    assert "fiber_g" in breakdown["missing_inputs"]

    # Missing sugars in beverage
    pts_bev, grade_bev, breakdown_bev = calculate_nutri_score_beverage(
        energy_kj=120.0,
        sugars_g=None,         # Missing!
        saturated_fat_g=0.0,
        salt_g=0.05,
        fiber_g=0.0,
        proteins_g=0.0
    )
    assert pts_bev is None
    assert grade_bev == "not_computable"
    assert "sugars_g" in breakdown_bev["missing_inputs"]

def test_sugar_cap_and_natural_fruit_exemption():
    """
    Tests that:
    1. A sugary cereal (e.g. 32g sugar) is capped at <= 39.0.
    2. A product with 26g sugar with added sugars is capped at <= 48.0.
    3. Pure dried fruit (e.g. 100% Medjool Dates or Organic Raisins with 65g sugar) is EXEMPT from the sugar cap.
    """
    # 1. Sugary Cereal: 32g sugar, contains cane sugar
    cereal_res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 32.0,
            "fiber_g": 3.0,
            "proteins_g": 6.0,
            "saturated_fat_g": 1.0,
            "sodium_mg": 150.0,
            "energy_kcal": 390.0
        },
        ingredients=[{"name": "Whole grain wheat"}, {"name": "Cane sugar"}, {"name": "Salt"}]
    )
    assert cereal_res["overall_score"] <= 39.0
    assert cereal_res["score_band"] == "Less Healthy"

    # 2. Cereal with 26.67g sugar (red traffic light zone >=22.5g)
    cereal_mid_res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 26.67,
            "fiber_g": 7.0,
            "proteins_g": 8.0,
            "saturated_fat_g": 0.8,
            "sodium_mg": 100.0,
            "energy_kcal": 360.0
        },
        ingredients=[{"name": "Whole grain corn"}, {"name": "Sugar"}, {"name": "Malt extract"}]
    )
    assert cereal_mid_res["overall_score"] <= 48.0

    # 3. Dried Dates / Raisins: 65g sugar, NO added sugars
    dates_res = compute_product_analysis(
        product_type="solid",
        nutriments={
            "sugars_g": 65.0,
            "fiber_g": 8.0,
            "proteins_g": 2.5,
            "saturated_fat_g": 0.2,
            "sodium_mg": 10.0,
            "energy_kcal": 280.0
        },
        ingredients=[{"name": "Pitted Medjool Dates"}]
    )
    # Because dates are exempt from the sugar cap, overall score is NOT forcefully clamped to 39.0
    assert dates_res["overall_score"] > 45.0
