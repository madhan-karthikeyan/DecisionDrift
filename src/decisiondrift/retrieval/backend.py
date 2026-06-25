from __future__ import annotations

from abc import ABC, abstractmethod

from decisiondrift.models.schema import DecisionRecord
from decisiondrift.retrieval.models import RetrievalResult


class RetrievalBackend(ABC):
    @abstractmethod
    def query(
        self,
        search_terms: list[str],
        decisions: list[DecisionRecord],
        top_k: int = 5,
    ) -> list[RetrievalResult]: ...
