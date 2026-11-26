import sys
import json
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models import Product, ScoringCriteria

db = SessionLocal()
cola = db.query(Product).filter(Product.barcode == "8901058800067").first()
if cola and cola.product_score:
    print(f"Cola Score: {cola.product_score.overall_project_score}")
    print(f"Scoring Engine Version: {cola.product_score.scoring_engine_version}")
    print(f"Sub-scores JSON: {cola.product_score.sub_scores_json}")
    print(f"Nutrition: Sugar={cola.nutrition.sugars_g}, Energy={cola.nutrition.energy_kcal}, Sodium={cola.nutrition.sodium_mg}")

flakes = db.query(Product).filter(Product.barcode == "8901058800036").first()
if flakes and flakes.product_score:
    print(f"\nFlakes Score: {flakes.product_score.overall_project_score}")
    print(f"Sub-scores JSON: {flakes.product_score.sub_scores_json}")
    print(f"Nutrition: Sugar={flakes.nutrition.sugars_g}, Fat={flakes.nutrition.fat_g}, SatFat={flakes.nutrition.saturated_fat_g}, Sodium={flakes.nutrition.sodium_mg}, Fiber={flakes.nutrition.fiber_g}, Protein={flakes.nutrition.proteins_g}")

# Check DB criteria for beverages
crit = db.query(ScoringCriteria).filter(ScoringCriteria.product_type == "beverage").all()
print("\nBeverage Criteria in DB:")
for c in crit:
    print(f"  {c.parameter_name}: weight={c.weight}, low={c.low_threshold}, high={c.high_threshold}")

db.close()
