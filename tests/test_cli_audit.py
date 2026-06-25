from click.testing import CliRunner

from decisiondrift.cli import cli


def test_audit_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["audit", "--help"])
    assert result.exit_code == 0
    assert "Audit ADR health" in result.output


def test_audit_no_adrs(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["audit", "--repo", str(tmp_path), "--adr-dir", str(tmp_path / "adr")])
    assert result.exit_code == 1
    assert "ADR directory not found" in result.output or "no ADR files found" in result.output
