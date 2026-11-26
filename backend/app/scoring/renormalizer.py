from typing import Dict, Any, List, Optional, Tuple

def renormalize_weights(
    sub_scores: Dict[str, Optional[float]],
    baseline_weights: Dict[str, float],
    min_weight_threshold: float = 0.50
) -> Tuple[Optional[float], Dict[str, float], float, str, List[str]]:
    """
    Computes null-safe weighted average project score by dynamically renormalizing weights
    over all available (non-None) parameters.

    Returns:
        overall_score: float (0.0 - 100.0) or None if total available weight < min_weight_threshold
        renormalized_weights: Dict mapping param_name -> renormalized weight (sums to 1.0)
        confidence_score: float (0.0 - 1.0, representing fraction of baseline weights available)
        confidence_level: 'High' (>= 0.85), 'Medium' (>= 0.60), 'Low' (< 0.60)
        missing_parameters: List of parameter names that were None
    """
    available_params = {}
    missing_params = []

    for param, score in sub_scores.items():
        if score is not None and param in baseline_weights:
            available_params[param] = baseline_weights[param]
        else:
            missing_params.append(param)

    total_avail_weight = sum(available_params.values())
    confidence_score = round(total_avail_weight, 3)

    if confidence_score >= 0.85:
        confidence_level = "High"
    elif confidence_score >= 0.60:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"

    # If available weight is below minimum threshold (e.g. 50%), reject calculation
    if total_avail_weight < min_weight_threshold:
        return None, {}, confidence_score, confidence_level, missing_params

    # Renormalize weights: w_i* = w_i / total_avail_weight
    renormalized_weights = {
        param: round(weight / total_avail_weight, 4)
        for param, weight in available_params.items()
    }

    # Slight floating-point adjustment so sum is exactly 1.0
    weight_sum = sum(renormalized_weights.values())
    if weight_sum > 0 and renormalized_weights:
        # adjust the first key
        first_key = next(iter(renormalized_weights))
        renormalized_weights[first_key] += round(1.0 - weight_sum, 4)

    # Compute overall score
    overall_score = sum(
        renormalized_weights[p] * sub_scores[p]
        for p in available_params
    )

    return round(max(0.0, min(100.0, overall_score)), 2), renormalized_weights, confidence_score, confidence_level, missing_params
