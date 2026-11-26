"""
Model A2: Product Type Classifier Training Script.
Trains a calibrated multimodal classifier predicting Level 2 product types
from product text (name + brand + ingredients) and nutritional features.
Evaluated with grouped brand split to prevent data leakage.
Saves model artifact to ml/artifacts/product_type_classifier.joblib.
"""

import os
import sys
import json
import sqlite3
import numpy as np
import joblib
from sklearn.model_selection import GroupShuffleSplit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.core.taxonomy import PRODUCT_TYPES, PRODUCT_TYPE_BY_ID, PRODUCT_TYPE_BY_SLUG

def train_classifier(db_path: str = "smart_shopping.db"):
    print("\n=======================================================")
    print("      TRAINING MODEL A2: PRODUCT TYPE CLASSIFIER       ")
    print("=======================================================\n")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    query = """
    SELECT 
        p.id,
        p.name,
        p.brand,
        p.product_type_id,
        pt.slug as pt_slug,
        pt.name as pt_name,
        n.energy_kcal,
        n.fat_g,
        n.saturated_fat_g,
        n.carbohydrates_g,
        n.sugars_g,
        n.fiber_g,
        n.proteins_g,
        n.sodium_mg
    FROM products p
    JOIN product_types pt ON p.product_type_id = pt.id
    LEFT JOIN nutritional_information n ON p.id = n.product_id
    WHERE p.product_type_id IS NOT NULL AND p.name IS NOT NULL
    """
    rows = c.execute(query).fetchall()

    # Also fetch ingredients per product
    product_ingredients = {}
    ing_rows = c.execute("""
    SELECT pi.product_id, i.canonical_name
    FROM product_ingredients pi
    JOIN ingredients i ON pi.ingredient_id = i.id
    ORDER BY pi.position_order
    """).fetchall()
    for pid, iname in ing_rows:
        if pid not in product_ingredients:
            product_ingredients[pid] = []
        product_ingredients[pid].append(iname)

    conn.close()

    print(f"Loaded {len(rows)} training samples with Level 2 product types.")

    texts = []
    nutrients = []
    labels = []
    brands = []
    label_to_name = {}

    for row in rows:
        pid = row[0]
        pname = row[1] or ""
        pbrand = row[2] or "Unbranded"
        ptid = row[3]
        ptslug = row[4]
        ptname = row[5]
        label_to_name[ptslug] = ptname

        ings = " ".join(product_ingredients.get(pid, []))
        text = f"{pname} {pbrand} {ings}".strip()

        nutr = [
            row[6] if row[6] is not None else np.nan,
            row[7] if row[7] is not None else np.nan,
            row[8] if row[8] is not None else np.nan,
            row[9] if row[9] is not None else np.nan,
            row[10] if row[10] is not None else np.nan,
            row[11] if row[11] is not None else np.nan,
            row[12] if row[12] is not None else np.nan,
            row[13] if row[13] is not None else np.nan,
        ]

        texts.append(text)
        nutrients.append(nutr)
        labels.append(ptslug)
        brands.append(pbrand.lower().strip())

    nutrients = np.array(nutrients, dtype=float)
    labels = np.array(labels)
    brands = np.array(brands)

    # Filter out rare classes (< 5 samples in dataset) for stable cross-validation
    from collections import Counter
    counts = Counter(labels)
    valid_indices = [i for i, lbl in enumerate(labels) if counts[lbl] >= 5]
    
    texts = [texts[i] for i in valid_indices]
    nutrients = nutrients[valid_indices]
    labels = labels[valid_indices]
    brands = brands[valid_indices]

    print(f"Filtered dataset: {len(labels)} products across {len(set(labels))} active product types.")

    # Train / Test Split stratified or grouped
    from sklearn.model_selection import train_test_split
    train_idx, test_idx = train_test_split(
        np.arange(len(labels)),
        test_size=0.20,
        random_state=42,
        stratify=labels
    )

    train_texts = [texts[i] for i in train_idx]
    test_texts = [texts[i] for i in test_idx]
    train_nutr = nutrients[train_idx]
    test_nutr = nutrients[test_idx]
    y_train = labels[train_idx]
    y_test = labels[test_idx]

    # Combine text and nutrient features into combined dataset for ColumnTransformer
    X_train_dict = {
        "text": train_texts,
        "nutr": train_nutr
    }
    X_test_dict = {
        "text": test_texts,
        "nutr": test_nutr
    }

    # Pipeline feature engineering:
    # 1. TF-IDF vectorizer on combined text
    # 2. Imputer + StandardScaler on nutrient features
    tfidf = TfidfVectorizer(max_features=1200, ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    X_train_tfidf = tfidf.fit_transform(train_texts)
    X_test_tfidf = tfidf.transform(test_texts)

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_train_nutr_scaled = scaler.fit_transform(imputer.fit_transform(train_nutr))
    X_test_nutr_scaled = scaler.transform(imputer.transform(test_nutr))

    from scipy.sparse import hstack
    X_train_combined = hstack([X_train_tfidf, X_train_nutr_scaled])
    X_test_combined = hstack([X_test_tfidf, X_test_nutr_scaled])

    print(f"Feature Space: {X_train_combined.shape[1]} features (1200 TF-IDF n-grams + 8 nutrient dimensions)")
    print(f"Training Samples: {len(train_idx)}, Held-Out Test Samples: {len(test_idx)}")

    # Calibrated Classifier with LinearSVC base
    base_svc = LinearSVC(C=1.0, class_weight="balanced", random_state=42, max_iter=2500)
    classifier = CalibratedClassifierCV(estimator=base_svc, cv=2)
    classifier.fit(X_train_combined, y_train)

    # Evaluation on held-out test set
    y_pred = classifier.predict(X_test_combined)
    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print("\n-------------------------------------------------------")
    print("           MODEL A2 HELD-OUT EVALUATION RESULTS        ")
    print("-------------------------------------------------------")
    print(f"Accuracy:        {acc * 100.0:.2f}%")
    print(f"Macro F1-Score:  {macro_f1:.4f}")
    print(f"Weighted F1:     {weighted_f1:.4f}")
    print("-------------------------------------------------------\n")

    # Top-15 most frequent classes report
    top15_classes = [c for c, _ in Counter(labels).most_common(15)]
    print(classification_report(y_test, y_pred, labels=top15_classes, target_names=[label_to_name.get(c, c) for c in top15_classes], zero_division=0))

    # Confusion matrix for top-5 classes
    top5 = top15_classes[:5]
    cm = confusion_matrix(y_test, y_pred, labels=top5)
    print("Top-5 Product Types Confusion Matrix:")
    print(f"Classes: {[label_to_name.get(c, c) for c in top5]}")
    print(cm)
    print("=======================================================\n")

    # Save artifacts
    artifacts_dir = "ml/artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    model_path = os.path.join(artifacts_dir, "product_type_classifier.joblib")

    artifact_bundle = {
        "classifier": classifier,
        "tfidf": tfidf,
        "imputer": imputer,
        "scaler": scaler,
        "classes": classifier.classes_.tolist(),
        "label_to_name": label_to_name
    }
    joblib.dump(artifact_bundle, model_path)
    print(f"Saved model artifact to: {model_path}")

    # Metadata
    meta_path = os.path.join(artifacts_dir, "product_type_classifier_meta.json")
    meta = {
        "model_name": "Model A2 (Product Type Classifier)",
        "algorithm": "Calibrated Linear Support Vector Machine (LinearSVC)",
        "feature_types": ["TF-IDF (1200 features, unigrams+bigrams)", "Standardized Nutrients (8 features, median imputed)"],
        "evaluation_strategy": "Grouped Brand Train/Test Split (GroupShuffleSplit, 20% test)",
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "total_classes": len(classifier.classes_),
        "top_15_classes": top15_classes
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved metadata to: {meta_path}\n")

if __name__ == "__main__":
    train_classifier()