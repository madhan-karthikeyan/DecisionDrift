from __future__ import annotations

from pathlib import Path
from typing import Optional

from decisiondrift.adr.parser import parse_adr_file
from decisiondrift.models.schema import DecisionRecord


def load_adrs(adr_dir: str | Path, status_filter: Optional[set[str]] = None) -> list[DecisionRecord]:
    adr_path = Path(adr_dir)
    if not adr_path.exists():
        return []

    records: list[DecisionRecord] = []
    for md_file in sorted(adr_path.glob("*.md")):
        record = parse_adr_file(md_file)
        if record is None:
            continue
        if status_filter and record.status not in status_filter:
            continue
        records.append(record)

    return records
