"""Job log API schemas"""

from datetime import datetime
from pydantic import BaseModel


class JobLogResponse(BaseModel):
    """Job log response"""
    id: str
    job_id: str
    level: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
