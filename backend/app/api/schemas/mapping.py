"""Mapping configuration API schemas"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ForeignKeyConfig(BaseModel):
    """Foreign key configuration schema"""
    table: str = Field(..., description="Target table name")
    lookup_column: str = Field(..., description="Column to lookup in target table")
    on_missing: str = Field(default="error", description="Action when FK not found: 'create', 'ignore', 'error'")

    @validator('on_missing')
    def validate_on_missing(cls, v):
        allowed = ['create', 'ignore', 'error']
        if v not in allowed:
            raise ValueError(f"on_missing must be one of {allowed}")
        return v


class ColumnMapping(BaseModel):
    """Column mapping schema"""
    sheet_column: str = Field(..., description="Column name in spreadsheet")
    db_column: str = Field(..., description="Column name in database")
    type: str = Field(..., description="Data type: string, int, float, decimal, date, datetime, boolean, fk")
    required: bool = Field(default=False, description="Whether column is required")
    fk: Optional[ForeignKeyConfig] = Field(None, description="Foreign key configuration (if type is 'fk')")

    @validator('type')
    def validate_type(cls, v):
        allowed = ['string', 'int', 'float', 'decimal', 'date', 'datetime', 'boolean', 'fk']
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}")
        return v

    @validator('fk')
    def validate_fk(cls, v, values):
        if v is not None and values.get('type') != 'fk':
            raise ValueError("fk config can only be set when type is 'fk'")
        if values.get('type') == 'fk' and v is None:
            raise ValueError("fk config is required when type is 'fk'")
        return v


class MappingConfig(BaseModel):
    """Complete mapping configuration schema"""
    target_table: str = Field(..., description="Target database table name")
    create_table: bool = Field(default=False, description="Whether to create table if it doesn't exist")
    columns: List[ColumnMapping] = Field(..., description="List of column mappings")

    @validator('target_table')
    def validate_table_name(cls, v):
        # Basic validation: no SQL injection patterns
        if not v or len(v.strip()) == 0:
            raise ValueError("target_table cannot be empty")
        # Only allow alphanumeric, underscore, and dot (for schema.table)
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', v):
            raise ValueError("target_table contains invalid characters")
        return v

    @validator('columns')
    def validate_columns(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one column mapping is required")
        return v


class ColumnInfo(BaseModel):
    """Column information from preview"""
    name: str
    suggested_type: str
    sample_values: List[Any]
    null_count: int
    total_count: int


class PreviewResponse(BaseModel):
    """Spreadsheet preview response"""
    columns: List[ColumnInfo]
    preview_rows: List[Dict[str, Any]]
    total_rows: int
    total_columns: int


class ImportJobCreateRequest(BaseModel):
    """Import job creation request with optional mapping"""
    mapping_config: Optional[MappingConfig] = Field(None, description="Optional mapping configuration")
    template_id: Optional[str] = Field(None, description="Optional template ID to use")
