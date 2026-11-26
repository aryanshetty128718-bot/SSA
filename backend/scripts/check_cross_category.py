import sys; sys.path.insert(0, 'backend')
from app.db.session import SessionLocal
from app.models import Product, Recommendation, Category
from app.services.recommendation_service import map_to_project_category

db = SessionLocal()
recs = db.query(Recommendation).all()
print(f"Total stored recommendation rows in DB: {len(recs)}")

cross_cat = []
for r in recs:
    q = db.query(Product).filter_by(id=r.target_product_id).first()
    c = db.query(Product).filter_by(id=r.alternative_product_id).first()
    if q and c:
        q_cat = map_to_project_category(q)
        c_cat = map_to_project_category(c)
        if q_cat != c_cat:
            cross_cat.append((q.barcode, q.name, q_cat, c.barcode, c.name, c_cat, r.similarity_score))

print(f"\nFound {len(cross_cat)} stored cross-category recommendations:")
for i, item in enumerate(cross_cat, 1):
    valid = (item[2] in ['soft-drinks-sodas', 'fruit-juices'] and item[5] in ['soft-drinks-sodas', 'fruit-juices'])
    status = "VALID (Beverage Coherence)" if valid else "INVALID (To Be Purged)"
    print(f"  {i:2d}. [{status}] {item[1]} ({item[2]}) -> {item[4]} ({item[5]}) | sim={item[6]:.4f}")

# Purge any invalid legacy cross-category pairings from DB
invalid_recs = []
for r in recs:
    q = db.query(Product).filter_by(id=r.target_product_id).first()
    c = db.query(Product).filter_by(id=r.alternative_product_id).first()
    if q and c:
        q_cat = map_to_project_category(q)
        c_cat = map_to_project_category(c)
        if q_cat != c_cat:
            is_valid = (q_cat in ['soft-drinks-sodas', 'fruit-juices'] and c_cat in ['soft-drinks-sodas', 'fruit-juices'])
            if not is_valid:
                db.delete(r)
                invalid_recs.append(r.id)

if invalid_recs:
    db.commit()
    print(f"\nPurged {len(invalid_recs)} invalid legacy cross-category recommendations from database.")
else:
    print("\nNo invalid cross-category recommendations to purge.")

db.close()
