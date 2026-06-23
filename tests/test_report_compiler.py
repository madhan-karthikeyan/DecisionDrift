from __future__ import annotations

from decisiondrift.models.schema import Finding, ReviewResult
from decisiondrift.report.compiler import compile_text


class TestCompiler:
    def test_no_findings(self):
        result = ReviewResult(files_scanned=2, symbols_analyzed=5)
        output = compile_text(result)
        assert "No findings" in output
        assert "2 file(s)" in output
        assert "5 symbol(s)" in output

    def test_no_violations(self):
        result = ReviewResult(
            findings=[
                Finding(
                    adr_id="ADR-001",
                    adr_title="Use Flask",
                    severity="high",
                    confidence=0.3,
                    evidence_strength="low",
                    symbol_name="app",
                    file_path="run.py",
                    classification="not_applicable",
                    reasoning="Follows the pattern.",
                    suggested_action="",
                )
            ],
            files_scanned=1,
            symbols_analyzed=1,
            adrs_considered=1,
        )
        output = compile_text(result)
        assert "No violations detected" in output

    def test_violation_output(self):
        result = ReviewResult(
            findings=[
                Finding(
                    adr_id="ADR-0002",
                    adr_title="Use SQLAlchemy ORM",
                    severity="critical",
                    confidence=0.9,
                    evidence_strength="high",
                    symbol_name="get_user_directly",
                    file_path="backend/models/user.py",
                    classification="violates",
                    reasoning="Uses raw sqlite3 instead of SQLAlchemy ORM.",
                    suggested_action="Use db.session.execute() instead.",
                )
            ],
            files_scanned=1,
            symbols_analyzed=3,
            adrs_considered=12,
        )
        output = compile_text(result)
        assert "HIGH" in output
        assert "ADR-0002" in output
        assert "get_user_directly" in output
        assert "backend/models/user.py" in output
        assert "LLM finding(s)" in output
