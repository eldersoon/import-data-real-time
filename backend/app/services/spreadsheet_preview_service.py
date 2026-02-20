"""Spreadsheet preview service for analyzing files and detecting columns/types"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from io import BytesIO

from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpreadsheetPreviewService:
    """Service for previewing spreadsheet files and detecting structure"""

    # Whitelist of allowed types
    ALLOWED_TYPES = ['string', 'int', 'float', 'decimal', 'date', 'datetime', 'boolean']

    @classmethod
    def _infer_type(cls, series: pd.Series) -> str:
        """
        Infer data type from pandas Series.

        Args:
            series: Pandas Series to analyze

        Returns:
            Suggested type string
        """
        # Remove null values for analysis
        non_null = series.dropna()

        if len(non_null) == 0:
            return 'string'  # Default to string if all null

        # Check for boolean
        if series.dtype == 'bool' or (series.dtype == 'object' and non_null.isin([True, False, 'True', 'False', 'true', 'false', 1, 0]).all()):
            return 'boolean'

        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'

        # Try to parse as date
        if series.dtype == 'object':
            try:
                pd.to_datetime(non_null.head(100), errors='raise')
                return 'date'
            except (ValueError, TypeError):
                pass

        # Check for integer
        if pd.api.types.is_integer_dtype(series):
            return 'int'

        # Check for float/decimal
        if pd.api.types.is_float_dtype(series):
            # Check if it's actually an integer
            if non_null.apply(lambda x: pd.notna(x) and float(x).is_integer()).all():
                return 'int'
            return 'decimal'

        # Try to convert to numeric
        try:
            numeric = pd.to_numeric(non_null.head(100), errors='raise')
            if numeric.apply(lambda x: pd.notna(x) and float(x).is_integer()).all():
                return 'int'
            return 'decimal'
        except (ValueError, TypeError):
            pass

        # Default to string
        return 'string'

    @classmethod
    def analyze_file(cls, file_path: Optional[str] = None, file_bytes: Optional[bytes] = None, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze spreadsheet file and return columns, types, and preview.

        Args:
            file_path: Path to file (if reading from disk)
            file_bytes: File content as bytes (if reading from memory)
            filename: Original filename (for extension detection)

        Returns:
            Dictionary with columns, types, and preview data

        Raises:
            ProcessingError: If file cannot be analyzed
        """
        if not file_path and not file_bytes:
            raise ProcessingError("Either file_path or file_bytes must be provided")

        try:
            # Determine file extension
            if file_path:
                file_ext = Path(file_path).suffix.lower()
            elif filename:
                file_ext = Path(filename).suffix.lower()
            else:
                raise ProcessingError("Cannot determine file extension")

            # Read file
            if file_ext == '.csv':
                if file_bytes:
                    df = pd.read_csv(BytesIO(file_bytes), nrows=1000)  # Read first 1000 rows for analysis
                else:
                    df = pd.read_csv(file_path, nrows=1000)
            elif file_ext in ['.xlsx', '.xls']:
                if file_bytes:
                    df = pd.read_excel(BytesIO(file_bytes), nrows=1000)
                else:
                    df = pd.read_excel(file_path, nrows=1000)
            else:
                raise ProcessingError(f"Formato de arquivo não suportado: {file_ext}")

            # Analyze columns
            columns = []
            for col_name in df.columns:
                col_series = df[col_name]
                suggested_type = cls._infer_type(col_series)
                
                columns.append({
                    'name': str(col_name),
                    'suggested_type': suggested_type,
                    'sample_values': col_series.dropna().head(5).tolist(),
                    'null_count': col_series.isna().sum(),
                    'total_count': len(col_series),
                })

            # Get preview (first 10 rows)
            preview_rows = []
            for idx, row in df.head(10).iterrows():
                preview_rows.append(row.to_dict())

            return {
                'columns': columns,
                'preview_rows': preview_rows,
                'total_rows': len(df),
                'total_columns': len(df.columns),
            }

        except Exception as e:
            logger.error("failed_to_analyze_file", error=str(e))
            raise ProcessingError(f"Falha ao analisar arquivo: {str(e)}")

    @classmethod
    def validate_type(cls, type_name: str) -> bool:
        """
        Validate if type is in whitelist.

        Args:
            type_name: Type name to validate

        Returns:
            True if valid
        """
        return type_name in cls.ALLOWED_TYPES
