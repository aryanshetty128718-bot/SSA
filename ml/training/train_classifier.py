"""
Model A: Multi-Class Product Category Classifier (Rigorous Group-Split Evaluation).
Splits train/test by product group_key (normalized name + brand) via GroupShuffleSplit.
Evaluates Linear SVM, Logistic Regression, Random Forest, and a Keyword Rule Baseline.
Reports Accuracy, Macro-F1, Confusion Matrix, and saves artifacts.
"""

import os
import re
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datetime import datetime
from typing import Dict, Any, List

from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

KEYWORD_RULES = {
    "breakfast-cereals": ["cereal", "muesli", "granola", "oats", "cornflakes", "chocos", "porridge", "cereales", "flocken"],
    "soft-drinks-sodas": ["soda", "cola", "carbonated", "soft drink", "fizzy", "sprite", "fanta", "pepsi", "boisson gazeuse"],
    "fruit-juices": ["juice", "nectar", "orange juice", "apple juice", "smoothie", "jus de fruits", "pur jus"],
    "yoghurts": ["yogurt", "yoghurt", "dahi", "curd", "fermented milk", "yaourt", "greek yogurt"],
    "biscuits-cookies": ["biscuit", "cookie", "cracker", "wafer", "shortbread", "biscotti", "galleta"],
    "chips-crisps-snacks": ["chips", "crisps", "potato chips", "nachos", "bhujia", "snack", "tortilla", "patatas fritas"],
    "chocolates-confectionery": ["chocolate", "candy", "cocoa", "toffee", "fudge", "chocolat", "bonbon"],
    "instant-noodles-pasta": ["noodle", "noodles", "pasta", "spaghetti", "macaroni", "ramen", "maggi", "nouilles", "pates"],
    "dairy-plant-drinks": ["milk", "soya milk", "almond milk", "oat milk", "dairy drink", "lait", "leche"],
    "breads-bakery": ["bread", "toast", "baguette", "bun", "bakery", "croissant", "loaf", "pain"]
}

def clean_key(name: str, brand: str) -> str:
    n = re.sub(r"[^a-z0-9]", "", str(name or "").lower())
    b = re.sub(r"[^a-z0-9]", "", str(brand or "").lower())
    return f"{n}_{b}"

def predict_baseline(text: str) -> str:
    t = str(text or "").lower()
    for cat, keywords in KEYWORD_RULES.items():
        if any(kw in t for kw in keywords):
            return cat
    return "chips-crisps-snacks"

def train_and_evaluate(processed_csv: str = "ml/data/processed/products_cleaned.csv",
                       artifacts_dir: str = "ml/artifacts",
                       evaluation_dir: str = "ml/evaluation"):
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(evaluation_dir, exist_ok=True)

    df = pd.read_csv(processed_csv)
    print(f"Loaded {len(df)} products for classification training.")

    df = df.dropna(subset=["category"]).copy()
    df["text_features"] = df["text_features"].fillna("")
    df["group_key"] = df.apply(lambda r: clean_key(r.get("product_name"), r.get("brand")), axis=1)

    print(f"Total products: {len(df)} | Unique product groups: {df['group_key'].nunique()}")

    nutrient_cols = [
        "energy_kcal_100g",
        "sugars_100g",
        "fat_100g",
        "saturated_fat_100g",
        "sodium_100g",
        "proteins_100g",
        "fiber_100g"
    ]

    X = df[["text_features", "group_key"] + nutrient_cols]
    y = df["category"]
    groups = df["group_key"]

    # Group-based 80/20 train/test split: guarantees variants of the same product NEVER straddle the split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
    y_train, y_test = y.iloc[train_idx].copy(), y.iloc[test_idx].copy()
    groups_train = groups.iloc[train_idx].copy()

    print(f"Group Split: Train set = {len(X_train)} samples ({groups_train.nunique()} groups) | Test set = {len(X_test)} samples ({groups.iloc[test_idx].nunique()} groups)")

    # Features
    text_transformer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=3500,
        sublinear_tf=True,
        stop_words="english"
    )

    nutrient_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    preprocessor = ColumnTransformer([
        ("text", text_transformer, "text_features"),
        ("nutr", nutrient_transformer, nutrient_cols)
    ])

    # Candidate Models
    models = {
        "LinearSVM": CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2500, random_state=42)),
        "LogisticRegression": LogisticRegression(max_iter=1000, C=2.0, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=16, random_state=42, n_jobs=-1)
    }

    # 5-Fold Stratified Group Cross-Validation
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = {}

    print("\n--- 5-Fold Stratified Group Cross-Validation ---")
    for name, clf in models.items():
        accuracies = []
        macro_f1s = []
        for fold, (f_train_idx, f_val_idx) in enumerate(sgkf.split(X_train, y_train, groups=groups_train)):
            X_f_tr, y_f_tr = X_train.iloc[f_train_idx], y_train.iloc[f_train_idx]
            X_f_val, y_f_val = X_train.iloc[f_val_idx], y_train.iloc[f_val_idx]

            pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", clf)
            ])
            pipe.fit(X_f_tr, y_f_tr)
            y_pred_val = pipe.predict(X_f_val)
            accuracies.append(accuracy_score(y_f_val, y_pred_val))
            macro_f1s.append(f1_score(y_f_val, y_pred_val, average="macro"))

        mean_acc = float(np.mean(accuracies))
        std_acc = float(np.std(accuracies))
        mean_f1 = float(np.mean(macro_f1s))
        std_f1 = float(np.std(macro_f1s))
        cv_results[name] = {
            "cv_accuracy_mean": mean_acc,
            "cv_accuracy_std": std_acc,
            "cv_f1_macro_mean": mean_f1,
            "cv_f1_macro_std": std_f1
        }
        print(f"{name:20s}: Accuracy={mean_acc:.4f} (+/- {std_acc:.4f}) | Macro-F1={mean_f1:.4f} (+/- {std_f1:.4f})")

    # Train best model on full training set
    best_name = max(cv_results, key=lambda k: cv_results[k]["cv_f1_macro_mean"])
    print(f"\nBest Model by Group-CV Macro-F1: {best_name}")

    best_pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", models[best_name])
    ])
    best_pipe.fit(X_train, y_train)

    # Evaluate on holdout test set (unseen groups)
    y_pred = best_pipe.predict(X_test)
    test_acc = float(accuracy_score(y_test, y_pred))
    test_f1 = float(f1_score(y_test, y_pred, average="macro"))
    labels = sorted(list(y.unique()))
    report_dict = classification_report(y_test, y_pred, target_names=labels, output_dict=True)

    # Evaluate Keyword Rule Baseline on test set
    y_pred_baseline = [predict_baseline(t) for t in X_test["text_features"]]
    base_acc = float(accuracy_score(y_test, y_pred_baseline))
    base_f1 = float(f1_score(y_test, y_pred_baseline, average="macro"))

    print(f"\n--- Held-Out Test Set Performance (Group-Split, Unseen Products) ---")
    print(f"Keyword Rule Baseline: Accuracy = {base_acc:.4f} | Macro-F1 = {base_f1:.4f}")
    print(f"Best ML ({best_name}) : Accuracy = {test_acc:.4f} | Macro-F1 = {test_f1:.4f}")
    delta_acc = (test_acc - base_acc) * 100
    print(f"-> ML Superiority over Rule Baseline: +{delta_acc:.2f} percentage points accuracy!")

    print("\nDetailed ML Classification Report:")
    print(classification_report(y_test, y_pred, target_names=labels))

    # Show cases where ML helps over baseline
    print("\n--- Diagnostic Cases: Where ML Model Wins Over Keyword Baseline ---")
    wins = []
    for idx, true_lbl, ml_lbl, base_lbl in zip(test_idx, y_test, y_pred, y_pred_baseline):
        if ml_lbl == true_lbl and base_lbl != true_lbl:
            row = df.iloc[idx]
            wins.append({
                "product_name": row["product_name"],
                "brand": row["brand"],
                "true_category": true_lbl,
                "ml_prediction": ml_lbl,
                "baseline_prediction": base_lbl,
                "text_snippet": row["text_features"][:70]
            })
            if len(wins) <= 5:
                print(f"  [{row['product_name'][:25]}] True: {true_lbl:22s} | ML: {ml_lbl:22s} | Baseline: {base_lbl}")

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    plt.figure(figsize=(10, 8))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix (Group-Split): {best_name} (Acc: {test_acc:.1%})", fontsize=13)
    plt.colorbar()
    tick_marks = np.arange(len(labels))
    plt.xticks(tick_marks, labels, rotation=45, ha="right", fontsize=9)
    plt.yticks(tick_marks, labels, fontsize=9)
    plt.xlabel("Predicted Category", fontsize=11)
    plt.ylabel("True Category", fontsize=11)
    plt.tight_layout()

    cm_plot_path = os.path.join(evaluation_dir, "confusion_matrix.png")
    plt.savefig(cm_plot_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix plot to {cm_plot_path}")

    # Save artifact
    model_artifact_path = os.path.join(artifacts_dir, "category_classifier.joblib")
    joblib.dump(best_pipe, model_artifact_path)
    print(f"Saved best model pipeline to {model_artifact_path}")

    metadata = {
        "model_type": best_name,
        "split_methodology": "GroupShuffleSplit (Grouped by normalized name+brand)",
        "training_timestamp": datetime.now().isoformat(),
        "total_dataset_size": len(df),
        "unique_groups": df["group_key"].nunique(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "categories": labels,
        "cv_results": cv_results,
        "baseline_comparison": {
            "baseline_type": "Deterministic Keyword / Substring Rules",
            "baseline_test_accuracy": base_acc,
            "baseline_test_macro_f1": base_f1,
            "ml_test_accuracy": test_acc,
            "ml_test_macro_f1": test_f1,
            "ml_accuracy_gain_pct_points": round(delta_acc, 2)
        },
        "test_metrics": {
            "accuracy": test_acc,
            "macro_f1": test_f1,
            "per_class": {lbl: report_dict[lbl] for lbl in labels}
        },
        "sample_ml_wins": wins[:10]
    }
    meta_path = os.path.join(artifacts_dir, "classifier_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved classifier metadata to {meta_path}")

    return metadata

if __name__ == "__main__":
    train_and_evaluate()
