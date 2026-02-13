"""Repository for ImportedVehicle operations"""

import uuid
from typing import List, Optional, Tuple, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.domain.models.imported_vehicle import ImportedVehicle
from app.core.logging import get_logger

logger = get_logger(__name__)


class VehicleRepository:
    """Repository for ImportedVehicle data access"""

    def __init__(self, db: Session):
        self.db = db

    def create_bulk(self, vehicles_data: List[Dict[str, Any]]) -> int:
        """
        Create multiple vehicles in bulk using bulk_insert_mappings.

        Args:
            vehicles_data: List of dictionaries with vehicle data

        Returns:
            Number of vehicles created
        """
        if not vehicles_data:
            return 0

        self.db.bulk_insert_mappings(ImportedVehicle, vehicles_data)
        self.db.commit()

        logger.info("vehicles_created_bulk", count=len(vehicles_data))
        return len(vehicles_data)

    def get_placas_in_batch(self, placas: List[str]) -> Set[str]:
        """
        Get set of placas that already exist in the database.

        Args:
            placas: List of placas to check

        Returns:
            Set of placas that already exist
        """
        if not placas:
            return set()

        existing = (
            self.db.query(ImportedVehicle.placa)
            .filter(ImportedVehicle.placa.in_(placas))
            .all()
        )
        return {row[0] for row in existing}

    def get_by_id(self, vehicle_id: uuid.UUID) -> Optional[ImportedVehicle]:
        """
        Get a vehicle by ID.

        Args:
            vehicle_id: Vehicle UUID

        Returns:
            ImportedVehicle instance or None
        """
        return self.db.query(ImportedVehicle).filter(ImportedVehicle.id == vehicle_id).first()

    def get_by_placa(self, placa: str) -> Optional[ImportedVehicle]:
        """
        Get a vehicle by placa.

        Args:
            placa: Vehicle placa

        Returns:
            ImportedVehicle instance or None
        """
        return self.db.query(ImportedVehicle).filter(ImportedVehicle.placa == placa).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        placa: Optional[str] = None,
        modelo: Optional[str] = None,
        ano_min: Optional[int] = None,
        ano_max: Optional[int] = None
    ) -> Tuple[List[ImportedVehicle], int]:
        """
        List vehicles with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            placa: Optional placa filter (partial match)
            modelo: Optional modelo filter (partial match)
            ano_min: Optional minimum year filter
            ano_max: Optional maximum year filter

        Returns:
            Tuple of (list of vehicles, total count)
        """
        query = self.db.query(ImportedVehicle)

        # Apply filters
        if placa:
            query = query.filter(ImportedVehicle.placa.ilike(f"%{placa}%"))
        if modelo:
            query = query.filter(ImportedVehicle.modelo.ilike(f"%{modelo}%"))
        if ano_min:
            query = query.filter(ImportedVehicle.ano >= ano_min)
        if ano_max:
            query = query.filter(ImportedVehicle.ano <= ano_max)

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        vehicles = query.order_by(desc(ImportedVehicle.created_at)).offset(skip).limit(limit).all()

        return vehicles, total

    def update(
        self,
        vehicle_id: uuid.UUID,
        modelo: Optional[str] = None,
        valor_fipe: Optional[float] = None
    ) -> Optional[ImportedVehicle]:
        """
        Update a vehicle (only modelo and valor_fipe allowed).

        Args:
            vehicle_id: Vehicle UUID
            modelo: Optional new modelo
            valor_fipe: Optional new valor_fipe

        Returns:
            Updated ImportedVehicle instance or None
        """
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return None

        if modelo is not None:
            vehicle.modelo = modelo
        if valor_fipe is not None:
            vehicle.valor_fipe = valor_fipe

        self.db.commit()
        self.db.refresh(vehicle)

        logger.info("vehicle_updated", vehicle_id=str(vehicle_id))
        return vehicle

    def delete(self, vehicle_id: uuid.UUID) -> bool:
        """
        Delete a vehicle.

        Args:
            vehicle_id: Vehicle UUID

        Returns:
            True if deleted, False if not found
        """
        vehicle = self.get_by_id(vehicle_id)
        if not vehicle:
            return False

        self.db.delete(vehicle)
        self.db.commit()

        logger.info("vehicle_deleted", vehicle_id=str(vehicle_id))
        return True
