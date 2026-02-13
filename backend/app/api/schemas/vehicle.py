"""Vehicle API schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class VehicleBase(BaseModel):
    """Base vehicle schema"""
    modelo: str
    placa: str
    ano: int
    valor_fipe: Decimal = Field(..., decimal_places=2)


class VehicleResponse(BaseModel):
    """Vehicle response"""
    id: str
    job_id: str
    modelo: str
    placa: str
    ano: int
    valor_fipe: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleUpdate(BaseModel):
    """Vehicle update schema"""
    modelo: Optional[str] = None
    valor_fipe: Optional[float] = Field(None, gt=0)


class PaginatedVehicleResponse(BaseModel):
    """Paginated vehicle response"""
    data: list[VehicleResponse]
    total: int
    page: int
    page_size: int
