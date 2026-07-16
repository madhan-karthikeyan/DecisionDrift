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
| `--min-confidence` | `low` | Minimum confidence level (`low`, `medium`, `high`) |
| `--max-candidates` | — | Maximum number of candidate ADRs to generate |
| `--adr-dir` | `docs/adr` | ADR output directory |

**Exit codes:** `0` on success, `1` on error.

### `decisiondrift enforce [diff]`

Enforce ADR rules against a diff or full repository. **No LLM required.**

| Flag | Default | Description |
|------|---------|-------------|
| `--from-git` | `false` | Read diff from `git diff` (working tree changes) |
| `--staged` | `false` | Read diff from `git diff --cached` (staged changes) |
| `--repo` | `.` | Repository root |
| `--adr-dir` | `docs/adr` | ADR directory |
| `--fail-on` | `block` | Minimum severity for non-zero exit (`block`, `require_approval`, `warn`, `info`) |

**Exit codes:** `0` on no violations, `1` on violations at or above `--fail-on` level.

### `decisiondrift review [diff]`

LLM-based semantic violation classification.

| Flag | Default | Description |
|------|---------|-------------|
| `--from-git` | `false` | Read diff from `git diff` (working tree) |
| `--staged` | `false` | Read diff from `git diff --cached` (staged) |
| `--repo` | `.` | Repository root |
| `--adr-dir` | `docs/adr` | ADR directory |
| `--llm-api-key` | `env/DECISIONDRIFT_LLM_API_KEY` | LLM API key (overrides config and env) |
| `--llm-model` | `gpt-4o` | LLM model (overrides config and env) |
| `--llm-base-url` | — | Custom API base URL (overrides config and env) |
| `--max-pairs` | `15` | Max (ADR, symbol) pairs to classify |
| `--similarity-threshold` | `0.5` | Minimum similarity for ADR consideration |
| `--timeout` | `300` | Max wall-clock time in seconds |

**Precedence:** CLI flags > Environment variables > Config file > Defaults

**Exit codes:** `0` on no violations, `1` on violations found.

Without an LLM API key, displays a message recommending `decisiondrift enforce --from-git`.

### `decisiondrift audit`

ADR health audit.

| Flag | Default | Description |
|------|---------|-------------|
| `--repo` | `.` | Repository root |
| `--adr-dir` | `<repo>/docs/adr` | ADR directory |

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
| `show ADR-XXXX` | Show full details of a single ADR |
| `approve ADR-XXXX` | Approve a proposed ADR |
| `reject ADR-XXXX` | Reject a proposed ADR |

**Exit codes (`list`):** `0` if ADRs found, `1` if empty.

### `decisiondrift guard`

Pre-commit hook runner.

| Flag | Description |
|------|-------------|
| `--install` | Install the pre-commit hook (uses `git diff --cached`) |
| `--uninstall` | Remove the pre-commit hook |

Runs `decisiondrift enforce --staged` when triggered by git (analyzes staged changes only).

## Exit Code Summary

| Code | Scenario |
|------|----------|
| `0` | Success / no violations |
| `1` | Violations detected / stale ADRs / error |
