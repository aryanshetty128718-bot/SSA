"""
Product Comparison Service.
Provides comprehensive side-by-side nutritional and score comparison across 2 to 4 products.
Evaluates parameter-level matrices, identifies best performers per nutrient with polarity awareness,
and synthesizes nuanced, balanced verdicts without declaring unqualified winners.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Product
from app.core.exceptions import ProductNotFoundError
from app.services.analysis_service import AnalysisService
from app.schemas.comparison import (
    ComparisonProductItem,
    ComparisonMatrixItem,
    ProductComparisonRequest,
    ProductComparisonResponse
)

analysis_service = AnalysisService()

class ComparisonService:
    def compare_products(
        self,
        request: ProductComparisonRequest,
        db: Session
    ) -> ProductComparisonResponse:
        """
        Compares 2 to 4 products side-by-side.
        Accepts either a list of product UUIDs or barcodes.
        """
        # 1. Validate input size
        identifiers: List[str] = []
        is_barcode = False

        if request.barcodes and len(request.barcodes) > 0:
            identifiers = request.barcodes
            is_barcode = True
        elif request.product_ids and len(request.product_ids) > 0:
            identifiers = request.product_ids
            is_barcode = False
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'barcodes' or 'product_ids' must be provided with 2 to 4 products."
            )

        # Deduplicate while preserving order
        unique_identifiers = list(dict.fromkeys(identifiers))
        if len(unique_identifiers) < 2:
            raise HTTPException(
                status_code=400,
                detail="Comparison requires at least 2 distinct products."
            )
        if len(unique_identifiers) > 4:
            raise HTTPException(
                status_code=400,
                detail="Comparison supports at most 4 products simultaneously."
            )

        # 2. Retrieve products from DB
        products: List[Product] = []
        for ident in unique_identifiers:
            # Query flexibly by either ID or Barcode
            prod = db.query(Product).filter((Product.id == ident) | (Product.barcode == ident)).first()
            if not prod:
                raise ProductNotFoundError(f"Product '{ident}' was not found in the database.")
            products.append(prod)

        # 3. Build product items with scores, pros/cons, and nutrients
        product_items: List[ComparisonProductItem] = []
        confidence_notes: List[str] = []
        has_solids = False
        has_beverages = False

        for prod in products:
            p_type = prod.category.product_type if prod.category else "solid"
            if p_type == "beverage":
                has_beverages = True
            else:
                has_solids = True

            # Ensure product analysis is cached
            if not prod.product_score:
                analysis_service.analyze_product(prod, db)
                db.refresh(prod)

            score = prod.product_score
            overall = score.overall_project_score if score else None
            band = score.project_health_band if score else "Unknown"
            badge = "green" if overall and overall >= 70 else ("amber" if overall and overall >= 40 else "red")
            raw_conf = score.confidence_score if score else 0.5
            conf_pct = round(raw_conf * 100.0, 1) if raw_conf <= 1.0 else round(raw_conf, 1)

            if conf_pct < 80.0:
                confidence_notes.append(
                    f"{prod.name} ({prod.barcode}) has a reduced data confidence of {conf_pct:.0f}% due to unrecorded nutrient fields."
                )

            # Nutrients dict
            nutr = prod.nutrition
            nutrients_dict: Dict[str, Optional[float]] = {
                "energy_kcal": nutr.energy_kcal if nutr else None,
                "sugars_g": nutr.sugars_g if nutr else None,
                "saturated_fat_g": nutr.saturated_fat_g if nutr else None,
                "sodium_mg": nutr.sodium_mg if nutr else None,
                "salt_g": nutr.salt_g if nutr else None,
                "fiber_g": nutr.fiber_g if nutr else None,
                "proteins_g": nutr.proteins_g if nutr else None,
            }

            # Ingredients list
            ingredients = [
                pi.ingredient.canonical_name for pi in prod.product_ingredients if pi.ingredient
            ]

            # Sub-scores dict
            sub_scores_dict: Dict[str, Optional[float]] = {}
            if score and score.sub_scores_json:
                import json
                try:
                    sub_scores_dict = json.loads(score.sub_scores_json)
                except Exception:
                    pass

            # Pros & cons
            pros_list = []
            cons_list = []
            if score and score.pros_json:
                import json
                try:
                    pros_list = json.loads(score.pros_json)
                except Exception:
                    pass
            if score and score.cons_json:
                import json
                try:
                    cons_list = json.loads(score.cons_json)
                except Exception:
                    pass

            product_items.append(
                ComparisonProductItem(
                    id=str(prod.id),
                    barcode=prod.barcode,
                    name=prod.name,
                    brand=prod.brand,
                    image_url=prod.image_url,
                    category_name=prod.category.name if prod.category else "General",
                    overall_score=overall,
                    score_band=band,
                    badge_color=badge,
                    nutri_score_grade=score.official_nutri_score_grade if score else None,
                    confidence_score=conf_pct,
                    nutrients=nutrients_dict,
                    sub_scores=sub_scores_dict,
                    pros=pros_list,
                    cons=cons_list,
                    ingredients=ingredients
                )
            )

        # 4. Construct Comparison Matrix
        matrix_configs = [
            ("sugars_g", "Sugars", "g", "negative"),
            ("saturated_fat_g", "Saturated Fat", "g", "negative"),
            ("sodium_mg", "Sodium", "mg", "negative"),
            ("energy_kcal", "Energy", "kcal", "negative"),
            ("fiber_g", "Dietary Fiber", "g", "positive"),
            ("proteins_g", "Proteins", "g", "positive"),
            ("salt_g", "Salt", "g", "negative"),
            ("overall_project_score", "Overall Health Score", "/100", "positive")
        ]

        matrix_items: List[ComparisonMatrixItem] = []
        wins_count: Dict[str, int] = {p.barcode: 0 for p in products}

        for param_key, display_name, unit, polarity in matrix_configs:
            val_map: Dict[str, Optional[float]] = {}
            for p in product_items:
                if param_key == "overall_project_score":
                    val_map[p.barcode] = p.overall_score
                else:
                    val_map[p.barcode] = p.nutrients.get(param_key)

            # Determine best barcode
            valid_items = [(b, v) for b, v in val_map.items() if v is not None]
            best_barcode = None
            summary_text = ""

            if valid_items:
                if polarity == "negative":
                    # Lowest is healthiest
                    best_barcode, best_val = min(valid_items, key=lambda x: x[1])
                    # Check if all valid items are tied
                    all_tied = all(abs(v - best_val) < 1e-4 for _, v in valid_items)
                    if all_tied and len(valid_items) > 1:
                        best_barcode = None
                        summary_text = f"All compared products have identical {display_name.lower()} ({best_val} {unit})."
                    else:
                        wins_count[best_barcode] += 1
                        best_name = next(p.name for p in product_items if p.barcode == best_barcode)
                        summary_text = f"{best_name} has the lowest {display_name.lower()} ({best_val} {unit})."
                else:
                    # Highest is healthiest
                    best_barcode, best_val = max(valid_items, key=lambda x: x[1])
                    all_tied = all(abs(v - best_val) < 1e-4 for _, v in valid_items)
                    if all_tied and len(valid_items) > 1:
                        best_barcode = None
                        summary_text = f"All compared products have identical {display_name.lower()} ({best_val} {unit})."
                    else:
                        wins_count[best_barcode] += 1
                        best_name = next(p.name for p in product_items if p.barcode == best_barcode)
                        summary_text = f"{best_name} offers the highest {display_name.lower()} ({best_val} {unit})."
            else:
                summary_text = f"Nutrient data for {display_name.lower()} is not recorded for any of the compared products."

            matrix_items.append(
                ComparisonMatrixItem(
                    parameter=param_key,
                    display_name=display_name,
                    unit=unit,
                    polarity=polarity,
                    values=val_map,
                    best_barcode=best_barcode,
                    summary=summary_text
                )
            )

        # 5. Formulate Nuanced Summary Verdict
        # Sort products by overall score descending
        sorted_prods = sorted(
            product_items,
            key=lambda x: (x.overall_score if x.overall_score is not None else -1),
            reverse=True
        )

        top_prod = sorted_prods[0]
        runner_up = sorted_prods[1]

        # Check for dominating product
        top_wins = wins_count.get(top_prod.barcode, 0)
        total_eval_params = len([m for m in matrix_items if m.best_barcode is not None])

        verdict_parts = []

        if has_solids and has_beverages:
            confidence_notes.append(
                "Notice: This comparison includes both solid foods and beverages. Standards, thresholds, and serving units (per 100g vs per 100ml) differ between product types."
            )

        if top_wins == total_eval_params and total_eval_params >= 5:
            verdict_parts.append(
                f"{top_prod.name} comprehensively outperforms other options across all evaluated parameters, achieving a score of {top_prod.overall_score:.1f}/100."
            )
        elif top_prod.overall_score is not None and runner_up.overall_score is not None:
            score_diff = top_prod.overall_score - runner_up.overall_score
            if score_diff >= 15.0:
                verdict_parts.append(
                    f"{top_prod.name} holds a substantial nutritional advantage (score {top_prod.overall_score:.1f}/100 vs {runner_up.name}'s {runner_up.overall_score:.1f}/100)."
                )
            elif score_diff >= 5.0:
                verdict_parts.append(
                    f"{top_prod.name} leads marginally in overall nutritional quality (score {top_prod.overall_score:.1f}/100 vs {runner_up.name}'s {runner_up.overall_score:.1f}/100)."
                )
            else:
                verdict_parts.append(
                    f"{top_prod.name} and {runner_up.name} have closely matched nutritional profiles (scores {top_prod.overall_score:.1f} and {runner_up.overall_score:.1f} respectively)."
                )

            # Highlight specific trade-offs between top products
            advantages: List[str] = []
            for m in matrix_items:
                if m.best_barcode == top_prod.barcode and m.parameter != "overall_project_score":
                    advantages.append(f"lower {m.display_name.lower()}" if m.polarity == "negative" else f"higher {m.display_name.lower()}")

            runner_advantages: List[str] = []
            for m in matrix_items:
                if m.best_barcode == runner_up.barcode and m.parameter != "overall_project_score":
                    runner_advantages.append(f"lower {m.display_name.lower()}" if m.polarity == "negative" else f"higher {m.display_name.lower()}")

            if advantages:
                verdict_parts.append(f"Key strengths for {top_prod.name} include {', '.join(advantages[:3])}.")
            if runner_advantages:
                verdict_parts.append(f"However, {runner_up.name} holds advantages in {', '.join(runner_advantages[:3])}.")

        summary_verdict = " ".join(verdict_parts)

        return ProductComparisonResponse(
            products=product_items,
            comparison_matrix=matrix_items,
            summary_verdict=summary_verdict,
            data_confidence_notes=confidence_notes
        )

comparison_service = ComparisonService()
