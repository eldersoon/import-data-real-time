"""Import service for handling file uploads and job creation"""

import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.domain.models.import_job import ImportJobStatus
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.infrastructure.file_storage import FileStorage
from app.infrastructure.sqs.publisher import SQSPublisher
from app.services.spreadsheet_parser import SpreadsheetParser
from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImportService:
    """Service for handling import operations"""

    def __init__(self, db: Session):
        self.db = db
        self.job_repository = ImportJobRepository(db)
        self.file_storage = FileStorage()
        self.sqs_publisher = SQSPublisher()
        self.parser = SpreadsheetParser()

    def create_import_job(self, file: UploadFile) -> uuid.UUID:
        """
        Create a new import job from uploaded file.

        Args:
            file: Uploaded file

        Returns:
            Job UUID

        Raises:
            ProcessingError: If file cannot be processed
        """
        try:
            # Create job record
            job = self.job_repository.create(filename=file.filename or "unknown")

            # Count total rows
            try:
                # Save file temporarily to count rows
                file_path = self.file_storage.save_file(file, job.id)
                total_rows = self.parser.count_rows(file_path)
                job.total_rows = total_rows
                self.db.commit()
                self.db.refresh(job)
            except Exception as e:
                logger.warning("failed_to_count_rows", job_id=str(job.id), error=str(e))
                # Continue even if counting fails

            # Publish to SQS
            self.sqs_publisher.publish_job(job.id)

            logger.info("import_job_created", job_id=str(job.id), filename=file.filename)
            return job.id

        except Exception as e:
            logger.error("failed_to_create_import_job", error=str(e))
            raise ProcessingError(f"Falha ao criar job de importação: {str(e)}")
