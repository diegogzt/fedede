"""
Configuración centralizada del sistema FDD.

Este módulo gestiona todas las configuraciones del sistema incluyendo:
- Rutas de archivos y directorios
- Parámetros del modelo de IA (Ollama)
- Configuraciones de procesamiento de datos
- Parámetros de generación de reportes
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
from app.config.translations import Language


@dataclass
class PathsConfig:
    """Configuración de rutas del sistema."""
    
    # Directorio base del proyecto
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    # Directorios de datos
    data_dir: Path = field(init=False)
    input_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    templates_dir: Path = field(init=False)
    
    # Directorios de logs y caché
    logs_dir: Path = field(init=False)
    cache_dir: Path = field(init=False)
    
    def __post_init__(self):
        """Inicializa las rutas derivadas."""
        self.data_dir = self.base_dir / "data"
        self.input_dir = self.data_dir / "input"
        self.output_dir = self.data_dir / "output"
        self.templates_dir = self.data_dir / "templates"
        self.logs_dir = self.base_dir / "logs"
        self.cache_dir = self.base_dir / ".cache"
    
    def ensure_directories(self) -> None:
        """Crea todos los directorios necesarios si no existen."""
        directories = [
            self.data_dir,
            self.input_dir,
            self.output_dir,
            self.templates_dir,
            self.logs_dir,
            self.cache_dir
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class AIConfig:
    """Configuración del sistema de IA."""
    
    # Modo de IA
    enabled: bool = True  # Si False, usa solo reglas sin IA
    provider: str = "ollama"  # Proveedor de IA (ollama, none)
    
    # Conexión Ollama
    host: str = "http://localhost"
    port: int = 11434
    
    # Modelo por defecto
    default_model: str = "llama3.2"
    
    # Parámetros de generación
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    
    # Timeouts (en segundos)
    request_timeout: int = 120
    connect_timeout: int = 10
    
    # Reintentos
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Fallback automático si IA no disponible
    auto_fallback: bool = True
    
    # Privacidad
    anonymize_data: bool = False  # Anonimizar datos antes de enviar a IA
    log_prompts: bool = False  # No loguear prompts por privacidad
    
    @property
    def base_url(self) -> str:
        """Retorna la URL base del servidor Ollama."""
        return f"{self.host}:{self.port}"
    
    @property
    def is_ai_enabled(self) -> bool:
        """Verifica si la IA está habilitada y configurada."""
        return self.enabled and self.provider != "none"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario."""
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "host": self.host,
            "port": self.port,
            "model": self.default_model,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_p": self.top_p
            }
        }


# Alias para compatibilidad
OllamaConfig = AIConfig


@dataclass 
class ProcessingConfig:
    """Configuración de procesamiento de datos."""
    
    # Formatos de archivo soportados
    supported_excel_extensions: List[str] = field(
        default_factory=lambda: [".xlsx", ".xls", ".xlsm"]
    )
    supported_csv_extensions: List[str] = field(
        default_factory=lambda: [".csv", ".txt"]
    )
    
    # Límites de procesamiento
    max_file_size_mb: int = 100
    max_rows_per_sheet: int = 1_000_000
    chunk_size: int = 10_000
    
    # Encoding por defecto
    default_encoding: str = "utf-8"
    fallback_encodings: List[str] = field(
        default_factory=lambda: ["latin-1", "cp1252", "iso-8859-1"]
    )
    
    # Procesamiento de fechas
    date_formats: List[str] = field(
        default_factory=lambda: [
            "%d/%m/%Y",
            "%Y-%m-%d", 
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y"
        ]
    )
    
    @property
    def all_supported_extensions(self) -> List[str]:
        """Retorna todas las extensiones soportadas."""
        return self.supported_excel_extensions + self.supported_csv_extensions


@dataclass
class ReportConfig:
    """Configuración de generación de reportes."""
    
    # Idioma del reporte
    language: Language = Language.SPANISH
    
    # Umbrales de materialidad
    materiality_threshold: float = 100000.0  # 100k por defecto
    percentage_threshold: float = 20.0       # 20% por defecto
    
    # Formato de salida
    default_format: str = "xlsx"
    
    # Configuración de Excel
    excel_engine: str = "xlsxwriter"
    
    # Estilos
    header_font_size: int = 12
    body_font_size: int = 10
    header_bg_color: str = "#4472C4"
    header_font_color: str = "#FFFFFF"
    alternate_row_color: str = "#D9E2F3"
    
    # Dimensiones
    default_column_width: int = 15
    max_column_width: int = 50
    
    # Metadatos
    company_name: str = "FDD Automatizado"
    report_author: str = "Sistema Automatizado"


@dataclass
class LoggingConfig:
    """Configuración del sistema de logging."""
    
    # Nivel de log
    level: str = "INFO"
    
    # Formato
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Archivos de log
    log_to_file: bool = True
    log_to_console: bool = True
    log_filename: str = "fdd_system.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # Logs separados por módulo
    separate_error_log: bool = True
    error_log_filename: str = "fdd_errors.log"


class Settings:
    """
    Clase principal de configuración del sistema.
    
    Implementa el patrón Singleton para asegurar una única instancia
    de configuración en todo el sistema.
    """
    
    _instance: Optional['Settings'] = None
    
    def __new__(cls) -> 'Settings':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Inicializar configuraciones
        self.paths = PathsConfig()
        self.ollama = OllamaConfig()
        self.processing = ProcessingConfig()
        self.report = ReportConfig()
        self.logging = LoggingConfig()
        
        # Alias para compatibilidad
        self.ai = self.ollama
        
        # Crear directorios necesarios
        self.paths.ensure_directories()
        
        # Cargar configuración desde archivo si existe
        self._load_config_file()
        
        self._initialized = True
    
    def _load_config_file(self) -> None:
        """Carga configuración desde archivo JSON si existe."""
        config_file = self.paths.base_dir / "config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._apply_config(config_data)
            except (json.JSONDecodeError, IOError) as e:
                # Log del error se manejará después de inicializar el logger
                pass
    
    def _apply_config(self, config_data: Dict[str, Any]) -> None:
        """Aplica configuración desde un diccionario."""
        if "ollama" in config_data:
            for key, value in config_data["ollama"].items():
                if hasattr(self.ollama, key):
                    setattr(self.ollama, key, value)
        
        if "processing" in config_data:
            for key, value in config_data["processing"].items():
                if hasattr(self.processing, key):
                    setattr(self.processing, key, value)
        
        if "report" in config_data:
            for key, value in config_data["report"].items():
                if hasattr(self.report, key):
                    setattr(self.report, key, value)
        
        if "logging" in config_data:
            for key, value in config_data["logging"].items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
    
    def save_config(self, filepath: Optional[Path] = None) -> None:
        """Guarda la configuración actual a un archivo JSON."""
        if filepath is None:
            filepath = self.paths.base_dir / "config.json"
        
        config_data = {
            "ollama": {
                "host": self.ollama.host,
                "port": self.ollama.port,
                "default_model": self.ollama.default_model,
                "temperature": self.ollama.temperature,
                "max_tokens": self.ollama.max_tokens,
                "request_timeout": self.ollama.request_timeout
            },
            "processing": {
                "max_file_size_mb": self.processing.max_file_size_mb,
                "chunk_size": self.processing.chunk_size,
                "default_encoding": self.processing.default_encoding
            },
            "report": {
                "company_name": self.report.company_name,
                "report_author": self.report.report_author,
                "header_bg_color": self.report.header_bg_color
            },
            "logging": {
                "level": self.logging.level,
                "log_to_file": self.logging.log_to_file,
                "log_to_console": self.logging.log_to_console
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def reload(self) -> None:
        """Recarga la configuración desde el archivo."""
        self._initialized = False
        self.__init__()
    
    @classmethod
    def reset(cls) -> None:
        """Reinicia la instancia singleton."""
        cls._instance = None


def get_settings() -> Settings:
    """
    Función de conveniencia para obtener la instancia de configuración.
    
    Returns:
        Settings: Instancia única de configuración del sistema.
    
    Example:
        >>> settings = get_settings()
        >>> print(settings.ollama.default_model)
        'llama3.2'
    """
    return Settings()


# Constantes globales del sistema
APP_NAME = "FDD Automatizado"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Sistema de Asistencia Automatizada para Due Diligence Financiero"

