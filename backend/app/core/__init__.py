"""
Módulo Core - Componentes centrales del sistema FDD.
"""

from .exceptions import (
    FDDBaseException,
    ConfigurationError,
    FileProcessingError,
    DataValidationError,
    AIProcessingError,
    ReportGenerationError
)

__all__ = [
    'FDDBaseException',
    'ConfigurationError', 
    'FileProcessingError',
    'DataValidationError',
    'AIProcessingError',
    'ReportGenerationError'
]
