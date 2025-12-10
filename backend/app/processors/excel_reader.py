"""
Lector de archivos Excel/CSV para datos financieros.

Este módulo proporciona la funcionalidad para leer archivos de balance
en formato Excel o CSV y convertirlos a estructuras de datos del sistema.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import re
import logging

from src.processors.models import Account, BalanceSheet, Period
from src.core.exceptions import (
    FileProcessingError,
    FileReadError,
    UnsupportedFileFormatError,
    EmptyDataError
)
from src.utils.file_utils import FileUtils
from src.utils.validators import DataValidator

# Alias para funciones
validate_file_exists = FileUtils.validate_file_exists
validate_file_extension = FileUtils.validate_file_extension

# Obtener parse_number y normalize_column_name de validators
parse_number = DataValidator.parse_number
normalize_column_name = DataValidator.normalize_column_name

# Alias para compatibilidad
InvalidFormatError = UnsupportedFileFormatError
EmptyFileError = EmptyDataError


logger = logging.getLogger(__name__)


class ExcelReader:
    """
    Lector de archivos Excel/CSV para datos de balance financiero.
    
    Soporta formatos:
    - Excel (.xlsx, .xls)
    - CSV (.csv)
    
    Características:
    - Detección automática de columnas de periodos
    - Parsing de números en formato español (parentesis para negativos)
    - Extracción de códigos de cuenta y descripciones
    """
    
    # Extensiones soportadas
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
    
    # Patrones para detectar columnas de periodo
    PERIOD_PATTERNS = [
        r'^[A-Za-z]{3}-\d{2}$',  # Jan-21, Feb-22, etc.
        r'^FY\d{2}$',            # FY23, FY24
        r'^YTD\d{2}$',           # YTD24, YTD25
    ]
    
    # Columnas que identifican código y descripción
    CODE_COLUMNS = ['code', 'codigo', 'cuenta', 'account', 'cta', 'cod']
    DESCRIPTION_COLUMNS = ['description', 'descripcion', 'nombre', 'name', 'concepto']
    
    def __init__(self, file_path: Union[str, Path]):
        """
        Inicializa el lector.
        
        Args:
            file_path: Ruta al archivo a leer
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            InvalidFormatError: Si el formato no es soportado
        """
        self.file_path = Path(file_path)
        
        # Validar existencia
        validate_file_exists(self.file_path)
        
        # Validar extensión
        if self.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            validate_file_extension(self.file_path, list(self.SUPPORTED_EXTENSIONS))
        
        self._df: Optional[pd.DataFrame] = None
        self._periods: List[Period] = []
        self._code_column: Optional[str] = None
        self._description_column: Optional[str] = None
    
    def read(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lee el archivo y retorna un DataFrame.
        
        Args:
            sheet_name: Nombre de la hoja (solo para Excel)
            
        Returns:
            DataFrame con los datos leídos
            
        Raises:
            FileReadError: Si hay error al leer el archivo
            EmptyFileError: Si el archivo está vacío
        """
        try:
            if self.file_path.suffix.lower() == '.csv':
                self._df = self._read_csv()
            else:
                self._df = self._read_excel(sheet_name)
            
            if self._df is None or self._df.empty:
                raise EmptyFileError(
                    file_path=str(self.file_path),
                    message="El archivo no contiene datos"
                )
            
            # Detectar estructura
            self._detect_columns()
            self._detect_periods()
            
            logger.info(f"Archivo leído exitosamente: {self.file_path.name}")
            logger.info(f"  - Filas: {len(self._df)}")
            logger.info(f"  - Columnas: {len(self._df.columns)}")
            logger.info(f"  - Periodos detectados: {len(self._periods)}")
            
            return self._df
            
        except pd.errors.EmptyDataError:
            raise EmptyFileError(
                file_path=str(self.file_path),
                message="El archivo está vacío"
            )
        except Exception as e:
            if isinstance(e, (EmptyFileError, FileReadError)):
                raise
            raise FileReadError(
                file_path=str(self.file_path),
                message=f"Error al leer el archivo: {str(e)}"
            )
    
    def _read_csv(self) -> pd.DataFrame:
        """Lee un archivo CSV."""
        # Intentar diferentes encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    self.file_path,
                    encoding=encoding,
                    dtype=str,  # Leer todo como string inicialmente
                    na_values=['', 'NA', 'N/A', '-'],
                    keep_default_na=True
                )
                logger.debug(f"CSV leído con encoding: {encoding}")
                
                # Detectar si la primera fila contiene los encabezados reales
                df = self._detect_and_fix_headers(df)
                
                return df
            except UnicodeDecodeError:
                continue
        
        raise FileReadError(
            file_path=str(self.file_path),
            message="No se pudo detectar el encoding del archivo CSV"
        )
    
    def _detect_and_fix_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detecta si los encabezados están en una fila diferente y corrige el DataFrame.
        
        Algunos archivos tienen una fila de totales u otros datos antes de los encabezados reales.
        Esta función busca la fila que contiene 'Code', 'Description', o patrones de periodo
        y la usa como encabezado.
        """
        # Verificar si los encabezados actuales parecen ser columnas válidas
        has_valid_headers = False
        for col in df.columns:
            col_str = str(col).strip().lower()
            # Verificar si es un nombre de columna válido
            if col_str in ['code', 'codigo', 'description', 'descripcion', 'cuenta']:
                has_valid_headers = True
                break
            # Verificar si es un patrón de periodo
            for pattern in self.PERIOD_PATTERNS:
                if re.match(pattern, str(col).strip(), re.IGNORECASE):
                    has_valid_headers = True
                    break
            if has_valid_headers:
                break
        
        if has_valid_headers:
            return df
        
        # Buscar la fila que contiene los encabezados reales (máximo primeras 10 filas)
        header_row = None
        for idx in range(min(10, len(df))):
            row = df.iloc[idx]
            for val in row.values:
                val_str = str(val).strip().lower()
                if val_str in ['code', 'codigo', 'description', 'descripcion']:
                    header_row = idx
                    break
                # Verificar patrones de periodo
                for pattern in self.PERIOD_PATTERNS:
                    if re.match(pattern, str(val).strip(), re.IGNORECASE):
                        header_row = idx
                        break
                if header_row is not None:
                    break
            if header_row is not None:
                break
        
        if header_row is not None:
            logger.info(f"Encabezados detectados en fila {header_row + 1}, reajustando DataFrame")
            # Usar la fila encontrada como encabezados
            new_headers = df.iloc[header_row].values
            # Crear nuevo DataFrame sin las filas antes del encabezado
            df = df.iloc[header_row + 1:].reset_index(drop=True)
            df.columns = new_headers
            
        return df
    
    def _read_excel(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Lee un archivo Excel."""
        try:
            # Si no se especifica hoja, usar la primera
            sheet = sheet_name or 0
            
            df = pd.read_excel(
                self.file_path,
                sheet_name=sheet,
                dtype=str,
                na_values=['', 'NA', 'N/A', '-'],
                keep_default_na=True
            )
            
            logger.debug(f"Excel leído, hoja: {sheet_name or 'primera'}")
            
            # Detectar si la primera fila contiene los encabezados reales
            df = self._detect_and_fix_headers(df)
            
            return df
            
        except Exception as e:
            raise FileReadError(
                file_path=str(self.file_path),
                message=f"Error al leer Excel: {str(e)}"
            )
    
    def _detect_columns(self) -> None:
        """Detecta las columnas de código y descripción."""
        if self._df is None:
            return
        
        columns_lower = {col: str(col).lower().strip() for col in self._df.columns}
        
        # Buscar columna de código
        for col, col_lower in columns_lower.items():
            normalized = normalize_column_name(col_lower)
            if normalized in self.CODE_COLUMNS or 'code' in normalized or 'codigo' in normalized:
                self._code_column = col
                break
        
        # Buscar columna de descripción
        for col, col_lower in columns_lower.items():
            normalized = normalize_column_name(col_lower)
            if normalized in self.DESCRIPTION_COLUMNS or 'description' in normalized or 'descripcion' in normalized:
                self._description_column = col
                break
        
        # Si no se encontraron, usar las primeras columnas no vacías con datos válidos
        if self._code_column is None or self._description_column is None:
            # Buscar columnas que contengan códigos numéricos (cuentas contables)
            for col in self._df.columns:
                if self._code_column is not None and self._description_column is not None:
                    break
                    
                col_str = str(col).strip()
                # Saltar columnas sin nombre o con nombre de periodo
                if col_str.startswith('Unnamed') or not col_str:
                    # Verificar si esta columna contiene códigos de cuenta
                    sample_values = self._df[col].dropna().head(10)
                    has_account_codes = False
                    has_descriptions = False
                    
                    for val in sample_values:
                        val_str = str(val).strip()
                        # Código de cuenta: 8 dígitos numéricos
                        if re.match(r'^\d{8}$', val_str):
                            has_account_codes = True
                        # Descripción: texto no numérico
                        elif val_str and not val_str.replace('.', '').replace(',', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
                            has_descriptions = True
                    
                    if has_account_codes and self._code_column is None:
                        self._code_column = col
                        logger.info(f"Detectada columna de códigos de cuenta: {col}")
                    elif has_descriptions and self._description_column is None and self._code_column != col:
                        self._description_column = col
                        logger.info(f"Detectada columna de descripciones: {col}")
        
        # Fallback: usar las dos primeras columnas
        if self._code_column is None and len(self._df.columns) >= 1:
            self._code_column = self._df.columns[0]
            logger.warning(f"Usando primera columna como código: {self._code_column}")
        
        if self._description_column is None and len(self._df.columns) >= 2:
            self._description_column = self._df.columns[1]
            logger.warning(f"Usando segunda columna como descripción: {self._description_column}")
        
        logger.info(f"Columna de código: {self._code_column}")
        logger.info(f"Columna de descripción: {self._description_column}")
    
    def _detect_periods(self) -> None:
        """Detecta las columnas que representan periodos."""
        if self._df is None:
            return
        
        self._periods = []
        
        for col in self._df.columns:
            if col in [self._code_column, self._description_column]:
                continue
            
            # Verificar si el nombre de columna coincide con un patrón de periodo
            is_period = False
            for pattern in self.PERIOD_PATTERNS:
                if re.match(pattern, str(col).strip(), re.IGNORECASE):
                    is_period = True
                    break
            
            if is_period:
                period = Period.from_string(str(col).strip())
                self._periods.append(period)
        
        # Ordenar periodos cronológicamente
        self._periods.sort()
    
    def to_balance_sheet(self) -> BalanceSheet:
        """
        Convierte los datos leídos a un BalanceSheet.
        
        Returns:
            BalanceSheet con las cuentas y periodos
            
        Raises:
            InvalidFormatError: Si la estructura no es válida
        """
        if self._df is None:
            self.read()
        
        if self._df is None:
            raise InvalidFormatError(
                expected_format="DataFrame válido",
                actual_format="None"
            )
        
        accounts: List[Account] = []
        period_columns = [p.name for p in self._periods]
        
        for idx, row in self._df.iterrows():
            # Obtener código y descripción
            code = str(row.get(self._code_column, '')).strip()
            description = str(row.get(self._description_column, '')).strip()
            
            # Saltar filas sin código
            if not code or code == 'nan':
                continue
            
            # Parsear valores por periodo
            values: Dict[str, float] = {}
            for period_name in period_columns:
                if period_name in row:
                    raw_value = row[period_name]
                    parsed = parse_number(raw_value)
                    if parsed is not None:
                        values[period_name] = parsed
            
            # Crear cuenta
            account = Account(
                code=code,
                description=description,
                values=values,
                level=self._detect_account_level(code)
            )
            accounts.append(account)
        
        # Crear BalanceSheet
        balance = BalanceSheet(
            accounts=accounts,
            periods=self._periods.copy(),
            source_file=str(self.file_path),
            metadata={
                'total_rows': len(self._df),
                'parsed_accounts': len(accounts),
                'period_count': len(self._periods)
            }
        )
        
        logger.info(f"BalanceSheet creado: {len(accounts)} cuentas, {len(self._periods)} periodos")
        
        return balance
    
    def _detect_account_level(self, code: str) -> int:
        """
        Detecta el nivel de cuenta basado en ceros finales.
        
        Ej:
        - 10000000 -> nivel 0 (cuenta mayor)
        - 10100000 -> nivel 1
        - 10101000 -> nivel 2
        - 10101100 -> nivel 3
        """
        if not code or not code.isdigit():
            return 0
        
        # Contar ceros finales
        trailing_zeros = len(code) - len(code.rstrip('0'))
        
        # Más ceros = nivel más alto en jerarquía
        level_map = {
            7: 0,  # X0000000 - cuenta principal
            6: 1,  # XX000000
            5: 2,  # XXX00000
            4: 3,  # XXXX0000
            3: 4,  # XXXXX000
            2: 5,  # XXXXXX00
            1: 6,  # XXXXXXX0
            0: 7,  # XXXXXXXX - cuenta más detallada
        }
        
        return level_map.get(trailing_zeros, 0)
    
    def get_periods(self) -> List[Period]:
        """Retorna los periodos detectados."""
        return self._periods.copy()
    
    def get_period_names(self) -> List[str]:
        """Retorna los nombres de los periodos."""
        return [p.name for p in self._periods]
    
    def get_column_info(self) -> Dict[str, Any]:
        """Retorna información sobre las columnas detectadas."""
        return {
            'code_column': self._code_column,
            'description_column': self._description_column,
            'period_columns': self.get_period_names(),
            'all_columns': list(self._df.columns) if self._df is not None else []
        }
    
    def get_sheet_names(self) -> List[str]:
        """Retorna los nombres de las hojas (solo para Excel)."""
        if self.file_path.suffix.lower() in ['.xlsx', '.xls']:
            try:
                xlsx = pd.ExcelFile(self.file_path)
                return xlsx.sheet_names
            except Exception:
                pass
        return []
    
    def preview(self, rows: int = 5) -> pd.DataFrame:
        """Retorna una vista previa de los datos."""
        if self._df is None:
            self.read()
        
        if self._df is not None:
            return self._df.head(rows)
        
        return pd.DataFrame()


def read_balance_file(file_path: Union[str, Path]) -> BalanceSheet:
    """
    Función de conveniencia para leer un archivo de balance.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        BalanceSheet con los datos
    """
    reader = ExcelReader(file_path)
    reader.read()
    return reader.to_balance_sheet()
