from __future__ import annotations

from pathlib import Path

from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.parser import parse_adr_file
from decisiondrift.adr.writer import set_status
from decisiondrift.models.schema import DecisionRecord


def list_adrs(adr_dir: str, status: str | None = None, source: str | None = None) -> list[DecisionRecord]:
    status_filter = {status} if status else None
    records = load_adrs(adr_dir, status_filter=status_filter)
    if source:
        records = [r for r in records if r.source == source]
    return records


def approve_adr(adr_dir: str, adr_id: str) -> None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return
    record = parse_adr_file(target)
    if record is None:
        print(f"Error: could not parse {target}")
        return
    if record.status != "proposed":
        print(f"Error: {adr_id} is not proposed (current status: {record.status})")
        return
    set_status(target, "accepted")
    print(f"{adr_id} approved.")


def reject_adr(adr_dir: str, adr_id: str, reason: str | None = None) -> None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return
    record = parse_adr_file(target)
    if record is None:
        print(f"Error: could not parse {target}")
        return
    set_status(target, "rejected", rejected_reason=reason)
    print(f"{adr_id} rejected.")
