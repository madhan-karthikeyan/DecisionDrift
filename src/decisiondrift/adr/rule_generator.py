from __future__ import annotations

from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.supersession import resolve_active
from decisiondrift.models.schema import DecisionRecord
from decisiondrift.rules.models import Action, Rule, RuleSet, RuleType


def generate_rules_from_adrs(
    adr_dir: str,
    status_filter: set[str] | None = None,
) -> RuleSet:
    """Generate rules from all ADRs, using prohibitions and custom rule fields."""
    decisions = load_adrs(adr_dir, status_filter=status_filter)
    active = resolve_active(decisions)
    all_rules: list[Rule] = []
    for adr in active:
        all_rules.extend(_rules_for_adr(adr))
    return RuleSet(rules=all_rules)


def _rules_for_adr(adr: DecisionRecord) -> list[Rule]:
    rules: list[Rule] = []
    confidence = adr.confidence or _default_confidence(adr.source)

    for prohibition in adr.prohibitions:
        rules.append(
            Rule(
                id=f"{adr.id}-dep-{_safe_id(prohibition)}",
                type=RuleType.DEPENDENCY,
                match=prohibition.strip().lower(),
                action=Action.BLOCK,
                source_adr=adr.id,
                confidence=confidence,
                description=f"ADR {adr.id}: {adr.title} — prohibition of dependency '{prohibition}'",
            )
        )
        rules.append(
            Rule(
                id=f"{adr.id}-imp-{_safe_id(prohibition)}",
                type=RuleType.IMPORT,
                match=prohibition.strip().lower(),
                action=Action.BLOCK,
                source_adr=adr.id,
                confidence=confidence,
                description=f"ADR {adr.id}: {adr.title} — prohibition of import '{prohibition}'",
            )
        )

    return rules


def _safe_id(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value.lower())


def _default_confidence(source: str) -> str:
    return {"manual": "high", "bootstrap": "medium", "ingest": "low"}.get(source, "medium")
