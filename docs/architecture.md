# Architecture

## CLI Flow

```
decisiondrift <command> [args]
       │
       ├─ bootstrap <path>          Deterministic — no LLM
       │    └─ scan_repo()
       │         ├─ structure_scan.py   (dirs, files, indicators)
       │         ├─ detectors.py        (technologies, frameworks)
       │         ├─ patterns.py         (pattern matching)
       │         └─ candidate_generator.py  → ADRSuggestion[]
       │
       ├─ enforce [diff|.]           Deterministic — no LLM
       │    └─ engine.py
       │         ├─ scan_dependencies()    (5 dep file types)
       │         ├─ scan_imports()         (Python AST)
       │         ├─ scan_api_calls()       (Python AST)
       │         ├─ scan_paths()           (regex)
       │         └─ scan_config()          (YAML/JSON/TOML/INI)
       │
       ├─ audit                      Deterministic — no LLM
       │    └─ adr_manager/
       │         ├─ check_drift()
       │         ├─ check_expiry()
       │         └─ quality_score()
       │
       ├─ review [diff]              Optional LLM
       │    └─ classification/classifier.py
       │         ├─ retrieve_adrs()       (keyword/embedding)
       │         └─ llm_classify()        (pairwise)
       │
       ├─ ingest <file>              LLM required
       │    └─ segmenter → LLM → ADR
       │
       ├─ adr list|approve|reject    Deterministic
       │
       └─ guard --install            Deterministic
            └─ pre-commit hook → enforce --from-git
```

## Bootstrap Pipeline (V3)

```
Repository Tree
      │
      ▼
┌─────────────────┐
│  structure_scan  │  ← walk dir tree (max depth 10), skip noise
│                  │     collect: dirs, files, indicator_files
└────────┬────────┘
         │ ProjectStructure
         ▼
┌─────────────────┐
│    detectors    │  ← detect technologies from deps, files, imports
│                  │     output: list[TechnologyCandidate]
└────────┬────────┘
         │ TechnologyCandidate[]
         ▼
┌─────────────────┐
│    patterns     │  ← match known architecture patterns
│                  │     e.g. Flask → web framework
│                  │     e.g. SQLAlchemy → data access
└────────┬────────┘
         │ PatternMatch[]
         ▼
┌─────────────────┐
│      v3.py      │  ← governance logic
│                  │     suppress non-decision patterns
│                  │     assign confidence levels
│                  │     generate ADRSuggestion[]
└────────┬────────┘
         │ ADRSuggestion[]
         ▼
┌─────────────────┐
│  template_gen   │  ← render ADR markdown files
└─────────────────┘
```

## Rule Engine

```
Accepted ADRs
      │
      ▼
┌─────────────────────┐
│    rule_generator   │  ← parse ADR frontmatter, prohibitions
│   (adr/rule_gen.)   │     output: RuleSet per ADR
└──────────┬──────────┘
           │ RuleSet (dependency, import, api, path, config)
           ▼
┌─────────────────────┐
│      engine.py      │  ← scan diff or repo against rules
│                      │
│  ┌───────────────┐  │
│  │ dep scanner   │  │  requirements.txt, pyproject.toml,
│  │               │  │  package.json, go.mod, Cargo.toml
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ import scanner│  │  Python AST import traversal
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ api scanner   │  │  Python AST method/function calls
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ path scanner  │  │  regex match on file paths
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ config scanner│  │  key-value match in config files
│  └───────────────┘  │
└──────────┬──────────┘
           │ EnforcementFinding[]
           ▼
    Exit code (0/1) + Report
```

## ADR Lifecycle

```
bootstrap ──→ proposed ──→ accepted ──→ [enforced]
                 │              │
                 │              ├──→ deprecated
                 │              │
                 │              └──→ superseded
                 │
                 └──→ rejected
```

Only `accepted` ADRs generate enforcement rules.
