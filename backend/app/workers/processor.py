"""Job processor for handling import jobs"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import SessionLocal
from app.domain.models.import_job import ImportJobStatus
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.infrastructure.repositories.vehicle_repository import VehicleRepository
from app.infrastructure.repositories.job_log_repository import JobLogRepository
from app.infrastructure.file_storage import FileStorage
from app.services.spreadsheet_parser import SpreadsheetParser
from app.services.validation_service import ValidationService
from app.infrastructure.events.job_events import get_event_manager
from app.core.config import settings
from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class JobProcessor:
    """Processes import jobs"""

    def __init__(self):
        self.file_storage = FileStorage()
        self.parser = SpreadsheetParser()
        self.validator = ValidationService()
        self.event_manager = get_event_manager()
        self._last_progress_update: Dict[str, datetime] = {}

    def process_job(self, job_id: uuid.UUID) -> None:
        """
        Process an import job.

        Args:
            job_id: Job UUID

        Raises:
            ProcessingError: If processing fails
        """
        db: Session = SessionLocal()
        try:
            job_repository = ImportJobRepository(db)
            vehicle_repository = VehicleRepository(db)
            log_repository = JobLogRepository(db)

            job = job_repository.get_by_id(job_id)
            if not job:
                raise ProcessingError(f"Job não encontrado: {job_id}")

            # Determine file extension
            file_ext = Path(job.filename).suffix.lower() or '.csv'
            file_path = self.file_storage.get_file_path(job_id, file_ext)

            if not self.file_storage.file_exists(job_id, file_ext):
                raise ProcessingError(f"Arquivo não encontrado: {file_path}")

            # Update status to processing
            job_repository.update_status(
                job_id,
                ImportJobStatus.PROCESSING,
                started_at=datetime.utcnow()
            )
            self._publish_event_async(
                str(job_id),
                "status_update",
                {
                    "id": str(job_id),
                    "status": ImportJobStatus.PROCESSING,
                    "started_at": datetime.utcnow().isoformat(),
                    "filename": job.filename,
                    "total_rows": job.total_rows,
                    "processed_rows": job.processed_rows,
                    "error_rows": job.error_rows,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            log_repository.create(
                job_id,
                "info",
                f"Starting processing of {job.filename}"
            )

            total_processed = 0
            total_errors = 0
            batch_size = settings.batch_size

            # Process file in chunks
            for chunk_df in self.parser.read_file(str(file_path), chunk_size=batch_size):
                vehicles_to_insert = []
                batch_placas = []

                # Collect placas for batch duplicate check
                for _, row in chunk_df.iterrows():
                    placa = str(row.get('placa', '')).strip().upper()
                    if placa:
                        batch_placas.append(placa)

                # Check for duplicates in database
                existing_placas = vehicle_repository.get_placas_in_batch(batch_placas)
                existing_placas_set = set(existing_placas)

                # Also check for duplicates within the batch itself
                seen_in_batch = set()

                # Process each row
                for row_number, row in chunk_df.iterrows():
                    try:
                        row_dict = row.to_dict()
                        is_valid, errors = self.validator.validate_vehicle(row_dict, row_number)

                        placa = str(row_dict.get('placa', '')).strip().upper()

                        # Check duplicates
                        if placa in existing_placas_set or placa in seen_in_batch:
                            total_errors += 1
                            log_repository.create(
                                job_id,
                                "warning",
                                f"Linha {row_number + 1}: Placa '{placa}' duplicada"
                            )
                            continue

                        if not is_valid:
                            total_errors += 1
                            error_msg = f"Linha {row_number + 1}: {', '.join(errors)}"
                            log_repository.create(job_id, "error", error_msg)
                            continue

                        seen_in_batch.add(placa)

                        # Prepare vehicle data
                        vehicle_data = {
                            'job_id': job_id,
                            'modelo': str(row_dict['modelo']).strip(),
                            'placa': placa,
                            'ano': int(row_dict['ano']),
                            'valor_fipe': Decimal(str(row_dict['valor_fipe'])),
                        }
                        vehicles_to_insert.append(vehicle_data)

                    except Exception as e:
                        total_errors += 1
                        log_repository.create(
                            job_id,
                            "error",
                            f"Linha {row_number + 1}: Erro ao processar - {str(e)}"
                        )

                # Bulk insert valid vehicles
                if vehicles_to_insert:
                    vehicle_repository.create_bulk(vehicles_to_insert)
                    total_processed += len(vehicles_to_insert)

                # Update progress
                job_repository.update_progress(
                    job_id,
                    processed_rows=total_processed,
                    error_rows=total_errors
                )

                # Publish progress update event (throttled)
                if (datetime.utcnow() - self._last_progress_update.get(str(job_id), datetime.min)).total_seconds() >= 1:
                    self._publish_event_async(
                        str(job_id),
                        "progress_update",
                        {
                            "id": str(job_id),
                            "processed_rows": total_processed,
                            "total_rows": job.total_rows,
                            "error_rows": total_errors,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    self._last_progress_update[str(job_id)] = datetime.utcnow()

            # Update status to completed
            job_repository.update_status(
                job_id,
                ImportJobStatus.COMPLETED,
                finished_at=datetime.utcnow()
            )

            # Publish status update event
            self._publish_event_async(
                str(job_id),
                "status_update",
                {
                    "id": str(job_id),
                    "status": ImportJobStatus.COMPLETED,
                    "finished_at": datetime.utcnow().isoformat(),
                    "processed_rows": total_processed,
                    "total_rows": job.total_rows,
                    "error_rows": total_errors,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Publish a final progress update to ensure frontend has latest numbers
            self._publish_event_async(
                str(job_id),
                "progress_update",
                {
                    "id": str(job_id),
                    "processed_rows": total_processed,
                    "total_rows": job.total_rows,
                    "error_rows": total_errors,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            log_repository.create(
                job_id,
                "info",
                f"Processing completed. Processed: {total_processed}, Errors: {total_errors}"
            )

            # Delete file after processing
            self.file_storage.delete_file(job_id, file_ext)

            logger.info(
                "job_completed",
                job_id=str(job_id),
                processed=total_processed,
                errors=total_errors
            )

        except Exception as e:
            logger.error("job_processing_failed", job_id=str(job_id), error=str(e))

            # Update status to failed
            try:
                job_repository = ImportJobRepository(db)
                job_repository.update_status(
                    job_id,
                    ImportJobStatus.FAILED,
                    finished_at=datetime.utcnow()
                )

                log_repository = JobLogRepository(db)
                log_repository.create(
                    job_id,
                    "error",
                    f"Processing failed: {str(e)}"
                )

                # Publish failure event
                self._publish_event_async(
                    str(job_id),
                    "status_update",
                    {
                        "id": str(job_id),
                        "status": ImportJobStatus.FAILED,
                        "finished_at": datetime.utcnow().isoformat(),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as update_error:
                logger.error("failed_to_update_job_status", job_id=str(job_id), error=str(update_error))

            raise ProcessingError(f"Falha ao processar job: {str(e)}")
        finally:
            db.close()

    def _publish_event_async(self, job_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish event asynchronously (fire and forget).

        Args:
            job_id: Job ID
            event_type: Event type
            data: Event data
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the coroutine
                asyncio.create_task(self.event_manager.publish(job_id, event_type, data))
            else:
                # If no loop is running, run it
                loop.run_until_complete(self.event_manager.publish(job_id, event_type, data))
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(self.event_manager.publish(job_id, event_type, data))
        except Exception as e:
            logger.warning("failed_to_publish_event", job_id=job_id, error=str(e))
