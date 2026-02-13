"""JobLog domain model"""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LogLevel(str, Enum):
    """Log level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class JobLog(Base):
    """Job log model"""

    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    job = relationship("ImportJob", backref="logs")

    __table_args__ = (
        CheckConstraint(
            "level IN ('info', 'warning', 'error')",
            name='check_level'
        ),
        Index('ix_job_logs_job_id', 'job_id'),
        Index('ix_job_logs_level', 'level'),
        Index('ix_job_logs_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<JobLog(id={self.id}, job_id={self.job_id}, level={self.level})>"
