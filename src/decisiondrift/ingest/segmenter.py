from __future__ import annotations

import re


def segment_notes(content: str) -> list[str]:
    """Split free-text notes into smaller segments for decision extraction.

    Splits by headings (##) or large paragraph breaks.
    """
    if not content.strip():
        return []

    # Split by markdown headers or multiple blank lines
    chunks = re.split(r"\n(?=#+ )|\n\n\n+", content)

    cleaned = []
    for chunk in chunks:
        c = chunk.strip()
        if c:
            cleaned.append(c)

    return cleaned if cleaned else [content.strip()]
