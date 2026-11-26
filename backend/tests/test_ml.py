import pytest
from app.api.v1.ml import classify_product, find_similar_products, get_model_info
from app.schemas.ml import ClassificationRequest, SimilarityRequest
from app.ml.loader import ModelManager, model_manager

def test_ml_model_info():
    """Verifies get_model_info returns metadata for trained models."""
    data = get_model_info()
    assert "classifier" in data
    assert "similarity_engine" in data
    assert data["classifier"]["loaded"] is True
    assert data["similarity_engine"]["loaded"] is True

    # Check classifier performance metrics in metadata
    meta = data["classifier"]["metadata"]
    assert meta["model_type"] in ["LinearSVM", "LogisticRegression", "RandomForest"]
    assert meta["test_metrics"]["accuracy"] >= 0.85
    assert meta["test_metrics"]["macro_f1"] >= 0.85

def test_ml_classify_real_cereal():
    """Verifies classify_product performs real ML inference and returns correct schema."""
    req = ClassificationRequest(
        product_name="Kellogg's Crunchy Granola with Almonds",
        brand="Kellogg's",
        ingredients_text="Rolled oats, whole grain wheat, sugar, almonds, sunflower oil, honey",
        nutriments={
            "energy-kcal_100g": 450.0,
            "sugars_100g": 18.0,
            "fat_100g": 15.0,
            "saturated-fat_100g": 2.5,
            "sodium_100g": 0.2,
            "proteins_100g": 9.0,
            "fiber_100g": 6.5
        }
    )
    res = classify_product(req)
    assert res["model_type"] == "ML prediction"
    assert res["predicted_category"] == "breakfast-cereals"
    assert 0.0 <= res["confidence"] <= 1.0
    assert len(res["probabilities"]) > 0
    assert "text_features" in res["features_used"]

def test_ml_classify_beverage():
    """Verifies soft drink classification."""
    req = ClassificationRequest(
        product_name="Coca-Cola Zero Sugar Soda",
        brand="Coca-Cola",
        ingredients_text="Carbonated water, caramel color, phosphoric acid, aspartame, potassium benzoate",
        nutriments={
            "energy-kcal_100g": 0.3,
            "sugars_100g": 0.0,
            "fat_100g": 0.0,
            "sodium_100g": 0.01,
            "proteins_100g": 0.0
        }
    )
    res = classify_product(req)
    assert res["model_type"] == "ML prediction"
    assert res["predicted_category"] == "soft-drinks-sodas"
    assert res["confidence"] > 0.5

def test_ml_similar_retrieval():
    """Verifies find_similar_products retrieves multimodal nearest neighbors."""
    req = SimilarityRequest(
        product_name="Dark Chocolate 70%",
        brand="Lindt",
        ingredients_text="Cocoa mass, sugar, cocoa butter, vanilla",
        nutriments={
            "energy-kcal_100g": 560.0,
            "sugars_100g": 29.0,
            "fat_100g": 41.0,
            "saturated-fat_100g": 24.0,
            "sodium_100g": 0.02,
            "proteins_100g": 8.0,
            "fiber_100g": 11.0
        },
        category_filter="chocolates-confectionery",
        top_k=3
    )
    res = find_similar_products(req)
    assert len(res) <= 3
    if len(res) > 0:
        p0 = res[0]
        assert p0["rank"] == 1
        assert "code" in p0
        assert "hybrid_similarity" in p0
        assert "text_similarity" in p0
        assert "nutrient_similarity" in p0
        assert p0["category"] == "chocolates-confectionery"
        assert p0["model_type"] == "ML prediction"

def test_ml_heuristic_fallback_when_unloaded(monkeypatch):
    """Verifies graceful degradation to heuristic rules when ML model is absent."""
    manager = ModelManager()
    monkeypatch.setattr(manager, "classifier", None)

    res = manager.classify(
        product_name="Classic Whole Wheat Bread Loaf",
        brand="Modern",
        ingredients_text="Wheat flour, yeast, salt, water"
    )
    assert res["model_type"] == "heuristic fallback"
    assert res["predicted_category"] == "breads-bakery"
    assert res["confidence"] == 0.60
