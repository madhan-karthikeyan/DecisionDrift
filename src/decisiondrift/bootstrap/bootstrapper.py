from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from decisiondrift.adr.parser import parse_adr_file
from decisiondrift.bootstrap.template_generator import (
    apply_suggestions,
)
from decisiondrift.bootstrap.v3 import (
    build_repository_model,
    generate_v3_suggestions,
)


def bootstrap(
    repo_path: str | Path,
    adr_dir: str | Path,
    dry_run: bool = True,
    min_confidence: str = "low",
    max_candidates: int | None = None,
    use_llm: bool = False,
    llm_api_key: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
    min_llm_confidence: float = 0.6,
    cache_templates: bool = False,
) -> list:
    """Scan a repository and generate candidate ADRs.

    Args:
        repo_path: Path to the repository root.
        adr_dir: Path to existing ADR directory.
        dry_run: If True, print candidates without writing.
        min_confidence: Minimum confidence threshold ("low", "medium", "high").
        max_candidates: Maximum number of candidate ADRs to generate.
        use_llm: If True, use LLM to recognize unknown technologies.
        llm_api_key: Override LLM API key.
        llm_model: Override LLM model name.
        llm_base_url: Override LLM API base URL.
        min_llm_confidence: Minimum confidence for LLM-generated results (0.0-1.0).
        cache_templates: If True, cache LLM-generated ADR templates.
    """
    print(f"Scanning repository: {repo_path}")

    knowledge_provider: Any = None
    if use_llm:
        api_key = llm_api_key or os.environ.get("DECISIONDRIFT_LLM_API_KEY")
        model = llm_model or os.environ.get("DECISIONDRIFT_LLM_MODEL", "gpt-4o")
        base_url = llm_base_url or os.environ.get("DECISIONDRIFT_LLM_BASE_URL")
        if api_key:
            from decisiondrift.bootstrap.knowledge_provider import KnowledgeProvider
            from decisiondrift.bootstrap.registry import load_registry
            from decisiondrift.llm.client import LLMClient

            llm_client = LLMClient(model=model, api_key=api_key, base_url=base_url)
            registry = load_registry()
            knowledge_provider = KnowledgeProvider(
                registry=registry,
                llm_client=llm_client,
                repo_path=str(repo_path),
                min_llm_confidence=min_llm_confidence,
                cache_templates=cache_templates,
            )
            print(f"  LLM bootstrap enabled (model={model})")
        else:
            print("  LLM requested but no API key configured. Set DECISIONDRIFT_LLM_API_KEY or pass --llm-api-key.")

    model = build_repository_model(repo_path, knowledge_provider=knowledge_provider)
    if not model.technologies:
        print("  No technologies detected.")
        return []

    print()
    print(_repository_summary(model))

    # Load existing ADRs for dedup
    existing_ids: set[str] = set()
    existing_titles: set[str] = set()
    adr_path = Path(adr_dir)
    next_id = 0
    if adr_path.exists():
        for f in sorted(adr_path.glob("ADR-*.md")):
            m = re.match(r"^ADR-(\d{4})\.md$", f.name)
            if m:
                existing_ids.add(f.name.replace(".md", ""))
                num = int(m.group(1))
                next_id = max(next_id, num + 1)
                record = parse_adr_file(f)
                if record:
                    existing_titles.add(record.title)

    suggestions = generate_v3_suggestions(model, existing_titles, next_id, min_confidence=min_confidence)

    # Apply max_candidates limit (keep highest confidence first)
    if max_candidates is not None and len(suggestions) > max_candidates:
        suggestions = suggestions[:max_candidates]

    if not suggestions:
        print("  No enforceable ADRs to suggest.")
        suppressed = _suppressed_summary(model)
        if suppressed:
            print()
            print("  Suppressed candidates:")
            for line in suppressed:
                print(f"    - {line}")
        return []

    print(f"  Suggested ADRs: {len(suggestions)}")
    print(f"  Suggested Rules: {sum(len(s.rules) for s in suggestions)}")
    print()

    if dry_run:
        print(f"{'=' * 60}")
        print("DRY RUN — no files written")
        print(f"Run with --apply to write ADRs to {adr_dir}")
        print(f"{'=' * 60}")
        print()
        for s in suggestions:
            print(s.dry_run_text())
            print("---")
    else:
        count = apply_suggestions(suggestions, adr_dir)
        print(f"Wrote {count} ADR(s) to {adr_dir}")

    return suggestions


def _repository_summary(model) -> str:
    lines = [
        "Repository Summary",
        "",
        f"  Role: {model.repository_role}",
        f"  Evidence records: {len(model.evidence)}",
        "  Technologies:",
    ]
    for tech in model.technologies:
        suffix = f" ({tech.suppress_reason})" if tech.suppress_reason else ""
        lines.append(f"    {tech.name} [{tech.category}] {tech.evidence_level.value}/{tech.role}{suffix}")
    lines.append("")
    lines.append(f"  Governance candidates: {len(model.governance_candidates)}")
    return "\n".join(lines)


def _suppressed_summary(model) -> list[str]:
    lines: list[str] = []
    for tech in model.technologies:
        if tech.suppress_reason:
            lines.append(f"{tech.name}: {tech.suppress_reason}")
    for candidate in model.governance_candidates:
        if candidate.suppress_reason:
            lines.append(f"{candidate.title}: {candidate.suppress_reason}")
    return lines[:12]
