import sys
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.score import ProductScore
from app.services.analysis_service import AnalysisService

def rescore_catalog():
    db = SessionLocal()
    analysis_svc = AnalysisService()
    try:
        before_count = db.query(ProductScore).count()
        total_products = db.query(Product).count()
        print(f"--- Starting Full Catalog Re-scoring ---")
        print(f"Products in DB: {total_products}")
        print(f"Scores currently in DB: {before_count}")

        t0 = time.time()
        success = 0
        failures = 0

        # Iterate in batches
        products = db.query(Product).all()
        for idx, prod in enumerate(products, 1):
            try:
                analysis_svc.analyze_product(prod, db)
                success += 1
            except Exception as e:
                failures += 1
                print(f"Error re-scoring product {prod.barcode} (id={prod.id}): {e}")

            if idx % 500 == 0 or idx == len(products):
                print(f"  Processed {idx}/{len(products)} products...")

        after_count = db.query(ProductScore).count()
        duration = time.time() - t0

        print(f"\n--- Re-scoring Run Complete ---")
        print(f"Before score count: {before_count}")
        print(f"After score count:  {after_count}")
        print(f"Successful:         {success}")
        print(f"Failures:           {failures}")
        print(f"Total duration:     {duration:.2f} seconds ({duration/len(products)*1000:.1f} ms/product)")
    finally:
        db.close()

if __name__ == "__main__":
    rescore_catalog()
