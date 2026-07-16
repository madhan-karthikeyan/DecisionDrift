# DecisionDrift for VS Code

Architecture governance powered by ADRs — enforce rules directly in your editor.

## Features

- **Analyze Current File** — runs `decisiondrift enforce --file <path>` on the active file
- **Analyze Entire Workspace** — batch analysis across all supported source files
- **Auto-analyze on Save/Open** — instant diagnostics as you edit
- **Findings Sidebar** — clickable tree view of all violations
- **Health Report** — checks CLI, config, registry, tree-sitter, embeddings, and LLM setup

## Requirements

- Python 3.10+ with `decisiondrift` installed: `pip install decisiondrift`
- Optional: `pip install decisiondrift[ast]` for tree-sitter language analysis
- Optional: `pip install decisiondrift[embeddings]` for embedding-based ADR retrieval

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `decisiondrift.cliPath` | `""` | Path to the CLI (auto-discovered from PATH if empty) |
| `decisiondrift.adrDir` | `""` | ADR directory (defaults to `<workspace>/docs/adr`) |
| `decisiondrift.runOnSave` | `true` | Run enforcement on file save |
| `decisiondrift.runOnOpen` | `true` | Run enforcement on file open |

## Commands

- `DecisionDrift: Analyze Current File`
- `DecisionDrift: Analyze Entire Workspace`
- `DecisionDrift: Show Health Report`
