from __future__ import annotations

from decisiondrift.models.schema import DecisionRecord


def resolve_active(records: list[DecisionRecord]) -> list[DecisionRecord]:
    active = [r for r in records if r.status == "accepted"]

    superseded_ids = set()
    for r in active:
        if r.superseded_by:
            superseded_ids.add(r.id)

    return [r for r in active if r.id not in superseded_ids]
