"""Template service for handling import templates"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.infrastructure.repositories.import_template_repository import ImportTemplateRepository
from app.services.mapping_service import MappingService
from app.core.exceptions import ProcessingError, NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class TemplateService:
    """Service for template operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ImportTemplateRepository(db)
        self.mapping_service = MappingService()

    def create_template(
        self,
        name: str,
        target_table: str,
        mapping_config: Dict[str, Any],
        create_table: bool = False
    ):
        """
        Create a new template.

        Args:
            name: Template name
            target_table: Target database table
            mapping_config: Mapping configuration dict
            create_table: Whether to create table if missing

        Returns:
            Created ImportTemplate instance

        Raises:
            ProcessingError: If validation fails
        """
        # Validate mapping config
        is_valid, errors = self.mapping_service.validate_mapping(mapping_config)
        if not is_valid:
            raise ProcessingError(f"Invalid mapping config: {', '.join(errors)}")

        # Check if name already exists
        existing = self.repository.get_by_name(name)
        if existing:
            raise ProcessingError(f"Template com nome '{name}' já existe")

        return self.repository.create(
            name=name,
            target_table=target_table,
            mapping_config=mapping_config,
            create_table=create_table
        )

    def get_template(self, template_id: uuid.UUID):
        """
        Get a template by ID.

        Args:
            template_id: Template UUID

        Returns:
            ImportTemplate instance or None
        """
        return self.repository.get_by_id(template_id)

    def list_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        target_table: Optional[str] = None
    ) -> List:
        """
        List templates with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            target_table: Optional target table filter

        Returns:
            List of ImportTemplate instances
        """
        return self.repository.list(skip=skip, limit=limit, target_table=target_table)

    def update_template(
        self,
        template_id: uuid.UUID,
        name: Optional[str] = None,
        target_table: Optional[str] = None,
        mapping_config: Optional[Dict[str, Any]] = None,
        create_table: Optional[bool] = None
    ):
        """
        Update a template.

        Args:
            template_id: Template UUID
            name: Optional new name
            target_table: Optional new target table
            mapping_config: Optional new mapping config
            create_table: Optional new create_table flag

        Returns:
            Updated ImportTemplate instance or None

        Raises:
            ProcessingError: If validation fails
        """
        # Validate mapping config if provided
        if mapping_config:
            is_valid, errors = self.mapping_service.validate_mapping(mapping_config)
            if not is_valid:
                raise ProcessingError(f"Invalid mapping config: {', '.join(errors)}")

        # Check name uniqueness if changing name
        if name:
            existing = self.repository.get_by_name(name)
            if existing and existing.id != template_id:
                raise ProcessingError(f"Template com nome '{name}' já existe")

        return self.repository.update(
            template_id=template_id,
            name=name,
            target_table=target_table,
            mapping_config=mapping_config,
            create_table=create_table
        )

    def delete_template(self, template_id: uuid.UUID) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template UUID

        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(template_id)
