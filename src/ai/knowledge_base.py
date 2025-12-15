from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ai.rag_engine import RAGEngine


@dataclass
class KnowledgeBase:
    def __init__(self) -> None:
        self.rag = RAGEngine(collection_name="knowledge")
        self._initialized = False

    def initialize_base_knowledge(self) -> None:
        if self._initialized:
            return
        # Conocimiento base mínimo.
        self.rag.add_document(content="Variaciones en inventario pueden indicar cambios de demanda.", category="inventory")
        self.rag.add_document(content="Incrementos de gastos de personal suelen venir de nuevas contrataciones.", category="expenses")
        self._initialized = True


_singleton: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    global _singleton
    if _singleton is None:
        _singleton = KnowledgeBase()
        _singleton.initialize_base_knowledge()
    return _singleton


def get_context_for_question(
    *,
    description: str,
    category: str,
    variation_type: str,
    variation_magnitude: str,
    **_: Any,
) -> list[str]:
    kb = get_knowledge_base()
    query = f"{category} {description} {variation_type} {variation_magnitude}"
    docs = kb.rag.retrieve(query, n_results=3)
    return [d.content for d in docs]
