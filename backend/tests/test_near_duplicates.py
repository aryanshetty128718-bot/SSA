import pytest
from app.ml.similarity import normalize_group_key
from app.services.recommendation_service import RecommendationService
from app.models.product import Product

def test_same_product_line_different_sizes_are_near_duplicates():
    # 250g vs 500g Marie Gold from Britannia must map to the SAME group key (excluded)
    key_250g = normalize_group_key("Britannia Marie Gold Biscuit 250g", "Britannia Industries Ltd")
    key_500g = normalize_group_key("Britannia Marie Gold 500g Pack", "Britannia Industries Ltd")
    assert key_250g == key_500g, f"Expected keys to match: {key_250g} vs {key_500g}"

def test_different_product_lines_same_brand_are_distinct():
    # Britannia Good Day vs Britannia Marie Gold must have DIFFERENT group keys (allowed)
    key_marie = normalize_group_key("Britannia Marie Gold Biscuits 250g", "Britannia Industries Ltd")
    key_good_day = normalize_group_key("Britannia Good Day Butter Cookies 200g", "Britannia Industries Ltd")
    assert key_marie != key_good_day, f"Expected distinct product lines to have different keys: {key_marie} vs {key_good_day}"

def test_meaningful_descriptors_preserved():
    # "Gold", "Tea", "Original" must be preserved as distinct tokens
    key_plain_marie = normalize_group_key("Marie Biscuit 100g", "Britannia")
    key_marie_gold = normalize_group_key("Marie Gold Biscuit 100g", "Britannia")
    key_marie_tea = normalize_group_key("Marie Tea Time Biscuit 100g", "Britannia")

    assert "gold" in key_marie_gold
    assert "gold" not in key_plain_marie
    assert key_marie_gold != key_marie_tea

def test_near_duplicate_filter_logic_in_candidate_selection():
    """
    Verifies that for a Marie Gold query:
    1. A different pack size of Marie Gold (e.g. 500g) is identified as a near-duplicate and excluded.
    2. Another product line from the same manufacturer/brand (e.g. Britannia NutriChoice / Good Day)
       is recognized as a distinct product line and allowed as a candidate.
    """
    rec_service = RecommendationService()

    query_prod = Product(
        id="q-marie-250",
        barcode="8901063012345",
        name="Britannia Marie Gold Biscuit 250g",
        brand="Britannia Industries Ltd"
    )
    query_key = rec_service._get_clean_group_key(query_prod)

    # Candidate 1: Same product line, different pack size (500g)
    cand_marie_500 = Product(
        id="c-marie-500",
        barcode="8901063098765",  # Same manufacturer prefix (8901063)
        name="Britannia Marie Gold Biscuit 500g Family Pack",
        brand="Britannia"
    )
    cand_marie_key = rec_service._get_clean_group_key(cand_marie_500)

    # Candidate 2: Different product line, same manufacturer (Britannia NutriChoice)
    cand_nutrichoice = Product(
        id="c-nutrichoice",
        barcode="8901063054321",  # Same manufacturer prefix (8901063)
        name="Britannia NutriChoice Digestive Biscuit 100g",
        brand="Britannia Industries Ltd"
    )
    cand_nutri_key = rec_service._get_clean_group_key(cand_nutrichoice)

    # Marie Gold 500g must match the query's group key -> MUST be excluded as near-duplicate
    assert cand_marie_key == query_key, "Marie Gold 500g must share the exact group key with Marie Gold 250g"

    # NutriChoice must NOT match the query's group key -> MUST NOT be excluded
    assert cand_nutri_key != query_key, "NutriChoice must have a distinct group key from Marie Gold"
    assert "digestivenutrichoice" in cand_nutri_key
    assert "goldmarie" in query_key
