"""Metadata routes for database schema information"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.api.schemas.entity import (
    TablesListResponse,
    TableInfoResponse,
    TableColumnInfo,
)
from app.services.database_metadata_service import DatabaseMetadataService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/tables", response_model=TablesListResponse)
def list_tables(
    db: Session = Depends(get_database),
):
    """
    List all tables in the database (for FK selection).

    Args:
        db: Database session

    Returns:
        List of table names
    """
    try:
        metadata_service = DatabaseMetadataService(db)
        tables = metadata_service.list_dynamic_tables()
        return TablesListResponse(tables=tables)
    except Exception as e:
        logger.error("failed_to_list_tables", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")


@router.get("/tables/{table_name}/columns", response_model=TableInfoResponse)
def get_table_columns(
    table_name: str,
    db: Session = Depends(get_database),
):
    """
    Get column information for a table.

    Args:
        table_name: Table name
        db: Database session

    Returns:
        Table information including columns and primary key

    Raises:
        HTTPException: If table not found or query fails
    """
    try:
        metadata_service = DatabaseMetadataService(db)
        table_info = metadata_service.get_table_info(table_name)

        return TableInfoResponse(
            table_name=table_info['table_name'],
            schema=table_info['schema'],
            columns=[
                TableColumnInfo(
                    column_name=col['column_name'],
                    data_type=col['data_type'],
                    is_nullable=col['is_nullable'],
                    column_default=col['column_default'],
                    max_length=col.get('max_length'),
                )
                for col in table_info['columns']
            ],
            primary_key=table_info['primary_key'],
        )
    except Exception as e:
        logger.error("failed_to_get_table_columns", table_name=table_name, error=str(e))
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found or error: {str(e)}")
