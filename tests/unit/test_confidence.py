from __future__ import annotations

from decisiondrift.models.schema import ConfidenceLevel
from decisiondrift.rules.engine import _to_finding
from decisiondrift.rules.models import Action, Rule, RuleType


class TestConfidenceHigh:
    def test_high_confidence_block_stays_block(self):
        rule = Rule(
            id="R001",
            type=RuleType.DEPENDENCY,
            match="flask",
            action=Action.BLOCK,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.HIGH,
        )
        finding = _to_finding(rule, "flask", "requirements.txt")
        assert finding.action == Action.BLOCK

    def test_high_confidence_require_approval_stays(self):
        rule = Rule(
            id="R002",
            type=RuleType.IMPORT,
            match="flask",
            action=Action.REQUIRE_APPROVAL,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.HIGH,
        )
        finding = _to_finding(rule, "flask", "app.py")
        assert finding.action == Action.REQUIRE_APPROVAL

    def test_high_confidence_warn_stays_warn(self):
        rule = Rule(
            id="R003",
            type=RuleType.PATH,
            match=r"^src/legacy/",
            action=Action.WARN,
            source_adr="ADR-0002",
            confidence=ConfidenceLevel.HIGH,
        )
        finding = _to_finding(rule, "src/legacy/old.py")
        assert finding.action == Action.WARN


class TestConfidenceMedium:
    def test_medium_confidence_block_downgrades_to_warn(self):
        rule = Rule(
            id="R004",
            type=RuleType.DEPENDENCY,
            match="django",
            action=Action.BLOCK,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.MEDIUM,
        )
        finding = _to_finding(rule, "django", "requirements.txt")
        assert finding.action == Action.WARN

    def test_medium_confidence_require_approval_downgrades_to_warn(self):
        rule = Rule(
            id="R005",
            type=RuleType.IMPORT,
            match="django",
            action=Action.REQUIRE_APPROVAL,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.MEDIUM,
        )
        finding = _to_finding(rule, "django", "app.py")
        assert finding.action == Action.WARN

    def test_medium_confidence_warn_stays_warn(self):
        rule = Rule(
            id="R006",
            type=RuleType.CONFIG,
            match="debug=true",
            action=Action.WARN,
            source_adr="ADR-0003",
            confidence=ConfidenceLevel.MEDIUM,
        )
        finding = _to_finding(rule, "debug=true", "config.py")
        assert finding.action == Action.WARN


class TestConfidenceLow:
    def test_low_confidence_block_downgrades_to_info(self):
        rule = Rule(
            id="R007",
            type=RuleType.DEPENDENCY,
            match="old-lib",
            action=Action.BLOCK,
            source_adr="ADR-0004",
            confidence=ConfidenceLevel.LOW,
        )
        finding = _to_finding(rule, "old-lib", "requirements.txt")
        assert finding.action == Action.INFO

    def test_low_confidence_require_approval_downgrades_to_info(self):
        rule = Rule(
            id="R008",
            type=RuleType.IMPORT,
            match="old-lib",
            action=Action.REQUIRE_APPROVAL,
            source_adr="ADR-0004",
            confidence=ConfidenceLevel.LOW,
        )
        finding = _to_finding(rule, "old-lib", "app.py")
        assert finding.action == Action.INFO

    def test_low_confidence_warn_downgrades_to_info(self):
        rule = Rule(
            id="R009",
            type=RuleType.PATH,
            match=r"^old/",
            action=Action.WARN,
            source_adr="ADR-0004",
            confidence=ConfidenceLevel.LOW,
        )
        finding = _to_finding(rule, "old/stuff.py")
        assert finding.action == Action.INFO


class TestConfidenceBoundary:
    def test_confidence_just_below_high_boundary(self):
        rule = Rule(
            id="R010",
            type=RuleType.DEPENDENCY,
            match="flask",
            action=Action.BLOCK,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.HIGH,
        )
        rule.confidence = ConfidenceLevel.HIGH
        finding = _to_finding(rule, "flask")
        assert finding.action == Action.BLOCK

    def test_action_severity_maps_correctly(self):
        rule = Rule(
            id="R011",
            type=RuleType.DEPENDENCY,
            match="flask",
            action=Action.BLOCK,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.HIGH,
        )
        finding = _to_finding(rule, "flask")
        assert finding.severity == "critical"

        rule2 = Rule(
            id="R012",
            type=RuleType.IMPORT,
            match="flask",
            action=Action.WARN,
            source_adr="ADR-0001",
            confidence=ConfidenceLevel.HIGH,
        )
        finding2 = _to_finding(rule2, "flask")
        assert finding2.severity == "medium"
