#!/usr/bin/env python3
"""Run Bootstrap V2 stability benchmark.

Measures, for each repo:
  - Crash-free completion
  - Technologies detected (count + confidence distribution)
  - ADRs generated (count, duplicates)
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

from decisiondrift.bootstrap.bootstrapper import _detect_architecture

BENCHMARKS_DIR = Path(__file__).parent.parent / "benchmarks"
BENCHMARK_SPEC = BENCHMARKS_DIR / "bootstrap.yaml"
DEFAULT_REPOS_DIR = Path(__file__).parent.parent / "repos" / "benchmark"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "docs" / "bootstrap-benchmark.md"


def run_benchmark(spec_path: Path, repos_dir: Path) -> dict:
    spec = yaml.safe_load(spec_path.read_text())
    repos = spec.get("repositories", [])

    results = []
    total_techs = Counter()
    total_adrs = 0
    total_dupes = 0
    total_latency = 0.0
    crashed = 0

    for repo_entry in repos:
        name = repo_entry if isinstance(repo_entry, str) else repo_entry["name"]
        repo_path = repos_dir / name

        if not repo_path.exists():
            results.append({
                "name": name,
                "status": "skipped",
                "error": "not cloned",
            })
            continue

        t0 = time.time()
        try:
            model = _detect_architecture(str(repo_path))
        except Exception as e:
            results.append({
                "name": name,
                "status": "crashed",
                "error": str(e),
            })
            crashed += 1
            continue

        t1 = time.time()
        latency = t1 - t0
        total_latency += latency

        if model is None:
            results.append({
                "name": name,
                "status": "ok",
                "tech_count": 0,
                "adr_count": 0,
                "duplicate_adrs": 0,
                "confidence_distribution": {},
                "latency": latency,
            })
            continue

        # Technology confidence distribution
        conf_dist: dict[str, int] = Counter()
        for f in model.findings:
            if f.confidence >= 0.85:
                conf_dist["high"] = conf_dist.get("high", 0) + 1
            elif f.confidence >= 0.7:
                conf_dist["medium"] = conf_dist.get("medium", 0) + 1
            else:
                conf_dist["low"] = conf_dist.get("low", 0) + 1

        total_techs["high"] += conf_dist.get("high", 0)
        total_techs["medium"] += conf_dist.get("medium", 0)
        total_techs["low"] += conf_dist.get("low", 0)

        # Generate suggestions (template-based, same as CLI default)
        from decisiondrift.bootstrap.suggester import generate_suggestions
        suggestions = generate_suggestions(model, set(), set(), 1)
        adr_count = len(suggestions)
        total_adrs += adr_count

        # Duplicate check within this repo's suggestions
        titles = [s.adr.title for s in suggestions]
        dupes = len(titles) - len(set(titles))
        total_dupes += dupes

        results.append({
            "name": name,
            "status": "ok",
            "tech_count": model.count(),
            "adr_count": adr_count,
            "duplicate_adrs": dupes,
            "confidence_distribution": dict(conf_dist),
            "detected_technologies": [f.name for f in model.findings],
            "latency": latency,
        })

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
            "total_adrs": total_adrs,
            "total_duplicates": total_dupes,
            "total_latency": round(total_latency, 1),
            "avg_latency": round(total_latency / max(len(ran), 1), 1),
        },
    }


def _format_report(data: dict) -> str:
    s = data["summary"]
    lines = [
        "# Bootstrap V2 Benchmark Report",
        "",
        f"**Date:** 2026-06-23",
        f"**Repos:** {s['ran']} evaluated, {s['skipped']} skipped, {s['crashed']} crashed",
        "",
        "---",
        "",
        "## Aggregate Metrics",
        "",
        f"  Technologies detected: {sum(s['total_technologies'].values())} "
        f"(high={s['total_technologies'].get('high', 0)}, "
        f"medium={s['total_technologies'].get('medium', 0)}, "
        f"low={s['total_technologies'].get('low', 0)})",
        f"  ADRs generated: {s['total_adrs']} ({s['total_duplicates']} duplicates)",
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

        lines.append(f"**Status:** ✓")
        lines.append(f"**Technologies:** {r['tech_count']} ({r['latency']:.1f}s)")
        if r["detected_technologies"]:
            lines.append(f"**Detected:** {', '.join(r['detected_technologies'])}")
        lines.append(f"**ADRs:** {r['adr_count']} ({r['duplicate_adrs']} duplicates)")
        lines.append(f"**Confidence:** {r['confidence_distribution']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Bootstrap V2 stability benchmark")
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

    print(f"Running Bootstrap V2 benchmark...")
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
    print(f"  Technologies: {sum(s['total_technologies'].values())}")
    print(f"  ADRs generated: {s['total_adrs']} ({s['total_duplicates']} dupes)")
    print(f"  Avg latency: {s['avg_latency']}s")
    print(f"Report: {output_path}")

    return 0


if __name__ == "__main__":
    main()
