import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class NutritionalInformation(Base):
    __tablename__ = "nutritional_information"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Nutritional values per 100g (solid) or per 100ml (beverage)
    # Strictly NULL when missing, NEVER 0!
    energy_kcal = Column(Float, nullable=True)
    energy_kj = Column(Float, nullable=True)
    fat_g = Column(Float, nullable=True)
    saturated_fat_g = Column(Float, nullable=True)
    trans_fat_g = Column(Float, nullable=True)
    carbohydrates_g = Column(Float, nullable=True)
    sugars_g = Column(Float, nullable=True)
    added_sugars_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    proteins_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    salt_g = Column(Float, nullable=True)
    fruits_vegetables_nuts_colza_walnut_olive_oils_pct = Column(Float, nullable=True)
    
    basis = Column(String(20), nullable=False, default="per 100g")  # 'per 100g' | 'per 100ml'
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="nutrition")
