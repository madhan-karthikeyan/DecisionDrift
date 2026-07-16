# DecisionDrift — Progress & Execution Plan

Last updated: 2026-07-16

## Current Stage

```
Feature Complete
    ↓
v1.0 Release Candidate ← YOU ARE HERE
    ↓
Beta Validation
    ↓
v1.0 Release
```

---

## What's Been Completed

### Core Features
- ✅ **Bootstrap V3** — fully deterministic repository scanning, evidence collection, technology detection, governance candidate generation, enforceability analysis, ADR proposal (37 techs, 25 templates)
- ✅ **Decision Capture (Ingest)** — free-text to ADR candidates via LLM extraction
- ✅ **ADR Lifecycle** — complete: `list/show/approve/reject/deprecate/archive/supersede/edit/history/review`
- ✅ **Rule Engine** — 5 rule types (dependency, import, API, path, config), deterministic, confidence-based severity downgrade
- ✅ **Multi-language Import/API Scanning** — Tree-sitter for JS/TS/Go/Java/Rust imports + API calls (`pip install decisiondrift[ast]`)
- ✅ **Custom Rule Packs** — `decisiondrift.yml` `rules:` section, merged with ADR-derived rules during enforcement
- ✅ **Enforcement** — diff-based and full-repo modes, `--fail-on` gating, CI-ready exit codes
- ✅ **Output Formats** — `--format text/json/sarif/markdown` + `--output <file>` on enforce command
- ✅ **Audit** — ADR quality scoring, drift detection, stale/expired ADRs, coverage analysis
- ✅ **Impact Analysis** — diff parsing, AST extraction (Python native + Tree-sitter multi-language)
- ✅ **LLM Review** — semantic violation classification with confidence-gated fallback
- ✅ **`init` Command** — one-command project setup: bootstrap → approve → hook → config → GitHub CI
- ✅ **GitHub Action** — SARIF output, commit status checks, formal PR review (comment/request-changes/auto)

### Engineering (Hardening & v1.0 Release)
- ✅ **Shell injection fix** in `guard --install`
- ✅ **Symlink traversal protection** in Bootstrap V3 scanner
- ✅ **All 5 rule types** in `_enforce_repo` — was only checking dependency+import
- ✅ **`apply_suggestions` bug fix** — `exclude_none=True` for Pydantic v2
- ✅ **`min_confidence` threading** through Bootstrap V3 pipeline
- ✅ **No-LLM review output** — clear message suggesting `decisiondrift enforce`
- ✅ **Standardized CLI exit codes** — audit/review/adr list/bootstrap all return meaningful codes
- ✅ **V2 dead code removal** — audit coverage now uses V3 `build_repository_model`
- ✅ **Dependency parsing consolidation** — shared `utils/dependency_parser.py` used by both rule engine and bootstrap
- ✅ **Dead imports and missing modules** — fixed `v3.py` importing 3 non-existent modules
- ✅ **363 tests passing** (26 skipped for tree-sitter — requires `pip install decisiondrift[ast]`)

---

## Execution Plan

### ✅ Phase A: Release Engineering (Complete)

| Step | Detail | Status |
|------|--------|--------|
| A1 | GitHub Actions CI (lint, format, all tests, coverage, package build) | ✅ |
| A2 | PyPI packaging: verify `pip install decisiondrift` and `pipx install decisiondrift` | ✅ |
| A3 | Tag `v1.0.0-beta.1` | ✅ |
| A4 | Release notes with changelog | ✅ `RELEASE_NOTES.md` |
| A5 | `action.yml` polish (input validation, branding) | ✅ |

### ✅ Phase B: Documentation (Complete)

| Step | Detail | Status |
|------|--------|--------|
| B1 | Quickstart guide | ✅ `docs/quickstart.md` |
| B2 | CLI reference | ✅ `docs/cli-reference.md` |
| B3 | Architecture diagrams | ✅ `docs/architecture.md` |
| B4 | FAQ | ✅ `docs/faq.md` |
| B5 | Contributing guide | ✅ `docs/contributing.md` |
| B6 | README badges | ✅ PyPI, Python version, CI, license, ruff |

### Phase C: Real Repository Validation (Week 2–3)

| Step | Detail | Priority |
|------|--------|----------|
| C1 | Curate 10–15 unseen repos across Python, JS/TS, Go, Rust, Java | Critical |
| C2 | Run bootstrap on each: record runtime, ADRs generated, rules, false positives | Critical |
| C3 | Manual review: what fraction of generated ADRs are approvable? (target: ≥80%) | Critical |
| C4 | Add regression tests for every real false positive | Critical |
| C5 | Build `benchmarks/` directory with fixtures, expected outputs, runner script | ✅ |
| C6 | Update benchmark script to output validation results | ✅ |

### Phase D: Repository Polish (Week 3–4)

| Step | Detail | Priority |
|------|--------|----------|
| D1 | Demo GIF (asciinema) showing bootstrap → enforce → violation output | ✅ |
| D2 | Architecture diagrams for README | ✅ |
| D3 | ROADMAP.md — built, planned, explicitly not planned | ✅ |
| D4 | License + pyproject.toml metadata | ✅ |
| D5 | GitHub topics, description, website URL | ✅ |

### Phase E: First External Users (Week 4–5)

| Step | Detail | Priority |
|------|--------|----------|
| E1 | Recruit 10–15 developers (OSS maintainers, peers, social) | Critical |
| E2 | Ask them to install + bootstrap their repo | Critical |
| E3 | Collect structured feedback | Critical |
| E4 | Fix top-3 friction points | Critical |
| E5 | Blog post or Show HN | Medium |

### Phase F: Stable Beta & Freeze (Week 5–6)

| Step | Detail | Priority |
|------|--------|----------|
| F1 | Tag `v1.0.0-beta.2` incorporating feedback | High |
| F2 | Write the benchmark suite | High |
| F3 | **Freeze feature set** | Critical |
| F4 | Switch to placement mode | Critical |

---

## Benchmark Suite Plan

```
benchmarks/
├── benchmark_runner.py              # orchestrates all benchmarks
├── repos/                           # git submodules or minimal fixtures
│   ├── flask-sample/
│   ├── fastapi-sample/
│   ├── django-sample/
│   ├── express-sample/
│   ├── go-sample/
│   ├── rust-sample/
│   └── adversarial/                 # edge cases
├── expected/                        # expected outputs for validation
│   ├── flask-adrs.json
│   ├── fastapi-adrs.json
│   └── ...
└── results/                         # timestamped run outputs (gitignored)
```

Each benchmark records: repo size, languages, bootstrap runtime, ADRs generated, approved ADRs, false positives, coverage, enforcement findings.

---

## VS Code Extension (Post-Validation)

**Do not build until Phase C confirms ≥80% ADR approval rate AND Phase E returns positive signal.**

**First version** (minimal):
1. Webview panel showing `decisiondrift audit` output
2. One-click `guard --install` for the workspace
3. Links to CLI documentation

**Second version** (contingent on usage):
1. Inline diagnostics as you code
2. Hover tooltips showing ADR context
3. Autofix suggestions for common violations

---

## What NOT to Build Right Now

| Feature | Rationale |
|---------|-----------|
| SaaS / cloud | No proven demand |
| Multi-repo governance | No proven demand |
| Dashboard / UI | CLI + GitHub comments are sufficient |
| Postgres / pgvector | ADR corpus is small; in-memory is sub-second |
| LLM bootstrap | Deterministic V3 is more reliable |
| Embeddings | Keyword retrieval achieves 95.2% Recall@5 |
| LangGraph / agents | Linear pipeline is sufficient |
| Test generation | Deliberately deferred to keep the product focused on architecture governance |

---

## Recommendation for You

**Freeze after Phase A (Release Engineering).** Here's the tradeoff:

| Phase | Time | Value to placements |
|-------|------|---------------------|
| A: Release Engineering | 1 week | High — shows you can ship |
| B: Documentation | 1 week | Medium — shows communication |
| C: Real-repo validation | 2 weeks | Low — doesn't matter for interviews |
| D: Repository polish | 1 week | Low |
| E: External users | 2 weeks | Medium — "X users" is a strong narrative |
| F: Stable beta | 1 week | Low |

**Highest-leverage path:**
1. **Week 1:** Phase A (CI + PyPI + beta tag). Non-negotiable.
2. **Weeks 2–10:** Placements and interviews with a shipped OSS project as your portfolio.
3. **After placements (optional):** Phases C–F, then evaluate VS Code extension.

A stable, shippable beta that you can reference in every conversation is more valuable than six more months of feature growth.
