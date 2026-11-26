from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.comparison import ProductComparisonRequest, ProductComparisonResponse
from app.services.comparison_service import comparison_service

router = APIRouter(tags=["Comparison"])

@router.post("/compare", response_model=ProductComparisonResponse)
def compare_products(
    request: ProductComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Side-by-side comparison across 2 to 4 products.
    Accepts a list of product UUIDs or barcodes.
    Returns:
    - Detailed products list with scores, pros/cons, and nutrients
    - Parameter-level matrix identifying the healthiest performer per nutrient
    - Nuanced summary verdict highlighting trade-offs without declaring unqualified winners
    - Data confidence and compatibility notices
    """
    return comparison_service.compare_products(request=request, db=db)
