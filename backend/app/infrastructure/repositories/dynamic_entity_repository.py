"""Repository for DynamicEntity operations"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domain.models.dynamic_entity import DynamicEntity
from app.core.logging import get_logger

logger = get_logger(__name__)


class DynamicEntityRepository:
    """Repository for DynamicEntity data access"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        table_name: str,
        display_name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        job_id: Optional[uuid.UUID] = None,
        is_visible: bool = True
    ) -> DynamicEntity:
        """
        Create a new dynamic entity record.

        Args:
            table_name: Database table name
            display_name: Human-readable name for menu
            description: Optional description
            icon: Optional icon name
            job_id: Optional job ID that created this entity
            is_visible: Whether entity is visible in menu

        Returns:
            Created DynamicEntity instance
        """
        entity = DynamicEntity(
            table_name=table_name,
            display_name=display_name,
            description=description,
            icon=icon,
            created_by_job_id=job_id,
            is_visible=is_visible
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        logger.info("dynamic_entity_created", entity_id=str(entity.id), table_name=table_name)
        return entity

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[DynamicEntity]:
        """
        Get an entity by ID.

        Args:
            entity_id: Entity UUID

        Returns:
            DynamicEntity instance or None
        """
        return self.db.query(DynamicEntity).filter(DynamicEntity.id == entity_id).first()

    def get_by_table_name(self, table_name: str) -> Optional[DynamicEntity]:
        """
        Get an entity by table name.

        Args:
            table_name: Database table name

        Returns:
            DynamicEntity instance or None
        """
        return self.db.query(DynamicEntity).filter(DynamicEntity.table_name == table_name).first()

    def get_all_visible(self) -> List[DynamicEntity]:
        """
        Get all visible entities (for menu).

        Returns:
            List of visible DynamicEntity instances
        """
        return (
            self.db.query(DynamicEntity)
            .filter(DynamicEntity.is_visible == True)
            .order_by(desc(DynamicEntity.created_at))
            .all()
        )

    def get_all(self) -> List[DynamicEntity]:
        """
        Get all entities (for admin).

        Returns:
            List of all DynamicEntity instances
        """
        return (
            self.db.query(DynamicEntity)
            .order_by(desc(DynamicEntity.created_at))
            .all()
        )

    def update_visibility(self, table_name: str, is_visible: bool) -> Optional[DynamicEntity]:
        """
        Update entity visibility.

        Args:
            table_name: Database table name
            is_visible: New visibility status

        Returns:
            Updated DynamicEntity instance or None
        """
        entity = self.get_by_table_name(table_name)
        if entity:
            entity.is_visible = is_visible
            self.db.commit()
            self.db.refresh(entity)

            logger.info("dynamic_entity_visibility_updated", table_name=table_name, is_visible=is_visible)
            return entity
        return None

    def update_display_name(self, table_name: str, display_name: str) -> Optional[DynamicEntity]:
        """
        Update entity display name.

        Args:
            table_name: Database table name
            display_name: New display name

        Returns:
            Updated DynamicEntity instance or None
        """
        entity = self.get_by_table_name(table_name)
        if entity:
            entity.display_name = display_name
            self.db.commit()
            self.db.refresh(entity)

            logger.info("dynamic_entity_display_name_updated", table_name=table_name, display_name=display_name)
            return entity
        return None

    def update(
        self,
        table_name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        is_visible: Optional[bool] = None
    ) -> Optional[DynamicEntity]:
        """
        Update entity fields.

        Args:
            table_name: Database table name
            display_name: Optional new display name
            description: Optional new description
            icon: Optional new icon
            is_visible: Optional new visibility status

        Returns:
            Updated DynamicEntity instance or None
        """
        entity = self.get_by_table_name(table_name)
        if entity:
            if display_name is not None:
                entity.display_name = display_name
            if description is not None:
                entity.description = description
            if icon is not None:
                entity.icon = icon
            if is_visible is not None:
                entity.is_visible = is_visible

            self.db.commit()
            self.db.refresh(entity)

            logger.info("dynamic_entity_updated", table_name=table_name)
            return entity
        return None

    def delete(self, table_name: str) -> bool:
        """
        Delete an entity record.

        Args:
            table_name: Database table name

        Returns:
            True if deleted, False if not found
        """
        entity = self.get_by_table_name(table_name)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            logger.info("dynamic_entity_deleted", table_name=table_name)
            return True
        return False
