# v1.0.0-beta.4 — HTML Output, Shared HTTP Registry, README Rewrite

## Highlights

- **HTML output format** — `--format html` generates a self-contained static HTML page with inline CSS, summary table, and action-colored findings badges. Ideal for CI artifact upload.
- **Shared HTTP registry** — `--registry-url <URL>` (CLI or `registry_urls` in config) fetches remote technology definition YAMLs and merges them into the registry layer stack.
- **README rewritten for clarity** — friendly tone, "What is this" section, situational use-case table, all technical docs moved to `docs/`.

## What's New

| Change | Details |
|--------|---------|
| HTML formatter | `_format_html()` in `formatter.py` renders full HTML report with inline CSS, badges, summary stats |
| Shared HTTP registry | `_load_yaml_from_url()` fetches remote YAML; `load_registry()` accepts `registry_urls` param; bundled → remote → cache → project layering |
| CLI `--registry-url` | Repeatable flag on `bootstrap`; auto-merged from config `registry_urls` |
| `registry_urls` config | New `decisiondrift.yml` key for persistent remote registry configuration |
| README rewrite | Focused on "install → init → enforce" loop; architecture/CLI details moved to `docs/` |

## Installation

```bash
pip install decisiondrift
# or
pipx install decisiondrift
```

---

# v1.0.0-beta.1 — Release Engineering & Audit Hardening

## Highlights

- **GitHub Actions CI** with lint (`ruff check`), format (`ruff format --check`), tests (310 passing, 13 skipped), coverage, and package build
- **All 4 phases of audit-driven hardening complete** — shell injection fix, symlink traversal protection, standardized exit codes, dead code removal, dependency parsing consolidation
- **Ruff lint auto-fix** across the entire codebase (162 errors fixed) + consistent formatting (59 files reformatted)
- **Documentation consolidation** — single `docs/plan.md` replaces old `plan.md` + `project-guide.md`; `docs/progress.md` tracks execution plan

## What's New

| Change | Details |
|--------|---------|
| CI pipeline | `.github/workflows/ci.yml` — lint, format, test (py3.11 + py3.14), coverage, build |
| `action.yml` | Added `min-confidence` input; updated descriptions for deterministic enforce-only mode |
| `pyproject.toml` | Ruff/Black/MyPy config; `[dev]` optional deps group; version bumped to `1.0.0-beta.1` |
| `.gitignore` | Added `dist/`, `build/`, `*.egg-info/`, `coverage_html/` |
| StrEnum migration | `EvidenceLevel`, `EvidenceRole`, `ConfidenceLevel`, `RuleType`, `Action` — migrated from `str, Enum` to `StrEnum` |
| Test fix | `test_not_available_without_api_key` — properly clears env var before assertion |

## Audit Hardening (Phases 1–4)

- **Critical:** Shell injection fix in `guard --install`; symlink traversal protection in Bootstrap V3 scanner; all 5 rule types enforced in `_enforce_repo`
- **High:** `min_confidence` threaded through Bootstrap V3 pipeline; standardized CLI exit codes; V2 dead code removal; dependency parsing consolidation
- **Medium:** Removed dead code (`_detect_architecture`, `_role_from_group_name`, unused imports); fixed broken module imports in `v3.py`
- **Low:** Rewrote `test_rules_scanner.py` for shared `utils.dependency_parser` API

## Installation

```bash
pip install decisiondrift
# or
pipx install decisiondrift
```

## Usage

```bash
# Bootstrap architecture decisions from your repo
decisiondrift bootstrap --apply

# Enforce rules (deterministic, no LLM needed)
decisiondrift enforce

# Audit ADR health
decisiondrift audit

# PR review with optional LLM classification
decisiondrift review
```
