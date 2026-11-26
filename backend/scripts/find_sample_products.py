import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, Category

db = SessionLocal()
print("Products with barcode starting with '890' (India):")
for p in db.query(Product).filter(Product.barcode.startswith("890")).all():
    print(f"  {p.barcode} | {p.name} | {p.brand} | {p.category.name if p.category else 'N/A'} | Source: {p.source}")

db.close()
