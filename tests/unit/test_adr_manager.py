from __future__ import annotations

from pathlib import Path

from decisiondrift.adr.supersession import resolve_active
from decisiondrift.adr_manager.commands import approve_adr, list_adrs, reject_adr
from decisiondrift.models.schema import DecisionRecord


class TestADRDependencies:
    def test_depends_on_keeps_adr_active_when_dependency_accepted(self):
        adrs = [
            DecisionRecord(id="ADR-0001", title="Use FastAPI", status="accepted", severity="high"),
            DecisionRecord(
                id="ADR-0002", title="Use Redis", status="accepted", severity="medium", depends_on="ADR-0001"
            ),
        ]
        active = resolve_active(adrs)
        active_ids = {r.id for r in active}
        assert "ADR-0002" in active_ids

    def test_depends_on_removes_adr_when_dependency_missing(self):
        adrs = [
            DecisionRecord(
                id="ADR-0002", title="Use Redis", status="accepted", severity="medium", depends_on="ADR-NONEXISTENT"
            ),
        ]
        active = resolve_active(adrs)
        active_ids = {r.id for r in active}
        assert "ADR-0002" not in active_ids

    def test_depends_on_removes_adr_when_dependency_rejected(self):
        adrs = [
            DecisionRecord(id="ADR-0001", title="Use FastAPI", status="rejected", severity="high"),
            DecisionRecord(
                id="ADR-0002", title="Use Redis", status="accepted", severity="medium", depends_on="ADR-0001"
            ),
        ]
        active = resolve_active(adrs)
        active_ids = {r.id for r in active}
        assert "ADR-0002" not in active_ids


class TestADRSupercession:
    def test_supersedes_removes_original(self):
        adrs = [
            DecisionRecord(
                id="ADR-0001", title="Use Flask", status="accepted", severity="high", superseded_by="ADR-0002"
            ),
            DecisionRecord(id="ADR-0002", title="Use FastAPI", status="accepted", severity="high"),
        ]
        active = resolve_active(adrs)
        active_ids = {r.id for r in active}
        assert "ADR-0001" not in active_ids

    def test_supersedes_only_applies_to_accepted(self):
        adrs = [
            DecisionRecord(id="ADR-0001", title="Use Flask", status="accepted", severity="high"),
            DecisionRecord(id="ADR-0002", title="Use FastAPI", status="proposed", severity="high"),
        ]
        active = resolve_active(adrs)
        active_ids = {r.id for r in active}
        assert "ADR-0001" in active_ids


class TestADRRejectionPropagation:
    def test_rejecting_adr_propagates_to_dependents(self):
        adrs = [
            DecisionRecord(id="ADR-0001", title="Use FastAPI", status="accepted", severity="high"),
            DecisionRecord(
                id="ADR-0002", title="Use SQLAlchemy", status="accepted", severity="medium", depends_on="ADR-0001"
            ),
        ]
        active = resolve_active(adrs)
        assert "ADR-0002" in {r.id for r in active}

        adrs[0].status = "rejected"
        active2 = resolve_active(adrs)
        assert "ADR-0002" not in {r.id for r in active2}

    def test_chain_of_dependencies(self):
        adrs = [
            DecisionRecord(id="ADR-0001", title="Base", status="accepted", severity="high"),
            DecisionRecord(id="ADR-0002", title="Middle", status="accepted", severity="medium", depends_on="ADR-0001"),
            DecisionRecord(id="ADR-0003", title="Leaf", status="accepted", severity="medium", depends_on="ADR-0002"),
        ]
        active = resolve_active(adrs)
        assert len(active) == 3

        adrs[0].status = "rejected"
        active2 = resolve_active(adrs)
        assert "ADR-0002" not in {r.id for r in active2}


class TestADRManagerCommands:
    def test_list_adrs_no_filter(self, adr_dir_with_records: Path):
        records = list_adrs(str(adr_dir_with_records))
        assert len(records) == 3

    def test_list_adrs_filter_by_status(self, adr_dir_with_records: Path):
        records = list_adrs(str(adr_dir_with_records), status="accepted")
        assert len(records) == 1
        assert records[0].id == "ADR-0001"

    def test_list_adrs_filter_by_source(self, adr_dir_with_records: Path):
        records = list_adrs(str(adr_dir_with_records), source="bootstrap")
        for r in records:
            assert r.source == "bootstrap"

    def test_approve_adr(self, adr_dir_with_records: Path):
        approve_adr(str(adr_dir_with_records), "ADR-0003")
        from decisiondrift.adr.parser import parse_adr_file

        record = parse_adr_file(adr_dir_with_records / "ADR-0003.md")
        assert record is not None
        assert record.status == "accepted"

    def test_approve_non_proposed_adr(self, adr_dir_with_records: Path):
        approve_adr(str(adr_dir_with_records), "ADR-0001")

    def test_reject_adr(self, adr_dir_with_records: Path):
        reject_adr(str(adr_dir_with_records), "ADR-0003", reason="Team decided against it.")
        from decisiondrift.adr.parser import parse_adr_file

        record = parse_adr_file(adr_dir_with_records / "ADR-0003.md")
        assert record is not None
        assert record.status == "rejected"
        assert record.rejected_reason == "Team decided against it."

    def test_reject_nonexistent_adr(self, adr_dir_with_records: Path):
        reject_adr(str(adr_dir_with_records), "ADR-9999")

    def test_reject_already_accepted_adr_fails(self, adr_dir_with_records: Path):
        """Regression: Bug #1 — reject should not overwrite accepted ADRs."""
        reject_adr(str(adr_dir_with_records), "ADR-0001")
        from decisiondrift.adr.parser import parse_adr_file

        record = parse_adr_file(adr_dir_with_records / "ADR-0001.md")
        assert record is not None
        assert record.status == "accepted", "Rejecting an accepted ADR should not change its status"

    def test_reject_already_rejected_adr_fails(self, adr_dir_with_records: Path):
        """Regression: Bug #1 — reject should not overwrite rejected ADRs."""
        reject_adr(str(adr_dir_with_records), "ADR-0003", reason="First rejection")
        reject_adr(str(adr_dir_with_records), "ADR-0003", reason="Second rejection")
        from decisiondrift.adr.parser import parse_adr_file

        record = parse_adr_file(adr_dir_with_records / "ADR-0003.md")
        assert record is not None
        assert record.rejected_reason == "First rejection", "Should keep first rejection reason"

    def test_approve_nonexistent_adr(self, adr_dir_with_records: Path):
        approve_adr(str(adr_dir_with_records), "ADR-9999")

    def test_show_adr(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import show_adr
        record = show_adr(str(adr_dir_with_records), "ADR-0001")
        assert record is not None
        assert record.id == "ADR-0001"
        assert record.title == "Use FastAPI for HTTP APIs"

    def test_show_nonexistent_adr(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import show_adr
        record = show_adr(str(adr_dir_with_records), "ADR-9999")
        assert record is None


class TestGuardCommands:
    def test_guard_install_creates_hook(self, tmp_path: Path):
        from click.testing import CliRunner
        from decisiondrift.cli import cli

        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["guard", "--install", "--repo", str(repo)])
        assert result.exit_code == 0
        hook_file = repo / ".git" / "hooks" / "pre-commit"
        assert hook_file.exists()
        content = hook_file.read_text()
        assert "decisiondrift enforce --staged" in content
        assert str(repo) in content

    def test_guard_uninstall_removes_hook(self, tmp_path: Path):
        from click.testing import CliRunner
        from decisiondrift.cli import cli

        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        hook_file = repo / ".git" / "hooks" / "pre-commit"
        hook_file.write_text("#!/bin/sh\nexec decisiondrift enforce --staged --repo /tmp\n")
        hook_file.chmod(0o755)

        runner = CliRunner()
        result = runner.invoke(cli, ["guard", "--uninstall", "--repo", str(repo)])
        assert result.exit_code == 0
        assert not hook_file.exists()

    def test_guard_uninstall_no_hook(self, tmp_path: Path):
        from click.testing import CliRunner
        from decisiondrift.cli import cli

        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["guard", "--uninstall", "--repo", str(repo)])
        assert result.exit_code == 0
        assert "Nothing to remove" in result.output

    def test_guard_install_preserves_adr_dir(self, tmp_path: Path):
        from click.testing import CliRunner
        from decisiondrift.cli import cli

        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["guard", "--install", "--repo", str(repo), "--adr-dir", "custom/adr"])
        assert result.exit_code == 0
        hook_file = repo / ".git" / "hooks" / "pre-commit"
        content = hook_file.read_text()
        assert "--adr-dir custom/adr" in content

    def test_list_empty_directory(self, tmp_path: Path):
        empty_dir = tmp_path / "empty_adr"
        empty_dir.mkdir()
        records = list_adrs(str(empty_dir))
        assert records == []

    def test_list_nonexistent_directory(self, tmp_path: Path):
        records = list_adrs(str(tmp_path / "nonexistent"))
        assert records == []


class TestADRDeprecation:
    def test_deprecate_adr(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import deprecate_adr
        from decisiondrift.adr.parser import parse_adr_file

        deprecate_adr(str(adr_dir_with_records), "ADR-0001", reason="No longer relevant")
        record = parse_adr_file(adr_dir_with_records / "ADR-0001.md")
        assert record is not None
        assert record.status == "deprecated"
        assert record.rejected_reason == "No longer relevant"

    def test_deprecate_nonexistent_adr(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import deprecate_adr

        deprecate_adr(str(adr_dir_with_records), "ADR-9999")

    def test_deprecate_already_rejected_adr_fails(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import deprecate_adr
        from decisiondrift.adr.parser import parse_adr_file

        deprecate_adr(str(adr_dir_with_records), "ADR-0003")
        record = parse_adr_file(adr_dir_with_records / "ADR-0003.md")
        assert record is not None
        assert record.status != "deprecated"

    def test_archive_aliases_deprecate(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import deprecate_adr
        from decisiondrift.adr.parser import parse_adr_file

        deprecate_adr(str(adr_dir_with_records), "ADR-0001", reason="Archived")
        record = parse_adr_file(adr_dir_with_records / "ADR-0001.md")
        assert record is not None
        assert record.status == "deprecated"


class TestADRSupercession:
    def test_supersede_creates_new_adr(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import supersede_adr
        from decisiondrift.adr.parser import parse_adr_file

        new_id = supersede_adr(str(adr_dir_with_records), "ADR-0001", "Use Fastify Instead")
        assert new_id is not None
        assert (adr_dir_with_records / f"{new_id}.md").exists()

        original = parse_adr_file(adr_dir_with_records / "ADR-0001.md")
        assert original is not None
        assert original.status == "superseded"
        assert original.superseded_by == new_id

        new_record = parse_adr_file(adr_dir_with_records / f"{new_id}.md")
        assert new_record is not None
        assert new_record.status == "proposed"

    def test_supersede_nonexistent_adr(self, adr_dir_with_records: Path):
        from decisiondrift.adr_manager.commands import supersede_adr

        new_id = supersede_adr(str(adr_dir_with_records), "ADR-9999", "New Title")
        assert new_id is None
