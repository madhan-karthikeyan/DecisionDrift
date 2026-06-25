#!/usr/bin/env python3
"""Run automated validation benchmark for Bootstrap V3.

Orchestrates all benchmarks, loads expected outputs, and calculates precision/recall metrics.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from decisiondrift.bootstrap.v3 import build_repository_model, generate_v3_suggestions

BENCHMARKS_DIR = Path(__file__).parent
REPOS_DIR = BENCHMARKS_DIR / "repos"
EXPECTED_DIR = BENCHMARKS_DIR / "expected"


def run_benchmark():
    if not REPOS_DIR.exists() or not EXPECTED_DIR.exists():
        print("Error: Missing repos/ or expected/ directories.")
        print("Run `python scripts/generate_benchmark_fixtures.py` first.")
        return 1

    total_tp = 0
    total_fp = 0
    total_fn = 0

    print("==================================================")
    print(" Bootstrap V3 Automated Validation Benchmark ")
    print("==================================================")

    for expected_file in EXPECTED_DIR.glob("*.json"):
        repo_name = expected_file.stem
        repo_path = REPOS_DIR / repo_name

        if not repo_path.exists():
            print(f"[{repo_name}] ⚠️ Repo not found, skipping...")
            continue

        with open(expected_file) as f:
            expected_data = json.load(f)

        expected_adrs = set(expected_data.get("expected_adrs", []))

        t0 = time.time()
        try:
            model = build_repository_model(repo_path)
            suggestions = generate_v3_suggestions(model, set(), 1)
            generated_adrs = set(s.adr.title for s in suggestions)
        except Exception as e:
            print(f"[{repo_name}] ❌ CRASHED: {e}")
            continue

        t1 = time.time()

        tp = len(expected_adrs.intersection(generated_adrs))
        fp = len(generated_adrs - expected_adrs)
        fn = len(expected_adrs - generated_adrs)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        print(f"\n[{repo_name}] - {(t1 - t0):.2f}s")
        print(f"  Expected:  {len(expected_adrs)}")
        print(f"  Generated: {len(generated_adrs)}")

        if fp > 0:
            print(f"  False Positives: {generated_adrs - expected_adrs}")
        if fn > 0:
            print(f"  False Negatives: {expected_adrs - generated_adrs}")

    print("\n==================================================")
    print(" OVERALL METRICS ")
    print("==================================================")

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"True Positives (TP):  {total_tp}")
    print(f"False Positives (FP): {total_fp}")
    print(f"False Negatives (FN): {total_fn}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1 Score:  {f1:.2%}")
    print("==================================================")

    return 0


if __name__ == "__main__":
    exit(run_benchmark())
