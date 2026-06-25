# DecisionDrift Roadmap

This document outlines the current state of DecisionDrift, our planned features for the near future, and architectural components that are explicitly **out of scope**.

## 🟢 Currently Built (v1.0.0-beta)

DecisionDrift currently offers a complete, end-to-end governance pipeline optimized for deterministic execution and CI integration.

### Core Governance Engine
- **Bootstrap V3 (Deterministic)**: A highly-tuned heuristic engine that scans repositories, identifies technologies/frameworks, and proposes actionable Architecture Decision Records (ADRs).
- **Rule Engine**: 5 distinct deterministic rule types (dependency, import, path, API call, and config).
- **Enforcement Pipeline**: Run rules against `git diff` or the full repository. Provides immediate CI-ready exit codes (`--fail-on`).
- **Audit System**: Periodic health checks for ADR drift, staleness, quality scoring, and technology coverage gaps.
- **LLM Review (Optional)**: Pairwise semantic classification of diffs against ADRs for complex, non-deterministic constraints.
- **Impact Analysis**: AST-aware symbol resolution (Python and Tree-sitter powered) to determine if a change impacts a governed component.

## 🟡 Planned Features (Next 6 Months)

Our focus is on hardening the core engine, improving developer experience, and expanding language ecosystem support.

1. **Enhanced AST Support (Tree-Sitter)**
   - Expand deep AST extraction beyond Python to fully support JS/TS, Go, Java, and Rust for `api` and `import` rules.
2. **VS Code Extension**
   - Inline diagnostics highlighting drift right in the editor.
   - Hover tooltips showing the exact ADR context when hovering over a prohibited import or dependency.
   - One-click `guard --install` configuration.
3. **Automated Autofix**
   - Provide command-line suggestions or patches to automatically resolve common architectural violations.
4. **Enhanced Markdown Parsing**
   - Support for custom frontmatter schemas and integration with existing ADR formats (e.g., MADR, Log4Brain).

## 🔴 Explicitly Not Planned

To keep DecisionDrift fast, focused, and secure, the following features are intentionally out of scope:

| Feature | Rationale |
|---------|-----------|
| **SaaS / Cloud Dashboard** | DecisionDrift is a developer tool. CLI reports and GitHub PR comments are sufficient; we won't build a standalone web UI. |
| **Multi-repo Governance** | ADRs belong in the repository they govern. Centralized architecture governance breaks the decentralized microservice model. |
| **Heavy Database Dependencies** | We will not require PostgreSQL or vector databases (pgvector). The typical ADR corpus is small enough to run fully in-memory with sub-second latency. |
| **LLM-based Bootstrapping** | While we use LLMs for ingest and review, bootstrapping a repo from scratch using LLMs is too non-deterministic and expensive. We strictly rely on the V3 heuristic engine. |
| **Complex Agentic Workflows** | LangGraph or complex multi-agent frameworks add unnecessary latency and debugging overhead. DecisionDrift uses a strict, linear pipeline. |
| **Test Generation** | Deliberately deferred to keep the product tightly focused on architecture governance. |

## Contributing

We welcome community feedback to help prioritize the `Planned Features`. If you have a use case that isn't covered, please open an issue or start a discussion on GitHub!
