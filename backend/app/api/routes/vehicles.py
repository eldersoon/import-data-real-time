"""Vehicle routes"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.api.schemas.vehicle import (
    VehicleResponse,
    VehicleUpdate,
    PaginatedVehicleResponse,
)
from app.services.vehicle_service import VehicleService
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=PaginatedVehicleResponse)
def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    placa: Optional[str] = Query(None),
    modelo: Optional[str] = Query(None),
    ano_min: Optional[int] = Query(None),
    ano_max: Optional[int] = Query(None),
    db: Session = Depends(get_database),
):
    """
    List vehicles with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        placa: Optional placa filter
        modelo: Optional modelo filter
        ano_min: Optional minimum year filter
        ano_max: Optional maximum year filter
        db: Database session

    Returns:
        Paginated vehicle response
    """
    service = VehicleService(db)
    vehicles, total = service.list_vehicles(
        page=page,
        page_size=page_size,
        placa=placa,
        modelo=modelo,
        ano_min=ano_min,
        ano_max=ano_max,
    )

    return PaginatedVehicleResponse(
        data=[
            VehicleResponse(
                id=str(v.id),
                job_id=str(v.job_id),
                modelo=v.modelo,
                placa=v.placa,
                ano=v.ano,
                valor_fipe=v.valor_fipe,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in vehicles
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_database),
):
    """
    Get vehicle by ID.

    Args:
        vehicle_id: Vehicle UUID
        db: Database session

    Returns:
        Vehicle response

    Raises:
        NotFoundError: If vehicle not found
    """
    try:
        vehicle_uuid = uuid.UUID(vehicle_id)
    except ValueError:
        raise NotFoundError(f"Vehicle ID inválido: {vehicle_id}")

    service = VehicleService(db)
    vehicle = service.get_vehicle(vehicle_uuid)

    return VehicleResponse(
        id=str(vehicle.id),
        job_id=str(vehicle.job_id),
        modelo=vehicle.modelo,
        placa=vehicle.placa,
        ano=vehicle.ano,
        valor_fipe=vehicle.valor_fipe,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: str,
    vehicle_update: VehicleUpdate,
    db: Session = Depends(get_database),
):
    """
    Update vehicle (only modelo and valor_fipe allowed).

    Args:
        vehicle_id: Vehicle UUID
        vehicle_update: Update data
        db: Database session

    Returns:
        Updated vehicle response

    Raises:
        NotFoundError: If vehicle not found
    """
    try:
        vehicle_uuid = uuid.UUID(vehicle_id)
    except ValueError:
        raise NotFoundError(f"Vehicle ID inválido: {vehicle_id}")

    service = VehicleService(db)
    vehicle = service.update_vehicle(
        vehicle_uuid,
        modelo=vehicle_update.modelo,
        valor_fipe=vehicle_update.valor_fipe,
    )

    return VehicleResponse(
        id=str(vehicle.id),
        job_id=str(vehicle.job_id),
        modelo=vehicle.modelo,
        placa=vehicle.placa,
        ano=vehicle.ano,
        valor_fipe=vehicle.valor_fipe,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


@router.delete("/{vehicle_id}", status_code=204)
def delete_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_database),
):
    """
    Delete vehicle.

    Args:
        vehicle_id: Vehicle UUID
        db: Database session

    Raises:
        NotFoundError: If vehicle not found
    """
    try:
        vehicle_uuid = uuid.UUID(vehicle_id)
    except ValueError:
        raise NotFoundError(f"Vehicle ID inválido: {vehicle_id}")

    service = VehicleService(db)
    service.delete_vehicle(vehicle_uuid)
