"""FastAPI application entry point"""

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.database import Base, engine
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    ProcessingError,
)
from app.api.exceptions import (
    validation_exception_handler,
    not_found_exception_handler,
    processing_exception_handler,
    general_exception_handler,
)
from app.api.routes import imports, vehicles, admin, templates, entities, metadata
from app.infrastructure.events.job_monitor import get_monitor

# Configure logging
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger.info("starting_job_monitor")
    monitor = get_monitor()
    asyncio.create_task(monitor.start_monitoring_all_jobs())
    yield
    logger.info("stopping_job_monitor")
    await monitor.stop_monitoring_all_jobs()


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(NotFoundError, not_found_exception_handler)
app.add_exception_handler(ProcessingError, processing_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(imports.router, prefix=settings.api_prefix)
app.include_router(vehicles.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(templates.router, prefix=settings.api_prefix)
app.include_router(entities.router, prefix=settings.api_prefix)
app.include_router(metadata.router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("application_starting", version=settings.api_version)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("application_shutting_down")
