import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Product, Category, NutritionalInformation, Ingredient, ProductIngredient, SearchHistory
from app.schemas.schemas import ProductDetail, ProductSummary, ProductIngredientItem, NutritionOut, CategoryOut, ProductManualEntryIn
from app.services.product_service import product_service
from app.services.analysis_service import analysis_service
from app.utils.barcode_validator import validate_barcode, clean_raw_barcode, normalize_barcode

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/categories", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    """Retrieve all food and beverage categories."""
    cats = db.query(Category).all()
    return cats

def format_product_detail(product) -> dict:
    """Helper to serialize a Product ORM instance into ProductDetail format."""
    ingredients_list = []
    if product.product_ingredients:
        for pi in product.product_ingredients:
            ingredients_list.append(ProductIngredientItem(
                ingredient_name=pi.ingredient.canonical_name if pi.ingredient else "Unknown",
                ins_number=pi.ingredient.ins_number if pi.ingredient else None,
                position_order=pi.position_order,
                estimated_percentage=pi.estimated_percentage,
                is_whole_grain=pi.is_whole_grain,
                is_allergen=pi.is_allergen,
                is_additive=pi.ingredient.is_additive if pi.ingredient else False,
                additive_type=pi.ingredient.additive_type if pi.ingredient else None
            ))

    nutrition_dto = NutritionOut.model_validate(product.nutrition) if product.nutrition else None
    category_dto = CategoryOut.model_validate(product.category) if product.category else None

    return {
        "id": product.id,
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        "generic_name": product.generic_name,
        "category_id": product.category_id,
        "serving_size": product.serving_size,
        "image_url": product.image_url,
        "packaging": product.packaging,
        "origin_country": product.origin_country,
        "nova_group": product.nova_group,
        "nutri_score_grade": product.nutri_score_grade,
        "source": getattr(product, "source", "seed"),
        "data_completeness_score": product.data_completeness_score,
        "data_source": product.data_source,
        "created_at": product.created_at,
        "category": category_dto,
        "nutrition": nutrition_dto,
        "ingredients": ingredients_list,
        # Warning flag if completeness is under 0.60
        "data_completeness_warning": product.data_completeness_score < 0.60
    }

@router.get("/barcode/{barcode}", response_model=ProductDetail)
def get_product_by_barcode(
    barcode: str = Path(..., description="GTIN-8, UPC-12, EAN-13, or ITF-14 barcode"),
    db: Session = Depends(get_db)
):
    """
    Search product by barcode.
    Order of operations:
    1. Validate barcode format and GS1 check-digit.
    2. Search local database (cache hit).
    3. If not found locally, query Open Food Facts API v2.
    4. Normalize and persist product, nutrition, and ingredients in local DB.
    5. Return complete product details with data completeness ratio.
    """
    product = product_service.get_by_barcode(barcode=barcode, db=db)
    return format_product_detail(product)

@router.get("/search", response_model=List[ProductSummary])
def search_products(
    q: str = Query(..., min_length=1, description="Search term (product name, brand, or barcode substring)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search products in local database by name, brand, or barcode substring.
    """
    products = product_service.search_products(query=q, db=db, limit=limit)
    return products

@router.post("/manual-entry", response_model=ProductDetail, status_code=status.HTTP_201_CREATED)
def create_manual_product(
    payload: ProductManualEntryIn,
    db: Session = Depends(get_db)
):
    """
    Manual entry endpoint when a product is missing from upstream databases.
    Enforces check-digit validation, nutrition range consistency, and immediate scoring.
    Saved with source='user_entered' and labelled 'Entered by a user; not verified' in UI.
    """
    # 1. Barcode check-digit validation
    cleaned_bc = clean_raw_barcode(payload.barcode)
    is_valid, err_msg = validate_barcode(cleaned_bc)
    if not is_valid:
        raise HTTPException(status_code=422, detail=err_msg)

    # 2. Verify category exists
    cat = db.query(Category).filter_by(id=payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail=f"Category with ID {payload.category_id} not found.")

    # 3. Calculate data completeness score
    critical_six = [payload.energy_kcal, payload.sugars_g, payload.sodium_mg, payload.saturated_fat_g, payload.proteins_g, payload.fiber_g]
    completeness = round(sum(1 for p in critical_six if p is not None) / 6.0, 2)
    if completeness == 0.0 and payload.ingredients_text:
        completeness = 0.25

    # 4. Check if barcode already exists
    product = db.query(Product).filter_by(barcode=cleaned_bc).first()
    if not product:
        product = Product(
            id=str(uuid.uuid4()),
            barcode=cleaned_bc,
            name=payload.name.strip(),
            brand=payload.brand.strip() if payload.brand else None,
            category_id=payload.category_id,
            serving_size=payload.serving_size,
            data_completeness_score=completeness,
            data_source="user_entered",
            source="user_entered"
        )
        db.add(product)
        db.flush()
    else:
        product.name = payload.name.strip()
        product.brand = payload.brand.strip() if payload.brand else product.brand
        product.category_id = payload.category_id
        product.serving_size = payload.serving_size or product.serving_size
        product.data_completeness_score = completeness
        product.data_source = "user_entered"
        product.source = "user_entered"

    # 5. Create / Update Nutritional Information
    nutrition = db.query(NutritionalInformation).filter_by(product_id=product.id).first()
    if not nutrition:
        nutrition = NutritionalInformation(
            id=str(uuid.uuid4()),
            product_id=product.id,
            energy_kcal=payload.energy_kcal,
            fat_g=payload.fat_g,
            saturated_fat_g=payload.saturated_fat_g,
            carbohydrates_g=payload.carbohydrates_g,
            sugars_g=payload.sugars_g,
            fiber_g=payload.fiber_g,
            proteins_g=payload.proteins_g,
            sodium_mg=payload.sodium_mg,
            salt_g=payload.salt_g,
            basis=payload.serving_basis
        )
        db.add(nutrition)
    else:
        nutrition.energy_kcal = payload.energy_kcal
        nutrition.fat_g = payload.fat_g
        nutrition.saturated_fat_g = payload.saturated_fat_g
        nutrition.carbohydrates_g = payload.carbohydrates_g
        nutrition.sugars_g = payload.sugars_g
        nutrition.fiber_g = payload.fiber_g
        nutrition.proteins_g = payload.proteins_g
        nutrition.sodium_mg = payload.sodium_mg
        nutrition.salt_g = payload.salt_g
        nutrition.basis = payload.serving_basis

    # 6. Parse ingredients if text provided
    if payload.ingredients_text:
        # Clear existing ingredients for update
        db.query(ProductIngredient).filter_by(product_id=product.id).delete()
        raw_tokens = [t.strip().strip(".()[]") for t in payload.ingredients_text.split(",") if t.strip()]
        seen_ing_ids = set()
        for idx, tok in enumerate(raw_tokens[:30]):
            tok_name = tok.title()
            ing = db.query(Ingredient).filter_by(canonical_name=tok_name).first()
            if not ing:
                ing = Ingredient(
                    id=str(uuid.uuid4()),
                    canonical_name=tok_name,
                    is_additive=False
                )
                db.add(ing)
                db.flush()

            if ing.id in seen_ing_ids:
                continue
            seen_ing_ids.add(ing.id)

            pi = ProductIngredient(
                id=str(uuid.uuid4()),
                product_id=product.id,
                ingredient_id=ing.id,
                position_order=idx + 1,
                is_whole_grain=False
            )
            db.add(pi)

    db.commit()
    db.refresh(product)

    # 7. Compute full scores immediately
    analysis_service.analyze_product(product, db)

    # 8. Log in SearchHistory as manual_entry
    history = SearchHistory(
        id=str(uuid.uuid4()),
        product_id=product.id,
        query_term=f"{cleaned_bc} [manual_entry]",
        query_type="barcode"
    )
    if hasattr(history, "outcome"):
        setattr(history, "outcome", "manual_entry")
    db.add(history)
    db.commit()

    return format_product_detail(product)
