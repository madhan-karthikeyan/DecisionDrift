from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from decisiondrift.impact.ast_treesitter import HAS_TREESITTER, extract_imports_treesitter
from decisiondrift.impact.language_registry import (
    EXTENSION_TO_LANGUAGE,
    LANGUAGE_REGISTRY,
)
from decisiondrift.rules.models import Rule, RuleMatch, RuleType
from decisiondrift.utils.dependency_parser import (
    parse_cargo_toml,
    parse_go_mod,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)

EXCLUDED_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", ".egg-info", ".tox", "env"}


def _is_excluded(path: Path, repo: Path) -> bool:
    try:
        parts = path.relative_to(repo).parts
        return any(p in EXCLUDED_DIRS for p in parts)
    except ValueError:
        return True


def scan_dependencies(repo_path: str | Path) -> list[str]:
    """Scan dependency files recursively and return discovered package names."""
    repo = Path(repo_path)
    results: list[str] = []
    seen_deps: set[str] = set()
    seen_files: set[Path] = set()

    def _parse_requirements(path: Path) -> list[tuple[str, str]]:
        return [(d, "runtime") for d in parse_requirements_txt(path)]

    def _parse_go(path: Path) -> list[tuple[str, str]]:
        return [(d, "runtime") for d in parse_go_mod(path)[1]]

    dep_file_patterns: dict[str, Any] = {
        "requirements.txt": _parse_requirements,
        "pyproject.toml": parse_pyproject_toml,
        "package.json": parse_package_json,
        "go.mod": _parse_go,
        "Cargo.toml": parse_cargo_toml,
    }

    for dep_file in repo.rglob("*"):
        if not dep_file.is_file() or dep_file.name not in dep_file_patterns:
            continue
        if _is_excluded(dep_file, repo):
            continue
        if dep_file in seen_files:
            continue
        seen_files.add(dep_file)

        parser = dep_file_patterns[dep_file.name]
        try:
            parsed = parser(dep_file)
        except Exception:
            continue
        for dep_name, _role in parsed:
            if dep_name and dep_name not in seen_deps:
                seen_deps.add(dep_name)
                results.append(dep_name)

    return results


def match_dependency_rules(
    rules: list[Rule],
    repo_path: str | Path,
) -> list[RuleMatch]:
    """Check which dependency rules match the actual dependencies in the repo."""
    repo = Path(repo_path)
    actual_deps = scan_dependencies(repo_path)
    actual_set = set(d.lower() for d in actual_deps)

    matches: list[RuleMatch] = []
    for rule in rules:
        if rule.type != RuleType.DEPENDENCY:
            continue
        for actual in actual_set:
            if rule.match in actual or actual in rule.match:
                matches.append(
                    RuleMatch(
                        rule=rule,
                        matched_value=actual,
                        file_path=_find_dep_file_containing(repo, rule.match),
                    )
                )
    return matches


def _find_dep_file_containing(repo: Path, match: str) -> str | None:
    """Find a dependency file that contains the given match string."""
    dep_file_names = {"requirements.txt", "pyproject.toml", "package.json", "go.mod", "Cargo.toml"}
    for dep_file in repo.rglob("*"):
        if not dep_file.is_file() or dep_file.name not in dep_file_names:
            continue
        if _is_excluded(dep_file, repo):
            continue
        try:
            text = dep_file.read_text(encoding="utf-8", errors="replace")
            if match.lower() in text.lower():
                try:
                    return str(dep_file.relative_to(repo))
                except ValueError:
                    return dep_file.name
        except OSError:
            continue
    return None


TS_LANG_EXTENSIONS: dict[str, str] = {
    ext: lang
    for lang, info in LANGUAGE_REGISTRY.items()
    for ext in info.extensions
    if info.treesitter_grammar
}


def scan_imports(repo_path: str | Path) -> list[str]:
    """Scan all source files in the repo and collect imported module names.
    Uses Python AST for .py files, tree-sitter for other supported languages."""
    repo = Path(repo_path)
    imports: set[str] = set()

    for source_file in repo.rglob("*"):
        if not source_file.is_file():
            continue
        if any(
            p.startswith(".") or p in EXCLUDED_DIRS
            for p in source_file.relative_to(repo).parts
        ):
            continue

        ext = source_file.suffix.lower()

        if ext == ".py":
            try:
                tree = ast.parse(source_file.read_text(encoding="utf-8", errors="replace"))
            except (SyntaxError, OSError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top:
                            imports.add(top.lower())
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top = node.module.split(".")[0]
                        if top:
                            imports.add(top.lower())
        elif ext in TS_LANG_EXTENSIONS and HAS_TREESITTER:
            lang = TS_LANG_EXTENSIONS[ext]
            file_imports = extract_imports_treesitter(str(source_file), lang)
            for imp in file_imports:
                imports.add(imp.lower())

    return sorted(imports)


def match_import_rules(
    rules: list[Rule],
    repo_path: str | Path,
) -> list[RuleMatch]:
    """Check which import rules match actual imports in the repo."""
    actual_imports = scan_imports(repo_path)
    actual_set = set(actual_imports)

    matches: list[RuleMatch] = []
    for rule in rules:
        if rule.type != RuleType.IMPORT:
            continue
        for actual in actual_set:
            if rule.match == actual or actual.startswith(rule.match + "."):
                matches.append(
                    RuleMatch(
                        rule=rule,
                        matched_value=actual,
                    )
                )
    return matches
