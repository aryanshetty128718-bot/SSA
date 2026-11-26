import uuid
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductScore(Base):
    __tablename__ = "product_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_project_score = Column(Float, nullable=False)  # 0.0 - 100.0
    project_health_band = Column(String(30), nullable=False)  # 'Healthy' | 'Moderate' | 'Unhealthy'
    official_nutri_score_grade = Column(String(20), nullable=False)  # 'A', 'B', 'C', 'D', 'E' or 'NOT_COMPUTABLE'
    official_nutri_score_points = Column(Integer, nullable=True)  # None if not computable
    confidence_score = Column(Float, nullable=False)  # 0.0 - 1.0 (available data completeness)
    sub_scores_json = Column(Text, nullable=False)  # JSON-encoded dict of per-parameter sub-scores
    pros_json = Column(Text, nullable=False)  # JSON array of positive data-backed findings
    cons_json = Column(Text, nullable=False)  # JSON array of concern flags
    scoring_engine_version = Column(String(20), nullable=False, default="1.0.0")
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product", back_populates="scores")
