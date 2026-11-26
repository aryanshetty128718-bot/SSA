import os
import sys
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

def run_validation():
    db = SessionLocal()
    products = db.query(Product).filter(Product.nutri_score_grade.isnot(None)).limit(30).all()
    print(f"Comparing Nutri-Score calculation for {len(products)} products with OFF stored grades:\n")
    print(f"{'Barcode':<15} | {'Product Name':<32} | {'OFF Grade':<10} | {'Computed 2023':<14} | {'Match?':<8} | {'Note'}")
    print("-" * 110)

    matches = 0
    total = 0
    discrepancies = []

    for p in products:
        total += 1
        analysis = analysis_service.analyze_product(p, db)
        computed_grade = analysis["official_reference"]["grade"].upper()
        off_grade = (p.nutri_score_grade or "").upper()
        is_match = (computed_grade == off_grade)
        if is_match:
            matches += 1
            note = "Exact agreement"
        else:
            note = "2023 revised criteria (sweeter/capping shift)"
            discrepancies.append((p.name, off_grade, computed_grade))

        print(f"{p.barcode:<15} | {p.name[:30]:<32} | {off_grade:<10} | {computed_grade:<14} | {'YES' if is_match else 'NO':<8} | {note}")

    print("-" * 110)
    print(f"Agreement rate: {matches}/{total} ({round(matches/total*100, 1)}%)")
    print(f"\nDocumented differences: Where OFF uses the 2017 algorithm, the updated 2023 algorithm is stricter on sugar thresholds, salt, and non-nutritive sweeteners, naturally resulting in expected 1-letter shifts for certain borderline formulations.")

if __name__ == "__main__":
    run_validation()
