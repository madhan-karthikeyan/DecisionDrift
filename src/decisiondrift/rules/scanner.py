from __future__ import annotations

import ast
import re
from pathlib import Path

from decisiondrift.rules.models import Rule, RuleMatch, RuleType


def scan_dependencies(repo_path: str | Path) -> list[RuleMatch]:
    """Scan dependency files and return matched dependencies."""
    repo = Path(repo_path)
    matches: list[RuleMatch] = []
    scanners = [
        _scan_requirements_txt,
        _scan_pyproject_toml,
        _scan_package_json,
        _scan_go_mod,
        _scan_cargo_toml,
    ]
    for scanner in scanners:
        matches.extend(scanner(repo))
    return matches


def _scan_requirements_txt(repo: Path) -> list[str]:
    """Extract package names from requirements.txt."""
    pkgs: list[str] = []
    path = repo / "requirements.txt"
    seen: set[str] = set()
    if not path.exists():
        return pkgs
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            pkg = re.split(r"[=<>!~]", line)[0].strip()
            if pkg and pkg not in seen:
                seen.add(pkg)
                pkgs.append(pkg)
    except OSError:
        pass
    return pkgs


def _scan_pyproject_toml(repo: Path) -> list[str]:
    """Extract package names from pyproject.toml."""
    pkgs: list[str] = []
    path = repo / "pyproject.toml"
    seen: set[str] = set()
    if not path.exists():
        return pkgs
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (ImportError, OSError, ValueError):
        try:
            import tomli as tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (ImportError, OSError, ValueError):
            return pkgs
    proj = data.get("project", {})
    deps_list = proj.get("dependencies", [])
    if isinstance(deps_list, list):
        for dep in deps_list:
            if isinstance(dep, str):
                pkg = re.split(r"[=<>!~\[ ]", dep)[0].strip()
                if pkg and pkg not in seen:
                    seen.add(pkg)
                    pkgs.append(pkg)
    # Optional dependencies (grouped)
    opt = proj.get("optional-dependencies", {})
    if isinstance(opt, dict):
        for group_deps in opt.values():
            if isinstance(group_deps, list):
                for dep in group_deps:
                    if isinstance(dep, str):
                        pkg = re.split(r"[=<>!~\[ ]", dep)[0].strip()
                        if pkg and pkg not in seen:
                            seen.add(pkg)
                            pkgs.append(pkg)
    return pkgs


def _scan_package_json(repo: Path) -> list[str]:
    """Extract package names from package.json."""
    pkgs: list[str] = []
    path = repo / "package.json"
    seen: set[str] = set()
    if not path.exists():
        return pkgs
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return pkgs
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        for pkg in data.get(key, {}):
            if pkg not in seen:
                seen.add(pkg)
                pkgs.append(pkg)
    return pkgs


def _scan_go_mod(repo: Path) -> list[str]:
    """Extract package names from go.mod."""
    pkgs: list[str] = []
    path = repo / "go.mod"
    seen: set[str] = set()
    if not path.exists():
        return pkgs
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("require ("):
                continue
            m = re.match(r'^([^\s]+)\s+v', line)
            if m:
                pkg = m.group(1).strip()
                if pkg and pkg not in seen:
                    seen.add(pkg)
                    pkgs.append(pkg)
    except OSError:
        pass
    return pkgs


def _scan_cargo_toml(repo: Path) -> list[str]:
    """Extract crate names from Cargo.toml."""
    pkgs: list[str] = []
    path = repo / "Cargo.toml"
    seen: set[str] = set()
    if not path.exists():
        return pkgs
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (ImportError, OSError, ValueError):
        try:
            import tomli as tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (ImportError, OSError, ValueError):
            return pkgs
    for section_key in ("dependencies", "dev-dependencies", "build-dependencies"):
        deps = data.get(section_key, {})
        if isinstance(deps, dict):
            for pkg in deps:
                if pkg not in seen:
                    seen.add(pkg)
                    pkgs.append(pkg)
    return pkgs


def match_dependency_rules(
    rules: list[Rule],
    repo_path: str | Path,
) -> list[RuleMatch]:
    """Check which dependency rules match the actual dependencies in the repo."""
    actual_deps = _scan_requirements_txt(Path(repo_path))
    actual_deps.extend(_scan_pyproject_toml(Path(repo_path)))
    actual_deps.extend(_scan_package_json(Path(repo_path)))
    actual_deps.extend(_scan_go_mod(Path(repo_path)))
    actual_deps.extend(_scan_cargo_toml(Path(repo_path)))
    actual_set = set(d.lower() for d in actual_deps)

    matches: list[RuleMatch] = []
    for rule in rules:
        if rule.type != RuleType.DEPENDENCY:
            continue
        for actual in actual_set:
            if rule.match in actual or actual in rule.match:
                matches.append(RuleMatch(
                    rule=rule,
                    matched_value=actual,
                    file_path=_find_dep_file(Path(repo_path)),
                ))
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
        if any(p.startswith(".") or p in ("__pycache__", "venv", ".venv", "node_modules", ".git") for p in py_file.relative_to(repo).parts):
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
                matches.append(RuleMatch(
                    rule=rule,
                    matched_value=actual,
                ))
    return matches
