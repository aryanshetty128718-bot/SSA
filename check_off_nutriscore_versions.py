import sys
sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from app.models import Product
from app.services.off_client import off_client

db = SessionLocal()
products = db.query(Product).all()
off_prods = [p for p in products if p.source == 'openfoodfacts']
print(f"Total products in DB: {len(products)}")
print(f"OpenFoodFacts sourced products: {len(off_prods)}")

for p in off_prods:
    try:
        data = off_client.fetch_product(p.barcode)
        raw_p = data.get('product', {})
        ns_dict = raw_p.get('nutriscore', {})
        has_2023 = '2023' in ns_dict
        v23_grade = ns_dict.get('2023', {}).get('grade')
        print(f"Barcode: {p.barcode} | Name: {p.name[:25]} | nutriscore_2023: {has_2023} | 2023 Grade: {v23_grade} | Root Grade: {raw_p.get('nutriscore_grade')}")
    except Exception as e:
        print(f"Barcode: {p.barcode} | Error: {e}")
