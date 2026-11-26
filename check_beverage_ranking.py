import sys
import logging
logging.disable(logging.INFO)

sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from app.models import Product
from app.services.analysis_service import analysis_service

def check_beverage_ranking():
    db = SessionLocal()
    barcodes = [
        ('Sparkling Mineral Spring Water', '8901058800081'),
        ('Diet Cola Zero Sugar Refresh', '8901058800074'),
        ('100% Pure Pressed Orange Juice', '8901058800111'),
        ('Mango Nectar Sweetened Fruit Drink', '8901058800128'),
        ('Classic Carbonated Cola Beverage', '8901058800067')
    ]

    header = f"{'Product Name':<36} | {'Project Score':<15} | {'Band':<15} | {'NS 2023 Grade':<15} | {'NS Points'}"
    print(header)
    print('-' * len(header))
    for name, bc in barcodes:
        p = db.query(Product).filter_by(barcode=bc).first()
        res = analysis_service.analyze_product(p, db)
        print(f"{name:<36} | {str(res['overall_project_score']):<15} | {res['score_band']:<15} | {res['official_reference']['grade']:<15} | {res['official_reference']['points']}")

if __name__ == '__main__':
    check_beverage_ranking()
