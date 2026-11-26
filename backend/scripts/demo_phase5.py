"""
Demo Script for Phase 5:
Demonstrates Healthier-Alternative Recommendations and Multi-Product Comparison
across:
1. Nutella (3017620422003 - Confectionary Spread)
2. Regular Cola (8901058800067 - Classic Carbonated Cola / 0000764001787 - Ryan's Lemonade)
3. Sugary Breakfast Cereal (8901058800036 - Sugar Frosted Flakes)
4. Biscuit & Cookies (8901058800203 - Double Cream Sandwich Biscuit / 0000168175589 - McVitie's)
5. Multi-Product Side-by-Side Comparison (POST /api/v1/compare)
"""

import sys
import json
import logging
from pathlib import Path

# Silence verbose SQL logs for clean demo output
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, Category
from app.services.recommendation_service import recommendation_service
from app.services.comparison_service import comparison_service
from app.schemas.comparison import ProductComparisonRequest

def print_banner(text: str):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def demo_recommendations(db, barcode: str, fallback_name: str, label: str):
    print_banner(f"DEMO RECOMMENDATIONS: {label}")
    
    prod = db.query(Product).filter(Product.barcode == barcode).first()
    if not prod and fallback_name:
        prod = db.query(Product).filter(Product.name.ilike(f"%{fallback_name}%")).first()

    if not prod:
        print(f"[-] Product '{barcode}' ({fallback_name}) not found in database.")
        return None

    print(f"[*] Query Product: {prod.name} | Brand: {prod.brand or 'N/A'}")
    print(f"    Barcode: {prod.barcode} | Category: {prod.category.name if prod.category else 'N/A'}")
    print(f"    Product Type: {prod.category.product_type if prod.category else 'N/A'} | Source: {prod.source}")
    
    score = prod.product_score
    overall = f"{score.overall_project_score:.1f}" if (score and score.overall_project_score) else "N/A"
    band = score.project_health_band if score else "N/A"
    grade = score.official_nutri_score_grade if score else "N/A"
    print(f"    Current Health Score: {overall}/100 ({band}) | Nutri-Score: {grade}")

    # Generate recommendations
    res = recommendation_service.find_alternatives(product=prod, db=db, limit=5)
    recs = res.get("recommendations", [])
    
    print(f"\n[+] Healthier Alternatives Found: {len(recs)}")
    if res.get("notes"):
        print(f"    Notice: {res.get('notes')}")
    print("-" * 80)
    for r in recs:
        print(f"  #{r['rank']} {r['name']} ({r.get('brand') or 'Brand N/A'}) [Barcode: {r['barcode']}]")
        print(f"     Health Score: {r['overall_score']:.1f}/100 ({r['score_band']}, Nutri-Score: {r.get('nutri_score_grade')})")
        print(f"     Model B Similarity: {r['similarity_score']:.2f} | Score Delta: {r['score_improvement']:+.1f} | Composite Rank: {r['composite_rank_score']:.4f}")
        print(f"     Explanation: {r['explanation']}")
        if r.get("trade_off_flags"):
            print(f"     [!] Trade-off Guard Flags: {', '.join(r['trade_off_flags'])}")
        print("-" * 80)

    return prod

def demo_comparison(db, barcodes):
    print_banner("DEMO MULTI-PRODUCT SIDE-BY-SIDE COMPARISON (/api/v1/compare)")
    req = ProductComparisonRequest(barcodes=barcodes)
    res = comparison_service.compare_products(request=req, db=db)

    print(f"Comparing {len(res.products)} Selected Products:")
    for p in res.products:
        print(f"  - {p.name} ({p.brand}) | Score: {p.overall_score:.1f} ({p.score_band}, NS: {p.nutri_score_grade}) | Barcode: {p.barcode}")

    print("\nPARAMETER COMPARISON MATRIX:")
    print(f"{'Parameter':<22} | " + " | ".join([f"{p.name[:16]:<16}" for p in res.products]) + " | Best Barcode")
    print("-" * 80)
    for m in res.comparison_matrix:
        row = f"{m.display_name:<22} | "
        vals = []
        for p in res.products:
            val = m.values.get(p.barcode)
            val_str = f"{val:.1f} {m.unit}" if val is not None else "N/A"
            vals.append(f"{val_str:<16}")
        row += " | ".join(vals)
        best_str = m.best_barcode or "Tie / None"
        row += f" | {best_str}"
        print(row)

    print("\nNUANCED SUMMARY VERDICT:")
    print(f"  {res.summary_verdict}")
    if res.data_confidence_notes:
        print("\nDATA CONFIDENCE / COMPATIBILITY NOTES:")
        for note in res.data_confidence_notes:
            print(f"  * {note}")

def main():
    db = SessionLocal()
    try:
        # 1. Nutella
        nutella = demo_recommendations(db, "3017620422003", "Nutella", "1. Nutella (Hazelnut Cocoa Spread)")

        # 2. Regular Cola
        cola = demo_recommendations(db, "8901058800067", "Classic Carbonated Cola", "2. Regular Cola (High Sugar Beverage)")

        # 3. Sugary Cereal
        cereal = demo_recommendations(db, "8901058800036", "Sugar Frosted Flakes", "3. Sugary Breakfast Cereal")

        # 4. Indian / Sweet Biscuit
        biscuit = demo_recommendations(db, "8901058800203", "Sandwich Biscuit", "4. Sandwich Biscuit / Cookies")

        # 5. Side-by-side comparison with 3 products (Cereal comparison)
        cereal_compare_barcodes = [
            "8901058800036",  # Sugar Frosted Flakes (Score ~45)
            "8901058800012",  # 100% Traditional Rolled Oats (Score ~92)
            "8901058800029"   # Crunchy Almond & Honey Granola (Score ~75)
        ]
        demo_comparison(db, cereal_compare_barcodes)

    finally:
        db.close()

if __name__ == "__main__":
    main()
