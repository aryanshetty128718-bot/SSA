import uuid
from sqlalchemy import Column, String, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    canonical_name = Column(String(255), unique=True, nullable=False, index=True)
    ins_number = Column(String(20), nullable=True, index=True)  # e.g., 'E950', 'INS 330'
    is_additive = Column(Boolean, nullable=False, default=False)
    additive_type = Column(String(50), nullable=True)  # 'sweetener' | 'preservative' | 'color' | 'flavor'
    health_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product_ingredients = relationship("ProductIngredient", back_populates="ingredient", cascade="all, delete-orphan")
