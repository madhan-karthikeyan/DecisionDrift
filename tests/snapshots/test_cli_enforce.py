from __future__ import annotations

import re
from pathlib import Path

from click.testing import CliRunner

from decisiondrift.adr.writer import write_adr
from decisiondrift.cli import cli


def _normalize_output(output: str) -> str:
    output = re.sub(r"ADR-\d{4}", "ADR-XXXX", output)
    output = re.sub(r"/tmp/[^\s]+", "/tmp/...", output)
    return output


class TestCLIEnforceSnapshot:
    def test_enforce_help(self, snapshot):
        runner = CliRunner()
        result = runner.invoke(cli, ["enforce", "--help"])
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_enforce_no_violations(self, fastapi_repo: Path, snapshot):
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
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_enforce_with_violation(self, tmp_path: Path, snapshot):
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
        normalized = _normalize_output(result.output)
        assert snapshot == normalized
