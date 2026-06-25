from __future__ import annotations

from decisiondrift.adr.rule_generator import _rules_for_adr
from decisiondrift.models.schema import DecisionRecord
from decisiondrift.rules.models import Action, RuleType


class TestRuleGenerator:
    def test_prohibition_generates_dep_and_import_rules(self):
        adr = DecisionRecord(
            id="ADR-0001",
            title="Use FastAPI",
            status="accepted",
            severity="high",
            prohibitions=["flask"],
        )
        rules = _rules_for_adr(adr)
        assert len(rules) == 2
        assert rules[0].type == RuleType.DEPENDENCY
        assert rules[0].match == "flask"
        assert rules[0].action == Action.BLOCK
        assert rules[0].source_adr == "ADR-0001"
        assert rules[1].type == RuleType.IMPORT
        assert rules[1].match == "flask"
        assert rules[1].action == Action.BLOCK
        assert rules[1].source_adr == "ADR-0001"

    def test_multiple_prohibitions(self):
        adr = DecisionRecord(
            id="ADR-0002",
            title="No Redis Queues",
            status="accepted",
            severity="high",
            prohibitions=["redis", "rq"],
        )
        rules = _rules_for_adr(adr)
        assert len(rules) == 4
        assert [r.match for r in rules] == ["redis", "redis", "rq", "rq"]

    def test_no_prohibitions(self):
        adr = DecisionRecord(
            id="ADR-0003",
            title="Use PostgreSQL",
            status="accepted",
            severity="medium",
        )
        rules = _rules_for_adr(adr)
        assert len(rules) == 0

    def test_rules_from_source_confidence(self):
        manual = DecisionRecord(
            id="ADR-01", title="Manual", status="accepted", severity="high", source="manual", prohibitions=["foo"]
        )
        bootstrap = DecisionRecord(
            id="ADR-02",
            title="Bootstrap",
            status="accepted",
            severity="medium",
            source="bootstrap",
            prohibitions=["bar"],
        )
        ingest = DecisionRecord(
            id="ADR-03", title="Ingest", status="accepted", severity="low", source="ingest", prohibitions=["baz"]
        )
        manual_rules = _rules_for_adr(manual)
        bootstrap_rules = _rules_for_adr(bootstrap)
        ingest_rules = _rules_for_adr(ingest)
        assert manual_rules[0].confidence.value == "high"
        assert bootstrap_rules[0].confidence.value == "medium"
        assert ingest_rules[0].confidence.value == "low"
