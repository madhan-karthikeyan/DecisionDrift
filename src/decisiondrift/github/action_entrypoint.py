from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from decisiondrift.models.schema import ReportEnvelope
from decisiondrift.report.formatter import format_output


def _findings_from_enforce(result) -> list[dict]:
    if result is None:
        return []
    return [
        {
            "adr_id": f.adr_id,
            "adr_title": f.adr_title,
            "rule_id": f.rule_id,
            "rule_type": f.rule_type.value,
            "action": f.action.value,
            "severity": f.severity,
            "match_value": f.match_value,
            "file_path": f.file_path,
            "description": f.description,
        }
        for f in result.findings
    ]


def _findings_from_lm(result) -> list[dict]:
    if result is None:
        return []
    return [
        {
            "adr_id": f.adr_id,
            "adr_title": f.adr_title,
            "rule_id": f.adr_id,
            "rule_type": "semantic",
            "action": "block" if f.classification in ("violates", "likely_violates") else "warn",
            "severity": f.severity,
            "match_value": f.symbol_name,
            "file_path": f.file_path,
            "description": f"{f.classification}: {f.reasoning}",
        }
        for f in result.findings
    ]


def _has_blocking(enforce_result, lm_result) -> bool:
    if enforce_result:
        for f in enforce_result.findings:
            if f.action.value == "block":
                return True
    if lm_result:
        for f in lm_result.findings:
            if f.classification in ("violates", "likely_violates"):
                return True
    return False


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
    head_sha = pr_data.get("head", {}).get("sha", "")

    sarif_output = os.environ.get("INPUT_SARIF_OUTPUT_PATH", "")
    review_mode = os.environ.get("INPUT_REVIEW_MODE", "comment")

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
        print("Running LLM classification...")
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

    all_findings = _findings_from_enforce(enforce_result) + _findings_from_lm(lm_result)

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

    # Set commit status
    has_blocks = _has_blocking(enforce_result, lm_result)
    if head_sha:
        state = "failure" if has_blocks else "success"
        desc = f"{len(all_findings)} finding(s)" if all_findings else "Clean"
        try:
            client.create_status(owner, repo_name, head_sha, state, desc, "DecisionDrift Review")
            print(f"Set commit status: {state}")
        except Exception as e:
            print(f"Error setting commit status: {e}")

    # Generate SARIF output file
    if sarif_output and all_findings:
        envelope = ReportEnvelope(
            command="enforce",
            summary={
                "findings_count": len(all_findings),
                "has_blocking": has_blocks,
                "pr_number": pr_number,
                "files_scanned": enforce_result.files_scanned if enforce_result else 0,
                "rules_evaluated": enforce_result.rules_evaluated if enforce_result else 0,
            },
            findings=all_findings,
        )
        sarif_text = format_output(envelope, "sarif")
        sarif_path = Path(sarif_output)
        sarif_path.parent.mkdir(parents=True, exist_ok=True)
        sarif_path.write_text(sarif_text)
        print(f"SARIF output written to {sarif_output}")

    # Submit formal PR review
    if review_mode != "comment":
        if has_blocks and review_mode in ("request-changes", "auto"):
            review_event = "REQUEST_CHANGES"
            review_body = (
                "## DecisionDrift Review — Changes Requested\n\n"
                f"{len(all_findings)} violation(s) detected. The comment above has full details."
            )
        elif not has_blocks and review_mode == "auto":
            review_event = "APPROVE"
            review_body = "## DecisionDrift Review — No violations detected. Approved."
        else:
            review_event = "COMMENT"
            review_body = body

        if review_event != "COMMENT":
            try:
                client.submit_review(owner, repo_name, pr_number, review_body, review_event)
                print(f"Submitted PR review: {review_event}")
            except Exception as e:
                print(f"Error submitting PR review: {e}")

    # Determine exit code
    if config["fail_on_violation"]:
        if has_blocks:
            print(f"FAIL_ON_VIOLATION enabled — {len(all_findings)} block(s) found.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
