from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from decisiondrift.adr.writer import write_adr
from decisiondrift.cli import cli


class TestEnforceFlow:
    def test_enforce_no_adr_directory(self, empty_repo: Path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "enforce",
                "--repo",
                str(empty_repo),
                "--adr-dir",
                str(empty_repo / "docs/adr"),
            ],
        )
        assert result.exit_code == 0
        assert "ADR directory not found" in result.output

    def test_enforce_no_accepted_adrs(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI",
                "status": "proposed",
                "severity": "medium",
            },
            "## Context\n\nTest.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "enforce",
                "--repo",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0
        assert "No accepted ADRs found" in result.output

    def test_enforce_no_violations(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI for HTTP APIs",
                "status": "accepted",
                "severity": "high",
                "prohibitions": ["flask", "django"],
                "keywords": ["fastapi"],
            },
            "## Context\n\nFastAPI is used.\n",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "enforce",
                "--repo",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0

    def test_enforce_with_violations(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI for HTTP APIs",
                "status": "accepted",
                "severity": "high",
                "prohibitions": ["flask"],
                "keywords": ["fastapi"],
            },
            "## Context\n\nFastAPI is used.\n",
        )
        (tmp_path / "requirements.txt").write_text("flask==3.0\n")
        (tmp_path / "app.py").write_text("import flask\n")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "enforce",
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 1
        assert "BLOCK" in result.output or "finding" in result.output

    def test_enforce_with_diff(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI for HTTP APIs",
                "status": "accepted",
                "severity": "high",
                "prohibitions": ["flask"],
                "keywords": ["fastapi"],
            },
            "## Context\n\nFastAPI is used.\n",
        )
        (tmp_path / "requirements.txt").write_text("flask==3.0\n")
        diff_file = tmp_path / "changes.diff"
        diff_file.write_text(
            "diff --git a/requirements.txt b/requirements.txt\n--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+flask==3.0\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "enforce",
                str(diff_file),
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 1
        assert "BLOCK" in result.output

    def test_enforce_with_fail_on_config(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use FastAPI for HTTP APIs",
                "status": "accepted",
                "severity": "high",
                "confidence": "medium",
                "prohibitions": ["flask"],
                "keywords": ["fastapi"],
            },
            "## Context\n\nFastAPI is used.\n",
        )
        (tmp_path / "requirements.txt").write_text("flask==3.0\n")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "enforce",
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
                "--fail-on",
                "warn",
            ],
        )
        assert result.exit_code == 1
