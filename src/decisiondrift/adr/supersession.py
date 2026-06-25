from __future__ import annotations

from decisiondrift.models.schema import DecisionRecord


def resolve_active(records: list[DecisionRecord]) -> list[DecisionRecord]:
    active = [r for r in records if r.status == "accepted"]
    record_map = {r.id: r for r in records}

    superseded_ids = set()
    invalidated_deps = set()

    for r in active:
        if r.superseded_by:
            superseded_ids.add(r.id)

        if r.depends_on:
            dep_record = record_map.get(r.depends_on)
            if not dep_record or dep_record.status != "accepted":
                invalidated_deps.add(r.id)

    return [r for r in active if r.id not in superseded_ids and r.id not in invalidated_deps]
