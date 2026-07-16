from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_REGISTRY_PATH = Path(__file__).parent / "default_registry.yaml"


@dataclass
class TechnologyProfile:
    name: str
    ecosystem: str
    category: str
    aliases: list[str]
    detection: dict[str, Any]
    confidence: float


@dataclass
class GovernanceTemplate:
    technology: str
    decision_type: str
    title: str
    prohibitions: list[str]
    rationale: str


@dataclass
class FileEvidenceRule:
    file: str
    technology: str
    role: str
    level: str
    note: str


@dataclass
class DirEvidenceRule:
    directory: str
    technology: str
    value: str
    role: str
    level: str
    note: str
    path: str = ""


@dataclass
class LanguageEvidenceRule:
    glob: str
    technology: str


@dataclass
class TechnologyRegistry:
    schema_version: int
    technologies: dict[str, TechnologyProfile]
    governance_templates: dict[str, GovernanceTemplate]
    self_framework_repos: dict[str, str]
    test_dependencies: set[str]
    file_evidence: dict[str, FileEvidenceRule]
    dir_evidence: list[DirEvidenceRule]
    language_evidence: list[LanguageEvidenceRule]
    evidence_resolution: dict[str, tuple[str, str]]
    category_overrides: dict[str, str]
    tooling_decisions: set[str]
    supporting_only_decisions: set[str]


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return raw


def _build_technologies(raw: dict[str, Any]) -> dict[str, TechnologyProfile]:
    techs: dict[str, TechnologyProfile] = {}
    for entry in raw.get("technologies", []):
        p = TechnologyProfile(
            name=entry["name"],
            ecosystem=entry.get("ecosystem", ""),
            category=entry["category"],
            aliases=entry.get("aliases", []),
            detection=entry.get("detection", {}),
            confidence=entry.get("confidence", 0.8),
        )
        techs[p.name] = p
        for alias in p.aliases:
            techs.setdefault(alias, p)
    return techs


def _build_governance_templates(raw: dict[str, Any]) -> dict[str, GovernanceTemplate]:
    templates: dict[str, GovernanceTemplate] = {}
    for entry in raw.get("governance_templates", []):
        t = GovernanceTemplate(
            technology=entry["technology"],
            decision_type=entry["decision_type"],
            title=entry["title"],
            prohibitions=entry.get("prohibitions", []),
            rationale=entry.get("rationale", ""),
        )
        templates[t.technology] = t
    return templates


def _build_file_evidence(raw: dict[str, Any]) -> dict[str, FileEvidenceRule]:
    rules: dict[str, FileEvidenceRule] = {}
    for entry in raw.get("file_evidence", []):
        r = FileEvidenceRule(
            file=entry["file"],
            technology=entry["technology"],
            role=entry["role"],
            level=entry["level"],
            note=entry.get("note", ""),
        )
        rules[r.file] = r
    return rules


def _build_dir_evidence(raw: dict[str, Any]) -> list[DirEvidenceRule]:
    rules: list[DirEvidenceRule] = []
    for entry in raw.get("dir_evidence", []):
        r = DirEvidenceRule(
            directory=entry.get("directory", ""),
            technology=entry["technology"],
            value=entry["value"],
            role=entry["role"],
            level=entry["level"],
            note=entry.get("note", ""),
            path=entry.get("path", ""),
        )
        rules.append(r)
    return rules


def _build_language_evidence(raw: dict[str, Any]) -> list[LanguageEvidenceRule]:
    rules: list[LanguageEvidenceRule] = []
    for entry in raw.get("language_evidence", []):
        rules.append(LanguageEvidenceRule(glob=entry["glob"], technology=entry["technology"]))
    return rules


def _build_evidence_resolution(raw: dict[str, Any]) -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for key, val in raw.get("evidence_resolution", {}).items():
        mapping[key] = (val[0], val[1])
    return mapping


def _build_category_overrides(raw: dict[str, Any]) -> dict[str, str]:
    return dict(raw.get("category_overrides", {}))


def load_registry(
    bundled_path: Path | None = None,
    global_cache_path: Path | None = None,
    project_cache_path: Path | None = None,
) -> TechnologyRegistry:
    bundled = _load_yaml(bundled_path or _DEFAULT_REGISTRY_PATH)
    global_cache = _load_yaml(global_cache_path) if global_cache_path and global_cache_path.exists() else {}
    project_cache = _load_yaml(project_cache_path) if project_cache_path and project_cache_path.exists() else {}
    schema = bundled.get("schema_version", 1)

    techs: dict[str, TechnologyProfile] = {}
    gov_templates: dict[str, GovernanceTemplate] = {}
    self_framework: dict[str, str] = {}
    test_deps: set[str] = set()
    file_rules: dict[str, FileEvidenceRule] = {}
    dir_rules: list[DirEvidenceRule] = []
    lang_rules: list[LanguageEvidenceRule] = []
    ev_resolution: dict[str, tuple[str, str]] = {}
    cat_overrides: dict[str, str] = {}
    tooling: set[str] = set()
    supporting: set[str] = set()

    for layer in (bundled, global_cache, project_cache):
        _merge_into(techs, _build_technologies(layer))
        _merge_into(gov_templates, _build_governance_templates(layer))
        self_framework.update(layer.get("self_framework_repos", {}))
        test_deps.update(layer.get("test_dependencies", []))
        _merge_into(file_rules, _build_file_evidence(layer))
        dir_rules.extend(_build_dir_evidence(layer))
        lang_rules.extend(_build_language_evidence(layer))
        ev_resolution.update(_build_evidence_resolution(layer))
        cat_overrides.update(_build_category_overrides(layer))
        tooling.update(layer.get("tooling_decisions", []))
        supporting.update(layer.get("supporting_only_decisions", []))

    return TechnologyRegistry(
        schema_version=schema,
        technologies=techs,
        governance_templates=gov_templates,
        self_framework_repos=self_framework,
        test_dependencies=test_deps,
        file_evidence=file_rules,
        dir_evidence=dir_rules,
        language_evidence=lang_rules,
        evidence_resolution=ev_resolution,
        category_overrides=cat_overrides,
        tooling_decisions=tooling,
        supporting_only_decisions=supporting,
    )


def _merge_into(target: dict, source: dict) -> None:
    target.update(source)


def resolve_technology(registry: TechnologyRegistry, dep_value: str) -> tuple[str, str] | None:
    dep_lower = dep_value.lower()
    for name, profile in registry.technologies.items():
        dep_names = profile.detection.get("dependencies", [])
        import_names = profile.detection.get("imports", [])
        all_names = dep_names + import_names + [name.lower()]
        for n in all_names:
            if n.lower() == dep_lower:
                return profile.name, profile.category
    return None


def resolve_evidence_value(registry: TechnologyRegistry, value: str) -> tuple[str, str] | None:
    return registry.evidence_resolution.get(value)


def governance_template_for_tech(registry: TechnologyRegistry, tech_name: str) -> GovernanceTemplate | None:
    return registry.governance_templates.get(tech_name)


def category_for_tech(registry: TechnologyRegistry, tech_name: str) -> str:
    profile = registry.technologies.get(tech_name)
    if profile:
        return profile.category
    return registry.category_overrides.get(tech_name, "tooling")


def is_tooling_decision(registry: TechnologyRegistry, tech_name: str) -> bool:
    return tech_name in registry.tooling_decisions


def is_supporting_only(registry: TechnologyRegistry, tech_name: str) -> bool:
    return tech_name in registry.supporting_only_decisions


def is_test_dependency(registry: TechnologyRegistry, dep_name: str) -> bool:
    return dep_name.lower() in registry.test_dependencies
