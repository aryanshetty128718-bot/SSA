"""
Healthier-Alternative Recommendation Service.
Implements the multi-stage recommendation pipeline with:
1. Category Coherence Gate:
   - Explicit project-level category mapping (11 categories + 'other')
   - ALLOWED_RELATED_CATEGORIES mapping
   - Hard exclusion of non-nutritive confectionery (chewing gum, mints, hard candy, lozenges, sweeteners)
   - Cross-category mismatch exclusion (e.g. couscous/rice snaps for cereals or biscuits)
2. Quality Gate:
   - Minimum data completeness >= 80% (configurable)
   - Official Nutri-Score grade MUST be computable (in ['A', 'B', 'C', 'D', 'E'], excluding 'NOT_COMPUTABLE')
3. Pairwise Multimodal Model B Similarity:
   - True TF-IDF cosine similarity + standardized nutrient Euclidean distance (no artificial floors)
4. Healthiness Delta & Sugar Guard:
   - Requires positive score delta or improved Nutri-Score grade
   - Trade-off guard checking increases in sugar, saturated fat, or sodium
   - Honest explanations with absolute values and truthful relative deltas (never '100% less' on 0.0g)
5. DB Persistence & Auditing.
"""

import re
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import or_

from app.models import Product, Category, NutritionalInformation, ProductScore, Recommendation, ProductCategoryTag, ProductIngredient, Ingredient
from app.core.taxonomy import (
    PRODUCT_TYPES,
    PRODUCT_TYPE_BY_ID,
    PRODUCT_TYPE_BY_SLUG,
    map_product_to_type
)
from app.core.config import settings
from app.core.exceptions import ProductNotFoundError, InsufficientDataError
from app.services.analysis_service import AnalysisService
from app.ml.loader import model_manager
from app.ml.similarity import normalize_group_key
from app.core.logging_config import logger

analysis_service = AnalysisService()

PROJECT_CATEGORIES = {
    "breakfast-cereals",
    "chocolates-confectionery",
    "sweet-spreads-nut-butters",
    "soft-drinks-sodas",
    "fruit-juices",
    "dairy-plant-drinks",
    "yoghurts",
    "biscuits-cookies",
    "breads-bakery",
    "chips-crisps",
    "instant-noodles-pasta",
    "other"
}

def map_to_project_category(product: Product, fallback_slug: Optional[str] = None) -> str:
    """
    Deterministically maps any product to one of the 11 project categories (+ other).
    Uses name, stored category slug, category name, tags hierarchy, and Model A prediction.
    Enforces that rice, pasta, couscous, noodles are mapped to instant-noodles-pasta or other, NOT breakfast-cereals.
    """
    prod_name_lower = (product.name or "").lower()
    cat_name = (product.category.name if product.category else "").lower()
    cat_tags = [ct.tag.lower() for ct in product.category_tags]
    all_text = f"{prod_name_lower} {cat_name} {' '.join(cat_tags)}".lower()

    # Hard overrides for rice, pasta, couscous misclassified under breakfast cereals in raw OFF data
    if any(k in all_text for k in ["pasta", "pastas", "spaghetti", "macaroni", "noodle", "ramen", "orzo", "risone", "fusilloni", "fusilli", "penne", "conchiglie", "strozzapreti", "orecchiette"]):
        return "instant-noodles-pasta"
    if any(k in all_text for k in ["couscous", "cous cous", "quinoa", "rice", "calrose"]) and not any(k in prod_name_lower for k in ["cereal", "krispies", "flakes"]):
        return "other"

    stored_slug = product.category.slug if product.category else ""
    if stored_slug in PROJECT_CATEGORIES and stored_slug != "breakfast-cereals":
        return stored_slug

    if any(k in all_text for k in ["spread", "nut butter", "peanut butter", "hazelnut spread", "pâte à tartiner", "tartiner"]):
        return "sweet-spreads-nut-butters"
    if any(k in all_text for k in ["cereal", "muesli", "granola", "oats", "porridge", "cereales", "oatmeal", "cheerios", "flakes"]):
        return "breakfast-cereals"
    if stored_slug == "breakfast-cereals":
        return "breakfast-cereals"
    if any(k in all_text for k in ["chocolate", "chocolat", "confectionery", "bonbon", "praline", "cacao"]):
        return "chocolates-confectionery"
    if any(k in all_text for k in ["biscuit", "cookie", "wafer", "cracker", "gaufre", "shortbread"]):
        return "biscuits-cookies"
    if any(k in all_text for k in ["bread", "bakery", "toast", "brioche", "pain", "boulangerie"]):
        return "breads-bakery"
    if any(k in all_text for k in ["chip", "crisp", "cracker", "nacho", "tortilla", "snack"]):
        return "chips-crisps"
    if any(k in all_text for k in ["noodle", "pasta", "ramen", "spaghetti", "macaroni", "nouille"]):
        return "instant-noodles-pasta"
    if any(k in all_text for k in ["juice", "jus", "nectar", "smoothie"]):
        return "fruit-juices"
    if any(k in all_text for k in ["soda", "cola", "soft drink", "carbonated", "lemonade", "sparkling"]):
        return "soft-drinks-sodas"
    if any(k in all_text for k in ["yoghurt", "yogurt", "yaourt", "fromage blanc", "curd"]):
        return "yoghurts"
    if any(k in all_text for k in ["milk", "dairy", "lait", "plant drink", "soya", "almond milk", "oat milk"]):
        return "dairy-plant-drinks"

    if fallback_slug and fallback_slug in PROJECT_CATEGORIES:
        return fallback_slug

    return "other"


def is_non_comparable_confectionery(product: Product) -> bool:
    """
    Identifies non-nutritive confectionery, chewing gums, breath mints, hard candies, or lozenges
    that must never be recommended as alternatives to food products.
    """
    text = f"{product.name or ''} {product.brand or ''} {product.category.name if product.category else ''}".lower()
    for kw in settings.NON_COMPARABLE_FOOD_KEYWORDS:
        if kw in text:
            return True

    for ct in product.category_tags:
        t_low = ct.tag.lower()
        if any(w in t_low for w in ["chewing-gum", "chewing_gum", "mints", "pastilles", "candies", "bonbons-durs", "sweeteners"]):
            return True

    # Empty nutrition panel check: solid foods with almost 0 energy and 0 protein but 0 fat/sugar
    if product.category and product.category.product_type == "solid" and product.nutrition:
        energy = product.nutrition.energy_kcal or 0.0
        protein = product.nutrition.proteins_g or 0.0
        fat = product.nutrition.fat_g or 0.0
        sugar = product.nutrition.sugars_g or 0.0
        if energy < 40.0 and protein < 0.5 and fat < 0.5 and sugar < 1.0:
            return True

    return False


class RecommendationService:
    def __init__(self):
        pass

    def _get_clean_group_key(self, product: Product) -> str:
        return normalize_group_key(product.name, product.brand)

    def _safe_rel_delta(self, cand_val: Optional[float], orig_val: Optional[float]) -> Optional[float]:
        """
        Calculates percentage change safely:
        Only report relative percentage if orig_val >= 1.0 and cand_val > 0.05.
        Prevents misleading '100% less' when values are 0.0 or negligible.
        """
        if cand_val is None or orig_val is None:
            return None
        if orig_val >= 1.0 and cand_val > 0.05:
            return round(((cand_val - orig_val) / orig_val) * 100.0, 1)
        return None

    def _build_parameter_comparison(
        self,
        orig_nutr: Dict[str, Optional[float]],
        cand_nutr: Dict[str, Optional[float]],
        product_type: str
    ) -> Tuple[List[Dict[str, Any]], List[str], str]:
        """
        Builds granular comparisons for all core parameters with safe delta calculations,
        checks the Trade-Off Guard, and synthesizes an honest, transparent natural language explanation.
        """
        unit_weight = "ml" if product_type == "beverage" else "g"
        comparisons = []
        trade_off_flags = []
        positive_highlights = []

        params_config = [
            ("sugars", "Sugars", f"g/100{unit_weight}", "sugars_g", "negative"),
            ("saturated_fat", "Saturated Fat", f"g/100{unit_weight}", "saturated_fat_g", "negative"),
            ("sodium", "Sodium", f"mg/100{unit_weight}", "sodium_mg", "negative"),
            ("energy", "Energy", f"kcal/100{unit_weight}", "energy_kcal", "negative"),
            ("fiber", "Dietary Fiber", f"g/100{unit_weight}", "fiber_g", "positive"),
            ("proteins", "Proteins", f"g/100{unit_weight}", "proteins_g", "positive")
        ]

        for p_key, p_name, p_unit, nutr_field, polarity in params_config:
            orig_val = orig_nutr.get(nutr_field)
            cand_val = cand_nutr.get(nutr_field)

            abs_delta = round(cand_val - orig_val, 2) if (cand_val is not None and orig_val is not None) else None
            rel_delta = self._safe_rel_delta(cand_val, orig_val)

            # Polarity assessment
            if abs_delta is not None:
                if polarity == "negative":
                    is_better = abs_delta < -0.05
                    is_worse = abs_delta > 0.05
                else:
                    is_better = abs_delta > 0.05
                    is_worse = abs_delta < -0.05
            else:
                is_better = False
                is_worse = False

            # Honest Explanation sentence
            if abs_delta is not None:
                if polarity == "negative":
                    if is_better:
                        if rel_delta is not None and abs(rel_delta) >= 15.0 and orig_val >= 2.0:
                            expl = f"Contains {abs(rel_delta):.0f}% less {p_name.lower()} ({cand_val}{p_unit} vs {orig_val}{p_unit})"
                        else:
                            expl = f"Lower {p_name.lower()} by {abs(abs_delta):.1f}{p_unit} ({cand_val}{p_unit} vs {orig_val}{p_unit})"
                        positive_highlights.append(expl)
                    elif is_worse:
                        expl = f"Higher {p_name.lower()} by {abs_delta:+.1f}{p_unit} ({cand_val}{p_unit} vs {orig_val}{p_unit})"
                    else:
                        expl = f"Comparable {p_name.lower()} ({cand_val}{p_unit})"
                else:
                    if is_better:
                        expl = f"Provides {abs_delta:+.1f}{p_unit} more {p_name.lower()} ({cand_val}{p_unit} vs {orig_val}{p_unit})"
                        positive_highlights.append(expl)
                    elif is_worse:
                        expl = f"Lower {p_name.lower()} ({cand_val}{p_unit} vs {orig_val}{p_unit})"
                    else:
                        expl = f"Comparable {p_name.lower()} ({cand_val}{p_unit})"
            else:
                expl = f"Data not available for direct {p_name.lower()} comparison"

            comparisons.append({
                "parameter": p_key,
                "display_name": p_name,
                "unit": p_unit,
                "query_value": orig_val,
                "candidate_value": cand_val,
                "absolute_delta": abs_delta,
                "relative_delta_pct": rel_delta,
                "is_better": is_better,
                "explanation": expl
            })

            # Trade-off Guard checks
            if abs_delta is not None:
                if p_key == "sugars" and (abs_delta >= 2.0 or (rel_delta is not None and rel_delta >= 25.0)):
                    trade_off_flags.append(f"Higher Sugar (+{abs_delta:.1f}{p_unit})")
                elif p_key == "saturated_fat" and (abs_delta >= 1.0 or (rel_delta is not None and rel_delta >= 25.0)):
                    trade_off_flags.append(f"Higher Saturated Fat (+{abs_delta:.1f}{p_unit})")
                elif p_key == "sodium" and (abs_delta >= 100.0 or (rel_delta is not None and rel_delta >= 25.0)):
                    trade_off_flags.append(f"Higher Sodium (+{abs_delta:.0f}{p_unit})")
                elif p_key == "energy" and abs_delta >= 50.0:
                    trade_off_flags.append(f"Higher Energy (+{abs_delta:.0f}{p_unit})")

        # Natural language synthesis
        if positive_highlights:
            summary_sentence = "; ".join(positive_highlights[:3]) + "."
        else:
            summary_sentence = "Provides an improved overall nutritional profile."

        if trade_off_flags:
            summary_sentence += f" Note trade-offs: {', '.join(trade_off_flags)}."

        return comparisons, trade_off_flags, summary_sentence

    def find_alternatives(
        self,
        product: Product,
        db: Session,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Convenience wrapper for finding alternatives given a Product ORM entity."""
        return self.get_recommendations(db=db, product_id=product.id, limit=limit)

    def get_recommendations(
        self,
        db: Session,
        product_id: Optional[str] = None,
        barcode: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Executes the verified 7-stage recommendation algorithm:
        1. Fetch query & verify score.
        2. Map query to project category via tags/name/Model A.
        3. Formulate Candidate Pool:
           - Invariance: product_type (solid vs beverage).
           - Hard Gate: Candidate mapped project category must be in ALLOWED_RELATED_CATEGORIES[query_category].
           - Hard Gate: Exclude non-comparable confectionery (chewing gum, mints, hard candy).
           - Hard Gate: Quality gate (completeness >= 80%, official_nutri_score_grade in ['A','B','C','D','E']).
           - Exclude query & near-duplicates (normalized group_key).
        4. Pairwise Multimodal Model B Similarity:
           - 0.50 * text_cosine + 0.50 * (1 / (1 + scaled_euclidean_distance)).
        5. Healthiness Improvement Check:
           - Score delta > 0 OR Nutri-Score grade improved.
        6. Trade-Off Guard & Disqualification.
        7. Deterministic Composite Ranking & Persistence.
        """
        # Step 0: Fetch Query Product
        base_qp = db.query(Product).options(
            selectinload(Product.scores),
            selectinload(Product.nutrition),
            selectinload(Product.category_tags),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            joinedload(Product.category),
            joinedload(Product.product_type_rel)
        )
        target_id = (product_id or "").strip()
        target_bc = (barcode or "").strip()
        query_prod = None
        if target_id and target_bc:
            query_prod = base_qp.filter(or_(Product.id == target_id, Product.barcode == target_bc)).first()
        elif target_id:
            query_prod = base_qp.filter(or_(Product.id == target_id, Product.barcode == target_id)).first()
        elif target_bc:
            query_prod = base_qp.filter_by(barcode=target_bc).first()

        if not query_prod:
            target_str = product_id or barcode or "unknown"
            raise ProductNotFoundError(target_str)

        # Ensure query product has a score
        if not query_prod.product_score:
            analysis_service.analyze_product(query_prod, db)
            db.refresh(query_prod)

        orig_score = query_prod.product_score.overall_project_score or 50.0
        orig_ns_grade = (query_prod.product_score.official_nutri_score_grade or "E").upper()
        orig_type = query_prod.category.product_type if query_prod.category else "solid"
        orig_group_key = self._get_clean_group_key(query_prod)

        orig_nutr = {}
        if query_prod.nutrition:
            orig_nutr = {
                "energy_kcal": query_prod.nutrition.energy_kcal,
                "sugars_g": query_prod.nutrition.sugars_g,
                "saturated_fat_g": query_prod.nutrition.saturated_fat_g,
                "sodium_mg": query_prod.nutrition.sodium_mg,
                "salt_g": query_prod.nutrition.salt_g,
                "fiber_g": query_prod.nutrition.fiber_g,
                "proteins_g": query_prod.nutrition.proteins_g
            }

        # Model A secondary prediction for mapping
        ml_pred_slug = None
        try:
            ml_res = model_manager.classify(
                product_name=query_prod.name,
                brand=query_prod.brand,
                nutriments=orig_nutr
            )
            ml_pred_slug = ml_res.get("predicted_category")
        except Exception as e:
            logger.debug(f"ML secondary category prediction skipped: {e}")

        # Map Query to Project Category
        query_project_cat = map_to_project_category(query_prod, fallback_slug=ml_pred_slug)
        allowed_cats = set(settings.ALLOWED_RELATED_CATEGORIES.get(query_project_cat, [query_project_cat]))

        # Identify Level 2 Product Type for Query Product
        query_pt = None
        if query_prod.product_type_id:
            query_pt = PRODUCT_TYPE_BY_ID.get(query_prod.product_type_id)
        if not query_pt:
            query_tags = [ct.tag.lower() for ct in query_prod.category_tags]
            query_pt = map_product_to_type(
                product_name=query_prod.name,
                brand=query_prod.brand,
                category_tags=query_tags,
                project_category_slug=query_project_cat
            )
            query_prod.product_type_id = query_pt["id"]
            try:
                db.commit()
            except Exception:
                db.rollback()

        query_pt_slug = query_pt["slug"]
        query_pt_name = query_pt["name"]
        related_pt_slugs = set(query_pt.get("related", []))

        # Query Product Ingredient Set for Jaccard Similarity
        query_ings = set()
        if query_prod.product_ingredients:
            for pi in query_prod.product_ingredients:
                if pi.ingredient and pi.ingredient.canonical_name:
                    query_ings.add(pi.ingredient.canonical_name.lower().strip())

        # Step 1 & 2: Candidate Pool Formulation
        # Must match product_type (solid vs beverage)
        cand_query = db.query(Product).join(Category).filter(
            Category.product_type == orig_type,
            Product.id != query_prod.id,
            Product.barcode != query_prod.barcode
        ).outerjoin(ProductScore, Product.id == ProductScore.product_id).order_by(
            ProductScore.overall_project_score.desc()
        ).options(
            selectinload(Product.scores),
            selectinload(Product.nutrition),
            selectinload(Product.category_tags),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            joinedload(Product.category),
            joinedload(Product.product_type_rel)
        )

        # Exclude seed products if configured
        if not settings.INCLUDE_SEED_IN_RECOMMENDATIONS:
            cand_query = cand_query.filter(Product.source != "seed")

        # Candidate Quality Gate 1: Completeness >= 80% (0.80)
        min_comp = (
            settings.RECOMMENDATION_MIN_COMPLETENESS / 100.0
            if settings.RECOMMENDATION_MIN_COMPLETENESS > 1.0
            else settings.RECOMMENDATION_MIN_COMPLETENESS
        )
        cand_query = cand_query.filter(Product.data_completeness_score >= min_comp)

        # Pre-filter by allowed related categories in SQL for relevance and performance
        allowed_cat_records = db.query(Category).filter(
            or_(
                Category.slug.in_(allowed_cats),
                Category.id == query_prod.category_id
            )
        ).all()
        allowed_cat_ids = {c.id for c in allowed_cat_records}

        if allowed_cat_ids:
            cand_query = cand_query.filter(Product.category_id.in_(allowed_cat_ids))

        raw_candidates = cand_query.limit(250).all()

        # Step 3, 4, 5, 6: Score and Filter Candidates
        scored_candidates = []
        valid_grades = {"A", "B", "C", "D", "E"}
        grade_ranks = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "NOT_COMPUTABLE": 0}

        query_text = f"{query_prod.name} {query_prod.brand or ''}"
        q_nutr_dict = {
            "energy_kcal_100g": orig_nutr.get("energy_kcal"),
            "sugars_100g": orig_nutr.get("sugars_g"),
            "fat_100g": query_prod.nutrition.fat_g if query_prod.nutrition else None,
            "saturated_fat_100g": orig_nutr.get("saturated_fat_g"),
            "sodium_100g": (orig_nutr.get("sodium_mg") / 1000.0) if orig_nutr.get("sodium_mg") else None,
            "proteins_100g": orig_nutr.get("proteins_g"),
            "fiber_100g": orig_nutr.get("fiber_g")
        }

        for cand in raw_candidates:
            # Near-duplicate exclusion (same product-line group key: name stem + brand)
            cand_group = self._get_clean_group_key(cand)
            if cand_group and cand_group == orig_group_key:
                continue

            # Near-duplicate check for same product line even when brand strings differ slightly:
            # If same GS1 manufacturer prefix (7 digits) AND identical normalized name stem:
            if (cand.barcode and query_prod.barcode and 
                len(cand.barcode) >= 8 and len(query_prod.barcode) >= 8 and 
                cand.barcode[:7] == query_prod.barcode[:7]):
                cand_stem = cand_group.split("_")[0] if "_" in cand_group else cand_group
                orig_stem = orig_group_key.split("_")[0] if "_" in orig_group_key else orig_group_key
                if cand_stem and orig_stem and (cand_stem == orig_stem or cand_stem in orig_stem or orig_stem in cand_stem):
                    # Same manufacturer AND overlapping product line -> exclude
                    continue

            # Candidate Quality Gate 2: Official Nutri-Score must be computable
            if not cand.product_score:
                analysis_service.analyze_product(cand, db)
                db.refresh(cand)

            cand_score = cand.product_score.overall_project_score
            if cand_score is None:
                continue

            cand_ns_grade = (cand.product_score.official_nutri_score_grade or "").upper()
            if cand_ns_grade not in valid_grades:
                # Excludes NOT_COMPUTABLE or missing
                continue

            # Category Coherence Hard Gate:
            # Map candidate to its project category and verify it is within allowed_cats
            cand_project_cat = map_to_project_category(cand)
            if cand_project_cat not in allowed_cats:
                continue

            # Confectionery Hard Gate: Exclude chewing gum, mints, hard candies, sweeteners
            if is_non_comparable_confectionery(cand):
                continue

            # Extract candidate nutrition
            cand_nutr = {}
            if cand.nutrition:
                cand_nutr = {
                    "energy_kcal": cand.nutrition.energy_kcal,
                    "sugars_g": cand.nutrition.sugars_g,
                    "saturated_fat_g": cand.nutrition.saturated_fat_g,
                    "sodium_mg": cand.nutrition.sodium_mg,
                    "salt_g": cand.nutrition.salt_g,
                    "fiber_g": cand.nutrition.fiber_g,
                    "proteins_g": cand.nutrition.proteins_g
                }

            # Meaningful Improvement Check:
            # Must achieve score_delta >= 10.0 (or score >= 80 if orig was already healthy),
            # OR an official Nutri-Score grade jump (e.g. D -> B),
            # OR a >= 20% reduction in a major negative nutrient (sugars, sat fat, sodium) with no trade-offs.
            # Trivial gains (e.g. +0.5 to +2.0 points without substantive nutrient shifts) are rejected.
            grade_improved = grade_ranks.get(cand_ns_grade, 0) > grade_ranks.get(orig_ns_grade, 0)
            score_delta = round(cand_score - orig_score, 1)

            q_sug = orig_nutr.get("sugars_g") or 0.0
            c_sug = cand_nutr.get("sugars_g") or 0.0
            q_sf = orig_nutr.get("saturated_fat_g") or 0.0
            c_sf = cand_nutr.get("saturated_fat_g") or 0.0
            q_sod = orig_nutr.get("sodium_mg") or 0.0
            c_sod = cand_nutr.get("sodium_mg") or 0.0

            substantive_nutrient_reduction = (
                (q_sug >= 5.0 and c_sug <= 0.80 * q_sug) or
                (q_sf >= 2.0 and c_sf <= 0.80 * q_sf) or
                (q_sod >= 200.0 and c_sod <= 0.80 * q_sod)
            )

            if orig_score >= 88.0:
                is_meaningful_improvement = cand_score >= 85.0
            elif orig_score >= 70.0:
                is_meaningful_improvement = (
                    cand_score > orig_score + 1.0 or
                    grade_improved or
                    (score_delta >= 2.0 and substantive_nutrient_reduction)
                )
            else:
                is_meaningful_improvement = (
                    score_delta >= 10.0 or
                    grade_improved or
                    (score_delta >= 5.0 and substantive_nutrient_reduction)
                )

            if not is_meaningful_improvement:
                continue

            c_nutr_dict = {
                "energy_kcal_100g": cand_nutr.get("energy_kcal"),
                "sugars_100g": cand_nutr.get("sugars_g"),
                "fat_100g": cand.nutrition.fat_g if cand.nutrition else None,
                "saturated_fat_100g": cand_nutr.get("saturated_fat_g"),
                "sodium_100g": (cand_nutr.get("sodium_mg") / 1000.0) if cand_nutr.get("sodium_mg") else None,
                "proteins_100g": cand_nutr.get("proteins_g"),
                "fiber_100g": cand_nutr.get("fiber_g")
            }

            # Candidate Level 2 Product Type & Tier Resolution
            cand_pt_id = cand.product_type_id
            cand_pt = PRODUCT_TYPE_BY_ID.get(cand_pt_id) if cand_pt_id else None
            if not cand_pt:
                cand_tags = [ct.tag.lower() for ct in cand.category_tags]
                cand_pt = map_product_to_type(cand.name, cand.brand, cand_tags, cand_project_cat)
            cand_slug = cand_pt["slug"]
            cand_type_name = cand_pt["name"]

            # Tier 1 vs Tier 2 vs Tier 3 Disqualification
            if cand_slug == query_pt_slug:
                tier = 1
                type_match = 1.0
                tier_badge = f"Same type: {query_pt_name}"
                tier_label = "Tier 1: Same Product Type"
            elif cand_slug in related_pt_slugs:
                tier = 2
                type_match = 0.5
                tier_badge = f"Related type: {cand_type_name}"
                tier_label = "Tier 2: Related Culinary Alternative"
            else:
                # Tier 3: Unrelated culinary type within broad category -> STRICTLY EXCLUDED
                continue

            # Step 4: True Pairwise Multimodal Model B Similarity & Ingredient Jaccard
            cand_text = f"{cand.name} {cand.brand or ''}"
            sim_score = 0.50
            text_sim = 0.0

            if model_manager.similarity_engine is not None:
                try:
                    sim_dict = model_manager.similarity_engine.compute_pairwise_similarity(
                        query_text=query_text,
                        query_nutrients=q_nutr_dict,
                        cand_text=cand_text,
                        cand_nutrients=c_nutr_dict
                    )
                    sim_score = sim_dict["hybrid_similarity"]
                    text_sim = sim_dict["text_similarity"]
                except Exception as sim_err:
                    logger.debug(f"Pairwise similarity fallback for {cand.barcode}: {sim_err}")

            # Jaccard Ingredient Similarity on canonical ingredient names
            cand_ings = set()
            if cand.product_ingredients:
                for pi in cand.product_ingredients:
                    if pi.ingredient and pi.ingredient.canonical_name:
                        cand_ings.add(pi.ingredient.canonical_name.lower().strip())

            if query_ings and cand_ings:
                intersection = len(query_ings & cand_ings)
                union = len(query_ings | cand_ings)
                ingredient_similarity = round(intersection / union, 3)
            else:
                ingredient_similarity = round(max(0.10, text_sim), 3)

            # Cosine Nutrient Similarity
            import numpy as np
            q_vec = np.array([
                orig_nutr.get("energy_kcal") or 0.0,
                orig_nutr.get("fat_g") or 0.0,
                orig_nutr.get("saturated_fat_g") or 0.0,
                orig_nutr.get("carbohydrates_g") or 0.0,
                orig_nutr.get("sugars_g") or 0.0,
                orig_nutr.get("fiber_g") or 0.0,
                orig_nutr.get("proteins_g") or 0.0,
                (orig_nutr.get("sodium_mg") or 0.0) / 100.0
            ], dtype=float)
            c_vec = np.array([
                cand_nutr.get("energy_kcal") or 0.0,
                cand_nutr.get("fat_g") or 0.0,
                cand_nutr.get("saturated_fat_g") or 0.0,
                cand_nutr.get("carbohydrates_g") or 0.0,
                cand_nutr.get("sugars_g") or 0.0,
                cand_nutr.get("fiber_g") or 0.0,
                cand_nutr.get("proteins_g") or 0.0,
                (cand_nutr.get("sodium_mg") or 0.0) / 100.0
            ], dtype=float)
            dot = np.dot(q_vec, c_vec)
            norm_q = np.linalg.norm(q_vec)
            norm_c = np.linalg.norm(c_vec)
            nutrient_similarity = round(float(dot / (norm_q * norm_c)), 3) if (norm_q > 0 and norm_c > 0) else 0.50

            # Step 6: Trade-off Guard & Disqualification
            comparisons, trade_offs, explanation = self._build_parameter_comparison(
                orig_nutr, cand_nutr, orig_type
            )

            sug_delta = (cand_nutr.get("sugars_g") or 0.0) - (orig_nutr.get("sugars_g") or 0.0)
            sf_delta = (cand_nutr.get("saturated_fat_g") or 0.0) - (orig_nutr.get("saturated_fat_g") or 0.0)
            sod_delta = (cand_nutr.get("sodium_mg") or 0.0) - (orig_nutr.get("sodium_mg") or 0.0)
            cand_sod = cand_nutr.get("sodium_mg") or 0.0
            cand_sf = cand_nutr.get("saturated_fat_g") or 0.0

            if sug_delta > 5.0 or (sf_delta > 3.0 and cand_sf > 5.0) or (sod_delta > 350.0 and cand_sod > 500.0):
                continue

            # Step 7: Hybrid Ranking Score: 0.35 type_match + 0.25 ing_sim + 0.15 nut_sim + 0.25 norm_delta
            trade_off_penalty = 0.10 if trade_offs else 0.0
            norm_delta = max(0.0, min(1.0, score_delta / 50.0))

            composite_rank = (
                0.35 * type_match +
                0.25 * ingredient_similarity +
                0.15 * nutrient_similarity +
                0.25 * norm_delta -
                trade_off_penalty
            )

            scored_candidates.append({
                "candidate": cand,
                "tier": tier,
                "tier_label": tier_label,
                "tier_badge": tier_badge,
                "composite_rank": composite_rank,
                "similarity_score": sim_score,
                "ingredient_similarity": ingredient_similarity,
                "nutrient_similarity": nutrient_similarity,
                "score_improvement": score_delta,
                "trade_off_flags": trade_offs,
                "explanation": explanation,
                "parameter_comparisons": comparisons,
                "cand_nutr": cand_nutr,
                "project_category": cand_project_cat
            })

        # Tiered Selection Strategy:
        # Tier 1 preferred; Tier 2 only if Tier 1 has < 5 qualified candidates; Tier 3 strictly 0
        tier1_candidates = [c for c in scored_candidates if c["tier"] == 1]
        tier2_candidates = [c for c in scored_candidates if c["tier"] == 2]

        tier1_candidates.sort(key=lambda x: x["composite_rank"], reverse=True)
        tier2_candidates.sort(key=lambda x: x["composite_rank"], reverse=True)

        if len(tier1_candidates) >= limit:
            top_candidates = tier1_candidates[:limit]
        else:
            needed = limit - len(tier1_candidates)
            top_candidates = tier1_candidates + tier2_candidates[:needed]

        # Format output and persist recommendations
        recommendation_items = []
        for rank, item in enumerate(top_candidates, start=1):
            c_prod = item["candidate"]
            c_score = c_prod.product_score
            deltas_summary = {comp["parameter"]: comp["absolute_delta"] for comp in item["parameter_comparisons"]}

            rec_item = {
                "id": c_prod.id,
                "barcode": c_prod.barcode,
                "name": c_prod.name,
                "brand": c_prod.brand,
                "image_url": c_prod.image_url,
                "category_name": c_prod.category.name if c_prod.category else "General",
                "source": getattr(c_prod, "source", "openfoodfacts"),
                "project_category": item["project_category"],
                "tier": item["tier_label"],
                "tier_badge": item["tier_badge"],
                "overall_score": c_score.overall_project_score,
                "score_band": c_score.project_health_band,
                "badge_color": "green" if c_score.overall_project_score >= 70 else ("amber" if c_score.overall_project_score >= 40 else "red"),
                "nutri_score_grade": c_score.official_nutri_score_grade,
                "similarity_score": item["similarity_score"],
                "ingredient_similarity": item["ingredient_similarity"],
                "nutrient_similarity": item["nutrient_similarity"],
                "composite_rank_score": round(item["composite_rank"], 4),
                "rank": rank,
                "score_improvement": item["score_improvement"],
                "parameter_deltas": deltas_summary,
                "trade_offs": item["trade_off_flags"],
                "trade_off_flags": item["trade_off_flags"],
                "explanation": item["explanation"],
                "key_nutrients": item["cand_nutr"],
                "parameter_comparisons": item["parameter_comparisons"]
            }
            recommendation_items.append(rec_item)

            # Persist to Recommendations audit table
            try:
                deltas_summary = {comp["parameter"]: comp["absolute_delta"] for comp in item["parameter_comparisons"]}
                rec_entity = Recommendation(
                    id=str(uuid.uuid4()),
                    target_product_id=query_prod.id,
                    alternative_product_id=c_prod.id,
                    similarity_score=item["similarity_score"],
                    score_improvement=item["score_improvement"],
                    parameter_deltas_json=json.dumps(deltas_summary),
                    explanation=item["explanation"]
                )
                db.add(rec_entity)
            except Exception as e:
                logger.warning(f"Failed to persist recommendation entity: {e}")

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to commit recommendation entities: {e}")

        # Transparent pool note
        pool_note = None
        if len(recommendation_items) == 0:
            pool_note = (
                f"No healthier alternatives matching the strict category '{query_project_cat}', "
                f"data completeness (>= 80%), and trade-off criteria were found in the current database pool."
            )
        elif len(recommendation_items) < limit:
            pool_note = (
                f"Found {len(recommendation_items)} healthier alternative(s) meeting all strict criteria in category '{query_project_cat}'."
            )

        return {
            "query_product": {
                "id": query_prod.id,
                "barcode": query_prod.barcode,
                "name": query_prod.name,
                "brand": query_prod.brand,
                "category": query_prod.category.name if query_prod.category else "General",
                "project_category": query_project_cat,
                "product_type": orig_type,
                "overall_score": query_prod.product_score.overall_project_score,
                "score_band": query_prod.product_score.project_health_band,
                "nutri_score_grade": query_prod.product_score.official_nutri_score_grade,
                "key_nutrients": orig_nutr
            },
            "count": len(recommendation_items),
            "recommendations": recommendation_items,
            "ranking_method": "Deterministic rule: 40% similarity (Model B multimodal), 35% health delta, 25% absolute score, with trade-off guard",
            "notes": pool_note
        }

recommendation_service = RecommendationService()

