from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from decisiondrift.cli import cli


def _normalize_output(output: str) -> str:
    output = re.sub(r"ADR-\d{4}", "ADR-XXXX", output)
    output = re.sub(r"/tmp/[^\s]+", "/tmp/...", output)
    return output


class TestCLIIngestSnapshot:
    def test_ingest_help(self, snapshot):
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", "--help"])
        normalized = _normalize_output(result.output)
        assert snapshot == normalized

    def test_ingest_no_api_key(self, tmp_path: Path, snapshot):
        notes = tmp_path / "notes.md"
        notes.write_text("## Decision\nUse Redis.\n")
        runner = CliRunner()
        with patch.dict("os.environ", clear=True):
            result = runner.invoke(
                cli,
                [
                    "ingest",
                    str(notes),
                    "--adr-dir",
                    str(tmp_path / "adr"),
                ],
            )
        normalized = _normalize_output(result.output)
        assert snapshot == normalized
