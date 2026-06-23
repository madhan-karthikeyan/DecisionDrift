from __future__ import annotations

from pydantic import BaseModel


class RetrievalResult(BaseModel):
    adr_id: str
    score: float
    matched_terms: list[str]
