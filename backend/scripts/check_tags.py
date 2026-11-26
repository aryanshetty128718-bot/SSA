import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import ProductCategoryTag, Product

db = SessionLocal()
tag_count = db.query(ProductCategoryTag).count()
print(f"ProductCategoryTag total count in DB: {tag_count}")

# Check Nutella tags
nutella = db.query(Product).filter(Product.barcode == "3017620422003").first()
if nutella:
    print("Nutella category:", nutella.category.name if nutella.category else None, "ID:", nutella.category_id)
    print("Nutella tags:", [t.tag for t in nutella.category_tags])

db.close()
