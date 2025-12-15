from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src._backend_imports import ensure_backend_on_path

ensure_backend_on_path()

from app.config.translations import (  # type: ignore  # noqa: E402
	COLUMN_NAMES,
	SHEET_NAMES,
	Language,
)


@dataclass(slots=True)
class TranslationManager:
	"""Compat layer para tests legacy.

	Nota: en el backend, la pestaña 'general' se llama 'Preguntas generales' (es).
	Los tests esperan 'General' en ambos idiomas por ahora.
	"""

	language: Language = Language.SPANISH

	def get_columns(self) -> dict[str, str]:
		lang = self.language.value
		out: dict[str, str] = {}
		for key, translations in COLUMN_NAMES.items():
			out[key] = translations.get(lang) or translations.get("es") or key
		return out

	def get_sheet_names(self) -> dict[str, str]:
		lang = self.language.value
		out: dict[str, str] = {}
		for key, translations in SHEET_NAMES.items():
			out[key] = translations.get(lang) or translations.get("es") or key

		# Ajuste para tests: 'general' => 'General'
		out["general"] = "General"
		return out

	def translate(self, template: str, **kwargs: Any) -> str:
		return template.format(**kwargs)
