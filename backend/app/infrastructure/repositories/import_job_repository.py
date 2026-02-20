"""Repository for ImportJob operations"""

import uuid
from typing import List, Optional, Dict, Any
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

    def create(
        self,
        filename: str,
        template_id: Optional[uuid.UUID] = None,
        mapping_config: Optional[Dict[str, Any]] = None
    ) -> ImportJob:
        """
        Create a new import job.

        Args:
            filename: File name
            template_id: Optional template ID
            mapping_config: Optional mapping configuration

        Returns:
            Created ImportJob instance
        """
        # Validate and normalize mapping_config
        final_mapping_config = None
        if mapping_config:
            if isinstance(mapping_config, dict) and len(mapping_config) > 0:
                # Ensure it has required structure
                if 'columns' in mapping_config and isinstance(mapping_config.get('columns'), list):
                    if len(mapping_config['columns']) > 0:
                        final_mapping_config = mapping_config
                    else:
                        logger.warning("mapping_config_has_empty_columns", filename=filename)
                else:
                    logger.warning("mapping_config_missing_columns", filename=filename)
            else:
                logger.warning("mapping_config_invalid_format", filename=filename, config_type=type(mapping_config).__name__)

        job = ImportJob(
            filename=filename,
            template_id=template_id,
            mapping_config=final_mapping_config
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Verify what was saved
        logger.info(
            "import_job_created",
            job_id=str(job.id),
            filename=filename,
            has_template_id=job.template_id is not None,
            has_mapping_config=job.mapping_config is not None,
            mapping_config_type=type(job.mapping_config).__name__ if job.mapping_config else None,
            mapping_config_keys=list(job.mapping_config.keys()) if job.mapping_config and isinstance(job.mapping_config, dict) else None
        )
        return job

    def get_by_id(self, job_id: uuid.UUID) -> Optional[ImportJob]:
        """
        Get a job by ID.

        Args:
            job_id: Job UUID

        Returns:
            ImportJob instance or None
        """
        job = self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if job:
            # Log what was retrieved for debugging
            logger.debug(
                "job_retrieved",
                job_id=str(job_id),
                has_template_id=job.template_id is not None,
                has_mapping_config=job.mapping_config is not None,
                mapping_config_type=type(job.mapping_config).__name__ if job.mapping_config else None
            )
        return job

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
