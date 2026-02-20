"""DynamicEntity domain model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DynamicEntity(Base):
    """Dynamic entity model for tracking dynamically created tables"""

    __tablename__ = "dynamic_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String, nullable=False, unique=True, index=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_visible = Column(Boolean, nullable=False, default=True)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index('ix_dynamic_entities_table_name', 'table_name'),
        Index('ix_dynamic_entities_is_visible', 'is_visible'),
        Index('ix_dynamic_entities_created_at', 'created_at'),
    )

    # Relationship
    job = relationship("ImportJob", backref="dynamic_entities")

    def __repr__(self):
        return f"<DynamicEntity(id={self.id}, table_name={self.table_name}, display_name={self.display_name}, is_visible={self.is_visible})>"
