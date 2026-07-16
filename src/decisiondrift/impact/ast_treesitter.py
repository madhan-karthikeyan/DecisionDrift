from __future__ import annotations

import sys
from pathlib import Path

from decisiondrift.impact.models import ChangedSymbol

try:
    from tree_sitter_languages import get_language, get_parser

    HAS_TREESITTER = True
except ImportError:
    HAS_TREESITTER = False


def _get_query(lang_name: str) -> str:
    """Returns tree-sitter query to extract classes, methods, and functions."""
    if lang_name in ("javascript", "typescript", "tsx"):
        return """
        (class_declaration name: (identifier) @class.name)
        (method_definition name: (property_identifier) @method.name)
        (function_declaration name: (identifier) @function.name)
        (lexical_declaration (variable_declarator name: (identifier) @function.name value: [(arrow_function) (function)]))
        """
    elif lang_name == "go":
        return """
        (type_spec name: (type_identifier) @class.name type: (struct_type))
        (method_declaration name: (field_identifier) @method.name)
        (function_declaration name: (identifier) @function.name)
        """
    elif lang_name == "java":
        return """
        (class_declaration name: (identifier) @class.name)
        (method_declaration name: (identifier) @method.name)
        """
    elif lang_name == "rust":
        return """
        (struct_item name: (type_identifier) @class.name)
        (impl_item (function_item name: (identifier) @method.name))
        (function_item name: (identifier) @function.name)
        """
    return ""


def _get_import_query(lang_name: str) -> str:
    """Returns tree-sitter query to extract import/require statements."""
    if lang_name in ("javascript", "typescript", "tsx"):
        return """
        (import_statement source: (string) @import)
        (call_expression
          function: (identifier) @require
          (#eq? @require "require")
          arguments: (arguments (string) @import))
        """
    elif lang_name == "go":
        return """
        (import_spec path: (interpreted_string_literal) @import)
        """
    elif lang_name == "java":
        return """
        (import_declaration name: (scoped_identifier) @import)
        """
    elif lang_name == "rust":
        return """
        (use_declaration argument: (use_path (identifier) @import))
        (extern_crate_declaration name: (identifier) @import)
        """
    return ""


def extract_symbols_treesitter(file_path: str, language: str, source: str | None = None) -> list[ChangedSymbol]:
    if not HAS_TREESITTER:
        print("Warning: tree-sitter not installed. Run `pip install decisiondrift[ast]`", file=sys.stderr)
        return []

    lang_map = {
        "javascript": "javascript",
        "typescript": "typescript",
        "tsx": "tsx",
        "go": "go",
        "java": "java",
        "rust": "rust",
    }

    ts_lang = lang_map.get(language.lower())
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
    query_str = _get_query(ts_lang)
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

    lang_map = {
        "javascript": "javascript",
        "typescript": "typescript",
        "tsx": "tsx",
        "go": "go",
        "java": "java",
        "rust": "rust",
    }

    ts_lang = lang_map.get(language.lower())
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
    query_str = _get_import_query(ts_lang)
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

        if language in ("javascript", "typescript", "tsx"):
            if name.startswith(".") or name.startswith("/"):
                continue
            top = name.split("/")[0]
            if top and top not in seen:
                seen.add(top)
                imports.append(top)
        elif language == "go":
            parts = name.strip("\"").split("/")
            if parts and parts[0] not in seen:
                seen.add(parts[0])
                imports.append(parts[0])
        elif language == "java":
            top = name.split(".")[0]
            if top and top not in seen:
                seen.add(top)
                imports.append(top)
        elif language == "rust":
            top = name.split(":")[0].strip()
            if top and top not in seen:
                seen.add(top)
                imports.append(top)

    return imports


def extract_api_calls_treesitter(file_path: str, language: str, source: str | None = None) -> list[str]:
    if not HAS_TREESITTER:
        return []

    lang_map = {
        "javascript": "javascript",
        "typescript": "typescript",
        "tsx": "tsx",
        "go": "go",
        "java": "java",
        "rust": "rust",
    }

    ts_lang = lang_map.get(language.lower())
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

    if ts_lang in ("javascript", "typescript", "tsx"):
        query_str = """
        (call_expression function: (member_expression property: (property_identifier) @call))
        (call_expression function: (identifier) @call)
        """
    elif ts_lang == "go":
        query_str = """
        (call_expression function: (selector_expression field: (field_identifier) @call))
        (call_expression function: (identifier) @call)
        """
    elif ts_lang == "java":
        query_str = """
        (method_invocation name: (identifier) @call)
        """
    elif ts_lang == "rust":
        query_str = """
        (call_expression function: (field_expression field: (field_identifier) @call))
        (call_expression function: (identifier) @call)
        """
    else:
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
