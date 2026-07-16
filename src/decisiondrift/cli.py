from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import click

from decisiondrift import __version__
from decisiondrift.adr_manager.commands import (
    approve_adr,
    deprecate_adr,
    edit_adr,
    history_adr,
    list_adrs,
    reject_adr,
    review_adrs,
    show_adr,
    supersede_adr,
)


@click.group()
@click.version_option(version=__version__, prog_name="decisiondrift")
def cli():
    pass


@cli.group()
def adr():
    """Manage ADR lifecycle."""


@adr.command("review")
@click.argument("path", type=click.Path(exists=True), default=".", required=False)
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_review(path: str, adr_dir: str):
    """Run bootstrap and interactively approve/reject candidate ADRs."""
    result = review_adrs(path, adr_dir)
    if result["approved"] == 0 and result["total"] > 0:
        sys.exit(1)


@adr.command("list")
@click.option("--status", type=str, help="Filter by status (proposed, accepted, rejected, deprecated, superseded)")
@click.option("--source", type=str, help="Filter by source (manual, bootstrap, ingest)")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_list(status: str | None, source: str | None, adr_dir: str):
    """List ADRs with optional status/source filters."""
    records = list_adrs(adr_dir, status=status, source=source)
    if not records:
        click.echo("No ADRs found.")
        if not status and not source:
            click.echo("")
            click.echo("  Generate candidate ADRs with:")
            click.echo("    decisiondrift bootstrap <repo-path> --apply")
            click.echo("")
            click.echo("  Or list with filters:")
            click.echo("    decisiondrift adr list --status proposed")
        sys.exit(1)
    _print_adr_table(records)


@adr.command("approve")
@click.argument("adr_id")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_approve(adr_id: str, adr_dir: str):
    """Approve a proposed ADR (status → accepted)."""
    approve_adr(adr_dir, adr_id)


@adr.command("reject")
@click.argument("adr_id")
@click.option("--reason", type=str, help="Reason for rejection")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_reject(adr_id: str, reason: str | None, adr_dir: str):
    """Reject a proposed ADR (status → rejected)."""
    reject_adr(adr_dir, adr_id, reason=reason)


@adr.command("deprecate")
@click.argument("adr_id")
@click.option("--reason", type=str, help="Reason for deprecation")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_deprecate(adr_id: str, reason: str | None, adr_dir: str):
    """Deprecate an ADR (status → deprecated)."""
    deprecate_adr(adr_dir, adr_id, reason=reason)


@adr.command("archive")
@click.argument("adr_id")
@click.option("--reason", type=str, help="Reason for archiving")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_archive(adr_id: str, reason: str | None, adr_dir: str):
    """Archive an ADR (alias for deprecate, status → deprecated)."""
    deprecate_adr(adr_dir, adr_id, reason=reason)


@adr.command("supersede")
@click.argument("adr_id")
@click.argument("title")
@click.option("--body", type=str, help="Body text for the new superseding ADR")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_supersede(adr_id: str, title: str, body: str | None, adr_dir: str):
    """Supersede an ADR with a new one (old → superseded, creates new ADR)."""
    new_id = supersede_adr(adr_dir, adr_id, title, body=body)
    if new_id is None:
        sys.exit(1)
    click.echo(f"Created {new_id}.md — run `decisiondrift adr show {new_id}` to view.")


@adr.command("edit")
@click.argument("adr_id")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_edit(adr_id: str, adr_dir: str):
    """Open an ADR in $EDITOR for editing."""
    edit_adr(adr_dir, adr_id)


@adr.command("history")
@click.argument("adr_id")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_history(adr_id: str, adr_dir: str):
    """Show git history for an ADR file."""
    history_adr(adr_dir, adr_id)


@adr.command("show")
@click.argument("adr_id")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_show(adr_id: str, adr_dir: str):
    """Show details of a single ADR."""
    record = show_adr(adr_dir, adr_id)
    if record is None:
        sys.exit(1)
    click.echo(f"ID:       {record.id}")
    click.echo(f"Title:    {record.title}")
    click.echo(f"Status:   {record.status}")
    click.echo(f"Severity: {record.severity}")
    click.echo(f"Source:   {record.source}")
    if record.type:
        click.echo(f"Type:     {record.type}")
    if record.confidence:
        click.echo(f"Confidence: {record.confidence.value}")
    if record.rationale:
        click.echo(f"\nRationale:\n{record.rationale}")
    if record.prohibitions:
        click.echo(f"\nProhibitions: {', '.join(record.prohibitions)}")
    if record.keywords:
        click.echo(f"Keywords: {', '.join(record.keywords)}")
    if record.exceptions:
        click.echo(f"Exceptions: {record.exceptions}")
    if record.alternatives_rejected:
        click.echo(f"Alternatives rejected: {', '.join(record.alternatives_rejected)}")
    if record.owner:
        click.echo(f"Owner: {record.owner}")
    if record.review_after:
        click.echo(f"Review by: {record.review_after}")
    if record.expires_after:
        click.echo(f"Expires: {record.expires_after}")
    if record.rejected_reason:
        click.echo(f"Rejection reason: {record.rejected_reason}")
    if record.superseded_by:
        click.echo(f"Superseded by: {record.superseded_by}")
    if record.evidence:
        click.echo(f"\nEvidence ({len(record.evidence)} items):")
        for e in record.evidence:
            click.echo(f"  - {e}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
@click.option("--dry-run", is_flag=True, default=True, help="Show candidates without writing (default)")
@click.option("--apply", is_flag=True, help="Write candidates to ADR directory")
@click.option(
    "--min-confidence",
    default="low",
    show_default=True,
    type=click.Choice(["low", "medium", "high"]),
    help="Minimum confidence level",
)
@click.option("--max-candidates", type=int, default=None, help="Maximum number of candidate ADRs to generate")
@click.option("--llm", is_flag=True, help="Enable LLM technology recognition for unknown dependencies")
@click.option("--llm-api-key", type=str, default=None, help="LLM API key (overrides DECISIONDRIFT_LLM_API_KEY)")
@click.option("--llm-model", type=str, default=None, help="LLM model name (default: gpt-4o)")
@click.option("--llm-base-url", type=str, default=None, help="LLM API base URL (for Ollama, Groq, etc.)")
@click.option("--min-llm-confidence", type=float, default=0.6, show_default=True, help="Minimum confidence for LLM results (0.0-1.0)")
@click.option("--cache-templates", is_flag=True, help="Cache LLM-generated ADR templates (opt-in)")
@click.option("--registry-url", "registry_urls", multiple=True, help="URL to a shared technology registry YAML (can be specified multiple times)")
def bootstrap(path: str, adr_dir: str, dry_run: bool, apply: bool, min_confidence: str, max_candidates: int | None,
              llm: bool, llm_api_key: str | None, llm_model: str | None, llm_base_url: str | None,
              min_llm_confidence: float, cache_templates: bool, registry_urls: tuple[str, ...] | None):
    """Generate candidate ADRs from repository structure.

    Bootstrap V3 uses deterministic evidence collection, repository modeling,
    governance candidate discovery, and enforceability analysis.

    With --llm, unknown technologies are recognized via LLM, and ADR templates
    can be generated for unrecognized technologies.
    """
    from decisiondrift.bootstrap.bootstrapper import bootstrap as run_bootstrap
    from decisiondrift.config import load_config

    if apply:
        dry_run = False

    # Merge CLI --registry-url with config file registry_urls
    cfg = load_config()
    if registry_urls:
        urls = list(registry_urls)
    else:
        urls = cfg.get("registry_urls", []) or []

    try:
        run_bootstrap(
            path,
            adr_dir=adr_dir,
            dry_run=dry_run,
            min_confidence=min_confidence,
            max_candidates=max_candidates,
            use_llm=llm,
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            min_llm_confidence=min_llm_confidence,
            cache_templates=cache_templates,
            registry_urls=urls or None,
        )
    except Exception as e:
        click.echo(f"Error during bootstrap: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="ADR output directory")
@click.option("--yes", "non_interactive", is_flag=True, help="Non-interactive mode (auto-approve all ADRs)")
@click.option("--template", type=str, default=None, help="Project template (e.g., fastapi, monorepo)")
@click.option("--with-ci", "generate_ci", is_flag=True, help="Generate GitHub Actions CI workflow")
def init_cmd(path: str, adr_dir: str, non_interactive: bool, template: str | None, generate_ci: bool):
    """Initialize DecisionDrift for a repository.

    Detects project technologies, bootstraps ADRs, prompts for approval,
    installs pre-commit hook, and generates configuration.
    """
    from decisiondrift.init.service import init_project
    from decisiondrift.models.schema import ReportEnvelope
    from decisiondrift.report.formatter import format_output

    repo_path = Path(path).resolve()
    click.echo(f"Initializing DecisionDrift in {repo_path}")
    click.echo("")

    try:
        result = init_project(
            repo_path=repo_path,
            non_interactive=non_interactive,
            template=template,
            adr_dir=adr_dir,
            generate_ci=generate_ci,
        )

        click.echo("")
        click.echo("Done!")
        click.echo("")
        for step in result["steps_taken"]:
            click.echo(f"  ✓ {step}")
        click.echo("")
        click.echo("Next steps:")
        click.echo("  - Review ADRs:  decisiondrift adr list")
        click.echo("  - Run enforce:  decisiondrift enforce --from-git")
        click.echo("  - Run audit:    decisiondrift audit")
        click.echo("  - Edit config:  decisiondrift.yml")
    except Exception as e:
        click.echo(f"Error during init: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def ingest(file: str, adr_dir: str):
    """Generate candidate ADRs from free-text notes."""
    from decisiondrift.ingest.service import run_ingest

    run_ingest(file, adr_dir)


def _read_diff(diff_file: str | None, repo: str, from_git: bool, staged: bool = False) -> str | None:
    if from_git:
        cmd = ["git", "diff", "--cached"] if staged else ["git", "diff"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repo,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            click.echo("Error: `git diff` timed out.", err=True)
            return None
        except FileNotFoundError:
            click.echo("Error: git not found. Make sure git is installed.", err=True)
            return None
        if result.returncode != 0:
            err = result.stderr.strip()
            click.echo(f"Error: `git diff` failed: {err or 'not a git repository?'}", err=True)
            return None
        return result.stdout
    if diff_file:
        try:
            return Path(diff_file).read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            click.echo(f"Error: diff file not found: {diff_file}", err=True)
            return None
        except OSError as e:
            click.echo(f"Error: could not read {diff_file}: {e}", err=True)
            return None
    return None


def _check_adr_dir(adr_dir: str) -> bool:
    path = Path(adr_dir)
    if not path.exists():
        click.echo(f"Warning: ADR directory not found: {adr_dir}", err=True)
        return False
    if not any(path.glob("*.md")):
        click.echo(f"Warning: no ADR files found in {adr_dir}", err=True)
        return False
    return True


@cli.command()
@click.argument("diff_file", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option("--repo", default=".", show_default=True, help="Path to repository root")
@click.option("--adr-dir", default=None, help="Path to ADR directory (default: <repo>/docs/adr)")
@click.option("--from-git", is_flag=True, help="Get diff from `git diff` in the repo")
@click.option("--staged", is_flag=True, help="Get diff from `git diff --cached` (staged changes)")
@click.option("--llm-api-key", type=str, default=None, help="LLM API key (overrides config and env)")
@click.option("--llm-model", type=str, default=None, help="LLM model name (overrides config and env)")
@click.option("--llm-base-url", type=str, default=None, help="LLM API base URL (overrides config and env)")
@click.option("--max-pairs", type=int, default=None, help="Max (ADR, symbol) pairs to classify")
@click.option("--similarity-threshold", type=float, default=None, help="Minimum similarity for ADR consideration")
@click.option("--timeout", type=int, default=None, help="Max wall-clock time in seconds")
def review(diff_file: str | None, repo: str, adr_dir: str | None, from_git: bool, staged: bool,
           llm_api_key: str | None, llm_model: str | None, llm_base_url: str | None,
           max_pairs: int | None, similarity_threshold: float | None, timeout: int | None):
    """Evaluate changes against accepted ADRs."""
    from decisiondrift.config import load_config
    from decisiondrift.review.service import run_review

    cfg = load_config()
    if llm_api_key is not None:
        cfg["llm"]["api_key"] = llm_api_key
    if llm_model is not None:
        cfg["llm"]["model"] = llm_model
    if llm_base_url is not None:
        cfg["llm"]["base_url"] = llm_base_url
    if max_pairs is not None:
        cfg["max_pairs_per_pr"] = max_pairs
    if similarity_threshold is not None:
        cfg["similarity_threshold"] = similarity_threshold
    if timeout is not None:
        cfg["wall_clock_budget_seconds"] = timeout

    resolved_adr_dir = Path(adr_dir) if adr_dir else Path(repo) / "docs" / "adr"

    diff_text = _read_diff(diff_file, repo, from_git, staged=staged)
    if diff_text is None:
        return
    if not diff_text.strip():
        click.echo("No changes detected (empty diff). Nothing to review.")
        return

    _check_adr_dir(str(resolved_adr_dir))

    from decisiondrift.report.compiler import compile_text

    try:
        result = run_review(diff_text, repo_path=repo, adr_dir=str(resolved_adr_dir), config=cfg)
        click.echo(compile_text(result))
        if result.llm_available and result.findings:
            violations = [f for f in result.findings if f.classification in ("violates", "likely_violates")]
            if violations:
                sys.exit(1)
    except Exception as e:
        click.echo(f"Error during review: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("diff_file", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option("--repo", default=".", show_default=True, help="Path to repository root")
@click.option("--from-git", is_flag=True, help="Get diff from `git diff` in the repo")
def impact(diff_file: str | None, repo: str, from_git: bool):
    """Analyze a diff and extract impacted symbols."""
    from decisiondrift.impact.service import analyze_diff

    diff_text = _read_diff(diff_file, repo, from_git)
    if diff_text is None:
        return
    if not diff_text.strip():
        click.echo("No changes detected (empty diff). Nothing to analyze.")
        return

    try:
        report = analyze_diff(diff_text, repo_path=repo)
        click.echo(report.summary())
    except Exception as e:
        click.echo(f"Error during impact analysis: {e}", err=True)
        import traceback

        traceback.print_exc()


@cli.command()
@click.argument("diff_file", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option("--repo", default=".", show_default=True, help="Path to repository root")
@click.option("--adr-dir", default=None, help="Path to ADR directory (default: <repo>/docs/adr)")
@click.option("--from-git", is_flag=True, help="Get diff from `git diff` (working tree)")
@click.option("--staged", is_flag=True, help="Get diff from `git diff --cached` (staged changes)")
@click.option(
    "--fail-on",
    default="block",
    show_default=True,
    type=click.Choice(["block", "require_approval", "warn", "info"]),
    help="Minimum action level that causes non-zero exit",
)
@click.option("--format", "output_format", default="text", show_default=True, type=click.Choice(["text", "json", "sarif", "markdown", "html"]), help="Output format")
@click.option("--output", "output_file", type=str, default=None, help="Write output to file instead of stdout")
@click.option("--file", "file_path", type=str, default=None, help="Analyze a single file (editor integration mode)")
def enforce(diff_file: str | None, repo: str, adr_dir: str | None, from_git: bool, staged: bool, fail_on: str, output_format: str, output_file: str | None, file_path: str | None):
    """Enforce ADR rules against a diff or full repo.

    Deterministic rule engine: checks dependencies, imports, paths, APIs, and configs.
    If no diff is provided and --from-git is not set, scans the full repo.
    Use --file <path> to analyze a single file (editor integration mode).
    """
    from decisiondrift.adr.loader import load_adrs
    from decisiondrift.adr.supersession import resolve_active
    from decisiondrift.config import load_config, load_custom_rules
    from decisiondrift.models.schema import ReportEnvelope
    from decisiondrift.report.formatter import format_output
    from decisiondrift.rules.engine import enforce_from_adrs

    resolved_adr_dir = Path(adr_dir) if adr_dir else Path(repo) / "docs" / "adr"
    _check_adr_dir(str(resolved_adr_dir))

    diff_text = _read_diff(diff_file, repo, from_git, staged=staged) if (diff_file or from_git or staged) else None

    try:
        decisions = load_adrs(str(resolved_adr_dir), status_filter={"accepted"})
        active = resolve_active(decisions)

        custom_rules = load_custom_rules()

        if not active and not custom_rules.rules:
            env = ReportEnvelope(
                command="enforce",
                summary={
                    "status": "no_active_adrs",
                    "message": "No accepted ADRs found. Approve proposed ADRs with:\n  decisiondrift adr approve <adr-id>\n\nOr generate new candidate ADRs with:\n  decisiondrift bootstrap <repo-path> --apply",
                },
            )
            _emit_output(format_output(env, output_format), output_file)
            return

        result = enforce_from_adrs(active, repo_path=repo, diff_text=diff_text, custom_rules=custom_rules, file_path=file_path)

        severity_order = {"block": 0, "require_approval": 1, "warn": 2, "info": 3}
        fail_level = severity_order.get(fail_on, 0)
        exit_code = 0

        findings = []
        for f in result.findings:
            findings.append({
                "adr_id": f.adr_id,
                "adr_title": f.adr_title,
                "rule_id": f.rule_id,
                "rule_type": f.rule_type.value,
                "action": f.action.value,
                "severity": f.severity,
                "match_value": f.match_value,
                "file_path": f.file_path,
                "description": f.description,
            })
            action_level = severity_order.get(f.action.value, 99)
            if action_level <= fail_level:
                exit_code = 1

        env = ReportEnvelope(
            command="enforce",
            summary={
                "status": "violations" if findings else "clean",
                "findings_count": len(findings),
                "rules_evaluated": result.rules_evaluated,
                "files_scanned": result.files_scanned,
                "exit_code": exit_code,
            },
            findings=findings,
            metadata={
                "repo": repo,
                "adr_dir": str(resolved_adr_dir),
                "diff_mode": diff_text is not None,
                "fail_on": fail_on,
            },
        )
        _emit_output(format_output(env, output_format), output_file)
        sys.exit(exit_code)

    except Exception as e:
        click.echo(f"Error during enforcement: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _emit_output(text: str, output_file: str | None = None) -> None:
    if output_file:
        Path(output_file).write_text(text)
    else:
        click.echo(text)


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository root")
@click.option("--adr-dir", default=None, help="Path to ADR directory (default: <repo>/docs/adr)")
def audit(repo: str, adr_dir: str | None):
    """Audit ADR health: drift detection, stale/expired ADRs, quality scores.

    Reuses the rule engine for drift detection — same engine, different report.
    """
    from datetime import date

    from decisiondrift.adr.loader import load_adrs
    from decisiondrift.adr.supersession import resolve_active
    from decisiondrift.rules.engine import enforce_from_adrs

    resolved_adr_dir = Path(adr_dir) if adr_dir else Path(repo) / "docs" / "adr"
    if not _check_adr_dir(str(resolved_adr_dir)):
        sys.exit(1)

    all_records = load_adrs(str(resolved_adr_dir))
    accepted = [r for r in all_records if r.status == "accepted"]
    proposed = [r for r in all_records if r.status == "proposed"]
    active = resolve_active(accepted)

    today = date.today()
    exit_code = 0

    click.echo(f"\nADR Audit — {today}")
    click.echo(f"{'─' * 50}")
    click.echo("")
    click.echo(f"  Total ADRs:     {len(all_records)}")
    click.echo(f"  Accepted:       {len(accepted)}")
    click.echo(f"  Proposed:       {len(proposed)}")
    click.echo(f"  Rejected:       {len([r for r in all_records if r.status == 'rejected'])}")
    click.echo("")

    # Expired ADRs
    expired = [r for r in active if r.expires_after and r.expires_after < today.isoformat()]
    if expired:
        click.echo(f"  ⚠ Expired ADRs: {len(expired)}")
        for r in expired:
            click.echo(f"    {r.id}: {r.title} (expired {r.expires_after})")
        click.echo("")
        exit_code = 1

    # Stale ADRs (past review_after)
    stale = [r for r in active if r.review_after and r.review_after < today.isoformat()]
    if stale:
        click.echo(f"  ⚠ Stale ADRs (past review date): {len(stale)}")
        for r in stale:
            click.echo(f"    {r.id}: {r.title} (review by {r.review_after})")
        click.echo("")
        exit_code = 1

    # Unreviewed ADRs
    if proposed:
        click.echo(f"  ⚠ Unreviewed ADRs: {len(proposed)}")
        for r in proposed:
            click.echo(f"    {r.id}: {r.title}")
        click.echo("")
        exit_code = 1

    # Drift detection (reuses rule engine)
    if active:
        click.echo("  Checking ADR drift...")
        drift_result = enforce_from_adrs(active, repo_path=repo)
        if drift_result.findings:
            click.echo(f"  ⚠ ADR Drift: {len(drift_result.findings)}")
            for f in drift_result.findings:
                click.echo(f"    {f.adr_id}: {f.match_value} found in repo ({f.rule_type.value})")
            exit_code = 1
        else:
            click.echo("  ✓ No ADR drift detected.")
        click.echo("")

    # ADR Coverage (via Bootstrap V3)
    click.echo("  Checking ADR coverage...")
    try:
        from decisiondrift.bootstrap.v3 import build_repository_model

        model = build_repository_model(repo)
        detected_techs = {
            t.name.lower() for t in model.technologies if t.evidence_level.value in ("moderate", "strong")
        }
        governed = {r.title.lower() for r in active}
        for r in active:
            if r.keywords:
                governed.update(k.lower() for k in r.keywords)
        covered = detected_techs & governed
        missing_techs = detected_techs - governed

        if detected_techs:
            click.echo("")
            click.echo(f"  Detected Technologies:   {len(detected_techs)}")
            click.echo(f"  Governed:                {len(covered)}")
            click.echo(f"  Coverage:                {len(covered) / len(detected_techs):.0%}")
            click.echo("")

            if missing_techs:
                click.echo("  Missing Governance:")
                for t in sorted(missing_techs):
                    click.echo(f"    ⚠ {t}")
                click.echo("")
        else:
            click.echo("  No technologies detected.")
            click.echo("")
    except Exception as e:
        click.echo(f"  (Coverage analysis skipped: {e})")
        click.echo("")

    # Quality scores
    click.echo("  ADR Quality Scores:")
    for r in active:
        score, missing, deductions = _adr_quality_score(r)
        click.echo(f"    {r.id}: {score}/100  ({r.title})")
        if missing:
            click.echo("          Missing:")
            for field, points in deductions:
                click.echo(f"            - {field} ({-points})")
        else:
            click.echo("          ✓ All recommended fields present")

    sys.exit(exit_code)


def _adr_quality_score(record) -> tuple[int, list[str], list[tuple[str, int]]]:
    field_weights = [
        ("rationale", 20, bool(record.rationale) and record.rationale.strip() not in ("", "#")),
        ("prohibitions", 15, bool(record.prohibitions)),
        ("keywords", 10, bool(record.keywords)),
        ("exceptions", 10, bool(record.exceptions)),
        ("alternatives_rejected", 15, bool(record.alternatives_rejected)),
        ("owner", 10, bool(record.owner)),
        ("review_after", 10, bool(record.review_after)),
        ("expires_after", 10, bool(record.expires_after)),
    ]
    missing = []
    deductions = []
    score = 100
    for field, weight, present in field_weights:
        if not present:
            missing.append(field)
            deductions.append((field, weight))
            score -= weight
    score = max(0, score)
    return score, missing, deductions


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository root")
@click.option("--adr-dir", default=None, help="Path to ADR directory")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), help="Output format")
def doctor(repo: str, adr_dir: str | None, output_format: str):
    """Health diagnostics: check CLI, config, registry, tree-sitter, and LLM setup.

    Returns a structured health report. Exit code 0 if all checks pass, 1 otherwise.
    """
    from decisiondrift import __version__
    from decisiondrift.models.schema import ReportEnvelope

    output_format = output_format or "text"
    resolved_adr_dir = Path(adr_dir) if adr_dir else Path(repo) / "docs" / "adr"

    checks: dict[str, dict] = {}

    # 1. CLI version
    checks["cli_version"] = {
        "name": "CLI version",
        "status": "ok",
        "value": __version__,
    }

    # 2. Config file
    from decisiondrift.config import find_config, load_config

    cfg_path = find_config(Path(repo))
    if cfg_path and cfg_path.exists():
        checks["config"] = {
            "name": "Config file",
            "status": "ok",
            "value": str(cfg_path),
        }
        try:
            load_config(cfg_path)
        except Exception as e:
            checks["config"] = {
                "name": "Config file",
                "status": "error",
                "value": f"Parse error: {e}",
            }
    else:
        checks["config"] = {
            "name": "Config file",
            "status": "warn",
            "value": "Not found (optional — uses defaults)",
        }

    # 3. Registry
    try:
        from decisiondrift.bootstrap.registry import load_registry

        reg = load_registry()
        tech_count = sum(1 for n, p in reg.technologies.items() if n == p.name)
        checks["registry"] = {
            "name": "Technology registry",
            "status": "ok",
            "value": f"{tech_count} technology profiles loaded",
        }
    except Exception as e:
        checks["registry"] = {
            "name": "Technology registry",
            "status": "error",
            "value": str(e),
        }

    # 4. Tree-sitter
    from decisiondrift.impact.ast_treesitter import HAS_TREESITTER

    checks["tree_sitter"] = {
        "name": "Tree-sitter",
        "status": "ok" if HAS_TREESITTER else "warn",
        "value": "Available" if HAS_TREESITTER else "Not installed (run `pip install decisiondrift[ast]`)",
    }

    # 5. Embeddings
    try:
        from decisiondrift.retrieval.embedding import HAS_FASTEMBED
    except ImportError:
        HAS_FASTEMBED = False
    checks["embeddings"] = {
        "name": "Embeddings",
        "status": "ok" if HAS_FASTEMBED else "warn",
        "value": "Available" if HAS_FASTEMBED else "Not installed (run `pip install decisiondrift[embeddings]`)",
    }

    # 6. ADR directory
    if resolved_adr_dir.exists():
        adr_files = list(resolved_adr_dir.glob("ADR-*.md"))
        checks["adr_dir"] = {
            "name": "ADR directory",
            "status": "ok",
            "value": f"{resolved_adr_dir} ({len(adr_files)} ADRs)",
        }
    else:
        checks["adr_dir"] = {
            "name": "ADR directory",
            "status": "warn",
            "value": f"Not found at {resolved_adr_dir}",
        }

    # 7. LLM (optional)
    cfg = load_config()
    api_key = cfg["llm"].get("api_key")
    if api_key:
        try:
            from decisiondrift.llm.client import LLMClient
            client = LLMClient(model=cfg["llm"]["model"], api_key=api_key, base_url=cfg["llm"].get("base_url"))
            checks["llm"] = {
                "name": "LLM",
                "status": "ok" if client.available() else "error",
                "value": f"Model: {cfg['llm']['model']}" if client.available() else "API key configured but not responding",
            }
        except Exception as e:
            checks["llm"] = {
                "name": "LLM",
                "status": "error",
                "value": str(e),
            }
    else:
        checks["llm"] = {
            "name": "LLM",
            "status": "warn",
            "value": "Not configured (required only for `review` and `ingest`)",
        }

    # Determine overall status
    statuses = [c["status"] for c in checks.values()]
    overall = "ok"
    if "error" in statuses:
        overall = "error"
    elif "warn" in statuses:
        overall = "warn"

    if output_format == "json":
        env = ReportEnvelope(
            command="doctor",
            summary={
                "status": overall,
                "findings_count": len(checks),
            },
            metadata={"checks": checks},
        )
        from decisiondrift.report.formatter import format_output
        click.echo(format_output(env, "json"))
    else:
        click.echo("\nDecisionDrift Health Report")
        click.echo("=" * 40)
        for key, check in checks.items():
            icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(check["status"], "?")
            click.echo(f"  {icon} {check['name']}: {check['value']}")
        click.echo("")

    sys.exit(0 if overall == "ok" else 1)


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository root")
@click.option("--adr-dir", default=None, help="Path to ADR directory (default: <repo>/docs/adr)")
@click.option("--install", is_flag=True, help="Install the pre-commit hook")
@click.option("--uninstall", is_flag=True, help="Remove the pre-commit hook")
def guard(repo: str, adr_dir: str | None, install: bool, uninstall: bool):
    """Pre-commit hook: enforce ADRs before commit.

    Run manually or install as a git pre-commit hook with --install.
    """
    hook_path = Path(repo) / ".git" / "hooks" / "pre-commit"

    if uninstall:
        if hook_path.exists():
            hook_path.unlink()
            click.echo(f"Pre-commit hook removed from {hook_path}")
        else:
            click.echo("No pre-commit hook found. Nothing to remove.")
        return

    if install:
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_content = "#!/bin/sh\nexec decisiondrift enforce --staged --repo " + shlex.quote(repo)
        if adr_dir:
            hook_content += " --adr-dir " + shlex.quote(adr_dir)
        hook_path.write_text(hook_content.strip() + "\n")
        hook_path.chmod(0o755)
        click.echo(f"Pre-commit hook installed at {hook_path}")
        return

    click.echo("Running guard (pre-commit enforcement)...")
    from click.testing import CliRunner

    runner = CliRunner()
    args = ["enforce", "--staged", "--repo", repo]
    if adr_dir:
        args.extend(["--adr-dir", adr_dir])
    result = runner.invoke(cli, args)
    click.echo(result.output)
    if result.exit_code != 0:
        sys.exit(result.exit_code)


def _print_adr_table(records):
    header = f"{'ID':<12} {'Title':<50} {'Status':<12} {'Source':<12} {'Severity':<10}"
    sep = "-" * len(header)
    print(header)
    print(sep)
    for r in records:
        print(f"{r.id:<12} {r.title[:48]:<50} {r.status:<12} {r.source:<12} {r.severity:<10}")


if __name__ == "__main__":
    cli()
