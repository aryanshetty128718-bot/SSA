from typing import Dict, Any, List, Optional, Tuple

def generate_parameter_explanations(
    sub_scores: Dict[str, Optional[float]],
    nutriments: Dict[str, Optional[float]],
    weights: Dict[str, float],
    criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generates granular per-parameter explanation objects with evidence, threshold bands,
    sub-scores, weights, and human-readable text.
    """
    params_def = criteria.get("parameters", {})
    explanations = []

    for param_name, defn in params_def.items():
        score = sub_scores.get(param_name)
        weight = weights.get(param_name, 0.0)
        unit = defn.get("unit", "")
        polarity = defn.get("polarity", "negative")
        source = defn.get("source", "Project Criteria")

        # Map param_name to nutriments key
        nutr_key_map = {
            "sugars": "sugars_g",
            "sodium": "sodium_mg",
            "saturated_fat": "saturated_fat_g",
            "energy": "energy_kcal",
            "fiber": "fiber_g",
            "proteins": "proteins_g"
        }
        raw_val = nutriments.get(nutr_key_map.get(param_name, "")) if nutr_key_map.get(param_name) else None

        if score is None:
            explanations.append({
                "parameter": param_name,
                "display_name": defn.get("name", param_name.title()),
                "raw_value": None,
                "unit": unit,
                "band": "Missing",
                "sub_score": None,
                "effective_weight": 0.0,
                "source": source,
                "text": f"{defn.get('name', param_name.title())} data is not declared on label; parameter excluded and weights renormalized."
            })
            continue

        # Determine band
        if score >= 70.0:
            band = "Green (Favorable)"
        elif score >= 40.0:
            band = "Amber (Moderate)"
        else:
            band = "Red (Caution)"

        # Text explanation
        if polarity == "negative":
            t_low = defn.get("t_low", 0)
            t_high = defn.get("t_high", 0)
            if raw_val is not None:
                if raw_val <= t_low:
                    text = f"Low level ({raw_val} {unit} <= {t_low} {unit} threshold). Positive nutritional contribution."
                elif raw_val <= t_high:
                    text = f"Moderate level ({raw_val} {unit} between {t_low} and {t_high} {unit}). Within intermediate dietary allowance."
                else:
                    text = f"High level ({raw_val} {unit} exceeds {t_high} {unit} threshold). Parameter reduces overall score."
            else:
                text = f"Evaluated sub-score of {score}/100 based on additive / formulation profile."
        else:
            t_target = defn.get("t_target", 0)
            if raw_val is not None:
                text = f"Declared content of {raw_val} {unit} (target benchmark: {t_target} {unit}). Adds positive points."
            else:
                text = f"Quality score of {score}/100 awarded based on whole food composition and processing level."

        explanations.append({
            "parameter": param_name,
            "display_name": defn.get("name", param_name.title()),
            "raw_value": raw_val,
            "unit": unit,
            "band": band,
            "sub_score": score,
            "effective_weight": weight,
            "source": source,
            "text": text
        })

    return explanations

def generate_pros_and_cons(
    sub_scores: Dict[str, Optional[float]],
    nutriments: Dict[str, Optional[float]],
    additive_reasons: List[str],
    product_type: str = "solid",
    criteria: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates evidence-backed pros and cons using exact configured thresholds for the product type.
    Crucial: Any parameter landing in the Red band generates a Con; Green band generates a Pro.
    """
    pros = []
    cons = []

    params_def = criteria.get("parameters", {}) if criteria else {}

    # 1. Sugars
    sug = nutriments.get("sugars_g")
    sug_score = sub_scores.get("sugars")
    sug_def = params_def.get("sugars", {})
    t_low_sug = sug_def.get("t_low", 1.0 if product_type == "beverage" else 5.0)
    t_high_sug = sug_def.get("t_high", 5.0 if product_type == "beverage" else 22.5)
    unit_sug = "ml" if product_type == "beverage" else "g"

    if sug is not None and sug_score is not None:
        if sug_score >= 70.0 or sug <= t_low_sug:
            pros.append({
                "parameter": "sugars",
                "title": "Low Sugar Content",
                "evidence": f"{sug}g per 100{unit_sug} (low sugar threshold <= {t_low_sug}g)"
            })
        elif sug_score < 40.0 or sug > t_high_sug:
            cons.append({
                "parameter": "sugars",
                "title": "High Sugar Content",
                "evidence": f"{sug}g per 100{unit_sug} (exceeds high threshold of {t_high_sug}g)"
            })

    # 2. Saturated fat
    sf = nutriments.get("saturated_fat_g")
    sf_score = sub_scores.get("saturated_fat")
    sf_def = params_def.get("saturated_fat", {})
    t_low_sf = sf_def.get("t_low", 0.75 if product_type == "beverage" else 1.5)
    t_high_sf = sf_def.get("t_high", 2.5 if product_type == "beverage" else 5.0)

    if sf is not None and sf_score is not None:
        if sf <= t_low_sf:
            pros.append({
                "parameter": "saturated_fat",
                "title": "Low Saturated Fat",
                "evidence": f"{sf}g per 100{unit_sug} (within low fat threshold <= {t_low_sf}g)"
            })
        elif sf_score < 40.0 or sf > t_high_sf:
            cons.append({
                "parameter": "saturated_fat",
                "title": "High Saturated Fat",
                "evidence": f"{sf}g per 100{unit_sug} (exceeds threshold of {t_high_sf}g)"
            })

    # 3. Sodium
    sod = nutriments.get("sodium_mg")
    sod_score = sub_scores.get("sodium")
    sod_def = params_def.get("sodium", {})
    t_low_sod = sod_def.get("t_low", 120.0)
    t_high_sod = sod_def.get("t_high", 300.0 if product_type == "beverage" else 600.0)

    if sod is not None and sod_score is not None:
        if sod <= t_low_sod:
            pros.append({
                "parameter": "sodium",
                "title": "Low Sodium",
                "evidence": f"{sod}mg per 100{unit_sug} (low sodium threshold <= {t_low_sod}mg)"
            })
        elif sod_score < 40.0 or sod > t_high_sod:
            cons.append({
                "parameter": "sodium",
                "title": "Elevated Sodium",
                "evidence": f"{sod}mg per 100{unit_sug} (exceeds {t_high_sod}mg traffic light cut-off)"
            })

    # 4. Dietary fiber
    fib = nutriments.get("fiber_g")
    fib_score = sub_scores.get("fiber")
    if fib is not None and (fib >= 3.0 or (fib_score and fib_score >= 70.0)):
        pros.append({
            "parameter": "fiber",
            "title": "Source of Dietary Fiber",
            "evidence": f"{fib}g per 100{unit_sug} provides notable dietary fiber contribution"
        })

    # 5. Proteins
    prot = nutriments.get("proteins_g")
    prot_score = sub_scores.get("proteins")
    if prot is not None and (prot >= 8.0 or (prot_score and prot_score >= 70.0)):
        pros.append({
            "parameter": "proteins",
            "title": "Good Protein Content",
            "evidence": f"{prot}g per 100{unit_sug} meets dietary protein enrichment target"
        })

    # 6. Additives (Informational neutral notes)
    for reason in additive_reasons:
        cons.append({
            "parameter": "additives",
            "title": "Additive Flag",
            "evidence": reason
        })

    return pros, cons
