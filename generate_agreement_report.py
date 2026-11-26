import sys
import logging
logging.disable(logging.INFO)

sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

def generate_report():
    db = SessionLocal()
    products = db.query(Product).all()

    header = f"{'No':<3} | {'Barcode':<15} | {'Source':<12} | {'Product Name':<30} | {'Stored':<8} | {'My Grade':<15} | {'My Pts':<6} | {'Diff'}"
    print(header)
    print('-' * len(header))

    matches = 0
    total_compared = 0

    for idx, p in enumerate(products, 1):
        res = analysis_service.analyze_product(p, db)
        my_grade = res['official_reference']['grade']
        my_pts = str(res['official_reference']['points']) if res['official_reference']['points'] is not None else 'N/A'
        stored_grade = (p.nutri_score_grade or 'NONE').upper()
        
        if my_grade == 'NOT_COMPUTABLE':
            diff = 'Input Missing'
        elif stored_grade == 'NONE':
            diff = 'No Stored Grade'
        elif my_grade == stored_grade:
            diff = 'MATCH'
            matches += 1
            total_compared += 1
        else:
            diff = f'Shift ({stored_grade} -> {my_grade})'
            total_compared += 1
            
        print(f"{idx:<3} | {p.barcode:<15} | {p.source:<12} | {p.name[:28]:<30} | {stored_grade:<8} | {my_grade:<15} | {my_pts:<6} | {diff}")

    print('-' * len(header))
    print(f"Agreement on products with comparable grades: {matches}/{total_compared} ({round(matches/total_compared*100, 1)}%)")

if __name__ == '__main__':
    generate_report()
