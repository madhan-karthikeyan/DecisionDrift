from __future__ import annotations

import re
from pathlib import Path

from typing import Optional

from decisiondrift.adr.parser import parse_adr_file
from decisiondrift.bootstrap.architecture import ArchitectureModel
from decisiondrift.bootstrap.detectors import (
    DetectionContext,
    collect_deps,
    detect_technologies,
)
from decisiondrift.bootstrap.structure_scan import scan_repo
from decisiondrift.bootstrap.suggester import apply_suggestions, generate_suggestions
from decisiondrift.rules.scanner import scan_imports


def _detect_architecture(repo_path: str) -> Optional[ArchitectureModel]:
    """Run technology detection and return architecture model.
    Used by audit CLI for coverage analysis.
    """
    try:
        structure = scan_repo(repo_path)
        ctx = DetectionContext(
            repo_path=Path(repo_path),
            deps=collect_deps(Path(repo_path)),
            imports=scan_imports(repo_path),
            structure=structure,
        )
        findings = detect_technologies(ctx)
        if not findings:
            return None
        return ArchitectureModel(findings)
    except Exception:
        return None


def bootstrap(
    repo_path: str | Path,
    adr_dir: str | Path,
    dry_run: bool = True,
    min_confidence: str = "low",
) -> list:
    print(f"Scanning repository: {repo_path}")

    structure = scan_repo(repo_path)
    ctx = DetectionContext(
        repo_path=Path(repo_path),
        deps=collect_deps(Path(repo_path)),
        imports=scan_imports(repo_path),
        structure=structure,
    )

    findings = detect_technologies(ctx)
    if not findings:
        print("  No technologies detected.")
        return []

    model = ArchitectureModel(findings)

    print(f"\n{model.summary()}")

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

    suggestions = generate_suggestions(model, existing_ids, existing_titles, next_id)

    if not suggestions:
        print("  No new ADRs to suggest (all already documented).")
        return []

    print(f"  Suggested ADRs: {len(suggestions)}")
    print(f"  Suggested Rules: {sum(len(s.rules) for s in suggestions)}")
    print()

    if dry_run:
        print(f"{'=' * 60}")
        print(f"DRY RUN — no files written")
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
