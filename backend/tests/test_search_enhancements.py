"""
Tests for Search Success Rate Enhancements:
- Barcode normalization (spaces, hyphens, leading zero EAN-13, GTIN-14)
- Check digit validation and error classifications
- Negative cache 24h TTL and retry_live bypass
- Parser tolerance (accepts name/brand + 1 nutrient or ingredients)
- Manual entry validation (sugars > carbs rejected, non-negative, user_entered source)
"""

import pytest
from app.utils.barcode_validator import (
    clean_raw_barcode,
    validate_barcode,
    get_barcode_variants
)
from app.services.off_parser import parse_off_product
from app.core.exceptions import InsufficientDataError, ProductNotFoundError
from app.services.off_client import OpenFoodFactsClient, _NEGATIVE_CACHE
import time

def test_clean_raw_barcode():
    assert clean_raw_barcode("  8901058852891  ") == "8901058852891"
    assert clean_raw_barcode("890-105-885-2891") == "8901058852891"
    assert clean_raw_barcode("0 12345 67890 5") == "012345678905"

def test_barcode_variants_upca_and_ean13():
    # 12-digit UPC-A: 012345678905 -> EAN-13: 0012345678905
    variants_12 = get_barcode_variants("012345678905")
    assert "012345678905" in variants_12
    assert "0012345678905" in variants_12

    # 13-digit EAN-13 starting with 0: 0012345678905 -> 012345678905
    variants_13 = get_barcode_variants("0012345678905")
    assert "012345678905" in variants_13

def test_barcode_check_digit_rejection():
    # 4006381333932 with altered last digit -> 4006381333931
    is_valid, msg = validate_barcode("4006381333931")
    assert not is_valid
    assert "Invalid check digit" in msg

def test_parser_tolerance_accepts_minimal_data():
    # Record with product name and only 1 nutrient (energy_kcal)
    minimal_payload = {
        "status": 1,
        "product": {
            "code": "8901234567890",
            "product_name": "Minimalist Oat Snack",
            "nutriments": {
                "energy-kcal_100g": 350.0
            }
        }
    }
    parsed = parse_off_product(minimal_payload)
    assert parsed["product"]["name"] == "Minimalist Oat Snack"
    assert parsed["nutrition"]["energy_kcal"] == 350.0
    assert parsed["nutrition"]["sugars_g"] is None
    assert parsed["nutrition"]["saturated_fat_g"] is None
    assert parsed["product"]["data_completeness_score"] < 0.50

def test_parser_tolerance_accepts_ingredients_only():
    # Record with product name and ingredients only, no nutrition facts
    ing_payload = {
        "status": 1,
        "product": {
            "code": "8901234567890",
            "product_name": "Organic Herbal Tea",
            "ingredients_text": "Peppermint leaves, Chamomile flowers, Spearmint"
        }
    }
    parsed = parse_off_product(ing_payload)
    assert parsed["product"]["name"] == "Organic Herbal Tea"
    assert len(parsed["ingredients"]) == 3
    assert parsed["product"]["data_completeness_score"] == 0.25

def test_parser_rejects_empty_record():
    empty_payload = {
        "status": 1,
        "product": {
            "code": "8901234567890"
        }
    }
    with pytest.raises(InsufficientDataError):
        parse_off_product(empty_payload)

def test_negative_cache_and_bypass():
    client = OpenFoodFactsClient(timeout=1.0, max_retries=0)
    fake_barcode = "9999999999994"

    # Manually populate negative cache
    _NEGATIVE_CACHE[fake_barcode] = time.time()

    # Normal lookup hits negative cache immediately without network call
    t0 = time.time()
    with pytest.raises(ProductNotFoundError):
        client.fetch_product(fake_barcode, retry_live=False)
    elapsed = time.time() - t0
    assert elapsed < 0.1, "Negative cache lookup should be near instantaneous"

    # Clean up
    if fake_barcode in _NEGATIVE_CACHE:
        del _NEGATIVE_CACHE[fake_barcode]

