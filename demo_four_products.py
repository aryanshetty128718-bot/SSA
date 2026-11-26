import os
import sys
import logging

os.environ["SQLALCHEMY_WARN_20"] = "0"
logging.disable(logging.INFO)

sys.path.insert(0, "backend")
from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

def run_demo_four():
    db = SessionLocal()
    
    nutella = db.query(Product).filter_by(barcode="3017620422003").first()
    cola = db.query(Product).filter(Product.barcode == "8901058800067").first()
    oats = db.query(Product).filter(Product.barcode == "8901058800012").first()
    spaghetti = db.query(Product).filter(Product.barcode == "0012700158042").first()

    targets = [
        ("NUTELLA HAZELNUT SPREAD (Solid, High Sugar & Saturated Fat)", nutella),
        ("CLASSIC COLA BEVERAGE (Beverage, High Liquid Sugars)", cola),
        ("ROLLED OATS 100% WHOLEGRAIN (Solid, High Fiber & Whole Grains)", oats),
        ("SKINNER SPAGHETTI (Solid, Incomplete Label / Missing Data OFF Record)", spaghetti)
    ]

    for label, product in targets:
        print("\n" + "=" * 95)
        print(f"DEMO: {label}")
        print("=" * 95)
        if not product:
            print("Product not found.")
            continue
        
        analysis = analysis_service.analyze_product(product, db)
        print(f"Product Name: {analysis['product_name']} | Brand: {analysis['brand'] or 'N/A'}")
        print(f"Barcode: {analysis['barcode']} | Type: {analysis['product_type'].upper()}")
        print(f"Proposed Project Score (0-100): {analysis['overall_project_score']}/100 [{analysis['score_band']}] (Badge: {analysis['badge_color']})")
        print(f"Data Confidence: {analysis['confidence_score']*100:.1f}% ({analysis['confidence_level']}) | Missing: {analysis['missing_parameters']}")
        
        off_ref = analysis['official_reference']
        print(f"Official Reference Nutri-Score 2023: Grade {off_ref['grade']} ({off_ref['points']} pts if computed)")
        if off_ref['grade'] == 'NOT_COMPUTABLE':
            print(f"  * Nutri-Score Status Reason: {off_ref['breakdown'].get('reason')}")
            print(f"  * Missing Required Inputs: {off_ref['breakdown'].get('missing_inputs')}")

        print("\nComplete 8-Parameter Sub-Score & Effective Weights Breakdown:")
        print(f"{'Parameter':<22} | {'Sub-Score (0-100)':<18} | {'Effective Weight':<18} | {'Threshold Band'}")
        print("-" * 80)
        for pe in analysis['parameter_explanations']:
            score_display = f"{pe['sub_score']}/100" if pe['sub_score'] is not None else "EXCLUDED (NULL)"
            weight_display = f"{pe['effective_weight']*100:.1f}%"
            print(f"{pe['display_name']:<22} | {score_display:<18} | {weight_display:<18} | {pe['band']}")

        print("\nEvidence-Based Pros:")
        for pro in analysis['pros']:
            print(f"  + [{pro['parameter'].upper()}] {pro['title']}: {pro['evidence']}")
        if not analysis['pros']:
            print("  (None)")

        print("\nEvidence-Based Cons:")
        for con in analysis['cons']:
            print(f"  - [{con['parameter'].upper()}] {con['title']}: {con['evidence']}")
        if not analysis['cons']:
            print("  (None)")

if __name__ == "__main__":
    run_demo_four()
