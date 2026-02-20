"""Template routes"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.api.schemas.mapping import MappingConfig
from app.services.template_service import TemplateService
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=List[dict])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    target_table: Optional[str] = Query(None),
    db: Session = Depends(get_database),
):
    """
    List import templates with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        target_table: Optional target table filter
        db: Database session

    Returns:
        List of templates
    """
    service = TemplateService(db)
    templates = service.list_templates(skip=skip, limit=limit, target_table=target_table)

    return [
        {
            "id": str(template.id),
            "name": template.name,
            "target_table": template.target_table,
            "create_table": template.create_table,
            "mapping_config": template.mapping_config,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }
        for template in templates
    ]


@router.post("", response_model=dict, status_code=201)
def create_template(
    name: str,
    target_table: str,
    mapping_config: MappingConfig,
    create_table: bool = False,
    db: Session = Depends(get_database),
):
    """
    Create a new import template.

    Args:
        name: Template name
        target_table: Target database table
        mapping_config: Mapping configuration
        create_table: Whether to create table if missing
        db: Database session

    Returns:
        Created template information
    """
    service = TemplateService(db)
    template = service.create_template(
        name=name,
        target_table=target_table,
        mapping_config=mapping_config.dict(),
        create_table=create_table
    )

    return {
        "id": str(template.id),
        "name": template.name,
        "target_table": template.target_table,
        "create_table": template.create_table,
        "mapping_config": template.mapping_config,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


@router.get("/{template_id}", response_model=dict)
def get_template(
    template_id: str,
    db: Session = Depends(get_database),
):
    """
    Get template details.

    Args:
        template_id: Template UUID
        db: Database session

    Returns:
        Template details

    Raises:
        NotFoundError: If template not found
    """
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Template ID inválido: {template_id}")

    service = TemplateService(db)
    template = service.get_template(template_uuid)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template não encontrado: {template_id}")

    return {
        "id": str(template.id),
        "name": template.name,
        "target_table": template.target_table,
        "create_table": template.create_table,
        "mapping_config": template.mapping_config,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


@router.put("/{template_id}", response_model=dict)
def update_template(
    template_id: str,
    name: Optional[str] = None,
    target_table: Optional[str] = None,
    mapping_config: Optional[MappingConfig] = None,
    create_table: Optional[bool] = None,
    db: Session = Depends(get_database),
):
    """
    Update a template.

    Args:
        template_id: Template UUID
        name: Optional new name
        target_table: Optional new target table
        mapping_config: Optional new mapping config
        create_table: Optional new create_table flag
        db: Database session

    Returns:
        Updated template information

    Raises:
        NotFoundError: If template not found
    """
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Template ID inválido: {template_id}")

    service = TemplateService(db)
    template = service.update_template(
        template_id=template_uuid,
        name=name,
        target_table=target_table,
        mapping_config=mapping_config.dict() if mapping_config else None,
        create_table=create_table
    )

    if not template:
        raise HTTPException(status_code=404, detail=f"Template não encontrado: {template_id}")

    return {
        "id": str(template.id),
        "name": template.name,
        "target_table": template.target_table,
        "create_table": template.create_table,
        "mapping_config": template.mapping_config,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    db: Session = Depends(get_database),
):
    """
    Delete a template.

    Args:
        template_id: Template UUID
        db: Database session

    Raises:
        NotFoundError: If template not found
    """
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Template ID inválido: {template_id}")

    service = TemplateService(db)
    deleted = service.delete_template(template_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template não encontrado: {template_id}")
