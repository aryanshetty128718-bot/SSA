from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.saved_product import SavedProduct
from app.models.history import SearchHistory
from app.models.product import Product
from app.core.exceptions import ProductNotFoundError, ValidationException
from app.schemas.auth_admin import (
    UserResponse,
    SavedProductCreate,
    SavedProductResponse,
    SearchHistoryResponse
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve authenticated user's profile."""
    return current_user

@router.get("/history", response_model=List[SearchHistoryResponse])
def get_search_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve paginated search history for the authenticated user."""
    offset = (page - 1) * limit
    history = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.searched_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return history

@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search_history_item(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific search history entry belonging to the authenticated user."""
    item = db.query(SearchHistory).filter(SearchHistory.id == history_id, SearchHistory.user_id == current_user.id).first()
    if not item:
        raise ValidationException("Search history entry not found or access denied")
    db.delete(item)
    db.commit()
    return None

@router.get("/saved-products", response_model=List[SavedProductResponse])
def list_saved_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all products bookmarked/saved by the current user."""
    saved = (
        db.query(SavedProduct)
        .filter(SavedProduct.user_id == current_user.id)
        .order_by(SavedProduct.saved_at.desc())
        .all()
    )
    results = []
    for s in saved:
        p = s.product
        p_dict = {
            "id": p.id,
            "barcode": p.barcode,
            "name": p.name,
            "brand": p.brand,
            "image_url": p.image_url,
            "category_name": p.category.name if p.category else None,
            "overall_score": p.product_score.overall_project_score if p.product_score else None,
            "nutri_score_grade": p.product_score.official_nutri_score_grade if p.product_score else None
        } if p else None
        results.append({
            "id": s.id,
            "user_id": s.user_id,
            "product_id": s.product_id,
            "notes": s.notes,
            "saved_at": s.saved_at,
            "product": p_dict
        })
    return results

@router.post("/saved-products", response_model=SavedProductResponse, status_code=status.HTTP_201_CREATED)
def add_saved_product(
    payload: SavedProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bookmark/save a product for quick reference."""
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise ProductNotFoundError(payload.product_id)

    # Check if already saved
    existing = db.query(SavedProduct).filter(
        SavedProduct.user_id == current_user.id,
        SavedProduct.product_id == payload.product_id
    ).first()
    p_dict = {
        "id": product.id,
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        "image_url": product.image_url,
        "overall_score": product.product_score.overall_project_score if product.product_score else None,
        "nutri_score_grade": product.product_score.official_nutri_score_grade if product.product_score else None
    }
    if existing:
        if payload.notes:
            existing.notes = payload.notes
            db.commit()
            db.refresh(existing)
        return {
            "id": existing.id,
            "user_id": existing.user_id,
            "product_id": existing.product_id,
            "notes": existing.notes,
            "saved_at": existing.saved_at,
            "product": p_dict
        }

    saved = SavedProduct(
        user_id=current_user.id,
        product_id=payload.product_id,
        notes=payload.notes
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    p_dict = {
        "id": product.id,
        "barcode": product.barcode,
        "name": product.name,
        "brand": product.brand,
        "image_url": product.image_url,
        "overall_score": product.product_score.overall_project_score if product.product_score else None,
        "nutri_score_grade": product.product_score.official_nutri_score_grade if product.product_score else None
    }
    return {
        "id": saved.id,
        "user_id": saved.user_id,
        "product_id": saved.product_id,
        "notes": saved.notes,
        "saved_at": saved.saved_at,
        "product": p_dict
    }

@router.delete("/saved-products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a bookmarked product from user's saved list."""
    saved = db.query(SavedProduct).filter(
        SavedProduct.user_id == current_user.id,
        SavedProduct.product_id == product_id
    ).first()
    if not saved:
        raise ValidationException("Product not found in saved list")
    db.delete(saved)
    db.commit()
    return None
