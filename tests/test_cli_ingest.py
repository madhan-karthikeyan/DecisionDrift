from click.testing import CliRunner

from decisiondrift.cli import cli


def test_ingest_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", "--help"])
    assert result.exit_code == 0
    assert "Generate candidate ADRs from free-text notes" in result.output


def test_ingest_missing_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", "does_not_exist.md"])
    assert result.exit_code != 0
    assert "No such file or directory" in result.output or "does not exist" in result.output


def test_ingest_empty_file(tmp_path):
    file_path = tmp_path / "notes.md"
    file_path.write_text("")

    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", str(file_path)])
    assert result.exit_code == 0
    assert "No content found to ingest" in result.output
