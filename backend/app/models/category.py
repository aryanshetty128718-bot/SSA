from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    product_type = Column(String(20), nullable=False)  # 'solid' | 'beverage'
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Self-referential hierarchy
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    
    # Products in category
    products = relationship("Product", back_populates="category")
    scoring_criteria = relationship("ScoringCriteria", back_populates="category")
