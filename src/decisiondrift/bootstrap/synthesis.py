from __future__ import annotations

import json
from typing import Any

from decisiondrift.bootstrap.architecture import ArchitectureModel
from decisiondrift.bootstrap.template_generator import (
    ADRSuggestion,
    _is_duplicate,
)
from decisiondrift.llm.client import LLMClient, LLMResponseError
from decisiondrift.models.schema import ConfidenceLevel, DecisionRecord


def generate_suggestions_llm(
    model: ArchitectureModel,
    existing_titles: set[str],
    next_id: int,
    llm: LLMClient,
) -> list[ADRSuggestion]:
    """Generate ADR candidates via a single LLM call on the architecture model.

    Requires an LLMClient with a configured API key.
    Falls back gracefully — returns an empty list on error (caller should use templates).
    """
    if not llm.available():
        return []

    arch_json = model.architecture_json()
    existing_str = ", ".join(sorted(existing_titles)) if existing_titles else "none"

    prompt = f"""Repository architecture:

{json.dumps(arch_json, indent=2)}

Existing decisions already documented (skip these): {existing_str}

Generate one ADR per detected technology with strong evidence.

Constraints:
- Every ADR must map to at least one detected technology.
- Every ADR must cite specific evidence from the detection.
- Every ADR must include at least one realistic prohibition.
- Never mention technologies absent from the architecture.
- Never infer business requirements or organizational structure.
- Never generate ADRs for generic patterns (CQRS, DDD, microservices, event sourcing).
- Only generate ADRs for technologies with confidence >= 0.7.

Output JSON with an "adrs" array containing objects with:
- title: string
- rationale: string (2-3 sentences specific to this tech stack)
- prohibitions: list of strings
- evidence: list of strings
- confidence: "high", "medium", or "low"
- category: string (e.g. "framework", "database", "cache")
"""

    try:
        data = llm.complete_json(prompt)
    except LLMResponseError:
        return []

    adrs_data = data.get("adrs", []) if isinstance(data, dict) else []
    if not adrs_data:
        return []

    suggestions: list[ADRSuggestion] = []
    num = next_id

    for item in adrs_data:
        if not isinstance(item, dict):
            continue
        title = item.get("title", "")
        if not title:
            continue
        if _is_duplicate(title, existing_titles):
            continue

        rationale = item.get("rationale", "No rationale provided.")
        prohibitions = item.get("prohibitions", [])
        confidence_str = item.get("confidence", "medium")
        category = item.get("category", "unknown")

        # Map LLM confidence to ConfidenceLevel
        conf_map = {"high": ConfidenceLevel.HIGH, "medium": ConfidenceLevel.MEDIUM, "low": ConfidenceLevel.LOW}
        conf_level = conf_map.get(confidence_str, ConfidenceLevel.MEDIUM)

        # Find the matching detected technology for evidence
        evidence_raw = item.get("evidence", [])
        tech_name = item.get("title", "").replace("Use ", "").split(" for")[0].split(" as")[0].strip()
        matching_tech = None
        for ft in model.findings:
            if ft.name.lower() == tech_name.lower():
                matching_tech = ft
                break

        if not matching_tech:
            continue

        adr_id = f"ADR-{num:04d}"
        num += 1

        adr = DecisionRecord(
            id=adr_id,
            title=title,
            status="proposed",
            severity="medium",
            type=category,
            source="bootstrap_llm",
            rationale=rationale,
            prohibitions=prohibitions,
            keywords=[matching_tech.name.lower(), category],
            evidence=evidence_raw,
            confidence=conf_level,
        )

        rules = []
        for p in prohibitions:
            rules.append({"type": "dependency", "match": p, "action": "block"})
            rules.append({"type": "import", "match": p, "action": "block"})

        suggestions.append(ADRSuggestion(tech=matching_tech, adr=adr, rules=rules))

    return suggestions
