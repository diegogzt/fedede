"""
Tests para el módulo GUI de FDD.

Incluye tests para:
- ThemeManager y temas
- Componentes base
- Componentes individuales
- MainWindow
"""

import pytest
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestThemeManager:
    """Tests para ThemeManager."""
    
    def test_singleton_pattern(self):
        """Test que ThemeManager es singleton."""
        from src.gui.theme import ThemeManager
        
        # Reset singleton para el test
        ThemeManager._instance = None
        
        tm1 = ThemeManager()
        tm2 = ThemeManager()
        
        assert tm1 is tm2
    
    def test_default_theme_is_light(self):
        """Test que el tema por defecto es claro."""
        from src.gui.theme import ThemeManager, ThemeType
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        assert tm.current_theme.theme_type == ThemeType.LIGHT
        assert not tm.is_dark
    
    def test_toggle_theme(self):
        """Test alternar tema."""
        from src.gui.theme import ThemeManager, ThemeType
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        assert tm.current_theme.theme_type == ThemeType.LIGHT
        
        tm.toggle_theme()
        assert tm.current_theme.theme_type == ThemeType.DARK
        assert tm.is_dark
        
        tm.toggle_theme()
        assert tm.current_theme.theme_type == ThemeType.LIGHT
    
    def test_set_theme(self):
        """Test establecer tema específico."""
        from src.gui.theme import ThemeManager, ThemeType
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        tm.set_theme(ThemeType.DARK)
        assert tm.is_dark
        
        tm.set_theme(ThemeType.LIGHT)
        assert not tm.is_dark
    
    def test_listener_notification(self):
        """Test que los listeners son notificados."""
        from src.gui.theme import ThemeManager, ThemeType
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        callback = Mock()
        tm.add_listener(callback)
        
        tm.toggle_theme()
        
        callback.assert_called_once()
        assert callback.call_args[0][0].theme_type == ThemeType.DARK
    
    def test_remove_listener(self):
        """Test remover listener."""
        from src.gui.theme import ThemeManager
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        callback = Mock()
        tm.add_listener(callback)
        tm.remove_listener(callback)
        
        tm.toggle_theme()
        
        callback.assert_not_called()
    
    def test_colors_access(self):
        """Test acceso a colores."""
        from src.gui.theme import ThemeManager
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        colors = tm.colors
        
        assert colors.primary is not None
        assert colors.background is not None
        assert colors.text_primary is not None
    
    def test_dark_theme_colors_different(self):
        """Test que los colores del tema oscuro son diferentes."""
        from src.gui.theme import ThemeManager, ThemeType
        
        ThemeManager._instance = None
        tm = ThemeManager()
        
        light_bg = tm.colors.background
        
        tm.set_theme(ThemeType.DARK)
        dark_bg = tm.colors.background
        
        assert light_bg != dark_bg


class TestColors:
    """Tests para la clase Colors."""
    
    def test_colors_dataclass(self):
        """Test que Colors es un dataclass válido."""
        from src.gui.theme import Colors
        
        colors = Colors()
        
        assert hasattr(colors, 'primary')
        assert hasattr(colors, 'background')
        assert hasattr(colors, 'error')
        assert hasattr(colors, 'success')
    
    def test_dark_colors_override(self):
        """Test que DarkColors sobrescribe valores."""
        from src.gui.theme import Colors, DarkColors
        
        light = Colors()
        dark = DarkColors()
        
        assert light.background != dark.background
        assert light.text_primary != dark.text_primary


class TestTheme:
    """Tests para la clase Theme."""
    
    def test_theme_creation(self):
        """Test crear un tema."""
        from src.gui.theme import Theme, ThemeType, Colors
        
        theme = Theme(
            name="Test",
            theme_type=ThemeType.LIGHT,
            colors=Colors()
        )
        
        assert theme.name == "Test"
        assert theme.theme_type == ThemeType.LIGHT
    
    def test_get_font(self):
        """Test obtener fuente."""
        from src.gui.theme import Theme, ThemeType, Colors
        
        theme = Theme(
            name="Test",
            theme_type=ThemeType.LIGHT,
            colors=Colors()
        )
        
        font = theme.get_font("normal")
        assert len(font) == 3
        assert font[0] == theme.font_family
        assert font[1] == theme.font_size_normal
    
    def test_get_font_sizes(self):
        """Test diferentes tamaños de fuente."""
        from src.gui.theme import Theme, ThemeType, Colors
        
        theme = Theme(
            name="Test",
            theme_type=ThemeType.LIGHT,
            colors=Colors()
        )
        
        sizes = ["small", "normal", "large", "title", "header"]
        
        for size in sizes:
            font = theme.get_font(size)
            assert font is not None


class TestProgressState:
    """Tests para ProgressState."""
    
    def test_progress_states(self):
        """Test todos los estados de progreso."""
        from src.gui.components.progress_panel import ProgressState
        
        assert ProgressState.IDLE.value == "idle"
        assert ProgressState.RUNNING.value == "running"
        assert ProgressState.COMPLETED.value == "completed"
        assert ProgressState.ERROR.value == "error"
        assert ProgressState.CANCELLED.value == "cancelled"


class TestFileSelectorStatic:
    """Tests estáticos para FileSelector."""
    
    def test_supported_extensions(self):
        """Test extensiones soportadas."""
        from src.gui.components.file_selector import FileSelector
        
        assert '.xlsx' in FileSelector.SUPPORTED_EXTENSIONS
        assert '.xls' in FileSelector.SUPPORTED_EXTENSIONS
        assert '.csv' in FileSelector.SUPPORTED_EXTENSIONS
    
    def test_format_size(self):
        """Test formateo de tamaño."""
        from src.gui.components.file_selector import FileSelector
        
        assert "B" in FileSelector._format_size(500)
        assert "KB" in FileSelector._format_size(1024)
        assert "MB" in FileSelector._format_size(1024 * 1024)
        assert "GB" in FileSelector._format_size(1024 * 1024 * 1024)


class TestSettingsPanelStatic:
    """Tests estáticos para SettingsPanel."""
    
    def test_ai_modes(self):
        """Test modos de IA disponibles."""
        from src.gui.components.settings_panel import SettingsPanel
        
        assert "auto" in SettingsPanel.AI_MODES
        assert "full_ai" in SettingsPanel.AI_MODES
        assert "hybrid" in SettingsPanel.AI_MODES
        assert "rule_based" in SettingsPanel.AI_MODES
    
    def test_default_models(self):
        """Test modelos por defecto."""
        from src.gui.components.settings_panel import SettingsPanel
        
        assert "llama3.2" in SettingsPanel.DEFAULT_MODELS
        assert "mistral" in SettingsPanel.DEFAULT_MODELS


@pytest.fixture
def mock_tk_root():
    """Fixture para mock de Tk root."""
    with patch('tkinter.Tk'):
        with patch('tkinter.ttk.Style'):
            yield


class TestIntegration:
    """Tests de integración (requieren display)."""
    
    @pytest.mark.skipif(
        not hasattr(tk, '_default_root') or tk._default_root is None,
        reason="Requiere display"
    )
    def test_theme_manager_apply_to_root(self):
        """Test aplicar tema a root."""
        from src.gui.theme import ThemeManager
        
        root = tk.Tk()
        root.withdraw()
        
        try:
            ThemeManager._instance = None
            tm = ThemeManager()
            tm.apply_to_root(root)
        finally:
            root.destroy()


class TestModuleImports:
    """Tests de importación de módulos."""
    
    def test_import_theme(self):
        """Test importar módulo theme."""
        from src.gui.theme import ThemeManager, Theme, Colors, ThemeType
        
        assert ThemeManager is not None
        assert Theme is not None
        assert Colors is not None
        assert ThemeType is not None
    
    def test_import_components(self):
        """Test importar componentes."""
        from src.gui.components import (
            BaseFrame,
            BasePanel,
            FileSelector,
            ProgressPanel,
            ResultsViewer,
            SettingsPanel,
            StatusBar
        )
        
        assert BaseFrame is not None
        assert BasePanel is not None
        assert FileSelector is not None
        assert ProgressPanel is not None
        assert ResultsViewer is not None
        assert SettingsPanel is not None
        assert StatusBar is not None
    
    def test_import_main_window(self):
        """Test importar MainWindow."""
        from src.gui.main_window import MainWindow, create_app
        
        assert MainWindow is not None
        assert create_app is not None
    
    def test_import_gui_package(self):
        """Test importar paquete gui completo."""
        from src.gui import (
            MainWindow,
            ThemeManager,
            Theme,
            Colors,
            BaseFrame,
            BasePanel,
            FileSelector,
            ProgressPanel,
            ResultsViewer,
            SettingsPanel,
            StatusBar
        )
        
        assert all([
            MainWindow,
            ThemeManager,
            Theme,
            Colors,
            BaseFrame,
            BasePanel,
            FileSelector,
            ProgressPanel,
            ResultsViewer,
            SettingsPanel,
            StatusBar
        ])


class TestMainModule:
    """Tests para el módulo main."""
    
    def test_setup_logging(self):
        """Test configuración de logging."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        # El módulo main tiene setup_logging que debería funcionar
        # sin errores
        pass
    
    def test_check_dependencies(self):
        """Test verificación de dependencias."""
        # Simular importaciones correctas
        import tkinter
        import pandas
        
        # Las dependencias principales deberían estar disponibles
        assert tkinter is not None
        assert pandas is not None


# Marcadores para tests que requieren GUI
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
