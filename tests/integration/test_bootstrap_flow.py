from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from decisiondrift.cli import cli


class TestBootstrapFlow:
    def test_bootstrap_flask_repo(self, flask_repo: Path):
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
        assert result.exit_code == 0
        assert "Repository Summary" in result.output

    def test_bootstrap_with_apply_creates_adrs(self, flask_repo: Path):
        adr_dir = flask_repo / "docs/adr"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                str(flask_repo),
                "--adr-dir",
                str(adr_dir),
                "--apply",
            ],
        )
        assert result.exit_code == 0
        adr_files = list(adr_dir.glob("ADR-*.md"))
        assert len(adr_files) > 0

    def test_bootstrap_adrs_have_metadata(self, flask_repo: Path):
        adr_dir = flask_repo / "docs/adr"
        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "bootstrap",
                str(flask_repo),
                "--adr-dir",
                str(adr_dir),
                "--apply",
            ],
        )
        assert adr_dir.exists()
        md_files = list(sorted(adr_dir.glob("ADR-*.md")))
        assert len(md_files) > 0
        for f in md_files:
            content = f.read_text()
            assert "---" in content
            assert "id:" in content
            assert "title:" in content
            assert "status:" in content
            assert "severity:" in content

    def test_bootstrap_ids_allocated_sequentially(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs/adr"
        runner = CliRunner()
        runner.invoke(
            cli,
            [
                "bootstrap",
                str(fastapi_repo),
                "--adr-dir",
                str(adr_dir),
                "--apply",
            ],
        )
        ids = []
        for f in sorted(adr_dir.glob("ADR-*.md")):
            from decisiondrift.adr.parser import parse_adr_file

            record = parse_adr_file(f)
            if record:
                ids.append(record.id)
        if len(ids) > 1:
            nums = [int(i.split("-")[1]) for i in ids]
            assert nums == sorted(nums)

    def test_bootstrap_empty_repo(self, empty_repo: Path):
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
        assert result.exit_code == 0
        assert "No technologies detected" in result.output

    def test_bootstrap_dedup_with_existing_adrs(self, flask_repo: Path):
        adr_dir = flask_repo / "docs/adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "ADR-0001.md").write_text(
            "---\nid: ADR-0001\ntitle: Use Flask as Web Framework\n"
            "status: accepted\nseverity: high\nsource: manual\n"
            "keywords: [flask, framework]\n---\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                str(flask_repo),
                "--adr-dir",
                str(adr_dir),
                "--apply",
            ],
        )
        assert result.exit_code == 0

    def test_bootstrap_with_max_candidates(self, flask_repo: Path):
        adr_dir = flask_repo / "docs/adr"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                str(flask_repo),
                "--adr-dir",
                str(adr_dir),
                "--max-candidates",
                "1",
            ],
        )
        assert result.exit_code == 0
