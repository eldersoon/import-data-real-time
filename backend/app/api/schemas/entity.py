"""Entity API schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DynamicEntityResponse(BaseModel):
    """Dynamic entity metadata response"""
    id: str
    table_name: str
    display_name: str
    description: Optional[str] = None
    is_visible: bool
    icon: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by_job_id: Optional[str] = None

    class Config:
        from_attributes = True


class DynamicEntityUpdate(BaseModel):
    """Dynamic entity update schema"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_visible: Optional[bool] = None


class EntityDataResponse(BaseModel):
    """Generic entity data response (dict)"""
    data: Dict[str, Any]

    class Config:
        from_attributes = True


class PaginatedEntityDataResponse(BaseModel):
    """Paginated entity data response"""
    data: list[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class EntityDataCreate(BaseModel):
    """Entity data create request (dict)"""
    data: Dict[str, Any] = Field(..., description="Entity data as key-value pairs")


class EntityDataUpdate(BaseModel):
    """Entity data update request (dict)"""
    data: Dict[str, Any] = Field(..., description="Entity data to update as key-value pairs")


class TableColumnInfo(BaseModel):
    """Table column information"""
    column_name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None
    max_length: Optional[int] = None


class TableInfoResponse(BaseModel):
    """Table information response"""
    table_name: str
    schema: str
    columns: list[TableColumnInfo]
    primary_key: Optional[str] = None


class TablesListResponse(BaseModel):
    """List of tables response"""
    tables: list[str]
