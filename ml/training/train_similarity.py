"""
Model B: Multimodal Similarity & Alternative Recommendation Engine.
Imports SimilarityEngine from app.ml.similarity, trains on products_cleaned.csv,
evaluates Top-1 and Top-5 same-category precision strictly excluding query product AND its near-duplicates.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.ml.similarity import SimilarityEngine, normalize_group_key

def evaluate_and_train_similarity(processed_csv: str = "ml/data/processed/products_cleaned.csv",
                                  artifacts_dir: str = "ml/artifacts",
                                  evaluation_dir: str = "ml/evaluation"):
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(evaluation_dir, exist_ok=True)

    df = pd.read_csv(processed_csv)
    print(f"Loaded {len(df)} products for Similarity Engine.")

    engine = SimilarityEngine(alpha=0.50)
    engine.fit(df)

    # Holdout evaluation of Top-1 and Top-5 Precision:
    # Strictly exclude query product itself AND any candidate with the same group_key (near-duplicates)
    np.random.seed(42)
    sample_indices = np.random.choice(len(df), size=min(400, len(df)), replace=False)
    
    precisions_top5 = []
    precisions_top1 = []

    for idx in sample_indices:
        target_row = df.iloc[idx]
        target_cat = target_row["category"]
        target_code = str(target_row["code"])
        target_group = normalize_group_key(target_row["product_name"], target_row["brand"])
        target_text = str(target_row["text_features"])
        target_nutr = {c: target_row[c] for c in engine.nutrient_cols}

        # Query WITHOUT category filter, strictly excluding self and all near-duplicates in group
        recs = engine.find_similar(
            query_text=target_text,
            query_nutrients=target_nutr,
            category_filter=None,
            top_k=5,
            exclude_code=target_code,
            exclude_group_key=target_group
        )

        if recs:
            matches = [1 if r["category"] == target_cat else 0 for r in recs]
            precisions_top5.append(sum(matches) / len(matches))
            precisions_top1.append(matches[0])

    mean_p5 = float(np.mean(precisions_top5)) if precisions_top5 else 0.0
    mean_p1 = float(np.mean(precisions_top1)) if precisions_top1 else 0.0

    print(f"\n--- Similarity Engine Holdout Evaluation ({len(sample_indices)} test queries, near-duplicates excluded) ---")
    print(f"Top-1 Same-Category Precision: {mean_p1:.4f} ({mean_p1*100:.1f}%)")
    print(f"Top-5 Intra-Category Retrieval Precision: {mean_p5:.4f} ({mean_p5*100:.1f}%)")

    # Save artifact
    artifact_path = os.path.join(artifacts_dir, "similarity_engine.joblib")
    joblib.dump(engine, artifact_path)
    print(f"Saved similarity engine artifact to {artifact_path}")

    metadata = {
        "model_type": "Hybrid TF-IDF Cosine + Nutrient Euclidean Proximity",
        "evaluation_rule": "Strictly excludes query product AND near-duplicate group variants",
        "training_timestamp": datetime.now().isoformat(),
        "catalog_size": len(df),
        "alpha_text_weight": engine.alpha,
        "evaluation": {
            "test_sample_size": len(sample_indices),
            "top1_category_precision": mean_p1,
            "top5_intra_category_precision": mean_p5
        }
    }
    meta_path = os.path.join(artifacts_dir, "similarity_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved similarity metadata to {meta_path}")

    return metadata

if __name__ == "__main__":
    evaluate_and_train_similarity()
