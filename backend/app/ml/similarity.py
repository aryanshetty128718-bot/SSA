"""
Multimodal Similarity Engine for Food & Beverage Alternatives.
Combines Text TF-IDF cosine similarity with standardized nutrient Euclidean distance.
Supports near-duplicate exclusion via normalized product group keys.
"""

from typing import List, Dict, Any, Optional
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

# Specific pack and size descriptors only.
# Meaningful distinct product-line words ("gold", "original", "tea", "classic", "vita") are NOT stripped.
SIZE_PACK_WORDS = {
    "100g", "200g", "250g", "400g", "500g", "800g", "1kg", "2kg", "g", "kg", "ml", "l", "oz",
    "pack", "packs", "multipack", "piece", "pieces", "packet", "slice", "slices",
    "biscuit", "biscuits", "cookie", "cookies", "mini", "family", "value"
}

BRAND_CORP_SUFFIXES = {
    "ltd", "limited", "pvt", "private", "industries", "india", "holdings", "co", "company", "corp", "corporation"
}

def normalize_group_key(name: Optional[str], brand: Optional[str]) -> str:
    """
    Computes a canonical product-line key for near-duplicate exclusion.
    Strips size/pack words and corporate suffixes, but preserves meaningful
    product line words (e.g., 'gold', 'original', 'tea', 'marie', 'good day').
    Ensures identical product lines across pack sizes (e.g., 'Marie Gold 250g' vs 'Marie Gold 500g')
    are excluded, while distinct product lines (e.g. 'Good Day' vs 'Marie Gold') are allowed.
    """
    raw_name = str(name or "").lower()
    raw_brand = str(brand or "").lower()

    # Clean brand
    b_tokens = [w for w in re.sub(r"[^a-z0-9\s]", " ", raw_brand).split() if w not in BRAND_CORP_SUFFIXES]
    b_clean = "".join(b_tokens)

    # Clean name: remove size patterns, pure numbers, pack words, and repeated brand tokens
    n_tokens = []
    for w in re.sub(r"[^a-z0-9\s]", " ", raw_name).split():
        if w in SIZE_PACK_WORDS or re.match(r"^\d+(g|kg|ml|l|oz)?$", w) or (b_clean and w in b_tokens):
            continue
        n_tokens.append(w)
    
    n_clean = "".join(sorted(n_tokens))
    if not n_clean:
        # Fallback if all tokens were stripped
        n_clean = re.sub(r"[^a-z0-9]", "", raw_name)

    return f"{n_clean}_{b_clean}"

class SimilarityEngine:
    def __init__(self, alpha: float = 0.50):
        self.alpha = alpha
        self.text_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=2500,
            sublinear_tf=True,
            stop_words="english"
        )
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        
        self.catalog_df: Optional[pd.DataFrame] = None
        self.text_matrix = None
        self.nutrient_matrix = None
        self.nutrient_cols = [
            "energy_kcal_100g",
            "sugars_100g",
            "fat_100g",
            "saturated_fat_100g",
            "sodium_100g",
            "proteins_100g",
            "fiber_100g"
        ]

    def fit(self, df: pd.DataFrame):
        self.catalog_df = df.copy().reset_index(drop=True)
        if "group_key" not in self.catalog_df.columns:
            self.catalog_df["group_key"] = self.catalog_df.apply(
                lambda r: normalize_group_key(r.get("product_name"), r.get("brand")), axis=1
            )

        texts = self.catalog_df["text_features"].fillna("").tolist()
        self.text_matrix = self.text_vectorizer.fit_transform(texts)

        nutrients_raw = self.catalog_df[self.nutrient_cols].values
        nutrients_imputed = self.imputer.fit_transform(nutrients_raw)
        self.nutrient_matrix = self.scaler.fit_transform(nutrients_imputed)
        return self

    def find_similar(self,
                     query_text: str,
                     query_nutrients: Dict[str, Optional[float]],
                     category_filter: Optional[str] = None,
                     top_k: int = 5,
                     exclude_code: Optional[str] = None,
                     exclude_group_key: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.catalog_df is None or self.text_matrix is None:
            raise RuntimeError("SimilarityEngine has not been fitted.")

        # Transform query text
        q_text_vec = self.text_vectorizer.transform([query_text or ""])
        text_sims = cosine_similarity(q_text_vec, self.text_matrix)[0]

        # Transform query nutrients
        q_nutr_raw = np.array([[query_nutrients.get(c) for c in self.nutrient_cols]], dtype=float)
        q_nutr_imputed = self.imputer.transform(q_nutr_raw)
        q_nutr_scaled = self.scaler.transform(q_nutr_imputed)
        
        # Nutrient distance -> similarity
        nutr_dists = euclidean_distances(q_nutr_scaled, self.nutrient_matrix)[0]
        nutr_sims = 1.0 / (1.0 + nutr_dists)

        # Hybrid similarity score
        hybrid_scores = self.alpha * text_sims + (1.0 - self.alpha) * nutr_sims

        # Masking / Filtering
        candidate_indices = np.arange(len(self.catalog_df))
        mask = np.ones(len(self.catalog_df), dtype=bool)

        if category_filter:
            mask = mask & (self.catalog_df["category"] == category_filter).values

        if exclude_code:
            mask = mask & (self.catalog_df["code"].astype(str) != str(exclude_code)).values

        if exclude_group_key:
            mask = mask & (self.catalog_df["group_key"] != exclude_group_key).values

        candidate_indices = candidate_indices[mask]
        if len(candidate_indices) == 0:
            return []

        # Sort top indices
        candidate_scores = hybrid_scores[candidate_indices]
        top_sub_idx = np.argsort(candidate_scores)[::-1][:top_k]
        best_indices = candidate_indices[top_sub_idx]

        results = []
        for rank, idx in enumerate(best_indices):
            row = self.catalog_df.iloc[idx]
            results.append({
                "rank": rank + 1,
                "code": str(row["code"]),
                "product_name": row["product_name"],
                "brand": row["brand"],
                "category": row["category"],
                "group_key": row.get("group_key", ""),
                "hybrid_similarity": float(round(hybrid_scores[idx], 4)),
                "text_similarity": float(round(text_sims[idx], 4)),
                "nutrient_similarity": float(round(nutr_sims[idx], 4)),
                "nutriments": {col: (None if pd.isna(row[col]) else float(row[col])) for col in self.nutrient_cols}
            })
        return results

    def compute_pairwise_similarity(
        self,
        query_text: str,
        query_nutrients: Dict[str, Optional[float]],
        cand_text: str,
        cand_nutrients: Dict[str, Optional[float]]
    ) -> Dict[str, float]:
        """
        Computes true multimodal hybrid similarity between a query and a candidate product.
        Returns hybrid_similarity, text_similarity, and nutrient_similarity without artificial floors.
        """
        if self.text_vectorizer is None or self.scaler is None:
            raise RuntimeError("SimilarityEngine has not been fitted.")

        q_t_vec = self.text_vectorizer.transform([query_text or ""])
        c_t_vec = self.text_vectorizer.transform([cand_text or ""])
        text_sim = float(cosine_similarity(q_t_vec, c_t_vec)[0][0])

        q_nutr_raw = np.array([[query_nutrients.get(c) for c in self.nutrient_cols]], dtype=float)
        c_nutr_raw = np.array([[cand_nutrients.get(c) for c in self.nutrient_cols]], dtype=float)

        q_nutr_scaled = self.scaler.transform(self.imputer.transform(q_nutr_raw))
        c_nutr_scaled = self.scaler.transform(self.imputer.transform(c_nutr_raw))

        nutr_dist = float(euclidean_distances(q_nutr_scaled, c_nutr_scaled)[0][0])
        nutr_sim = 1.0 / (1.0 + nutr_dist)

        hybrid_sim = float(round(self.alpha * text_sim + (1.0 - self.alpha) * nutr_sim, 4))
        return {
            "hybrid_similarity": hybrid_sim,
            "text_similarity": round(text_sim, 4),
            "nutrient_similarity": round(nutr_sim, 4)
        }
