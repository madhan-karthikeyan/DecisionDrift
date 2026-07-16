from __future__ import annotations

from importlib import import_module
from typing import Callable

from decisiondrift.impact.language_registry import LANGUAGE_REGISTRY

_QUERY_CACHE: dict[str, dict[str, str]] = {}


def _load_queries(lang_name: str) -> dict[str, str] | None:
    if lang_name in _QUERY_CACHE:
        return _QUERY_CACHE[lang_name]

    if lang_name not in LANGUAGE_REGISTRY:
        return None

    module_name = lang_name.replace("-", "_")
    try:
        mod = import_module(f"decisiondrift.impact.treesitter_queries.{module_name}")
    except ImportError:
        return None

    queries = {
        "symbols": getattr(mod, "symbols_query", lambda: "")(),
        "imports": getattr(mod, "imports_query", lambda: "")(),
        "api_calls": getattr(mod, "api_calls_query", lambda: "")(),
    }
    _QUERY_CACHE[lang_name] = queries
    return queries


def get_query(lang_name: str, query_type: str) -> str:
    queries = _load_queries(lang_name)
    if queries is None:
        return ""
    return queries.get(query_type, "")
