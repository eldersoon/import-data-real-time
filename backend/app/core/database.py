"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create declarative base
Base = declarative_base()

# Create engine
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for getting database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
