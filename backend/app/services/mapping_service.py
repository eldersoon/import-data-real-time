"""Mapping service for handling dynamic import mappings"""

import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import ProcessingError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MappingService:
    """Service for handling import mappings, FK resolution, and dynamic table creation"""

    # Whitelist of allowed types
    ALLOWED_TYPES = ['string', 'int', 'float', 'decimal', 'date', 'datetime', 'boolean', 'fk']

    # Whitelist of allowed schemas (for security)
    ALLOWED_SCHEMAS = ['public']

    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """
        Validate table name to prevent SQL injection.

        Args:
            table_name: Table name to validate

        Returns:
            True if valid
        """
        # Only allow alphanumeric, underscore, and dot (for schema.table)
        if not table_name or len(table_name.strip()) == 0:
            return False
        
        # Check if schema.table format
        parts = table_name.split('.')
        if len(parts) > 2:
            return False
        
        if len(parts) == 2:
            schema, table = parts
            if schema not in cls.ALLOWED_SCHEMAS:
                return False
            table_name = table
        
        # Validate table name pattern
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return False
        
        return True

    @classmethod
    def validate_column_name(cls, column_name: str) -> bool:
        """
        Validate column name to prevent SQL injection.

        Args:
            column_name: Column name to validate

        Returns:
            True if valid
        """
        if not column_name or len(column_name.strip()) == 0:
            return False
        # Only allow alphanumeric and underscore
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name))

    @classmethod
    def validate_mapping(cls, mapping_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate mapping configuration.

        Args:
            mapping_config: Mapping configuration dict

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate target_table
        target_table = mapping_config.get('target_table')
        if not target_table:
            errors.append("target_table is required")
        elif not cls.validate_table_name(target_table):
            errors.append(f"Invalid target_table name: {target_table}")

        # Validate columns
        columns = mapping_config.get('columns', [])
        if not columns or len(columns) == 0:
            errors.append("At least one column mapping is required")

        seen_db_columns = set()
        for idx, col in enumerate(columns):
            # Validate sheet_column
            sheet_col = col.get('sheet_column')
            if not sheet_col:
                errors.append(f"Column {idx}: sheet_column is required")
            
            # Validate db_column
            db_col = col.get('db_column')
            if not db_col:
                errors.append(f"Column {idx}: db_column is required")
            elif not cls.validate_column_name(db_col):
                errors.append(f"Column {idx}: Invalid db_column name: {db_col}")
            elif db_col in seen_db_columns:
                errors.append(f"Column {idx}: Duplicate db_column: {db_col}")
            else:
                seen_db_columns.add(db_col)

            # Validate type
            col_type = col.get('type')
            if not col_type:
                errors.append(f"Column {idx}: type is required")
            elif col_type not in cls.ALLOWED_TYPES:
                errors.append(f"Column {idx}: Invalid type: {col_type}")

            # Validate FK config if type is fk
            if col_type == 'fk':
                fk_config = col.get('fk')
                if not fk_config:
                    errors.append(f"Column {idx}: fk config is required when type is 'fk'")
                else:
                    fk_table = fk_config.get('table')
                    fk_lookup = fk_config.get('lookup_column')
                    fk_on_missing = fk_config.get('on_missing', 'error')
                    
                    if not fk_table:
                        errors.append(f"Column {idx}: fk.table is required")
                    elif not cls.validate_table_name(fk_table):
                        errors.append(f"Column {idx}: Invalid fk.table name: {fk_table}")
                    
                    if not fk_lookup:
                        errors.append(f"Column {idx}: fk.lookup_column is required")
                    elif not cls.validate_column_name(fk_lookup):
                        errors.append(f"Column {idx}: Invalid fk.lookup_column name: {fk_lookup}")
                    
                    if fk_on_missing not in ['create', 'ignore', 'error']:
                        errors.append(f"Column {idx}: fk.on_missing must be 'create', 'ignore', or 'error'")

        return len(errors) == 0, errors

    @classmethod
    def convert_value(cls, value: Any, target_type: str) -> Any:
        """
        Convert value to target type.

        Args:
            value: Value to convert
            target_type: Target type

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return None

        try:
            if target_type == 'string':
                return str(value).strip()
            elif target_type == 'int':
                return int(float(str(value)))  # Handle "123.0" -> 123
            elif target_type == 'float':
                return float(value)
            elif target_type == 'decimal':
                return Decimal(str(value))
            elif target_type == 'date':
                if isinstance(value, date):
                    return value
                if isinstance(value, datetime):
                    return value.date()
                return pd.to_datetime(value).date()
            elif target_type == 'datetime':
                if isinstance(value, datetime):
                    return value
                return pd.to_datetime(value)
            elif target_type == 'boolean':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'sim']
                return bool(value)
            else:
                return str(value)
        except Exception as e:
            raise ValueError(f"Cannot convert '{value}' to {target_type}: {str(e)}")

    @classmethod
    def resolve_foreign_key(
        cls,
        db: Session,
        fk_config: Dict[str, Any],
        lookup_value: Any
    ) -> Optional[int]:
        """
        Resolve foreign key value.

        Args:
            db: Database session
            fk_config: FK configuration dict
            lookup_value: Value to lookup

        Returns:
            FK ID or None

        Raises:
            ProcessingError: If resolution fails and on_missing is 'error'
        """
        if lookup_value is None:
            return None

        fk_table = fk_config['table']
        lookup_column = fk_config['lookup_column']
        on_missing = fk_config.get('on_missing', 'error')

        try:
            # Sanitize table and column names
            if not cls.validate_table_name(fk_table):
                raise ProcessingError(f"Invalid FK table name: {fk_table}")
            if not cls.validate_column_name(lookup_column):
                raise ProcessingError(f"Invalid FK lookup column name: {lookup_column}")

            # Query for existing record
            query = text(f"SELECT id FROM {fk_table} WHERE {lookup_column} = :value LIMIT 1")
            result = db.execute(query, {"value": str(lookup_value)})
            row = result.fetchone()

            if row:
                return row[0]

            # Handle missing FK
            if on_missing == 'create':
                # Create new record
                insert_query = text(f"INSERT INTO {fk_table} ({lookup_column}) VALUES (:value) RETURNING id")
                result = db.execute(insert_query, {"value": str(lookup_value)})
                db.commit()
                row = result.fetchone()
                if row:
                    return row[0]
            elif on_missing == 'ignore':
                return None
            elif on_missing == 'error':
                raise ProcessingError(f"FK not found: {fk_table}.{lookup_column} = {lookup_value}")

            return None

        except SQLAlchemyError as e:
            logger.error("fk_resolution_error", error=str(e), fk_table=fk_table)
            if on_missing == 'error':
                raise ProcessingError(f"Failed to resolve FK: {str(e)}")
            return None

    @classmethod
    def create_table_if_needed(
        cls,
        db: Session,
        mapping_config: Dict[str, Any]
    ) -> None:
        """
        Create table dynamically if needed.

        Args:
            db: Database session
            mapping_config: Mapping configuration dict

        Raises:
            ProcessingError: If table creation fails
        """
        if not mapping_config.get('create_table', False):
            return

        target_table = mapping_config['target_table']
        columns = mapping_config['columns']

        # Validate table name
        if not cls.validate_table_name(target_table):
            raise ProcessingError(f"Invalid table name: {target_table}")

        try:
            # Check if table exists
            inspector = inspect(db.bind)
            if inspector.has_table(target_table):
                logger.info("table_already_exists", table=target_table)
                return

            # Build CREATE TABLE statement
            column_defs = []
            for col in columns:
                db_col = col['db_column']
                col_type = col['type']
                required = col.get('required', False)

                # Validate column name
                if not cls.validate_column_name(db_col):
                    raise ProcessingError(f"Invalid column name: {db_col}")

                # Map type to SQL type
                sql_type = cls._map_type_to_sql(col_type)
                nullable = "NOT NULL" if required else "NULL"

                column_defs.append(f"{db_col} {sql_type} {nullable}")

            # Add id column as primary key
            column_defs.insert(0, "id UUID PRIMARY KEY DEFAULT gen_random_uuid()")
            column_defs.append("created_at TIMESTAMP DEFAULT NOW()")
            column_defs.append("updated_at TIMESTAMP DEFAULT NOW()")

            # Create table
            create_sql = f"CREATE TABLE {target_table} ({', '.join(column_defs)})"
            db.execute(text(create_sql))
            db.commit()

            logger.info("table_created", table=target_table)

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("table_creation_failed", table=target_table, error=str(e))
            raise ProcessingError(f"Failed to create table: {str(e)}")

    @classmethod
    def _map_type_to_sql(cls, type_name: str) -> str:
        """
        Map type name to SQL type.

        Args:
            type_name: Type name

        Returns:
            SQL type string
        """
        type_map = {
            'string': 'VARCHAR(255)',
            'int': 'INTEGER',
            'float': 'DOUBLE PRECISION',
            'decimal': 'NUMERIC(12, 2)',
            'date': 'DATE',
            'datetime': 'TIMESTAMP',
            'boolean': 'BOOLEAN',
            'fk': 'UUID',  # Assume FK references UUID primary keys
        }
        return type_map.get(type_name, 'VARCHAR(255)')
