from __future__ import annotations

from decisiondrift.models.schema import Finding, ReviewResult


def compile_markdown(result: ReviewResult) -> str:
    if not result.findings:
        return _no_findings(result)

    violations = [f for f in result.findings if f.classification in ("violates", "likely_violates")]

    if not violations:
        return _no_violations(result)

    return _violations_report(violations, result)


def compile_text(
    result: ReviewResult,
    rule_findings: list | None = None,
) -> str:
    """Compact text format for CLI output.

    Includes both deterministic rule findings and LLM classification findings.
    """
    lines: list[str] = []

    # Rule engine findings
    if rule_findings:
        lines.append("## Deterministic Rule Findings")
        lines.append("")
        for f in rule_findings:
            action = getattr(f, "action", None) or f.get("action", "info")
            if hasattr(action, "value"):
                action = action.value
            adr_id = getattr(f, "adr_id", None) or f.get("adr_id", "")
            rule_type = getattr(f, "rule_type", None) or f.get("rule_type", "")
            if hasattr(rule_type, "value"):
                rule_type = rule_type.value
            match_val = getattr(f, "match_value", None) or f.get("match_value", "")
            file_path = getattr(f, "file_path", None) or f.get("file_path")

            lines.append(f"  [{action.upper()}] {adr_id} ({rule_type})")
            lines.append(f"           Match: {match_val}")
            if file_path:
                lines.append(f"           File: {file_path}")
            lines.append("")

    # LLM findings
    if not result or not result.findings:
        if not rule_findings:
            return (
                f"No findings.\n"
                f"Scanned {result.files_scanned} file(s), {result.symbols_analyzed} symbol(s), "
                f"{result.adrs_considered} ADR(s)."
            )
        lines.append("---")
        lines.append(f"{len(rule_findings)} rule finding(s). No LLM findings.")
        return "\n".join(lines)

    violations = [f for f in result.findings if f.classification in ("violates", "likely_violates")]

    if violations:
        if rule_findings:
            lines.append("## LLM Classification Findings")
            lines.append("")
        for f in violations:
            lines.append(f.evidence_strength.upper())
            lines.append(f.adr_id)
            lines.append("")
            lines.append(f"  Symbol: {f.symbol_name}")
            lines.append(f"  File: {f.file_path}")
            lines.append(f"  Classification: {f.classification}")
            lines.append(f"  Reasoning: {f.reasoning}")
            if f.suggested_action:
                lines.append(f"  Suggested: {f.suggested_action}")
            lines.append("")
    else:
        lines.append("No violations detected.")

    lines.append("---")
    parts = []
    if rule_findings:
        parts.append(f"{len(rule_findings)} rule finding(s)")
    if result.findings:
        parts.append(f"{len(result.findings)} LLM finding(s)")
    parts.append(f"{result.files_scanned} file(s) scanned")
    parts.append(f"{result.symbols_analyzed} symbol(s)")
    lines.append(", ".join(parts) + ".")
    return "\n".join(lines)


def _no_findings(result: ReviewResult) -> str:
    return (
        f"No findings.\n"
        f"Scanned {result.files_scanned} file(s), {result.symbols_analyzed} symbol(s), "
        f"{result.adrs_considered} ADR(s)."
    )


def _no_violations(result: ReviewResult) -> str:
    total = len(result.findings)
    return (
        f"No violations detected.\n"
        f"{total} finding(s) reviewed, all clear. "
        f"Scanned {result.files_scanned} file(s), {result.symbols_analyzed} symbol(s), "
        f"{result.adrs_considered} ADR(s)."
    )


def _violations_report(violations: list[Finding], result: ReviewResult) -> str:
    lines: list[str] = []
    for f in violations:
        lines.append(f.evidence_strength.upper())
        lines.append(f.adr_id)
        lines.append("")
        lines.append(f"  Symbol: {f.symbol_name}")
        lines.append(f"  File: {f.file_path}")
        lines.append(f"  Classification: {f.classification}")
        lines.append(f"  Reasoning: {f.reasoning}")
        if f.suggested_action:
            lines.append(f"  Suggested: {f.suggested_action}")
        lines.append("")

    lines.append("---")
    lines.append(
        f"{len(violations)} violation(s) found across {result.files_scanned} file(s)."
    )
    return "\n".join(lines)
