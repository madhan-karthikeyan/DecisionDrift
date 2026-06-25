from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import click

from decisiondrift import __version__
from decisiondrift.adr_manager.commands import approve_adr, list_adrs, reject_adr


@click.group()
@click.version_option(version=__version__, prog_name="decisiondrift")
def cli():
    pass


@cli.group()
def adr():
    """Manage ADR lifecycle."""


@adr.command("list")
@click.option("--status", type=str, help="Filter by status (proposed, accepted, rejected, deprecated, superseded)")
@click.option("--source", type=str, help="Filter by source (manual, bootstrap, ingest)")
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def adr_list(status: str | None, source: str | None, adr_dir: str):
    """List ADRs with optional status/source filters."""
    records = list_adrs(adr_dir, status=status, source=source)
    if not records:
        click.echo("No ADRs found.")
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
@click.option("--llm", is_flag=True, help="Deprecated; Bootstrap V3 always uses deterministic inference")
def bootstrap(path: str, adr_dir: str, dry_run: bool, apply: bool, min_confidence: str, llm: bool):
    """Generate candidate ADRs from repository structure.

    Bootstrap V3 uses deterministic evidence collection, repository modeling,
    governance candidate discovery, and enforceability analysis.
    """
    from decisiondrift.bootstrap.bootstrapper import bootstrap as run_bootstrap

    if apply:
        dry_run = False

    try:
        run_bootstrap(path, adr_dir=adr_dir, dry_run=dry_run, min_confidence=min_confidence, use_llm=llm)
    except Exception as e:
        click.echo(f"Error during bootstrap: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option("--adr-dir", default="docs/adr", show_default=True, help="Path to ADR directory")
def ingest(file: str, adr_dir: str):
    """Generate candidate ADRs from free-text notes."""
    from decisiondrift.ingest.service import run_ingest

    run_ingest(file, adr_dir)


def _read_diff(diff_file: str | None, repo: str, from_git: bool) -> str | None:
    if from_git:
        try:
            result = subprocess.run(
                ["git", "diff"],
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
def review(diff_file: str | None, repo: str, adr_dir: str | None, from_git: bool):
    """Evaluate changes against accepted ADRs."""
    from decisiondrift.config import load_config
    from decisiondrift.review.service import run_review

    cfg = load_config()
    resolved_adr_dir = Path(adr_dir) if adr_dir else Path(repo) / "docs" / "adr"

    diff_text = _read_diff(diff_file, repo, from_git)
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
@click.option("--from-git", is_flag=True, help="Get diff from `git diff` in the repo")
@click.option(
    "--fail-on",
    default="block",
    show_default=True,
    type=click.Choice(["block", "require_approval", "warn", "info"]),
    help="Minimum action level that causes non-zero exit",
)
def enforce(diff_file: str | None, repo: str, adr_dir: str | None, from_git: bool, fail_on: str):
    """Enforce ADR rules against a diff or full repo.

    Deterministic rule engine: checks dependencies, imports, paths, APIs, and configs.
    If no diff is provided and --from-git is not set, scans the full repo.
    """
    from decisiondrift.adr.loader import load_adrs
    from decisiondrift.adr.supersession import resolve_active
    from decisiondrift.rules.engine import enforce_from_adrs

    resolved_adr_dir = Path(adr_dir) if adr_dir else Path(repo) / "docs" / "adr"
    _check_adr_dir(str(resolved_adr_dir))

    diff_text = _read_diff(diff_file, repo, from_git) if (diff_file or from_git) else None

    try:
        decisions = load_adrs(str(resolved_adr_dir), status_filter={"accepted"})
        active = resolve_active(decisions)
        if not active:
            click.echo("No accepted ADRs found. No rules to enforce.")
            return

        result = enforce_from_adrs(active, repo_path=repo, diff_text=diff_text)

        if not result.findings:
            click.echo("No violations found.")
            return

        severity_order = {"block": 0, "require_approval": 1, "warn": 2, "info": 3}
        fail_level = severity_order.get(fail_on, 0)
        exit_code = 0

        click.echo("")
        for f in result.findings:
            action_label = f.action.value.upper()
            click.echo(f"  [{action_label}] {f.adr_id} ({f.rule_type.value})")
            click.echo(f"           Match: {f.match_value}")
            if f.file_path:
                click.echo(f"           File: {f.file_path}")
            if f.description:
                click.echo(f"           {f.description}")
            click.echo("")

            action_level = severity_order.get(f.action.value, 99)
            if action_level <= fail_level:
                exit_code = 1

        click.echo("---")
        click.echo(
            f"{len(result.findings)} finding(s), "
            f"{result.rules_evaluated} rule(s) evaluated, "
            f"{result.files_scanned} file(s) scanned."
        )
        sys.exit(exit_code)

    except Exception as e:
        click.echo(f"Error during enforcement: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)


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
@click.option("--adr-dir", default=None, help="Path to ADR directory (default: <repo>/docs/adr)")
@click.option("--install", is_flag=True, help="Install the pre-commit hook")
def guard(repo: str, adr_dir: str | None, install: bool):
    """Pre-commit hook: enforce ADRs before commit.

    Run manually or install as a git pre-commit hook with --install.
    """
    if install:
        hook_path = Path(repo) / ".git" / "hooks" / "pre-commit"
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        args = [shlex.quote(repo)]
        if adr_dir:
            args.extend(["--adr-dir", shlex.quote(adr_dir)])
        hook_content = "#!/bin/sh\nexec decisiondrift enforce --from-git --repo " + " ".join(args)
        hook_path.write_text(hook_content.strip())
        hook_path.chmod(0o755)
        click.echo(f"Pre-commit hook installed at {hook_path}")
        return

    click.echo("Running guard (pre-commit enforcement)...")
    from click.testing import CliRunner

    runner = CliRunner()
    args = ["enforce", "--from-git", "--repo", repo]
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
