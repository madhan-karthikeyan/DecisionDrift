# DecisionDrift — Product Plan

**Decision Governance Platform.** Enforce every engineering decision your team has ever made — without needing an LLM for everything.

---

## 1. Product Identity

**One sentence:** Enforce every engineering decision your team has ever made — deterministically, at every stage of development.

Not "Institutional Memory Platform" (too broad). Not "ADR Tool" (too narrow).

**Decision Governance Platform for Software Teams.**

Core loop:

```
Decisions → Rules → Enforcement → Drift Detection
```

---

## 2. What's Built

### Shipped (as of v1.0.0-beta)

| Component | Status | Description |
|-----------|--------|-------------|
| Bootstrap V3 | ✅ | Deterministic repository scanning, evidence collection, technology detection, governance candidate generation, enforceability analysis |
| Rule Engine | ✅ | 5 rule types (dependency, import, API, path, config), deterministic, zero LLM cost |
| Enforcement | ✅ | Diff-based and full-repo modes, confidence-based severity downgrade, exit-code gating |
| Audit | ✅ | ADR health: drift detection, stale/expired ADRs, quality scores, coverage analysis |
| ADR Lifecycle | ✅ | `adr list/approve/reject`, supersession resolution, dependency tracking |
| Decision Capture | ✅ | `ingest` — free-text to ADR candidates (requires LLM key) |
| Review | ✅ | LLM-based semantic violation classification (requires LLM key) |
| Guard | ✅ | Pre-commit hook with deterministic enforcement |
| Impact | ✅ | Diff parsing, AST extraction, symbol analysis |
| GitHub Action | ✅ | Full CI integration with deterministic + LLM paths |
| 310 tests | ✅ | Unit, integration, snapshot — passing |

### Architecture (current)

```
src/decisiondrift/
  cli.py                     # CLI entrypoint (Click)
  config.py                  # Config loader (YAML + .env)
  models/schema.py           # Pydantic models (DecisionRecord, ReviewResult, etc.)
  adr/                       # ADR loader, parser, writer, supersession, id allocator, dedup
  adr_manager/               # adr list/approve/reject commands
  bootstrap/                 # V3 pipeline: evidence → technology candidates → governance → enforceability → ADR suggestions
  rules/                     # Deterministic rule engine (scanner, engine, models)
  classification/            # LLM classifier
  review/                    # Orchestrator pipeline (diff → retrieval → classification → report)
  report/                    # Output formatters (text, GitHub comment)
  impact/                    # Diff parser + AST extraction (Python + Tree-sitter)
  ingest/                    # Free-text → ADR pipeline (segmentation → LLM extraction → dedup → write)
  retrieval/                 # Keyword-based ADR retrieval
  github/                    # GitHub Action adapter, client, comment manager
  llm/                       # LLM client abstraction (OpenAI, Groq, Ollama)
  utils/                     # Shared utilities (dependency_parser)
```

---

## 3. CLI Reference

| Command | Description | LLM Required |
|---------|-------------|-------------|
| `bootstrap <path>` | Generate ADR candidates from repo structure (V3 deterministic) | No |
| `enforce [diff]` | Enforce ADR rules against diff or full repo | No |
| `audit` | ADR health: drift, stale/expired, quality, coverage | No |
| `guard [--install]` | Pre-commit hook runner | No |
| `impact [diff]` | Analyze diff for impacted symbols | No |
| `review [diff]` | LLM semantic violation classification | Yes |
| `ingest <file>` | Extract ADR candidates from free-text notes | Yes |
| `adr list` | List ADRs (filter by status, source) | No |
| `adr approve <id>` | Approve a proposed ADR | No |
| `adr reject <id>` | Reject a proposed ADR | No |

---

## 4. Rule Engine

### Rule Types

| Type | What It Scans | Method |
|------|--------------|--------|
| `dependency` | requirements.txt, pyproject.toml, go.mod, package.json, Cargo.toml | File parsing |
| `import` | Python import statements | AST scanning |
| `api` | Function/method calls in Python files | AST pattern matching |
| `path` | File paths and directory structure | Regex matching |
| `config` | Config file keys/values (.yml, .toml, .ini, .json, .cfg, .env) | Pattern matching |

### Actions

| Action | Meaning | Exit Code |
|--------|---------|-----------|
| `block` | Merge prevented | 1 |
| `require_approval` | Senior review mandated | 1 |
| `warn` | Advisory | 1 (if `--fail-on warn`) |
| `info` | Informational | 0 |

### Confidence-Based Downgrade

Rules inherit confidence from their source ADR:

| Source | Default Confidence | Enforcement |
|--------|-------------------|-------------|
| `manual` | HIGH | Full enforcement |
| `bootstrap` | Evidence-level dependent | See below |
| `ingest` | LOW | Informational only |

At enforcement time:
- **HIGH**: rules apply at original severity
- **MEDIUM**: BLOCK → WARN, REQUIRE_APPROVAL → WARN
- **LOW**: all rules → INFO

---

## 5. Bootstrap V3 Pipeline (Deterministic)

```
Evidence (dependency, import, file, directory, config, entrypoint)
    ↓
Technology Candidates (role, evidence level, contradictions, suppression)
    ↓
Repository Model (role, subtype, technologies, governance candidates)
    ↓
Governance Decision Candidates (title, decision type, scope, evidence)
    ↓
Enforceability Analysis (proposed rules, enforceable? reason)
    ↓
ADR Suggestions (ADR with prohibitions + rules)
```

**Key properties:**
- Zero LLM calls
- Evidence-level based confidence (WEAK → LOW, MODERATE → MEDIUM, STRONG → HIGH)
- `--min-confidence` filter (low/medium/high)
- Framework/product repos suppress consumer implementation ADRs
- Library repos suppress data-access integration ADRs
- Frontend ADRs require component scope (frontend/, ui/, web/, client/, app/)

---

## 6. ADR Lifecycle

| Status | Set by | Enforced? |
|--------|--------|-----------|
| `proposed` | Bootstrap, Ingest, or manual draft | No |
| `accepted` | `adr approve` (human) | Yes |
| `rejected` | `adr reject` (human) | No (kept for dedup) |
| `deprecated` | Manual edit | No |
| `superseded` | Manual edit with `superseded_by` | No |

Only `accepted` ADRs participate in enforcement. Generated candidates can never silently block a PR.

---

## 7. ADR Schema

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | `ADR-XXXX` |
| `title` | Yes | Human-readable title |
| `status` | Yes | proposed / accepted / rejected / deprecated / superseded |
| `severity` | Yes | critical / high / medium / low |
| `source` | No | manual / bootstrap / ingest |
| `type` | No | dependency / architecture / tooling / workflow |
| `prohibitions` | No | Auto-generates dependency + import rules |
| `rationale` | No | Why this decision exists |
| `exceptions` | No | When this ADR doesn't apply |
| `alternatives_rejected` | No | What was considered and rejected |
| `keywords` | No | Search terms for retrieval |
| `owner` | No | Team or person responsible |
| `review_after` | No | Date for next review |
| `expires_after` | No | Date after which ADR is invalid |
| `depends_on` | No | ADR-XXXX this depends on |
| `supersedes` | No | ADR-XXXX this replaces |

---

## 8. Exit Codes

| Command | Exit 0 | Exit 1 |
|---------|--------|--------|
| `bootstrap` | Success (even if no ADRs generated) | Error during scanning |
| `enforce` | No violations above threshold | Violations found at or above `--fail-on` level |
| `audit` | No expired, stale, drifted, or unreviewed ADRs | Issues found |
| `review` | No violations or LLM unavailable | Violations detected |
| `adr list` | ADRs found | No ADRs match filter |
| `adr approve/reject` | Success | ADR not found |
| `ingest` | Success | Error |
| `guard` | No violations | Violations found |

---

## 9. What NOT to Build

| Feature | Reason |
|---------|--------|
| SaaS / hosted mode | V1 is local CLI + GitHub Action. No proven demand. |
| Postgres / pgvector | ADR corpus is small; in-memory is sub-second. |
| Dashboard / UI | CLI output + GitHub comments are sufficient for V1. |
| Multi-repo governance | No proven demand. |
| Test generation | Deliberately deferred to keep the product tightly focused on architecture governance, not QA automation. |
| LangGraph / agentic workflows | Linear pipeline is sufficient. |
| Custom security scanner | Existing tools are mature. Integrate, don't build. |
| LLM bootstrap synthesis | Deterministic V3 is more reliable and cheaper. |
| Embeddings / hybrid retrieval | Keyword retrieval achieves 95.2% Recall@5 on evaluation set. |

---

## 10. What to Build After Validation

Assuming real-user feedback confirms demand:

1. **VS Code extension** — inline governance feedback as you code
2. **GitHub Action improvements** — richer output, better onboarding
3. **Claude Code / Cursor hook** — decision-aware AI coding
4. **Decision graph visualization** — ADR relationships as a navigable graph
5. **Better onboarding** — guided first-run experience
6. **Embedding fallback** — for repos where keyword retrieval misses context

---

## 11. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Keyword-only retrieval | May miss ADRs when terms don't match | Embedding-based fallback in extras |
| Python-focused AST | Non-Python enforcement limited to dep/path/config rules | Tree-sitter in `[ast]` extras |
| Call-graph soundness | AST performs localized syntax matching, not deep dataflow/alias tracking | LLM semantic review provides deeper analysis |
| Bootstrap is heuristic | Directory detection ≠ architectural understanding | Human approval gate |
| LLM required for review | Semantic classification not available without API key | Use `enforce` instead |
