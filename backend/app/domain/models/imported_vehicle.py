"""ImportedVehicle domain model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from decimal import Decimal

from app.core.database import Base


class ImportedVehicle(Base):
    """Imported vehicle model"""

    __tablename__ = "imported_vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False)
    modelo = Column(String, nullable=False)
    placa = Column(String(7), nullable=False)
    ano = Column(Integer, nullable=False)
    valor_fipe = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    job = relationship("ImportJob", backref="vehicles")

    __table_args__ = (
        CheckConstraint(
            "ano >= 1900 AND ano <= EXTRACT(YEAR FROM CURRENT_DATE) + 1",
            name='check_ano'
        ),
        CheckConstraint(
            "valor_fipe > 0",
            name='check_valor_fipe'
        ),
        UniqueConstraint('placa', name='uq_imported_vehicles_placa'),
        Index('ix_imported_vehicles_job_id', 'job_id'),
        Index('ix_imported_vehicles_placa', 'placa'),
        Index('ix_imported_vehicles_ano', 'ano'),
    )

    def __repr__(self):
        return f"<ImportedVehicle(id={self.id}, placa={self.placa}, modelo={self.modelo})>"
