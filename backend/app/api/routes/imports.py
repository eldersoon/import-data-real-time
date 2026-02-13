"""Import routes"""

import json
import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.api.schemas.import_job import (
    ImportJobResponse,
    ImportJobDetail,
    ImportJobCreateResponse,
    JobLogResponse,
)
from app.services.import_service import ImportService
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.infrastructure.repositories.job_log_repository import JobLogRepository
from app.infrastructure.events.job_events import get_event_manager
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("", response_model=ImportJobCreateResponse, status_code=201)
async def create_import_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_database),
):
    """
    Create a new import job from uploaded file.

    Args:
        file: CSV or Excel file
        db: Database session

    Returns:
        Created job information
    """
    service = ImportService(db)
    job_id = service.create_import_job(file)

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
