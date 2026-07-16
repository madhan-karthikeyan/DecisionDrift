from __future__ import annotations

import datetime
import os
import subprocess
import sys
from pathlib import Path

from decisiondrift.adr.id_allocator import allocate_id
from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.parser import parse_adr_file
from decisiondrift.adr.writer import read_adr, set_status, write_adr
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


def show_adr(adr_dir: str, adr_id: str) -> DecisionRecord | None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return None
    record = parse_adr_file(target)
    if record is None:
        print(f"Error: could not parse {target}")
        return None
    return record


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
    if record.status != "proposed":
        print(f"Error: {adr_id} is not proposed (current status: {record.status})")
        return
    set_status(target, "rejected", rejected_reason=reason)
    print(f"{adr_id} rejected.")


def deprecate_adr(adr_dir: str, adr_id: str, reason: str | None = None) -> None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return
    record = parse_adr_file(target)
    if record is None:
        print(f"Error: could not parse {target}")
        return
    if record.status not in ("accepted", "proposed"):
        print(f"Error: {adr_id} is already {record.status}")
        return
    set_status(target, "deprecated", rejected_reason=reason)
    print(f"{adr_id} deprecated.")


def supersede_adr(adr_dir: str, adr_id: str, title: str, body: str | None = None) -> str | None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return None
    record = parse_adr_file(target)
    if record is None:
        print(f"Error: could not parse {target}")
        return None
    if record.status not in ("accepted", "proposed"):
        print(f"Error: {adr_id} is already {record.status} and cannot be superseded")
        return None

    new_id = allocate_id(str(adr_path))
    new_path = adr_path / f"{new_id}.md"

    metadata, old_body = read_adr(target)

    metadata["status"] = "superseded"
    metadata["superseded_by"] = new_id
    write_adr(target, metadata, old_body)

    new_metadata = {
        "id": new_id,
        "title": title,
        "status": "proposed",
        "severity": record.severity,
        "source": "manual",
        "date": datetime.date.today().isoformat(),
        "supersedes": adr_id,
    }
    new_body = body or f"Supercedes {adr_id}: {record.title}\n\n"
    write_adr(new_path, new_metadata, new_body)

    print(f"{adr_id} superseded by {new_id}.")
    return new_id


def edit_adr(adr_dir: str, adr_id: str) -> None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))
    try:
        subprocess.check_call([editor, str(target)])
    except subprocess.CalledProcessError:
        print("Error: editor exited with non-zero status")
    except FileNotFoundError:
        print(f"Error: editor '{editor}' not found. Set $EDITOR or $VISUAL.")
        sys.exit(1)


def history_adr(adr_dir: str, adr_id: str) -> None:
    adr_path = Path(adr_dir)
    target = adr_path / f"{adr_id}.md"
    if not target.exists():
        print(f"Error: {adr_id} not found in {adr_dir}")
        return

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--follow", str(target)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            print("Error: not a git repository or git not available")
            return
        if not result.stdout.strip():
            print(f"No history found for {adr_id}.")
            return
        print(result.stdout.strip())
    except FileNotFoundError:
        print("Error: git not found")
        sys.exit(1)
