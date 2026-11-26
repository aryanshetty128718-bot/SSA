from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models import Product
from app.core.exceptions import ProductNotFoundError
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import recommendation_service

router = APIRouter(tags=["Recommendations"])

@router.get("/products/{id}/alternatives", response_model=RecommendationResponse)
@router.get("/recommendations/{id}", response_model=RecommendationResponse)
def get_alternatives_by_id(
    id: str = Path(..., description="Target product UUID or barcode"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations to return"),
    db: Session = Depends(get_db)
):
    """
    Returns healthier alternative products for a given product UUID or barcode.
    Applies strict category relevance, data completeness filtering, trade-off guarding,
    multimodal similarity, and deterministic composite ranking.
    """
    clean_id = str(id).strip()
    product = db.query(Product).filter(
        or_(Product.id == clean_id, Product.barcode == clean_id)
    ).first()

    if not product:
        if clean_id.isdigit():
            try:
                from app.services.product_service import product_service
                product = product_service.get_by_barcode(clean_id, db)
            except Exception:
                product = None

    if not product:
        raise ProductNotFoundError(f"Product '{clean_id}' was not found in database.")

    return recommendation_service.find_alternatives(product=product, db=db, limit=limit)

@router.get("/products/barcode/{barcode}/alternatives", response_model=RecommendationResponse)
@router.get("/recommendations/barcode/{barcode}", response_model=RecommendationResponse)
def get_alternatives_by_barcode(
    barcode: str = Path(..., description="Target product GTIN barcode"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations to return"),
    db: Session = Depends(get_db)
):
    """
    Returns healthier alternative products for a given product barcode.
    Applies strict category relevance, data completeness filtering, trade-off guarding,
    multimodal similarity, and deterministic composite ranking.
    """
    product = db.query(Product).filter(Product.barcode == barcode.strip()).first()
    if not product:
        try:
            from app.services.product_service import product_service
            product = product_service.get_by_barcode(barcode.strip(), db)
        except Exception:
            product = None

    if not product:
        raise ProductNotFoundError(f"Product with barcode '{barcode}' was not found in database.")

    return recommendation_service.find_alternatives(product=product, db=db, limit=limit)
