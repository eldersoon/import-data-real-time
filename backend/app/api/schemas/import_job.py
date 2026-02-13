"""Import job API schemas"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.domain.models.import_job import ImportJobStatus


class ImportJobBase(BaseModel):
    """Base import job schema"""
    filename: str
    status: str


class ImportJobCreateResponse(BaseModel):
    """Import job creation response"""
    job_id: str
    status: str

    class Config:
        from_attributes = True


class ImportJobResponse(BaseModel):
    """Import job response"""
    id: str
    filename: str
    status: str
    total_rows: Optional[int]
    processed_rows: int
    error_rows: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class JobLogResponse(BaseModel):
    """Job log response"""
    id: str
    job_id: str
    level: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImportJobDetail(ImportJobResponse):
    """Import job detail with logs"""
    logs: List[JobLogResponse] = []
