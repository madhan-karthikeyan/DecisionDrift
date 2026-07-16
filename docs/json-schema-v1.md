# JSON Schema — `ReportEnvelope` (v1)

Every JSON-formatted output from DecisionDrift uses the `ReportEnvelope` schema below.

## Schema version

The `schema_version` field indicates the schema revision. It increments only on **breaking changes**.

| Version | Notes |
|---------|-------|
| `1` | Initial stable schema |

Consumers should assert `schema_version == 1` to confirm compatibility.

## Structure

```json
{
  "schema_version": 1,
  "command": "enforce",
  "tool_version": "1.1.0",
  "timestamp": "2026-07-16T12:34:56.789000+00:00",
  "duration_ms": 142,
  "summary": {
    "status": "violations",
    "findings_count": 1,
    "rules_evaluated": 5,
    "files_scanned": 10,
    "exit_code": 0
  },
  "findings": [
    {
      "adr_id": "ADR-0001",
      "adr_title": "Use Flask",
      "rule_id": "no-django",
      "rule_type": "import",
      "action": "block",
      "severity": "high",
      "match_value": "django",
      "file_path": "src/app/views.py",
      "description": "Django import detected but ADR mandates Flask"
    }
  ],
  "metadata": {
    "repo": ".",
    "adr_dir": "/path/to/docs/adr",
    "diff_mode": true,
    "fail_on": "block"
  }
}
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `int` | Yes | Schema revision (`1` = current) |
| `command` | `string` | Yes | CLI command that generated this report (`enforce`, `audit`, `bootstrap`, `init`) |
| `tool_version` | `string` | Yes | DecisionDrift semver (e.g. `1.1.0`) |
| `timestamp` | `string` | Yes | ISO-8601 UTC timestamp |
| `duration_ms` | `int` | Yes | Wall-clock execution time in milliseconds |
| `summary` | `object` | Yes | Aggregate counts and exit status |
| `findings` | `array` | Yes | List of individual finding objects |
| `metadata` | `object` | Yes | Command-specific context |

### `summary` fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | `"ok"`, `"violations"`, or `"error"` |
| `findings_count` | `int` | Number of findings |
| `rules_evaluated` | `int` | Number of rules checked |
| `files_scanned` | `int` | Number of files inspected |
| `exit_code` | `int` | Process exit code (0 = success) |

### `findings[]` fields

| Field | Type | Description |
|-------|------|-------------|
| `adr_id` | `string` | ADR identifier (e.g. `ADR-0001`) |
| `adr_title` | `string` | ADR title |
| `rule_id` | `string` | Rule identifier |
| `rule_type` | `string` | `"dependency"`, `"import"`, `"path"`, `"api"`, `"config"` |
| `action` | `string` | `"block"`, `"warn"`, `"require_approval"`, `"info"` |
| `severity` | `string` | `"critical"`, `"high"`, `"medium"`, `"low"` |
| `match_value` | `string` | The value that triggered the rule |
| `file_path` | `string` | File where the violation was found |
| `description` | `string` | Human-readable explanation |
