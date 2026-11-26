"""
Demonstration runner for Phase 5 recommendations and multi-product comparison.
Runs:
1. Nutella (3017620422003)
2. Coca-Cola Original Taste (5449000000439)
3. Sugary Cereal (e.g. Sugar Frosted Flakes 0038000318214 or imported sweet cereal)
4. Britannia Indian Biscuit (Britannia Bourbon 8901063139329 or Marie Gold 8901063162914)
"""

import sys
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal
from app.models import Product
from app.services.recommendation_service import recommendation_service
from app.services.comparison_service import comparison_service

def demo_product(barcode, label, db):
    print(f"\n{'='*70}")
    print(f"DEMO: {label} (Barcode: {barcode})")
    print(f"{'='*70}")
    prod = db.query(Product).filter(Product.barcode == barcode).first()
    if not prod:
        print(f"Product with barcode {barcode} not found in database!")
        return

    res = recommendation_service.find_alternatives(product=prod, db=db, limit=5)
    q = res["query_product"]
    print(f"Query Product: {q['name']} ({q['brand']})")
    print(f"Project Category: {q['project_category']} | Type: {q['product_type']}")
    print(f"Health Score: {q['overall_score']:.1f} ({q['score_band']}) | Nutri-Score: {q['nutri_score_grade']}")
    print(f"Key Nutrients: {q['key_nutrients']}")
    print(f"\nRecommendations Found ({len(res['recommendations'])}):")
    if res.get("notes"):
        print(f"Note: {res['notes']}")

    for r in res["recommendations"]:
        print(f"\n  Rank #{r['rank']}: {r['name']} ({r['brand']})")
        print(f"  Category: {r['category_name']} (Project: {r['project_category']})")
        print(f"  Overall Score: {r['overall_score']:.1f} ({r['score_band']}) | Nutri-Score: {r['nutri_score_grade']}")
        print(f"  Health Improvement: +{r['score_improvement']:.1f}")
        print(f"  Similarity Breakdown: Hybrid={r['similarity_score']:.4f} (Text={r['text_similarity']:.4f}, Nutrient={r['nutrient_similarity']:.4f})")
        print(f"  Composite Rank Score: {r['composite_rank_score']:.4f}")
        print(f"  Trade-off Flags: {r['trade_off_flags'] if r['trade_off_flags'] else 'None'}")
        print(f"  Explanation: {r['explanation']}")

def main():
    db = SessionLocal()
    # 1. Nutella
    demo_product("3017620422003", "1. Nutella Hazelnut Spread", db)
    # 2. Coca-Cola
    demo_product("5449000000439", "2. Coca-Cola Original Taste", db)
    # 3. Cereal (Frosted Flakes or Chocapic or Honey Nut)
    cereal = db.query(Product).filter(Product.barcode == "0038000318214").first()
    if cereal:
        demo_product("0038000318214", "3. Kellogg's Frosted Flakes", db)
    else:
        # find any cereal with high sugar
        c_prod = db.query(Product).filter(Product.category.has(slug="breakfast-cereals")).first()
        if c_prod:
            demo_product(c_prod.barcode, f"3. Cereal: {c_prod.name}", db)
    # 4. Britannia Biscuit
    bb = db.query(Product).filter(Product.barcode == "8901063139329").first()
    if bb:
        demo_product("8901063139329", "4. Britannia Bourbon Chocolate Cream Biscuit", db)
    else:
        mg = db.query(Product).filter(Product.barcode == "8901063162914").first()
        if mg:
            demo_product("8901063162914", "4. Britannia Marie Gold Biscuit", db)
    db.close()

if __name__ == "__main__":
    main()
