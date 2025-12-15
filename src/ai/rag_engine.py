from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RetrievedDocument:
    content: str
    category: str | None = None
    source: str | None = None
    metadata: dict[str, Any] | None = None
    score: float | None = None


@dataclass(slots=True)
class AugmentResult:
    augmented_prompt: str
    contexts: list[RetrievedDocument]


class RAGEngine:
    def __init__(self, *, collection_name: str = "default", db_path: Path | None = None) -> None:
        self.collection_name = collection_name
        self.db_path = db_path
        self._docs: list[RetrievedDocument] = []

    def add_document(
        self,
        *,
        content: str,
        category: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._docs.append(RetrievedDocument(content=content, category=category, source=source, metadata=metadata))

    def retrieve(self, query: str, *, n_results: int = 3) -> list[RetrievedDocument]:
        if not self._docs:
            return []
        q = (query or "").lower().split()
        if not q:
            return self._docs[:n_results]

        def score(doc: RetrievedDocument) -> float:
            tokens = (doc.content or "").lower().split()
            overlap = len(set(q).intersection(tokens))
            return float(overlap)

        ranked = sorted(self._docs, key=score, reverse=True)
        return ranked[:n_results]

    def augment_prompt(self, prompt: str, *, n_contexts: int = 3) -> AugmentResult:
        contexts = self.retrieve(prompt, n_results=n_contexts)
        if not contexts:
            return AugmentResult(augmented_prompt=prompt, contexts=[])

        context_text = "\n\n".join([f"- {c.content}" for c in contexts])
        augmented = f"{prompt}\n\nContexto:\n{context_text}"
        return AugmentResult(augmented_prompt=augmented, contexts=contexts)

    def learn_from_qa(
        self,
        *,
        question: str,
        answer: str,
        category: str | None = None,
        variation_info: dict[str, Any] | None = None,
    ) -> None:
        content = f"Q: {question}\nA: {answer}"
        metadata = {"variation_info": variation_info or {}}
        self.add_document(content=content, category=category, source="learned", metadata=metadata)

    def get_stats(self) -> dict[str, int]:
        return {"total_documents": len(self._docs)}
