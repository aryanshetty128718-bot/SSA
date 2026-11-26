from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ScoringCriteria(Base):
    __tablename__ = "scoring_criteria"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    product_type = Column(String(20), nullable=False)  # 'solid' | 'beverage'
    parameter_name = Column(String(50), nullable=False)  # 'sugar', 'sodium', 'saturated_fat', etc.
    weight = Column(Float, nullable=False)
    low_threshold = Column(Float, nullable=False)  # Green cut-off
    medium_threshold = Column(Float, nullable=False)  # Amber cut-off
    high_threshold = Column(Float, nullable=False)  # Red cut-off
    unit = Column(String(20), nullable=False)  # 'g', 'mg', 'kcal'
    polarity = Column(String(20), nullable=False)  # 'negative' (lower is better) | 'positive' (higher is better)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("Category", back_populates="scoring_criteria")
