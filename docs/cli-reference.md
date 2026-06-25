# CLI Reference

## Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit |

## Commands

### `decisiondrift bootstrap <path>`

Generate candidate ADRs from repository structure.

| Flag | Default | Description |
|------|---------|-------------|
| `--dry-run` | `true` | Preview candidates without writing |
| `--apply` | `false` | Write candidates to `--adr-dir` |
| `--min-confidence` | `0.3` | Minimum confidence threshold (0.0–1.0) |
| `--adr-dir` | `docs/adr` | ADR output directory |
| `--max-candidates` | `20` | Maximum candidates to generate |

**Exit codes:** `0` on success, `1` on error.

### `decisiondrift enforce [diff]`

Enforce ADR rules against a diff or full repository. **No LLM required.**

| Flag | Default | Description |
|------|---------|-------------|
| `--from-git` | `false` | Read diff from `git diff` |
| `--repo` | `.` | Repository root |
| `--adr-dir` | `docs/adr` | ADR directory |
| `--fail-on` | `block` | Minimum severity for non-zero exit (`block`, `require_approval`, `warn`, `info`) |

**Exit codes:** `0` on no violations, `1` on violations at or above `--fail-on` level.

### `decisiondrift review [diff]`

LLM-based semantic violation classification.

| Flag | Default | Description |
|------|---------|-------------|
| `--from-git` | `false` | Read diff from `git diff` |
| `--repo` | `.` | Repository root |
| `--adr-dir` | `docs/adr` | ADR directory |
| `--llm-api-key` | `env` | LLM API key |
| `--llm-model` | `gpt-4o` | LLM model |
| `--llm-base-url` | — | Custom API base URL |
| `--max-pairs` | `15` | Max (ADR, symbol) pairs to classify |
| `--similarity-threshold` | `0.5` | Minimum similarity for ADR consideration |
| `--timeout` | `300` | Max wall-clock time in seconds |

**Exit codes:** `0` on no violations, `1` on violations found.

Without an LLM API key, prints a message recommending `enforce`.

### `decisiondrift audit`

ADR health audit.

| Flag | Default | Description |
|------|---------|-------------|
| `--adr-dir` | `docs/adr` | ADR directory |

Reports: expired/stale ADRs, drift from current code, coverage gaps, quality scores.

**Exit codes:** `0` on healthy, `1` if any stale/expired/drift/proposed ADRs found.

### `decisiondrift impact [diff]`

Analyze diff for impacted symbols (AST-based diagnostic).

| Flag | Default | Description |
|------|---------|-------------|
| `--from-git` | `false` | Read diff from `git diff` |
| `--repo` | `.` | Repository root |

### `decisiondrift ingest <file>`

Extract candidate ADRs from free-text notes (LLM required).

| Flag | Default | Description |
|------|---------|-------------|
| `--adr-dir` | `docs/adr` | ADR output directory |

### `decisiondrift adr`

Manage ADRs.

| Subcommand | Description |
|------------|-------------|
| `list` | List ADRs (`--status` to filter by status, `--source` to filter by source) |
| `approve ADR-XXXX` | Approve a proposed ADR |
| `reject ADR-XXXX` | Reject a proposed ADR |

**Exit codes (`list`):** `0` if ADRs found, `1` if empty.

### `decisiondrift guard`

Pre-commit hook runner.

| Flag | Description |
|------|-------------|
| `--install` | Install the pre-commit hook |
| `--uninstall` | Remove the pre-commit hook |

Runs `decisiondrift enforce --from-git` when triggered by git.

## Exit Code Summary

| Code | Scenario |
|------|----------|
| `0` | Success / no violations |
| `1` | Violations detected / stale ADRs / error |
