"""
Sistema de Logging del FDD.

Proporciona un sistema de logging centralizado con:
- Logging a consola y archivo
- Rotación automática de archivos de log
- Colores en consola para mejor legibilidad
- Logs separados para errores
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime

from app.config.settings import get_settings


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para la consola."""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea el registro con colores."""
        # Guardar el levelname original
        original_levelname = record.levelname
        
        # Aplicar color si está disponible
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{self.BOLD}"
                f"{record.levelname}{self.RESET}"
            )
        
        # Formatear el mensaje
        result = super().format(record)
        
        # Restaurar el levelname original
        record.levelname = original_levelname
        
        return result


class FDDLogger:
    """
    Logger centralizado para el sistema FDD.
    
    Características:
    - Singleton para asegurar configuración única
    - Logging a consola con colores
    - Logging a archivo con rotación
    - Log separado para errores
    """
    
    _instance: Optional['FDDLogger'] = None
    _loggers: dict = {}
    
    def __new__(cls) -> 'FDDLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.settings = get_settings()
        self._setup_logging()
        self._initialized = True
    
    def _setup_logging(self) -> None:
        """Configura el sistema de logging."""
        config = self.settings.logging
        
        # Crear directorio de logs si no existe
        log_dir = self.settings.paths.logs_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar el logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.level.upper()))
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Handler de consola
        if config.log_to_console:
            console_handler = self._create_console_handler(config)
            root_logger.addHandler(console_handler)
        
        # Handler de archivo principal
        if config.log_to_file:
            file_handler = self._create_file_handler(
                log_dir / config.log_filename,
                config
            )
            root_logger.addHandler(file_handler)
            
            # Handler separado para errores
            if config.separate_error_log:
                error_handler = self._create_error_handler(
                    log_dir / config.error_log_filename,
                    config
                )
                root_logger.addHandler(error_handler)
    
    def _create_console_handler(self, config) -> logging.StreamHandler:
        """Crea el handler de consola con colores."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.level.upper()))
        
        # Usar formatter con colores
        formatter = ColoredFormatter(
            fmt=config.format,
            datefmt=config.date_format
        )
        console_handler.setFormatter(formatter)
        
        return console_handler
    
    def _create_file_handler(
        self, 
        filepath: Path, 
        config
    ) -> RotatingFileHandler:
        """Crea el handler de archivo con rotación."""
        file_handler = RotatingFileHandler(
            filename=str(filepath),
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        
        formatter = logging.Formatter(
            fmt=config.format,
            datefmt=config.date_format
        )
        file_handler.setFormatter(formatter)
        
        return file_handler
    
    def _create_error_handler(
        self, 
        filepath: Path, 
        config
    ) -> RotatingFileHandler:
        """Crea el handler separado para errores."""
        error_handler = RotatingFileHandler(
            filename=str(filepath),
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            fmt=config.format,
            datefmt=config.date_format
        )
        error_handler.setFormatter(formatter)
        
        return error_handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtiene un logger con el nombre especificado.
        
        Args:
            name: Nombre del logger (generalmente __name__)
            
        Returns:
            Logger configurado
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]
    
    @classmethod
    def reset(cls) -> None:
        """Reinicia la instancia del logger."""
        cls._instance = None
        cls._loggers = {}


def get_logger(name: str) -> logging.Logger:
    """
    Función de conveniencia para obtener un logger.
    
    Args:
        name: Nombre del logger (usar __name__)
        
    Returns:
        Logger configurado
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensaje informativo")
        >>> logger.error("Mensaje de error")
    """
    fdd_logger = FDDLogger()
    return fdd_logger.get_logger(name)


class LogContext:
    """
    Context manager para logging de operaciones.
    
    Útil para registrar inicio y fin de operaciones con timing.
    
    Example:
        >>> with LogContext(logger, "Procesamiento de archivo"):
        ...     # Operación
        ...     pass
    """
    
    def __init__(
        self, 
        logger: logging.Logger, 
        operation: str,
        level: int = logging.INFO
    ):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time: Optional[datetime] = None
    
    def __enter__(self) -> 'LogContext':
        self.start_time = datetime.now()
        self.logger.log(self.level, f"Iniciando: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed = datetime.now() - self.start_time
        elapsed_ms = elapsed.total_seconds() * 1000
        
        if exc_type is not None:
            self.logger.error(
                f"Error en {self.operation}: {exc_val} "
                f"(tiempo: {elapsed_ms:.2f}ms)"
            )
            return False
        
        self.logger.log(
            self.level,
            f"Completado: {self.operation} (tiempo: {elapsed_ms:.2f}ms)"
        )
        return True

