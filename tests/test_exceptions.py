"""
Tests para el módulo de excepciones.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.exceptions import (
    FDDBaseException,
    ConfigurationError,
    InvalidConfigValueError,
    MissingConfigError,
    FileProcessingError,
    FileNotFoundError,
    UnsupportedFileFormatError,
    FileSizeExceededError,
    DataValidationError,
    EmptyDataError,
    MissingColumnError,
    InvalidDataTypeError,
    AIProcessingError,
    OllamaConnectionError,
    ModelNotFoundError,
    ReportGenerationError,
    get_error_description
)


class TestFDDBaseException:
    """Tests para la excepción base."""
    
    def test_basic_creation(self):
        """Test de creación básica."""
        exc = FDDBaseException("Test message")
        
        assert exc.message == "Test message"
        assert exc.code == "FDD_ERROR"
        assert exc.details == {}
    
    def test_with_code_and_details(self):
        """Test con código y detalles."""
        exc = FDDBaseException(
            "Test message",
            code="CUSTOM_CODE",
            details={"key": "value"}
        )
        
        assert exc.code == "CUSTOM_CODE"
        assert exc.details["key"] == "value"
    
    def test_to_dict(self):
        """Test de conversión a diccionario."""
        exc = FDDBaseException("Test", details={"info": "data"})
        result = exc.to_dict()
        
        assert result["error_type"] == "FDDBaseException"
        assert result["message"] == "Test"
        assert result["details"]["info"] == "data"
    
    def test_str_representation(self):
        """Test de representación string."""
        exc = FDDBaseException("Test message")
        assert "[FDD_ERROR] Test message" in str(exc)
        
        exc_with_details = FDDBaseException("Test", details={"key": "val"})
        assert "Detalles:" in str(exc_with_details)


class TestConfigurationErrors:
    """Tests para errores de configuración."""
    
    def test_configuration_error(self):
        """Test ConfigurationError básico."""
        exc = ConfigurationError("Config error")
        assert exc.code == "CONFIG_ERROR"
    
    def test_invalid_config_value(self):
        """Test InvalidConfigValueError."""
        exc = InvalidConfigValueError(
            param_name="timeout",
            value=-1,
            expected="número positivo"
        )
        
        assert exc.code == "INVALID_CONFIG_VALUE"
        assert "timeout" in exc.message
        assert exc.details["param_name"] == "timeout"
        assert exc.details["invalid_value"] == "-1"
    
    def test_missing_config(self):
        """Test MissingConfigError."""
        exc = MissingConfigError("database_url")
        
        assert exc.code == "MISSING_CONFIG"
        assert "database_url" in exc.message


class TestFileProcessingErrors:
    """Tests para errores de procesamiento de archivos."""
    
    def test_file_not_found(self):
        """Test FileNotFoundError."""
        exc = FileNotFoundError("/path/to/file.xlsx")
        
        assert exc.code == "FILE_NOT_FOUND"
        assert "/path/to/file.xlsx" in exc.message
        assert exc.details["filepath"] == "/path/to/file.xlsx"
    
    def test_unsupported_format(self):
        """Test UnsupportedFileFormatError."""
        exc = UnsupportedFileFormatError(
            filepath="/path/to/file.pdf",
            extension=".pdf",
            supported=[".xlsx", ".csv"]
        )
        
        assert exc.code == "UNSUPPORTED_FORMAT"
        assert ".pdf" in exc.message
        assert exc.details["extension"] == ".pdf"
        assert ".xlsx" in exc.details["supported_formats"]
    
    def test_file_size_exceeded(self):
        """Test FileSizeExceededError."""
        exc = FileSizeExceededError(
            filepath="/path/to/large.xlsx",
            actual_size_mb=150.5,
            max_size_mb=100
        )
        
        assert exc.code == "FILE_SIZE_EXCEEDED"
        assert "150.50" in exc.message
        assert exc.details["actual_size_mb"] == 150.5
        assert exc.details["max_size_mb"] == 100


class TestDataValidationErrors:
    """Tests para errores de validación de datos."""
    
    def test_empty_data(self):
        """Test EmptyDataError."""
        exc = EmptyDataError("Sheet1")
        
        assert exc.code == "EMPTY_DATA"
        assert "Sheet1" in exc.message
    
    def test_missing_column(self):
        """Test MissingColumnError."""
        exc = MissingColumnError(
            column_name="total_amount",
            available_columns=["date", "description", "quantity"]
        )
        
        assert exc.code == "MISSING_COLUMN"
        assert "total_amount" in exc.message
        assert "date" in exc.details["available_columns"]
    
    def test_invalid_data_type(self):
        """Test InvalidDataTypeError."""
        exc = InvalidDataTypeError(
            column_name="amount",
            expected_type="numeric",
            actual_type="object"
        )
        
        assert exc.code == "INVALID_DATA_TYPE"
        assert "amount" in exc.message
        assert exc.details["expected_type"] == "numeric"


class TestAIErrors:
    """Tests para errores de IA."""
    
    def test_ollama_connection_error(self):
        """Test OllamaConnectionError."""
        exc = OllamaConnectionError(
            host="localhost",
            port=11434,
            reason="Connection refused"
        )
        
        assert exc.code == "OLLAMA_CONNECTION_ERROR"
        assert "localhost" in exc.message
        assert "11434" in exc.message
    
    def test_model_not_found(self):
        """Test ModelNotFoundError."""
        exc = ModelNotFoundError(
            model_name="gpt-4",
            available_models=["llama3.2", "mistral"]
        )
        
        assert exc.code == "MODEL_NOT_FOUND"
        assert "gpt-4" in exc.message
        assert "llama3.2" in exc.details["available_models"]


class TestErrorDescriptions:
    """Tests para descripciones de errores."""
    
    def test_known_error_codes(self):
        """Test descripciones de códigos conocidos."""
        assert get_error_description("FILE_NOT_FOUND") == "Archivo no encontrado"
        assert get_error_description("DATA_VALIDATION_ERROR") == "Error de validación de datos"
        assert get_error_description("OLLAMA_CONNECTION_ERROR") == "Error de conexión Ollama"
    
    def test_unknown_error_code(self):
        """Test descripción de código desconocido."""
        assert get_error_description("UNKNOWN_CODE") == "Error desconocido"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
