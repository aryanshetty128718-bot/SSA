import math
from typing import Optional, Dict, Any, List, Tuple

def calculate_negative_subscore(value: Optional[float], t_low: float, t_high: float) -> Optional[float]:
    """
    Computes a 0-100 continuous score for negative nutrients (sugars, sodium, saturated fat, energy).
    Lower value is better:
    - 0 <= val <= t_low: Score is 70 to 100 (Green band)
    - t_low < val <= t_high: Score is 40 to 70 (Amber band)
    - val > t_high: Score is 0 to 40 (Red band, exponential decay)
    Returns None if value is None.
    """
    if value is None:
        return None
    val = max(0.0, float(value))
    if t_low <= 0:
        t_low = 1.0
    if t_high <= t_low:
        t_high = t_low * 2.0

    if val <= t_low:
        # Interpolates 100 -> 70
        score = 100.0 - 30.0 * (val / t_low)
    elif val <= t_high:
        # Interpolates 70 -> 40
        score = 70.0 - 30.0 * ((val - t_low) / (t_high - t_low))
    else:
        # Exponential decline from 40 down towards 0
        excess = (val - t_high) / t_high
        score = 40.0 * math.exp(-min(excess, 5.0))

    return round(max(0.0, min(100.0, score)), 2)

def calculate_positive_subscore(value: Optional[float], t_target: float) -> Optional[float]:
    """
    Computes a 0-100 continuous score for beneficial nutrients (fiber, protein).
    Higher value is better:
    - val = 0 -> Score 0
    - val = t_target -> Score 100
    - val > t_target -> Score 100 (capped)
    Returns None if value is None.
    """
    if value is None:
        return None
    val = max(0.0, float(value))
    if t_target <= 0:
        t_target = 5.0

    ratio = min(val / t_target, 1.0)
    # Concave scaling: (ratio)^0.85 rewards initial healthy contributions quickly
    score = 100.0 * (ratio ** 0.85)
    return round(max(0.0, min(100.0, score)), 2)

def calculate_ingredient_quality_subscore(
    ingredients: List[Dict[str, Any]],
    nova_group: Optional[int] = None,
    fruits_veg_pct: Optional[float] = None
) -> float:
    """
    Computes 0-100 score for ingredient quality based on:
    1. NOVA group baseline (NOVA 1=100, 2=85, 3=65, 4=40)
    2. Sugar hierarchy check (-30 if sugar at #1, -15 if sugar in top 3)
    3. Whole food / whole grain presence (+15 to +20)
    4. Fruit & vegetable percentage (+10 to +20)
    """
    # 1. Baseline from NOVA if available, else standard starting baseline 75
    if nova_group == 1:
        base = 100.0
    elif nova_group == 2:
        base = 85.0
    elif nova_group == 3:
        base = 65.0
    elif nova_group == 4:
        base = 40.0
    else:
        base = 75.0

    sugar_synonyms = {"sugar", "sucrose", "glucose", "fructose", "corn syrup", "high fructose corn syrup", "invert sugar", "dextrose", "molasses"}
    has_sugar_first = False
    has_sugar_top3 = False
    has_whole_grain = False

    for ing in ingredients:
        pos = ing.get("position_order", 999)
        name_lower = ing.get("canonical_name", ing.get("name", "")).lower()
        is_wg = ing.get("is_whole_grain", False)
        if is_wg or any(w in name_lower for w in ["whole wheat", "whole grain", "oats", "rolled oats", "brown rice"]):
            has_whole_grain = True

        if any(s in name_lower for s in sugar_synonyms):
            if pos == 1:
                has_sugar_first = True
            elif pos <= 3:
                has_sugar_top3 = True

    # Adjustments
    score = base
    if has_sugar_first:
        score -= 25.0
    elif has_sugar_top3:
        score -= 12.0

    if has_whole_grain:
        score += 15.0

    if fruits_veg_pct is not None and fruits_veg_pct > 40:
        score += min(15.0, (fruits_veg_pct - 40) * 0.3)

    return round(max(0.0, min(100.0, score)), 2)

def calculate_additive_subscore(
    ingredients: List[Dict[str, Any]]
) -> Tuple[float, List[str]]:
    """
    Computes 0-100 additive profile score and returns list of informational deduction reasons.
    Neutral scientific approach: Additives are not labeled 'toxic', but presence of cosmetic
    colorants, artificial sweeteners, and ultra-processing texturizers is noted with calibrated deductions.
    Baseline is 100. Deductions capped at min 0.
    """
    score = 100.0
    reasons = []

    # Map of markers to deduction and neutral description
    # Sweeteners
    sweetener_markers = {"E950", "E951", "E952", "E954", "E955", "E960", "E961", "E962", "ASPARTAME", "SUCRALOSE", "ACESULFAME", "SACCHARIN", "STEVIOL"}
    # Artificial azo colors
    color_markers = {"E102", "E110", "E122", "E124", "E129", "E133", "TARTRAZINE", "SUNSET YELLOW", "ALLURA RED", "BRILLIANT BLUE"}
    # Preservatives / thickeners / emulsifiers
    texturizer_markers = {"E407", "E466", "E471", "E472", "CARRAGEENAN", "CARBOXYMETHYLCELLULOSE"}

    deductions_applied = set()

    for ing in ingredients:
        ins = (ing.get("ins_number") or "").upper().replace(" ", "")
        name = (ing.get("canonical_name", ing.get("name", "")) or "").upper()

        if any(sw in ins or sw in name for sw in sweetener_markers):
            if "sweetener" not in deductions_applied:
                deductions_applied.add("sweetener")
                score -= 15.0
                reasons.append("Contains non-nutritive sweetener (-15 pts per project ultra-processing criteria)")

        if any(cl in ins or cl in name for cl in color_markers):
            if "color" not in deductions_applied:
                deductions_applied.add("color")
                score -= 15.0
                reasons.append("Contains artificial food color (-15 pts per project additive criteria)")

        if any(tx in ins or tx in name for tx in texturizer_markers):
            if "texturizer" not in deductions_applied:
                deductions_applied.add("texturizer")
                score -= 10.0
                reasons.append("Contains industrial texturizer/emulsifier (-10 pts)")

        if ing.get("is_additive") and len(deductions_applied) < 5:
            # Minor general additive deduction
            score -= 2.0

    return round(max(0.0, min(100.0, score)), 2), reasons
