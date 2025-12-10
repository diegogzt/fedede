"""
Utilidades para manejo de archivos.

Proporciona funciones para:
- Validación de archivos
- Lectura y escritura de archivos
- Gestión de rutas y directorios
- Operaciones de limpieza
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Union, Generator
from datetime import datetime
import hashlib

from app.config.settings import get_settings
from app.core.exceptions import (
    FileNotFoundError,
    UnsupportedFileFormatError,
    FileSizeExceededError,
    FileReadError,
    FileWriteError
)


class FileUtils:
    """
    Clase de utilidades para manejo de archivos.
    
    Proporciona métodos estáticos y de clase para operaciones
    comunes de archivos en el sistema FDD.
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    @classmethod
    def validate_file_exists(cls, filepath: Union[str, Path]) -> Path:
        """
        Valida que un archivo existe.
        
        Args:
            filepath: Ruta al archivo
            
        Returns:
            Path: Objeto Path del archivo
            
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(str(filepath))
        return path
    
    @classmethod
    def validate_file_extension(
        cls, 
        filepath: Union[str, Path],
        allowed_extensions: Optional[List[str]] = None
    ) -> str:
        """
        Valida que la extensión del archivo sea soportada.
        
        Args:
            filepath: Ruta al archivo
            allowed_extensions: Lista de extensiones permitidas
            
        Returns:
            str: Extensión del archivo (en minúsculas)
            
        Raises:
            UnsupportedFileFormatError: Si la extensión no es soportada
        """
        path = Path(filepath)
        extension = path.suffix.lower()
        
        if allowed_extensions is None:
            settings = get_settings()
            allowed_extensions = settings.processing.all_supported_extensions
        
        if extension not in allowed_extensions:
            raise UnsupportedFileFormatError(
                filepath=str(filepath),
                extension=extension,
                supported=allowed_extensions
            )
        
        return extension
    
    @classmethod
    def validate_file_size(
        cls, 
        filepath: Union[str, Path],
        max_size_mb: Optional[float] = None
    ) -> float:
        """
        Valida que el tamaño del archivo no exceda el límite.
        
        Args:
            filepath: Ruta al archivo
            max_size_mb: Tamaño máximo en MB
            
        Returns:
            float: Tamaño del archivo en MB
            
        Raises:
            FileSizeExceededError: Si el archivo excede el límite
        """
        path = Path(filepath)
        
        if max_size_mb is None:
            settings = get_settings()
            max_size_mb = settings.processing.max_file_size_mb
        
        size_bytes = path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            raise FileSizeExceededError(
                filepath=str(filepath),
                actual_size_mb=size_mb,
                max_size_mb=max_size_mb
            )
        
        return size_mb
    
    @classmethod
    def validate_file(
        cls,
        filepath: Union[str, Path],
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: Optional[float] = None
    ) -> Path:
        """
        Realiza todas las validaciones de archivo.
        
        Args:
            filepath: Ruta al archivo
            allowed_extensions: Extensiones permitidas
            max_size_mb: Tamaño máximo en MB
            
        Returns:
            Path: Objeto Path validado
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            UnsupportedFileFormatError: Si la extensión no es soportada
            FileSizeExceededError: Si el archivo excede el límite
        """
        path = cls.validate_file_exists(filepath)
        cls.validate_file_extension(path, allowed_extensions)
        cls.validate_file_size(path, max_size_mb)
        return path
    
    @classmethod
    def get_file_info(cls, filepath: Union[str, Path]) -> dict:
        """
        Obtiene información detallada de un archivo.
        
        Args:
            filepath: Ruta al archivo
            
        Returns:
            dict: Información del archivo
        """
        path = Path(filepath)
        stat = path.stat()
        
        return {
            "name": path.name,
            "stem": path.stem,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "parent": str(path.parent),
            "absolute_path": str(path.absolute())
        }
    
    @classmethod
    def get_file_hash(
        cls, 
        filepath: Union[str, Path], 
        algorithm: str = "md5"
    ) -> str:
        """
        Calcula el hash de un archivo.
        
        Args:
            filepath: Ruta al archivo
            algorithm: Algoritmo de hash (md5, sha256, etc.)
            
        Returns:
            str: Hash del archivo en hexadecimal
        """
        path = Path(filepath)
        hash_obj = hashlib.new(algorithm)
        
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @classmethod
    def list_files(
        cls,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        Lista archivos en un directorio.
        
        Args:
            directory: Directorio a listar
            pattern: Patrón glob para filtrar
            recursive: Si buscar recursivamente
            
        Returns:
            List[Path]: Lista de archivos encontrados
        """
        path = Path(directory)
        
        if recursive:
            return list(path.rglob(pattern))
        return list(path.glob(pattern))
    
    @classmethod
    def list_excel_files(
        cls,
        directory: Union[str, Path],
        recursive: bool = False
    ) -> List[Path]:
        """
        Lista archivos Excel en un directorio.
        
        Args:
            directory: Directorio a buscar
            recursive: Si buscar recursivamente
            
        Returns:
            List[Path]: Lista de archivos Excel
        """
        settings = get_settings()
        extensions = settings.processing.supported_excel_extensions
        
        files = []
        for ext in extensions:
            pattern = f"*{ext}"
            files.extend(cls.list_files(directory, pattern, recursive))
        
        return sorted(files)
    
    @classmethod
    def ensure_directory(cls, directory: Union[str, Path]) -> Path:
        """
        Asegura que un directorio existe, creándolo si es necesario.
        
        Args:
            directory: Ruta del directorio
            
        Returns:
            Path: Objeto Path del directorio
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def generate_unique_filename(
        cls,
        base_name: str,
        extension: str,
        directory: Union[str, Path],
        include_timestamp: bool = True
    ) -> Path:
        """
        Genera un nombre de archivo único.
        
        Args:
            base_name: Nombre base del archivo
            extension: Extensión del archivo
            directory: Directorio destino
            include_timestamp: Si incluir timestamp
            
        Returns:
            Path: Ruta única del archivo
        """
        path = Path(directory)
        
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}{extension}"
        else:
            filename = f"{base_name}{extension}"
        
        filepath = path / filename
        
        # Si existe, agregar contador
        counter = 1
        while filepath.exists():
            if include_timestamp:
                filename = f"{base_name}_{timestamp}_{counter}{extension}"
            else:
                filename = f"{base_name}_{counter}{extension}"
            filepath = path / filename
            counter += 1
        
        return filepath
    
    @classmethod
    def safe_copy(
        cls,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> Path:
        """
        Copia un archivo de forma segura.
        
        Args:
            source: Archivo origen
            destination: Destino
            overwrite: Si sobrescribir si existe
            
        Returns:
            Path: Ruta del archivo copiado
        """
        src = Path(source)
        dst = Path(destination)
        
        cls.validate_file_exists(src)
        
        if dst.is_dir():
            dst = dst / src.name
        
        if dst.exists() and not overwrite:
            raise FileWriteError(
                filepath=str(dst),
                reason="El archivo ya existe y overwrite=False"
            )
        
        # Asegurar que el directorio destino existe
        cls.ensure_directory(dst.parent)
        
        shutil.copy2(str(src), str(dst))
        return dst
    
    @classmethod
    def safe_delete(
        cls,
        filepath: Union[str, Path],
        missing_ok: bool = True
    ) -> bool:
        """
        Elimina un archivo de forma segura.
        
        Args:
            filepath: Archivo a eliminar
            missing_ok: Si ignorar si no existe
            
        Returns:
            bool: True si se eliminó, False si no existía
        """
        path = Path(filepath)
        
        if not path.exists():
            if missing_ok:
                return False
            raise FileNotFoundError(str(filepath))
        
        path.unlink()
        return True
    
    @classmethod
    def clean_directory(
        cls,
        directory: Union[str, Path],
        pattern: str = "*",
        older_than_days: Optional[int] = None
    ) -> int:
        """
        Limpia archivos de un directorio.
        
        Args:
            directory: Directorio a limpiar
            pattern: Patrón de archivos a eliminar
            older_than_days: Solo eliminar archivos más antiguos
            
        Returns:
            int: Número de archivos eliminados
        """
        path = Path(directory)
        deleted = 0
        
        if older_than_days is not None:
            cutoff = datetime.now().timestamp() - (older_than_days * 86400)
        else:
            cutoff = None
        
        for file in path.glob(pattern):
            if file.is_file():
                if cutoff is None or file.stat().st_mtime < cutoff:
                    file.unlink()
                    deleted += 1
        
        return deleted
    
    @classmethod
    def read_text_file(
        cls,
        filepath: Union[str, Path],
        encoding: Optional[str] = None
    ) -> str:
        """
        Lee un archivo de texto.
        
        Args:
            filepath: Ruta al archivo
            encoding: Encoding a usar
            
        Returns:
            str: Contenido del archivo
        """
        path = cls.validate_file_exists(filepath)
        settings = get_settings()
        
        encodings_to_try = [encoding] if encoding else []
        encodings_to_try.append(settings.processing.default_encoding)
        encodings_to_try.extend(settings.processing.fallback_encodings)
        
        for enc in encodings_to_try:
            if enc is None:
                continue
            try:
                with open(path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise FileReadError(
            filepath=str(filepath),
            reason="No se pudo decodificar el archivo con ningún encoding soportado"
        )
    
    @classmethod
    def write_text_file(
        cls,
        filepath: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True
    ) -> Path:
        """
        Escribe contenido a un archivo de texto.
        
        Args:
            filepath: Ruta del archivo
            content: Contenido a escribir
            encoding: Encoding a usar
            create_dirs: Si crear directorios necesarios
            
        Returns:
            Path: Ruta del archivo escrito
        """
        path = Path(filepath)
        
        if create_dirs:
            cls.ensure_directory(path.parent)
        
        try:
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return path
        except IOError as e:
            raise FileWriteError(
                filepath=str(filepath),
                reason=str(e)
            )

