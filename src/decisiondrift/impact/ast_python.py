from __future__ import annotations

import ast
import sys
from pathlib import Path

from decisiondrift.impact.models import ChangedSymbol


def extract_symbols(file_path: str, source: str | None = None) -> list[ChangedSymbol]:
    if source is None:
        try:
            source = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return []
        except OSError as e:
            print(f"Warning: could not read {file_path}: {e}", file=sys.stderr)
            return []

    symbols: list[ChangedSymbol] = []

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        print(f"Warning: syntax error in {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: unexpected error parsing {file_path}: {e}", file=sys.stderr)
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Only collect top-level classes (parent is module)
            if isinstance(getattr(node, "parent", None), ast.Module) or not hasattr(node, "parent"):
                symbols.append(ChangedSymbol(
                    name=node.name,
                    symbol_type="class",
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                ))
            # Collect methods inside this class
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(ChangedSymbol(
                        name=child.name,
                        symbol_type="method",
                        file_path=file_path,
                        start_line=child.lineno,
                        end_line=child.end_lineno or child.lineno,
                    ))

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only collect module-level functions
            parent = getattr(node, "parent", None)
            if parent is None:
                for p in ast.walk(tree):
                    for child in ast.iter_child_nodes(p):
                        if child is node:
                            parent = p
                            break
                    if parent:
                        break
            if isinstance(parent, ast.Module):
                symbols.append(ChangedSymbol(
                    name=node.name,
                    symbol_type="function",
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                ))

    return symbols


def _set_parents(node, parent=None):
    for child in ast.iter_child_nodes(node):
        child.parent = parent
        _set_parents(child, node)


# Patch ast.iter_child_nodes to set parent references
_original_iter = ast.iter_child_nodes


def _patched_iter(node):
    for child in _original_iter(node):
        child.parent = node
        yield child


ast.iter_child_nodes = _patched_iter
