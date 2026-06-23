from __future__ import annotations

from decisiondrift.models.schema import DecisionRecord
from decisiondrift.retrieval.backend import RetrievalBackend
from decisiondrift.retrieval.models import RetrievalResult


class KeywordBackend(RetrievalBackend):
    def query(
        self,
        search_terms: list[str],
        decisions: list[DecisionRecord],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not search_terms or not decisions:
            return []

        scored: list[tuple[float, str, list[str]]] = []

        for decision in decisions:
            score, matched = self._score_decision(search_terms, decision)
            if score > 0:
                scored.append((score, decision.id, matched))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievalResult(adr_id=adr_id, score=round(score, 4), matched_terms=matched)
            for score, adr_id, matched in scored[:top_k]
        ]

    def _score_decision(
        self,
        search_terms: list[str],
        decision: DecisionRecord,
    ) -> tuple[float, list[str]]:
        total_score = 0.0
        all_matched: set[str] = set()
        lower_terms = [t.lower() for t in search_terms]

        title_lower = decision.title.lower()
        rationale_lower = decision.rationale.lower()
        exceptions_lower = (decision.exceptions or "").lower()
        keyword_lower = [k.lower() for k in decision.keywords]
        evidence_lower = [e.lower() for e in decision.evidence]

        for i, term in enumerate(lower_terms):
            term_score = 0.0
            term_matched: list[str] = []

            # Title match = 3x
            if term in title_lower:
                term_score += 3.0
                term_matched.append("title")

            # Keyword match = 3x
            if any(term in kw for kw in keyword_lower):
                term_score += 3.0
                term_matched.append("keywords")

            # Evidence path match = 2x
            if any(term in ev for ev in evidence_lower):
                term_score += 2.0
                term_matched.append("evidence")

            # Rationale match = 1x
            if term in rationale_lower:
                term_score += 1.0
                term_matched.append("rationale")

            # Exceptions penalty = -1x
            if term in exceptions_lower:
                term_score -= 1.0

            if term_score > 0:
                total_score += term_score
                all_matched.add(search_terms[i])

        if total_score == 0:
            return 0.0, []

        normalized = total_score / len(search_terms)
        return normalized, sorted(all_matched)
