import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductIngredient(Base):
    __tablename__ = "product_ingredients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = Column(String(36), ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False, index=True)
    position_order = Column(Integer, nullable=False)  # 1-indexed order on label
    estimated_percentage = Column(Float, nullable=True)
    is_whole_grain = Column(Boolean, nullable=False, default=False)
    is_allergen = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("product_id", "ingredient_id", name="uq_product_ingredient"),
    )

    product = relationship("Product", back_populates="product_ingredients")
    ingredient = relationship("Ingredient", back_populates="product_ingredients")
