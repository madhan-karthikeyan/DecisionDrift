from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from decisiondrift.adr.writer import write_adr
from decisiondrift.cli import cli


class TestAuditFlow:
    def test_audit_no_adr_directory(self, empty_repo: Path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "audit",
                "--repo",
                str(empty_repo),
                "--adr-dir",
                str(empty_repo / "docs/adr"),
            ],
        )
        assert result.exit_code == 1
        assert "ADR directory not found" in result.output

    def test_audit_with_accepted_adrs(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI for HTTP APIs",
                "status": "accepted",
                "severity": "high",
                "source": "bootstrap",
                "prohibitions": ["flask", "django"],
                "keywords": ["fastapi", "framework"],
            },
            "## Context\n\nFastAPI is used.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "audit",
                "--repo",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0
        assert "ADR Audit" in result.output

    def test_audit_shows_stale_adr(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI",
                "status": "accepted",
                "severity": "high",
                "review_after": "2020-01-01",
            },
            "## Context\n\nFastAPI is used.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "audit",
                "--repo",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 1
        assert "Stale" in result.output or "past review date" in result.output

    def test_audit_shows_quality_scores(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI for HTTP APIs",
                "status": "accepted",
                "severity": "high",
                "source": "bootstrap",
                "rationale": "FastAPI is used for HTTP APIs.",
                "prohibitions": ["flask"],
                "keywords": ["fastapi"],
                "owner": "team",
                "review_after": "2025-01-01",
            },
            "## Context\n\nFastAPI is the chosen framework.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "audit",
                "--repo",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 1
        assert "ADR Quality Scores" in result.output

    def test_audit_drift_detection(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use Flask as Web Framework",
                "status": "accepted",
                "severity": "high",
                "source": "manual",
                "prohibitions": ["fastapi"],
                "keywords": ["flask"],
            },
            "## Context\n\nFlask is used.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "audit",
                "--repo",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 1

    def test_audit_no_adrs_shows_count(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Test ADR",
                "status": "accepted",
                "severity": "medium",
            },
            "## Context\n\nTest.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "audit",
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0
