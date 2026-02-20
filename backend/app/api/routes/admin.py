"""Admin routes"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.dependencies import get_database
from app.api.schemas.common import MessageResponse
from app.infrastructure.sqs.publisher import SQSPublisher
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.domain.models.import_job import ImportJobStatus
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.delete("/clear-data", response_model=MessageResponse)
def clear_all_data(db: Session = Depends(get_database)):
    """
    Clear all data (vehicles, jobs, logs) - for development/testing only.

    Args:
        db: Database session

    Returns:
        Success message
    """
    try:
        # Delete in order due to foreign key constraints
        db.execute(text("DELETE FROM imported_vehicles"))
        db.execute(text("DELETE FROM job_logs"))
        db.execute(text("DELETE FROM import_jobs"))
        db.commit()

        logger.warning("all_data_cleared")
        return MessageResponse(message="Todos os dados foram deletados com sucesso")
    except Exception as e:
        db.rollback()
        logger.error("failed_to_clear_data", error=str(e))
        raise


@router.post("/reprocess-job/{job_id}", response_model=MessageResponse)
def reprocess_job(job_id: str, db: Session = Depends(get_database)):
    """
    Manually reprocess a pending job by republishing it to SQS.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Success message
    """
    try:
        job_uuid = uuid.UUID(job_id)
        repository = ImportJobRepository(db)
        job = repository.get_by_id(job_uuid)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
        
        if job.status == ImportJobStatus.PROCESSING:
            raise HTTPException(status_code=400, detail=f"Job {job_id} já está sendo processado")
        
        # Republish to SQS
        publisher = SQSPublisher()
        publisher.publish_job(job_uuid)
        
        logger.info("job_republished", job_id=job_id)
        return MessageResponse(message=f"Job {job_id} republicado para processamento")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"ID de job inválido: {job_id}")
    except Exception as e:
        logger.error("failed_to_reprocess_job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao reprocessar job: {str(e)}")


@router.get("/sqs-status", response_model=dict)
def get_sqs_status():
    """
    Get SQS queue status and configuration.

    Returns:
        SQS status information
    """
    try:
        from app.core.config import settings
        from app.infrastructure.sqs.client import get_sqs_client
        
        client = get_sqs_client()
        queue_url = settings.sqs_queue_url
        
        # Try to get queue attributes
        try:
            response = client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            attributes = response.get('Attributes', {})
            
            return {
                "queue_url": queue_url,
                "status": "connected",
                "messages_available": int(attributes.get('ApproximateNumberOfMessages', 0)),
                "messages_in_flight": int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
            }
        except Exception as e:
            return {
                "queue_url": queue_url,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    except Exception as e:
        logger.error("failed_to_get_sqs_status", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
