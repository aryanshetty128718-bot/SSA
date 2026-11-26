import pytest
from unittest.mock import patch
from app.api.v1.products import get_product_by_barcode, search_products
from app.core.exceptions import (
    BarcodeValidationError,
    ProductNotFoundError,
    ExternalAPIUnavailableError,
    InsufficientDataError
)
from app.db.session import SessionLocal
from app.models import Product, NutritionalInformation, Category, Ingredient, ProductIngredient, SearchHistory

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- 1. Local Database & Barcode Validation Tests -----------------

def test_local_barcode_cache_hit(db_session):
    """Test lookup of an existing seeded barcode hits the local DB directly without OFF."""
    seeded_product = db_session.query(Product).filter_by(source="seed").first()
    assert seeded_product is not None
    seeded_barcode = seeded_product.barcode

    result = get_product_by_barcode(barcode=seeded_barcode, db=db_session)
    
    assert result["barcode"] == seeded_barcode
    assert result["name"] == seeded_product.name
    assert result["source"] == "seed"
    assert result["nutrition"].basis in ("per 100g", "per 100ml")
    
    # Check that search history recorded a local_hit
    hist = db_session.query(SearchHistory).filter(SearchHistory.query_term.like(f"%{seeded_barcode}%")).order_by(SearchHistory.searched_at.desc()).first()
    assert hist is not None
    assert "local_hit" in hist.query_term

def test_invalid_barcode_raises_422(db_session):
    """Invalid barcodes must raise BarcodeValidationError (422)."""
    # Non-numeric
    with pytest.raises(BarcodeValidationError) as exc:
        get_product_by_barcode(barcode="890105880001A", db=db_session)
    assert "non-numeric" in str(exc.value.message)

    # Invalid check digit
    with pytest.raises(BarcodeValidationError) as exc:
        get_product_by_barcode(barcode="8901058800019", db=db_session)  # Real check digit for 890105880001 is 2
    assert "Invalid check digit" in str(exc.value.message)

# ----------------- 2. Mocked Open Food Facts Tests -----------------

def test_off_mocked_success_solid(db_session):
    """Test successful OFF response for a solid food: caches product, nutrition, and ingredients."""
    test_barcode = "9990000000012"
    
    mock_payload = {
        "status": 1,
        "code": test_barcode,
        "product": {
            "code": test_barcode,
            "product_name": "Organic Spelt Wholegrain Crackers",
            "brands": "BioSnack",
            "categories_tags": ["en:plant-based-foods-and-beverages", "en:snacks", "en:crackers"],
            "nova_group": 3,
            "nutriscore_grade": "b",
            "serving_size": "30g",
            "nutriments": {
                "energy-kcal_100g": 410.0,
                "fat_100g": 12.0,
                "saturated-fat_100g": 1.5,
                "carbohydrates_100g": 62.0,
                "sugars_100g": 4.5,
                "fiber_100g": 7.8,
                "proteins_100g": 11.2,
                "salt_100g": 1.2
            },
            "ingredients": [
                {"text": "Whole Spelt Flour", "position": 1, "percent": 75.0},
                {"text": "Sunflower Oil", "position": 2, "percent": 12.0},
                {"text": "Sea Salt", "position": 3, "percent": 1.2}
            ]
        }
    }

    # Delete existing test product if present from previous run
    existing = db_session.query(Product).filter_by(barcode=test_barcode).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    try:
        with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", return_value=mock_payload):
            result = get_product_by_barcode(barcode=test_barcode, db=db_session)

        assert result["barcode"] == test_barcode
        assert result["name"] == "Organic Spelt Wholegrain Crackers"
        assert result["brand"] == "BioSnack"
        assert result["source"] == "openfoodfacts"
        assert result["nova_group"] == 3
        assert result["nutri_score_grade"] == "B"
        assert result["nutrition"].energy_kcal == 410.0
        assert result["nutrition"].sodium_mg == 480.0  # Derived from salt: 1.2 / 2.5 * 1000
        assert result["nutrition"].basis == "per 100g"
        assert result["data_completeness_score"] == 1.0
        assert len(result["ingredients"]) == 3
        assert result["ingredients"][0].ingredient_name == "Whole Spelt Flour"
        assert result["ingredients"][0].position_order == 1
    finally:
        p = db_session.query(Product).filter_by(barcode=test_barcode).first()
        if p:
            db_session.delete(p)
            db_session.commit()

def test_off_mocked_beverage_detection(db_session):
    """Test that OFF category tags with beverage keywords correctly detect product_type='beverage'."""
    test_barcode = "9990000000029"
    
    mock_payload = {
        "status": 1,
        "code": test_barcode,
        "product": {
            "code": test_barcode,
            "product_name": "Zero Sugar Sparkling Green Tea",
            "brands": "TeaZen",
            "categories_tags": ["en:beverages", "en:teas", "en:iced-teas"],
            "nova_group": 2,
            "nutriscore_grade": "b",
            "serving_size": "250ml",
            "nutriments": {
                "energy-kj_100g": 12.0,  # Only kJ provided
                "fat_100g": 0.0,
                "saturated-fat_100g": 0.0,
                "carbohydrates_100g": 0.2,
                "sugars_100g": 0.1,
                "proteins_100g": 0.1,
                "salt_100g": 0.02
            },
            "ingredients": [
                {"text": "Brewed Green Tea", "position": 1},
                {"text": "Citric Acid", "position": 2, "id": "en:e330"}
            ]
        }
    }

    existing = db_session.query(Product).filter_by(barcode=test_barcode).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    try:
        with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", return_value=mock_payload):
            result = get_product_by_barcode(barcode=test_barcode, db=db_session)

        assert result["barcode"] == test_barcode
        assert result["nutrition"].basis == "per 100ml"  # Verified beverage basis
        assert result["nutrition"].energy_kcal == 2.9     # Converted 12 kJ -> 2.9 kcal
        assert result["category"].product_type == "beverage"
    finally:
        p = db_session.query(Product).filter_by(barcode=test_barcode).first()
        if p:
            db_session.delete(p)
            db_session.commit()

def test_off_mocked_404_not_found(db_session):
    """When OFF returns status 0 / not found, ProductNotFoundError (404) must be raised."""
    unknown_barcode = "8901058899993"
    
    with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", side_effect=ProductNotFoundError(unknown_barcode)):
        with pytest.raises(ProductNotFoundError):
            get_product_by_barcode(barcode=unknown_barcode, db=db_session)

    hist = db_session.query(SearchHistory).filter(SearchHistory.query_term.like(f"%{unknown_barcode}%")).order_by(SearchHistory.searched_at.desc()).first()
    assert hist is not None
    assert "not_found" in hist.query_term

def test_off_mocked_timeout_503(db_session):
    """When OFF times out, ExternalAPIUnavailableError (503) must be raised."""
    test_barcode = "8901058899986"
    
    with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", side_effect=ExternalAPIUnavailableError("Open Food Facts", detail="Timeout")):
        with pytest.raises(ExternalAPIUnavailableError):
            get_product_by_barcode(barcode=test_barcode, db=db_session)

    hist = db_session.query(SearchHistory).filter(SearchHistory.query_term.like(f"%{test_barcode}%")).order_by(SearchHistory.searched_at.desc()).first()
    assert hist is not None
    assert "error" in hist.query_term

def test_off_mocked_partial_nutrition_missing_data(db_session):
    """Test partial nutrition: missing values must be None (never 0), and completeness < 1.0."""
    test_barcode = "9990000000036"
    
    mock_payload = {
        "status": 1,
        "code": test_barcode,
        "product": {
            "code": test_barcode,
            "product_name": "Artisan Fruit Bar",
            "brands": "RawBite",
            "categories_tags": ["en:plant-based-foods", "en:snacks"],
            "nutriments": {
                "energy-kcal_100g": 380.0,
                "carbohydrates_100g": 65.0,
                "sugars_100g": 45.0,
                "proteins_100g": 6.0
                # saturated-fat, sodium, fiber intentionally omitted by label
            }
        }
    }

    existing = db_session.query(Product).filter_by(barcode=test_barcode).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    try:
        with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", return_value=mock_payload):
            result = get_product_by_barcode(barcode=test_barcode, db=db_session)

        assert result["nutrition"].saturated_fat_g is None, "Missing saturated_fat must be None, not 0"
        assert result["nutrition"].sodium_mg is None, "Missing sodium must be None, not 0"
        assert result["nutrition"].fiber_g is None, "Missing fiber must be None, not 0"
        assert result["data_completeness_score"] == 0.50  # 3 of 6 core parameters present
        assert result["data_completeness_warning"] is True
    finally:
        p = db_session.query(Product).filter_by(barcode=test_barcode).first()
        if p:
            db_session.delete(p)
            db_session.commit()

def test_off_mocked_incomplete_reject(db_session):
    """Records with missing name or zero usable nutrition must be rejected with InsufficientDataError."""
    test_barcode = "8901058899979"
    
    # Missing name
    mock_no_name = {
        "status": 1,
        "product": {
            "code": test_barcode,
            "product_name": "",
            "nutriments": {"energy-kcal": 200}
        }
    }
    with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", return_value=mock_no_name):
        with pytest.raises(InsufficientDataError) as exc:
            get_product_by_barcode(barcode=test_barcode, db=db_session)
        assert "Missing product name" in str(exc.value.message)

    # Zero usable nutrition
    mock_no_nutrition = {
        "status": 1,
        "product": {
            "code": test_barcode,
            "product_name": "Mystery Powder",
            "nutriments": {}
        }
    }
    with patch("app.services.off_client.OpenFoodFactsClient.fetch_product", return_value=mock_no_nutrition):
        with pytest.raises(InsufficientDataError) as exc:
            get_product_by_barcode(barcode=test_barcode, db=db_session)
        assert "no usable nutritional data" in str(exc.value.message)

def test_product_search_text(db_session):
    """Test product text search endpoint searches local database by name/brand."""
    results = search_products(q="oats", limit=10, db=db_session)
    assert len(results) >= 1
    assert any("oats" in p.name.lower() for p in results)

    # Empty search
    empty_results = search_products(q="nonexistentxyzfood123", limit=10, db=db_session)
    assert len(empty_results) == 0
