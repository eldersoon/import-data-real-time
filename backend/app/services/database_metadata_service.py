"""Database metadata service for querying table and column information"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseMetadataService:
    """Service for querying database metadata (tables, columns, etc.)"""

    # Whitelist of allowed schemas (for security)
    ALLOWED_SCHEMAS = ['public']

    def __init__(self, db: Session):
        self.db = db

    def get_table_columns(self, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
        """
        Get column information for a table.

        Args:
            table_name: Table name
            schema: Schema name (default: 'public')

        Returns:
            List of column info dicts with keys: column_name, data_type, is_nullable, column_default

        Raises:
            ProcessingError: If table doesn't exist or query fails
        """
        if schema not in self.ALLOWED_SCHEMAS:
            raise ProcessingError(f"Schema '{schema}' is not allowed")

        try:
            query = text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table_name
                ORDER BY ordinal_position
            """)

            result = self.db.execute(query, {"schema": schema, "table_name": table_name})
            columns = []
            for row in result:
                columns.append({
                    "column_name": row.column_name,
                    "data_type": row.data_type,
                    "is_nullable": row.is_nullable == 'YES',
                    "column_default": row.column_default,
                    "max_length": row.character_maximum_length,
                })

            if not columns:
                raise ProcessingError(f"Table '{table_name}' not found in schema '{schema}'")

            return columns

        except SQLAlchemyError as e:
            logger.error("failed_to_get_table_columns", table_name=table_name, error=str(e))
            raise ProcessingError(f"Failed to get columns for table '{table_name}': {str(e)}")

    def get_table_primary_key(self, table_name: str, schema: str = 'public') -> Optional[str]:
        """
        Get primary key column name for a table.

        Args:
            table_name: Table name
            schema: Schema name (default: 'public')

        Returns:
            Primary key column name or None if no PK exists
        """
        if schema not in self.ALLOWED_SCHEMAS:
            raise ProcessingError(f"Schema '{schema}' is not allowed")

        try:
            inspector = inspect(self.db.bind)
            pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
            if pk_constraint and pk_constraint.get('constrained_columns'):
                return pk_constraint['constrained_columns'][0]
            return None

        except Exception as e:
            logger.error("failed_to_get_primary_key", table_name=table_name, error=str(e))
            return None

    def list_dynamic_tables(self, schema: str = 'public') -> List[str]:
        """
        List all tables in the database (for FK selection).

        Args:
            schema: Schema name (default: 'public')

        Returns:
            List of table names
        """
        if schema not in self.ALLOWED_SCHEMAS:
            raise ProcessingError(f"Schema '{schema}' is not allowed")

        try:
            inspector = inspect(self.db.bind)
            tables = inspector.get_table_names(schema=schema)
            return tables

        except Exception as e:
            logger.error("failed_to_list_tables", schema=schema, error=str(e))
            raise ProcessingError(f"Failed to list tables: {str(e)}")

    def validate_table_exists(self, table_name: str, schema: str = 'public') -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Table name
            schema: Schema name (default: 'public')

        Returns:
            True if table exists, False otherwise
        """
        if schema not in self.ALLOWED_SCHEMAS:
            return False

        try:
            inspector = inspect(self.db.bind)
            return inspector.has_table(table_name, schema=schema)

        except Exception as e:
            logger.error("failed_to_validate_table", table_name=table_name, error=str(e))
            return False

    def get_table_info(self, table_name: str, schema: str = 'public') -> Dict[str, Any]:
        """
        Get comprehensive table information including columns and primary key.

        Args:
            table_name: Table name
            schema: Schema name (default: 'public')

        Returns:
            Dict with keys: table_name, columns, primary_key
        """
        columns = self.get_table_columns(table_name, schema)
        primary_key = self.get_table_primary_key(table_name, schema)

        return {
            "table_name": table_name,
            "schema": schema,
            "columns": columns,
            "primary_key": primary_key,
        }
