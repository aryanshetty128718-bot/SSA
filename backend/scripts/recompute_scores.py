import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, ProductScore
from app.services.analysis_service import analysis_service

db = SessionLocal()
products = db.query(Product).all()
print(f"Recomputing scores under Version 1.1.0 for {len(products)} products...")

updated_count = 0
for p in products:
    try:
        analysis_service.analyze_product(p, db)
        updated_count += 1
    except Exception as e:
        pass

db.close()
print(f"Successfully recomputed and updated {updated_count} product scores.")
