from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from decisiondrift.ingest.segmenter import segment_notes
from decisiondrift.ingest.service import run_ingest


class TestIngestSegmentation:
    def test_single_segment(self):
        content = "Decision:\nUse Redis for caching."
        segments = segment_notes(content)
        assert len(segments) == 1

    def test_multiple_segments_by_heading(self):
        content = "## Meeting\nDecision: Use Redis.\n## Notes\nDecision: Use Celery.\n"
        segments = segment_notes(content)
        assert len(segments) >= 2

    def test_empty_content_returns_empty(self):
        assert segment_notes("") == []
        assert segment_notes("   ") == []
        assert segment_notes("\n\n\n") == []

    def test_markdown_input(self):
        content = "# Team Sync\n\nWe decided on **Redis** for caching.\n\n## Action Items\n\nNone.\n"
        segments = segment_notes(content)
        assert len(segments) >= 1

    def test_text_input_no_headings(self):
        content = "Decision: Use Redis.\nDecision: Use Celery.\n"
        segments = segment_notes(content)
        assert len(segments) == 1 or len(segments) == 2


class TestIngestService:
    def test_run_ingest_missing_file(self, tmp_path: Path):
        adr_dir = tmp_path / "adr"
        with patch("decisiondrift.ingest.service.click.echo") as mock_echo:
            run_ingest(str(tmp_path / "nonexistent.md"), str(adr_dir))
            mock_echo.assert_any_call(
                f"Error: file not found: {tmp_path / 'nonexistent.md'}",
                err=True,
            )

    @patch("decisiondrift.ingest.service.LLMClient")
    def test_run_ingest_no_llm_key(self, mock_llm, tmp_path: Path):
        notes_file = tmp_path / "notes.md"
        notes_file.write_text("Decision: Use Redis.")
        adr_dir = tmp_path / "adr"
        mock_client = mock_llm.return_value
        mock_client.available.return_value = False
        with patch("decisiondrift.ingest.service.click.echo") as mock_echo:
            run_ingest(str(notes_file), str(adr_dir))
            mock_echo.assert_any_call(
                "Error: LLM API key not configured. Set DECISIONDRIFT_LLM_API_KEY.",
                err=True,
            )

    @patch("decisiondrift.ingest.service.LLMClient")
    def test_run_ingest_processes_segments(self, mock_llm, tmp_path: Path):
        notes_file = tmp_path / "notes.md"
        notes_file.write_text(
            "## Meeting\n\nDecision:\nUse Redis for caching.\n\n## Discussion\n\nDecision:\nUse Celery for async tasks.\n"
        )
        adr_dir = tmp_path / "adr"
        mock_client = mock_llm.return_value
        mock_client.available.return_value = True

        call_count = 0

        def side_effect(text, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "decisions": [
                        {
                            "title": "Use Redis for Caching",
                            "decision": "Use Redis for caching.",
                            "rationale": "Redis provides fast in-memory caching.",
                            "confidence": "high",
                        }
                    ]
                }
            return {
                "decisions": [
                    {
                        "title": "Use Celery for Async Tasks",
                        "decision": "Use Celery for async tasks.",
                        "rationale": "Celery handles background jobs.",
                        "confidence": "high",
                    }
                ]
            }

        mock_client.complete_json.side_effect = side_effect

        with patch("decisiondrift.ingest.service.click.echo"):
            run_ingest(str(notes_file), str(adr_dir))

        assert len(list(adr_dir.glob("ADR-*.md"))) >= 1

    @patch("decisiondrift.ingest.service.LLMClient")
    def test_run_ingest_duplicate_detection(self, mock_llm, tmp_path: Path):
        notes_file = tmp_path / "notes.md"
        notes_file.write_text("Decision:\nUse Redis for caching.\n\nDecision:\nUse Redis for caching.\n")
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "ADR-0001.md").write_text(
            "---\nid: ADR-0001\ntitle: Use Redis for Caching\nstatus: accepted\nseverity: medium\nsource: manual\n---\n"
        )
        mock_client = mock_llm.return_value
        mock_client.available.return_value = True
        mock_client.complete_json.return_value = {
            "decisions": [
                {
                    "title": "Use Redis for Caching",
                    "decision": "Use Redis for caching.",
                    "rationale": "Redis provides fast in-memory caching.",
                    "confidence": "high",
                }
            ]
        }
        with patch("decisiondrift.ingest.service.click.echo") as mock_echo:
            run_ingest(str(notes_file), str(adr_dir))
        mock_echo.assert_any_call("  Skipping 'Use Redis for Caching': already documented as ADR-0001")

    def test_segment_empty_content(self):
        assert segment_notes("") == []

    def test_segment_only_whitespace(self):
        assert segment_notes("   \n  \n  ") == []

    @patch("decisiondrift.ingest.service.LLMClient")
    def test_llm_response_error_handled_gracefully(self, mock_llm, tmp_path: Path):
        notes_file = tmp_path / "notes.md"
        notes_file.write_text("Decision:\nUse Redis.\n")
        adr_dir = tmp_path / "adr"
        mock_client = mock_llm.return_value
        mock_client.available.return_value = True
        from decisiondrift.llm.client import LLMResponseError

        mock_client.complete_json.side_effect = LLMResponseError("API error")
        with patch("decisiondrift.ingest.service.click.echo") as mock_echo:
            run_ingest(str(notes_file), str(adr_dir))
            mock_echo.assert_any_call("No new decisions extracted.")
