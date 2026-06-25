from __future__ import annotations

from decisiondrift.rules.models import Action, Rule, RuleSet, RuleType


class TestRuleModel:
    def test_rule_creation(self):
        rule = Rule(
            id="test-rule",
            type=RuleType.DEPENDENCY,
            match="flask",
            action=Action.BLOCK,
            source_adr="ADR-0001",
        )
        assert rule.id == "test-rule"
        assert rule.type == RuleType.DEPENDENCY
        assert rule.match == "flask"
        assert rule.action == Action.BLOCK
        assert rule.source_adr == "ADR-0001"

    def test_ruleset_by_type(self):
        rules = RuleSet(
            rules=[
                Rule(id="r1", type=RuleType.DEPENDENCY, match="flask", action=Action.BLOCK, source_adr="ADR-1"),
                Rule(id="r2", type=RuleType.IMPORT, match="flask", action=Action.BLOCK, source_adr="ADR-1"),
                Rule(id="r3", type=RuleType.DEPENDENCY, match="redis", action=Action.BLOCK, source_adr="ADR-2"),
            ]
        )
        dep_rules = rules.by_type(RuleType.DEPENDENCY)
        assert len(dep_rules) == 2
        assert dep_rules[0].match == "flask"
        assert dep_rules[1].match == "redis"

    def test_ruleset_for_adr(self):
        rules = RuleSet(
            rules=[
                Rule(id="r1", type=RuleType.DEPENDENCY, match="flask", action=Action.BLOCK, source_adr="ADR-1"),
                Rule(id="r2", type=RuleType.IMPORT, match="redis", action=Action.BLOCK, source_adr="ADR-2"),
            ]
        )
        adr1_rules = rules.for_adr("ADR-1")
        assert len(adr1_rules) == 1
        assert adr1_rules[0].match == "flask"


class TestActionEnum:
    def test_action_values(self):
        assert Action.BLOCK.value == "block"
        assert Action.REQUIRE_APPROVAL.value == "require_approval"
        assert Action.WARN.value == "warn"
        assert Action.INFO.value == "info"
