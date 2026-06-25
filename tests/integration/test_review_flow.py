from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from decisiondrift.adr.writer import write_adr
from decisiondrift.cli import cli


class TestReviewFlow:
    def test_review_no_diff(self, fastapi_repo: Path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "review",
                "--repo",
                str(fastapi_repo),
            ],
        )
        assert result.exit_code == 0

    def test_review_no_accepted_adrs(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Proposed Test",
                "status": "proposed",
                "severity": "medium",
            },
            "## Context\n\nTest.\n",
        )
        diff_file = tmp_path / "changes.diff"
        diff_file.write_text(
            "diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1 @@\n+def new_func():\n    pass\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "review",
                str(diff_file),
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0

    def test_review_with_accepted_adr(self, tmp_path: Path):
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
        diff_file = tmp_path / "changes.diff"
        diff_file.write_text(
            "diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1 @@\n+def new_func():\n    pass\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "review",
                str(diff_file),
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0

    def test_review_no_diff_shows_prompt(self, fastapi_repo: Path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "review",
                "--repo",
                str(fastapi_repo),
            ],
        )
        assert result.exit_code == 0


class TestReviewWithProposedRejected:
    def test_review_rejected_adr_not_considered(self, tmp_path: Path):
        adr_dir = tmp_path / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        write_adr(
            adr_dir / "ADR-0001.md",
            {
                "id": "ADR-0001",
                "title": "Use Flask",
                "status": "rejected",
                "severity": "medium",
            },
            "## Context\n\nRejected.\n",
        )
        runner = CliRunner()
        diff_file = tmp_path / "changes.diff"
        diff_file.write_text(
            "diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1 @@\n+def new_func():\n    pass\n"
        )
        result = runner.invoke(
            cli,
            [
                "review",
                str(diff_file),
                "--repo",
                str(tmp_path),
                "--adr-dir",
                str(adr_dir),
            ],
        )
        assert result.exit_code == 0
