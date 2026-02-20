"""Import routes"""

import json
import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.api.schemas.import_job import (
    ImportJobResponse,
    ImportJobDetail,
    ImportJobCreateResponse,
    JobLogResponse,
)
from app.api.schemas.mapping import PreviewResponse, ImportJobCreateRequest
from app.services.import_service import ImportService
from app.services.spreadsheet_preview_service import SpreadsheetPreviewService
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.infrastructure.repositories.job_log_repository import JobLogRepository
from app.infrastructure.events.job_events import get_event_manager
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/preview", response_model=PreviewResponse, status_code=200)
async def preview_spreadsheet(
    file: UploadFile = File(...),
):
    """
    Preview spreadsheet file and return columns, types, and sample data.

    Args:
        file: CSV or Excel file

    Returns:
        Preview information with columns and sample rows
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Analyze file
        preview_service = SpreadsheetPreviewService()
        analysis = preview_service.analyze_file(
            file_bytes=file_content,
            filename=file.filename
        )

        return PreviewResponse(**analysis)
    except Exception as e:
        logger.error("failed_to_preview_file", error=str(e))
        raise


@router.post("", response_model=ImportJobCreateResponse, status_code=201)
async def create_import_job(
    file: UploadFile = File(...),
    mapping_config: Optional[str] = Form(None),
    template_id: Optional[str] = Form(None),
    db: Session = Depends(get_database),
):
    """
    Create a new import job from uploaded file.

    Args:
        file: CSV or Excel file
        mapping_config: Optional JSON string with mapping configuration
        template_id: Optional template ID to use
        db: Database session

    Returns:
        Created job information
    """
    import json as json_lib
    
    # Parse mapping_config if provided
    parsed_mapping_config = None
    if mapping_config:
        # Handle both string and already parsed dict (in case FastAPI auto-parses)
        if isinstance(mapping_config, str):
            if mapping_config.strip():
                try:
                    parsed_mapping_config = json_lib.loads(mapping_config)
                except json_lib.JSONDecodeError as e:
                    logger.warning("invalid_mapping_config_json", error=str(e), raw_value=mapping_config[:100])
                    parsed_mapping_config = None
        elif isinstance(mapping_config, dict):
            # Already parsed (shouldn't happen with Form(), but handle it)
            parsed_mapping_config = mapping_config
        
        # Validate parsed config
        if parsed_mapping_config:
            if not isinstance(parsed_mapping_config, dict) or not parsed_mapping_config:
                logger.warning("mapping_config_empty_dict")
                parsed_mapping_config = None
            elif 'columns' not in parsed_mapping_config or not parsed_mapping_config.get('columns'):
                logger.warning("mapping_config_missing_columns", keys=list(parsed_mapping_config.keys()))
                parsed_mapping_config = None
            elif not isinstance(parsed_mapping_config.get('columns'), list) or len(parsed_mapping_config['columns']) == 0:
                logger.warning("mapping_config_empty_columns")
                parsed_mapping_config = None

    logger.info(
        "creating_import_job",
        filename=file.filename,
        has_mapping_config=parsed_mapping_config is not None,
        has_template_id=template_id is not None,
        mapping_config_type=type(mapping_config).__name__ if mapping_config else None,
        template_id_value=template_id
    )

    service = ImportService(db)
    job_id = service.create_import_job(
        file,
        mapping_config=parsed_mapping_config,
        template_id=uuid.UUID(template_id) if template_id else None
    )

    return ImportJobCreateResponse(
        job_id=str(job_id),
        status="pending",
    )


@router.get("/stream")
async def stream_job_events(
    job_id: Optional[str] = Query(None, description="Optional job ID to stream specific job events"),
    db: Session = Depends(get_database)
):
    """
    Stream job events via Server-Sent Events (SSE).

    Args:
        job_id: Optional job ID to stream specific job events
        db: Database session

    Returns:
        SSE stream
    """
    event_manager = get_event_manager()

    async def event_generator():
        queue = await event_manager.subscribe(job_id)
        logger.info("sse_connection_opened", job_id=job_id)

        try:
            yield f"event: connected\ndata: {json.dumps({'message': 'Connected to job events stream'})}\n\n"

            # Send initial state if job_id is provided
            if job_id:
                try:
                    job_uuid = uuid.UUID(job_id)
                    job_repository = ImportJobRepository(db)
                    log_repository = JobLogRepository(db)

                    job = job_repository.get_by_id(job_uuid)
                    if job:
                        logs = log_repository.get_by_job_id(job_uuid)
                        initial_data = {
                            "id": str(job.id),
                            "filename": job.filename,
                            "status": job.status,
                            "total_rows": job.total_rows,
                            "processed_rows": job.processed_rows,
                            "error_rows": job.error_rows,
                            "started_at": job.started_at.isoformat() if job.started_at else None,
                            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                            "created_at": job.created_at.isoformat(),
                            "logs": [
                                {
                                    "id": str(log.id),
                                    "level": log.level,
                                    "message": log.message,
                                    "created_at": log.created_at.isoformat(),
                                }
                                for log in logs
                            ],
                        }
                        yield f"event: job_status\ndata: {json.dumps(initial_data)}\n\n"
                except ValueError:
                    yield f"event: error\ndata: {json.dumps({'error': 'Invalid job ID'})}\n\n"

            # Stream events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)

                    event_type = event.get("event_type", "message")
                    event_data = event.get("data", {})
                    job_id_str = event.get("job_id")

                    if job_id_str:
                        event_data["job_id"] = job_id_str

                    # Map event types to SSE event names
                    sse_event_type = event_type
                    if event_type == "status_update":
                        sse_event_type = "job_status"
                    elif event_type == "progress_update":
                        sse_event_type = "job_progress"
                    elif event_type == "log_update":
                        sse_event_type = "job_log"

                    logger.debug("sending_sse_event", event_type=sse_event_type, job_id=job_id_str)
                    message = f"event: {sse_event_type}\ndata: {json.dumps(event_data)}\n\n"
                    yield message

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                except Exception as e:
                    logger.error("sse_error", error=str(e))
                    yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await event_manager.unsubscribe(job_id, queue)
            logger.info("sse_connection_closed", job_id=job_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("", response_model=list[ImportJobResponse])
def list_import_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_database),
):
    """
    List import jobs with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        db: Database session

    Returns:
        List of import jobs
    """
    repository = ImportJobRepository(db)
    jobs = repository.list(skip=skip, limit=limit, status=status)

    return [
        ImportJobResponse(
            id=str(job.id),
            filename=job.filename,
            status=job.status,
            total_rows=job.total_rows,
            processed_rows=job.processed_rows,
            error_rows=job.error_rows,
            started_at=job.started_at,
            finished_at=job.finished_at,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=ImportJobDetail)
def get_import_job(
    job_id: str,
    db: Session = Depends(get_database),
):
    """
    Get import job details.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Import job details with logs

    Raises:
        NotFoundError: If job not found
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise NotFoundError(f"Job ID inválido: {job_id}")

    repository = ImportJobRepository(db)
    log_repository = JobLogRepository(db)

    job = repository.get_by_id(job_uuid)
    if not job:
        raise NotFoundError(f"Job não encontrado: {job_id}")

    logs = log_repository.get_by_job_id(job_uuid)

    return ImportJobDetail(
        id=str(job.id),
        filename=job.filename,
        status=job.status,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        error_rows=job.error_rows,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
        logs=[
            JobLogResponse(
                id=str(log.id),
                job_id=str(log.job_id),
                level=log.level,
                message=log.message,
                created_at=log.created_at,
            )
            for log in logs
        ],
    )
