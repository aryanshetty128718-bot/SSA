from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.session import get_db
from app.models import Product
from app.schemas.schemas import ProductAnalysisOut
from app.services.product_service import product_service
from app.services.analysis_service import analysis_service
from app.core.exceptions import ProductNotFoundError

router = APIRouter(tags=["Product Analysis"])

@router.get("/products/{product_id}/analysis", response_model=ProductAnalysisOut)
@router.get("/analysis/{product_id}", response_model=ProductAnalysisOut)
def get_product_analysis_by_id(
    product_id: str = Path(..., description="UUID or GTIN barcode of the product"),
    db: Session = Depends(get_db)
):
    """
    Performs nutritional scoring analysis for a product by its database ID or barcode.
    Returns both the 0-100 Proposed Project Continuous Score and the official Nutri-Score 2023 grade.
    """
    clean_id = str(product_id).strip()
    product = db.query(Product).filter(
        or_(Product.id == clean_id, Product.barcode == clean_id)
    ).first()

    if not product and clean_id.isdigit() and len(clean_id) in {8, 12, 13, 14}:
        # Attempt fallback to barcode search service
        try:
            product = product_service.get_by_barcode(clean_id, db)
        except Exception:
            product = None

    if not product:
        raise ProductNotFoundError(f"Product '{clean_id}' not found.")
    return analysis_service.analyze_product(product, db)

@router.get("/products/barcode/{barcode}/analysis", response_model=ProductAnalysisOut)
@router.get("/analysis/barcode/{barcode}", response_model=ProductAnalysisOut)
def get_product_analysis_by_barcode(
    barcode: str = Path(..., description="GTIN barcode of the product"),
    db: Session = Depends(get_db)
):
    """
    Retrieves or fetches a product by barcode (local DB first, then Open Food Facts),
    and computes the full nutritional analysis.
    """
    product = product_service.get_by_barcode(barcode, db)
    return analysis_service.analyze_product(product, db)
