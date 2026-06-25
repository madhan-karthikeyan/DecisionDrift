#!/usr/bin/env python3
"""Clone all benchmark repositories for Bootstrap V2 evaluation.

Usage:
    python scripts/clone_benchmark_repos.py [--dir repos/benchmark] [--shallow]
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import yaml

BENCHMARK_SPEC = Path(__file__).parent.parent / "benchmarks" / "bootstrap.yaml"


def clone_repo(url: str, dest: Path, shallow: bool = True) -> bool:
    """Clone a single repo. Returns True if successful."""
    if dest.exists():
        print(f"  ✓ Already exists: {dest}")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone"]
    if shallow:
        cmd.extend(["--depth", "1"])
    cmd.extend([url, str(dest)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return True
        print(f"  ✗ Failed: {result.stderr.strip()[:200]}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("  ✗ Timed out after 120s", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}", file=sys.stderr)
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clone benchmark repos")
    parser.add_argument("--dir", default="repos/benchmark", help="Output directory")
    parser.add_argument("--shallow", action="store_true", default=True, help="Shallow clone")
    parser.add_argument("--resume", action="store_true", help="Skip existing dirs")
    args = parser.parse_args()

    if not BENCHMARK_SPEC.exists():
        print(f"Error: {BENCHMARK_SPEC} not found")
        return 1

    spec = yaml.safe_load(BENCHMARK_SPEC.read_text())
    repos = spec.get("repositories", [])
    out_dir = Path(args.dir)

    print(f"Cloning {len(repos)} benchmark repos into {out_dir}...")
    print()

    success = 0
    failed = 0

    for i, repo in enumerate(repos, 1):
        name = repo if isinstance(repo, str) else repo["name"]
        url = repo["url"] if isinstance(repo, dict) and "url" in repo else f"https://github.com/{name}.git"
        dest = out_dir / name

        if args.resume and dest.exists():
            print(f"[{i}/{len(repos)}] ✓ {name} (cached)")
            success += 1
            continue

        print(f"[{i}/{len(repos)}] Cloning {name}...", end=" ", flush=True)
        ok = clone_repo(url, dest, shallow=args.shallow)
        if ok:
            success += 1
            print("  ✓ Done")
        else:
            failed += 1
            print("")

        # Rate-limit: avoid hitting GitHub too fast
        time.sleep(0.5)

    print()
    print(f"Results: {success} cloned, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    main()
