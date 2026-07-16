# Contributing

## Setup

```bash
git clone https://github.com/madhan-karthikeyan/DecisionDrift
cd DecisionDrift
pip install -e ".[dev,ast,embeddings]"
```

## Development Commands

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check (WIP — expect pre-existing errors)
mypy src/decisiondrift

# Test
pytest                           # all tests
pytest tests/unit/               # fast unit tests only
pytest -k "not snapshot"         # skip snapshot tests

# Coverage
pytest --cov=decisiondrift --cov-report=term-missing
```

## Project Structure

```
src/decisiondrift/
  cli.py                     # CLI entrypoint (Click)
  config.py                  # Config loader (YAML + .env + custom rules)
  models/schema.py           # Pydantic models
  bootstrap/                 # Repository scanning → ADR candidate generation
  rules/                     # Deterministic rule engine (5 rule types)
  adr/                       # ADR file management
  classification/            # LLM classifier
  impact/                    # Diff parser + AST extraction (Python + Tree-sitter)
    language_registry.py     # Single source of truth for all language metadata
    treesitter_queries/      # Per-language query modules (12 languages)
  ingest/                    # Free-text → ADR pipeline
  init/                      # Project initialization
  report/                    # Output formatters (text/json/sarif/markdown/html)
  retrieval/                 # ADR retrieval (keyword + embedding)
  review/                    # Orchestrator
  github/                    # GitHub Action adapter
```

## Adding a new bootstrap pattern

1. Add the pattern definition in `bootstrap/patterns.py`
2. Add detection logic in `bootstrap/detectors.py`
3. Add tests in `tests/test_bootstrap_patterns.py`
4. Verify with `pytest tests/test_bootstrap_patterns.py`

## Adding a new rule type

1. Define the rule model in `rules/models.py`
2. Implement scanning logic in `rules/engine.py`
3. Add tests in `tests/test_rules_engine.py`

## Testing philosophy

- Unit tests should be fast and use no network
- Integration tests use temp repos and fixtures
- Snapshot tests use `syrupy` (run with `--snapshot-update` to regenerate)
- Aim for >80% coverage on core modules

## PR Process

1. Open an issue describing the change
2. Fork and create a feature branch
3. Add tests for new functionality
4. Ensure `ruff check .` and `ruff format --check .` pass
5. Open a PR linking the issue
