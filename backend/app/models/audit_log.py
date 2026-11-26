import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    admin_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE', 'RE_SCORE', 'CRITERIA_UPDATE'
    target_entity = Column(String(50), nullable=False)  # 'product', 'category', 'scoring_criteria'
    target_id = Column(String(100), nullable=True)
    changes_json = Column(Text, nullable=True)  # JSON diff or metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    admin_user = relationship("User", back_populates="audit_logs")
