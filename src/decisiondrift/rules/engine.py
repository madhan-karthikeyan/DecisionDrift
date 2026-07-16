from __future__ import annotations

import ast
import re
from pathlib import Path

from decisiondrift.impact.ast_treesitter import HAS_TREESITTER, extract_imports_treesitter
from decisiondrift.impact.diff_parser import parse_diff
from decisiondrift.models.schema import DecisionRecord
from decisiondrift.rules.models import (
    Action,
    EnforcementFinding,
    EnforcementResult,
    Rule,
    RuleSet,
    RuleType,
)
from decisiondrift.rules.scanner import (
    TS_LANG_EXTENSIONS,
    match_dependency_rules,
    match_import_rules,
)
from decisiondrift.utils.dependency_parser import (
    parse_build_gradle_kts,
    parse_cargo_toml,
    parse_composer_json,
    parse_csproj,
    parse_gemfile,
    parse_gemfile_lock,
    parse_go_mod,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
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
    custom_rules: RuleSet | None = None,
) -> EnforcementResult:
    """Convenience: convert ADRs to rules, optionally add custom rules, then enforce."""
    from decisiondrift.adr.rule_generator import _rules_for_adr

    all_rules: list[Rule] = []
    for adr in adrs:
        all_rules.extend(_rules_for_adr(adr))
    if custom_rules:
        all_rules.extend(custom_rules.rules)
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

    # API rules: check function calls in changed files
    for rule in api_rules:
        rules_evaluated += 1
        for f in files:
            file_path = repo / f.path
            calls = _scan_api_calls(file_path, f.language)
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

    # Collect all files in the repo for path, API, and config checks
    all_files: list[Path] = []
    for f in repo.rglob("*"):
        if f.is_file() and not f.is_symlink():
            all_files.append(f)

    # Path rules: check all file paths
    for rule in path_rules:
        rules_evaluated += 1
        for f in all_files:
            try:
                rel = str(f.relative_to(repo))
            except ValueError:
                continue
            if re.search(rule.match, rel):
                findings.append(_to_finding(rule, rel, rel))

    # API rules: check function calls in all source files
    for rule in api_rules:
        rules_evaluated += 1
        for f in all_files:
            ext = f.suffix.lower()
            lang = "python" if ext == ".py" else TS_LANG_EXTENSIONS.get(ext)
            if lang is None:
                continue
            if ext != ".py" and not HAS_TREESITTER:
                continue
            try:
                rel = str(f.relative_to(repo))
            except ValueError:
                rel = f.name
            calls = _scan_api_calls(f, lang)
            for call in calls:
                if rule.match in call:
                    findings.append(_to_finding(rule, call, rel))

    # Config rules: check config files for key-value patterns
    for rule in config_rules:
        rules_evaluated += 1
        for f in all_files:
            try:
                rel = str(f.relative_to(repo))
            except ValueError:
                continue
            if not _is_config_file(rel):
                continue
            matches = _scan_config_pattern(f, rule.match)
            for val in matches:
                findings.append(_to_finding(rule, val, rel))

    return EnforcementResult(
        findings=findings,
        files_scanned=len(all_files),
        dependencies_scanned=len(dep_matches),
        imports_scanned=len(imp_matches),
        rules_evaluated=rules_evaluated,
    )


def _to_finding(rule: Rule, match_value: str, file_path: str | None = None) -> EnforcementFinding:
    action = rule.action
    conf_val = rule.confidence.numeric()

    if conf_val < 0.50:
        action = Action.INFO
    elif conf_val < 0.80 and action in (Action.BLOCK, Action.REQUIRE_APPROVAL):
        action = Action.WARN

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
        action=action,
        severity=severity_map.get(action, "medium"),
        match_value=match_value,
        file_path=file_path,
        description=rule.description,
    )


def _extract_deps_from_file(path: Path) -> list[str]:
    """Extract dependency names from a dependency file."""
    name = path.name
    if name == "requirements.txt":
        return parse_requirements_txt(path)
    if name == "pyproject.toml":
        return [dep for dep, _role in parse_pyproject_toml(path)]
    if name == "package.json":
        return [dep for dep, _role in parse_package_json(path)]
    if name == "Cargo.toml":
        _pkg, deps = parse_cargo_toml(path)
        return [dep for dep, _role in deps]
    if name == "go.mod":
        _module, deps = parse_go_mod(path)
        return deps
    if name == "Gemfile":
        return [dep for dep, _role in parse_gemfile(path)]
    if name == "Gemfile.lock":
        return [dep for dep, _role in parse_gemfile_lock(path)]
    if name == "composer.json":
        return [dep for dep, _role in parse_composer_json(path)]
    if name == "build.gradle.kts":
        return [dep for dep, _role in parse_build_gradle_kts(path)]
    if name.endswith(".csproj"):
        return [dep for dep, _role in parse_csproj(path)]
    return []


def _scan_imports_in_diff(files, repo: Path) -> list[tuple[str, str]]:
    """Scan changed files for imports.
    Uses Python AST for .py files, tree-sitter for other supported languages."""
    imports: list[tuple[str, str]] = []
    for f in files:
        file_path = repo / f.path
        if not file_path.exists():
            continue

        ext = file_path.suffix.lower()

        if ext == ".py":
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
        elif ext in TS_LANG_EXTENSIONS and HAS_TREESITTER:
            lang = TS_LANG_EXTENSIONS[ext]
            file_imports = extract_imports_treesitter(str(file_path), lang)
            for imp in file_imports:
                imports.append((imp.lower(), f.path))

    return imports


def _scan_api_calls(file_path: Path, language: str = "python") -> list[str]:
    """Scan a source file for function/method call names.
    Uses Python AST for .py files, tree-sitter for other supported languages."""
    if not file_path.exists():
        return []

    if language == "python":
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

    if HAS_TREESITTER:
        from decisiondrift.impact.ast_treesitter import extract_api_calls_treesitter
        return extract_api_calls_treesitter(str(file_path), language)

    return []


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
