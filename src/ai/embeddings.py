from __future__ import annotations

import hashlib
from dataclasses import dataclass


_DIM = 384


def _hash_to_vector(text: str) -> list[float]:
    # Vector determinista de dimensión 384 basado en SHA256.
    # No pretende ser semántico; solo cubre los tests sin dependencias.
    h = hashlib.sha256((text or "").encode("utf-8")).digest()
    out: list[float] = []
    # Expandimos el hash repitiéndolo para llegar a _DIM.
    i = 0
    while len(out) < _DIM:
        b = h[i % len(h)]
        out.append((b / 255.0) * 2.0 - 1.0)  # [-1, 1]
        i += 1
    return out


@dataclass
class EmbeddingService:
    def encode_single(self, text: str) -> list[float]:
        return _hash_to_vector(text)

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self.encode_single(t) for t in texts]


_singleton: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _singleton
    if _singleton is None:
        _singleton = EmbeddingService()
    return _singleton
