import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductCategoryTag(Base):
    __tablename__ = "product_category_tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(255), nullable=False, index=True)
    depth = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("product_id", "tag", name="uq_product_category_tag"),
    )

    product = relationship("Product", back_populates="category_tags")
