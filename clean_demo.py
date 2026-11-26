import os
import sys
import logging
from pathlib import Path

# Suppress SQLAlchemy engine echo for clean CLI report
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

def demo_clean():
    db = SessionLocal()
    
    nutella = db.query(Product).filter_by(barcode="3017620422003").first()
    cola = db.query(Product).filter(Product.name.ilike("%cola%")).first()
    cereal = db.query(Product).filter(Product.name.ilike("%oats%") | Product.name.ilike("%muesli%")).first()
    low_data = db.query(Product).filter(Product.data_completeness_score < 0.70).first()

    targets = [
        ("1. NUTELLA HAZELNUT SPREAD (Solid, High Sugar & Saturated Fat)", nutella),
        ("2. SOFT DRINK (Beverage, Liquid Sugars)", cola),
        ("3. BREAKFAST CEREAL / OATS (Solid, High Fiber & Whole Grains)", cereal),
        ("4. LOW-DATA ARTISAN PRODUCT (Missing Nutrients, Weight Renormalization Test)", low_data)
    ]

    for label, product in targets:
        print("\n" + "=" * 85)
        print(f"{label}")
        print("=" * 85)
        if not product:
            print("Product not found.")
            continue
        
        analysis = analysis_service.analyze_product(product, db)
        print(f"Product Name: {analysis['product_name']} (Brand: {analysis['brand'] or 'N/A'})")
        print(f"Barcode: {analysis['barcode']} | Form: {analysis['product_type'].upper()}")
        print(f"Proposed Project Score: {analysis['overall_project_score']}/100 [{analysis['score_band']}] (Badge: {analysis['badge_color']})")
        print(f"Data Confidence: {analysis['confidence_score']*100:.1f}% ({analysis['confidence_level']}) | Excluded/Missing: {analysis['missing_parameters']}")
        print(f"Official Reference (Nutri-Score 2023): Grade {analysis['official_reference']['grade']} ({analysis['official_reference']['points']} pts)")
        
        print("\nGranular Sub-Scores & Renormalized Weights:")
        for k, v in analysis['sub_scores'].items():
            w = analysis['effective_weights'].get(k, 0.0)
            score_str = f"{v}/100" if v is not None else "EXCLUDED (NULL)"
            print(f"  * {k:<20}: Sub-score = {score_str:<16} | Renormalized Weight = {w*100:.1f}%")
        
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
    demo_clean()
