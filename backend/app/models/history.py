import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    query_term = Column(String(255), nullable=False)
    query_type = Column(String(50), nullable=False)  # 'barcode' | 'text' | 'category'
    outcome = Column(String(50), nullable=True, default="found_local")  # 'found_local' | 'found_off' | 'found_usda' | 'manual_entry' | failure causes
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="search_history")
    product = relationship("Product")
