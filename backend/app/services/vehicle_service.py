"""Vehicle service for CRUD operations"""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from decimal import Decimal

from app.domain.models.imported_vehicle import ImportedVehicle
from app.infrastructure.repositories.vehicle_repository import VehicleRepository
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class VehicleService:
    """Service for vehicle operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = VehicleRepository(db)

    def list_vehicles(
        self,
        page: int = 1,
        page_size: int = 10,
        placa: Optional[str] = None,
        modelo: Optional[str] = None,
        ano_min: Optional[int] = None,
        ano_max: Optional[int] = None
    ) -> Tuple[List[ImportedVehicle], int]:
        """
        List vehicles with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            placa: Optional placa filter
            modelo: Optional modelo filter
            ano_min: Optional minimum year filter
            ano_max: Optional maximum year filter

        Returns:
            Tuple of (vehicles list, total count)
        """
        skip = (page - 1) * page_size
        return self.repository.list(
            skip=skip,
            limit=page_size,
            placa=placa,
            modelo=modelo,
            ano_min=ano_min,
            ano_max=ano_max
        )

    def get_vehicle(self, vehicle_id: uuid.UUID) -> ImportedVehicle:
        """
        Get a vehicle by ID.

        Args:
            vehicle_id: Vehicle UUID

        Returns:
            ImportedVehicle instance

        Raises:
            NotFoundError: If vehicle not found
        """
        vehicle = self.repository.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundError(f"Veículo não encontrado: {vehicle_id}")
        return vehicle

    def update_vehicle(
        self,
        vehicle_id: uuid.UUID,
        modelo: Optional[str] = None,
        valor_fipe: Optional[float] = None
    ) -> ImportedVehicle:
        """
        Update a vehicle.

        Args:
            vehicle_id: Vehicle UUID
            modelo: Optional new modelo
            valor_fipe: Optional new valor_fipe

        Returns:
            Updated ImportedVehicle instance

        Raises:
            NotFoundError: If vehicle not found
        """
        vehicle = self.repository.update(vehicle_id, modelo, valor_fipe)
        if not vehicle:
            raise NotFoundError(f"Veículo não encontrado: {vehicle_id}")
        return vehicle

    def delete_vehicle(self, vehicle_id: uuid.UUID) -> None:
        """
        Delete a vehicle.

        Args:
            vehicle_id: Vehicle UUID

        Raises:
            NotFoundError: If vehicle not found
        """
        deleted = self.repository.delete(vehicle_id)
        if not deleted:
            raise NotFoundError(f"Veículo não encontrado: {vehicle_id}")
