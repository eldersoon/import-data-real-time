"""ImportTemplate domain model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ImportTemplate(Base):
    """Import template model for storing reusable import configurations"""

    __tablename__ = "import_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    target_table = Column(String, nullable=False)
    create_table = Column(Boolean, nullable=False, default=False)
    mapping_config = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    jobs = relationship("ImportJob", backref="template")

    __table_args__ = (
        Index('ix_import_templates_name', 'name'),
        Index('ix_import_templates_target_table', 'target_table'),
        Index('ix_import_templates_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ImportTemplate(id={self.id}, name={self.name}, target_table={self.target_table})>"
