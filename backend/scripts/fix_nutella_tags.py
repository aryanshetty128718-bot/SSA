import sys
import json
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, ProductCategoryTag, Category

db = SessionLocal()
nutella = db.query(Product).filter(Product.barcode == "3017620422003").first()
if nutella and not nutella.category_tags:
    print("Populating category tags for Nutella...")
    tags = [
        "en:spreads",
        "en:sweet-spreads",
        "en:hazelnut-spreads",
        "en:chocolate-spreads",
        "en:cocoa-and-hazelnuts-spreads"
    ]
    for depth, tag in enumerate(tags):
        ct = ProductCategoryTag(
            product_id=nutella.id,
            tag=tag,
            depth=depth
        )
        db.add(ct)
    
    # Also link Nutella's category to Chocolates & Confectionery or ensure category exists
    choc_cat = db.query(Category).filter_by(slug="chocolates-confectionery").first()
    if choc_cat:
        print(f"Chocolates & Confectionery category id: {choc_cat.id}")

    db.commit()
    print("Done populating Nutella tags.")

# Check how many products in DB share any of Nutella's tags
shared = db.query(ProductCategoryTag).filter(ProductCategoryTag.tag.in_([
    "en:spreads", "en:sweet-spreads", "en:chocolate-spreads", "en:cocoa-and-hazelnuts-spreads"
])).all()
print(f"Products in DB sharing spread/chocolate tags: {len(shared)}")
for s in shared[:5]:
    p = db.query(Product).filter_by(id=s.product_id).first()
    if p:
        print(f"  {p.barcode} | {p.name} | Tag: {s.tag} | Cat: {p.category.name if p.category else 'N/A'}")

db.close()
