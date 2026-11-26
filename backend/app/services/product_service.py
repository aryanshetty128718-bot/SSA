import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import (
    Product, Category, NutritionalInformation,
    Ingredient, ProductIngredient, SearchHistory, ProductCategoryTag
)
from app.utils.barcode_validator import validate_barcode, normalize_barcode, clean_raw_barcode, get_barcode_variants
from app.core.exceptions import (
    BarcodeValidationError,
    ProductNotFoundError,
    ExternalAPIUnavailableError,
    InsufficientDataError
)
from app.services.off_client import off_client, OpenFoodFactsClient
from app.services.off_parser import parse_off_product
from app.core.logging_config import logger

class ProductService:
    def __init__(self, client: Optional[OpenFoodFactsClient] = None):
        self.off_client = client or off_client

    def _log_search(
        self,
        db: Session,
        term: str,
        query_type: str,
        outcome: str,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Records an entry in the search_history audit log with structured outcome."""
        try:
            history = SearchHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                product_id=product_id,
                query_term=f"{term} [{outcome}]",
                query_type=query_type
            )
            # If outcome column exists on model, populate it
            if hasattr(history, "outcome"):
                setattr(history, "outcome", outcome)
            db.add(history)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record search history: {e}")

    def get_by_barcode(
        self,
        barcode: str,
        db: Session,
        user_id: Optional[str] = None,
        retry_live: bool = False
    ) -> Product:
        """
        Retrieves a product by barcode.
        Search Order:
        1. Validates barcode format & check digit; extracts standard variants (UPC-A <-> EAN-13, GTIN-14).
        2. Queries local database for barcode and variants (Cache HIT).
        3. If not found locally, queries upstream with country routing, 24h negative cache, and USDA fallback.
        4. Normalizes and caches product, nutrition, and ingredients in the database (safely deduplicating ingredients).
        5. Logs the query and outcome in SearchHistory.
        """
        # 1. Barcode validation & variant generation
        cleaned = clean_raw_barcode(barcode)
        is_valid, error_msg = validate_barcode(cleaned)
        if not is_valid:
            self._log_search(db, cleaned or barcode, "barcode", "invalid_check_digit" if "check digit" in error_msg.lower() else "barcode_format", user_id=user_id)
            raise BarcodeValidationError(error_msg)

        variants = get_barcode_variants(cleaned)
        clean_barcode = variants[0]

        # 2. Local Database Query First across all variants
        local_product = db.query(Product).filter(Product.barcode.in_(variants)).first()
        if local_product:
            logger.info(f"Barcode {clean_barcode} (or variant) found in local database (Cache HIT: {local_product.barcode}).")
            self._log_search(db, clean_barcode, "barcode", "found_local", product_id=local_product.id, user_id=user_id)
            return local_product

        logger.info(f"Barcode {clean_barcode} NOT in local DB. Querying upstream APIs (OFF/USDA)...")

        # 3. Upstream Query with fallback across barcode variants
        raw_data = None
        upstream_source = "openfoodfacts"
        matched_barcode = clean_barcode
        last_error = None

        for cand_bc in variants:
            try:
                raw_data = self.off_client.fetch_product(cand_bc, retry_live=retry_live)
                matched_barcode = cand_bc
                upstream_source = raw_data.get("_source", "openfoodfacts")
                break
            except ProductNotFoundError as pnf:
                last_error = pnf
                continue
            except ExternalAPIUnavailableError as api_err:
                last_error = api_err
                continue

        if not raw_data:
            if isinstance(last_error, ExternalAPIUnavailableError):
                # Double check concurrent insert
                concurrent_check = db.query(Product).filter(Product.barcode.in_(variants)).first()
                if concurrent_check:
                    self._log_search(db, clean_barcode, "barcode", "found_local", product_id=concurrent_check.id, user_id=user_id)
                    return concurrent_check
                self._log_search(db, clean_barcode, "barcode", "timeout/rate_limit", user_id=user_id)
                raise last_error
            self._log_search(db, clean_barcode, "barcode", "not_in_off", user_id=user_id)
            raise ProductNotFoundError(clean_barcode)

        # 4. Parse & Normalize Payload
        try:
            parsed = parse_off_product(raw_data)
        except InsufficientDataError as data_err:
            self._log_search(db, clean_barcode, "barcode", "in_off_but_rejected", user_id=user_id)
            raise data_err
        except Exception as parse_err:
            self._log_search(db, clean_barcode, "barcode", "other", user_id=user_id)
            raise ExternalAPIUnavailableError(
                service="Open Food Facts",
                detail=f"Failed to parse upstream product structure: {parse_err}"
            )

        # 5. Store / Cache in Database
        try:
            # Find or create Category
            cat_info = parsed["category"]
            category = db.query(Category).filter_by(slug=cat_info["slug"]).first()
            if not category:
                category = Category(
                    name=cat_info["name"],
                    slug=cat_info["slug"],
                    product_type=cat_info["product_type"],
                    description=f"Auto-created from tag '{cat_info['slug']}'"
                )
                db.add(category)
                db.flush()

            # Create Product
            prod_info = parsed["product"]
            new_product = Product(
                id=str(uuid.uuid4()),
                barcode=clean_barcode,
                name=prod_info["name"],
                brand=prod_info["brand"],
                generic_name=prod_info["generic_name"],
                category_id=category.id,
                serving_size=prod_info["serving_size"],
                image_url=prod_info["image_url"],
                packaging=prod_info["packaging"],
                nova_group=prod_info["nova_group"],
                nutri_score_grade=prod_info["nutri_score_grade"],
                data_completeness_score=prod_info["data_completeness_score"],
                data_source=upstream_source,
                source=upstream_source
            )
            db.add(new_product)
            db.flush()

            # Create Nutritional Information
            nut_info = parsed["nutrition"]
            new_nutrition = NutritionalInformation(
                id=str(uuid.uuid4()),
                product_id=new_product.id,
                energy_kcal=nut_info["energy_kcal"],
                energy_kj=nut_info["energy_kj"],
                fat_g=nut_info["fat_g"],
                saturated_fat_g=nut_info["saturated_fat_g"],
                trans_fat_g=nut_info["trans_fat_g"],
                carbohydrates_g=nut_info["carbohydrates_g"],
                sugars_g=nut_info["sugars_g"],
                added_sugars_g=nut_info["added_sugars_g"],
                fiber_g=nut_info["fiber_g"],
                proteins_g=nut_info["proteins_g"],
                sodium_mg=nut_info["sodium_mg"],
                salt_g=nut_info["salt_g"],
                fruits_vegetables_nuts_colza_walnut_olive_oils_pct=nut_info["fruits_vegetables_nuts_colza_walnut_olive_oils_pct"],
                basis=nut_info["basis"]
            )
            db.add(new_nutrition)

            # Create Ingredients & ProductIngredient relations with deduplication
            seen_ingredients = set()
            for ing_item in parsed["ingredients"]:
                canonical_name = ing_item["name"]
                # Match or insert ingredient
                ingredient = db.query(Ingredient).filter_by(canonical_name=canonical_name).first()
                if not ingredient:
                    ingredient = Ingredient(
                        id=str(uuid.uuid4()),
                        canonical_name=canonical_name,
                        ins_number=ing_item.get("ins_number"),
                        is_additive=ing_item.get("is_additive", False)
                    )
                    db.add(ingredient)
                    db.flush()

                if ingredient.id in seen_ingredients:
                    continue
                seen_ingredients.add(ingredient.id)

                pi = ProductIngredient(
                    id=str(uuid.uuid4()),
                    product_id=new_product.id,
                    ingredient_id=ingredient.id,
                    position_order=ing_item["position_order"],
                    estimated_percentage=ing_item.get("estimated_percentage"),
                    is_whole_grain=ing_item.get("is_whole_grain", False)
                )
                db.add(pi)

            # Store category tags hierarchy
            category_tags = parsed.get("category_tags", [])
            for depth, tag in enumerate(category_tags):
                cat_tag = ProductCategoryTag(
                    id=str(uuid.uuid4()),
                    product_id=new_product.id,
                    tag=tag,
                    depth=depth
                )
                db.add(cat_tag)

            db.commit()
            db.refresh(new_product)

            outcome_code = f"found_{upstream_source}" if upstream_source in ("usda", "off") else "found_off"
            logger.info(f"Successfully cached product '{new_product.name}' ({clean_barcode}) into local DB via {upstream_source}.")
            self._log_search(db, clean_barcode, "barcode", outcome_code, product_id=new_product.id, user_id=user_id)
            return new_product

        except Exception as db_err:
            db.rollback()
            logger.exception(f"Error persisting upstream product to database: {db_err}")
            self._log_search(db, clean_barcode, "barcode", "other", user_id=user_id)
            raise db_err

    def persist_parsed_product(self, parsed: Dict[str, Any], db: Session) -> Optional[Product]:
        """Helper to persist a parsed product dict into DB, returning the Product."""
        try:
            prod_info = parsed["product"]
            clean_barcode = prod_info["barcode"]

            # If already exists, return existing
            existing = db.query(Product).filter_by(barcode=clean_barcode).first()
            if existing:
                return existing

            # Category
            cat_info = parsed["category"]
            category = db.query(Category).filter_by(slug=cat_info["slug"]).first()
            if not category:
                category = Category(
                    name=cat_info["name"],
                    slug=cat_info["slug"],
                    product_type=cat_info["product_type"],
                    description=f"Auto-created from Open Food Facts tag '{cat_info['slug']}'"
                )
                db.add(category)
                db.flush()

            # Product
            new_product = Product(
                id=str(uuid.uuid4()),
                barcode=clean_barcode,
                name=prod_info["name"],
                brand=prod_info["brand"],
                generic_name=prod_info["generic_name"],
                category_id=category.id,
                serving_size=prod_info["serving_size"],
                image_url=prod_info["image_url"],
                packaging=prod_info["packaging"],
                nova_group=prod_info["nova_group"],
                nutri_score_grade=prod_info["nutri_score_grade"],
                data_completeness_score=prod_info["data_completeness_score"],
                data_source="open_food_facts",
                source="openfoodfacts"
            )
            db.add(new_product)
            db.flush()

            # Nutrition
            nut_info = parsed["nutrition"]
            new_nutrition = NutritionalInformation(
                id=str(uuid.uuid4()),
                product_id=new_product.id,
                energy_kcal=nut_info["energy_kcal"],
                energy_kj=nut_info["energy_kj"],
                fat_g=nut_info["fat_g"],
                saturated_fat_g=nut_info["saturated_fat_g"],
                trans_fat_g=nut_info["trans_fat_g"],
                carbohydrates_g=nut_info["carbohydrates_g"],
                sugars_g=nut_info["sugars_g"],
                added_sugars_g=nut_info["added_sugars_g"],
                fiber_g=nut_info["fiber_g"],
                proteins_g=nut_info["proteins_g"],
                sodium_mg=nut_info["sodium_mg"],
                salt_g=nut_info["salt_g"],
                fruits_vegetables_nuts_colza_walnut_olive_oils_pct=nut_info["fruits_vegetables_nuts_colza_walnut_olive_oils_pct"],
                basis=nut_info["basis"]
            )
            db.add(new_nutrition)

            # Ingredients
            for ing_item in parsed["ingredients"]:
                canonical_name = ing_item["name"]
                ingredient = db.query(Ingredient).filter_by(canonical_name=canonical_name).first()
                if not ingredient:
                    ingredient = Ingredient(
                        id=str(uuid.uuid4()),
                        canonical_name=canonical_name,
                        ins_number=ing_item.get("ins_number"),
                        is_additive=ing_item.get("is_additive", False)
                    )
                    db.add(ingredient)
                    db.flush()

                pi = ProductIngredient(
                    id=str(uuid.uuid4()),
                    product_id=new_product.id,
                    ingredient_id=ingredient.id,
                    position_order=ing_item["position_order"],
                    estimated_percentage=ing_item.get("estimated_percentage"),
                    is_whole_grain=ing_item.get("is_whole_grain", False)
                )
                db.add(pi)

            # Category tags
            category_tags = parsed.get("category_tags", [])
            for depth, tag in enumerate(category_tags):
                cat_tag = ProductCategoryTag(
                    id=str(uuid.uuid4()),
                    product_id=new_product.id,
                    tag=tag,
                    depth=depth
                )
                db.add(cat_tag)

            db.commit()
            db.refresh(new_product)
            return new_product
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist parsed product from search: {e}")
            return None

    def search_products(
        self,
        query: str,
        db: Session,
        limit: int = 20,
        user_id: Optional[str] = None
    ) -> List[Product]:
        """
        Searches products in local database first.
        If local results < limit, queries Open Food Facts search API, parses,
        and caches valid items in the database.
        Upstream failures degrade gracefully to returning local results.
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        search_filter = or_(
            Product.name.ilike(f"%{clean_q}%"),
            Product.brand.ilike(f"%{clean_q}%"),
            Product.barcode.ilike(f"%{clean_q}%")
        )

        local_products = db.query(Product).filter(search_filter).limit(limit).all()
        
        # If we have sufficient local results or search query is short, return local
        if len(local_products) >= limit:
            self._log_search(db, clean_q, "text", "local_hit", user_id=user_id)
            return local_products

        # Query Open Food Facts search fallback
        needed = limit - len(local_products)
        try:
            logger.info(f"Local search returned {len(local_products)} results for '{clean_q}'. Querying OFF fallback...")
            off_results = self.off_client.search_products(clean_q, page_size=min(needed * 2, 10))
            cached_new = []
            for raw_prod in off_results:
                try:
                    # Check barcode validity & local existence
                    bc = raw_prod.get("code")
                    if not bc:
                        continue
                    is_val, _ = validate_barcode(str(bc))
                    if not is_val:
                        continue
                    clean_bc = normalize_barcode(str(bc))
                    if any(p.barcode == clean_bc for p in local_products):
                        continue

                    parsed = parse_off_product({"status": 1, "product": raw_prod})
                    persisted = self.persist_parsed_product(parsed, db)
                    if persisted:
                        cached_new.append(persisted)
                        if len(local_products) + len(cached_new) >= limit:
                            break
                except Exception as parse_err:
                    logger.debug(f"Skipping OFF search result item: {parse_err}")
                    continue

            combined = list(local_products) + cached_new
            outcome = "local_and_api_hit" if cached_new else ("local_hit" if local_products else "not_found")
            self._log_search(db, clean_q, "text", outcome, user_id=user_id)
            return combined

        except Exception as e:
            logger.warning(f"OFF search fallback failed for '{clean_q}': {e}. Returning local results.")
            self._log_search(db, clean_q, "text", "local_hit_api_error" if local_products else "not_found", user_id=user_id)
            return local_products

product_service = ProductService()
