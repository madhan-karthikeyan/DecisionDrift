from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("GITHUB_EVENT_PATH not set — not running in GitHub Action context.")
        return 1

    event = json.loads(Path(event_path).read_text())
    repository = event.get("repository", {})
    pr_data = event.get("pull_request")

    if not pr_data:
        print("Not a pull request event. Skipping.")
        return 0

    owner = (repository.get("full_name") or "").split("/")[0] if repository.get("full_name") else ""
    repo_name = (repository.get("full_name") or "").split("/")[1] if repository.get("full_name") else ""
    pr_number = pr_data.get("number")

    config = {
        "llm": {
            "api_key": os.environ.get("INPUT_LLM_API_KEY") or os.environ.get("DECISIONDRIFT_LLM_API_KEY"),
            "model": os.environ.get("INPUT_LLM_MODEL") or os.environ.get("DECISIONDRIFT_LLM_MODEL", "gpt-4o"),
            "base_url": os.environ.get("INPUT_LLM_BASE_URL") or os.environ.get("DECISIONDRIFT_LLM_BASE_URL"),
        },
        "adr_dir": os.environ.get("INPUT_ADR_DIR", "docs/adr"),
        "fail_on_violation": os.environ.get("INPUT_FAIL_ON_VIOLATION", "false").lower() == "true",
        "max_pairs_per_pr": int(os.environ.get("INPUT_MAX_PAIRS", "15")),
        "wall_clock_budget_seconds": int(os.environ.get("INPUT_TIMEOUT_SECONDS", "300")),
        "similarity_threshold": float(os.environ.get("INPUT_SIMILARITY_THRESHOLD", "0.5")),
    }

    if not config["llm"]["api_key"]:
        print("Info: LLM API key not configured. Running deterministic rule engine only.")

    from decisiondrift.adr.loader import load_adrs
    from decisiondrift.adr.supersession import resolve_active
    from decisiondrift.github.client import GitHubClient
    from decisiondrift.github.comment_manager import upsert_comment
    from decisiondrift.report.github_formatter import compile_github_comment
    from decisiondrift.review.service import run_review
    from decisiondrift.rules.engine import enforce_from_adrs

    client = GitHubClient()

    print(f"Fetching diff for PR #{pr_number}...")
    try:
        diff_text = client.get_pr_diff(owner, repo_name, pr_number)
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        return 1

    if not diff_text.strip():
        print("No changes detected — empty diff.")
        return 0

    # Load ADRs
    decisions = load_adrs(config["adr_dir"], status_filter={"accepted"})
    active = resolve_active(decisions)

    if not active:
        print("No accepted ADRs found. Nothing to enforce.")
        return 0

    # Step 1: Rule engine (deterministic, zero LLM cost)
    print(f"Running deterministic rule engine ({len(active)} ADRs)...")
    try:
        enforce_result = enforce_from_adrs(active, repo_path=".", diff_text=diff_text)
    except Exception as e:
        print(f"Error during rule enforcement: {e}")
        enforce_result = None

    # Step 2: LLM classification (semantic reasoning, only for remaining analysis)
    lm_result = None
    if config["llm"]["api_key"]:
        print(f"Running LLM classification...")
        try:
            lm_result = run_review(
                diff_text,
                repo_path=".",
                adr_dir=config["adr_dir"],
                config=config,
            )
        except Exception as e:
            print(f"Error during LLM review: {e}")

    # Combine results
    if enforce_result and enforce_result.findings:
        print(f"Rule engine: {len(enforce_result.findings)} finding(s)")
    if lm_result and lm_result.findings:
        print(f"LLM classification: {len(lm_result.findings)} finding(s)")

    body = compile_github_comment(
        lm_result,
        rule_findings=enforce_result.findings if enforce_result else [],
    )

    print(f"Posting comment to PR #{pr_number}...")
    try:
        upsert_comment(client, owner, repo_name, pr_number, body)
    except Exception as e:
        print(f"Error posting comment: {e}")
        return 1

    # Determine exit code
    if config["fail_on_violation"]:
        block_count = 0
        if enforce_result:
            block_count += sum(1 for f in enforce_result.findings if f.action.value == "block")
        if lm_result:
            block_count += sum(1 for f in lm_result.findings if f.classification in ("violates", "likely_violates"))
        if block_count:
            print(f"FAIL_ON_VIOLATION enabled — {block_count} block(s) found.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
