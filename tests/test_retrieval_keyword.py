from __future__ import annotations

from decisiondrift.models.schema import DecisionRecord
from decisiondrift.retrieval.keyword import KeywordBackend


class TestKeywordBackend:
    def _make_adr(
        self,
        id: str,
        title: str,
        rationale: str = "",
        keywords: list[str] | None = None,
        evidence: list[str] | None = None,
        exceptions: str = "",
    ) -> DecisionRecord:
        return DecisionRecord(
            id=id,
            title=title,
            rationale=rationale,
            status="accepted",
            severity="high",
            source="manual",
            keywords=keywords or [],
            evidence=evidence or [],
            exceptions=exceptions or None,
        )

    def test_empty_search_terms(self):
        backend = KeywordBackend()
        result = backend.query([], [self._make_adr("ADR-001", "Test")])
        assert result == []

    def test_empty_decisions(self):
        backend = KeywordBackend()
        result = backend.query(["test"], [])
        assert result == []

    def test_title_match_scored_highest(self):
        backend = KeywordBackend()
        adr_a = self._make_adr("ADR-001", "Use JWT for Authentication", "tokens and login")
        adr_b = self._make_adr("ADR-002", "Use SQLAlchemy ORM", "jwt is not mentioned here")
        result = backend.query(["jwt"], [adr_a, adr_b], top_k=5)
        assert len(result) >= 2
        assert result[0].adr_id == "ADR-001"
        assert "jwt" in result[0].matched_terms

    def test_keyword_match(self):
        backend = KeywordBackend()
        adr = self._make_adr("ADR-001", "Redis Cache", keywords=["redis", "cache", "ttl"])
        result = backend.query(["redis", "cache"], [adr])
        assert len(result) == 1
        assert result[0].score > 0
        assert "redis" in result[0].matched_terms
        assert "cache" in result[0].matched_terms

    def test_evidence_path_match(self):
        backend = KeywordBackend()
        adr = self._make_adr("ADR-001", "Notifications", evidence=["backend/utils/notifications.py"])
        result = backend.query(["notifications.py"], [adr])
        assert len(result) == 1
        assert result[0].score > 0
        assert "notifications.py" in result[0].matched_terms

    def test_rationale_match(self):
        backend = KeywordBackend()
        adr = self._make_adr("ADR-001", "JWT Auth", rationale="All endpoints use JSON Web Tokens")
        result = backend.query(["tokens"], [adr])
        assert len(result) == 1
        assert result[0].score > 0

    def test_exceptions_penalty(self):
        backend = KeywordBackend()
        adr = self._make_adr("ADR-001", "JWT Auth", exceptions="Public endpoints may skip JWT")
        result = backend.query(["public"], [adr])
        assert len(result) == 0

    def test_top_k_limits_results(self):
        backend = KeywordBackend()
        adrs = [self._make_adr(f"ADR-{i:03d}", "Use Flask for web") for i in range(10)]
        result = backend.query(["flask", "web"], adrs, top_k=3)
        assert len(result) <= 3

    def test_multiple_match_sources_combined(self):
        backend = KeywordBackend()
        adr = self._make_adr(
            "ADR-001",
            "Use Celery for Async Tasks",
            rationale="All background work uses Celery workers",
            keywords=["celery", "async", "task", "worker"],
            evidence=["backend/tasks/email_tasks.py"],
        )
        result = backend.query(["celery", "worker", "email_tasks"], [adr])
        assert len(result) == 1
        assert result[0].score > 0
        assert len(result[0].matched_terms) >= 2

    def test_case_insensitive_matching(self):
        backend = KeywordBackend()
        adr = self._make_adr("ADR-001", "JWT Authentication")
        result = backend.query(["jwt"], [adr])
        result2 = backend.query(["JWT"], [adr])
        assert result[0].score == result2[0].score
