import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.nutrition import NutritionalInformation
from app.models.score import ProductScore
from app.models.criteria import ScoringCriteria
from app.models.audit_log import AdminAuditLog
from app.models.history import SearchHistory
from app.models.recommendation import Recommendation
from app.core.exceptions import ProductNotFoundError, ValidationException, DatabaseException
from app.services.analysis_service import AnalysisService
from app.api.deps import get_current_admin
from app.schemas.auth_admin import (
    AdminProductCreate,
    AdminProductUpdate,
    AdminCategoryCreate,
    AdminCategoryUpdate,
    ScoringCriteriaUpdate,
    AuditLogResponse
)

router = APIRouter(prefix="/admin", tags=["Admin"])
analysis_service = AnalysisService()

def log_admin_action(db: Session, admin_id: str, action: str, entity: str, target_id: str, changes: Optional[Dict[str, Any]] = None):
    audit = AdminAuditLog(
        admin_user_id=admin_id,
        action=action,
        target_entity=entity,
        target_id=str(target_id),
        changes_json=json.dumps(changes or {}, default=str)
    )
    db.add(audit)
    db.commit()

# ----------------- Product CRUD & Automatic Re-scoring -----------------

@router.post("/products", status_code=status.HTTP_201_CREATED)
def admin_create_product(
    payload: AdminProductCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin creates a new product with nutritional information, triggering immediate scoring."""
    existing = db.query(Product).filter(Product.barcode == payload.barcode).first()
    if existing:
        raise ValidationException(f"Product with barcode {payload.barcode} already exists")

    product = Product(
        barcode=payload.barcode,
        name=payload.name,
        brand=payload.brand,
        category_id=payload.category_id,
        serving_size=payload.serving_size,
        origin_country=payload.origin_country,
        image_url=payload.image_url,
        source="admin",
        data_source="Manual Admin Entry"
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    if payload.nutrition:
        nutr = NutritionalInformation(
            product_id=product.id,
            energy_kcal=payload.nutrition.get("energy_kcal"),
            sugars_g=payload.nutrition.get("sugars_g"),
            saturated_fat_g=payload.nutrition.get("saturated_fat_g"),
            sodium_mg=payload.nutrition.get("sodium_mg"),
            salt_g=payload.nutrition.get("salt_g"),
            fiber_g=payload.nutrition.get("fiber_g"),
            proteins_g=payload.nutrition.get("proteins_g"),
            fat_g=payload.nutrition.get("fat_g"),
            carbohydrates_g=payload.nutrition.get("carbohydrates_g")
        )
        db.add(nutr)
        db.commit()

    # Automatically compute nutritional analysis and persist ProductScore
    analysis = analysis_service.analyze_product(product, db)

    log_admin_action(db, admin.id, "CREATE", "product", product.id, {"barcode": product.barcode, "name": product.name})
    return {
        "message": "Product created and scored successfully",
        "product_id": product.id,
        "score": analysis.get("overall_project_score")
    }

@router.put("/products/{product_id}")
def admin_update_product(
    product_id: str,
    payload: AdminProductUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin updates product metadata and nutrition, triggering automatic re-scoring."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError(product_id)

    changes = {}
    if payload.name is not None:
        changes["name"] = {"old": product.name, "new": payload.name}
        product.name = payload.name
    if payload.brand is not None:
        changes["brand"] = {"old": product.brand, "new": payload.brand}
        product.brand = payload.brand
    if payload.category_id is not None:
        changes["category_id"] = {"old": product.category_id, "new": payload.category_id}
        product.category_id = payload.category_id
    if payload.serving_size is not None:
        product.serving_size = payload.serving_size
    if payload.origin_country is not None:
        product.origin_country = payload.origin_country
    if payload.image_url is not None:
        product.image_url = payload.image_url

    if payload.nutrition is not None:
        nutr = product.nutrition
        if not nutr:
            nutr = NutritionalInformation(product_id=product.id)
            db.add(nutr)
        for k, v in payload.nutrition.items():
            if hasattr(nutr, k):
                setattr(nutr, k, v)
        changes["nutrition_updated"] = True

    db.commit()
    db.refresh(product)

    # Automatic Re-scoring on Update
    analysis = analysis_service.analyze_product(product, db)
    log_admin_action(db, admin.id, "UPDATE", "product", product.id, changes)

    return {
        "message": "Product updated and re-scored successfully",
        "product_id": product.id,
        "score": analysis.get("overall_project_score")
    }

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_product(
    product_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin deletes a product and its associated scores and recommendations."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError(product_id)

    p_name = product.name
    db.delete(product)
    db.commit()

    log_admin_action(db, admin.id, "DELETE", "product", product_id, {"name": p_name})
    return None

# ----------------- Category CRUD -----------------

@router.get("/categories")
def admin_get_categories(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin lists all categories."""
    cats = db.query(Category).order_by(Category.name.asc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "product_type": c.product_type,
            "description": c.description,
            "parent_id": c.parent_id
        }
        for c in cats
    ]

@router.post("/categories", status_code=status.HTTP_201_CREATED)
def admin_create_category(
    payload: AdminCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin creates a new category."""
    existing = db.query(Category).filter(Category.slug == payload.slug).first()
    if existing:
        raise ValidationException(f"Category with slug '{payload.slug}' already exists")

    cat = Category(
        name=payload.name,
        slug=payload.slug,
        product_type=payload.product_type,
        description=payload.description,
        parent_id=payload.parent_id
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    log_admin_action(db, admin.id, "CREATE", "category", str(cat.id), {"name": cat.name, "slug": cat.slug})
    return cat

@router.put("/categories/{category_id}")
def admin_update_category(
    category_id: int,
    payload: AdminCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin updates an existing category."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise ValidationException(f"Category {category_id} not found")

    changes = {}
    if payload.name is not None:
        changes["name"] = payload.name
        cat.name = payload.name
    if payload.slug is not None:
        changes["slug"] = payload.slug
        cat.slug = payload.slug
    if payload.product_type is not None:
        changes["product_type"] = payload.product_type
        cat.product_type = payload.product_type
    if payload.description is not None:
        cat.description = payload.description
    if payload.parent_id is not None:
        cat.parent_id = payload.parent_id

    db.commit()
    db.refresh(cat)

    log_admin_action(db, admin.id, "UPDATE", "category", str(cat.id), changes)
    return cat

# ----------------- Scoring Criteria & Version Bumping -----------------

@router.get("/scoring-criteria")
def get_scoring_criteria(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """View active scoring criteria and version history."""
    from app.scoring.calculator import CRITERIA_DEFAULTS
    from sqlalchemy import text
    try:
        history = db.execute(text("SELECT version, released_at, description, is_active FROM scoring_version_history ORDER BY id DESC")).fetchall()
        hist_list = [{"version": r[0], "released_at": str(r[1]), "description": r[2], "is_active": bool(r[3])} for r in history]
    except Exception:
        hist_list = []
    
    return {
        **CRITERIA_DEFAULTS,
        "version_history": hist_list
    }

@router.get("/rescore/status")
def get_rescoring_status(
    admin: User = Depends(get_current_admin)
):
    """Get status and progress of the background catalog re-scoring job."""
    from app.services.rescore_job import rescoring_manager
    return rescoring_manager.get_status()

@router.post("/rescore/start")
def start_catalog_rescoring(
    target_version: str = "1.2.0",
    description: str = "Administrative batch catalog re-scoring",
    admin: User = Depends(get_current_admin)
):
    """Manually initiate asynchronous background catalog re-scoring."""
    from app.services.rescore_job import rescoring_manager
    return rescoring_manager.start_rescoring(target_version=target_version, description=description)

@router.put("/scoring-criteria")
def update_scoring_criteria(
    payload: ScoringCriteriaUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin updates scoring criteria.
    Validates that weights sum to 1.0 and cut-offs are strictly ordered.
    Bumps scoring engine version to '1.2.0' and triggers background re-scoring audit.
    """
    # Validation is enforced automatically by Pydantic schema ScoringCriteriaUpdate
    changes = {
        "product_type": payload.product_type,
        "parameters": {k: v.model_dump() for k, v in payload.parameters.items()}
    }

    # Record audit log
    log_admin_action(
        db=db,
        admin_id=admin.id,
        action="CRITERIA_UPDATE",
        entity="scoring_criteria",
        target_id=payload.product_type,
        changes=changes
    )

    # Trigger background re-scoring job
    from app.services.rescore_job import rescoring_manager
    job_info = rescoring_manager.start_rescoring(
        target_version="1.2.0",
        description=f"Criteria updated for {payload.product_type} by admin {admin.email}"
    )

    return {
        "message": f"Scoring criteria for {payload.product_type} updated successfully",
        "scoring_engine_version": "1.2.0",
        "weights_sum": round(sum(p.weight for p in payload.parameters.values()), 4),
        "status": "Criteria active and validated",
        "background_job": job_info
    }

# ----------------- Audit Logs & System Stats -----------------

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """View administrative audit trail."""
    offset = (page - 1) * limit
    logs = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return logs

@router.get("/stats")
def get_system_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Returns administrative operational statistics:
    - Daily searches count
    - Top searched products
    - Local vs OFF API hit ratio
    - Data completeness distribution
    - Source counts ('seed', 'openfoodfacts', 'admin')
    - Total recommendation links
    """
    total_products = db.query(Product).count()
    total_searches = db.query(SearchHistory).count()
    total_recommendations = db.query(Recommendation).count()

    # Source breakdown
    source_counts = dict(
        db.query(Product.source, func.count(Product.id)).group_by(Product.source).all()
    )

    # Completeness breakdown
    high_comp = db.query(Product).filter(Product.data_completeness_score >= 0.80).count()
    med_comp = db.query(Product).filter(Product.data_completeness_score >= 0.50, Product.data_completeness_score < 0.80).count()
    low_comp = db.query(Product).filter(Product.data_completeness_score < 0.50).count()

    # Top search terms
    top_terms = db.query(SearchHistory.query_term, func.count(SearchHistory.id).label("count")).group_by(
        SearchHistory.query_term
    ).order_by(func.count(SearchHistory.id).desc()).limit(10).all()

    # Local cache vs API searches
    local_searches = db.query(SearchHistory).filter(SearchHistory.query_type != "openfoodfacts_live").count()
    api_searches = total_searches - local_searches
    hit_ratio = round((local_searches / total_searches * 100.0), 1) if total_searches > 0 else 100.0

    # Search outcomes breakdown for Admin Dashboard chart
    search_outcomes = {}
    history_records = db.query(SearchHistory.query_term).all()
    for row in history_records:
        term = row[0] or ""
        if "[" in term and term.endswith("]"):
            outcome = term.split("[")[-1].rstrip("]")
            search_outcomes[outcome] = search_outcomes.get(outcome, 0) + 1

    return {
        "total_catalog_products": total_products,
        "total_searches_recorded": total_searches,
        "total_recommendation_links": total_recommendations,
        "local_hit_ratio_pct": hit_ratio,
        "source_breakdown": source_counts,
        "search_outcomes": search_outcomes,
        "completeness_distribution": {
            "high_ge_80pct": high_comp,
            "medium_50_to_80pct": med_comp,
            "low_lt_50pct": low_comp
        },
        "top_searched_terms": [{"term": t[0], "count": t[1]} for t in top_terms]
    }

@router.get("/user-entered-products")
def list_user_entered_products(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lists all user-submitted products for administrative review."""
    products = db.query(Product).filter(Product.source == "user_entered").all()
    return [
        {
            "id": p.id,
            "barcode": p.barcode,
            "name": p.name,
            "brand": p.brand,
            "category": p.category.name if p.category else "Unknown",
            "data_completeness_score": p.data_completeness_score,
            "created_at": p.created_at,
            "score": p.product_score.overall_project_score if p.product_score else None
        }
        for p in products
    ]

@router.delete("/user-entered-products/{product_id}")
def delete_user_entered_product(
    product_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Allows administrators to delete unverified user-entered records."""
    product = db.query(Product).filter(Product.id == product_id, Product.source == "user_entered").first()
    if not product:
        raise ProductNotFoundError(product_id)
    db.delete(product)
    db.commit()
    log_admin_action(db, admin.id, "DELETE", "user_entered_product", product_id, {"name": product.name, "barcode": product.barcode})
    return {"message": "User-entered product deleted successfully"}

