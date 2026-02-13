"""Repository for ImportJob operations"""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.models.import_job import ImportJob, ImportJobStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImportJobRepository:
    """Repository for ImportJob data access"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, filename: str) -> ImportJob:
        """
        Create a new import job.

        Args:
            filename: File name

        Returns:
            Created ImportJob instance
        """
        job = ImportJob(filename=filename)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info("import_job_created", job_id=str(job.id), filename=filename)
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Optional[ImportJob]:
        """
        Get a job by ID.

        Args:
            job_id: Job UUID

        Returns:
            ImportJob instance or None
        """
        return self.db.query(ImportJob).filter(ImportJob.id == job_id).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[ImportJob]:
        """
        List jobs with pagination and optional status filter.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of ImportJob instances
        """
        query = self.db.query(ImportJob)

        if status:
            query = query.filter(ImportJob.status == status)

        return query.order_by(desc(ImportJob.created_at)).offset(skip).limit(limit).all()

    def update_status(
        self,
        job_id: uuid.UUID,
        status: ImportJobStatus,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None
    ) -> None:
        """
        Update job status.

        Args:
            job_id: Job UUID
            status: New status
            started_at: Optional start time
            finished_at: Optional finish time
        """
        job = self.get_by_id(job_id)
        if job:
            job.status = status
            if started_at:
                job.started_at = started_at
            if finished_at:
                job.finished_at = finished_at
            self.db.commit()
            self.db.refresh(job)

            logger.info("job_status_updated", job_id=str(job_id), status=status)

    def update_progress(
        self,
        job_id: uuid.UUID,
        processed_rows: int,
        error_rows: int
    ) -> None:
        """
        Update job progress.

        Args:
            job_id: Job UUID
            processed_rows: Number of processed rows
            error_rows: Number of error rows
        """
        job = self.get_by_id(job_id)
        if job:
            job.processed_rows = processed_rows
            job.error_rows = error_rows
            self.db.commit()
            self.db.refresh(job)

            logger.debug(
                "job_progress_updated",
                job_id=str(job_id),
                processed_rows=processed_rows,
                error_rows=error_rows
            )
