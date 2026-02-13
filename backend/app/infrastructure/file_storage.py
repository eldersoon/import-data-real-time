"""File storage for temporary uploads"""

import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileStorage:
    """Handles temporary file storage"""

    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file: UploadFile, job_id: uuid.UUID) -> str:
        """
        Save uploaded file temporarily.

        Args:
            file: Uploaded file
            job_id: Job UUID

        Returns:
            Path to saved file
        """
        file_ext = Path(file.filename).suffix if file.filename else '.csv'
        file_path = self.get_file_path(job_id, file_ext)

        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)

        logger.info("file_saved", job_id=str(job_id), file_path=str(file_path))
        return str(file_path)

    def get_file_path(self, job_id: uuid.UUID, file_ext: str) -> Path:
        """
        Get file path for a job.

        Args:
            job_id: Job UUID
            file_ext: File extension

        Returns:
            Path object
        """
        return self.upload_dir / f"{job_id}{file_ext}"

    def file_exists(self, job_id: uuid.UUID, file_ext: str) -> bool:
        """
        Check if file exists.

        Args:
            job_id: Job UUID
            file_ext: File extension

        Returns:
            True if file exists
        """
        file_path = self.get_file_path(job_id, file_ext)
        return file_path.exists()

    def delete_file(self, job_id: uuid.UUID, file_ext: str) -> None:
        """
        Delete file after processing.

        Args:
            job_id: Job UUID
            file_ext: File extension
        """
        file_path = self.get_file_path(job_id, file_ext)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("file_deleted", job_id=str(job_id), file_path=str(file_path))
        except Exception as e:
            logger.warning("failed_to_delete_file", job_id=str(job_id), error=str(e))
