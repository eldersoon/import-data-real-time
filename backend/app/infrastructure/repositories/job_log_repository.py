"""Repository for JobLog operations"""

import uuid
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.models.job_log import JobLog, LogLevel
from app.core.logging import get_logger

logger = get_logger(__name__)


class JobLogRepository:
    """Repository for JobLog data access"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        job_id: uuid.UUID,
        level: LogLevel,
        message: str
    ) -> JobLog:
        """
        Create a new job log entry.

        Args:
            job_id: Job UUID
            level: Log level
            message: Log message

        Returns:
            Created JobLog instance
        """
        log = JobLog(
            job_id=job_id,
            level=level,
            message=message
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        logger.debug("job_log_created", job_id=str(job_id), level=level)
        return log

    def get_by_job_id(self, job_id: uuid.UUID) -> List[JobLog]:
        """
        Get all logs for a job.

        Args:
            job_id: Job UUID

        Returns:
            List of JobLog instances
        """
        return (
            self.db.query(JobLog)
            .filter(JobLog.job_id == job_id)
            .order_by(desc(JobLog.created_at))
            .all()
        )
