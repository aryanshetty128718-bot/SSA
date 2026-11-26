import pytest
from app.main import root_endpoint
from app.api.v1.health import get_health_status
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import (
    User, Category, Product, NutritionalInformation,
    Ingredient, ProductIngredient, ScoringCriteria
)

def test_root_endpoint():
    data = root_endpoint()
    assert "Welcome to the" in data["message"]
    assert data["health_check"] == "/api/v1/health"
    assert data["documentation"] == "/docs"

def test_health_endpoint():
    db = SessionLocal()
    try:
        health = get_health_status(db=db)
        assert health.status == "healthy"
        assert health.database_connected is True
        assert health.app_name == settings.APP_NAME
        assert health.version == "1.0.0"
    finally:
        db.close()

def test_database_counts():
    db = SessionLocal()
    try:
        # 1. Check users
        user_count = db.query(User).count()
        assert user_count >= 2, f"Expected at least 2 users, found {user_count}"

        # 2. Check categories (at least 10 expected)
        cat_count = db.query(Category).count()
        assert cat_count >= 10, f"Expected >= 10 categories, found {cat_count}"

        # 3. Check scoring criteria (15 expected)
        crit_count = db.query(ScoringCriteria).count()
        assert crit_count >= 15, f"Expected >= 15 criteria, found {crit_count}"

        # 4. Check products (at least 40 expected)
        prod_count = db.query(Product).count()
        assert prod_count >= 40, f"Expected >= 40 products, found {prod_count}"

        # 5. Check nutrition records
        nut_count = db.query(NutritionalInformation).count()
        assert nut_count >= 40, f"Expected >= 40 nutrition records, found {nut_count}"

        # 6. Check ingredients
        ing_count = db.query(Ingredient).count()
        assert ing_count >= 20, f"Expected >= 20 ingredients, found {ing_count}"

        # 7. Check product-ingredient associations
        pi_count = db.query(ProductIngredient).count()
        assert pi_count >= 80, f"Expected >= 80 product ingredients, found {pi_count}"

        # 8. Verify missing-data handling (strictly None, not 0)
        incomplete_products = db.query(NutritionalInformation).filter(
            (NutritionalInformation.saturated_fat_g.is_(None)) |
            (NutritionalInformation.fiber_g.is_(None)) |
            (NutritionalInformation.sugars_g.is_(None))
        ).all()
        assert len(incomplete_products) > 0, "Expected some products to have None for missing nutrient fields"

        # Check a specific product with missing value
        bread_bun = db.query(Product).filter(Product.name.like("%Sweet Fruit%")).first()
        assert bread_bun is not None
        assert bread_bun.nutrition.saturated_fat_g is None, "Expected saturated_fat_g to be None for Sweet Fruit Buns"
        assert bread_bun.data_completeness_score == 0.85

    finally:
        db.close()
