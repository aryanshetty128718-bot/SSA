import uuid
from sqlalchemy import Column, String, Integer, Float, SmallInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    barcode = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    brand = Column(String(255), nullable=True, index=True)
    generic_name = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_type_id = Column(Integer, ForeignKey("product_types.id", ondelete="SET NULL"), nullable=True, index=True)
    serving_size = Column(String(100), nullable=True)
    image_url = Column(String(1024), nullable=True)
    packaging = Column(String(100), nullable=True)
    origin_country = Column(String(100), nullable=True)
    nova_group = Column(SmallInteger, nullable=True)  # 1, 2, 3, 4
    nutri_score_grade = Column(String(2), nullable=True)  # A, B, C, D, E
    data_completeness_score = Column(Float, nullable=False, default=0.0)  # 0.0 - 1.0
    data_source = Column(String(50), nullable=False, default="local_seed")  # 'local_seed' | 'open_food_facts'
    source = Column(String(50), nullable=False, default="seed")  # 'seed' | 'openfoodfacts' | 'admin'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="products")
    product_type_rel = relationship("ProductType", back_populates="products")
    category_tags = relationship("ProductCategoryTag", back_populates="product", cascade="all, delete-orphan", order_by="ProductCategoryTag.depth")
    nutrition = relationship("NutritionalInformation", back_populates="product", uselist=False, cascade="all, delete-orphan")
    product_ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan", order_by="ProductIngredient.position_order")
    scores = relationship("ProductScore", back_populates="product", cascade="all, delete-orphan")
    recommendations_as_target = relationship("Recommendation", foreign_keys="Recommendation.target_product_id", back_populates="target_product", cascade="all, delete-orphan")
    recommendations_as_alternative = relationship("Recommendation", foreign_keys="Recommendation.alternative_product_id", back_populates="alternative_product", cascade="all, delete-orphan")

    @property
    def product_score(self):
        """Returns the primary cached ProductScore entity if available."""
        return self.scores[0] if self.scores else None
