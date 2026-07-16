from __future__ import annotations

import ast
from collections import Counter
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from decisiondrift.bootstrap.template_generator import ADRSuggestion
from decisiondrift.models.schema import ConfidenceLevel, DecisionRecord
from decisiondrift.utils.dependency_parser import (
    parse_cargo_toml as _parse_cargo_toml_shared,
)
from decisiondrift.utils.dependency_parser import (
    parse_go_mod as _parse_go_mod_shared,
)
from decisiondrift.utils.dependency_parser import (
    parse_package_json as _parse_package_json_shared,
)
from decisiondrift.utils.dependency_parser import (
    parse_pyproject_toml as _parse_pyproject_toml_shared,
)
from decisiondrift.utils.dependency_parser import (
    parse_requirements_txt as _parse_requirements_txt_shared,
)

_REGISTRY: Any = None
_REGISTRY_URLS: tuple[str, ...] = ()


def _get_registry(registry_urls: list[str] | None = None):
    global _REGISTRY, _REGISTRY_URLS
    urls_tuple = tuple(registry_urls) if registry_urls else ()
    if _REGISTRY is None or urls_tuple != _REGISTRY_URLS:
        _REGISTRY_URLS = urls_tuple
        from decisiondrift.bootstrap.registry import load_registry
        _REGISTRY = load_registry(registry_urls=registry_urls)
        _populate_legacy_constants(_REGISTRY)
    return _REGISTRY


def _populate_legacy_constants(reg) -> None:
    global TECH_SIGNATURES, DECISION_TEMPLATES, SELF_FRAMEWORK_REPOS
    global TEST_DEPENDENCIES, TOOLING_DECISIONS, SUPPORTING_ONLY_DECISIONS
    sigs: dict[str, tuple[str, str, list[str]]] = {}
    for name, profile in reg.technologies.items():
        detect = profile.detection
        dep_names = detect.get("dependencies", [])
        imp_names = detect.get("imports", [])
        all_names = dep_names + imp_names + [name.lower()]
        for n in all_names:
            sigs[n] = (profile.name, profile.category, list(set(all_names)))
    TECH_SIGNATURES.clear()
    TECH_SIGNATURES.update(sigs)
    templates: dict[str, tuple[str, str, list[str], str]] = {}
    for tech_name, tmpl in reg.governance_templates.items():
        templates[tech_name] = (tmpl.title, tmpl.decision_type, tmpl.prohibitions, tmpl.rationale)
    DECISION_TEMPLATES.clear()
    DECISION_TEMPLATES.update(templates)
    SELF_FRAMEWORK_REPOS.clear()
    SELF_FRAMEWORK_REPOS.update(reg.self_framework_repos)
    TEST_DEPENDENCIES.clear()
    TEST_DEPENDENCIES.update(reg.test_dependencies)
    TOOLING_DECISIONS.clear()
    TOOLING_DECISIONS.update(reg.tooling_decisions)
    SUPPORTING_ONLY_DECISIONS.clear()
    SUPPORTING_ONLY_DECISIONS.update(reg.supporting_only_decisions)


class EvidenceLevel(StrEnum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class EvidenceRole(StrEnum):
    RUNTIME = "runtime"
    DEV = "dev"
    TEST = "test"
    EXAMPLE = "example"
    TOOLING = "tooling"
    OPTIONAL = "optional"
    UNKNOWN = "unknown"


class Evidence(BaseModel):
    kind: Literal["dependency", "import", "file", "directory", "config", "entrypoint", "language"]
    value: str
    source_path: str
    role: EvidenceRole
    level: EvidenceLevel
    scope_path: str | None = None
    notes: list[str] = []


class TechnologyCandidate(BaseModel):
    name: str
    category: Literal[
        "framework",
        "runtime",
        "database",
        "orm",
        "cache",
        "queue",
        "frontend",
        "language",
        "ci",
        "container",
        "testing",
        "auth",
        "tooling",
        "css",
        "migration",
        "monitoring",
    ]
    role: Literal["primary", "supporting", "incidental", "dev", "test", "example", "tooling", "unknown"]
    evidence_level: EvidenceLevel
    evidence: list[Evidence]
    contradictions: list[str] = []
    suppress_reason: str | None = None


class GovernanceDecisionCandidate(BaseModel):
    title: str
    decision_type: Literal[
        "technology_choice",
        "runtime_policy",
        "data_access",
        "boundary_policy",
        "deployment_policy",
        "testing_policy",
    ]
    scope_path: str | None = None
    evidence_level: EvidenceLevel
    evidence: list[Evidence]
    rationale: str
    prohibitions: list[str] = []
    suppress_reason: str | None = None
    llm_generated: bool = False
    technology_name: str = ""


class RuleCandidate(BaseModel):
    type: Literal["dependency", "import", "path", "api", "config"]
    match: str
    action: Literal["block", "require_approval", "warn"]
    scope_path: str | None = None
    rationale: str


class EnforceabilityAnalysis(BaseModel):
    enforceable: bool
    level: Literal["none", "weak", "moderate", "strong"]
    reason: str
    proposed_rules: list[RuleCandidate] = []


class RepositoryModel(BaseModel):
    schema_version: str = "3"
    repo_path: str
    repository_role: Literal[
        "application",
        "api_service",
        "frontend_app",
        "library",
        "framework",
        "cli",
        "infra_controller",
        "monorepo",
        "template",
        "unknown",
    ]
    repository_subtype: Literal["async_python_api", "unknown"] = "unknown"
    evidence: list[Evidence]
    technologies: list[TechnologyCandidate]
    governance_candidates: list[GovernanceDecisionCandidate] = []


TECH_SIGNATURES: dict[str, tuple[str, str, list[str]]] = {}
DECISION_TEMPLATES: dict[str, tuple[str, str, list[str], str]] = {}
SELF_FRAMEWORK_REPOS: dict[str, str] = {}
TEST_DEPENDENCIES: set[str] = set()
TOOLING_DECISIONS: set[str] = set()
SUPPORTING_ONLY_DECISIONS: set[str] = set()


def build_repository_model(
    repo_path: str | Path,
    knowledge_provider: Any = None,
    registry_urls: list[str] | None = None,
) -> RepositoryModel:
    repo = Path(repo_path)
    _get_registry(registry_urls=registry_urls)
    evidence = collect_evidence(repo)
    technologies = build_technology_candidates(repo, evidence, knowledge_provider=knowledge_provider)
    repository_role = infer_repository_role(repo, evidence, technologies)
    technologies = apply_repository_context(repo, repository_role, technologies)
    model = RepositoryModel(
        repo_path=str(repo),
        repository_role=repository_role,
        repository_subtype=infer_repository_subtype(repository_role, evidence, technologies),
        evidence=evidence,
        technologies=technologies,
    )
    model.governance_candidates = discover_governance_candidates(model, knowledge_provider=knowledge_provider)
    return model


def collect_evidence(repo_path: Path) -> list[Evidence]:
    evidence: list[Evidence] = []
    evidence.extend(_collect_dependency_evidence(repo_path))
    evidence.extend(_collect_import_evidence(repo_path))
    evidence.extend(_collect_file_evidence(repo_path))
    return evidence


def build_technology_candidates(
    repo_path: Path,
    evidence: list[Evidence],
    knowledge_provider: Any = None,
) -> list[TechnologyCandidate]:
    grouped: dict[str, list[Evidence]] = {}
    known_names: dict[str, str] = {}
    repo_role = "unknown"

    for ev in evidence:
        tech = _technology_for_evidence(ev)
        if tech:
            grouped.setdefault(tech[0], []).append(ev)
            known_names[ev.value.lower()] = tech[0]
        elif knowledge_provider and ev.kind == "dependency" and ev.role == EvidenceRole.RUNTIME:
            result = knowledge_provider.recognize_technology(
                ev.value,
                evidence=evidence,
                repo_role=repo_role,
                nearby_techs=list(known_names.values()),
            )
            if result:
                grouped.setdefault(result.technology, []).append(ev)
                known_names[ev.value.lower()] = result.technology

    _attach_supporting_evidence(grouped, evidence)

    candidates: list[TechnologyCandidate] = []
    for name, evs in grouped.items():
        category = _category_for_name(name)
        level = _aggregate_evidence_level(evs)
        role = _candidate_role(evs, level)
        contradictions = _candidate_contradictions(name, evs)
        suppress_reason = _suppression_reason(name, role, level, evs, contradictions)
        candidates.append(
            TechnologyCandidate(
                name=name,
                category=category,
                role=role,
                evidence_level=level,
                evidence=evs,
                contradictions=contradictions,
                suppress_reason=suppress_reason,
            )
        )

    candidates.sort(key=lambda c: (_level_rank(c.evidence_level), c.name), reverse=True)
    return candidates


def infer_repository_role(
    repo_path: Path,
    evidence: list[Evidence],
    technologies: list[TechnologyCandidate],
) -> str:
    top_name = repo_path.name.lower()
    if top_name in SELF_FRAMEWORK_REPOS:
        return "framework"

    runtime_frameworks = {
        t.name
        for t in technologies
        if t.category == "framework"
        and t.role == "primary"
        and not t.suppress_reason
        and _has_framework_runtime_usage(t)
    }
    frontend = {
        t.name for t in technologies if t.category in {"frontend", "css"} and t.role in {"primary", "supporting"}
    }
    has_package = any(ev.source_path.endswith("package.json") and ev.role == EvidenceRole.RUNTIME for ev in evidence)

    if len({ev.scope_path for ev in evidence if ev.scope_path}) > 3 and len(runtime_frameworks) > 1:
        return "monorepo"
    if runtime_frameworks & {"FastAPI", "Flask", "Django", "Express", "Gin"}:
        return "api_service"
    if "Next.js" in runtime_frameworks or (frontend and has_package and not runtime_frameworks):
        return "frontend_app"
    if any(Path(ev.source_path).name in {"pyproject.toml", "setup.py", "Cargo.toml", "go.mod"} for ev in evidence):
        return "library"
    return "unknown"


def infer_repository_subtype(
    repository_role: str,
    evidence: list[Evidence],
    technologies: list[TechnologyCandidate],
) -> str:
    names = {t.name for t in technologies if not t.suppress_reason}
    has_fastapi_entrypoint = any(ev.value == "fastapi_app" for ev in evidence)
    has_routers = any(ev.value == "fastapi_routers" for ev in evidence)
    if repository_role == "api_service" and "FastAPI" in names and (has_fastapi_entrypoint or has_routers):
        return "async_python_api"
    return "unknown"


def apply_repository_context(
    repo_path: Path,
    repository_role: str,
    technologies: list[TechnologyCandidate],
) -> list[TechnologyCandidate]:
    self_tech = SELF_FRAMEWORK_REPOS.get(repo_path.name.lower())
    updated: list[TechnologyCandidate] = []
    for tech in technologies:
        data = tech.model_dump()
        suppressions = list(tech.contradictions)
        suppress_reason = tech.suppress_reason

        if self_tech and tech.name == self_tech:
            suppress_reason = f"{tech.name} is the repository product, not a governance decision."
        elif repository_role in {"library", "framework"} and tech.role == "primary" and tech.category == "framework":
            data["role"] = "supporting"
            suppressions.append("Framework evidence appears in a library/framework repository.")
            suppress_reason = "Framework evidence is not sufficient to infer an application decision."
        elif repository_role == "api_service":
            data["role"] = _api_service_role(tech)
            if tech.category == "testing":
                suppress_reason = f"{tech.name} evidence is test, not a runtime governance decision."
            elif tech.name in TOOLING_DECISIONS:
                suppress_reason = f"{tech.name} is tooling and needs explicit deployment policy evidence."

        data["contradictions"] = suppressions
        data["suppress_reason"] = suppress_reason
        updated.append(TechnologyCandidate(**data))
    return updated


def _api_service_role(tech: TechnologyCandidate) -> str:
    if tech.category == "framework":
        return "primary"
    if tech.category == "database":
        return "primary"
    if tech.category in {"orm", "cache", "queue", "runtime", "migration"}:
        return "supporting"
    if tech.category in {"container", "ci", "tooling"}:
        return "tooling"
    if tech.category == "testing":
        return "test"
    return tech.role


def _attach_supporting_evidence(grouped: dict[str, list[Evidence]], evidence: list[Evidence]) -> None:
    if "SQLAlchemy" in grouped:
        grouped["SQLAlchemy"].extend(ev for ev in evidence if ev.value == "relational_persistence")
    if "FastAPI" in grouped:
        grouped["FastAPI"].extend(ev for ev in evidence if ev.value == "fastapi_routers")


def _governance_suppression_reason(
    model: RepositoryModel,
    tech: TechnologyCandidate,
    candidate: GovernanceDecisionCandidate,
) -> str | None:
    if model.repository_role == "framework":
        return "Framework/product repositories do not produce consumer governance ADRs for implementation technologies."

    if tech.category == "frontend":
        if not _is_frontend_component_scope(candidate.scope_path):
            return "Frontend technology evidence is not scoped to a frontend component."
        if not _has_runtime_dependency_or_usage(tech.evidence):
            return "Frontend technology lacks runtime component evidence."

    if candidate.decision_type == "data_access" and model.repository_role not in {"api_service", "application"}:
        if not any(ev.value == "relational_persistence" and ev.role == EvidenceRole.RUNTIME for ev in tech.evidence):
            return "Data-access evidence appears in a library/integration context, not an application persistence boundary."

    return None


def _dominant_runtime_scope(evidence: list[Evidence]) -> str | None:
    counts: Counter[str] = Counter()
    for ev in evidence:
        if ev.role == EvidenceRole.RUNTIME and ev.scope_path:
            counts[ev.scope_path] += 1
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _is_frontend_component_scope(scope_path: str | None) -> bool:
    if not scope_path:
        return False
    return scope_path.lower() in {"frontend", "ui", "web", "client", "app"}


def _has_runtime_dependency_or_usage(evidence: list[Evidence]) -> bool:
    return any(ev.role == EvidenceRole.RUNTIME and ev.kind in {"dependency", "import", "entrypoint"} for ev in evidence)


def discover_governance_candidates(
    model: RepositoryModel,
    knowledge_provider: Any = None,
) -> list[GovernanceDecisionCandidate]:
    candidates: list[GovernanceDecisionCandidate] = []
    for tech in model.technologies:
        if tech.suppress_reason:
            continue
        if tech.role not in {"primary", "supporting"}:
            continue

        _prohibitions: list[str] = []
        llm_generated = False
        if tech.name in DECISION_TEMPLATES:
            title, decision_type, _prohibitions, rationale = DECISION_TEMPLATES[tech.name]
        elif knowledge_provider:
            evidence_summary = "; ".join(
                f"{ev.kind}:{ev.value}" for ev in tech.evidence[:5]
            )
            result = knowledge_provider.generate_template(
                tech_name=tech.name,
                ecosystem="",
                category=tech.category,
                evidence_summary=evidence_summary,
            )
            if result:
                title = f"Use {result.technology}"
                decision_type = result.decision_type
                rationale = result.rationale
                _prohibitions = getattr(result, 'prohibitions', [])
                llm_generated = result.llm_generated if hasattr(result, 'llm_generated') else True
            else:
                continue
        else:
            continue
        technology_name = tech.name
        candidate = GovernanceDecisionCandidate(
            title=title,
            decision_type=decision_type,  # type: ignore[arg-type]
            scope_path=_dominant_runtime_scope(tech.evidence),
            evidence_level=tech.evidence_level,
            evidence=tech.evidence,
            rationale=rationale,
            prohibitions=_prohibitions,
            llm_generated=llm_generated,
            technology_name=technology_name,
        )
        suppress_reason = _governance_suppression_reason(model, tech, candidate)
        if suppress_reason:
            candidate.suppress_reason = suppress_reason
            candidates.append(candidate)
            continue

        analysis = analyze_enforceability(candidate)
        if not analysis.enforceable:
            candidate.suppress_reason = analysis.reason
        candidates.append(candidate)
    return candidates


_MIN_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def generate_v3_suggestions(
    model: RepositoryModel,
    existing_titles: set[str],
    next_id: int,
    min_confidence: str = "low",
) -> list[ADRSuggestion]:
    suggestions: list[ADRSuggestion] = []
    num = next_id

    min_level = _MIN_CONFIDENCE_ORDER.get(min_confidence, 0)
    candidate_levels = {
        EvidenceLevel.WEAK: 0,
        EvidenceLevel.MODERATE: 1,
        EvidenceLevel.STRONG: 2,
    }

    for candidate in model.governance_candidates:
        if candidate.suppress_reason:
            continue
        analysis = analyze_enforceability(candidate)
        if not analysis.enforceable:
            continue
        if candidate_levels.get(candidate.evidence_level, 0) < min_level:
            continue

        tech = _technology_for_governance_candidate(model, candidate)
        if tech is None:
            continue
        if _is_duplicate_title(candidate.title, existing_titles, tech.name):
            continue

        adr_id = f"ADR-{num:04d}"
        num += 1
        confidence = _confidence_from_level(candidate.evidence_level)
        prohibitions = [
            r.match for r in analysis.proposed_rules if r.type in {"dependency", "import"} and r.action == "block"
        ]
        prohibitions = sorted(set(prohibitions))

        adr = DecisionRecord(
            id=adr_id,
            title=candidate.title,
            status="proposed",
            severity="medium",
            type=candidate.decision_type,
            source="bootstrap",
            rationale=_adr_rationale(candidate, analysis),
            prohibitions=prohibitions,
            keywords=sorted({tech.name.lower(), tech.category, candidate.decision_type}),
            evidence=[_evidence_text(ev) for ev in candidate.evidence],
            confidence=confidence,
        )
        rules = [r.model_dump() for r in analysis.proposed_rules]
        suggestions.append(ADRSuggestion(tech=_to_detected_technology(tech), adr=adr, rules=rules))

    return suggestions


def analyze_enforceability(candidate: GovernanceDecisionCandidate) -> EnforceabilityAnalysis:
    template = _template_for_candidate(candidate)
    if not template:
        return EnforceabilityAnalysis(
            enforceable=False,
            level="none",
            reason="No deterministic rule strategy exists for this candidate.",
        )

    tech_name, _title, _decision_type, prohibitions, _rationale = template
    if tech_name in TOOLING_DECISIONS:
        return EnforceabilityAnalysis(
            enforceable=False,
            level="none",
            reason=f"{tech_name} is tooling; no strong deterministic governance rule exists yet.",
        )
    if tech_name in SUPPORTING_ONLY_DECISIONS:
        return EnforceabilityAnalysis(
            enforceable=False,
            level="weak",
            reason=f"{tech_name} evidence is supporting infrastructure, not enough for an ADR without stronger policy evidence.",
        )

    rules: list[RuleCandidate] = []
    for prohibition in prohibitions:
        rules.append(
            RuleCandidate(
                type="dependency",
                match=prohibition,
                action="block",
                scope_path=candidate.scope_path,
                rationale=f"{candidate.title} prohibits adding {prohibition} as a competing dependency.",
            )
        )
        rules.append(
            RuleCandidate(
                type="import",
                match=prohibition,
                action="block",
                scope_path=candidate.scope_path,
                rationale=f"{candidate.title} prohibits importing {prohibition} in governed source.",
            )
        )

    if tech_name == "SQLAlchemy":
        rules.append(
            RuleCandidate(
                type="import",
                match="sqlite3",
                action="warn",
                scope_path=candidate.scope_path,
                rationale="Relational persistence should go through SQLAlchemy rather than direct sqlite3 imports.",
            )
        )

    if candidate.evidence_level == EvidenceLevel.WEAK:
        return EnforceabilityAnalysis(
            enforceable=False,
            level="weak",
            reason="Evidence is too weak to create enforceable governance.",
            proposed_rules=rules,
        )

    if not rules:
        return EnforceabilityAnalysis(
            enforceable=False,
            level="none",
            reason="Candidate does not yield meaningful deterministic rules.",
        )

    level = "strong" if candidate.evidence_level == EvidenceLevel.STRONG else "moderate"
    return EnforceabilityAnalysis(
        enforceable=True,
        level=level,
        reason=f"{candidate.title} yields deterministic {level} rule coverage.",
        proposed_rules=rules,
    )


def _collect_dependency_evidence(repo: Path) -> list[Evidence]:
    evidence: list[Evidence] = []
    for path in _iter_named_files(repo, "requirements.txt"):
        role = _role_from_path(path, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        for dep in _parse_requirements(path):
            evidence.append(_dependency_evidence(repo, path, dep, role))

    for path in _iter_named_files(repo, "pyproject.toml"):
        role = _role_from_path(path, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        for dep, dep_role in _parse_pyproject(path):
            evidence.append(_dependency_evidence(repo, path, dep, dep_role or role))

    for path in _iter_named_files(repo, "package.json"):
        path_role = _role_from_path(path, repo)
        for dep, dep_role in _parse_package_json(path):
            if path_role in {EvidenceRole.TEST, EvidenceRole.EXAMPLE, EvidenceRole.TOOLING}:
                dep_role = path_role
            evidence.append(_dependency_evidence(repo, path, dep, dep_role))

    for path in _iter_named_files(repo, "go.mod"):
        role = _role_from_path(path, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        module = _parse_go_module(path)
        if module:
            evidence.append(
                _file_evidence(repo, path, "go.mod", EvidenceRole.RUNTIME, EvidenceLevel.STRONG, "Go module root.")
            )
            evidence.append(_dependency_evidence(repo, path, module, role))
        for dep in _parse_go_requires(path):
            evidence.append(_dependency_evidence(repo, path, dep, role))

    for path in _iter_named_files(repo, "Cargo.toml"):
        role = _role_from_path(path, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        package_name, deps = _parse_cargo(path)
        evidence.append(
            _file_evidence(
                repo, path, "Cargo.toml", EvidenceRole.RUNTIME, EvidenceLevel.STRONG, "Rust package manifest."
            )
        )
        if package_name:
            evidence.append(_dependency_evidence(repo, path, package_name, role))
        for dep, dep_role in deps:
            evidence.append(_dependency_evidence(repo, path, dep, dep_role or role))

    return evidence


def _collect_import_evidence(repo: Path) -> list[Evidence]:
    evidence: list[Evidence] = []
    for py_file in _iter_source_files(repo, "*.py"):
        role = _role_from_path(py_file, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError):
            continue
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0].lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0].lower())
            elif isinstance(node, ast.Call):
                call_name = _call_name(node)
                if call_name in {"FastAPI", "fastapi.FastAPI"}:
                    evidence.append(
                        Evidence(
                            kind="entrypoint",
                            value="fastapi_app",
                            source_path=_rel(repo, py_file),
                            role=role,
                            level=EvidenceLevel.STRONG if role == EvidenceRole.RUNTIME else EvidenceLevel.MODERATE,
                            scope_path=_scope_path(repo, py_file),
                            notes=["FastAPI application entrypoint detected."],
                        )
                    )
        for imp in imports:
            level = EvidenceLevel.STRONG if role == EvidenceRole.RUNTIME else EvidenceLevel.MODERATE
            evidence.append(
                Evidence(
                    kind="import",
                    value=imp,
                    source_path=_rel(repo, py_file),
                    role=role,
                    level=level,
                    scope_path=_scope_path(repo, py_file),
                )
            )

    import re

    # Simple JS/TS import extraction
    for js_file in _iter_source_files(repo, "*.[jt]s*"):
        role = _role_from_path(js_file, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
            # match `import ... from 'express'` or `require('express')`
            imports = set(
                re.findall(r"from\s+['\"]([^'\"]+)['\"]", content)
                + re.findall(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content)
            )
            for imp in imports:
                level = EvidenceLevel.STRONG if role == EvidenceRole.RUNTIME else EvidenceLevel.MODERATE
                evidence.append(
                    Evidence(
                        kind="import",
                        value=imp,
                        source_path=_rel(repo, js_file),
                        role=role,
                        level=level,
                        scope_path=_scope_path(repo, js_file),
                    )
                )
        except OSError:
            pass

    # Simple Go import extraction
    for go_file in _iter_source_files(repo, "*.go"):
        role = _role_from_path(go_file, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        try:
            content = go_file.read_text(encoding="utf-8", errors="replace")
            # match `import "github.com/gin-gonic/gin"`
            imports = set(re.findall(r"import\s+[\(\s]*['\"]([^'\"]+)['\"]", content))
            for imp in imports:
                level = EvidenceLevel.STRONG if role == EvidenceRole.RUNTIME else EvidenceLevel.MODERATE
                evidence.append(
                    Evidence(
                        kind="import",
                        value=imp,
                        source_path=_rel(repo, go_file),
                        role=role,
                        level=level,
                        scope_path=_scope_path(repo, go_file),
                    )
                )
        except OSError:
            pass

    return evidence


def _collect_file_evidence(repo: Path) -> list[Evidence]:
    evidence: list[Evidence] = []
    reg = _get_registry()
    file_rules_map: dict[str, tuple[str, EvidenceRole, EvidenceLevel, str]] = {}
    _role_map_s = {"runtime": EvidenceRole.RUNTIME, "unknown": EvidenceRole.UNKNOWN, "tooling": EvidenceRole.TOOLING}
    _level_map_s = {"strong": EvidenceLevel.STRONG, "moderate": EvidenceLevel.MODERATE, "weak": EvidenceLevel.WEAK}
    for rule in reg.file_evidence.values():
        file_rules_map[rule.file] = (
            rule.technology,
            _role_map_s.get(rule.role, EvidenceRole.RUNTIME),
            _level_map_s.get(rule.level, EvidenceLevel.MODERATE),
            rule.note,
        )
    for path in _iter_files(repo):
        rule = file_rules_map.get(path.name)
        if not rule:
            continue
        value, default_role, level, note = rule
        role = _role_from_path(path, repo)
        if role == EvidenceRole.UNKNOWN:
            role = default_role
        evidence.append(_file_evidence(repo, path, value, role, level, note))

    reg = _get_registry()
    _role_map_s = {"runtime": EvidenceRole.RUNTIME, "unknown": EvidenceRole.UNKNOWN, "tooling": EvidenceRole.TOOLING}
    _level_map_s = {"strong": EvidenceLevel.STRONG, "moderate": EvidenceLevel.MODERATE, "weak": EvidenceLevel.WEAK}
    for path in _iter_dirs(repo):
        lowered = path.name.lower()
        rel = _rel(repo, path)
        role = _role_from_path(path, repo)
        if role == EvidenceRole.UNKNOWN:
            role = EvidenceRole.RUNTIME
        matched = False
        for dir_rule in reg.dir_evidence:
            if dir_rule.path:
                if path.parts[-len(dir_rule.path.split("/")):] == tuple(dir_rule.path.split("/")) or rel == dir_rule.path:
                    matched = True
            elif dir_rule.directory and lowered == dir_rule.directory.lower():
                matched = True
            if matched:
                dr_role = _role_map_s.get(dir_rule.role, role)
                evidence.append(
                    Evidence(
                        kind="directory",
                        value=dir_rule.value,
                        source_path=rel,
                        role=dr_role,
                        level=_level_map_s.get(dir_rule.level, EvidenceLevel.MODERATE),
                        scope_path=_scope_path(repo, path),
                        notes=[dir_rule.note],
                    )
                )
                break

    reg = _get_registry()
    for lang_rule in reg.language_evidence:
        for path in repo.rglob(lang_rule.glob):
            if path.is_file() and _is_allowed_path(repo, path):
                evidence.append(
                    Evidence(
                        kind="language",
                        value=lang_rule.technology,
                        source_path=lang_rule.glob,
                        role=EvidenceRole.RUNTIME,
                        level=EvidenceLevel.STRONG,
                        scope_path=None,
                        notes=[f"{lang_rule.technology} source files detected."],
                    )
                )
                break

    return evidence


def _technology_for_evidence(ev: Evidence) -> tuple[str, str] | None:
    reg = _get_registry()
    value = ev.value.lower()
    if ev.kind in {"file", "directory", "language"}:
        resolved = reg.evidence_resolution.get(ev.value)
        if resolved:
            return resolved
        return None

    for dep_name, sig in TECH_SIGNATURES.items():
        name, category, aliases = sig
        if any(_match_dependency(value, alias.lower()) for alias in aliases + [dep_name]):
            return name, category
    return None


def _category_for_name(name: str) -> str:
    from decisiondrift.bootstrap.registry import category_for_tech
    return category_for_tech(_get_registry(), name)


def _aggregate_evidence_level(evidence: list[Evidence]) -> EvidenceLevel:
    has_runtime_strong = any(ev.role == EvidenceRole.RUNTIME and ev.level == EvidenceLevel.STRONG for ev in evidence)
    has_runtime_moderate = any(
        ev.role == EvidenceRole.RUNTIME and ev.level == EvidenceLevel.MODERATE for ev in evidence
    )
    runtime_count = sum(1 for ev in evidence if ev.role == EvidenceRole.RUNTIME)

    if has_runtime_strong and runtime_count >= 2:
        return EvidenceLevel.STRONG
    if has_runtime_strong or (has_runtime_moderate and runtime_count >= 2):
        return EvidenceLevel.MODERATE
    if any(ev.role == EvidenceRole.RUNTIME for ev in evidence):
        return EvidenceLevel.MODERATE
    return EvidenceLevel.WEAK


def _candidate_role(evidence: list[Evidence], level: EvidenceLevel) -> str:
    roles = {ev.role for ev in evidence}
    if EvidenceRole.RUNTIME in roles:
        if all(ev.kind == "dependency" and ev.value in TEST_DEPENDENCIES for ev in evidence):
            return "test"
        return "primary" if level in {EvidenceLevel.MODERATE, EvidenceLevel.STRONG} else "supporting"
    if roles <= {EvidenceRole.TEST}:
        return "test"
    if EvidenceRole.EXAMPLE in roles:
        return "example"
    if EvidenceRole.DEV in roles:
        return "dev"
    if EvidenceRole.TOOLING in roles:
        return "tooling"
    if EvidenceRole.OPTIONAL in roles:
        return "incidental"
    return "unknown"


def _candidate_contradictions(name: str, evidence: list[Evidence]) -> list[str]:
    contradictions: list[str] = []
    if all(
        ev.role
        in {EvidenceRole.DEV, EvidenceRole.TEST, EvidenceRole.EXAMPLE, EvidenceRole.TOOLING, EvidenceRole.OPTIONAL}
        for ev in evidence
    ):
        contradictions.append("No runtime evidence found.")
    if _category_for_name(name) == "framework" and not _has_framework_runtime_usage_evidence(evidence):
        contradictions.append("No runtime framework import, entrypoint, or route evidence found.")
    if name == "Strapi" and all(ev.value == "Strapi" and ev.kind == "file" for ev in evidence):
        contradictions.append("Only generic favicon evidence found.")
    if name == "FastAPI" and not any(ev.value.lower() == "fastapi" for ev in evidence):
        contradictions.append("No direct FastAPI evidence found.")
    return contradictions


def _suppression_reason(
    name: str,
    role: str,
    level: EvidenceLevel,
    evidence: list[Evidence],
    contradictions: list[str],
) -> str | None:
    if contradictions:
        return "; ".join(contradictions)
    if name.lower() in TEST_DEPENDENCIES or name in {"pytest", "Jest"}:
        return f"{name} is a testing technology, not a runtime governance decision."
    if role in {"dev", "test", "example", "tooling", "incidental", "unknown"}:
        return f"{name} evidence is {role}, not a runtime governance decision."
    if level == EvidenceLevel.WEAK:
        return f"{name} evidence is too weak for governance inference."
    return None


def _template_for_candidate(
    candidate: GovernanceDecisionCandidate,
) -> tuple[str, str, str, list[str], str] | None:
    for name, (title, decision_type, prohibitions, rationale) in DECISION_TEMPLATES.items():
        if candidate.title == title:
            return name, title, decision_type, prohibitions, rationale
    if candidate.llm_generated and candidate.prohibitions:
        return "LLM", candidate.title, candidate.decision_type, candidate.prohibitions, candidate.rationale
    return None


def _technology_for_governance_candidate(
    model: RepositoryModel,
    candidate: GovernanceDecisionCandidate,
) -> TechnologyCandidate | None:
    template = _template_for_candidate(candidate)
    if not template:
        return None
    name = template[0]
    if name == "LLM" and candidate.technology_name:
        name = candidate.technology_name
    for tech in model.technologies:
        if tech.name == name:
            return tech
    return None


def _adr_rationale(candidate: GovernanceDecisionCandidate, analysis: EnforceabilityAnalysis) -> str:
    evidence_lines = "\n".join(f"- {_evidence_text(ev)}" for ev in candidate.evidence[:8])
    rule_lines = "\n".join(f"- {rule.action}: {rule.type} `{rule.match}`" for rule in analysis.proposed_rules)
    return (
        f"## Context\n\n{candidate.rationale}\n\n"
        f"## Evidence\n\n{evidence_lines or '- No concrete evidence captured.'}\n\n"
        f"## Decision (candidate)\n\n{candidate.title}.\n\n"
        f"## Enforceability\n\n{analysis.reason}\n\n{rule_lines}\n\n"
        f"## Confidence\n\n{candidate.evidence_level.value}. "
        "This decision is inferred from repository evidence and requires human approval."
    )


def _to_detected_technology(tech: TechnologyCandidate):
    from decisiondrift.bootstrap.detectors import DetectedTechnology

    confidence = {
        EvidenceLevel.STRONG: 0.9,
        EvidenceLevel.MODERATE: 0.7,
        EvidenceLevel.WEAK: 0.3,
    }[tech.evidence_level]
    return DetectedTechnology(
        category=tech.category,
        name=tech.name,
        confidence=confidence,
        evidence=[_evidence_text(ev) for ev in tech.evidence],
    )


def _confidence_from_level(level: EvidenceLevel) -> ConfidenceLevel:
    if level == EvidenceLevel.STRONG:
        return ConfidenceLevel.HIGH
    if level == EvidenceLevel.MODERATE:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _is_duplicate_title(title: str, existing_titles: set[str], tech_name: str | None = None) -> bool:
    tl = title.lower()
    tech_prefix = f"use {tech_name.lower()} " if tech_name else None
    for existing in existing_titles:
        existing_l = existing.lower()
        if existing_l == tl:
            return True
        if tech_prefix and existing_l.startswith(tech_prefix) and tl.startswith(tech_prefix):
            return True
    return False


def _evidence_text(ev: Evidence) -> str:
    detail = f"{ev.kind}: {ev.value} ({ev.role.value}, {ev.level.value}) at {ev.source_path}"
    if ev.notes:
        detail += f" - {'; '.join(ev.notes)}"
    return detail


def _dependency_evidence(repo: Path, path: Path, dep: str, role: EvidenceRole) -> Evidence:
    if dep.lower() in TEST_DEPENDENCIES:
        role = EvidenceRole.TEST
    level = EvidenceLevel.MODERATE if role == EvidenceRole.RUNTIME else EvidenceLevel.WEAK
    return Evidence(
        kind="dependency",
        value=dep.lower(),
        source_path=_rel(repo, path),
        role=role,
        level=level,
        scope_path=_scope_path(repo, path),
    )


def _file_evidence(
    repo: Path,
    path: Path,
    value: str,
    role: EvidenceRole,
    level: EvidenceLevel,
    note: str,
) -> Evidence:
    return Evidence(
        kind="file",
        value=value,
        source_path=_rel(repo, path),
        role=role,
        level=level,
        scope_path=_scope_path(repo, path),
        notes=[note],
    )


_ROLE_MAP = {
    "runtime": EvidenceRole.RUNTIME,
    "dev": EvidenceRole.DEV,
    "test": EvidenceRole.TEST,
    "optional": EvidenceRole.OPTIONAL,
    "tooling": EvidenceRole.TOOLING,
}


def _role_from_section(section: str) -> EvidenceRole:
    return _ROLE_MAP.get(section, EvidenceRole.UNKNOWN)


def _parse_requirements(path: Path) -> list[str]:
    return _parse_requirements_txt_shared(path)


def _parse_pyproject(path: Path) -> list[tuple[str, EvidenceRole | None]]:
    return [(dep, _role_from_section(role)) for dep, role in _parse_pyproject_toml_shared(path)]


def _parse_package_json(path: Path) -> list[tuple[str, EvidenceRole]]:
    return [(dep, _role_from_section(role)) for dep, role in _parse_package_json_shared(path)]


def _parse_go_module(path: Path) -> str | None:
    module, _ = _parse_go_mod_shared(path)
    return module


def _parse_go_requires(path: Path) -> list[str]:
    _, deps = _parse_go_mod_shared(path)
    return deps


def _parse_cargo(path: Path) -> tuple[str | None, list[tuple[str, EvidenceRole | None]]]:
    pkg, deps = _parse_cargo_toml_shared(path)
    return pkg, [(dep, _role_from_section(role)) for dep, role in deps]


def _role_from_path(path: Path, repo: Path) -> EvidenceRole:
    try:
        parts = path.relative_to(repo).parts
    except ValueError:
        return EvidenceRole.UNKNOWN
    lowered = {part.lower() for part in parts}
    if lowered & {"tests", "test", "testing", "__tests__", "fixtures"}:
        return EvidenceRole.TEST
    if any(part.startswith("test") or "fixture" in part for part in lowered):
        return EvidenceRole.TEST
    if lowered & {"examples", "example", "demo", "demos", "samples", "sample"}:
        return EvidenceRole.EXAMPLE
    if lowered & {"docs", "doc"}:
        return EvidenceRole.EXAMPLE
    if lowered & {".github", "scripts", "tools", "tooling", "build", "cli"}:
        return EvidenceRole.TOOLING
    if any(part.startswith(".") for part in parts):
        return EvidenceRole.TOOLING
    return EvidenceRole.UNKNOWN


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        current = func.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def _has_framework_runtime_usage(tech: TechnologyCandidate) -> bool:
    return _has_framework_runtime_usage_evidence(tech.evidence)


def _has_framework_runtime_usage_evidence(evidence: list[Evidence]) -> bool:
    for ev in evidence:
        if ev.role != EvidenceRole.RUNTIME:
            continue
        if ev.kind in {"import", "entrypoint"}:
            return True
        if ev.kind == "directory" and ev.value == "fastapi_routers":
            return True
        if ev.kind == "file" and ev.value == "Django":
            return True
    return False


def _scope_path(repo: Path, path: Path) -> str | None:
    try:
        rel = path.relative_to(repo)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) > 1:
        return parts[0]
    return None


def _match_dependency(actual: str, expected: str) -> bool:
    return (
        actual == expected
        or actual.startswith(expected + ".")
        or actual.startswith(expected + "-")
        or actual.startswith(expected + "_")
        or actual.endswith("/" + expected)
    )


def _level_rank(level: EvidenceLevel) -> int:
    return {
        EvidenceLevel.WEAK: 1,
        EvidenceLevel.MODERATE: 2,
        EvidenceLevel.STRONG: 3,
    }[level]


EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    ".tox",
    ".nox",
    "dist",
    "build",
    ".eggs",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".gradle",
}


def _iter_named_files(repo: Path, name: str) -> list[Path]:
    return [path for path in repo.rglob(name) if _is_allowed_path(repo, path)]


def _iter_source_files(repo: Path, glob: str) -> list[Path]:
    return [path for path in repo.rglob(glob) if path.is_file() and _is_allowed_path(repo, path)]


def _iter_files(repo: Path) -> list[Path]:
    return [path for path in repo.rglob("*") if path.is_file() and _is_allowed_path(repo, path)]


def _iter_dirs(repo: Path) -> list[Path]:
    return [path for path in repo.rglob("*") if path.is_dir() and _is_allowed_path(repo, path)]


def _is_allowed_path(repo: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(repo).parts
    except ValueError:
        return False
    if path.is_symlink():
        return False
    for parent in path.parents:
        if parent == repo:
            break
        if parent.is_symlink():
            return False
    return not any(part in EXCLUDE_DIRS for part in parts)


def _rel(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)
