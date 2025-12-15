from __future__ import annotations

import sys
from pathlib import Path


def ensure_backend_on_path() -> None:
    """Asegura que `backend/` esté en `sys.path` para poder importar `app.*`.

    Mantiene compatibilidad con imports legacy tipo `src.*` usados en tests.
    """
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    if backend_dir.exists() and str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
