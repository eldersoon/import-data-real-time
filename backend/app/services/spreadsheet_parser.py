"""Spreadsheet parser service"""

import os
from pathlib import Path
from typing import Iterator
import pandas as pd
from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpreadsheetParser:
    """Service for parsing CSV and Excel files"""

    REQUIRED_COLUMNS = ['modelo', 'placa', 'ano', 'valor_fipe']

    @classmethod
    def _validate_columns(cls, df: pd.DataFrame) -> None:
        """
        Validate that required columns exist.

        Args:
            df: DataFrame to validate

        Raises:
            ProcessingError: If required columns are missing
        """
        missing_columns = set(cls.REQUIRED_COLUMNS) - set(df.columns)
        if missing_columns:
            raise ProcessingError(
                f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}"
            )

    @classmethod
    def read_file(cls, file_path: str, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
        """
        Read file in chunks (CSV or Excel).

        Args:
            file_path: Path to file
            chunk_size: Number of rows per chunk

        Yields:
            DataFrame chunks

        Raises:
            ProcessingError: If file cannot be read
        """
        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.csv':
                for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                    cls._validate_columns(chunk)
                    yield chunk
            elif file_ext in ['.xlsx', '.xls']:
                # Excel files need to be read entirely first, then chunked manually
                full_df = pd.read_excel(file_path)
                cls._validate_columns(full_df)
                for i in range(0, len(full_df), chunk_size):
                    yield full_df.iloc[i:i + chunk_size]
            else:
                raise ProcessingError(f"Formato de arquivo não suportado: {file_ext}")
        except Exception as e:
            raise ProcessingError(f"Falha ao ler arquivo: {str(e)}")

    @classmethod
    def read_file_bytes(cls, file_bytes: bytes, filename: str, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
        """
        Read file from bytes in chunks.

        Args:
            file_bytes: File content as bytes
            filename: Original filename (for extension detection)
            chunk_size: Number of rows per chunk

        Yields:
            DataFrame chunks

        Raises:
            ProcessingError: If file cannot be read
        """
        file_ext = Path(filename).suffix.lower()

        try:
            if file_ext == '.csv':
                from io import BytesIO
                for chunk in pd.read_csv(BytesIO(file_bytes), chunksize=chunk_size):
                    cls._validate_columns(chunk)
                    yield chunk
            elif file_ext in ['.xlsx', '.xls']:
                from io import BytesIO
                # Excel files need to be read entirely first
                full_df = pd.read_excel(BytesIO(file_bytes))
                cls._validate_columns(full_df)
                for i in range(0, len(full_df), chunk_size):
                    yield full_df.iloc[i:i + chunk_size]
            else:
                raise ProcessingError(f"Formato de arquivo não suportado: {file_ext}")
        except Exception as e:
            raise ProcessingError(f"Falha ao ler arquivo: {str(e)}")

    @classmethod
    def count_rows(cls, file_path: str) -> int:
        """
        Count total rows in file.

        Args:
            file_path: Path to file

        Returns:
            Total number of rows
        """
        file_ext = Path(file_path).suffix.lower()

        try:
            if file_ext == '.csv':
                return sum(1 for _ in pd.read_csv(file_path, chunksize=1000))
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return len(df)
            else:
                raise ProcessingError(f"Formato de arquivo não suportado: {file_ext}")
        except Exception as e:
            raise ProcessingError(f"Falha ao contar linhas: {str(e)}")
