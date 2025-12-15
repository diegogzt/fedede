from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from string import Template
from typing import Any


class PromptType(str, Enum):
    QUESTION_GENERATION = "question_generation"
    ANALYSIS = "analysis"


@dataclass(slots=True)
class PromptTemplate:
    name: str
    prompt_type: PromptType
    system_prompt: str
    user_prompt: str

    def format(self, **kwargs: Any) -> dict[str, str]:
        system = Template(self.system_prompt).safe_substitute(**kwargs)
        user = Template(self.user_prompt).safe_substitute(**kwargs)
        return {"system": system, "user": user}


class PromptGenerator:
    def generate_question_prompt(
        self,
        *,
        description: str,
        account_code: str,
        period_base: str,
        period_compare: str,
        value_base: float,
        value_compare: float,
        variation_abs: float,
        variation_pct: float,
        variation_type: str,
        category: str,
    ) -> dict[str, str]:
        system = "Eres un asistente experto en due diligence financiera."
        user = (
            f"Descripción: {description}\n"
            f"Cuenta: {account_code}\n"
            f"Periodo base: {period_base} ({value_base})\n"
            f"Periodo comparación: {period_compare} ({value_compare})\n"
            f"Variación abs: {variation_abs}\n"
            f"Variación %: {variation_pct}\n"
            f"Tipo: {variation_type}\n"
            f"Categoría: {category}\n"
            "Genera una pregunta de due diligence."
        )
        return {"system": system, "user": user}

    def generate_analysis_prompt(
        self,
        *,
        description: str,
        account_type: str,
        period_base: str,
        period_compare: str,
        value_base: float,
        value_compare: float,
        variation_pct: float,
    ) -> dict[str, str]:
        system = "Eres un analista financiero."
        user = (
            f"Descripción: {description}\n"
            f"Tipo: {account_type}\n"
            f"Base: {period_base} ({value_base})\n"
            f"Comparación: {period_compare} ({value_compare})\n"
            f"Variación %: {variation_pct}\n"
            "Explica posibles drivers."
        )
        return {"system": system, "user": user}

    @staticmethod
    def get_rule_based_question(
        *,
        description: str,
        variation_type: str,
        variation_pct: float,
        period_base: str,
        period_compare: str,
    ) -> str:
        vt = (variation_type or "").lower()
        pct = abs(float(variation_pct))
        pct_txt = f"{pct:.1f}%"

        if "dismin" in vt or "decrease" in vt:
            return (
                f"¿A qué se debe la reducción del {pct_txt} en {description} "
                f"({period_base} vs {period_compare})?"
            )
        if "nuevo" in vt or "new" in vt:
            return f"¿Cuál es el motivo del nuevo concepto {description} en {period_compare}?"

        # Default: incremento
        return (
            f"¿A qué se debe el incremento del {pct_txt} en {description} "
            f"({period_base} vs {period_compare})?"
        )
