from __future__ import annotations

from dataclasses import dataclass


try:
    import httpx  # noqa: F401

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

try:
    import requests  # noqa: F401

    REQUESTS_AVAILABLE = True
except Exception:  # pragma: no cover
    REQUESTS_AVAILABLE = False


@dataclass(slots=True)
class OllamaResponse:
    text: str
    model: str
    done: bool
    total_duration: int | None = None  # nanosegundos
    eval_count: int | None = None

    @property
    def tokens_generated(self) -> int | None:
        return self.eval_count

    @property
    def generation_time_seconds(self) -> float:
        if not self.total_duration:
            return 0.0
        return float(self.total_duration) / 1_000_000_000.0


class OllamaClient:
    def __init__(
        self,
        host: str = "http://localhost",
        port: int = 11434,
        model: str = "llama3.2",
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        self.host = host.rstrip("/")
        self.port = port
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def base_url(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api/generate"

    @property
    def models_url(self) -> str:
        return f"{self.base_url}/api/tags"

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/api/chat"

    def is_available(self) -> bool:
        # En este repo no instalamos clientes HTTP por defecto.
        if not HTTPX_AVAILABLE and not REQUESTS_AVAILABLE:
            return False
        # No intentamos hacer llamada de red en tests.
        return False
