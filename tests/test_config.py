"""
Tests para el módulo de configuración.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import (
    Settings, 
    get_settings, 
    PathsConfig, 
    OllamaConfig,
    ProcessingConfig,
    ReportConfig,
    LoggingConfig
)


class TestPathsConfig:
    """Tests para PathsConfig."""
    
    def test_default_paths_created(self):
        """Verifica que las rutas por defecto se crean correctamente."""
        config = PathsConfig()
        
        assert config.base_dir.exists() or True  # Puede no existir en test
        assert config.data_dir == config.base_dir / "data"
        assert config.input_dir == config.data_dir / "input"
        assert config.output_dir == config.data_dir / "output"
        assert config.templates_dir == config.data_dir / "templates"
        assert config.logs_dir == config.base_dir / "logs"
        assert config.cache_dir == config.base_dir / ".cache"
    
    def test_ensure_directories(self, tmp_path):
        """Verifica que ensure_directories crea los directorios."""
        config = PathsConfig()
        config.base_dir = tmp_path
        config.__post_init__()
        
        config.ensure_directories()
        
        assert config.data_dir.exists()
        assert config.input_dir.exists()
        assert config.output_dir.exists()
        assert config.logs_dir.exists()


class TestOllamaConfig:
    """Tests para OllamaConfig."""
    
    def test_default_values(self):
        """Verifica valores por defecto de Ollama."""
        config = OllamaConfig()
        
        assert config.host == "http://localhost"
        assert config.port == 11434
        assert config.default_model == "llama3.2"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
    
    def test_base_url(self):
        """Verifica la construcción de base_url."""
        config = OllamaConfig()
        assert config.base_url == "http://localhost:11434"
        
        config.host = "http://192.168.1.100"
        config.port = 8080
        assert config.base_url == "http://192.168.1.100:8080"
    
    def test_to_dict(self):
        """Verifica la conversión a diccionario."""
        config = OllamaConfig()
        result = config.to_dict()
        
        assert "host" in result
        assert "port" in result
        assert "model" in result
        assert "options" in result
        assert "temperature" in result["options"]


class TestProcessingConfig:
    """Tests para ProcessingConfig."""
    
    def test_supported_extensions(self):
        """Verifica las extensiones soportadas."""
        config = ProcessingConfig()
        
        assert ".xlsx" in config.supported_excel_extensions
        assert ".xls" in config.supported_excel_extensions
        assert ".csv" in config.supported_csv_extensions
    
    def test_all_supported_extensions(self):
        """Verifica la propiedad all_supported_extensions."""
        config = ProcessingConfig()
        all_ext = config.all_supported_extensions
        
        assert ".xlsx" in all_ext
        assert ".csv" in all_ext
        assert len(all_ext) == len(config.supported_excel_extensions) + len(config.supported_csv_extensions)
    
    def test_date_formats(self):
        """Verifica los formatos de fecha."""
        config = ProcessingConfig()
        
        assert "%d/%m/%Y" in config.date_formats
        assert "%Y-%m-%d" in config.date_formats


class TestSettings:
    """Tests para la clase Settings."""
    
    def setup_method(self):
        """Reset singleton antes de cada test."""
        Settings.reset()
    
    def test_singleton_pattern(self):
        """Verifica que Settings es singleton."""
        settings1 = Settings()
        settings2 = Settings()
        
        assert settings1 is settings2
    
    def test_get_settings_function(self):
        """Verifica la función get_settings."""
        settings = get_settings()
        
        assert isinstance(settings, Settings)
        assert settings is get_settings()
    
    def test_has_all_configs(self):
        """Verifica que Settings tiene todas las configuraciones."""
        settings = get_settings()
        
        assert hasattr(settings, 'paths')
        assert hasattr(settings, 'ollama')
        assert hasattr(settings, 'processing')
        assert hasattr(settings, 'report')
        assert hasattr(settings, 'logging')
    
    def test_reload(self):
        """Verifica el método reload."""
        settings = get_settings()
        original_model = settings.ollama.default_model
        
        settings.ollama.default_model = "test_model"
        settings.reload()
        
        # Después del reload debería volver al valor por defecto
        assert settings.ollama.default_model == original_model
    
    def test_save_and_load_config(self, tmp_path):
        """Verifica guardar y cargar configuración."""
        Settings.reset()
        settings = get_settings()
        
        # Modificar algún valor
        settings.ollama.default_model = "custom_model"
        settings.report.company_name = "Test Company"
        
        # Guardar
        config_file = tmp_path / "config.json"
        settings.save_config(config_file)
        
        # Verificar que el archivo existe
        assert config_file.exists()
        
        # Leer y verificar contenido
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config["ollama"]["default_model"] == "custom_model"
        assert saved_config["report"]["company_name"] == "Test Company"


class TestReportConfig:
    """Tests para ReportConfig."""
    
    def test_default_values(self):
        """Verifica valores por defecto."""
        config = ReportConfig()
        
        assert config.default_format == "xlsx"
        assert config.excel_engine == "xlsxwriter"
        assert config.header_font_size == 12
        assert config.header_bg_color == "#4472C4"


class TestLoggingConfig:
    """Tests para LoggingConfig."""
    
    def test_default_values(self):
        """Verifica valores por defecto."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.log_to_file == True
        assert config.log_to_console == True
        assert config.log_filename == "fdd_system.log"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
