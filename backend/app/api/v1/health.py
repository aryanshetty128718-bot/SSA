from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings
from app.schemas.schemas import HealthCheck
from app.core.logging_config import logger

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthCheck)
def get_health_status(db: Session = Depends(get_db)):
    """Health check verifying database connectivity and service state."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.error(f"Health check DB ping failed: {e}")
        db_connected = False

    return HealthCheck(
        status="healthy" if db_connected else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )
