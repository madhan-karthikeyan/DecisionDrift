# DecisionDrift

**Decision-aware AI PR review.** Detects when a pull request violates documented architecture decisions — before the code is merged.

```
Repository ADRs (docs/adr/)
         │
    PR opened ──► DecisionDrift ──► PR comment with findings
                      │
                 classifies diff
                 against accepted
                 architecture decisions
```

## How It Works

1. **You document decisions** as ADRs (Architecture Decision Records) in `docs/adr/`
2. **DecisionDrift reads your ADRs** and understands what rules exist
3. **On every PR**, it parses the diff, extracts changed symbols via AST, retrieves relevant ADRs by keyword overlap, and classifies each pair via LLM
4. **Results posted** as a PR comment — violations, non-violations, and confidence levels

### Example Violation

Given this ADR:
```yaml
id: ADR-0001
title: Use Flask Framework
status: accepted
rationale: All web endpoints must use the Flask framework
```

And this PR diff:
```python
-from http.server import HTTPServer  # ❌ violates ADR-0001
+from flask import Flask             # ✅ complies
```

DecisionDrift flags the left change as a **violation**.

---

## Quickstart

### 1. Install

```bash
pip install decisiondrift
```

Or from source:
```bash
git clone https://github.com/yourorg/decisiondrift
cd decisiondrift
pip install -e .
```

### 2. Bootstrap ADRs from your repo structure

```bash
# Scan the repo and propose candidate ADRs (dry-run by default)
decisiondrift bootstrap .

# Review what was generated
decisiondrift adr list --status proposed

# Approve the ones that reflect real team decisions
decisiondrift adr approve ADR-0001
```

### 3. Run a review on a PR diff

```bash
# From a local git diff
decisiondrift review --from-git

# From a diff file
decisiondrift review path/to/pr.diff
```

### 4. Enable in CI

Add `.github/workflows/decisiondrift.yml`:

```yaml
name: DecisionDrift
on: pull_request
permissions:
  pull-requests: write
  contents: read
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: yourorg/decisiondrift@v1
        with:
          llm-api-key: ${{ secrets.DECISIONDRIFT_LLM_KEY }}
```

---

## LLM Configuration

DecisionDrift needs an LLM to classify diff-ADR pairs. Set via environment variables or `decisiondrift.yml`:

### OpenAI / Groq / OpenRouter

```env
DECISIONDRIFT_LLM_API_KEY=sk-...
DECISIONDRIFT_LLM_MODEL=gpt-4o
DECISIONDRIFT_LLM_BASE_URL=https://api.openai.com/v1
```

### Local Ollama (free, private)

```env
DECISIONDRIFT_LLM_API_KEY=ollama
DECISIONDRIFT_LLM_MODEL=qwen2.5-coder:7b
DECISIONDRIFT_LLM_BASE_URL=http://localhost:11434/v1
```

```bash
ollama pull qwen2.5-coder:7b
```

Without an API key, classification falls back to `needs_human_review` — retrieval still works.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `decisiondrift bootstrap .` | Generate candidate ADRs from repo structure |
| `decisiondrift adr list` | List ADRs (filter by `--status`, `--source`) |
| `decisiondrift adr approve ADR-XXXX` | Approve a proposed ADR |
| `decisiondrift adr reject ADR-XXXX --reason "..."` | Reject a proposed ADR |
| `decisiondrift review --from-git` | Evaluate local diff against accepted ADRs |
| `decisiondrift review diff.patch` | Same, from a patch file |
| `decisiondrift impact --from-git` | Analyze diff for impacted symbols (diagnostic) |

---

## ADR Lifecycle

| Status | Meaning | Enforced? |
|--------|---------|-----------|
| `proposed` | Generated but unreviewed | No |
| `accepted` | Approved by a maintainer | **Yes** |
| `rejected` | Declined; kept for dedup | No |
| `deprecated` | No longer valid | No |
| `superseded` | Replaced by a newer ADR | No |

Only `accepted` ADRs participate in PR review. This ensures generated candidates can never silently block a PR.

---

## Evaluation

| Metric | Score |
|--------|-------|
| Retrieval Recall@5 | **95.2%** (20/21 patches) |
| Retrieval Recall@1 | **85.7%** (18/21 patches) |
| Classification | Requires LLM API key; see `docs/evaluation.md` |

Tested against 21 labeled patches (13 violations, 8 non-violations) across 12 architecture decisions.

---

## Project Structure

```
src/decisiondrift/
  cli.py                     # CLI entrypoint
  config.py                  # Config loader (YAML + .env)
  models/schema.py           # Pydantic models
  adr/                       # ADR loader, parser, writer, supersession
  adr_manager/               # adr list/approve/reject commands
  bootstrap/                 # Structure scanner + candidate generation
  classification/            # LLM classifier
  github/                    # GitHub Action adapter
  impact/                    # Diff parser + AST extraction
  ingest/                    # Free-text → ADR pipeline (WIP)
  report/                    # Text + GitHub comment formatters
  retrieval/                 # Keyword-based ADR retrieval
  review/                    # Orchestrator pipeline
```

---

## Limitations

- **Python-only AST analysis.** Non-Python files produce no symbols (tree-sitter support planned).
- **Keyword-only retrieval.** May miss ADRs when symbol/file-path terms don't match (embedding-based hybrid retrieval planned).
- **Ollama CPU-bound on large models.** ~17s/pair with qwen2.5-coder:7b; use Groq/OpenAI for ~1s latency.
- **Bootstrap is heuristic.** Directory-naming detection is not architectural understanding — generated ADRs require human approval.

---

## Development

```bash
pip install -e ".[embeddings]"
python -m pytest tests/ -k "not Classification"
```

See `docs/plan.md` for the full design document and `docs/progress.md` for current status.
