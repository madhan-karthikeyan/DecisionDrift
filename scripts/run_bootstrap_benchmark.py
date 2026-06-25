#!/usr/bin/env python3
"""Run Bootstrap V3 stability benchmark.

Measures, for each repo:
  - Crash-free completion
  - Technology candidates (count + evidence distribution)
  - Suppressed candidates
  - Enforceable ADRs generated (count, duplicates)
  - Latency (detection + total)

Usage:
    python scripts/run_bootstrap_benchmark.py
        [--repos repos/benchmark]
        [--spec benchmarks/bootstrap.yaml]
        [--output docs/bootstrap-benchmark.md]
"""

from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

import yaml

from decisiondrift.bootstrap.v3 import build_repository_model, generate_v3_suggestions

BENCHMARKS_DIR = Path(__file__).parent.parent / "benchmarks"
BENCHMARK_SPEC = BENCHMARKS_DIR / "bootstrap.yaml"
DEFAULT_REPOS_DIR = Path(__file__).parent.parent / "repos" / "benchmark"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "docs" / "bootstrap-benchmark.md"


def run_benchmark(spec_path: Path, repos_dir: Path) -> dict:
    spec = yaml.safe_load(spec_path.read_text())
    repos = spec.get("repositories", [])

    results = []
    total_techs = Counter()
    total_suppressed = 0
    total_adrs = 0
    total_dupes = 0
    total_latency = 0.0
    crashed = 0

    for repo_entry in repos:
        name = repo_entry if isinstance(repo_entry, str) else repo_entry["name"]
        repo_path = repos_dir / name

        if not repo_path.exists():
            results.append(
                {
                    "name": name,
                    "status": "skipped",
                    "error": "not cloned",
                }
            )
            continue

        t0 = time.time()
        try:
            model = build_repository_model(repo_path)
        except Exception as e:
            results.append(
                {
                    "name": name,
                    "status": "crashed",
                    "error": str(e),
                }
            )
            crashed += 1
            continue

        t1 = time.time()
        latency = t1 - t0
        total_latency += latency

        # Technology evidence distribution
        conf_dist: dict[str, int] = Counter()
        for tech in model.technologies:
            conf_dist[tech.evidence_level.value] = conf_dist.get(tech.evidence_level.value, 0) + 1

        total_techs["strong"] += conf_dist.get("strong", 0)
        total_techs["moderate"] += conf_dist.get("moderate", 0)
        total_techs["weak"] += conf_dist.get("weak", 0)

        suggestions = generate_v3_suggestions(model, set(), 1)
        adr_count = len(suggestions)
        total_adrs += adr_count
        suppressed = [t for t in model.technologies if t.suppress_reason]
        suppressed_candidates = [c for c in model.governance_candidates if c.suppress_reason]
        total_suppressed += len(suppressed) + len(suppressed_candidates)

        # Duplicate check within this repo's suggestions
        titles = [s.adr.title for s in suggestions]
        dupes = len(titles) - len(set(titles))
        total_dupes += dupes

        results.append(
            {
                "name": name,
                "status": "ok",
                "repo_role": model.repository_role,
                "repo_subtype": model.repository_subtype,
                "tech_count": len(model.technologies),
                "adr_count": adr_count,
                "duplicate_adrs": dupes,
                "confidence_distribution": dict(conf_dist),
                "detected_technologies": [t.name for t in model.technologies],
                "suppressed_technologies": [f"{t.name}: {t.suppress_reason}" for t in suppressed[:8]],
                "suppressed_candidates": [f"{c.title}: {c.suppress_reason}" for c in suppressed_candidates[:8]],
                "adrs": [s.adr.title for s in suggestions],
                "latency": latency,
            }
        )

    ran = [r for r in results if r["status"] == "ok"]
    skipped = [r for r in results if r["status"] == "skipped"]

    return {
        "results": results,
        "summary": {
            "total": len(repos),
            "ran": len(ran),
            "skipped": len(skipped),
            "crashed": crashed,
            "total_technologies": dict(total_techs),
            "total_suppressed": total_suppressed,
            "total_adrs": total_adrs,
            "total_duplicates": total_dupes,
            "total_latency": round(total_latency, 1),
            "avg_latency": round(total_latency / max(len(ran), 1), 1),
        },
    }


def _format_report(data: dict) -> str:
    s = data["summary"]
    lines = [
        "# Bootstrap V3 Benchmark Report",
        "",
        "**Date:** 2026-06-23",
        f"**Repos:** {s['ran']} evaluated, {s['skipped']} skipped, {s['crashed']} crashed",
        "",
        "---",
        "",
        "## Aggregate Metrics",
        "",
        f"  Technology candidates: {sum(s['total_technologies'].values())} "
        f"(strong={s['total_technologies'].get('strong', 0)}, "
        f"moderate={s['total_technologies'].get('moderate', 0)}, "
        f"weak={s['total_technologies'].get('weak', 0)})",
        f"  Suppressed findings/candidates: {s['total_suppressed']}",
        f"  Enforceable ADRs generated: {s['total_adrs']} ({s['total_duplicates']} duplicates)",
        f"  Average latency: {s['avg_latency']}s",
        f"  Crash rate: {s['crashed']}/{s['total']}",
        "",
        "---",
        "",
        "## Per-Repository Details",
        "",
    ]

    for r in data["results"]:
        lines.append(f"### {r['name']}")
        lines.append("")

        if r["status"] == "skipped":
            lines.append(f"_Skipped: {r.get('error', 'not cloned')}_")
            lines.append("")
            continue
        if r["status"] == "crashed":
            lines.append(f"_Crashed: {r.get('error', 'unknown')}_")
            lines.append("")
            continue

        lines.append("**Status:** ✓")
        lines.append(f"**Repository role:** {r['repo_role']} ({r['repo_subtype']})")
        lines.append(f"**Technologies:** {r['tech_count']} ({r['latency']:.1f}s)")
        if r["detected_technologies"]:
            lines.append(f"**Detected:** {', '.join(r['detected_technologies'])}")
        if r["suppressed_technologies"]:
            lines.append(f"**Suppressed technologies:** {'; '.join(r['suppressed_technologies'])}")
        if r["suppressed_candidates"]:
            lines.append(f"**Suppressed candidates:** {'; '.join(r['suppressed_candidates'])}")
        lines.append(f"**Enforceable ADRs:** {r['adr_count']} ({r['duplicate_adrs']} duplicates)")
        if r["adrs"]:
            lines.append(f"**ADR titles:** {', '.join(r['adrs'])}")
            lines.append("")
            lines.append("**Manual ADR review:**")
            lines.append("For each ADR, mark: [approve/reject/unsure] and provide brief reason")
            for title in r["adrs"]:
                lines.append(f"  - [ ] {title}")
                lines.append("    Decision: __ | Reason: __")
        if r["suppressed_technologies"] or r["suppressed_candidates"]:
            lines.append("")
            lines.append("**Manual suppression review:**")
            lines.append("For each suppression, mark: [correct/incorrect/unsure] and provide brief reason")
            for item in r["suppressed_technologies"][:5]:
                lines.append(f"  - [ ] {item}")
                lines.append("    Decision: __ | Reason: __")
            for item in r["suppressed_candidates"][:5]:
                lines.append(f"  - [ ] {item}")
                lines.append("    Decision: __ | Reason: __")
        lines.append(f"**Evidence:** {r['confidence_distribution']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Bootstrap V3 stability benchmark")
    parser.add_argument("--repos", default=str(DEFAULT_REPOS_DIR), help="Path to cloned repos")
    parser.add_argument("--spec", default=str(BENCHMARK_SPEC), help="Path to benchmark YAML")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output report path")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    repos_dir = Path(args.repos)

    if not spec_path.exists():
        print(f"Error: spec not found: {spec_path}")
        return 1

    if not repos_dir.exists():
        print(f"Warning: repos dir not found: {repos_dir}")
        print("Run `python scripts/clone_benchmark_repos.py` first.")

    print("Running Bootstrap V3 benchmark...")
    print(f"  Spec:  {spec_path}")
    print(f"  Repos: {repos_dir}")
    print()

    data = run_benchmark(spec_path, repos_dir)
    report = _format_report(data)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)

    s = data["summary"]
    print(f"Evaluated: {s['ran']} repos ({s['skipped']} skipped, {s['crashed']} crashed)")
    print(f"  Technology candidates: {sum(s['total_technologies'].values())}")
    print(f"  Suppressed findings/candidates: {s['total_suppressed']}")
    print(f"  Enforceable ADRs generated: {s['total_adrs']} ({s['total_duplicates']} dupes)")
    print(f"  Avg latency: {s['avg_latency']}s")
    print(f"Report: {output_path}")

    return 0


if __name__ == "__main__":
    main()
