from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"


@dataclass
class Colors:
    primary: str = "#2563eb"
    background: str = "#ffffff"
    text_primary: str = "#111827"
    error: str = "#dc2626"
    success: str = "#16a34a"


@dataclass
class DarkColors(Colors):
    background: str = "#0b1220"
    text_primary: str = "#f9fafb"


@dataclass
class Theme:
    name: str
    theme_type: ThemeType
    colors: Colors

    font_family: str = "Arial"
    font_size_small: int = 9
    font_size_normal: int = 10
    font_size_large: int = 12
    font_size_title: int = 14
    font_size_header: int = 16

    def get_font(self, size: str = "normal", weight: str = "normal") -> tuple[str, int, str]:
        size_map = {
            "small": self.font_size_small,
            "normal": self.font_size_normal,
            "large": self.font_size_large,
            "title": self.font_size_title,
            "header": self.font_size_header,
        }
        return (self.font_family, size_map.get(size, self.font_size_normal), weight)


class ThemeManager:
    _instance: "ThemeManager | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_singleton()
        return cls._instance

    def _init_singleton(self) -> None:
        self._listeners: list[Callable[[Theme], None]] = []
        self._light = Theme(name="Light", theme_type=ThemeType.LIGHT, colors=Colors())
        self._dark = Theme(name="Dark", theme_type=ThemeType.DARK, colors=DarkColors())
        self.current_theme: Theme = self._light

    @property
    def is_dark(self) -> bool:
        return self.current_theme.theme_type == ThemeType.DARK

    @property
    def colors(self) -> Colors:
        return self.current_theme.colors

    def add_listener(self, callback: Callable[[Theme], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Theme], None]) -> None:
        self._listeners = [c for c in self._listeners if c is not callback]

    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb(self.current_theme)

    def toggle_theme(self) -> None:
        self.current_theme = self._dark if not self.is_dark else self._light
        self._notify()

    def set_theme(self, theme_type: ThemeType) -> None:
        self.current_theme = self._dark if theme_type == ThemeType.DARK else self._light
        self._notify()

    def apply_to_root(self, root) -> None:
        # No-op seguro para tests (evita requerir display).
        _ = root
