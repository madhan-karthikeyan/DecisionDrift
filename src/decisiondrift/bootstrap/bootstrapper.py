from __future__ import annotations

import re
from pathlib import Path

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
    use_llm: bool = False,
) -> list:
    """Scan a repository and generate candidate ADRs.

    Args:
        repo_path: Path to the repository root.
        adr_dir: Path to existing ADR directory.
        dry_run: If True, print candidates without writing.
        min_confidence: Minimum confidence threshold ("low", "medium", "high").
        use_llm: Deprecated in Bootstrap V3. Deterministic evidence-based
                 inference is always used.
    """
    print(f"Scanning repository: {repo_path}")
    if use_llm:
        print("  LLM bootstrap synthesis is disabled in Bootstrap V3; using deterministic inference.")

    model = build_repository_model(repo_path)
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
