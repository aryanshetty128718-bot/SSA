import os
import time
import httpx
from typing import Dict, Any, Optional, List, Tuple
from app.core.config import settings
from app.core.logging_config import logger
from app.core.exceptions import ProductNotFoundError, ExternalAPIUnavailableError

# In-memory negative cache: barcode -> timestamp of 404/not_found
# TTL = 24 hours (86,400 seconds)
NEGATIVE_CACHE_TTL_SECONDS = 86400
_NEGATIVE_CACHE: Dict[str, float] = {}

def get_country_mirror(barcode: str) -> Optional[str]:
    """Determines preferred Open Food Facts regional mirror based on GS1 country prefix."""
    clean = barcode.strip()
    if clean.startswith("890"):
        return "https://in.openfoodfacts.org"
    elif clean.startswith(("30", "31", "32", "33", "34", "35", "36", "37")):
        return "https://fr.openfoodfacts.org"
    elif clean.startswith(("40", "41", "42", "43", "44")):
        return "https://de.openfoodfacts.org"
    elif clean.startswith(("50", "500", "501", "502", "503", "504", "505", "506", "509")):
        return "https://uk.openfoodfacts.org"
    return None

class OpenFoodFactsClient:
    """
    Resilient client for Open Food Facts API v2 with regional country routing,
    24h negative cache, fast retries, and optional USDA FoodData Central fallback.
    """

    FIELDS = [
        "code",
        "product_name",
        "product_name_en",
        "generic_name",
        "brands",
        "image_url",
        "image_front_url",
        "categories_tags",
        "categories",
        "ingredients_text",
        "ingredients",
        "allergens_tags",
        "quantity",
        "serving_size",
        "nutriments",
        "nova_group",
        "nutriscore_grade"
    ]

    def __init__(self, base_url: Optional[str] = None, timeout: float = 3.5, max_retries: int = 1):
        self.base_url = (base_url or settings.OPEN_FOOD_FACTS_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": "SmartShoppingAssistant/1.0 (academic project; contact: admin@smartshopping.local)",
            "Accept": "application/json"
        }

    def fetch_product(self, barcode: str, retry_live: bool = False) -> Dict[str, Any]:
        """
        Fetches product JSON from Open Food Facts API v2.
        Order:
        1. Checks 24h negative cache (unless retry_live=True).
        2. Queries regional mirror first (e.g. in.openfoodfacts.org for 890).
        3. Falls back to world.openfoodfacts.org.
        4. If not found, attempts USDA FoodData Central fallback if API key configured.
        5. Updates negative cache if genuinely not in any source.
        """
        clean_barcode = barcode.strip()

        # 1. Check 24-hour negative cache
        now = time.time()
        if not retry_live and clean_barcode in _NEGATIVE_CACHE:
            cached_time = _NEGATIVE_CACHE[clean_barcode]
            if now - cached_time < NEGATIVE_CACHE_TTL_SECONDS:
                logger.info(f"Negative cache HIT for barcode {clean_barcode} (not found within last 24h).")
                raise ProductNotFoundError(clean_barcode)
            else:
                del _NEGATIVE_CACHE[clean_barcode]
        elif retry_live and clean_barcode in _NEGATIVE_CACHE:
            del _NEGATIVE_CACHE[clean_barcode]

        # 2. Build ordered endpoints (country mirror first, then world)
        mirror = get_country_mirror(clean_barcode)
        urls_to_try = []
        if mirror and mirror != self.base_url:
            urls_to_try.append(f"{mirror}/api/v2/product/{clean_barcode}.json")
        urls_to_try.append(f"{self.base_url}/api/v2/product/{clean_barcode}.json")

        params = {"fields": ",".join(self.FIELDS)}
        last_exception = None

        for endpoint_url in urls_to_try:
            for attempt in range(self.max_retries + 1):
                try:
                    logger.info(f"Querying OFF endpoint {endpoint_url} (attempt {attempt + 1})...")
                    with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                        response = client.get(endpoint_url, params=params)

                    if response.status_code == 404:
                        break  # Try next endpoint or fallback

                    if response.status_code >= 500:
                        logger.warning(f"OFF returned {response.status_code} at {endpoint_url}")
                        if attempt < self.max_retries:
                            time.sleep(0.3 * (attempt + 1))
                            continue
                        break

                    try:
                        data = response.json()
                    except Exception:
                        break

                    if data.get("status") == 1 and "product" in data:
                        data["_source"] = "openfoodfacts"
                        return data
                    elif data.get("status") == 0:
                        break  # Product confirmed not in this mirror

                except (httpx.TimeoutException, httpx.RequestError) as net_err:
                    logger.warning(f"OFF net error on {endpoint_url} (attempt {attempt + 1}): {net_err}")
                    last_exception = net_err
                    if attempt < self.max_retries:
                        time.sleep(0.3 * (attempt + 1))
                        continue

        # 3. Optional USDA FoodData Central fallback
        usda_res = self._try_usda_fallback(clean_barcode)
        if usda_res:
            return usda_res

        # 4. Product confirmed not found in any upstream database -> record in negative cache
        _NEGATIVE_CACHE[clean_barcode] = time.time()
        raise ProductNotFoundError(clean_barcode)

    def _try_usda_fallback(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Queries USDA FoodData Central branded foods API if FDC_API_KEY is available."""
        api_key = getattr(settings, "FDC_API_KEY", None) or os.getenv("FDC_API_KEY")
        if not api_key:
            return None

        clean_barcode = barcode.strip()
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        params = {
            "query": clean_barcode,
            "dataType": "Branded",
            "pageSize": 1,
            "api_key": api_key
        }

        try:
            logger.info(f"Querying USDA FoodData Central for UPC {clean_barcode}...")
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
            foods = data.get("foods", [])
            if not foods:
                return None

            food = foods[0]
            # Convert USDA food item to OFF-like product dict
            nutriments = {}
            for nut in food.get("foodNutrients", []):
                n_name = (nut.get("nutrientName") or "").lower()
                val = nut.get("value")
                if "energy" in n_name:
                    nutriments["energy-kcal_100g"] = val
                elif "sugar" in n_name:
                    nutriments["sugars_100g"] = val
                elif "fatty acids, total saturated" in n_name or "saturated fat" in n_name:
                    nutriments["saturated-fat_100g"] = val
                elif "total lipid (fat)" in n_name or "total fat" in n_name:
                    nutriments["fat_100g"] = val
                elif "carbohydrate" in n_name:
                    nutriments["carbohydrates_100g"] = val
                elif "protein" in n_name:
                    nutriments["proteins_100g"] = val
                elif "sodium" in n_name:
                    # In USDA, sodium is in mg
                    nutriments["sodium_100g"] = (val / 1000.0) if val is not None else None
                elif "fiber" in n_name:
                    nutriments["fiber_100g"] = val

            product_dict = {
                "code": clean_barcode,
                "product_name": food.get("description", "").title(),
                "brands": food.get("brandOwner") or food.get("brandName") or "",
                "categories": food.get("brandedFoodCategory") or "Packaged Foods",
                "categories_tags": [f"en:{food.get('brandedFoodCategory', 'packaged-foods').lower().replace(' ', '-')}"],
                "ingredients_text": food.get("ingredients") or "",
                "serving_size": food.get("servingSizeUnit") and f"{food.get('servingSize', '')} {food.get('servingSizeUnit', '')}",
                "nutriments": nutriments,
                "nova_group": None,
                "nutriscore_grade": None
            }

            return {
                "status": 1,
                "product": product_dict,
                "_source": "usda"
            }
        except Exception as e:
            logger.warning(f"USDA fallback error for {clean_barcode}: {e}")
            return None

    def search_products(self, query: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """
        Searches Open Food Facts for products matching query using search API.
        Returns a list of raw product dicts.
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        url = f"{self.base_url}/cgi/search.pl"
        params = {
            "search_terms": clean_q,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": page_size,
            "fields": ",".join(self.FIELDS)
        }

        try:
            logger.info(f"Searching Open Food Facts for '{clean_q}' (limit={page_size})...")
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(url, params=params)

            if response.status_code >= 400:
                logger.warning(f"Open Food Facts search returned HTTP {response.status_code}")
                return []

            data = response.json()
            products = data.get("products", [])
            return [p for p in products if isinstance(p, dict)]
        except Exception as e:
            logger.warning(f"Open Food Facts search error for '{clean_q}': {e}")
            return []

# Global client singleton
off_client = OpenFoodFactsClient()
