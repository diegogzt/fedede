from __future__ import annotations

from ._backend_imports import ensure_backend_on_path

ensure_backend_on_path()

from app.processors.qa_generator import *  # type: ignore  # noqa: F401,F403,E402
