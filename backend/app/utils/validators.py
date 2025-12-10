"""
Validadores de datos.

Proporciona funciones para validación de datos
financieros y estructuras de datos del sistema FDD.
"""

from typing import Any, List, Dict, Optional, Union, Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re

from src.core.exceptions import (
    DataValidationError,
    EmptyDataError,
    MissingColumnError,
    InvalidDataTypeError
)


class DataValidator:
    """
    Clase para validación de datos.
    
    Proporciona métodos de validación para diferentes tipos
    de datos financieros y estructuras comunes.
    """
    
    # Patrones de regex comunes
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^[\d\s\-\+\(\)]{7,20}$",
        "cif_nif": r"^[A-Z]?\d{7,8}[A-Z0-9]?$",
        "iban": r"^[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}$",
        "currency": r"^-?\d{1,3}(,\d{3})*(\.\d{2})?$|^-?\d+(\.\d{2})?$",
        "percentage": r"^-?\d+(\.\d+)?%?$"
    }
    
    @classmethod
    def is_not_empty(cls, value: Any) -> bool:
        """
        Verifica que un valor no esté vacío.
        
        Args:
            value: Valor a verificar
            
        Returns:
            bool: True si no está vacío
        """
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, (list, dict, tuple)) and len(value) == 0:
            return False
        return True
    
    @classmethod
    def is_numeric(cls, value: Any) -> bool:
        """
        Verifica si un valor es numérico.
        
        Args:
            value: Valor a verificar
            
        Returns:
            bool: True si es numérico
        """
        if isinstance(value, (int, float, Decimal)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(",", ".").replace(" ", ""))
                return True
            except ValueError:
                return False
        return False
    
    @classmethod
    def is_positive(cls, value: Union[int, float, str]) -> bool:
        """
        Verifica si un valor numérico es positivo.
        
        Args:
            value: Valor a verificar
            
        Returns:
            bool: True si es positivo
        """
        if not cls.is_numeric(value):
            return False
        
        if isinstance(value, str):
            value = float(value.replace(",", ".").replace(" ", ""))
        
        return value > 0
    
    @classmethod
    def is_valid_date(
        cls, 
        value: Any, 
        formats: Optional[List[str]] = None
    ) -> bool:
        """
        Verifica si un valor es una fecha válida.
        
        Args:
            value: Valor a verificar
            formats: Formatos de fecha a intentar
            
        Returns:
            bool: True si es fecha válida
        """
        if isinstance(value, datetime):
            return True
        
        if not isinstance(value, str):
            return False
        
        if formats is None:
            formats = [
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%d.%m.%Y"
            ]
        
        for fmt in formats:
            try:
                datetime.strptime(value.strip(), fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    @classmethod
    def parse_date(
        cls, 
        value: Any, 
        formats: Optional[List[str]] = None
    ) -> Optional[datetime]:
        """
        Parsea un valor a fecha.
        
        Args:
            value: Valor a parsear
            formats: Formatos a intentar
            
        Returns:
            datetime o None si no se pudo parsear
        """
        if isinstance(value, datetime):
            return value
        
        if not isinstance(value, str):
            return None
        
        if formats is None:
            formats = [
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%d.%m.%Y"
            ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def parse_number(
        cls, 
        value: Any, 
        decimal_separator: str = ",",
        thousands_separator: str = "."
    ) -> Optional[float]:
        """
        Parsea un valor a número.
        
        Args:
            value: Valor a parsear
            decimal_separator: Separador decimal
            thousands_separator: Separador de miles
            
        Returns:
            float o None si no se pudo parsear
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return None
        
        try:
            # Limpiar el string
            cleaned = value.strip()
            
            # Detectar si es negativo por paréntesis: (50,000) -> -50000
            is_negative = False
            if cleaned.startswith('(') and cleaned.endswith(')'):
                is_negative = True
                cleaned = cleaned[1:-1]  # Quitar paréntesis
            
            # Manejar guión como cero o vacío
            if cleaned == '-' or cleaned == '':
                return None
            
            # Reemplazar separadores
            # Detectar formato automáticamente: 
            # - Si tiene coma después de punto: formato europeo (1.234,56)
            # - Si tiene punto después de coma: formato americano (1,234.56)
            # - Si solo tiene comas y el último grupo tiene 3 dígitos: comas son miles
            
            if ',' in cleaned and '.' in cleaned:
                # Ambos separadores presentes
                comma_pos = cleaned.rfind(',')
                dot_pos = cleaned.rfind('.')
                if comma_pos > dot_pos:
                    # Formato europeo: 1.234,56
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Formato americano: 1,234.56
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Solo comas - detectar si es decimal o miles
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Probablemente formato europeo con decimal: 1234,56
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Formato americano con miles: 1,234,567
                    cleaned = cleaned.replace(',', '')
            # Si solo tiene puntos, asumimos que son miles o es un decimal
            
            cleaned = cleaned.replace(" ", "")
            cleaned = cleaned.replace("€", "").replace("$", "")
            cleaned = cleaned.replace("%", "")
            
            result = float(cleaned)
            
            if is_negative:
                result = -result
                
            return result
        except ValueError:
            return None
    
    @classmethod
    def matches_pattern(cls, value: str, pattern_name: str) -> bool:
        """
        Verifica si un valor coincide con un patrón predefinido.
        
        Args:
            value: Valor a verificar
            pattern_name: Nombre del patrón
            
        Returns:
            bool: True si coincide
        """
        if pattern_name not in cls.PATTERNS:
            return False
        
        pattern = cls.PATTERNS[pattern_name]
        return bool(re.match(pattern, value.strip(), re.IGNORECASE))
    
    @classmethod
    def validate_required_columns(
        cls,
        columns: List[str],
        required: List[str]
    ) -> List[str]:
        """
        Valida que existan las columnas requeridas.
        
        Args:
            columns: Columnas disponibles
            required: Columnas requeridas
            
        Returns:
            List[str]: Columnas faltantes
        """
        columns_lower = [c.lower().strip() for c in columns]
        missing = []
        
        for req in required:
            if req.lower().strip() not in columns_lower:
                missing.append(req)
        
        return missing
    
    @classmethod
    def validate_dataframe_not_empty(cls, df, source: str = "DataFrame") -> None:
        """
        Valida que un DataFrame no esté vacío.
        
        Args:
            df: DataFrame a validar
            source: Nombre de la fuente para el mensaje de error
            
        Raises:
            EmptyDataError: Si el DataFrame está vacío
        """
        if df is None or len(df) == 0:
            raise EmptyDataError(source)
    
    @classmethod
    def validate_column_exists(
        cls,
        df,
        column: str
    ) -> None:
        """
        Valida que una columna exista en el DataFrame.
        
        Args:
            df: DataFrame
            column: Nombre de la columna
            
        Raises:
            MissingColumnError: Si la columna no existe
        """
        if column not in df.columns:
            raise MissingColumnError(
                column_name=column,
                available_columns=list(df.columns)
            )
    
    @classmethod
    def validate_column_type(
        cls,
        df,
        column: str,
        expected_types: List[str]
    ) -> None:
        """
        Valida el tipo de datos de una columna.
        
        Args:
            df: DataFrame
            column: Nombre de la columna
            expected_types: Tipos esperados
            
        Raises:
            InvalidDataTypeError: Si el tipo no coincide
        """
        cls.validate_column_exists(df, column)
        
        actual_type = str(df[column].dtype)
        
        if not any(exp in actual_type for exp in expected_types):
            raise InvalidDataTypeError(
                column_name=column,
                expected_type=", ".join(expected_types),
                actual_type=actual_type
            )
    
    @classmethod
    def clean_string(cls, value: Any) -> str:
        """
        Limpia un valor de string.
        
        Args:
            value: Valor a limpiar
            
        Returns:
            str: String limpio
        """
        if value is None:
            return ""
        return str(value).strip()
    
    @classmethod
    def normalize_column_name(cls, name: str) -> str:
        """
        Normaliza un nombre de columna.
        
        Args:
            name: Nombre original
            
        Returns:
            str: Nombre normalizado
        """
        # Quitar espacios y convertir a minúsculas
        normalized = name.strip().lower()
        
        # Reemplazar espacios y caracteres especiales con guion bajo
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)
        
        # Quitar acentos comunes
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    @classmethod
    def create_validation_report(
        cls,
        df,
        validations: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        Crea un reporte de validación para un DataFrame.
        
        Args:
            df: DataFrame a validar
            validations: Diccionario de {columna: función_validación}
            
        Returns:
            dict: Reporte de validación
        """
        report = {
            "total_rows": len(df),
            "columns_validated": [],
            "errors": [],
            "warnings": [],
            "valid": True
        }
        
        for column, validator in validations.items():
            if column not in df.columns:
                report["errors"].append({
                    "column": column,
                    "error": "Columna no encontrada"
                })
                report["valid"] = False
                continue
            
            report["columns_validated"].append(column)
            
            # Aplicar validación
            invalid_mask = ~df[column].apply(validator)
            invalid_count = invalid_mask.sum()
            
            if invalid_count > 0:
                report["errors"].append({
                    "column": column,
                    "invalid_count": int(invalid_count),
                    "invalid_rows": df[invalid_mask].index.tolist()[:10]  # Primeros 10
                })
                report["valid"] = False
        
        return report
