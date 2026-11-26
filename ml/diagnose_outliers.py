import os
import sys
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from app.scoring.calculator import compute_product_analysis

BEVERAGE_CATEGORIES = {"soft-drinks-sodas", "fruit-juices", "dairy-plant-drinks"}

df = pd.read_csv("ml/data/processed/products_cleaned.csv")
core_nutrients = ["energy_kcal_100g", "sugars_100g", "saturated_fat_100g", "sodium_100g", "proteins_100g", "fiber_100g"]
complete_df = df.dropna(subset=core_nutrients).copy()

records = []
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
    analysis = compute_product_analysis(prod_type, nutriments, [], nova_group=nova)
    proj_score = analysis.get("overall_score")
    ns_ref = analysis.get("official_reference", {})
    ns_pts = ns_ref.get("points")
    ns_grade = ns_ref.get("grade")
    if proj_score is not None and ns_pts is not None and ns_grade not in ("NOT_COMPUTABLE", None):
        records.append({
            "code": str(row["code"]),
            "product_name": str(row["product_name"]),
            "brand": str(row["brand"]),
            "category": cat,
            "product_type": prod_type,
            "project_score": proj_score,
            "ns_points": ns_pts,
            "ns_grade": ns_grade,
            "sub_scores": analysis["sub_scores"],
            "effective_weights": analysis["effective_weights"],
            "energy_kcal": nutriments["energy_kcal"],
            "sugars_g": nutriments["sugars_g"],
            "sat_fat_g": nutriments["saturated_fat_g"],
            "sodium_mg": nutriments["sodium_mg"],
            "proteins_g": nutriments["proteins_g"],
            "fiber_g": nutriments["fiber_g"]
        })

v_df = pd.DataFrame(records)

print("=== Top 10 Grade E Products with Highest Project Score ===")
top_e = v_df[v_df["ns_grade"] == "E"].sort_values(by="project_score", ascending=False).head(10)
for idx, r in top_e.iterrows():
    print(f"[{r['code']}] {r['product_name'][:30]:30s} | Brand: {r['brand'][:15]:15s} | Cat: {r['category'][:15]:15s} | Type: {r['product_type']} | Proj: {r['project_score']:.1f} | NS: {r['ns_points']} (E)")
    print(f"    Nutr: Sug={r['sugars_g']}g, SatFat={r['sat_fat_g']}g, Sod={r['sodium_mg']}mg, E={r['energy_kcal']}kcal, Fib={r['fiber_g']}g, Prot={r['proteins_g']}g")
    print(f"    Sub-scores: {r['sub_scores']}")

print("\n=== Top 10 Grade A/B Products with Lowest Project Score ===")
low_ab = v_df[v_df["ns_grade"].isin(["A", "B"])].sort_values(by="project_score", ascending=True).head(10)
for idx, r in low_ab.iterrows():
    print(f"[{r['code']}] {r['product_name'][:30]:30s} | Brand: {r['brand'][:15]:15s} | Cat: {r['category'][:15]:15s} | Type: {r['product_type']} | Proj: {r['project_score']:.1f} | NS: {r['ns_points']} ({r['ns_grade']})")
    print(f"    Nutr: Sug={r['sugars_g']}g, SatFat={r['sat_fat_g']}g, Sod={r['sodium_mg']}mg, E={r['energy_kcal']}kcal, Fib={r['fiber_g']}g, Prot={r['proteins_g']}g")
    print(f"    Sub-scores: {r['sub_scores']}")
