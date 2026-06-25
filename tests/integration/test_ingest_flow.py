from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from decisiondrift.cli import cli
from tests.conftest import MockLLMClient


class TestIngestFlow:
    def test_ingest_no_llm_key_shows_error(self, tmp_path: Path):
        notes = tmp_path / "notes.md"
        notes.write_text("## Meeting\nDecision: Use Redis.\n")
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
        assert result.exit_code == 0
        assert "API key not configured" in result.output

    def test_ingest_nonexistent_file(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "ingest",
                str(tmp_path / "nonexistent.md"),
                "--adr-dir",
                str(tmp_path / "adr"),
            ],
        )
        assert result.exit_code == 2

    def test_ingest_empty_file(self, tmp_path: Path):
        notes = tmp_path / "notes.md"
        notes.write_text("")
        runner = CliRunner()

        mock_client = MockLLMClient()
        mock_client.set_available(True)

        with patch("decisiondrift.ingest.service.LLMClient", return_value=mock_client):
            result = runner.invoke(
                cli,
                [
                    "ingest",
                    str(notes),
                    "--adr-dir",
                    str(tmp_path / "adr"),
                ],
            )
        assert result.exit_code == 0
        assert "No content found" in result.output

    def test_ingest_creates_adr_files(self, tmp_path: Path):
        notes = tmp_path / "notes.md"
        notes.write_text("## Meeting\n\nDecision:\nUse Redis for caching.\n\nDecision:\nUse Celery for async jobs.\n")
        adr_dir = tmp_path / "adr"
        runner = CliRunner()

        mock_client = MockLLMClient(
            responses=[
                {
                    "decisions": [
                        {
                            "title": "Use Redis for Caching",
                            "decision": "Use Redis for caching.",
                            "rationale": "Redis provides fast caching.",
                            "confidence": "high",
                        }
                    ]
                },
                {
                    "decisions": [
                        {
                            "title": "Use Celery for Async Jobs",
                            "decision": "Use Celery for async jobs.",
                            "rationale": "Celery handles background jobs.",
                            "confidence": "high",
                        }
                    ]
                },
            ]
        )
        mock_client.set_available(True)

        with patch("decisiondrift.ingest.service.LLMClient", return_value=mock_client):
            result = runner.invoke(
                cli,
                [
                    "ingest",
                    str(notes),
                    "--adr-dir",
                    str(adr_dir),
                ],
            )

        assert result.exit_code == 0
        adr_files = list(adr_dir.glob("ADR-*.md"))
        assert len(adr_files) >= 1
