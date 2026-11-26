import pytest
from app.utils.data_quality import check_brand_name_consistency

def test_consistent_brand_and_product():
    # Regular consistent products
    ok, msg = check_brand_name_consistency(
        product_name="Zero Sugar Sparkling Green Tea",
        brand="TeaZen"
    )
    assert ok is True
    assert msg == "consistent"

    ok, msg = check_brand_name_consistency(
        product_name="Coca-Cola Original Taste 1.5L",
        brand="Coca-Cola"
    )
    assert ok is True

    ok, msg = check_brand_name_consistency(
        product_name="Nutella Hazelnut Spread",
        brand="Ferrero"
    )
    assert ok is True

def test_inconsistent_brand_name_detected():
    # Crowdsourced error: product name says Coca-Cola, but brand says TeaZen
    ok, msg = check_brand_name_consistency(
        product_name="Coca-Cola Zero Sugar",
        brand="TeaZen"
    )
    assert ok is False
    assert "inconsistency" in msg
    assert "coca-cola" in msg
    assert "TeaZen" in msg

def test_inconsistent_nestle_brand_detected():
    ok, msg = check_brand_name_consistency(
        product_name="Nestle KitKat 4-Finger Milk Chocolate",
        brand="Generic Local Sweets Inc"
    )
    assert ok is False
    assert "nestle" in msg
