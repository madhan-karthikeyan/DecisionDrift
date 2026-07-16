from __future__ import annotations

import sys
from typing import Any

import numpy as np

from decisiondrift.models.schema import DecisionRecord
from decisiondrift.retrieval.backend import RetrievalBackend
from decisiondrift.retrieval.models import RetrievalResult

try:
    from fastembed import TextEmbedding

    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class EmbeddingBackend(RetrievalBackend):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", cache_dir: str | None = None):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model: Any = None
        self._adr_embeddings: dict[str, np.ndarray] = {}

    def _get_model(self):
        if self._model is None:
            if not HAS_FASTEMBED:
                print(
                    "Warning: fastembed not installed. Run `pip install decisiondrift[embeddings]`",
                    file=sys.stderr,
                )
                return None
            try:
                kwargs: dict[str, Any] = {}
                if self.cache_dir:
                    kwargs["cache_dir"] = self.cache_dir
                self._model = TextEmbedding(model_name=self.model_name, **kwargs)
            except Exception as e:
                print(f"Warning: could not load embedding model {self.model_name}: {e}", file=sys.stderr)
                return None
        return self._model

    def _adr_text(self, decision: DecisionRecord) -> str:
        parts = [decision.title or "", decision.rationale or ""]
        if decision.keywords:
            parts.extend(decision.keywords)
        return " ".join(parts)

    def _embed(self, texts: list[str]) -> list[np.ndarray]:
        model = self._get_model()
        if model is None:
            return [np.array([]) for _ in texts]
        try:
            return list(model.embed(texts))
        except Exception:
            return [np.array([]) for _ in texts]

    def _ensure_adr_embeddings(self, decisions: list[DecisionRecord]) -> None:
        pending: list[DecisionRecord] = []
        for d in decisions:
            if d.id not in self._adr_embeddings:
                pending.append(d)
        if not pending:
            return
        texts = [self._adr_text(d) for d in pending]
        embeddings = self._embed(texts)
        for d, emb in zip(pending, embeddings):
            if emb.size > 0:
                self._adr_embeddings[d.id] = emb

    def query(
        self,
        search_terms: list[str],
        decisions: list[DecisionRecord],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not search_terms or not decisions:
            return []
        if not self._get_model():
            return []

        self._ensure_adr_embeddings(decisions)
        query_text = " ".join(search_terms)
        query_emb = self._embed([query_text])[0]
        if query_emb.size == 0:
            return []

        scored: list[tuple[float, str]] = []
        for d in decisions:
            adr_emb = self._adr_embeddings.get(d.id)
            if adr_emb is None or adr_emb.size == 0:
                continue
            sim = _cosine_similarity(query_emb, adr_emb)
            if sim > 0:
                scored.append((sim, d.id))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RetrievalResult(adr_id=adr_id, score=round(score, 4), matched_terms=[])
            for score, adr_id in scored[:top_k]
        ]
