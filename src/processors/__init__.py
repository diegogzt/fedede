"""Capa de compatibilidad para imports legacy en tests.

Los tests históricos importan desde `src.processors.*`, pero la implementación
vive en `backend/app/processors` (paquete `app`).

Este paquete re-exporta esos módulos para no romper tests/scripts existentes.
"""

from __future__ import annotations

# Re-export explícito (módulos)
from .models import *  # noqa: F401,F403
from .excel_reader import *  # noqa: F401,F403
from .data_normalizer import *  # noqa: F401,F403
from .financial_analyzer import *  # noqa: F401,F403
from .excel_exporter import *  # noqa: F401,F403
from .qa_generator import *  # noqa: F401,F403
