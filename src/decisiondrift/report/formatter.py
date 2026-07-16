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
    if fmt == "html":
        return _format_html(envelope)
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


def _format_html(envelope: ReportEnvelope) -> str:
    cmd = envelope.command
    summary = envelope.summary
    findings = envelope.findings

    status = summary.get("status", "") if summary else ""
    findings_count = len(findings)
    status_color = "#22c55e" if status == "clean" else ("#ef4444" if findings_count else "#6b7280")
    status_label = "Clean" if status == "clean" else (f"{findings_count} Finding(s)" if findings_count else "No Findings")

    rows = ""
    for i, f in enumerate(findings, 1):
        action = f.get("action", "info").upper()
        desc = f.get("description", f.get("match_value", ""))
        adr = f.get("adr_id", "")
        file_path = f.get("file_path", "")
        rule_type = f.get("rule_type", "")
        action_colors = {"BLOCK": "#ef4444", "REQUIRE_APPROVAL": "#f59e0b", "WARN": "#f97316", "INFO": "#6b7280"}
        ac = action_colors.get(action, "#6b7280")
        rows += f"""
        <tr>
          <td><span class="badge" style="background:{ac}">{action}</span></td>
          <td>{adr}</td>
          <td>{rule_type}</td>
          <td>{desc}</td>
          <td>{file_path}</td>
        </tr>"""

    summary_rows = ""
    if summary:
        for key, val in summary.items():
            if key in ("message", "status"):
                continue
            summary_rows += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{val}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DecisionDrift Report — {cmd}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f8fafc; color:#1e293b; padding:2rem; }}
  .container {{ max-width:960px; margin:0 auto; }}
  header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:2rem; }}
  h1 {{ font-size:1.5rem; font-weight:600; }}
  .status {{ padding:0.5rem 1rem; border-radius:9999px; color:#fff; font-weight:500; font-size:0.875rem; }}
  .meta {{ display:flex; gap:2rem; margin-bottom:2rem; color:#64748b; font-size:0.875rem; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background:#f1f5f9; text-align:left; padding:0.75rem 1rem; font-weight:600; font-size:0.875rem; text-transform:uppercase; color:#475569; }}
  td {{ padding:0.75rem 1rem; border-top:1px solid #e2e8f0; font-size:0.875rem; }}
  .badge {{ display:inline-block; padding:0.125rem 0.5rem; border-radius:4px; color:#fff; font-size:0.75rem; font-weight:600; }}
  .empty {{ text-align:center; padding:3rem; color:#94a3b8; }}
  .footer {{ margin-top:2rem; font-size:0.75rem; color:#94a3b8; text-align:center; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>DecisionDrift Report — {cmd}</h1>
    <div class="status" style="background:{status_color}">{status_label}</div>
  </header>
  <div class="meta">
    <span>Version: {envelope.tool_version}</span>
    <span>Timestamp: {envelope.timestamp}</span>
    {f"<span>Duration: {envelope.duration_ms}ms</span>" if envelope.duration_ms else ""}
  </div>
  {"<h2>Findings</h2><table><thead><tr><th>Action</th><th>ADR</th><th>Type</th><th>Description</th><th>File</th></tr></thead><tbody>" + rows + "</tbody></table>" if findings else '<div class="empty"><p>No findings.</p></div>'}
  {f"<h2>Summary</h2><table><tbody>{summary_rows}</tbody></table>" if summary_rows else ""}
  <div class="footer">Generated by DecisionDrift v{envelope.tool_version}</div>
</div>
</body>
</html>"""
