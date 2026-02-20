"""Entity routes for dynamic entity management and generic CRUD"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.api.schemas.entity import (
    DynamicEntityResponse,
    DynamicEntityUpdate,
    EntityDataResponse,
    PaginatedEntityDataResponse,
    EntityDataCreate,
    EntityDataUpdate,
)
from app.services.dynamic_entity_service import DynamicEntityService
from app.infrastructure.repositories.dynamic_entity_repository import DynamicEntityRepository
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=list[DynamicEntityResponse])
def list_entities(
    visible_only: bool = Query(False, description="Only return visible entities"),
    db: Session = Depends(get_database),
):
    """
    List all registered entities (for admin) or visible entities (for menu).

    Args:
        visible_only: If True, only return visible entities
        db: Database session

    Returns:
        List of entity metadata
    """
    entity_repo = DynamicEntityRepository(db)
    if visible_only:
        entities = entity_repo.get_all_visible()
    else:
        entities = entity_repo.get_all()

    return [
        DynamicEntityResponse(
            id=str(e.id),
            table_name=e.table_name,
            display_name=e.display_name,
            description=e.description,
            is_visible=e.is_visible,
            icon=e.icon,
            created_at=e.created_at,
            updated_at=e.updated_at,
            created_by_job_id=str(e.created_by_job_id) if e.created_by_job_id else None,
        )
        for e in entities
    ]


@router.get("/{table_name}", response_model=DynamicEntityResponse)
def get_entity(
    table_name: str,
    db: Session = Depends(get_database),
):
    """
    Get entity metadata by table name.

    Args:
        table_name: Table name
        db: Database session

    Returns:
        Entity metadata

    Raises:
        HTTPException: If entity not found
    """
    entity_repo = DynamicEntityRepository(db)
    entity = entity_repo.get_by_table_name(table_name)

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{table_name}' not found")

    return DynamicEntityResponse(
        id=str(entity.id),
        table_name=entity.table_name,
        display_name=entity.display_name,
        description=entity.description,
        is_visible=entity.is_visible,
        icon=entity.icon,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_job_id=str(entity.created_by_job_id) if entity.created_by_job_id else None,
    )


@router.put("/{table_name}/visibility", response_model=DynamicEntityResponse)
def update_entity_visibility(
    table_name: str,
    is_visible: bool = Query(..., description="New visibility status"),
    db: Session = Depends(get_database),
):
    """
    Update entity visibility.

    Args:
        table_name: Table name
        is_visible: New visibility status
        db: Database session

    Returns:
        Updated entity metadata

    Raises:
        HTTPException: If entity not found
    """
    entity_repo = DynamicEntityRepository(db)
    entity = entity_repo.update_visibility(table_name, is_visible)

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{table_name}' not found")

    return DynamicEntityResponse(
        id=str(entity.id),
        table_name=entity.table_name,
        display_name=entity.display_name,
        description=entity.description,
        is_visible=entity.is_visible,
        icon=entity.icon,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_job_id=str(entity.created_by_job_id) if entity.created_by_job_id else None,
    )


@router.put("/{table_name}/display-name", response_model=DynamicEntityResponse)
def update_entity_display_name(
    table_name: str,
    display_name: str = Query(..., description="New display name"),
    db: Session = Depends(get_database),
):
    """
    Update entity display name.

    Args:
        table_name: Table name
        display_name: New display name
        db: Database session

    Returns:
        Updated entity metadata

    Raises:
        HTTPException: If entity not found
    """
    entity_repo = DynamicEntityRepository(db)
    entity = entity_repo.update_display_name(table_name, display_name)

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{table_name}' not found")

    return DynamicEntityResponse(
        id=str(entity.id),
        table_name=entity.table_name,
        display_name=entity.display_name,
        description=entity.description,
        is_visible=entity.is_visible,
        icon=entity.icon,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_job_id=str(entity.created_by_job_id) if entity.created_by_job_id else None,
    )


@router.put("/{table_name}", response_model=DynamicEntityResponse)
def update_entity(
    table_name: str,
    update_data: DynamicEntityUpdate,
    db: Session = Depends(get_database),
):
    """
    Update entity metadata.

    Args:
        table_name: Table name
        update_data: Update data
        db: Database session

    Returns:
        Updated entity metadata

    Raises:
        HTTPException: If entity not found
    """
    entity_repo = DynamicEntityRepository(db)
    entity = entity_repo.update(
        table_name,
        display_name=update_data.display_name,
        description=update_data.description,
        icon=update_data.icon,
        is_visible=update_data.is_visible,
    )

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{table_name}' not found")

    return DynamicEntityResponse(
        id=str(entity.id),
        table_name=entity.table_name,
        display_name=entity.display_name,
        description=entity.description,
        is_visible=entity.is_visible,
        icon=entity.icon,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        created_by_job_id=str(entity.created_by_job_id) if entity.created_by_job_id else None,
    )


# Generic CRUD routes for entity data

@router.get("/{table_name}/data", response_model=PaginatedEntityDataResponse)
def list_entity_data(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_database),
):
    """
    List entity records with pagination.

    Args:
        table_name: Table name
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session

    Returns:
        Paginated entity data
    """
    service = DynamicEntityService(db)
    entities, total = service.list_entities(table_name, page=page, page_size=page_size)

    return PaginatedEntityDataResponse(
        data=entities,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{table_name}/data/{entity_id}", response_model=EntityDataResponse)
def get_entity_data(
    table_name: str,
    entity_id: str,
    db: Session = Depends(get_database),
):
    """
    Get a single entity record by ID.

    Args:
        table_name: Table name
        entity_id: Entity UUID
        db: Database session

    Returns:
        Entity data

    Raises:
        HTTPException: If entity not found
    """
    service = DynamicEntityService(db)
    try:
        entity = service.get_entity(table_name, entity_id)
        return EntityDataResponse(data=entity)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{table_name}/data", response_model=EntityDataResponse, status_code=201)
def create_entity_data(
    table_name: str,
    create_data: EntityDataCreate,
    db: Session = Depends(get_database),
):
    """
    Create a new entity record.

    Args:
        table_name: Table name
        create_data: Entity data
        db: Database session

    Returns:
        Created entity data

    Raises:
        HTTPException: If creation fails
    """
    service = DynamicEntityService(db)
    try:
        entity = service.create_entity(table_name, create_data.data)
        return EntityDataResponse(data=entity)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{table_name}/data/{entity_id}", response_model=EntityDataResponse)
def update_entity_data(
    table_name: str,
    entity_id: str,
    update_data: EntityDataUpdate,
    db: Session = Depends(get_database),
):
    """
    Update an entity record.

    Args:
        table_name: Table name
        entity_id: Entity UUID
        update_data: Update data
        db: Database session

    Returns:
        Updated entity data

    Raises:
        HTTPException: If entity not found
    """
    service = DynamicEntityService(db)
    try:
        entity = service.update_entity(table_name, entity_id, update_data.data)
        return EntityDataResponse(data=entity)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{table_name}/data/{entity_id}", status_code=204)
def delete_entity_data(
    table_name: str,
    entity_id: str,
    db: Session = Depends(get_database),
):
    """
    Delete an entity record.

    Args:
        table_name: Table name
        entity_id: Entity UUID
        db: Database session

    Raises:
        HTTPException: If entity not found
    """
    service = DynamicEntityService(db)
    try:
        service.delete_entity(table_name, entity_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
