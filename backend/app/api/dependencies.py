"""FastAPI dependencies"""

from sqlalchemy.orm import Session
from app.core.database import get_db


def get_database() -> Session:
    """
    Dependency for getting database session.

    Yields:
        Database session
    """
    yield from get_db()
