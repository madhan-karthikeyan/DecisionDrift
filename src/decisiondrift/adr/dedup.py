from __future__ import annotations

from decisiondrift.models.schema import DecisionRecord


def is_duplicate(
    candidate: DecisionRecord, existing: list[DecisionRecord], threshold: float = 0.85
) -> tuple[bool, str | None]:
    for record in existing:
        if record.title.lower() == candidate.title.lower():
            return True, record.id
    return False, None
