"""Dynamic entity service for generic CRUD operations on any table"""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.repositories.dynamic_entity_repository import DynamicEntityRepository
from app.services.database_metadata_service import DatabaseMetadataService
from app.core.exceptions import NotFoundError, ProcessingError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class DynamicEntityService:
    """Service for generic CRUD operations on dynamically created tables"""

    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = DynamicEntityRepository(db)
        self.metadata_service = DatabaseMetadataService(db)

    def _validate_table_name(self, table_name: str) -> None:
        """
        Validate that table_name exists in DynamicEntity whitelist.

        Args:
            table_name: Table name to validate

        Raises:
            NotFoundError: If table is not in whitelist
        """
        entity = self.entity_repo.get_by_table_name(table_name)
        if not entity:
            raise NotFoundError(f"Entity '{table_name}' not found. Only dynamically created entities are accessible.")

    def _convert_value(self, value: Any, data_type: str) -> Any:
        """
        Convert value to appropriate Python type based on SQL data type.

        Args:
            value: Value to convert
            data_type: SQL data type

        Returns:
            Converted value
        """
        if value is None:
            return None

        # Normalize data type
        data_type_lower = data_type.lower()

        if 'uuid' in data_type_lower:
            return str(value) if value else None
        elif 'int' in data_type_lower:
            return int(value) if value else None
        elif 'numeric' in data_type_lower or 'decimal' in data_type_lower:
            return float(value) if value else None
        elif 'double' in data_type_lower or 'real' in data_type_lower or 'float' in data_type_lower:
            return float(value) if value else None
        elif 'bool' in data_type_lower:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif 'date' in data_type_lower:
            if isinstance(value, date):
                return value
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
        elif 'timestamp' in data_type_lower or 'time' in data_type_lower:
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))

        return value

    def list_entities(
        self,
        table_name: str,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List entities from a table with pagination and optional filtering.

        Args:
            table_name: Table name
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional dict of column_name: value filters

        Returns:
            Tuple of (entities list, total count)

        Raises:
            NotFoundError: If table is not in whitelist
            ProcessingError: If query fails
        """
        self._validate_table_name(table_name)

        try:
            # Get table metadata
            table_info = self.metadata_service.get_table_info(table_name)
            columns = [col['column_name'] for col in table_info['columns']]

            # Build WHERE clause for filters
            where_clauses = []
            params = {}
            if filters:
                for col_name, value in filters.items():
                    if col_name in columns:
                        where_clauses.append(f"{col_name} = :filter_{col_name}")
                        params[f"filter_{col_name}"] = value

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Get total count
            count_sql = f"SELECT COUNT(*) as total FROM {table_name} {where_sql}"
            count_result = self.db.execute(text(count_sql), params)
            total = count_result.scalar()

            # Get paginated results
            skip = (page - 1) * page_size
            select_sql = f"SELECT * FROM {table_name} {where_sql} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params['limit'] = page_size
            params['offset'] = skip

            result = self.db.execute(text(select_sql), params)
            entities = []
            for row in result:
                entity_dict = {}
                for col_name in columns:
                    value = getattr(row, col_name)
                    # Convert UUIDs to strings
                    if isinstance(value, uuid.UUID):
                        entity_dict[col_name] = str(value)
                    elif isinstance(value, (datetime, date)):
                        entity_dict[col_name] = value.isoformat()
                    elif isinstance(value, Decimal):
                        entity_dict[col_name] = float(value)
                    else:
                        entity_dict[col_name] = value
                entities.append(entity_dict)

            return entities, total

        except SQLAlchemyError as e:
            logger.error("failed_to_list_entities", table_name=table_name, error=str(e))
            raise ProcessingError(f"Failed to list entities: {str(e)}")

    def get_entity(self, table_name: str, entity_id: str) -> Dict[str, Any]:
        """
        Get a single entity by ID.

        Args:
            table_name: Table name
            entity_id: Entity UUID

        Returns:
            Entity dict

        Raises:
            NotFoundError: If entity not found
        """
        self._validate_table_name(table_name)

        try:
            table_info = self.metadata_service.get_table_info(table_name)
            pk_column = table_info['primary_key'] or 'id'
            columns = [col['column_name'] for col in table_info['columns']]

            select_sql = f"SELECT * FROM {table_name} WHERE {pk_column} = :entity_id"
            result = self.db.execute(text(select_sql), {"entity_id": entity_id})

            row = result.first()
            if not row:
                raise NotFoundError(f"Entity with ID '{entity_id}' not found in table '{table_name}'")

            entity_dict = {}
            for col_name in columns:
                value = getattr(row, col_name)
                if isinstance(value, uuid.UUID):
                    entity_dict[col_name] = str(value)
                elif isinstance(value, (datetime, date)):
                    entity_dict[col_name] = value.isoformat()
                elif isinstance(value, Decimal):
                    entity_dict[col_name] = float(value)
                else:
                    entity_dict[col_name] = value

            return entity_dict

        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error("failed_to_get_entity", table_name=table_name, entity_id=entity_id, error=str(e))
            raise ProcessingError(f"Failed to get entity: {str(e)}")

    def create_entity(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity.

        Args:
            table_name: Table name
            data: Entity data dict (excluding id, created_at, updated_at)

        Returns:
            Created entity dict

        Raises:
            NotFoundError: If table is not in whitelist
            ValidationError: If data validation fails
        """
        self._validate_table_name(table_name)

        try:
            table_info = self.metadata_service.get_table_info(table_name)
            columns_info = {col['column_name']: col for col in table_info['columns']}

            # Filter out system columns
            system_columns = {'id', 'created_at', 'updated_at'}
            insert_data = {}
            for col_name, value in data.items():
                if col_name in system_columns:
                    continue
                if col_name not in columns_info:
                    raise ValidationError(f"Column '{col_name}' does not exist in table '{table_name}'")
                # Convert value based on column type
                col_info = columns_info[col_name]
                converted_value = self._convert_value(value, col_info['data_type'])
                insert_data[col_name] = converted_value

            # Build INSERT statement
            columns = list(insert_data.keys())
            values = [f":{col}" for col in columns]
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)}) RETURNING *"

            result = self.db.execute(text(insert_sql), insert_data)
            self.db.commit()

            row = result.first()
            entity_dict = {}
            for col_name in [col['column_name'] for col in table_info['columns']]:
                value = getattr(row, col_name)
                if isinstance(value, uuid.UUID):
                    entity_dict[col_name] = str(value)
                elif isinstance(value, (datetime, date)):
                    entity_dict[col_name] = value.isoformat()
                elif isinstance(value, Decimal):
                    entity_dict[col_name] = float(value)
                else:
                    entity_dict[col_name] = value

            logger.info("entity_created", table_name=table_name, entity_id=entity_dict.get('id'))
            return entity_dict

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("failed_to_create_entity", table_name=table_name, error=str(e))
            raise ProcessingError(f"Failed to create entity: {str(e)}")

    def update_entity(self, table_name: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an entity.

        Args:
            table_name: Table name
            entity_id: Entity UUID
            data: Update data dict (excluding id, created_at, updated_at)

        Returns:
            Updated entity dict

        Raises:
            NotFoundError: If entity not found
            ValidationError: If data validation fails
        """
        self._validate_table_name(table_name)

        try:
            table_info = self.metadata_service.get_table_info(table_name)
            pk_column = table_info['primary_key'] or 'id'
            columns_info = {col['column_name']: col for col in table_info['columns']}

            # Filter out system columns
            system_columns = {'id', 'created_at', 'updated_at'}
            update_data = {}
            for col_name, value in data.items():
                if col_name in system_columns:
                    continue
                if col_name not in columns_info:
                    raise ValidationError(f"Column '{col_name}' does not exist in table '{table_name}'")
                # Convert value based on column type
                col_info = columns_info[col_name]
                converted_value = self._convert_value(value, col_info['data_type'])
                update_data[col_name] = converted_value

            if not update_data:
                raise ValidationError("No valid columns to update")

            # Build UPDATE statement
            set_clauses = [f"{col} = :{col}" for col in update_data.keys()]
            update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)}, updated_at = NOW() WHERE {pk_column} = :entity_id RETURNING *"

            params = {**update_data, "entity_id": entity_id}
            result = self.db.execute(text(update_sql), params)
            self.db.commit()

            row = result.first()
            if not row:
                raise NotFoundError(f"Entity with ID '{entity_id}' not found in table '{table_name}'")

            entity_dict = {}
            for col_name in [col['column_name'] for col in table_info['columns']]:
                value = getattr(row, col_name)
                if isinstance(value, uuid.UUID):
                    entity_dict[col_name] = str(value)
                elif isinstance(value, (datetime, date)):
                    entity_dict[col_name] = value.isoformat()
                elif isinstance(value, Decimal):
                    entity_dict[col_name] = float(value)
                else:
                    entity_dict[col_name] = value

            logger.info("entity_updated", table_name=table_name, entity_id=entity_id)
            return entity_dict

        except (NotFoundError, ValidationError):
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("failed_to_update_entity", table_name=table_name, entity_id=entity_id, error=str(e))
            raise ProcessingError(f"Failed to update entity: {str(e)}")

    def delete_entity(self, table_name: str, entity_id: str) -> None:
        """
        Delete an entity.

        Args:
            table_name: Table name
            entity_id: Entity UUID

        Raises:
            NotFoundError: If entity not found
        """
        self._validate_table_name(table_name)

        try:
            table_info = self.metadata_service.get_table_info(table_name)
            pk_column = table_info['primary_key'] or 'id'

            delete_sql = f"DELETE FROM {table_name} WHERE {pk_column} = :entity_id RETURNING {pk_column}"
            result = self.db.execute(text(delete_sql), {"entity_id": entity_id})
            self.db.commit()

            if not result.first():
                raise NotFoundError(f"Entity with ID '{entity_id}' not found in table '{table_name}'")

            logger.info("entity_deleted", table_name=table_name, entity_id=entity_id)

        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("failed_to_delete_entity", table_name=table_name, entity_id=entity_id, error=str(e))
            raise ProcessingError(f"Failed to delete entity: {str(e)}")
