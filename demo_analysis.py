import os
import sys
import json
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

def demo_product_analysis():
    db = SessionLocal()
    
    # 1. Nutella (Barcode: 3017620422003)
    nutella = db.query(Product).filter_by(barcode="3017620422003").first()
    # 2. A Soft Drink (e.g. Cola)
    cola = db.query(Product).filter(Product.name.ilike("%cola%")).first()
    # 3. A Breakfast Cereal (e.g. Oats or Corn Flakes)
    cereal = db.query(Product).filter(Product.name.ilike("%oats%") | Product.name.ilike("%muesli%")).first()
    # 4. Low data product (e.g. Missing nutrient product)
    low_data = db.query(Product).filter(Product.data_completeness_score < 0.70).first()

    targets = [
        ("Nutella Hazelnut Spread (Solid, High Sugar & Sat Fat)", nutella),
        ("Soft Drink (Beverage, Liquid Sugars)", cola),
        ("Breakfast Cereal / Oats (Solid, High Fiber)", cereal),
        ("Low-Data Product (Missing nutrients, Renormalization test)", low_data)
    ]

    for label, product in targets:
        print("\n" + "=" * 90)
        print(f"PRODUCT DEMO: {label}")
        print("=" * 90)
        if not product:
            print("Product not found in database.")
            continue
        
        analysis = analysis_service.analyze_product(product, db)
        print(f"Barcode: {analysis['barcode']} | Name: {analysis['product_name']} | Type: {analysis['product_type']}")
        print(f"Proposed Project Score (0-100): {analysis['overall_project_score']}/100 [{analysis['score_band']}]")
        print(f"Data Confidence: {analysis['confidence_score']*100}% ({analysis['confidence_level']}) | Missing: {analysis['missing_parameters']}")
        print(f"Official Reference (Nutri-Score 2023): Grade {analysis['official_reference']['grade']} ({analysis['official_reference']['points']} points)")
        
        print("\nSub-Scores & Effective Weights:")
        for k, v in analysis['sub_scores'].items():
            w = analysis['effective_weights'].get(k, 0.0)
            print(f"  - {k:<20}: Sub-score = {str(v):<6} | Weight = {w*100:.1f}%")
        
        print("\nEvidence-Backed Pros:")
        for pro in analysis['pros']:
            print(f"  + [{pro['parameter']}] {pro['title']}: {pro['evidence']}")
        if not analysis['pros']:
            print("  (None)")

        print("\nEvidence-Backed Cons:")
        for con in analysis['cons']:
            print(f"  - [{con['parameter']}] {con['title']}: {con['evidence']}")
        if not analysis['cons']:
            print("  (None)")

if __name__ == "__main__":
    demo_product_analysis()
