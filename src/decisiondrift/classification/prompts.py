from __future__ import annotations

SYSTEM_PROMPT = """You are a code review assistant. Your task is to determine whether a code change violates a specific architecture decision rule.

Given a decision rule (ADR) and a code change (diff hunk), determine if the change contradicts the rule.

Consider:
1. The decision's stated rule and rationale
2. Any explicit exceptions to the rule
3. The specific code change, not the surrounding code quality
4. The symbol being changed (function, class, or method)

Output ONLY valid JSON with no additional text."""


def build_user_prompt(
    adr_title: str,
    adr_rationale: str,
    adr_exceptions: str | None,
    symbol_name: str,
    symbol_type: str,
    file_path: str,
    diff_hunk: str,
) -> str:
    exceptions_text = adr_exceptions if adr_exceptions else "None"
    return f"""Decision Rule: {adr_title}
Rationale: {adr_rationale}
Exceptions: {exceptions_text}

Changed Symbol: {symbol_name} ({symbol_type})
File: {file_path}

Diff Hunk:
```
{diff_hunk}
```

Respond with JSON only:
{{
  "classification": "violates" | "likely_violates" | "ambiguous" | "not_applicable" | "needs_human_review",
  "evidence_strength": "high" | "medium" | "low",
  "reasoning": "Brief explanation of why this does or does not violate the decision",
  "suggested_action": "What the developer should do instead"
}}"""


CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["violates", "likely_violates", "ambiguous", "not_applicable", "needs_human_review"],
        },
        "evidence_strength": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "reasoning": {"type": "string"},
        "suggested_action": {"type": "string"},
    },
    "required": ["classification", "evidence_strength", "reasoning", "suggested_action"],
}
