from __future__ import annotations

import ast
from pathlib import Path

from decisiondrift.rules.models import Rule, RuleMatch, RuleType
from decisiondrift.utils.dependency_parser import (
    parse_cargo_toml,
    parse_go_mod,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)


def scan_dependencies(repo_path: str | Path) -> list[str]:
    """Scan dependency files and return discovered package names."""
    repo = Path(repo_path)
    results: list[str] = []
    seen: set[str] = set()

    for dep in parse_requirements_txt(repo / "requirements.txt"):
        if dep not in seen:
            seen.add(dep)
            results.append(dep)
    for dep, _role in parse_pyproject_toml(repo / "pyproject.toml"):
        if dep not in seen:
            seen.add(dep)
            results.append(dep)
    for dep, _role in parse_package_json(repo / "package.json"):
        if dep not in seen:
            seen.add(dep)
            results.append(dep)
    _module, go_deps = parse_go_mod(repo / "go.mod")
    for dep in go_deps:
        if dep not in seen:
            seen.add(dep)
            results.append(dep)
    _pkg, cargo_deps = parse_cargo_toml(repo / "Cargo.toml")
    for dep, _role in cargo_deps:
        if dep not in seen:
            seen.add(dep)
            results.append(dep)

    return results


def match_dependency_rules(
    rules: list[Rule],
    repo_path: str | Path,
) -> list[RuleMatch]:
    """Check which dependency rules match the actual dependencies in the repo."""
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
                        file_path=_find_dep_file(Path(repo_path)),
                    )
                )
    return matches


def _find_dep_file(repo: Path) -> str | None:
    for name in ("requirements.txt", "pyproject.toml", "package.json", "go.mod", "Cargo.toml"):
        path = repo / name
        if path.exists():
            return name
    return None


def scan_imports(repo_path: str | Path) -> list[str]:
    """Scan all Python files in the repo and collect imported module names."""
    repo = Path(repo_path)
    imports: set[str] = set()
    for py_file in repo.rglob("*.py"):
        if any(
            p.startswith(".") or p in ("__pycache__", "venv", ".venv", "node_modules", ".git")
            for p in py_file.relative_to(repo).parts
        ):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
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
