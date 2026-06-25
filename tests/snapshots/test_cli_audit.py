from __future__ import annotations

import re
from pathlib import Path

from click.testing import CliRunner

from decisiondrift.adr.writer import write_adr
from decisiondrift.cli import cli


def _normalize_output(output: str) -> str:
    output = re.sub(r"ADR-\d{4}", "ADR-XXXX", output)
    output = re.sub(r"/tmp/[^\s]+", "/tmp/...", output)
    output = re.sub(r"\d{4}-\d{2}-\d{2}", "YYYY-MM-DD", output)
    return output


class TestCLIAuditSnapshot:
    def test_audit_help(self, snapshot):
        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "--help"])
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_audit_with_adrs(self, fastapi_repo: Path, snapshot):
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
                "rationale": "FastAPI is the chosen HTTP framework.",
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
        normalized = _normalize_output(result.output)
        assert snapshot == normalized
