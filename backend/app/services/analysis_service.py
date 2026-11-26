import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models import Product, ProductScore, ScoringCriteria, Category
from app.schemas.schemas import NutritionOut, ProductIngredientItem
from app.core.exceptions import ProductNotFoundError, InsufficientDataError
from app.scoring.calculator import compute_product_analysis, CRITERIA_DEFAULTS
from app.core.logging_config import logger

CURRENT_SCORING_VERSION = "1.2.0"

class AnalysisService:
    def __init__(self):
        pass

    def _get_criteria_override(self, db: Session, product_type: str, category_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Loads criteria override from scoring_criteria table if customized by admin.
        Returns a dict formatted like criteria_defaults or None to use default.
        """
        query = db.query(ScoringCriteria).filter_by(product_type=product_type)
        if category_id:
            cat_criteria = query.filter_by(category_id=category_id).all()
            if cat_criteria:
                return self._build_criteria_dict(cat_criteria, product_type)

        # Fallback to general product_type criteria if exists in DB
        general_criteria = query.filter(ScoringCriteria.category_id.is_(None)).all()
        if general_criteria:
            return self._build_criteria_dict(general_criteria, product_type)

        return None

    def _build_criteria_dict(self, db_records: List[ScoringCriteria], product_type: str) -> Dict[str, Any]:
        params = {}
        for rec in db_records:
            # Map legacy names if present in DB
            param_key = rec.parameter_name
            if param_key == "sugar":
                param_key = "sugars"
            elif param_key == "protein":
                param_key = "proteins"
            elif param_key == "additive_penalty":
                param_key = "additives"

            params[param_key] = {
                "name": param_key.title(),
                "unit": rec.unit,
                "polarity": rec.polarity,
                "weight": rec.weight,
                "t_low": rec.low_threshold,
                "t_high": rec.high_threshold,
                "t_target": rec.high_threshold if rec.polarity == "positive" else None,
                "source": "Database scoring_criteria table"
            }
        return {"product_type": product_type, "parameters": params}

    def analyze_product(self, product: Product, db: Session) -> Dict[str, Any]:
        """
        Performs nutritional analysis for a Product ORM entity.
        Persists and caches the computed score in ProductScore table.
        Returns standardized analysis dict.
        """
        # Determine product type
        cat_type = product.category.product_type if product.category else "solid"
        
        # Build nutriments dict
        nutrition = product.nutrition
        nutriments = {}
        if nutrition:
            nutriments = {
                "energy_kcal": nutrition.energy_kcal,
                "energy_kj": nutrition.energy_kj,
                "fat_g": nutrition.fat_g,
                "saturated_fat_g": nutrition.saturated_fat_g,
                "trans_fat_g": nutrition.trans_fat_g,
                "carbohydrates_g": nutrition.carbohydrates_g,
                "sugars_g": nutrition.sugars_g,
                "added_sugars_g": nutrition.added_sugars_g,
                "fiber_g": nutrition.fiber_g,
                "proteins_g": nutrition.proteins_g,
                "sodium_mg": nutrition.sodium_mg,
                "salt_g": nutrition.salt_g,
                "fruits_vegetables_nuts_colza_walnut_olive_oils_pct": nutrition.fruits_vegetables_nuts_colza_walnut_olive_oils_pct
            }

        # Build ingredients list
        ingredients_list = []
        for pi in product.product_ingredients:
            c_name = pi.ingredient.canonical_name if pi.ingredient else "Unknown"
            ing_dict = {
                "canonical_name": c_name,
                "ingredient_name": c_name,
                "ins_number": pi.ingredient.ins_number if pi.ingredient else None,
                "is_additive": pi.ingredient.is_additive if pi.ingredient else False,
                "additive_type": pi.ingredient.additive_type if pi.ingredient else None,
                "position_order": pi.position_order,
                "is_whole_grain": pi.is_whole_grain,
                "is_allergen": getattr(pi, "is_allergen", False),
                "estimated_percentage": pi.estimated_percentage
            }
            ingredients_list.append(ing_dict)

        # Check criteria override from DB
        criteria_override = self._get_criteria_override(db, cat_type, product.category_id)

        # Run pure calculation
        is_water = "water" in (product.name or "").lower() and cat_type == "beverage"
        analysis_res = compute_product_analysis(
            product_type=cat_type,
            nutriments=nutriments,
            ingredients=ingredients_list,
            nova_group=product.nova_group,
            criteria_override=criteria_override,
            is_water=is_water
        )

        overall_score = analysis_res["overall_score"]
        score_band = analysis_res["score_band"]
        official_ref = analysis_res["official_reference"]

        # Persist or update ProductScore record
        try:
            existing_score = db.query(ProductScore).filter_by(product_id=product.id).first()
            if not existing_score:
                existing_score = ProductScore(
                    id=str(uuid.uuid4()),
                    product_id=product.id,
                    overall_project_score=overall_score if overall_score is not None else -1.0,
                    project_health_band=score_band,
                    official_nutri_score_grade=official_ref["grade"],
                    official_nutri_score_points=official_ref["points"],
                    confidence_score=analysis_res["confidence_score"],
                    sub_scores_json=json.dumps(analysis_res["sub_scores"]),
                    pros_json=json.dumps(analysis_res["pros"]),
                    cons_json=json.dumps(analysis_res["cons"]),
                    scoring_engine_version=CURRENT_SCORING_VERSION
                )
                db.add(existing_score)
            else:
                existing_score.overall_project_score = overall_score if overall_score is not None else -1.0
                existing_score.project_health_band = score_band
                existing_score.official_nutri_score_grade = official_ref["grade"]
                existing_score.official_nutri_score_points = official_ref["points"]
                existing_score.confidence_score = analysis_res["confidence_score"]
                existing_score.sub_scores_json = json.dumps(analysis_res["sub_scores"])
                existing_score.pros_json = json.dumps(analysis_res["pros"])
                existing_score.cons_json = json.dumps(analysis_res["cons"])
                existing_score.scoring_engine_version = CURRENT_SCORING_VERSION
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not persist ProductScore for product {product.id}: {e}")

        # Assemble full output response
        return {
            "product_id": product.id,
            "barcode": product.barcode,
            "product_name": product.name,
            "product_type": cat_type,
            "brand": product.brand,
            "image_url": product.image_url,
            "overall_project_score": overall_score,
            "score_band": score_band,
            "badge_color": analysis_res["badge_color"],
            "confidence_score": analysis_res["confidence_score"],
            "confidence_level": analysis_res["confidence_level"],
            "missing_parameters": analysis_res["missing_parameters"],
            "sub_scores": analysis_res["sub_scores"],
            "effective_weights": analysis_res["effective_weights"],
            "parameter_explanations": analysis_res["parameter_explanations"],
            "pros": analysis_res["pros"],
            "cons": analysis_res["cons"],
            "official_reference": official_ref,
            "calculated_at": datetime.now(timezone.utc),
            "scoring_engine_version": CURRENT_SCORING_VERSION,
            "source": getattr(product, "source", None),
            "nutrition": NutritionOut.model_validate(product.nutrition) if product.nutrition else None,
            "ingredients": [ProductIngredientItem(**i) for i in ingredients_list] if ingredients_list else []
        }

analysis_service = AnalysisService()
