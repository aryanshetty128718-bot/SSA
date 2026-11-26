import uuid
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    target_product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    alternative_product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)  # Combined Cosine + KNN similarity (0.0 - 1.0)
    score_improvement = Column(Float, nullable=False)  # Delta overall score
    parameter_deltas_json = Column(Text, nullable=False)  # JSON dict e.g. {"sugar": -45.0, "fiber": 120.0}
    explanation = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    target_product = relationship("Product", foreign_keys=[target_product_id], back_populates="recommendations_as_target")
    alternative_product = relationship("Product", foreign_keys=[alternative_product_id], back_populates="recommendations_as_alternative")
