from __future__ import annotations

import sys
from pathlib import Path

from decisiondrift.impact.language_registry import LANGUAGE_REGISTRY
from decisiondrift.impact.models import ChangedSymbol
from decisiondrift.impact.treesitter_queries import get_query

try:
    from tree_sitter_languages import get_language, get_parser

    HAS_TREESITTER = True
except ImportError:
    HAS_TREESITTER = False


def _is_jslik(ts_lang: str) -> bool:
    return ts_lang in ("javascript", "typescript", "tsx")


def _ts_language(language: str) -> str | None:
    info = LANGUAGE_REGISTRY.get(language.lower())
    if info and info.treesitter_grammar:
        return info.treesitter_grammar
    return None


def extract_symbols_treesitter(file_path: str, language: str, source: str | None = None) -> list[ChangedSymbol]:
    if not HAS_TREESITTER:
        print("Warning: tree-sitter not installed. Run `pip install decisiondrift[ast]`", file=sys.stderr)
        return []

    ts_lang = _ts_language(language)
    if not ts_lang:
        return []

    if source is None:
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Warning: could not read {file_path}: {e}", file=sys.stderr)
            return []

    try:
        parser = get_parser(ts_lang)
        lang_obj = get_language(ts_lang)
    except Exception as e:
        print(f"Warning: could not load tree-sitter language {ts_lang}: {e}", file=sys.stderr)
        return []

    tree = parser.parse(bytes(source, "utf8"))
    query_str = get_query(language.lower(), "symbols")
    if not query_str:
        return []

    try:
        query = lang_obj.query(query_str)
        captures = query.captures(tree.root_node)
    except Exception as e:
        print(f"Warning: failed to query {file_path}: {e}", file=sys.stderr)
        return []

    symbols = []
    for node, capture_name in captures:
        sym_type = "function"
        if "class" in capture_name:
            sym_type = "class"
        elif "method" in capture_name:
            sym_type = "method"

        try:
            name_text = source.encode("utf-8")[node.start_byte : node.end_byte].decode("utf-8")
        except Exception:
            name_text = "unknown"

        symbols.append(
            ChangedSymbol(
                name=name_text,
                symbol_type=sym_type,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
        )

    return symbols


def extract_imports_treesitter(file_path: str, language: str, source: str | None = None) -> list[str]:
    if not HAS_TREESITTER:
        return []

    ts_lang = _ts_language(language)
    if not ts_lang:
        return []

    if source is None:
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

    try:
        parser = get_parser(ts_lang)
        lang_obj = get_language(ts_lang)
    except Exception:
        return []

    tree = parser.parse(bytes(source, "utf8"))
    query_str = get_query(language.lower(), "imports")
    if not query_str:
        return []

    try:
        query = lang_obj.query(query_str)
        captures = query.captures(tree.root_node)
    except Exception:
        return []

    seen: set[str] = set()
    imports: list[str] = []

    for node, capture_name in captures:
        try:
            raw = source.encode("utf-8")[node.start_byte : node.end_byte].decode("utf-8")
        except Exception:
            continue

        name = raw.strip("\"'")

        if capture_name == "require":
            continue

        if _is_jslik(ts_lang):
            if name.startswith(".") or name.startswith("/"):
                continue
            top = name.split("/")[0]
            if top and top not in seen:
                seen.add(top)
                imports.append(top)
        elif ts_lang == "go":
            parts = name.strip("\"").split("/")
            if parts and parts[0] not in seen:
                seen.add(parts[0])
                imports.append(parts[0])
        elif ts_lang == "java":
            top = name.split(".")[0]
            if top and top not in seen:
                seen.add(top)
                imports.append(top)
        elif ts_lang == "rust":
            top = name.split(":")[0].strip()
            if top and top not in seen:
                seen.add(top)
                imports.append(top)
        else:
            if name and name not in seen:
                seen.add(name)
                imports.append(name)

    return imports


def extract_api_calls_treesitter(file_path: str, language: str, source: str | None = None) -> list[str]:
    if not HAS_TREESITTER:
        return []

    ts_lang = _ts_language(language)
    if not ts_lang:
        return []

    if source is None:
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

    try:
        parser = get_parser(ts_lang)
        lang_obj = get_language(ts_lang)
    except Exception:
        return []

    tree = parser.parse(bytes(source, "utf8"))
    query_str = get_query(language.lower(), "api_calls")
    if not query_str:
        return []

    try:
        query = lang_obj.query(query_str)
        captures = query.captures(tree.root_node)
    except Exception:
        return []

    seen: set[str] = set()
    calls: list[str] = []
    for node, _capture_name in captures:
        try:
            raw = source.encode("utf-8")[node.start_byte : node.end_byte].decode("utf-8")
        except Exception:
            continue
        raw = raw.strip()
        if raw and raw not in seen:
            seen.add(raw)
            calls.append(raw)

    return calls
