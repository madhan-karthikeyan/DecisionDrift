from __future__ import annotations

import tempfile
from pathlib import Path

from decisiondrift.bootstrap.candidate_generator import (
    _is_duplicate,
    _jaccard_words,
    _keyword_overlap,
    apply_candidates,
    generate_candidates,
)
from decisiondrift.bootstrap.patterns import match_patterns
from decisiondrift.bootstrap.structure_scan import scan_repo

HMS_V2 = Path(__file__).parent.parent / "repos" / "hospital-management-system-V2"
HMS_ADR = HMS_V2 / "docs" / "adr"


class TestDedup:
    def test_jaccard_identical(self):
        assert _jaccard_words("Use Flask", "Use Flask") == 1.0

    def test_jaccard_no_overlap(self):
        assert _jaccard_words("aaaa bbbb", "cccc dddd") == 0.0

    def test_jaccard_partial(self):
        score = _jaccard_words("Use Flask as Web Framework", "Use Flask Blueprints for Routes")
        assert 0.0 < score < 1.0

    def test_jaccard_empty(self):
        assert _jaccard_words("", "") == 0.0
        assert _jaccard_words("hello", "") == 0.0
        assert _jaccard_words("", "hello") == 0.0

    def test_keyword_overlap_exact_title_match(self):
        score = _keyword_overlap(
            "Use Flask as Web Framework",
            ["flask", "web"],
            "Use Flask as Web Framework",
            ["flask", "web"],
        )
        assert score >= 0.5

    def test_keyword_overlap_unrelated(self):
        score = _keyword_overlap(
            "Use Celery for Async Tasks",
            ["celery", "async"],
            "Use Flask as Web Framework",
            ["flask", "web"],
        )
        assert score < 0.3

    def test_is_duplicate_finds_exact(self):
        from decisiondrift.models.schema import DecisionRecord

        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="Use Flask as Web Framework",
                status="accepted",
                severity="high",
                keywords=["flask", "web"],
            )
        ]
        is_dup, dup_id = _is_duplicate(
            "Use Flask as Web Framework",
            ["flask"],
            existing,
        )
        assert is_dup
        assert dup_id == "ADR-0001"

    def test_is_duplicate_skips_novel(self):
        from decisiondrift.models.schema import DecisionRecord

        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="Use Flask as Web Framework",
                status="accepted",
                severity="high",
                keywords=["flask", "web"],
            )
        ]
        is_dup, dup_id = _is_duplicate(
            "Use Redis for Caching",
            ["redis", "cache"],
            existing,
        )
        assert not is_dup
        assert dup_id is None


class TestGenerateCandidates:
    def test_generates_candidates_for_hms_v2(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        candidates = generate_candidates(matches, HMS_ADR)
        assert len(candidates) > 0
        assert all(c.adr.status == "proposed" for c in candidates)
        assert all(c.adr.source == "bootstrap" for c in candidates)

    def test_each_candidate_has_unique_id(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        candidates = generate_candidates(matches, HMS_ADR)
        ids = [c.adr.id for c in candidates]
        assert len(ids) == len(set(ids))

    def test_candidates_have_rationale(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        candidates = generate_candidates(matches, HMS_ADR)
        for c in candidates:
            assert "## Context" in c.adr.rationale
            assert "## Decision (candidate)" in c.adr.rationale
            assert "## Confidence" in c.adr.rationale

    def test_min_confidence_filters_low(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        all_candidates = generate_candidates(matches, HMS_ADR, min_confidence="low")
        high_only = generate_candidates(matches, HMS_ADR, min_confidence="high")
        assert len(high_only) <= len(all_candidates)

    def test_known_adrs_are_skipped(self):
        from decisiondrift.bootstrap.candidate_generator import _is_duplicate
        from decisiondrift.models.schema import DecisionRecord

        existing = [
            DecisionRecord(
                id="ADR-0001",
                title="Use Flask as Web Framework",
                status="accepted",
                severity="high",
                keywords=["flask"],
            ),
            DecisionRecord(
                id="ADR-0002",
                title="Use SQLAlchemy as ORM",
                status="accepted",
                severity="high",
                keywords=["sqlalchemy"],
            ),
        ]
        is_dup, dup_id = _is_duplicate(
            "Use Flask as Web Framework",
            ["flask", "web"],
            existing,
        )
        assert is_dup

    def test_no_matches_returns_empty(self):
        matches = []
        candidates = generate_candidates(matches, HMS_ADR)
        assert candidates == []


class TestApplyCandidates:
    def test_apply_writes_files(self):
        from decisiondrift.bootstrap.candidate_generator import CandidateADR
        from decisiondrift.models.schema import DecisionRecord

        with tempfile.TemporaryDirectory() as tmp:
            adr_dir = Path(tmp)
            candidates = [
                CandidateADR(
                    adr=DecisionRecord(
                        id="ADR-9001",
                        title="Test Pattern",
                        status="proposed",
                        severity="medium",
                        source="bootstrap",
                        rationale="## Test\n\nTest body",
                        keywords=["test"],
                        evidence=["test.py"],
                    ),
                    pattern_name="Test Pattern",
                    confidence="medium",
                    evidence=["test.py"],
                ),
            ]
            count = apply_candidates(candidates, adr_dir)
            assert count == 1
            assert (adr_dir / "ADR-9001.md").exists()

    def test_apply_creates_adr_dir(self):
        from decisiondrift.bootstrap.candidate_generator import CandidateADR
        from decisiondrift.models.schema import DecisionRecord

        with tempfile.TemporaryDirectory() as tmp:
            adr_dir = Path(tmp) / "docs" / "adr"
            assert not adr_dir.exists()
            candidates = [
                CandidateADR(
                    adr=DecisionRecord(
                        id="ADR-9002",
                        title="Test Pattern",
                        status="proposed",
                        severity="medium",
                        source="bootstrap",
                        rationale="## Test\n\nTest body",
                        keywords=["test"],
                        evidence=["test.py"],
                    ),
                    pattern_name="Test Pattern",
                    confidence="medium",
                    evidence=["test.py"],
                ),
            ]
            count = apply_candidates(candidates, adr_dir)
            assert count == 1
            assert adr_dir.exists()

    def test_apply_writes_valid_adr_format(self):
        import frontmatter

        from decisiondrift.bootstrap.candidate_generator import CandidateADR
        from decisiondrift.models.schema import DecisionRecord

        with tempfile.TemporaryDirectory() as tmp:
            adr_dir = Path(tmp)
            candidates = [
                CandidateADR(
                    adr=DecisionRecord(
                        id="ADR-9003",
                        title="Written ADR",
                        status="proposed",
                        severity="high",
                        source="bootstrap",
                        rationale="## Decision\n\nDo the thing.",
                        keywords=["test"],
                        evidence=["file.py"],
                    ),
                    pattern_name="Test",
                    confidence="high",
                    evidence=["file.py"],
                ),
            ]
            apply_candidates(candidates, adr_dir)
            post = frontmatter.load(str(adr_dir / "ADR-9003.md"))
            assert dict(post.metadata)["title"] == "Written ADR"
            assert "## Decision" in post.content
