"""
Excepciones personalizadas del sistema FDD.

Define una jerarquía de excepciones específicas para el dominio
de Due Diligence Financiero, permitiendo un manejo de errores
más preciso y descriptivo.
"""

from typing import Optional, Any, Dict


class FDDBaseException(Exception):
    """
    Excepción base para todas las excepciones del sistema FDD.
    
    Attributes:
        message: Mensaje descriptivo del error
        code: Código de error opcional
        details: Diccionario con detalles adicionales
    """
    
    def __init__(
        self, 
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self._default_code()
        self.details = details or {}
        super().__init__(self.message)
    
    def _default_code(self) -> str:
        """Retorna el código de error por defecto."""
        return "FDD_ERROR"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a un diccionario."""
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }
    
    def __str__(self) -> str:
        if self.details:
            return f"[{self.code}] {self.message} - Detalles: {self.details}"
        return f"[{self.code}] {self.message}"


# =============================================================================
# Excepciones de Configuración
# =============================================================================

class ConfigurationError(FDDBaseException):
    """Error relacionado con la configuración del sistema."""
    
    def _default_code(self) -> str:
        return "CONFIG_ERROR"


class InvalidConfigValueError(ConfigurationError):
    """Valor de configuración inválido."""
    
    def __init__(
        self, 
        param_name: str, 
        value: Any, 
        expected: str,
        **kwargs
    ):
        message = (
            f"Valor inválido para '{param_name}': {value}. "
            f"Se esperaba: {expected}"
        )
        super().__init__(message, **kwargs)
        self.details["param_name"] = param_name
        self.details["invalid_value"] = str(value)
        self.details["expected"] = expected
    
    def _default_code(self) -> str:
        return "INVALID_CONFIG_VALUE"


class MissingConfigError(ConfigurationError):
    """Configuración requerida no encontrada."""
    
    def __init__(self, config_name: str, **kwargs):
        message = f"Configuración requerida no encontrada: '{config_name}'"
        super().__init__(message, **kwargs)
        self.details["config_name"] = config_name
    
    def _default_code(self) -> str:
        return "MISSING_CONFIG"


# =============================================================================
# Excepciones de Procesamiento de Archivos
# =============================================================================

class FileProcessingError(FDDBaseException):
    """Error durante el procesamiento de archivos."""
    
    def __init__(self, message: str, filepath: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if filepath:
            self.details["filepath"] = filepath
    
    def _default_code(self) -> str:
        return "FILE_PROCESSING_ERROR"


class FileNotFoundError(FileProcessingError):
    """Archivo no encontrado."""
    
    def __init__(self, filepath: str, **kwargs):
        message = f"Archivo no encontrado: '{filepath}'"
        super().__init__(message, filepath=filepath, **kwargs)
    
    def _default_code(self) -> str:
        return "FILE_NOT_FOUND"


class UnsupportedFileFormatError(FileProcessingError):
    """Formato de archivo no soportado."""
    
    def __init__(
        self, 
        filepath: str, 
        extension: str,
        supported: list,
        **kwargs
    ):
        message = (
            f"Formato de archivo no soportado: '{extension}'. "
            f"Formatos soportados: {', '.join(supported)}"
        )
        super().__init__(message, filepath=filepath, **kwargs)
        self.details["extension"] = extension
        self.details["supported_formats"] = supported
    
    def _default_code(self) -> str:
        return "UNSUPPORTED_FORMAT"


class FileSizeExceededError(FileProcessingError):
    """Tamaño de archivo excede el límite permitido."""
    
    def __init__(
        self, 
        filepath: str, 
        actual_size_mb: float,
        max_size_mb: float,
        **kwargs
    ):
        message = (
            f"Tamaño de archivo ({actual_size_mb:.2f} MB) excede "
            f"el límite permitido ({max_size_mb} MB)"
        )
        super().__init__(message, filepath=filepath, **kwargs)
        self.details["actual_size_mb"] = actual_size_mb
        self.details["max_size_mb"] = max_size_mb
    
    def _default_code(self) -> str:
        return "FILE_SIZE_EXCEEDED"


class FileReadError(FileProcessingError):
    """Error al leer el archivo."""
    
    def __init__(self, filepath: str, reason: str, **kwargs):
        message = f"Error al leer el archivo: {reason}"
        super().__init__(message, filepath=filepath, **kwargs)
        self.details["reason"] = reason
    
    def _default_code(self) -> str:
        return "FILE_READ_ERROR"


class FileWriteError(FileProcessingError):
    """Error al escribir el archivo."""
    
    def __init__(self, filepath: str, reason: str, **kwargs):
        message = f"Error al escribir el archivo: {reason}"
        super().__init__(message, filepath=filepath, **kwargs)
        self.details["reason"] = reason
    
    def _default_code(self) -> str:
        return "FILE_WRITE_ERROR"


# =============================================================================
# Excepciones de Validación de Datos
# =============================================================================

class DataValidationError(FDDBaseException):
    """Error de validación de datos."""
    
    def _default_code(self) -> str:
        return "DATA_VALIDATION_ERROR"


class EmptyDataError(DataValidationError):
    """Datos vacíos o sin contenido."""
    
    def __init__(self, source: str, **kwargs):
        message = f"Los datos están vacíos o no contienen registros: '{source}'"
        super().__init__(message, **kwargs)
        self.details["source"] = source
    
    def _default_code(self) -> str:
        return "EMPTY_DATA"


class MissingColumnError(DataValidationError):
    """Columna requerida no encontrada."""
    
    def __init__(
        self, 
        column_name: str, 
        available_columns: Optional[list] = None,
        **kwargs
    ):
        message = f"Columna requerida no encontrada: '{column_name}'"
        super().__init__(message, **kwargs)
        self.details["missing_column"] = column_name
        if available_columns:
            self.details["available_columns"] = available_columns
    
    def _default_code(self) -> str:
        return "MISSING_COLUMN"


class InvalidDataTypeError(DataValidationError):
    """Tipo de dato inválido."""
    
    def __init__(
        self, 
        column_name: str,
        expected_type: str,
        actual_type: str,
        **kwargs
    ):
        message = (
            f"Tipo de dato inválido en columna '{column_name}': "
            f"esperado {expected_type}, encontrado {actual_type}"
        )
        super().__init__(message, **kwargs)
        self.details["column_name"] = column_name
        self.details["expected_type"] = expected_type
        self.details["actual_type"] = actual_type
    
    def _default_code(self) -> str:
        return "INVALID_DATA_TYPE"


class DataIntegrityError(DataValidationError):
    """Error de integridad de datos."""
    
    def __init__(self, message: str, rows_affected: Optional[list] = None, **kwargs):
        super().__init__(message, **kwargs)
        if rows_affected:
            self.details["rows_affected"] = rows_affected
    
    def _default_code(self) -> str:
        return "DATA_INTEGRITY_ERROR"


# =============================================================================
# Excepciones de IA/Ollama
# =============================================================================

class AIProcessingError(FDDBaseException):
    """Error durante el procesamiento con IA."""
    
    def _default_code(self) -> str:
        return "AI_PROCESSING_ERROR"


class OllamaConnectionError(AIProcessingError):
    """Error de conexión con Ollama."""
    
    def __init__(self, host: str, port: int, reason: str, **kwargs):
        message = f"No se pudo conectar con Ollama en {host}:{port}: {reason}"
        super().__init__(message, **kwargs)
        self.details["host"] = host
        self.details["port"] = port
        self.details["reason"] = reason
    
    def _default_code(self) -> str:
        return "OLLAMA_CONNECTION_ERROR"


class ModelNotFoundError(AIProcessingError):
    """Modelo de IA no encontrado."""
    
    def __init__(self, model_name: str, available_models: Optional[list] = None, **kwargs):
        message = f"Modelo no encontrado: '{model_name}'"
        super().__init__(message, **kwargs)
        self.details["model_name"] = model_name
        if available_models:
            self.details["available_models"] = available_models
    
    def _default_code(self) -> str:
        return "MODEL_NOT_FOUND"


class AITimeoutError(AIProcessingError):
    """Timeout en la respuesta de IA."""
    
    def __init__(self, timeout_seconds: int, operation: str, **kwargs):
        message = (
            f"Timeout ({timeout_seconds}s) en operación de IA: {operation}"
        )
        super().__init__(message, **kwargs)
        self.details["timeout_seconds"] = timeout_seconds
        self.details["operation"] = operation
    
    def _default_code(self) -> str:
        return "AI_TIMEOUT"


class PromptError(AIProcessingError):
    """Error relacionado con el prompt de IA."""
    
    def _default_code(self) -> str:
        return "PROMPT_ERROR"


# =============================================================================
# Excepciones de Generación de Reportes
# =============================================================================

class ReportGenerationError(FDDBaseException):
    """Error durante la generación de reportes."""
    
    def _default_code(self) -> str:
        return "REPORT_GENERATION_ERROR"


class TemplateNotFoundError(ReportGenerationError):
    """Plantilla de reporte no encontrada."""
    
    def __init__(self, template_name: str, **kwargs):
        message = f"Plantilla de reporte no encontrada: '{template_name}'"
        super().__init__(message, **kwargs)
        self.details["template_name"] = template_name
    
    def _default_code(self) -> str:
        return "TEMPLATE_NOT_FOUND"


class ReportExportError(ReportGenerationError):
    """Error al exportar el reporte."""
    
    def __init__(self, format: str, reason: str, **kwargs):
        message = f"Error al exportar reporte en formato {format}: {reason}"
        super().__init__(message, **kwargs)
        self.details["format"] = format
        self.details["reason"] = reason
    
    def _default_code(self) -> str:
        return "REPORT_EXPORT_ERROR"


# =============================================================================
# Mapeo de códigos de error
# =============================================================================

ERROR_CODES = {
    "FDD_ERROR": "Error general del sistema",
    "CONFIG_ERROR": "Error de configuración",
    "INVALID_CONFIG_VALUE": "Valor de configuración inválido",
    "MISSING_CONFIG": "Configuración faltante",
    "FILE_PROCESSING_ERROR": "Error procesando archivo",
    "FILE_NOT_FOUND": "Archivo no encontrado",
    "UNSUPPORTED_FORMAT": "Formato no soportado",
    "FILE_SIZE_EXCEEDED": "Tamaño de archivo excedido",
    "FILE_READ_ERROR": "Error de lectura",
    "FILE_WRITE_ERROR": "Error de escritura",
    "DATA_VALIDATION_ERROR": "Error de validación de datos",
    "EMPTY_DATA": "Datos vacíos",
    "MISSING_COLUMN": "Columna faltante",
    "INVALID_DATA_TYPE": "Tipo de dato inválido",
    "DATA_INTEGRITY_ERROR": "Error de integridad",
    "AI_PROCESSING_ERROR": "Error de procesamiento IA",
    "OLLAMA_CONNECTION_ERROR": "Error de conexión Ollama",
    "MODEL_NOT_FOUND": "Modelo no encontrado",
    "AI_TIMEOUT": "Timeout de IA",
    "PROMPT_ERROR": "Error de prompt",
    "REPORT_GENERATION_ERROR": "Error generando reporte",
    "TEMPLATE_NOT_FOUND": "Plantilla no encontrada",
    "REPORT_EXPORT_ERROR": "Error exportando reporte",
}


def get_error_description(code: str) -> str:
    """Obtiene la descripción de un código de error."""
    return ERROR_CODES.get(code, "Error desconocido")
