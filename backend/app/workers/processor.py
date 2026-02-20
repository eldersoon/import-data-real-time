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
from app.services.mapping_service import MappingService
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
        self.mapping_service = MappingService()
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

            # Log initial job state
            logger.info(
                "job_retrieved_for_processing",
                job_id=str(job_id),
                filename=job.filename,
                template_id=str(job.template_id) if job.template_id else None,
                mapping_config_present=job.mapping_config is not None,
                mapping_config_type=type(job.mapping_config).__name__ if job.mapping_config else None,
                mapping_config_is_dict=isinstance(job.mapping_config, dict) if job.mapping_config else False
            )

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

            # Check if this is a dynamic import (has mapping_config or template_id)
            # IMPORTANT: Refresh job to ensure we have the latest mapping_config from DB
            db.refresh(job)
            mapping_config = job.mapping_config
            template_id = job.template_id
            
            # Handle case where mapping_config might be stored as string (shouldn't happen, but be safe)
            if isinstance(mapping_config, str):
                import json
                try:
                    mapping_config = json.loads(mapping_config)
                    logger.warning("mapping_config_was_string", job_id=str(job_id), message="converted_to_dict")
                except json.JSONDecodeError:
                    logger.error("mapping_config_invalid_json_string", job_id=str(job_id))
                    mapping_config = None
            
            # Log what we retrieved
            logger.info(
                "mapping_config_retrieved",
                job_id=str(job_id),
                mapping_config_type=type(mapping_config).__name__ if mapping_config else None,
                mapping_config_keys=list(mapping_config.keys()) if isinstance(mapping_config, dict) else None,
                template_id=str(template_id) if template_id else None
            )
            
            # If template_id exists but mapping_config is None, load from template
            if template_id and (mapping_config is None or not mapping_config or (isinstance(mapping_config, dict) and len(mapping_config) == 0)):
                from app.infrastructure.repositories.import_template_repository import ImportTemplateRepository
                template_repo = ImportTemplateRepository(db)
                template = template_repo.get_by_id(template_id)
                if template:
                    mapping_config = template.mapping_config
                    logger.info("loaded_mapping_from_template", job_id=str(job_id), template_id=str(template_id))
                else:
                    raise ProcessingError(
                        f"Template {template_id} não encontrado. Não é possível processar importação dinâmica sem template válido."
                    )
            
            # Check if mapping_config exists and is valid
            is_dynamic_import = (
                mapping_config is not None 
                and isinstance(mapping_config, dict) 
                and len(mapping_config) > 0
                and 'columns' in mapping_config
                and len(mapping_config.get('columns', [])) > 0
            )
            
            # Safety check: if template_id exists but we don't have valid mapping_config, fail early
            if template_id and not is_dynamic_import:
                raise ProcessingError(
                    f"Job {job_id} tem template_id ({template_id}) mas não possui mapping_config válido. "
                    "Não é possível processar como importação dinâmica."
                )

            logger.info(
                "processing_job",
                job_id=str(job_id),
                has_mapping_config=mapping_config is not None,
                is_dynamic_import=is_dynamic_import,
                template_id=str(template_id) if template_id else None,
                mapping_config_type=type(mapping_config).__name__ if mapping_config else None,
                mapping_config_value=str(mapping_config)[:200] if mapping_config else None
            )

            # CRITICAL: If job was created with template_id or mapping_config but we can't use it,
            # fail instead of falling back to vehicle import (which would validate wrong columns)
            if (template_id or (mapping_config is not None and mapping_config != {} and isinstance(mapping_config, dict))) and not is_dynamic_import:
                error_msg = (
                    f"Job {job_id} foi criado como importação dinâmica "
                    f"(template_id={template_id}, mapping_config presente={mapping_config is not None}), "
                    f"mas a configuração não é válida para processamento. "
                    f"mapping_config type: {type(mapping_config).__name__}, "
                    f"is_dict: {isinstance(mapping_config, dict)}, "
                    f"has_columns: {'columns' in mapping_config if isinstance(mapping_config, dict) else False}, "
                    f"columns_count: {len(mapping_config.get('columns', [])) if isinstance(mapping_config, dict) and 'columns' in mapping_config else 0}. "
                    "Não é possível processar como importação de veículos. "
                    "Verifique se o mapping_config foi salvo corretamente no banco de dados."
                )
                logger.error("dynamic_import_config_invalid", job_id=str(job_id), error_details=error_msg)
                raise ProcessingError(error_msg)

            if is_dynamic_import:
                # Validate mapping config
                is_valid, errors = self.mapping_service.validate_mapping(mapping_config)
                if not is_valid:
                    raise ProcessingError(f"Invalid mapping config: {', '.join(errors)}")

                # Create table if needed (pass job_id and entity metadata to link DynamicEntity to job)
                entity_display_name = mapping_config.get('entity_display_name')
                entity_description = mapping_config.get('entity_description')
                entity_icon = mapping_config.get('entity_icon')
                self.mapping_service.create_table_if_needed(
                    db, 
                    mapping_config, 
                    job_id=job_id,
                    entity_display_name=entity_display_name,
                    entity_description=entity_description,
                    entity_icon=entity_icon
                )

                # Process with dynamic mapping
                total_processed, total_errors = self._process_dynamic_import(
                    db, job_id, job, file_path, mapping_config, batch_size,
                    job_repository, log_repository
                )
            else:
                # Legacy vehicle import processing
                total_processed, total_errors = self._process_vehicle_import(
                    db, job_id, job, file_path, batch_size,
                    job_repository, vehicle_repository, log_repository
                )

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

    def _process_vehicle_import(
        self,
        db: Session,
        job_id: uuid.UUID,
        job: Any,
        file_path: Path,
        batch_size: int,
        job_repository: ImportJobRepository,
        vehicle_repository: VehicleRepository,
        log_repository: Any
    ) -> tuple[int, int]:
        """Process legacy vehicle import."""
        total_processed = 0
        total_errors = 0

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

        return total_processed, total_errors

    def _process_dynamic_import(
        self,
        db: Session,
        job_id: uuid.UUID,
        job: Any,
        file_path: Path,
        mapping_config: Dict[str, Any],
        batch_size: int,
        job_repository: ImportJobRepository,
        log_repository: Any
    ) -> tuple[int, int]:
        """Process dynamic import with mapping configuration."""
        from sqlalchemy import text
        
        total_processed = 0
        total_errors = 0
        target_table = mapping_config['target_table']
        columns_mapping = {col['sheet_column']: col for col in mapping_config['columns']}

        # Process file in chunks with mapping
        for chunk_df in self.parser.read_file_with_mapping(str(file_path), mapping_config, chunk_size=batch_size):
            rows_to_insert = []

            # Process each row
            for row_number, row in chunk_df.iterrows():
                try:
                    row_dict = row.to_dict()
                    row_data = {}
                    errors = []

                    # Process each mapped column
                    for col_config in mapping_config['columns']:
                        db_col = col_config['db_column']
                        col_type = col_config['type']
                        required = col_config.get('required', False)
                        
                        # Get value from row (already mapped to db_column name)
                        value = row_dict.get(db_col)

                        # Check required
                        if required and (value is None or (isinstance(value, str) and value.strip() == '')):
                            errors.append(f"Campo '{db_col}' é obrigatório")
                            continue

                        # Convert value
                        if value is not None:
                            try:
                                if col_type == 'fk':
                                    # Resolve foreign key
                                    fk_config = col_config['fk']
                                    fk_value = self.mapping_service.resolve_foreign_key(
                                        db, fk_config, value
                                    )
                                    row_data[db_col] = fk_value
                                else:
                                    # Convert to target type
                                    converted_value = self.mapping_service.convert_value(value, col_type)
                                    row_data[db_col] = converted_value
                            except Exception as e:
                                errors.append(f"Erro ao converter '{db_col}': {str(e)}")

                    if errors:
                        total_errors += 1
                        error_msg = f"Linha {row_number + 1}: {', '.join(errors)}"
                        log_repository.create(job_id, "error", error_msg)
                        continue

                    rows_to_insert.append(row_data)

                except Exception as e:
                    total_errors += 1
                    log_repository.create(
                        job_id,
                        "error",
                        f"Linha {row_number + 1}: Erro ao processar - {str(e)}"
                    )

            # Bulk insert using raw SQL
            if rows_to_insert:
                try:
                    # Build INSERT statement
                    db_columns = [col['db_column'] for col in mapping_config['columns']]
                    placeholders = ', '.join([f':{col}' for col in db_columns])
                    columns_str = ', '.join(db_columns)
                    
                    insert_sql = f"INSERT INTO {target_table} ({columns_str}) VALUES ({placeholders})"
                    
                    # Execute bulk insert
                    for row_data in rows_to_insert:
                        db.execute(text(insert_sql), row_data)
                    
                    db.commit()
                    total_processed += len(rows_to_insert)
                except Exception as e:
                    db.rollback()
                    total_errors += len(rows_to_insert)
                    log_repository.create(
                        job_id,
                        "error",
                        f"Erro ao inserir lote: {str(e)}"
                    )

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

        return total_processed, total_errors

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
