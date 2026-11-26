import os
import sys

# Suppress engine logging before imports
os.environ["SQLALCHEMY_WARN_20"] = "0"
import logging
logging.disable(logging.INFO)

sys.path.insert(0, "backend")
from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

db = SessionLocal()
prods = [
    ("NUTELLA", db.query(Product).filter_by(barcode="3017620422003").first()),
    ("SOFT DRINK", db.query(Product).filter(Product.name.ilike("%cola%")).first()),
    ("BREAKFAST CEREAL", db.query(Product).filter(Product.name.ilike("%oats%")).first()),
    ("LOW-DATA ARTISAN", db.query(Product).filter(Product.data_completeness_score < 0.70).first())
]

for label, p in prods:
    a = analysis_service.analyze_product(p, db)
    print(f"=== {label}: {a['product_name']} ({a['barcode']}) ===")
    print(f"Type: {a['product_type'].upper()}")
    print(f"Proposed Project Score: {a['overall_project_score']}/100 [{a['score_band']}] (Badge: {a['badge_color']})")
    print(f"Data Confidence: {a['confidence_score']*100:.1f}% ({a['confidence_level']}) | Excluded/Missing: {a['missing_parameters']}")
    print(f"Official Reference Nutri-Score 2023: Grade {a['official_reference']['grade']} ({a['official_reference']['points']} pts)")
    print("Sub-scores:")
    for k, v in a['sub_scores'].items():
        w = a['effective_weights'].get(k, 0.0)
        score_str = f"{v}/100" if v is not None else "EXCLUDED (NULL)"
        print(f"  - {k:<20}: {score_str:<16} (Renormalized Weight: {w*100:.1f}%)")
    print("Pros:")
    for pro in a['pros']:
        print(f"  + [{pro['parameter'].upper()}] {pro['title']}: {pro['evidence']}")
    if not a['pros']:
        print("  (None)")
    print("Cons:")
    for con in a['cons']:
        print(f"  - [{con['parameter'].upper()}] {con['title']}: {con['evidence']}")
    if not a['cons']:
        print("  (None)")
    print()
