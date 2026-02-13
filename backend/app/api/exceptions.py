"""FastAPI exception handlers"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import ValidationError, NotFoundError, ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Handle not found errors"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def processing_exception_handler(request: Request, exc: ProcessingError):
    """Handle processing errors"""
    logger.error("processing_error", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"},
    )
