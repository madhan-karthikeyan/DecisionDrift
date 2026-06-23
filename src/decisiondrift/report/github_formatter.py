from __future__ import annotations

from decisiondrift.models.schema import Finding, ReviewResult

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

ACTION_EMOJI = {
    "block": "🚫",
    "require_approval": "👀",
    "warn": "⚠️",
    "info": "ℹ️",
}


def _collapsible(summary: str, body: str) -> str:
    return f"<details>\n<summary>{summary}</summary>\n\n{body}\n</details>"


def compile_github_comment(
    result: ReviewResult | None,
    rule_findings: list | None = None,
) -> str:
    parts = [
        "<!-- decisiondrift-review -->",
        "## DecisionDrift Review",
    ]

    # Determine sections based on what we have
    has_rule = rule_findings and len(rule_findings) > 0
    has_lm = result and result.findings

    if not has_rule and not has_lm:
        files = result.files_scanned if result else 0
        adrs = result.adrs_considered if result else 0
        return (
            "<!-- decisiondrift-review -->\n"
            "## DecisionDrift Review\n\n"
            "ℹ️ No findings.\n\n"
            f"*Scanned {files} file(s), {adrs} ADR(s).*"
            "\n<!-- end decisiondrift-review -->"
        )

    # Rule engine findings (deterministic)
    if has_rule:
        parts.append("\n### 🔍 Deterministic Rule Findings")
        parts.append("")
        for f in rule_findings:
            e = ACTION_EMOJI.get(getattr(f, "action", None) or f.get("action", "info"), "ℹ️")
            action = getattr(f, "action", None) or f.get("action", "info")
            if hasattr(action, "value"):
                action = action.value
            adr_id = getattr(f, "adr_id", None) or f.get("adr_id", "")
            rule_type = getattr(f, "rule_type", None) or f.get("rule_type", "")
            if hasattr(rule_type, "value"):
                rule_type = rule_type.value
            match_val = getattr(f, "match_value", None) or f.get("match_value", "")
            file_path = getattr(f, "file_path", None) or f.get("file_path")
            summary = f"{e} **{action.upper()}** · {adr_id} ({rule_type})"
            body_lines = [f"**Match:** `{match_val}`"]
            if file_path:
                body_lines.append(f"**File:** `{file_path}`")
            desc = getattr(f, "description", None) or f.get("description", "")
            if desc:
                body_lines.append(f"**Detail:** {desc}")
            body = "\n\n".join(body_lines)
            parts.append(f"\n{_collapsible(summary, body)}\n")

    # LLM findings (semantic)
    if has_lm:
        violations = [f for f in result.findings if f.classification in ("violates", "likely_violates")]
        others = [f for f in result.findings if f.classification not in ("violates", "likely_violates")]

        if violations:
            parts.append(f"\n### 🤖 LLM Classification — {len(violations)} Violation(s)")
            parts.append("")
            for f in violations:
                emoji = SEVERITY_EMOJI.get(f.severity, "⚪")
                summary = f"{emoji} **{f.severity.upper()}** · {f.adr_id} · {f.adr_title}"
                body_lines = [
                    f"**File:** `{f.file_path}`",
                    f"**Symbol:** `{f.symbol_name}`",
                    f"**Reasoning:** {f.reasoning}" if f.reasoning else "",
                    f"**Suggested Action:** {f.suggested_action}" if f.suggested_action else "",
                    f"**Confidence:** {f.confidence:.0%} ({f.evidence_strength})",
                ]
                body = "\n\n".join(l for l in body_lines if l)
                parts.append(f"\n{_collapsible(summary, body)}\n")
        else:
            parts.append("\n### ✅ LLM Classification — No Violations Detected")

        if others:
            others_text = "\n".join(
                f"- `{f.adr_id}` — {f.adr_title} ({f.classification}, {f.evidence_strength})"
                for f in others
            )
            parts.append(f"\n<details>\n<summary>📋 {len(others)} Additional LLM Finding(s)</summary>\n\n{others_text}\n</details>\n")

    # Summary line
    total_files = result.files_scanned if has_lm else 0
    total_adrs = result.adrs_considered if has_lm else 0
    parts.append(
        "\n---\n"
        f"*Scanned {total_files} file(s), {total_adrs} ADR(s). "
        f"Deterministic rule engine + LLM semantic analysis.*"
    )
    parts.append("<!-- end decisiondrift-review -->")

    return "\n".join(parts)
