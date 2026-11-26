import re
from typing import Dict, Any, List, Optional, Tuple
from app.core.exceptions import InsufficientDataError, ProductNotFoundError

BEVERAGE_KEYWORDS = {
    "beverage", "beverages", "drink", "drinks", "soda", "sodas", "water", "waters",
    "juice", "juices", "tea", "teas", "coffee", "coffees", "milk", "milks",
    "smoothie", "smoothies", "lemonade", "cola", "nectar", "kombucha"
}

WHOLE_GRAIN_KEYWORDS = {
    "whole wheat", "whole grain", "whole oats", "rolled oats", "brown rice",
    "quinoa", "millet", "buckwheat", "barley", "spelt", "rye"
}

def clean_float(val: Any) -> Optional[float]:
    """Safely parse float value or return None if missing/invalid/negative."""
    if val is None or val == "" or val == "None":
        return None
    try:
        f = float(val)
        return None if f < 0 else f
    except (ValueError, TypeError):
        return None

def get_nutriment(nutriments: dict, *keys: str) -> Optional[float]:
    """
    Extracts float nutrient from nutriments dict checking keys in order.
    Crucial: An absent key returns None (NULL), never 0.0.
    An explicit 0 is parsed as 0.0 without falsy fallback.
    """
    if not isinstance(nutriments, dict):
        return None
    for key in keys:
        if key in nutriments and nutriments[key] is not None and nutriments[key] != "":
            return clean_float(nutriments[key])
    return None

def determine_product_type(category_tags: List[str], categories_str: str = "") -> str:
    """
    Determines if product is 'beverage' or 'solid' based on category tags and descriptions.
    Ignores generic umbrella tags like 'plant-based-foods-and-beverages'.
    """
    for tag in category_tags:
        clean_tag = tag.lower().replace("en:", "")
        # Skip generic broad umbrella tag
        if "plant-based-foods-and-beverages" in clean_tag:
            continue
        for kw in BEVERAGE_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', clean_tag):
                return "beverage"

    # Also check free-text categories if provided
    clean_cat_str = categories_str.lower().replace("plant-based foods and beverages", "")
    for kw in BEVERAGE_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', clean_cat_str):
            return "beverage"

    return "solid"

def parse_off_product(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses and standardizes Open Food Facts product JSON.
    
    Returns:
        Structured dictionary matching Product, Category, NutritionalInformation,
        and ProductIngredients entities.
    Raises:
        ProductNotFoundError: If product block is missing.
        InsufficientDataError: If product lacks minimum usable identity or nutrition.
    """
    product = raw_data.get("product")
    if not product or not isinstance(product, dict):
        raise ProductNotFoundError("No product payload found in Open Food Facts response.")

    # 1. Product Identity
    barcode = str(product.get("code") or raw_data.get("code") or "").strip()
    name = (
        product.get("product_name") or
        product.get("product_name_en") or
        product.get("generic_name") or
        ""
    ).strip()

    brand = (product.get("brands") or "").split(",")[0].strip() or None
    generic_name = (product.get("generic_name") or "").strip() or None

    # If name is missing, fall back to brand or generic name if available
    if not name and brand:
        name = f"{brand} Food Product"
    elif not name and generic_name:
        name = generic_name

    if not name:
        raise InsufficientDataError("Product rejected: Missing product name, brand, and generic description in record.")
    image_url = product.get("image_front_url") or product.get("image_url") or None
    serving_size = product.get("serving_size") or None
    packaging = product.get("packaging") or None

    # NOVA Group
    raw_nova = product.get("nova_group")
    nova_group = int(raw_nova) if raw_nova in (1, 2, 3, 4, "1", "2", "3", "4") else None

    # Nutri-Score Grade
    raw_grade = str(product.get("nutriscore_grade") or "").strip().upper()
    nutri_score_grade = raw_grade if raw_grade in ("A", "B", "C", "D", "E") else None

    # 2. Category & Product Type
    category_tags = product.get("categories_tags", []) or []
    categories_str = product.get("categories") or ""
    product_type = determine_product_type(category_tags, categories_str)
    basis = "per 100ml" if product_type == "beverage" else "per 100g"

    # Derive clean primary category name
    category_name = "Packaged Foods"
    category_slug = "packaged-foods"
    if category_tags:
        # Find cleanest tag (prefer English tag if available)
        primary_tag = category_tags[-1]
        for tag in reversed(category_tags):
            if tag.startswith("en:"):
                primary_tag = tag
                break
        clean_tag = primary_tag.replace("en:", "").replace("-", " ").strip().title()
        if clean_tag:
            category_name = clean_tag
            category_slug = primary_tag.replace("en:", "").replace(" ", "-").lower()

    # 3. Nutriments Extraction
    nutriments = product.get("nutriments", {}) or {}

    energy_kj = get_nutriment(nutriments, "energy-kj_100g", "energy-kj")
    energy_kcal = get_nutriment(nutriments, "energy-kcal_100g", "energy-kcal", "energy_100g")

    # If kcal is missing but kJ is available, convert kJ -> kcal
    if energy_kcal is None and energy_kj is not None:
        energy_kcal = round(energy_kj / 4.184, 1)
    elif energy_kj is None and energy_kcal is not None:
        energy_kj = round(energy_kcal * 4.184, 1)

    fat_g = get_nutriment(nutriments, "fat_100g", "fat")
    saturated_fat_g = get_nutriment(nutriments, "saturated-fat_100g", "saturated-fat")
    trans_fat_g = get_nutriment(nutriments, "trans-fat_100g", "trans-fat")
    carbohydrates_g = get_nutriment(nutriments, "carbohydrates_100g", "carbohydrates")
    sugars_g = get_nutriment(nutriments, "sugars_100g", "sugars")
    added_sugars_g = get_nutriment(nutriments, "added-sugars_100g", "added-sugars")
    fiber_g = get_nutriment(nutriments, "fiber_100g", "fiber")
    proteins_g = get_nutriment(nutriments, "proteins_100g", "proteins")

    salt_g = get_nutriment(nutriments, "salt_100g", "salt")
    # In Open Food Facts, sodium_100g is reported in grams! Convert to mg.
    sodium_g_raw = get_nutriment(nutriments, "sodium_100g", "sodium")
    sodium_mg = None
    if sodium_g_raw is not None:
        sodium_mg = round(sodium_g_raw * 1000.0, 1)
    elif salt_g is not None:
        # 1g salt ~ 400mg sodium
        sodium_mg = round((salt_g / 2.5) * 1000.0, 1)

    if salt_g is None and sodium_mg is not None:
        salt_g = round((sodium_mg / 1000.0) * 2.5, 3)

    fruits_veg_pct = get_nutriment(
        nutriments,
        "fruits-vegetables-nuts-estimate-from-ingredients_100g",
        "fruits-vegetables-nuts_100g",
        "fruits-vegetables-legumes-estimate-from-ingredients_100g"
    )

    # 4. Ingredients Parsing
    parsed_ingredients = []
    raw_ingredients_list = product.get("ingredients")
    if isinstance(raw_ingredients_list, list) and len(raw_ingredients_list) > 0:
        for idx, item in enumerate(raw_ingredients_list):
            if isinstance(item, dict):
                ing_text = (item.get("text") or item.get("id") or "").replace("en:", "").replace("-", " ").strip()
                if ing_text:
                    ing_clean = ing_text.title()
                    # Check for additive e-number
                    ins_match = re.search(r'\b(e\s*\d{3,4}[a-z]?|ins\s*\d{3,4}[a-z]?)\b', ing_clean, re.I)
                    ins_num = ins_match.group(0).upper().replace(" ", "") if ins_match else None
                    is_additive = bool(ins_num or "en:e" in (item.get("id") or ""))
                    
                    is_whole_grain = any(wg in ing_clean.lower() for wg in WHOLE_GRAIN_KEYWORDS)
                    
                    pct = clean_float(item.get("percent_estimate") or item.get("percent"))
                    parsed_ingredients.append({
                        "name": ing_clean,
                        "position_order": idx + 1,
                        "ins_number": ins_num,
                        "is_additive": is_additive,
                        "is_whole_grain": is_whole_grain,
                        "estimated_percentage": pct
                    })
    elif product.get("ingredients_text"):
        # Fallback: parse comma-separated text
        raw_text = product.get("ingredients_text", "")
        tokens = [t.strip().strip(".()[]") for t in raw_text.split(",") if t.strip()]
        for idx, token in enumerate(tokens[:30]):
            clean_tok = token.title()
            ins_match = re.search(r'\b(e\s*\d{3,4}[a-z]?|ins\s*\d{3,4}[a-z]?)\b', clean_tok, re.I)
            ins_num = ins_match.group(0).upper().replace(" ", "") if ins_match else None
            is_additive = bool(ins_num)
            is_whole_grain = any(wg in clean_tok.lower() for wg in WHOLE_GRAIN_KEYWORDS)
            parsed_ingredients.append({
                "name": clean_tok,
                "position_order": idx + 1,
                "ins_number": ins_num,
                "is_additive": is_additive,
                "is_whole_grain": is_whole_grain,
                "estimated_percentage": None
            })

    # Validate that we have at least minimum usable nutritional parameters OR ingredient declarations
    core_parameters = [energy_kcal, fat_g, saturated_fat_g, carbohydrates_g, sugars_g, proteins_g, sodium_mg, fiber_g]
    present_core_count = sum(1 for p in core_parameters if p is not None)

    if present_core_count == 0 and len(parsed_ingredients) == 0:
        raise InsufficientDataError(f"Product '{name}' rejected: Contains neither nutritional data nor declared ingredients.")

    # Calculate data completeness score (0.0 - 1.0) based on 6 critical scoring parameters + ingredients
    critical_six = [energy_kcal, sugars_g, sodium_mg, saturated_fat_g, proteins_g, fiber_g]
    nutr_completeness = sum(1 for p in critical_six if p is not None) / 6.0
    if nutr_completeness == 0.0 and len(parsed_ingredients) > 0:
        completeness_score = 0.25  # Has declared ingredients but unstated nutrients
    else:
        completeness_score = round(nutr_completeness, 2)

    return {
        "product": {
            "barcode": barcode,
            "name": name,
            "brand": brand,
            "generic_name": generic_name,
            "serving_size": serving_size,
            "image_url": image_url,
            "packaging": packaging,
            "nova_group": nova_group,
            "nutri_score_grade": nutri_score_grade,
            "data_completeness_score": completeness_score,
            "data_source": "open_food_facts",
            "source": "openfoodfacts"
        },
        "category": {
            "name": category_name,
            "slug": category_slug,
            "product_type": product_type
        },
        "category_tags": category_tags,
        "nutrition": {
            "energy_kcal": energy_kcal,
            "energy_kj": energy_kj,
            "fat_g": fat_g,
            "saturated_fat_g": saturated_fat_g,
            "trans_fat_g": trans_fat_g,
            "carbohydrates_g": carbohydrates_g,
            "sugars_g": sugars_g,
            "added_sugars_g": added_sugars_g,
            "fiber_g": fiber_g,
            "proteins_g": proteins_g,
            "sodium_mg": sodium_mg,
            "salt_g": salt_g,
            "fruits_vegetables_nuts_colza_walnut_olive_oils_pct": fruits_veg_pct,
            "basis": basis
        },
        "ingredients": parsed_ingredients
    }
