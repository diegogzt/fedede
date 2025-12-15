from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Any

from src.ai.ollama_client import OllamaClient
from src.ai.prompts import PromptGenerator


class AIMode(str, Enum):
    RULE_BASED = "rules"
    FULL_AI = "full_ai"
    AUTO = "auto"


@dataclass(slots=True)
class QuestionResult:
    question: str
    generated_by: str
    confidence: float = 0.7
    model_used: str | None = None
    processing_time: float | None = None


class AIService:
    def __init__(
        self,
        *,
        mode: AIMode = AIMode.AUTO,
        settings: Any | None = None,
        enable_rag: bool = False,
        sector: str | None = None,
    ) -> None:
        self.settings = settings
        self._requested_mode = mode
        self.enable_rag = enable_rag
        self.sector = sector

        # Si la IA está deshabilitada en settings, forzamos reglas.
        if settings is not None and getattr(getattr(settings, "ai", None), "enabled", True) is False:
            self.mode = AIMode.RULE_BASED
        else:
            self.mode = mode

        self.prompt_generator = PromptGenerator()

        ai_cfg = getattr(settings, "ai", None)
        host = getattr(ai_cfg, "host", "http://localhost") if ai_cfg else "http://localhost"
        port = getattr(ai_cfg, "port", 11434) if ai_cfg else 11434
        model = getattr(ai_cfg, "default_model", "llama3.2") if ai_cfg else "llama3.2"
        timeout = getattr(ai_cfg, "request_timeout", 120) if ai_cfg else 120
        max_retries = getattr(ai_cfg, "max_retries", 3) if ai_cfg else 3

        self.client = OllamaClient(host=host, port=port, model=model, timeout=timeout, max_retries=max_retries)

    @property
    def is_ai_enabled(self) -> bool:
        return self.mode in (AIMode.FULL_AI, AIMode.AUTO) and self.client.is_available()

    def get_status(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "ai_enabled": self.is_ai_enabled,
            "provider": getattr(getattr(self.settings, "ai", None), "provider", None),
            "rag_enabled": bool(self.enable_rag),
        }

    def generate_question(
        self,
        *,
        description: str,
        account_code: str,
        period_base: str,
        period_compare: str,
        value_base: float,
        value_compare: float,
        variation_pct: float,
        variation_type: str | None = None,
        force_rules: bool = False,
        use_rag: bool = False,
        **_: Any,
    ) -> QuestionResult:
        start = perf_counter()

        # Por defecto, en este repo generamos por reglas (sin dependencias externas).
        use_rules = force_rules or self.mode == AIMode.RULE_BASED or not self.client.is_available()

        question = PromptGenerator.get_rule_based_question(
            description=description,
            variation_type=variation_type or "aumento_significativo",
            variation_pct=variation_pct,
            period_base=period_base,
            period_compare=period_compare,
        )

        generated_by = "rules" if use_rules else "ai"
        if use_rag and self.enable_rag:
            generated_by = f"{generated_by}_rag"
        elapsed = perf_counter() - start
        return QuestionResult(
            question=question,
            generated_by=generated_by,
            confidence=0.7,
            model_used=None if generated_by != "ai" else self.client.model,
            processing_time=elapsed,
        )

    def generate_batch_questions(self, variations: list[dict[str, Any]]) -> list[QuestionResult]:
        results: list[QuestionResult] = []
        for v in variations:
            results.append(
                self.generate_question(
                    description=v.get("description", ""),
                    account_code=v.get("account_code", ""),
                    period_base=v.get("period_base", ""),
                    period_compare=v.get("period_compare", ""),
                    value_base=v.get("value_base", 0),
                    value_compare=v.get("value_compare", 0),
                    variation_pct=v.get("variation_pct", 0),
                    variation_type=v.get("variation_type"),
                )
            )
        return results
