"""
Tests para utilidades de archivos y validadores.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.file_utils import FileUtils
from src.utils.validators import DataValidator
from src.core.exceptions import (
    FileNotFoundError,
    UnsupportedFileFormatError,
    FileSizeExceededError
)


class TestFileUtils:
    """Tests para FileUtils."""
    
    def test_validate_file_exists_success(self, tmp_path):
        """Test validación de archivo existente."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = FileUtils.validate_file_exists(test_file)
        
        assert result == test_file
        assert result.exists()
    
    def test_validate_file_exists_failure(self):
        """Test validación de archivo no existente."""
        with pytest.raises(FileNotFoundError):
            FileUtils.validate_file_exists("/nonexistent/file.txt")
    
    def test_validate_file_extension_success(self, tmp_path):
        """Test validación de extensión válida."""
        test_file = tmp_path / "test.xlsx"
        test_file.write_text("")
        
        ext = FileUtils.validate_file_extension(
            test_file, 
            [".xlsx", ".xls", ".csv"]
        )
        
        assert ext == ".xlsx"
    
    def test_validate_file_extension_failure(self, tmp_path):
        """Test validación de extensión inválida."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("")
        
        with pytest.raises(UnsupportedFileFormatError) as exc_info:
            FileUtils.validate_file_extension(
                test_file, 
                [".xlsx", ".csv"]
            )
        
        assert exc_info.value.details["extension"] == ".pdf"
    
    def test_get_file_info(self, tmp_path):
        """Test obtención de información de archivo."""
        test_file = tmp_path / "test.xlsx"
        test_file.write_text("test content" * 100)
        
        info = FileUtils.get_file_info(test_file)
        
        assert info["name"] == "test.xlsx"
        assert info["stem"] == "test"
        assert info["extension"] == ".xlsx"
        assert info["size_bytes"] > 0
        assert isinstance(info["created"], datetime)
    
    def test_ensure_directory(self, tmp_path):
        """Test creación de directorio."""
        new_dir = tmp_path / "new" / "nested" / "directory"
        
        result = FileUtils.ensure_directory(new_dir)
        
        assert result.exists()
        assert result.is_dir()
    
    def test_generate_unique_filename(self, tmp_path):
        """Test generación de nombre único."""
        filename = FileUtils.generate_unique_filename(
            base_name="report",
            extension=".xlsx",
            directory=tmp_path,
            include_timestamp=True
        )
        
        assert filename.parent == tmp_path
        assert filename.suffix == ".xlsx"
        assert "report" in filename.stem
    
    def test_generate_unique_filename_collision(self, tmp_path):
        """Test nombre único con colisión."""
        # Crear primer archivo
        first = FileUtils.generate_unique_filename(
            "test", ".txt", tmp_path, include_timestamp=False
        )
        first.write_text("")
        
        # Segundo debería tener sufijo
        second = FileUtils.generate_unique_filename(
            "test", ".txt", tmp_path, include_timestamp=False
        )
        
        assert first != second
        assert "_1" in second.stem
    
    def test_safe_copy(self, tmp_path):
        """Test copia segura de archivo."""
        source = tmp_path / "source.txt"
        source.write_text("content")
        dest_dir = tmp_path / "dest"
        
        result = FileUtils.safe_copy(source, dest_dir)
        
        assert result.exists()
        assert result.read_text() == "content"
    
    def test_safe_delete(self, tmp_path):
        """Test eliminación segura."""
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("")
        
        result = FileUtils.safe_delete(test_file)
        
        assert result == True
        assert not test_file.exists()
    
    def test_safe_delete_missing_ok(self):
        """Test eliminación de archivo no existente con missing_ok."""
        result = FileUtils.safe_delete("/nonexistent/file.txt", missing_ok=True)
        assert result == False
    
    def test_list_files(self, tmp_path):
        """Test listado de archivos."""
        # Crear archivos de prueba
        (tmp_path / "file1.xlsx").write_text("")
        (tmp_path / "file2.xlsx").write_text("")
        (tmp_path / "file3.csv").write_text("")
        
        xlsx_files = FileUtils.list_files(tmp_path, "*.xlsx")
        
        assert len(xlsx_files) == 2
    
    def test_read_write_text_file(self, tmp_path):
        """Test lectura y escritura de texto."""
        test_file = tmp_path / "test.txt"
        content = "Línea 1\nLínea 2\nCaracteres especiales: áéíóú ñ"
        
        FileUtils.write_text_file(test_file, content)
        read_content = FileUtils.read_text_file(test_file)
        
        assert read_content == content


class TestDataValidator:
    """Tests para DataValidator."""
    
    def test_is_not_empty(self):
        """Test validación de no vacío."""
        assert DataValidator.is_not_empty("text") == True
        assert DataValidator.is_not_empty(123) == True
        assert DataValidator.is_not_empty([1, 2]) == True
        
        assert DataValidator.is_not_empty(None) == False
        assert DataValidator.is_not_empty("") == False
        assert DataValidator.is_not_empty("   ") == False
        assert DataValidator.is_not_empty([]) == False
    
    def test_is_numeric(self):
        """Test validación numérica."""
        assert DataValidator.is_numeric(123) == True
        assert DataValidator.is_numeric(123.45) == True
        assert DataValidator.is_numeric("123") == True
        assert DataValidator.is_numeric("123.45") == True
        assert DataValidator.is_numeric("123,45") == True
        
        assert DataValidator.is_numeric("abc") == False
        assert DataValidator.is_numeric("12.34.56") == False
    
    def test_is_positive(self):
        """Test validación de positivo."""
        assert DataValidator.is_positive(100) == True
        assert DataValidator.is_positive(0.01) == True
        assert DataValidator.is_positive("50") == True
        
        assert DataValidator.is_positive(0) == False
        assert DataValidator.is_positive(-10) == False
        assert DataValidator.is_positive("abc") == False
    
    def test_is_valid_date(self):
        """Test validación de fecha."""
        assert DataValidator.is_valid_date("01/12/2024") == True
        assert DataValidator.is_valid_date("2024-12-01") == True
        assert DataValidator.is_valid_date("01-12-2024") == True
        
        assert DataValidator.is_valid_date("32/13/2024") == False
        assert DataValidator.is_valid_date("not a date") == False
    
    def test_parse_date(self):
        """Test parseo de fecha."""
        result = DataValidator.parse_date("15/06/2024")
        
        assert result is not None
        assert result.day == 15
        assert result.month == 6
        assert result.year == 2024
    
    def test_parse_number(self):
        """Test parseo de número."""
        # Formato español (coma decimal)
        assert DataValidator.parse_number("1.234,56") == 1234.56
        assert DataValidator.parse_number("100,50") == 100.50
        
        # Con símbolos de moneda
        assert DataValidator.parse_number("€ 100,00") == 100.00
        assert DataValidator.parse_number("50%") == 50.0
    
    def test_matches_pattern(self):
        """Test coincidencia de patrones."""
        assert DataValidator.matches_pattern(
            "test@email.com", "email"
        ) == True
        assert DataValidator.matches_pattern(
            "invalid-email", "email"
        ) == False
        
        assert DataValidator.matches_pattern(
            "ES1234567890123456789012", "iban"
        ) == True
    
    def test_validate_required_columns(self):
        """Test validación de columnas requeridas."""
        columns = ["fecha", "concepto", "importe", "saldo"]
        required = ["fecha", "importe", "categoria"]
        
        missing = DataValidator.validate_required_columns(columns, required)
        
        assert "categoria" in missing
        assert "fecha" not in missing
        assert "importe" not in missing
    
    def test_clean_string(self):
        """Test limpieza de string."""
        assert DataValidator.clean_string("  text  ") == "text"
        assert DataValidator.clean_string(None) == ""
        assert DataValidator.clean_string(123) == "123"
    
    def test_normalize_column_name(self):
        """Test normalización de nombre de columna."""
        assert DataValidator.normalize_column_name("  Fecha Valor  ") == "fecha_valor"
        # Aceptar resultado con o sin underscore trailing
        result = DataValidator.normalize_column_name("Importe (€)")
        assert result in ["importe", "importe_"]
        assert DataValidator.normalize_column_name("Descripción") == "descripcion"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
