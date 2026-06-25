from click.testing import CliRunner

from decisiondrift.cli import cli


def test_bootstrap_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["bootstrap", "--help"])
    assert result.exit_code == 0
    assert "Generate candidate ADRs" in result.output


def test_bootstrap_dry_run(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("import fastapi\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["bootstrap", str(tmp_path), "--adr-dir", str(tmp_path / "adr")])
    assert result.exit_code == 0
    assert "Repository Summary" in result.output or "No technologies detected" in result.output
