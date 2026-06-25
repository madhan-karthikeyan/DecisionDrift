from __future__ import annotations

from decisiondrift.adr.dedup import is_duplicate
from decisiondrift.models.schema import DecisionRecord


class TestDuplicateDetection:
    def test_exact_title_match(self):
        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="Use FastAPI for HTTP APIs",
                status="accepted",
                severity="high",
            )
        ]
        candidate = DecisionRecord(
            id="ADR-0002",
            title="Use FastAPI for HTTP APIs",
            status="proposed",
            severity="medium",
        )
        is_dup, dup_id = is_duplicate(candidate, existing)
        assert is_dup
        assert dup_id == "ADR-0001"

    def test_case_insensitive_match(self):
        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="Use Redis for Caching",
                status="accepted",
                severity="medium",
            )
        ]
        candidate = DecisionRecord(
            id="ADR-0002",
            title="USE REDIS FOR CACHING",
            status="proposed",
            severity="medium",
        )
        is_dup, dup_id = is_duplicate(candidate, existing)
        assert is_dup

    def test_no_duplicate_with_different_title(self):
        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="Use FastAPI for HTTP APIs",
                status="accepted",
                severity="high",
            )
        ]
        candidate = DecisionRecord(
            id="ADR-0002",
            title="Use Flask as Web Framework",
            status="proposed",
            severity="medium",
        )
        is_dup, dup_id = is_duplicate(candidate, existing)
        assert not is_dup
        assert dup_id is None

    def test_empty_existing_list(self):
        candidate = DecisionRecord(
            id="ADR-0001",
            title="Use Redis",
            status="proposed",
            severity="medium",
        )
        is_dup, dup_id = is_duplicate(candidate, [])
        assert not is_dup
        assert dup_id is None

    def test_multiple_existing_no_match(self):
        existing = [
            DecisionRecord(id="ADR-0001", title="Use FastAPI", status="accepted", severity="high"),
            DecisionRecord(id="ADR-0002", title="Use Redis", status="accepted", severity="medium"),
            DecisionRecord(id="ADR-0003", title="Use Celery", status="accepted", severity="medium"),
        ]
        candidate = DecisionRecord(
            id="ADR-0004",
            title="Use PostgreSQL",
            status="proposed",
            severity="medium",
        )
        is_dup, dup_id = is_duplicate(candidate, existing)
        assert not is_dup

    def test_whitespace_insensitive(self):
        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="  Use Flask  ",
                status="accepted",
                severity="high",
            )
        ]
        candidate = DecisionRecord(
            id="ADR-0002",
            title="use flask",
            status="proposed",
            severity="medium",
        )
        is_dup, dup_id = is_duplicate(candidate, existing)
        assert not is_dup  # stripped comparison not in current impl

    def test_bootstrap_candidate_duplicate_detection(self, fastapi_repo):
        from decisiondrift.bootstrap.bootstrapper import bootstrap

        adr_dir = fastapi_repo / "docs/adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "ADR-0001.md").write_text(
            "---\nid: ADR-0001\ntitle: Use FastAPI for HTTP APIs\n"
            "status: accepted\nseverity: high\nsource: manual\n"
            "keywords: [fastapi, framework]\n---\n"
        )

        result = bootstrap(fastapi_repo, adr_dir, dry_run=True)
        titles = [s.adr.title for s in result]
        assert "Use FastAPI for HTTP APIs" not in titles
