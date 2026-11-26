import pytest
from fastapi import HTTPException
from app.db.session import SessionLocal
from app.models import Product, Category
from app.core.config import settings
from app.core.exceptions import ProductNotFoundError
from app.services.recommendation_service import RecommendationService, is_non_comparable_confectionery
from app.services.comparison_service import comparison_service
from app.schemas.comparison import ProductComparisonRequest
from app.api.v1.recommendations import get_alternatives_by_barcode
from app.api.v1.compare import compare_products

recommendation_service = RecommendationService()

def test_safe_relative_delta_handles_zero_division():
    """Verifies that relative delta calculation avoids ZeroDivisionError and misleading 100% deltas."""
    # 0 baseline should return None
    assert recommendation_service._safe_rel_delta(5.0, 0.0) is None
    assert recommendation_service._safe_rel_delta(0.0, 0.0) is None
    assert recommendation_service._safe_rel_delta(10.0, 0.04) is None  # below 0.05 threshold

    # Missing values should return None
    assert recommendation_service._safe_rel_delta(None, 10.0) is None
    assert recommendation_service._safe_rel_delta(5.0, None) is None

    # Baseline >= 1.0 and candidate > 0.05 returns rounded percentage
    assert recommendation_service._safe_rel_delta(5.0, 10.0) == -50.0
    assert recommendation_service._safe_rel_delta(15.0, 10.0) == 50.0

def test_trade_off_guard_detection():
    """Verifies that significant spikes in negative nutrients are flagged by the Trade-Off Guard."""
    orig_nutr = {
        "sugars_g": 5.0,
        "saturated_fat_g": 1.0,
        "sodium_mg": 100.0,
        "energy_kcal": 200.0,
        "fiber_g": 3.0,
        "proteins_g": 5.0
    }
    
    # Candidate with spiked sugar (+5g) and spiked sodium (+150mg)
    cand_nutr = {
        "sugars_g": 10.0,
        "saturated_fat_g": 1.0,
        "sodium_mg": 250.0,
        "energy_kcal": 180.0,
        "fiber_g": 6.0,
        "proteins_g": 8.0
    }

    comps, trade_offs, explanation = recommendation_service._build_parameter_comparison(
        orig_nutr=orig_nutr,
        cand_nutr=cand_nutr,
        product_type="solid"
    )

    assert len(trade_offs) >= 2
    assert any("Sugar" in to for to in trade_offs)
    assert any("Sodium" in to for to in trade_offs)
    assert "Note trade-offs:" in explanation

def test_recommendations_beverage_invariance():
    """Beverages must never recommend solid foods."""
    db = SessionLocal()
    try:
        bev = db.query(Product).join(Category).filter(
            Category.product_type == "beverage",
            Product.source == "openfoodfacts"
        ).first()

        if not bev:
            pytest.skip("No real beverage found in DB")

        res = recommendation_service.find_alternatives(product=bev, db=db, limit=5)
        assert res["query_product"]["product_type"] == "beverage"

        for rec in res["recommendations"]:
            rec_prod = db.query(Product).filter(Product.id == rec["id"]).first()
            assert rec_prod.category.product_type == "beverage", (
                f"Beverage {bev.name} recommended solid product {rec_prod.name} ({rec_prod.category.name})"
            )
    finally:
        db.close()

def test_recommendations_solid_invariance():
    """Solid foods must never recommend beverages."""
    db = SessionLocal()
    try:
        solid = db.query(Product).join(Category).filter(
            Category.product_type == "solid",
            Product.source == "openfoodfacts"
        ).first()

        if not solid:
            pytest.skip("No real solid product found in DB")

        res = recommendation_service.find_alternatives(product=solid, db=db, limit=5)
        assert res["query_product"]["product_type"] == "solid"

        for rec in res["recommendations"]:
            rec_prod = db.query(Product).filter(Product.id == rec["id"]).first()
            assert rec_prod.category.product_type == "solid", (
                f"Solid product {solid.name} recommended beverage {rec_prod.name} ({rec_prod.category.name})"
            )
    finally:
        db.close()

def test_nutella_does_not_return_gum_or_mints():
    """Nutella or hazelnut spread queries must never recommend chewing gum, breath mints, or lozenges."""
    db = SessionLocal()
    try:
        nutella = db.query(Product).filter(Product.barcode == "3017620422003").first()
        if not nutella:
            pytest.skip("Nutella not found in DB")

        res = recommendation_service.find_alternatives(product=nutella, db=db, limit=5)
        for rec in res["recommendations"]:
            name_lower = rec["name"].lower()
            assert "gum" not in name_lower, f"Nutella recommended gum: {rec['name']}"
            assert "mint" not in name_lower, f"Nutella recommended mints: {rec['name']}"
            assert "pastille" not in name_lower, f"Nutella recommended pastilles: {rec['name']}"
            assert "candy" not in name_lower, f"Nutella recommended candy: {rec['name']}"
            
            # Verify candidate is either sweet spread or chocolate/confectionery
            assert rec["project_category"] in ["sweet-spreads-nut-butters", "chocolates-confectionery"]
    finally:
        db.close()

def test_cereal_does_not_return_couscous_or_rice_snaps():
    """Breakfast cereals must never recommend couscous, rice, or pasta dishes."""
    db = SessionLocal()
    try:
        # Find a cereal query
        cereal = db.query(Product).join(Category).filter(
            Category.slug == "breakfast-cereals",
            Product.source == "openfoodfacts"
        ).first()
        if not cereal:
            pytest.skip("No breakfast cereal found in DB")

        res = recommendation_service.find_alternatives(product=cereal, db=db, limit=5)
        for rec in res["recommendations"]:
            name_lower = rec["name"].lower()
            assert "couscous" not in name_lower, f"Cereal recommended couscous: {rec['name']}"
            assert "poultry" not in name_lower, f"Cereal recommended poultry: {rec['name']}"
            assert rec["project_category"] == "breakfast-cereals"
    finally:
        db.close()

def test_not_computable_nutri_score_excluded():
    """Candidates with NOT_COMPUTABLE official Nutri-Score grade must never be recommended."""
    db = SessionLocal()
    try:
        prod = db.query(Product).filter(Product.source == "openfoodfacts").first()
        if not prod:
            pytest.skip("No product found in DB")

        res = recommendation_service.find_alternatives(product=prod, db=db, limit=10)
        for rec in res["recommendations"]:
            grade = rec["nutri_score_grade"]
            assert grade is not None
            assert grade.upper() in ["A", "B", "C", "D", "E"], f"Candidate {rec['name']} has invalid grade {grade}"
            assert grade.upper() != "NOT_COMPUTABLE"
    finally:
        db.close()

def test_similarity_scores_are_non_constant():
    """Verifies that similarity scores reflect true continuous multimodal distance, not a constant floor."""
    db = SessionLocal()
    try:
        # Target a query with multiple recommendations
        cola = db.query(Product).filter(Product.barcode == "5449000000439").first()
        if not cola:
            cola = db.query(Product).join(Category).filter(Category.slug == "soft-drinks-sodas").first()

        if not cola:
            pytest.skip("No soda query found")

        res = recommendation_service.find_alternatives(product=cola, db=db, limit=5)
        if len(res["recommendations"]) >= 2:
            sims = [r["similarity_score"] for r in res["recommendations"]]
            # At least two similarity scores must differ or not all be exactly 0.6000
            assert not all(s == 0.60 for s in sims), f"All similarity scores were constant 0.60: {sims}"
    finally:
        db.close()

def test_product_comparison_endpoint():
    """Tests POST /compare with 2 products."""
    db = SessionLocal()
    try:
        prods = db.query(Product).filter(Product.source == "openfoodfacts").limit(2).all()
        if len(prods) < 2:
            pytest.skip("Not enough products in DB for comparison")

        req = ProductComparisonRequest(barcodes=[prods[0].barcode, prods[1].barcode])
        res = compare_products(request=req, db=db)

        assert len(res.products) == 2
        assert len(res.comparison_matrix) >= 6
        assert len(res.summary_verdict) > 0
        assert isinstance(res.data_confidence_notes, list)

        for item in res.comparison_matrix:
            assert item.polarity in ["positive", "negative"]
            assert len(item.values) == 2
            assert prods[0].barcode in item.values
            assert prods[1].barcode in item.values
    finally:
        db.close()

def test_product_comparison_validation():
    """Tests validation edge cases (< 2 products, > 4 products, non-existent barcode)."""
    db = SessionLocal()
    try:
        # Less than 2 products
        with pytest.raises(HTTPException) as exc_info:
            compare_products(ProductComparisonRequest(barcodes=["12345"]), db=db)
        assert exc_info.value.status_code == 400

        # More than 4 products
        with pytest.raises(HTTPException) as exc_info:
            compare_products(ProductComparisonRequest(barcodes=["1", "2", "3", "4", "5"]), db=db)
        assert exc_info.value.status_code == 400

        # Non-existent product
        with pytest.raises(ProductNotFoundError):
            compare_products(ProductComparisonRequest(barcodes=["0000000000000", "1111111111111"]), db=db)
    finally:
        db.close()
