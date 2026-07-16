from __future__ import annotations

import json

from decisiondrift.models.schema import ReportEnvelope


def format_output(envelope: ReportEnvelope, fmt: str = "text") -> str:
    if fmt == "json":
        return _format_json(envelope)
    if fmt == "sarif":
        return _format_sarif(envelope)
    if fmt == "markdown":
        return _format_markdown(envelope)
    return _format_text(envelope)


def _format_json(envelope: ReportEnvelope) -> str:
    return envelope.model_dump_json(indent=2)


def _format_sarif(envelope: ReportEnvelope) -> str:
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "DecisionDrift",
                        "version": envelope.tool_version,
                        "informationUri": "https://github.com/madhan-karthikeyan/DecisionDrift",
                    }
                },
                "results": _findings_to_sarif_results(envelope.findings),
                "properties": {
                    "summary": envelope.summary,
                    "command": envelope.command,
                    "duration_ms": envelope.duration_ms,
                },
            }
        ],
    }
    return json.dumps(sarif, indent=2)


def _findings_to_sarif_results(findings: list[dict]) -> list[dict]:
    results = []
    for f in findings:
        level = "error"
        action = f.get("action", "").lower()
        if action in ("warn", "require_approval"):
            level = "warning"
        elif action in ("info",):
            level = "note"
        result = {
            "ruleId": f.get("rule_id", f.get("adr_id", "unknown")),
            "level": level,
            "message": {
                "text": f.get("description", f.get("match_value", "Finding"))
            },
        }
        loc = f.get("file_path")
        if loc:
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": loc},
                    }
                }
            ]
        results.append(result)
    return results


def _format_markdown(envelope: ReportEnvelope) -> str:
    lines: list[str] = []
    cmd = envelope.command
    summary = envelope.summary
    findings = envelope.findings

    lines.append(f"# DecisionDrift Report — {cmd}")
    lines.append("")
    lines.append(f"**Tool version:** {envelope.tool_version}")
    lines.append(f"**Timestamp:** {envelope.timestamp}")
    if envelope.duration_ms:
        lines.append(f"**Duration:** {envelope.duration_ms}ms")
    lines.append("")

    if summary:
        lines.append("## Summary")
        lines.append("")
        for key, val in summary.items():
            lines.append(f"- **{key}:** {val}")
        lines.append("")

    if findings:
        lines.append(f"## Findings ({len(findings)})")
        lines.append("")
        for i, f in enumerate(findings, 1):
            action = f.get("action", "info").upper()
            desc = f.get("description", f.get("match_value", ""))
            adr = f.get("adr_id", "")
            file_path = f.get("file_path", "")
            lines.append(f"### {i}. [{action}] {desc}")
            if adr:
                lines.append(f"- ADR: {adr}")
            if file_path:
                lines.append(f"- File: `{file_path}`")
            lines.append("")
    else:
        lines.append("**No findings.**")
        lines.append("")

    return "\n".join(lines)


def _format_text(envelope: ReportEnvelope) -> str:
    cmd = envelope.command
    summary = envelope.summary
    findings = envelope.findings

    lines: list[str] = []

    message = summary.pop("message", "") if summary else ""
    status = summary.pop("status", "") if summary else ""

    if message:
        lines.append(message)
        lines.append("")

    if summary and not message:
        for key, val in summary.items():
            if key in ("exit_code", "findings_count"):
                continue
            lines.append(f"{key.replace('_', ' ').title()}: {val}")
        lines.append("")

    if findings:
        for f in findings:
            action = f.get("action", "info").upper()
            adr_id = f.get("adr_id", "")
            rule_type = f.get("rule_type", "")
            match_value = f.get("match_value", "")
            file_path = f.get("file_path", "")
            description = f.get("description", "")

            lines.append(f"  [{action}] {adr_id} ({rule_type})")
            lines.append(f"           Match: {match_value}")
            if file_path:
                lines.append(f"           File: {file_path}")
            if description:
                lines.append(f"           {description}")
            lines.append("")

        lines.append("---")
        findings_count = summary.get("findings_count", len(findings)) if summary else len(findings)
        rules = summary.get("rules_evaluated", "") if summary else ""
        files = summary.get("files_scanned", "") if summary else ""
        parts = [f"{findings_count} finding(s)"]
        if rules:
            parts.append(f"{rules} rule(s) evaluated")
        if files:
            parts.append(f"{files} file(s) scanned")
        lines.append(", ".join(parts) + ".")
    elif status == "no_active_adrs":
        pass
    elif status == "clean":
        lines.append("No violations found.")
    else:
        lines.append("No findings.")

    return "\n".join(lines)
