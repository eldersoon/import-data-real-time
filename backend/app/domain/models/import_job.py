"""ImportJob domain model"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ImportJobStatus(str, Enum):
    """Import job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportJob(Base):
    """Import job model"""

    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default=ImportJobStatus.PENDING)
    total_rows = Column(Integer, nullable=True)
    processed_rows = Column(Integer, nullable=False, default=0)
    error_rows = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name='check_status'
        ),
        Index('ix_import_jobs_status', 'status'),
        Index('ix_import_jobs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<ImportJob(id={self.id}, filename={self.filename}, status={self.status})>"
