import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.taxonomy import (
    PRODUCT_TYPES,
    PRODUCT_TYPE_BY_SLUG,
    PRODUCT_TYPE_BY_ID,
    map_product_to_type
)
from app.ml.loader import model_manager
from app.db.session import SessionLocal
from app.models import Product, ProductType
from app.services.recommendation_service import recommendation_service

client = TestClient(app)

def test_taxonomy_definitions():
    """Verify 45 product types are defined and cross-linked."""
    assert len(PRODUCT_TYPES) == 45
    for pt in PRODUCT_TYPES:
        assert pt["id"] > 0
        assert pt["slug"]
        assert pt["name"]
        assert pt["category_slug"]
        assert isinstance(pt["related"], list)

def test_map_product_to_type_by_tags():
    """Verify tag-based precedence in product type mapping."""
    pt = map_product_to_type(
        product_name="Generic Pasta",
        category_tags=["en:penne", "en:dried-pastas"],
        project_category_slug="instant-noodles-pasta"
    )
    assert pt["slug"] == "pasta"
    assert pt["name"] == "Dried Pasta"

def test_map_product_to_type_by_keywords():
    """Verify keyword heuristic fallback in product type mapping."""
    pt = map_product_to_type(
        product_name="Crunchy Roasted Peanut Butter",
        category_tags=[],
        project_category_slug="sweet-spreads-nut-butters"
    )
    assert pt["slug"] == "peanut-butter"

def test_model_a2_classification():
    """Verify Model A2 predicts valid product type for text + nutrients."""
    pred = model_manager.classify_product_type(
        product_name="Whole Grain Penne Rigate",
        brand="Barilla",
        nutriments={"carbohydrates_g": 70.0, "proteins_g": 12.0, "fiber_g": 6.0}
    )
    assert pred is not None
    assert pred["product_type_slug"] in PRODUCT_TYPE_BY_SLUG

def test_hybrid_recommendations_nutella():
    """Verify Nutella triggers Tier 2 related culinary alternatives with valid scores."""
    db = SessionLocal()
    try:
        res = recommendation_service.get_recommendations(db, barcode="3017620422003", limit=5)
        recs = res.get("recommendations", [])
        assert len(recs) > 0
        for r in recs:
            assert r["overall_score"] > 37.1
            assert r["tier_badge"] is not None
            assert "Related type" in r["tier_badge"] or "Same type" in r["tier_badge"]
            assert r["ingredient_similarity"] is not None
            assert r["nutrient_similarity"] is not None
    finally:
        db.close()

def test_hybrid_recommendations_pasta():
    """Verify Penne Rigate prefers Tier 1 same-type dried pasta alternatives."""
    db = SessionLocal()
    try:
        res = recommendation_service.get_recommendations(db, barcode="0011110849250", limit=5)
        recs = res.get("recommendations", [])
        assert len(recs) > 0
        for r in recs:
            assert "Same type: Dried Pasta" in r["tier_badge"]
            assert r["ingredient_similarity"] >= 0.0
    finally:
        db.close()

def test_manual_entry_validation():
    """Verify manual entry endpoint validates nutrition bounds (sugars <= carbs, sat fat <= fat)."""
    # 1. Invalid sugars > carbs
    invalid_payload = {
        "barcode": "8901058852431",
        "name": "Invalid Product",
        "category_id": 1,
        "energy_kcal": 200,
        "carbohydrates_g": 10.0,
        "sugars_g": 20.0,  # sugars > carbs
        "fat_g": 5.0,
        "saturated_fat_g": 2.0,
        "proteins_g": 5.0,
        "sodium_mg": 100.0
    }
    response = client.post("/api/v1/products/manual-entry", json=invalid_payload)
    assert response.status_code == 422

    # 2. Invalid saturated fat > total fat
    invalid_fat = {
        "barcode": "8901058852431",
        "name": "Invalid Fat Product",
        "category_id": 1,
        "energy_kcal": 200,
        "carbohydrates_g": 30.0,
        "sugars_g": 10.0,
        "fat_g": 5.0,
        "saturated_fat_g": 12.0,  # sat fat > fat
        "proteins_g": 5.0,
        "sodium_mg": 100.0
    }
    response2 = client.post("/api/v1/products/manual-entry", json=invalid_fat)
    assert response2.status_code == 422
