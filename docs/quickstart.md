# Quickstart

## Install

```bash
pip install decisiondrift
```

Verify it works:

```bash
decisiondrift --help
```

## 1. Bootstrap ADRs from your repository

```bash
cd my-project

# Scan and propose candidate ADRs (dry-run by default)
decisiondrift bootstrap .

# See what was generated
decisiondrift adr list --status proposed

# Approve the ones that reflect real team decisions
decisiondrift adr approve ADR-0001
decisiondrift adr approve ADR-0002
```

## 2. Enforce rules (deterministic, no LLM needed)

```bash
# Check unstaged changes against accepted ADRs
decisiondrift enforce --from-git

# Full repository scan
decisiondrift enforce .

# Fail CI on any rule violation
decisiondrift enforce --from-git --fail-on warn
```

Example output when a violation is detected:

```
[BLOCK] ADR-0001: Use Flask as Web Framework
        Match: fastapi
        File: requirements.txt
        Action: Remove dependency or propose ADR change
```

## 3. Audit ADR health

```bash
decisiondrift audit
```

Reports: expired/stale ADRs, drift (rules violated by current code), coverage gaps, and quality scores.

## 4. Install pre-commit hook

```bash
decisiondrift guard --install
```

Runs `decisiondrift enforce --from-git` before every commit.

## 5. LLM-based review (optional)

```bash
export DECISIONDRIFT_LLM_API_KEY=sk-...
decisiondrift review --from-git
```

Without an API key, `review` tells you to use `enforce` instead.

## What's next?

- [CLI Reference](cli-reference.md) — full command reference
- [Architecture & Design](plan.md) — how DecisionDrift works
- [Evaluation Results](evaluation.md) — retrieval accuracy benchmarks
