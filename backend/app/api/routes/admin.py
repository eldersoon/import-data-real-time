"""Admin routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.dependencies import get_database
from app.api.schemas.common import MessageResponse
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
