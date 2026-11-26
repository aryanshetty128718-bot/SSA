"""
Real Data Score Validation & Nutri-Score 2023 Correlation Analysis.
Validates the Proposed Project Scoring Algorithm against official Nutri-Score 2023 points
on complete real Open Food Facts products (excluding seed data).
Calculates Spearman rank correlation, grade-by-grade distributions, and diagnoses major discrepancies.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add backend to path so we can import scoring calculators directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.scoring.calculator import compute_product_analysis

BEVERAGE_CATEGORIES = {"soft-drinks-sodas", "fruit-juices", "dairy-plant-drinks"}

def validate_on_real_data(processed_csv: str = "ml/data/processed/products_cleaned.csv",
                           evaluation_dir: str = "ml/evaluation"):
    os.makedirs(evaluation_dir, exist_ok=True)

    if not os.path.exists(processed_csv):
        raise FileNotFoundError(f"Processed file not found: {processed_csv}")

    df = pd.read_csv(processed_csv)
    print(f"Loaded {len(df)} cleaned real products for algorithm validation.")

    # Select complete products that have all core nutrients
    core_nutrients = [
        "energy_kcal_100g",
        "sugars_100g",
        "saturated_fat_100g",
        "sodium_100g",
        "proteins_100g",
        "fiber_100g"
    ]
    complete_df = df.dropna(subset=core_nutrients).copy()
    print(f"Found {len(complete_df)} products with complete core nutrition across all 6 parameters.")

    results = []
    for _, row in complete_df.iterrows():
        cat = str(row["category"])
        prod_type = "beverage" if cat in BEVERAGE_CATEGORIES else "solid"

        nutriments = {
            "energy_kcal": float(row["energy_kcal_100g"]),
            "sugars_g": float(row["sugars_100g"]),
            "saturated_fat_g": float(row["saturated_fat_100g"]),
            "sodium_mg": float(row["sodium_100g"]) * 1000.0,
            "salt_g": float(row["sodium_100g"]) * 2.5,
            "proteins_g": float(row["proteins_100g"]),
            "fiber_g": float(row["fiber_100g"])
        }

        nova = int(row["nova_group"]) if pd.notna(row["nova_group"]) else None

        analysis = compute_product_analysis(
            product_type=prod_type,
            nutriments=nutriments,
            ingredients=[],
            nova_group=nova
        )

        proj_score = analysis.get("overall_score")
        conf_pct = analysis.get("confidence_score")
        ns_ref = analysis.get("official_reference", {})
        ns_pts = ns_ref.get("points")
        ns_grade = ns_ref.get("grade")

        if proj_score is None or ns_pts is None or ns_grade in ("NOT_COMPUTABLE", None):
            continue

        results.append({
            "code": str(row["code"]),
            "product_name": str(row["product_name"]),
            "category": cat,
            "product_type": prod_type,
            "is_india": bool(row.get("is_india", False)),
            "project_score": proj_score,
            "data_confidence_pct": conf_pct,
            "nutri_score_2023_points": ns_pts,
            "nutri_score_2023_grade": ns_grade,
            "sugars": nutriments["sugars_g"],
            "sat_fat": nutriments["saturated_fat_g"],
            "sodium": nutriments["sodium_mg"] / 1000.0,
            "energy_kcal": nutriments["energy_kcal"],
            "fiber": nutriments["fiber_g"],
            "proteins": nutriments["proteins_g"]
        })

    v_df = pd.DataFrame(results)
    print(f"Successfully computed paired scores for {len(v_df)} real OFF products.")

    # Spearman & Pearson Correlation
    # Nutri-Score points: lower points = healthier.
    # Project score: higher score = healthier.
    # Therefore, true correlation is strongly negative.
    spearman_corr, sp_pvalue = spearmanr(v_df["project_score"], v_df["nutri_score_2023_points"])
    pearson_corr, pe_pvalue = pearsonr(v_df["project_score"], v_df["nutri_score_2023_points"])

    print(f"\n--- Correlation Analysis (n={len(v_df)}) ---")
    print(f"Spearman Rank Correlation: {spearman_corr:.4f} (p-value: {sp_pvalue:.2e})")
    print(f"Pearson Linear Correlation: {pearson_corr:.4f} (p-value: {pe_pvalue:.2e})")

    # Grade-by-grade Project Score statistics
    grade_order = ["A", "B", "C", "D", "E"]
    grade_summary = {}
    print("\n--- Grade-by-Grade Project Score Distribution ---")
    for g in grade_order:
        sub = v_df[v_df["nutri_score_2023_grade"] == g]["project_score"]
        if len(sub) > 0:
            mean_s = float(sub.mean())
            std_s = float(sub.std()) if len(sub) > 1 else 0.0
            median_s = float(sub.median())
            grade_summary[g] = {
                "count": len(sub),
                "mean_project_score": round(mean_s, 2),
                "std_project_score": round(std_s, 2),
                "median_project_score": round(median_s, 2),
                "min": round(float(sub.min()), 2),
                "max": round(float(sub.max()), 2)
            }
            print(f"Grade {g} (n={len(sub):4d}): Mean Project Score = {mean_s:5.1f} | Median = {median_s:5.1f} | Min = {sub.min():5.1f} | Max = {sub.max():5.1f}")

    # Top Disagreements (Outliers)
    v_df["rank_proj"] = v_df["project_score"].rank()
    v_df["rank_ns"] = (-v_df["nutri_score_2023_points"]).rank()
    v_df["rank_diff"] = (v_df["rank_proj"] - v_df["rank_ns"]).abs()

    top_disagreements = v_df.sort_values(by="rank_diff", ascending=False).head(10)
    disagreements_list = []
    print("\n--- Top 10 Scoring Disagreement Cases ---")
    for _, row in top_disagreements.iterrows():
        driver = []
        if row["product_type"] == "beverage":
            driver.append("Beverage strict scoring")
        if row["proteins"] > 10 and row["sat_fat"] > 5:
            driver.append("High protein balancing high fat in NS")
        if row["sodium"] > 0.5:
            driver.append("High sodium penalty in Project Score")
        driver_str = "; ".join(driver) if driver else "Differing parameter weighting"

        diag = {
            "code": row["code"],
            "product_name": row["product_name"],
            "category": row["category"],
            "project_score": row["project_score"],
            "ns_points": int(row["nutri_score_2023_points"]),
            "ns_grade": row["nutri_score_2023_grade"],
            "primary_driver": driver_str
        }
        disagreements_list.append(diag)
        print(f"[{row['code']}] {row['product_name'][:30]:30s} | Proj: {row['project_score']:5.1f} | NS: {row['nutri_score_2023_points']:2d} ({row['nutri_score_2023_grade']}) | Driver: {driver_str}")

    # Plots
    # 1. Scatter Plot with Trendline
    plt.figure(figsize=(9, 6))
    plt.scatter(v_df["nutri_score_2023_points"], v_df["project_score"], alpha=0.35, color="#2563eb", edgecolors="none", s=30)
    z = np.polyfit(v_df["nutri_score_2023_points"], v_df["project_score"], 1)
    p = np.poly1d(z)
    plt.plot(v_df["nutri_score_2023_points"], p(v_df["nutri_score_2023_points"]), "r--", linewidth=2, label=f"Trendline (Spearman r = {spearman_corr:.2f})")
    plt.title("Algorithm Validation: Project Score vs Official Nutri-Score 2023 Points", fontsize=13)
    plt.xlabel("Official Nutri-Score 2023 Points (Lower = Healthier)", fontsize=11)
    plt.ylabel("Project Score (0-100, Higher = Healthier)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=11)
    plt.tight_layout()
    scatter_path = os.path.join(evaluation_dir, "score_correlation.png")
    plt.savefig(scatter_path, dpi=200)
    plt.close()
    print(f"Saved correlation scatter plot to {scatter_path}")

    # 2. Boxplot of Project Score by Nutri-Score Grade
    plt.figure(figsize=(8, 5))
    box_data = [v_df[v_df["nutri_score_2023_grade"] == g]["project_score"].values for g in grade_order if len(v_df[v_df["nutri_score_2023_grade"] == g]) > 0]
    box_labels = [g for g in grade_order if len(v_df[v_df["nutri_score_2023_grade"] == g]) > 0]
    bplot = plt.boxplot(box_data, labels=box_labels, patch_artist=True, medianprops=dict(color="black", linewidth=1.5))
    colors = ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444"]
    for patch, color in zip(bplot["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    plt.title("Project Score Distribution Across Official Nutri-Score 2023 Grades", fontsize=13)
    plt.xlabel("Official Nutri-Score 2023 Grade", fontsize=11)
    plt.ylabel("Project Health Score (0 - 100)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    box_path = os.path.join(evaluation_dir, "grade_vs_project_score.png")
    plt.savefig(box_path, dpi=200)
    plt.close()
    print(f"Saved grade distribution plot to {box_path}")

    # Output JSON summary
    summary = {
        "validation_sample_size": len(v_df),
        "spearman_rank_correlation": round(spearman_corr, 4),
        "spearman_pvalue": float(sp_pvalue),
        "pearson_linear_correlation": round(pearson_corr, 4),
        "pearson_pvalue": float(pe_pvalue),
        "grade_summary": grade_summary,
        "top_disagreements": disagreements_list
    }
    summary_path = os.path.join(evaluation_dir, "validation_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved validation summary to {summary_path}")

    return summary

if __name__ == "__main__":
    validate_on_real_data()
