from __future__ import annotations

import re
from pathlib import Path

from click.testing import CliRunner

from decisiondrift.cli import cli


def _normalize_output(output: str) -> str:
    output = re.sub(r"ADR-\d{4}", "ADR-XXXX", output)
    output = re.sub(r"/tmp/[^\s]+", "/tmp/...", output)
    output = re.sub(r"\d{4}-\d{2}-\d{2}", "YYYY-MM-DD", output)
    return output


class TestCLIBootstrapSnapshot:
    def test_bootstrap_help(self, snapshot):
        runner = CliRunner()
        result = runner.invoke(cli, ["bootstrap", "--help"])
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_bootstrap_dry_run_flask(self, flask_repo: Path, snapshot):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                str(flask_repo),
                "--adr-dir",
                str(flask_repo / "docs/adr"),
            ],
        )
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_bootstrap_dry_run_fastapi(self, fastapi_repo: Path, snapshot):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                str(fastapi_repo),
                "--adr-dir",
                str(fastapi_repo / "docs/adr"),
            ],
        )
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_bootstrap_empty_repo(self, empty_repo: Path, snapshot):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                str(empty_repo),
                "--adr-dir",
                str(empty_repo / "docs/adr"),
            ],
        )
        normalized = _normalize_output(result.output)
        assert snapshot == normalized
