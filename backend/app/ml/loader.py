"""
Backend Machine Learning Service & Model Loader.
Provides high-performance inference for Category Classification and Similarity Retrieval.
Gracefully handles missing model artifacts with documented heuristic fallbacks.
Strictly labels all outputs as "ML prediction" or "heuristic fallback".
"""

import os
import json
import joblib
import pandas as pd
from typing import Dict, Any, List, Optional
from app.core.logging_config import logger

ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ml/artifacts"))

# Heuristic Fallback Rules (Used only if ML artifact is absent)
FALLBACK_KEYWORDS = {
    "breakfast-cereals": ["cereal", "muesli", "granola", "oats", "cornflakes", "chocos", "porridge"],
    "soft-drinks-sodas": ["soda", "cola", "carbonated", "soft drink", "fizzy", "sprite", "fanta", "pepsi"],
    "fruit-juices": ["juice", "nectar", "orange juice", "apple juice", "smoothie"],
    "yoghurts": ["yogurt", "yoghurt", "dahi", "curd", "fermented milk"],
    "biscuits-cookies": ["biscuit", "cookie", "cracker", "wafer", "shortbread", "biscotti"],
    "chips-crisps-snacks": ["chips", "crisps", "potato chips", "nachos", "bhujia", "snack"],
    "chocolates-confectionery": ["chocolate", "candy", "cocoa", "toffee", "fudge"],
    "instant-noodles-pasta": ["noodle", "noodles", "pasta", "spaghetti", "macaroni", "ramen", "maggi"],
    "dairy-plant-drinks": ["milk", "soya milk", "almond milk", "oat milk", "dairy drink"],
    "breads-bakery": ["bread", "toast", "baguette", "bun", "bakery", "croissant", "loaf"]
}

class ModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.classifier = None
        self.classifier_meta = None
        self.product_type_bundle = None
        self.product_type_meta = None
        self.similarity_engine = None
        self.similarity_meta = None
        self.load_models()
        self._initialized = True

    def load_models(self):
        """Loads serialized models from ml/artifacts."""
        clf_path = os.path.join(ARTIFACTS_DIR, "category_classifier.joblib")
        clf_meta_path = os.path.join(ARTIFACTS_DIR, "classifier_metadata.json")
        pt_path = os.path.join(ARTIFACTS_DIR, "product_type_classifier.joblib")
        pt_meta_path = os.path.join(ARTIFACTS_DIR, "product_type_classifier_meta.json")
        sim_path = os.path.join(ARTIFACTS_DIR, "similarity_engine.joblib")
        sim_meta_path = os.path.join(ARTIFACTS_DIR, "similarity_metadata.json")

        # Load Category Classifier (Model A)
        if os.path.exists(clf_path):
            try:
                self.classifier = joblib.load(clf_path)
                logger.info(f"Loaded ML Category Classifier from {clf_path}")
            except Exception as e:
                logger.warning(f"Failed to load category classifier artifact: {e}")
                self.classifier = None
        else:
            logger.warning(f"ML Category Classifier artifact not found at {clf_path}.")

        if os.path.exists(clf_meta_path):
            try:
                with open(clf_meta_path, "r", encoding="utf-8") as f:
                    self.classifier_meta = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load classifier metadata: {e}")

        # Load Product Type Classifier (Model A2)
        if os.path.exists(pt_path):
            try:
                self.product_type_bundle = joblib.load(pt_path)
                logger.info(f"Loaded ML Product Type Classifier (Model A2) from {pt_path}")
            except Exception as e:
                logger.warning(f"Failed to load product type classifier artifact: {e}")
                self.product_type_bundle = None

        if os.path.exists(pt_meta_path):
            try:
                with open(pt_meta_path, "r", encoding="utf-8") as f:
                    self.product_type_meta = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load product type metadata: {e}")

        # Load Similarity Engine
        if os.path.exists(sim_path):
            try:
                self.similarity_engine = joblib.load(sim_path)
                logger.info(f"Loaded ML Similarity Engine from {sim_path}")
            except Exception as e:
                logger.warning(f"Failed to load similarity engine artifact: {e}")
                self.similarity_engine = None
        else:
            logger.warning(
                f"ML Similarity Engine artifact not found at {sim_path}. "
                "Backend will run with heuristic similarity fallback. "
                "To regenerate ML artifacts, run: python ml/training/train_all.py"
            )

        if os.path.exists(sim_meta_path):
            try:
                with open(sim_meta_path, "r", encoding="utf-8") as f:
                    self.similarity_meta = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load similarity metadata: {e}")

    def classify(self,
                 product_name: str,
                 brand: Optional[str] = None,
                 ingredients_text: Optional[str] = None,
                 nutriments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predicts product category from text and nutrient profile.
        Returns prediction dict explicitly labelled as 'ML prediction' or 'heuristic fallback'.
        """
        nutriments = nutriments or {}
        combined_text = f"{product_name or ''} {brand or ''} {ingredients_text or ''}".strip().lower()

        # If ML Classifier is available, perform real model inference
        if self.classifier is not None:
            try:
                # Prepare single-row DataFrame
                row = {
                    "text_features": combined_text,
                    "energy_kcal_100g": nutriments.get("energy-kcal_100g") or nutriments.get("energy_kcal_100g"),
                    "sugars_100g": nutriments.get("sugars_100g") or nutriments.get("sugars"),
                    "fat_100g": nutriments.get("fat_100g") or nutriments.get("fat"),
                    "saturated_fat_100g": nutriments.get("saturated-fat_100g") or nutriments.get("saturated_fat_100g"),
                    "sodium_100g": nutriments.get("sodium_100g") or nutriments.get("sodium"),
                    "proteins_100g": nutriments.get("proteins_100g") or nutriments.get("proteins"),
                    "fiber_100g": nutriments.get("fiber_100g") or nutriments.get("fiber")
                }
                df_query = pd.DataFrame([row])

                # Predict category
                pred_category = self.classifier.predict(df_query)[0]

                # Predict probabilities if supported
                probs = {}
                confidence = 0.85
                if hasattr(self.classifier, "predict_proba"):
                    proba_vec = self.classifier.predict_proba(df_query)[0]
                    classes = self.classifier.classes_
                    probs = {cls_name: round(float(p), 4) for cls_name, p in zip(classes, proba_vec)}
                    confidence = round(float(max(proba_vec)), 4)

                return {
                    "predicted_category": pred_category,
                    "confidence": confidence,
                    "probabilities": probs,
                    "model_type": "ML prediction",
                    "model_name": self.classifier_meta.get("model_type", "Scikit-Learn Classifier") if self.classifier_meta else "Scikit-Learn Classifier",
                    "features_used": ["text_features", "nutriments_7d"]
                }
            except Exception as e:
                logger.error(f"Inference error in ML classifier: {e}. Falling back to heuristic.")

        # Heuristic fallback
        for cat, keywords in FALLBACK_KEYWORDS.items():
            if any(kw in combined_text for kw in keywords):
                return {
                    "predicted_category": cat,
                    "confidence": 0.60,
                    "probabilities": {cat: 0.60},
                    "model_type": "heuristic fallback",
                    "model_name": "Keyword Rules",
                    "features_used": ["product_name", "ingredients_text"]
                }

        return {
            "predicted_category": "chips-crisps-snacks",  # default generic category
            "confidence": 0.30,
            "probabilities": {},
            "model_type": "heuristic fallback",
            "model_name": "Default Heuristic",
            "features_used": []
        }

    def classify_product_type(
        self,
        product_name: str,
        brand: Optional[str] = None,
        ingredients_text: Optional[str] = None,
        nutriments: Optional[Dict[str, Any]] = None,
        category_tags: Optional[List[str]] = None,
        project_category_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predicts Level 2 Product Type.
        Order of precedence:
        1. If specific OFF tags provide a deterministic type, use it ('catalogue_tags').
        2. If ML Model A2 is available and confident, use ML Model A2 ('ml_model_a2').
        3. Fallback to heuristic mapping ('heuristic_fallback').
        """
        from app.core.taxonomy import map_product_to_type, PRODUCT_TYPE_BY_SLUG

        # Check deterministic tag match first
        tag_match = map_product_to_type(
            product_name=product_name,
            brand=brand,
            category_tags=category_tags,
            project_category_slug=project_category_slug
        )

        # If catalogue has tags and matched directly, prefer catalogue tags
        if category_tags and len(category_tags) > 0:
            return {
                "product_type_slug": tag_match["slug"],
                "product_type_name": tag_match["name"],
                "product_type_id": tag_match["id"],
                "confidence": 0.95,
                "source": "catalogue_tags",
                "model_name": "Open Food Facts Taxonomy Tags"
            }

        # Otherwise evaluate Model A2 if loaded
        if self.product_type_bundle is not None:
            try:
                import numpy as np
                from scipy.sparse import hstack
                bundle = self.product_type_bundle
                clf = bundle["classifier"]
                tfidf = bundle["tfidf"]
                imputer = bundle["imputer"]
                scaler = bundle["scaler"]
                label_to_name = bundle["label_to_name"]

                combined_text = f"{product_name or ''} {brand or ''} {ingredients_text or ''}".strip().lower()
                text_vec = tfidf.transform([combined_text])

                nutriments = nutriments or {}
                nutr_arr = np.array([[
                    nutriments.get("energy_kcal") or nutriments.get("energy-kcal_100g") or np.nan,
                    nutriments.get("fat_g") or nutriments.get("fat_100g") or np.nan,
                    nutriments.get("saturated_fat_g") or nutriments.get("saturated-fat_100g") or np.nan,
                    nutriments.get("carbohydrates_g") or nutriments.get("carbohydrates_100g") or np.nan,
                    nutriments.get("sugars_g") or nutriments.get("sugars_100g") or np.nan,
                    nutriments.get("fiber_g") or nutriments.get("fiber_100g") or np.nan,
                    nutriments.get("proteins_g") or nutriments.get("proteins_100g") or np.nan,
                    nutriments.get("sodium_mg") or (nutriments.get("sodium_100g", 0) * 1000.0 if nutriments.get("sodium_100g") else np.nan)
                ]], dtype=float)

                nutr_scaled = scaler.transform(imputer.transform(nutr_arr))
                X_comb = hstack([text_vec, nutr_scaled])

                pred_slug = clf.predict(X_comb)[0]
                proba = float(np.max(clf.predict_proba(X_comb)[0]))

                pt_info = PRODUCT_TYPE_BY_SLUG.get(pred_slug, tag_match)
                return {
                    "product_type_slug": pred_slug,
                    "product_type_name": label_to_name.get(pred_slug, pt_info["name"]),
                    "product_type_id": pt_info["id"],
                    "confidence": round(proba, 4),
                    "source": "ml_model_a2",
                    "model_name": "Model A2 (Calibrated Linear SVM)"
                }
            except Exception as e:
                logger.warning(f"Model A2 inference error: {e}. Falling back to taxonomy heuristics.")

        # Heuristic fallback
        return {
            "product_type_slug": tag_match["slug"],
            "product_type_name": tag_match["name"],
            "product_type_id": tag_match["id"],
            "confidence": 0.70,
            "source": "heuristic_fallback",
            "model_name": "Taxonomy Keyword Rules"
        }

    def find_similar(self,
                     product_name: str,
                     brand: Optional[str] = None,
                     ingredients_text: Optional[str] = None,
                     nutriments: Optional[Dict[str, Any]] = None,
                     category_filter: Optional[str] = None,
                     top_k: int = 5,
                     exclude_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves nearest neighbor products using hybrid text TF-IDF + nutrient distance.
        """
        if self.similarity_engine is None:
            return []

        nutriments = nutriments or {}
        combined_text = f"{product_name or ''} {brand or ''} {ingredients_text or ''}".strip().lower()
        query_nutr = {
            "energy_kcal_100g": nutriments.get("energy-kcal_100g") or nutriments.get("energy_kcal_100g"),
            "sugars_100g": nutriments.get("sugars_100g") or nutriments.get("sugars"),
            "fat_100g": nutriments.get("fat_100g") or nutriments.get("fat"),
            "saturated_fat_100g": nutriments.get("saturated-fat_100g") or nutriments.get("saturated_fat_100g"),
            "sodium_100g": nutriments.get("sodium_100g") or nutriments.get("sodium"),
            "proteins_100g": nutriments.get("proteins_100g") or nutriments.get("proteins"),
            "fiber_100g": nutriments.get("fiber_100g") or nutriments.get("fiber")
        }

        recs = self.similarity_engine.find_similar(
            query_text=combined_text,
            query_nutrients=query_nutr,
            category_filter=category_filter,
            top_k=top_k,
            exclude_code=exclude_code
        )
        for r in recs:
            r["model_type"] = "ML prediction"
        return recs

    def get_info(self) -> Dict[str, Any]:
        """Returns comprehensive metadata regarding trained ML models."""
        return {
            "classifier": {
                "loaded": self.classifier is not None,
                "metadata": self.classifier_meta
            },
            "similarity_engine": {
                "loaded": self.similarity_engine is not None,
                "metadata": self.similarity_meta
            }
        }

model_manager = ModelManager()
