"""Repository for ImportTemplate operations"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.models.import_template import ImportTemplate
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImportTemplateRepository:
    """Repository for ImportTemplate data access"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        target_table: str,
        mapping_config: Dict[str, Any],
        create_table: bool = False
    ) -> ImportTemplate:
        """
        Create a new import template.

        Args:
            name: Template name
            target_table: Target database table
            mapping_config: Mapping configuration dict
            create_table: Whether to create table if missing

        Returns:
            Created ImportTemplate instance
        """
        template = ImportTemplate(
            name=name,
            target_table=target_table,
            mapping_config=mapping_config,
            create_table=create_table
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info("import_template_created", template_id=str(template.id), name=name)
        return template

    def get_by_id(self, template_id: uuid.UUID) -> Optional[ImportTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Template UUID

        Returns:
            ImportTemplate instance or None
        """
        return self.db.query(ImportTemplate).filter(ImportTemplate.id == template_id).first()

    def get_by_name(self, name: str) -> Optional[ImportTemplate]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            ImportTemplate instance or None
        """
        return self.db.query(ImportTemplate).filter(ImportTemplate.name == name).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        target_table: Optional[str] = None
    ) -> List[ImportTemplate]:
        """
        List templates with pagination and optional filter.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            target_table: Optional target table filter

        Returns:
            List of ImportTemplate instances
        """
        query = self.db.query(ImportTemplate)

        if target_table:
            query = query.filter(ImportTemplate.target_table == target_table)

        return query.order_by(desc(ImportTemplate.created_at)).offset(skip).limit(limit).all()

    def update(
        self,
        template_id: uuid.UUID,
        name: Optional[str] = None,
        target_table: Optional[str] = None,
        mapping_config: Optional[Dict[str, Any]] = None,
        create_table: Optional[bool] = None
    ) -> Optional[ImportTemplate]:
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
        """
        template = self.get_by_id(template_id)
        if template:
            if name is not None:
                template.name = name
            if target_table is not None:
                template.target_table = target_table
            if mapping_config is not None:
                template.mapping_config = mapping_config
            if create_table is not None:
                template.create_table = create_table

            self.db.commit()
            self.db.refresh(template)

            logger.info("import_template_updated", template_id=str(template_id))
            return template
        return None

    def delete(self, template_id: uuid.UUID) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template UUID

        Returns:
            True if deleted, False if not found
        """
        template = self.get_by_id(template_id)
        if template:
            self.db.delete(template)
            self.db.commit()
            logger.info("import_template_deleted", template_id=str(template_id))
            return True
        return False
