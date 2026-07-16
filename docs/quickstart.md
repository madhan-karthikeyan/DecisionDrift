# Quickstart

## Install

```bash
pip install decisiondrift
```

Verify it works:

```bash
decisiondrift --help
```

## Quick Setup (one command)

```bash
cd my-project
decisiondrift init .
```

This runs bootstrap, prompts approve/reject per ADR, installs pre-commit hook,
generates `decisiondrift.yml`, and optionally creates a GitHub Actions CI workflow.

## Manual Setup

### 1. Bootstrap ADRs from your repository

```bash
# Scan and propose candidate ADRs (dry-run by default)
decisiondrift bootstrap .

# See what was generated
decisiondrift adr list --status proposed

# Approve the ones that reflect real team decisions
decisiondrift adr approve ADR-0001
decisiondrift adr approve ADR-0002
```

### 2. Enforce rules (deterministic, no LLM needed)

```bash
# Check unstaged changes against accepted ADRs
decisiondrift enforce --from-git

# Full repository scan
decisiondrift enforce .

# Fail CI on any rule violation
decisiondrift enforce --from-git --fail-on warn

# JSON output for CI/tooling
decisiondrift enforce . --format json --output report.json

# SARIF output for GitHub code scanning
decisiondrift enforce . --format sarif --output results.sarif
```

Example output when a violation is detected:

```
[BLOCK] ADR-0001: Use Flask as Web Framework
        Match: fastapi
        File: requirements.txt
        Action: Remove dependency or propose ADR change
```

### 3. Audit ADR health

```bash
decisiondrift audit
```

Reports: expired/stale ADRs, drift (rules violated by current code), coverage gaps, and quality scores.

### 4. Manage ADR lifecycle

```bash
# Interactive review of bootstrap candidates
decisiondrift adr review .

# View ADR details
decisiondrift adr show ADR-0001

# Reject a proposed ADR
decisiondrift adr reject ADR-0003 --reason "Not applicable to our stack"

# Deprecate an outdated ADR
decisiondrift adr deprecate ADR-0002 --reason "Superseded by newer approach"

# Supersede an ADR with a new one
decisiondrift adr supersede ADR-0001 "Use FastAPI for HTTP APIs"

# Edit an ADR directly
decisiondrift adr edit ADR-0001

# View git history for an ADR
decisiondrift adr history ADR-0001
```

### 5. Install pre-commit hook

```bash
decisiondrift guard --install
```

Runs `decisiondrift enforce --from-git` before every commit.

### 6. LLM-based review (optional)

```bash
export DECISIONDRIFT_LLM_API_KEY=sk-...
decisiondrift review --from-git
```

Without an API key, `review` tells you to use `enforce` instead.

## Custom Rules

Define additional rules in `decisiondrift.yml` — no ADR needed:

```yaml
rules:
  - match: deprecated-library
    type: dependency
    action: block
    description: "Block deprecated library"
  - match: old_module
    type: import
    action: warn
    description: "Warn on imports from old_module"
```

## Multi-language Support

Install Tree-sitter extras for import and API call scanning in JS/TS/Go/Java/Rust:

```bash
pip install decisiondrift[ast]
```

Without this extra, dependency, path, and config rules work for all languages; import and API rules work for Python only.

## What's next?

- [CLI Reference](cli-reference.md) — full command reference
- [Architecture & Design](plan.md) — how DecisionDrift works
- [Evaluation Results](evaluation.md) — retrieval accuracy benchmarks
