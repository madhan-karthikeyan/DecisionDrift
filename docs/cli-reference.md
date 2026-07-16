# CLI Reference

## Global Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit |

## Commands

### `decisiondrift bootstrap <path>`

Generate candidate ADRs from repository structure. Deterministic by default;
with `--llm`, recognizes unknown technologies and generates ADR templates via LLM.

| Flag | Default | Description |
|------|---------|-------------|
| `--dry-run` | `true` | Preview candidates without writing |
| `--apply` | `false` | Write candidates to `--adr-dir` |
| `--min-confidence` | `low` | Minimum confidence level (`low`, `medium`, `high`) |
| `--max-candidates` | — | Maximum number of candidate ADRs to generate |
| `--adr-dir` | `docs/adr` | ADR output directory |
| `--llm` | `false` | Enable LLM technology recognition for unknown dependencies |
| `--llm-api-key` | `env/DECISIONDRIFT_LLM_API_KEY` | LLM API key |
| `--llm-model` | `gpt-4o` | LLM model name |
| `--llm-base-url` | — | Custom API base URL (for Ollama, Groq, etc.) |
| `--min-llm-confidence` | `0.6` | Minimum confidence threshold for LLM results (0.0–1.0) |
| `--cache-templates` | `false` | Cache LLM-generated ADR templates (opt-in, tech recognition always cached) |
| `--registry-url` | — | URL to shared technology registry YAML (can be specified multiple times) |

**Layered knowledge precedence:** Remote HTTP registries > Project cache (`.decisiondrift/cache.yaml`) > Global cache (`~/.config/decisiondrift/cache.yaml`) > Bundled registry (`default_registry.yaml`) > LLM fallback

**Exit codes:** `0` on success, `1` on error.

### `decisiondrift enforce [diff]`

Enforce ADR rules against a diff or full repository. **No LLM required.**

Scans 5 rule types: dependency (12 file formats), import (Python AST + Tree-sitter for 12 languages), API calls (same multi-language), path (regex), config (key-value). Also loads custom rules from `decisiondrift.yml` `rules:` section.

| Flag | Default | Description |
|------|---------|-------------|
| `--from-git` | `false` | Read diff from `git diff` (working tree changes) |
| `--staged` | `false` | Read diff from `git diff --cached` (staged changes) |
| `--repo` | `.` | Repository root |
| `--adr-dir` | `docs/adr` | ADR directory |
| `--fail-on` | `block` | Minimum severity for non-zero exit (`block`, `require_approval`, `warn`, `info`) |
| `--format` | `text` | Output format (`text`, `json`, `sarif`, `markdown`, `html`) |
| `--output` | — | Write output to file instead of stdout |

**Output formats:**
- `text`: Human-readable console output (default)
- `json`: Structured JSON via `ReportEnvelope`
- `sarif`: SARIF v2.1.0 for GitHub code scanning integration
- `markdown`: Rendered markdown report
- `html`: Self-contained static HTML page (inline CSS)

**Exit codes:** `0` on no violations, `1` on violations at or above `--fail-on` level.

### `decisiondrift init [path]`

Initialize a repository for governance. Runs bootstrap, interactively approves/rejects candidates, installs pre-commit hook, generates `decisiondrift.yml`, and optionally generates CI workflow.

| Flag | Default | Description |
|------|---------|-------------|
| `--yes` | `false` | Non-interactive mode (auto-approve all) |
| `--template` | — | ADR template to use |
| `--with-ci` | `false` | Also generate `.github/workflows/decisiondrift.yml` |

**Exit codes:** `0` on success, `1` on error.

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

Manage ADRs and their lifecycle.

| Subcommand | Description |
|------------|-------------|
| `review [path]` | Run bootstrap + interactively approve/reject each candidate |
| `list` | List ADRs (`--status` to filter, `--source` to filter) |
| `show ADR-XXXX` | Show full details of a single ADR |
| `approve ADR-XXXX` | Approve a proposed ADR (status → accepted) |
| `reject ADR-XXXX` | Reject a proposed ADR (status → rejected) |
| `deprecate ADR-XXXX` | Deprecate an ADR (status → deprecated) |
| `archive ADR-XXXX` | Alias for deprecate |
| `supersede ADR-XXXX <title>` | Supersede an ADR: marks old as superseded, creates new proposed ADR |
| `edit ADR-XXXX` | Open ADR in `$EDITOR` for editing |
| `history ADR-XXXX` | Show `git log --follow` for the ADR file |

**Exit codes (`list`):** `0` if ADRs found, `1` if empty.
**Exit codes (`review`):** `0` if at least one ADR approved, `1` if none approved.

### `decisiondrift guard`

Pre-commit hook runner.

| Flag | Description |
|------|-------------|
| `--install` | Install the pre-commit hook (uses `git diff --cached`) |
| `--uninstall` | Remove the pre-commit hook |

Runs `decisiondrift enforce --staged` when triggered by git (analyzes staged changes only).

## Configuration (`decisiondrift.yml`)

Auto-discovered from the current directory. Supports custom rule packs:

```yaml
llm:
  api_key: null       # Set DECISIONDRIFT_LLM_API_KEY or configure here
  model: gpt-4o
  base_url: null      # Use for Ollama, Groq, etc.

adr_dir: docs/adr

# Shared HTTP registry URLs (optional)
# Technology definitions fetched from these URLs are merged into the registry.
registry_urls:
  - https://example.com/team-registry.yaml

# Embedding model for semantic retrieval fallback (requires `pip install decisiondrift[embeddings]`)
embedding_model: BAAI/bge-small-en-v1.5

# Custom rule packs — additional rules beyond ADR-derived ones.
# Types: dependency, import, path, api, config
# Actions: block, require_approval, warn, info
rules:
  - match: deprecated-library
    type: dependency
    action: block
    description: "Block deprecated library"
```

## Exit Code Summary

| Command | Exit 0 | Exit 1 |
|---------|--------|--------|
| `bootstrap` | Success | Error |
| `enforce` | No violations above threshold | Violations found |
| `audit` | Healthy | Stale/expired/drift found |
| `review` | No violations | Violations detected |
| `adr list` | ADRs found | No ADRs match filter |
| `adr approve/reject` | Success | ADR not found |
| `adr deprecate/supersede` | Success | ADR not found or invalid state |
| `adr review` | At least one approved | None approved |
| `ingest` | Success | Error |
| `guard` | No violations | Violations found |
