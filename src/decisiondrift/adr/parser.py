from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from decisiondrift.models.schema import ADR_SCHEMA, DecisionRecord


def parse_adr_file(path: Path) -> DecisionRecord | None:
    try:
        post = frontmatter.load(str(path))
    except Exception as e:
        print(f"Warning: could not parse {path}: {e}")
        return None

    metadata: dict[str, Any] = {k: v for k, v in post.metadata.items()}
    body: str = post.content

    try:
        validate(instance=metadata, schema=ADR_SCHEMA)
    except ValidationError as e:
        print(f"Warning: {path} failed validation: {e.message}")
        return None

    from decisiondrift.models.schema import ConfidenceLevel

    record = DecisionRecord(
        id=metadata["id"],
        title=metadata["title"],
        status=metadata["status"],
        severity=metadata["severity"],
        type=metadata.get("type"),
        source=metadata.get("source", "manual"),
        superseded_by=metadata.get("superseded_by"),
        rejected_reason=metadata.get("rejected_reason"),
        rationale=metadata.get("rationale", body.strip()),
        prohibitions=metadata.get("prohibitions", []),
        exceptions=metadata.get("exceptions"),
        alternatives_rejected=metadata.get("alternatives_rejected", []),
        related_links=metadata.get("related_links", []),
        keywords=metadata.get("keywords", []),
        evidence=metadata.get("evidence", []),
        date=metadata.get("date"),
        confidence=ConfidenceLevel(metadata["confidence"]) if metadata.get("confidence") else None,
        owner=metadata.get("owner"),
        review_after=metadata.get("review_after"),
        expires_after=metadata.get("expires_after"),
        depends_on=metadata.get("depends_on"),
    )
    return record
