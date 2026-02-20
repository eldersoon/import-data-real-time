"""Import service for handling file uploads and job creation"""

import uuid
import json
from typing import Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.domain.models.import_job import ImportJobStatus
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.infrastructure.repositories.import_template_repository import ImportTemplateRepository
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
        self.template_repository = ImportTemplateRepository(db)
        self.file_storage = FileStorage()
        self.sqs_publisher = SQSPublisher()
        self.parser = SpreadsheetParser()

    def create_import_job(
        self,
        file: UploadFile,
        mapping_config: Optional[Dict[str, Any]] = None,
        template_id: Optional[uuid.UUID] = None
    ) -> uuid.UUID:
        """
        Create a new import job from uploaded file.

        Args:
            file: Uploaded file
            mapping_config: Optional mapping configuration dict
            template_id: Optional template ID to use

        Returns:
            Job UUID

        Raises:
            ProcessingError: If file cannot be processed
        """
        try:
            # Resolve mapping config from template if template_id provided
            final_mapping_config = mapping_config
            final_template_id = template_id

            if template_id:
                template = self.template_repository.get_by_id(template_id)
                if not template:
                    raise ProcessingError(f"Template não encontrado: {template_id}")
                final_mapping_config = template.mapping_config
                final_template_id = template_id
                # Validate template mapping config
                if not final_mapping_config or not isinstance(final_mapping_config, dict):
                    raise ProcessingError(f"Template {template_id} não possui mapping_config válido")
                if 'columns' not in final_mapping_config or not final_mapping_config.get('columns'):
                    raise ProcessingError(f"Template {template_id} não possui colunas configuradas")
            elif mapping_config:
                # Validate inline mapping_config
                if not isinstance(mapping_config, dict):
                    raise ProcessingError("mapping_config deve ser um dicionário")
                if 'target_table' not in mapping_config:
                    raise ProcessingError("mapping_config deve conter 'target_table'")
                if 'columns' not in mapping_config or not isinstance(mapping_config.get('columns'), list):
                    raise ProcessingError("mapping_config deve conter 'columns' como uma lista")
                if len(mapping_config.get('columns', [])) == 0:
                    raise ProcessingError("mapping_config deve conter pelo menos uma coluna")
                final_template_id = None
            else:
                # No mapping config and no template - this is a legacy vehicle import
                final_mapping_config = None
                final_template_id = None

            # Log mapping config for debugging
            logger.info(
                "creating_job_with_config",
                filename=file.filename,
                has_mapping_config=final_mapping_config is not None,
                has_template_id=final_template_id is not None,
                mapping_config_keys=list(final_mapping_config.keys()) if final_mapping_config else None
            )

            # Create job record
            job = self.job_repository.create(
                filename=file.filename or "unknown",
                template_id=final_template_id,
                mapping_config=final_mapping_config
            )

            # Verify mapping_config was saved
            self.db.refresh(job)
            logger.info(
                "job_created",
                job_id=str(job.id),
                saved_mapping_config=job.mapping_config is not None,
                saved_template_id=job.template_id is not None
            )

            # Save file first (required for processing)
            try:
                file_path = self.file_storage.save_file(file, job.id)
                logger.info("file_saved", job_id=str(job.id), file_path=str(file_path))
            except Exception as e:
                logger.error("failed_to_save_file", job_id=str(job.id), error=str(e))
                raise ProcessingError(f"Falha ao salvar arquivo: {str(e)}")

            # Count total rows (skip validation for dynamic imports)
            try:
                # For dynamic imports, we don't validate columns, so count_rows should work
                # For legacy imports, count_rows will validate columns
                total_rows = self.parser.count_rows(file_path)
                job.total_rows = total_rows
                self.db.commit()
                self.db.refresh(job)
                logger.info("rows_counted", job_id=str(job.id), total_rows=total_rows)
            except Exception as e:
                # If counting fails due to missing columns and this is a dynamic import,
                # it's okay - we'll count during processing
                if job.mapping_config or job.template_id:
                    logger.info("skipping_row_count_for_dynamic_import", job_id=str(job.id), error=str(e))
                else:
                    logger.warning("failed_to_count_rows", job_id=str(job.id), error=str(e))
                # Continue even if counting fails - job will be created with total_rows=None

            # Publish to SQS - CRITICAL: This must succeed for the job to be processed
            try:
                self.sqs_publisher.publish_job(job.id)
                logger.info("job_published_to_sqs", job_id=str(job.id))
            except Exception as e:
                # Log error but don't fail job creation - job can be manually triggered later
                logger.error(
                    "failed_to_publish_job_to_sqs",
                    job_id=str(job.id),
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Still log success of job creation
                logger.warning(
                    "job_created_but_not_published",
                    job_id=str(job.id),
                    message="Job criado mas não foi publicado para SQS. Pode ser processado manualmente."
                )

            logger.info("import_job_created", job_id=str(job.id), filename=file.filename)
            return job.id

        except Exception as e:
            logger.error("failed_to_create_import_job", error=str(e))
            raise ProcessingError(f"Falha ao criar job de importação: {str(e)}")
