from __future__ import annotations

from pathlib import Path

from decisiondrift.impact.models import ChangedSymbol


def _add(terms: list[str], seen: set[str], term: str) -> None:
    key = term.lower()
    if key not in seen and len(key) > 1:
        terms.append(term)
        seen.add(key)


def generate_search_terms(symbols: list[ChangedSymbol]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    for symbol in symbols:
        name = symbol.name
        _add(terms, seen, name)

        for part in _split_camelcase(name):
            _add(terms, seen, part)

        path = Path(symbol.file_path)
        for part in path.parts:
            _add(terms, seen, part)

        stem = path.stem
        _add(terms, seen, stem)

        for part in stem.split("_"):
            _add(terms, seen, part)

        for part in name.split("_"):
            _add(terms, seen, part)

    return terms


def _split_camelcase(name: str) -> list[str]:
    if not name:
        return []
    parts: list[str] = []
    current: list[str] = []
    for ch in name:
        if ch.isupper() and current:
            parts.append("".join(current))
            current = [ch]
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts
