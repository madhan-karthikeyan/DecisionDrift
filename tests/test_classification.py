from __future__ import annotations

from decisiondrift.classification.classifier import Classifier
from decisiondrift.classification.models import ClassificationInput
from decisiondrift.models.schema import DecisionRecord, ImpactedSymbol


class TestClassifier:
    def _make_input(self, adr_title: str, symbol_name: str, diff_hunk: str = "") -> ClassificationInput:
        adr = DecisionRecord(
            id="ADR-001",
            title=adr_title,
            status="accepted",
            severity="high",
            rationale="All code must follow this rule for consistency.",
        )
        symbol = ImpactedSymbol(
            name=symbol_name,
            kind="function",
            file="test.py",
            diff_hunk=diff_hunk,
        )
        return ClassificationInput(adr=adr, symbol=symbol, diff_hunk=diff_hunk)

    def test_fallback_without_api_key(self):
        classifier = Classifier(api_key=None)
        inp = self._make_input("Use SQLAlchemy ORM", "db_connect", "sqlite3.connect(...)")
        results = classifier.classify([inp])
        assert len(results) == 1
        assert results[0].finding.classification == "needs_human_review"
        assert results[0].finding.adr_id == "ADR-001"

    def test_fallback_empty_input(self):
        classifier = Classifier(api_key=None)
        results = classifier.classify([])
        assert results == []

    def test_adr_id_propagates(self):
        classifier = Classifier(api_key=None)
        inp = self._make_input("Use JWT", "login")
        results = classifier.classify([inp])
        assert results[0].adr_id == "ADR-001"
        assert results[0].classification == "needs_human_review"

    def test_symbol_name_in_result(self):
        classifier = Classifier(api_key=None)
        inp = self._make_input("Use Redis", "cache_get")
        results = classifier.classify([inp])
        assert results[0].finding.symbol_name == "cache_get"

    def test_finding_has_all_fields(self):
        classifier = Classifier(api_key=None)
        inp = self._make_input("Use SQLAlchemy ORM", "db_query")
        results = classifier.classify([inp])
        f = results[0].finding
        assert f.adr_id == "ADR-001"
        assert f.adr_title == "Use SQLAlchemy ORM"
        assert f.severity == "high"
        assert f.confidence == 0.3  # low maps to 0.3
        assert f.evidence_strength == "low"
        assert f.symbol_name == "db_query"
        assert f.file_path == "test.py"
        assert f.classification == "needs_human_review"
