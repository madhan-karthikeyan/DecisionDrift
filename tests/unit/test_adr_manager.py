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

    def test_approve_nonexistent_adr(self, adr_dir_with_records: Path):
        approve_adr(str(adr_dir_with_records), "ADR-9999")

    def test_list_empty_directory(self, tmp_path: Path):
        empty_dir = tmp_path / "empty_adr"
        empty_dir.mkdir()
        records = list_adrs(str(empty_dir))
        assert records == []

    def test_list_nonexistent_directory(self, tmp_path: Path):
        records = list_adrs(str(tmp_path / "nonexistent"))
        assert records == []
