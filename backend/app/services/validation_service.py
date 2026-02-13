"""Validation service for vehicle data"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Tuple

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationService:
    """Service for validating vehicle data"""

    # Mercosul plate pattern: ABC1D23 or ABC1234 (old format)
    PLACA_PATTERN = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$|^[A-Z]{3}[0-9]{4}$')

    @staticmethod
    def validate_placa(placa: str) -> bool:
        """
        Validate Mercosul plate format.

        Args:
            placa: Plate string

        Returns:
            True if valid
        """
        if not placa:
            return False
        placa = placa.upper().strip()
        return bool(ValidationService.PLACA_PATTERN.match(placa))

    @staticmethod
    def validate_ano(ano: int) -> bool:
        """
        Validate year range (1900 to current year + 1).

        Args:
            ano: Year

        Returns:
            True if valid
        """
        current_year = datetime.now().year
        return 1900 <= ano <= current_year + 1

    @staticmethod
    def validate_valor_fipe(valor_fipe: float) -> bool:
        """
        Validate FIPE value (must be positive).

        Args:
            valor_fipe: FIPE value

        Returns:
            True if valid
        """
        return valor_fipe > 0

    @staticmethod
    def validate_vehicle(row: Dict[str, Any], row_number: int) -> Tuple[bool, List[str]]:
        """
        Validate a vehicle row.

        Args:
            row: Row data dictionary
            row_number: Row number for error reporting

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        required_fields = ['modelo', 'placa', 'ano', 'valor_fipe']
        for field in required_fields:
            if field not in row or row[field] is None:
                errors.append(f"Campo '{field}' é obrigatório")

        if errors:
            return False, errors

        # Validate placa
        placa = str(row['placa']).strip()
        if not ValidationService.validate_placa(placa):
            errors.append(f"Placa '{placa}' inválida (formato esperado: ABC1D23 ou ABC1234)")

        # Validate ano
        try:
            ano = int(row['ano'])
            if not ValidationService.validate_ano(ano):
                errors.append(f"Ano '{ano}' inválido (deve estar entre 1900 e {datetime.now().year + 1})")
        except (ValueError, TypeError):
            errors.append(f"Ano '{row['ano']}' inválido (deve ser um número)")

        # Validate valor_fipe
        try:
            valor_fipe = float(row['valor_fipe'])
            if not ValidationService.validate_valor_fipe(valor_fipe):
                errors.append(f"Valor FIPE '{valor_fipe}' inválido (deve ser maior que zero)")
        except (ValueError, TypeError):
            errors.append(f"Valor FIPE '{row['valor_fipe']}' inválido (deve ser um número)")

        return len(errors) == 0, errors
