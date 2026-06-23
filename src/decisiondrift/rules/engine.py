from __future__ import annotations

import ast
import re
from pathlib import Path

from decisiondrift.impact.diff_parser import parse_diff
from decisiondrift.models.schema import DecisionRecord
from decisiondrift.rules.models import (
    Action,
    EnforcementFinding,
    EnforcementResult,
    Rule,
    RuleMatch,
    RuleSet,
    RuleType,
)
from decisiondrift.rules.scanner import (
    match_dependency_rules,
    match_import_rules,
    scan_dependencies,
    scan_imports,
)


def enforce(
    rules: RuleSet,
    repo_path: str | Path = ".",
    diff_text: str | None = None,
) -> EnforcementResult:
    """Evaluate rules against a diff or full repo.
    If diff_text is provided, only changed files are scanned.
    If diff_text is None, the entire repo is scanned.
    """
    if diff_text:
        return _enforce_diff(rules, repo_path, diff_text)
    return _enforce_repo(rules, repo_path)


def enforce_from_adrs(
    adrs: list[DecisionRecord],
    repo_path: str | Path = ".",
    diff_text: str | None = None,
) -> EnforcementResult:
    """Convenience: convert ADRs to rules, then enforce."""
    from decisiondrift.adr.rule_generator import _rules_for_adr

    all_rules: list[Rule] = []
    for adr in adrs:
        all_rules.extend(_rules_for_adr(adr))
    return enforce(RuleSet(rules=all_rules), repo_path=repo_path, diff_text=diff_text)


def _enforce_diff(
    rules: RuleSet,
    repo_path: str | Path,
    diff_text: str,
) -> EnforcementResult:
    repo = Path(repo_path)
    files = parse_diff(diff_text)
    findings: list[EnforcementFinding] = []
    rules_evaluated = 0

    dep_rules = rules.by_type(RuleType.DEPENDENCY)
    import_rules = rules.by_type(RuleType.IMPORT)
    path_rules = rules.by_type(RuleType.PATH)
    api_rules = rules.by_type(RuleType.API)
    config_rules = rules.by_type(RuleType.CONFIG)

    # Dependency rules: check if changed files include dependency files
    for f in files:
        fpath = f.path.lower()
        if "requirements.txt" in fpath or "pyproject.toml" in fpath:
            for rule in dep_rules:
                rules_evaluated += 1
                deps_in_file = _extract_deps_from_file(repo / f.path)
                for dep in deps_in_file:
                    if rule.match in dep.lower():
                        findings.append(_to_finding(rule, dep, f.path))

    # Import rules: check AST of changed Python files
    import_scan = _scan_imports_in_diff(files, repo)
    for rule in import_rules:
        rules_evaluated += 1
        for imp, file_path in import_scan:
            if rule.match == imp or imp.startswith(rule.match + "."):
                findings.append(_to_finding(rule, imp, file_path))

    # Path rules: check changed file paths
    for rule in path_rules:
        rules_evaluated += 1
        for f in files:
            if re.search(rule.match, f.path):
                findings.append(_to_finding(rule, f.path, f.path))

    # API rules: check function calls in AST of changed Python files
    for rule in api_rules:
        rules_evaluated += 1
        for f in files:
            if f.language != "python":
                continue
            file_path = repo / f.path
            calls = _scan_api_calls(file_path)
            for call in calls:
                if rule.match in call:
                    findings.append(_to_finding(rule, call, f.path))

    # Config rules: check config files for key-value patterns
    for rule in config_rules:
        rules_evaluated += 1
        for f in files:
            if not _is_config_file(f.path):
                continue
            matches = _scan_config_pattern(repo / f.path, rule.match)
            for val in matches:
                findings.append(_to_finding(rule, val, f.path))

    return EnforcementResult(
        findings=findings,
        files_scanned=len(files),
        rules_evaluated=rules_evaluated,
    )


def _enforce_repo(
    rules: RuleSet,
    repo_path: str | Path,
) -> EnforcementResult:
    """Full repo scan for audit mode."""
    repo = Path(repo_path)
    findings: list[EnforcementFinding] = []
    rules_evaluated = 0

    dep_rules = rules.by_type(RuleType.DEPENDENCY)
    import_rules = rules.by_type(RuleType.IMPORT)
    path_rules = rules.by_type(RuleType.PATH)
    api_rules = rules.by_type(RuleType.API)
    config_rules = rules.by_type(RuleType.CONFIG)

    dep_matches = match_dependency_rules(dep_rules, repo)
    for m in dep_matches:
        rules_evaluated += 1
        findings.append(_to_finding(m.rule, m.matched_value, m.file_path))

    imp_matches = match_import_rules(import_rules, repo)
    for m in imp_matches:
        rules_evaluated += 1
        findings.append(_to_finding(m.rule, m.matched_value, m.file_path))

    return EnforcementResult(
        findings=findings,
        files_scanned=len(list(repo.rglob("*"))),
        dependencies_scanned=len(dep_matches),
        imports_scanned=len(imp_matches),
        rules_evaluated=rules_evaluated,
    )


def _to_finding(rule: Rule, match_value: str, file_path: str | None = None) -> EnforcementFinding:
    severity_map: dict[Action, str] = {
        Action.BLOCK: "critical",
        Action.REQUIRE_APPROVAL: "high",
        Action.WARN: "medium",
        Action.INFO: "low",
    }
    return EnforcementFinding(
        adr_id=rule.source_adr,
        adr_title="",
        rule_id=rule.id,
        rule_type=rule.type,
        action=rule.action,
        severity=severity_map.get(rule.action, "medium"),
        match_value=match_value,
        file_path=file_path,
        description=rule.description,
    )


def _extract_deps_from_file(path: Path) -> list[str]:
    """Extract dependency names from a dependency file."""
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    deps: list[str] = []
    if path.name == "requirements.txt":
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                pkg = re.split(r"[=<>!~]", line)[0].strip()
                if pkg:
                    deps.append(pkg)
    elif path.name == "pyproject.toml":
        try:
            import tomllib
            data = tomllib.loads(text)
        except (ImportError, ValueError):
            return deps
        proj = data.get("project", {})
        for dep in proj.get("dependencies", []):
            if isinstance(dep, str):
                pkg = re.split(r"[=<>!~\[ ]", dep)[0].strip()
                if pkg:
                    deps.append(pkg)
    elif path.name == "package.json":
        try:
            import json
            data = json.loads(text)
        except (ImportError, ValueError):
            return deps
        for key in ("dependencies", "devDependencies"):
            for pkg in data.get(key, {}):
                deps.append(pkg)
    elif path.name == "Cargo.toml":
        try:
            import tomllib
            data = tomllib.loads(text)
        except (ImportError, ValueError):
            return deps
        for pkg in data.get("dependencies", {}):
            deps.append(pkg)
    elif path.name == "go.mod":
        for m in re.finditer(r'^require\s+([^\s]+)\s', text, re.MULTILINE):
            deps.append(m.group(1))
    return deps


def _scan_imports_in_diff(files, repo: Path) -> list[tuple[str, str]]:
    """Scan changed Python files for imports."""
    imports: list[tuple[str, str]] = []
    for f in files:
        if f.language != "python":
            continue
        file_path = repo / f.path
        if not file_path.exists():
            continue
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0].lower()
                    if top:
                        imports.append((top, f.path))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0].lower()
                    if top:
                        imports.append((top, f.path))
    return imports


def _scan_api_calls(file_path: Path) -> list[str]:
    """Scan a Python file for function/method call names."""
    if not file_path.exists():
        return []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, OSError):
        return []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                parts = []
                n = node.func
                while isinstance(n, ast.Attribute):
                    parts.append(n.attr)
                    n = n.value
                if isinstance(n, ast.Name):
                    parts.append(n.id)
                calls.append(".".join(reversed(parts)))
            elif isinstance(node.func, ast.Name):
                calls.append(node.func.id)
    return calls


def _is_config_file(path: str) -> bool:
    return any(path.endswith(ext) for ext in (".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".env"))


def _scan_config_pattern(file_path: Path, pattern: str) -> list[str]:
    """Scan a config file for matching key=value patterns."""
    if not file_path.exists():
        return []
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    matches: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or line.startswith("//"):
            continue
        if pattern.lower() in line.lower():
            matches.append(line)
    return matches
