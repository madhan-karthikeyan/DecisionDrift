from click.testing import CliRunner

from decisiondrift.cli import cli


def test_enforce_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["enforce", "--help"])
    assert result.exit_code == 0
    assert "Enforce ADR rules" in result.output


def test_enforce_no_adrs(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["enforce", "--repo", str(tmp_path), "--adr-dir", str(tmp_path / "adr")])
    assert result.exit_code == 0
    assert (
        "ADR directory not found" in result.output
        or "no ADR files found" in result.output
        or "No accepted ADRs found" in result.output
    )
