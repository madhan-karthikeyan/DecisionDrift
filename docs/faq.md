# FAQ

## Do I need an LLM?

**No.** The core workflow — `bootstrap` → `enforce` → `audit` → `guard` — is fully deterministic. You only need an LLM API key for `decisiondrift review` (semantic violation classification) and `decisiondrift ingest` (free-text to ADR extraction).

Without an API key, `review` tells you to use `enforce` instead.

## How is this different from ruff/mypy?

Ruff and mypy check *code correctness* (lint, types). DecisionDrift checks *architectural governance* — whether a change violates documented decisions like "don't add Flask alongside FastAPI" or "only use PostgreSQL."

| Tool | What it checks |
|------|---------------|
| Ruff | Code style, lint rules |
| mypy | Type correctness |
| DecisionDrift | Architecture decision compliance |

They're complementary. You'd run all three in CI.

## How is this different from ADR tools like adr-tools or log4brains?

Those tools help you *write and manage* ADRs as files. DecisionDrift goes further by *enforcing* those ADRs as rules against your actual code. It's the difference between having a policy document and having automated compliance checking.

## Does it work with my language/framework?

Yes for dependency/path/config rules (they work with any language). Import and API rules use Python AST by default. Tree-sitter support for JS, TS, Go, Java, Rust is available via `pip install decisiondrift[ast]`.

## Can I define rules without creating an ADR?

Yes. Add a `rules:` section to `decisiondrift.yml` with custom rules. These are merged with ADR-derived rules during enforcement:

```yaml
rules:
  - match: deprecated-lib
    type: dependency
    action: block
    description: "Block deprecated library"
```

## What output formats are available?

The `enforce` command supports `--format text|json|sarif|markdown` and `--output <file>`. SARIF output integrates with GitHub code scanning. JSON output uses the unified `ReportEnvelope` schema.

## Will it block my PR?

Only ADRs with `status: accepted` generate enforcement rules. Proposed candidates are never silently enforced. You control which ADRs to approve.

## Can I run it in CI?

Yes. The `enforce` command exits non-zero on violations, making it suitable for CI gating. There's a [GitHub Action](../README.md#github-action) that posts PR comments, sets commit status checks, submits formal reviews, and generates SARIF output.

## How do I set up a project from scratch?

Run `decisiondrift init .` — it bootstraps ADRs, interactively prompts approval, installs pre-commit hooks, and generates configuration.

## What's the full ADR lifecycle?

`decisiondrift adr list/show/approve/reject/deprecate/archive/supersede/edit/history/review`. All lifecycle commands are deterministic and require no LLM.

## What happens if I have conflicting ADRs?

The rule engine evaluates all accepted ADRs independently. If two ADRs produce conflicting rules, both fire — the one with higher severity (BLOCK > WARN > INFO) determines the exit code. Best practice is to supersede or deprecate older ADRs.

## How are confidence levels used?

Bootstrap assigns evidence levels (weak/moderate/strong) to each candidate. `--min-confidence` filters out low-evidence candidates. In the rule engine, confidence downgrades enforcement severity: a BLOCK rule with low confidence becomes INFO.

## Do I need to write YAML for ADRs?

No. The `bootstrap` command generates them from your repo structure. You just approve or reject the candidates. If you want to write ADRs manually, they use standard frontmatter format.
