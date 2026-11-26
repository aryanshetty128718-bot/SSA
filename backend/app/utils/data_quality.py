import re
from typing import Tuple

# Recognised mega-brands with high risk of counterfeiting or crowdsourced naming confusion
MEGA_BRANDS = {
    "coca-cola", "coca cola", "pepsi", "pepsi-cola", "nestle", "nestlé",
    "kraft", "unilever", "kellogg", "kelloggs", "heinz", "cadbury",
    "mars", "danone", "lactalis", "ferrero", "mondelez"
}

def normalize_brand_token(text: str) -> str:
    """Strips punctuation and spacing for robust substring matching."""
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())

def check_brand_name_consistency(product_name: str, brand: str) -> Tuple[bool, str]:
    """
    Validates semantic brand-name consistency.
    Detects contradictory crowdsourced records where a famous mega-brand appears
    in the product title (e.g. 'Coca-Cola Zero Sugar') but the stated manufacturer/brand
    is an unrelated third-party entity (e.g. 'TeaZen').

    Returns:
        (is_consistent: bool, message: str)
    """
    clean_name = str(product_name or "").lower()
    clean_brand = str(brand or "").lower()

    if not clean_name or not clean_brand:
        return True, "insufficient data to check"

    norm_brand = normalize_brand_token(clean_brand)

    # Check first 40 characters of name for prominent brand claims
    name_prefix = clean_name[:40]
    for mega in MEGA_BRANDS:
        norm_mega = normalize_brand_token(mega)
        # If the product name prominently starts with or features a mega brand
        if mega in name_prefix:
            # The brand must contain this mega-brand identity
            if norm_mega not in norm_brand and norm_brand not in norm_mega:
                return False, f"Brand-name inconsistency: product name prominently features '{mega}' but brand is declared as '{brand}'"

    return True, "consistent"
