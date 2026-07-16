from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from decisiondrift.bootstrap.registry import (
    TechnologyRegistry,
    category_for_tech,
    governance_template_for_tech,
    is_test_dependency,
    is_tooling_decision,
    is_supporting_only,
    load_registry,
    resolve_evidence_value,
    resolve_technology,
)


@pytest.fixture
def registry() -> TechnologyRegistry:
    return load_registry()


class TestRegistryLoader:
    def test_loads_default_registry(self, registry: TechnologyRegistry):
        assert registry.schema_version == 1
        assert len(registry.technologies) >= 30
        assert len(registry.governance_templates) >= 20

    def test_contains_fastapi(self, registry: TechnologyRegistry):
        assert "FastAPI" in registry.technologies
        profile = registry.technologies["FastAPI"]
        assert profile.category == "framework"
        assert profile.ecosystem == "Python"

    def test_contains_flask_governance(self, registry: TechnologyRegistry):
        tmpl = governance_template_for_tech(registry, "Flask")
        assert tmpl is not None
        assert "flask" in tmpl.title.lower()
        assert "fastapi" in tmpl.prohibitions
        assert "django" in tmpl.prohibitions

    def test_self_framework_repos(self, registry: TechnologyRegistry):
        assert registry.self_framework_repos["fastapi"] == "FastAPI"
        assert registry.self_framework_repos["django"] == "Django"
        assert registry.self_framework_repos["gin"] == "Gin"

    def test_test_dependencies(self, registry: TechnologyRegistry):
        assert is_test_dependency(registry, "pytest")
        assert is_test_dependency(registry, "unittest")
        assert not is_test_dependency(registry, "flask")


class TestRegistryLookups:
    def test_resolve_known_dependency(self, registry: TechnologyRegistry):
        name, cat = resolve_technology(registry, "fastapi")
        assert name == "FastAPI"
        assert cat == "framework"

    def test_resolve_known_dependency_case_insensitive(self, registry: TechnologyRegistry):
        name, cat = resolve_technology(registry, "FastAPI")
        assert name == "FastAPI"

    def test_resolve_unknown_dependency(self, registry: TechnologyRegistry):
        assert resolve_technology(registry, "some_random_unknown_pkg_xyz") is None

    def test_resolve_evidence_value(self, registry: TechnologyRegistry):
        resolved = resolve_evidence_value(registry, "Docker")
        assert resolved is not None
        assert resolved[0] == "Docker"

    def test_resolve_unknown_evidence(self, registry: TechnologyRegistry):
        assert resolve_evidence_value(registry, "nonexistent_value") is None

    def test_category_for_known(self, registry: TechnologyRegistry):
        assert category_for_tech(registry, "FastAPI") == "framework"
        assert category_for_tech(registry, "PostgreSQL") == "database"

    def test_category_for_unknown_falls_back(self, registry: TechnologyRegistry):
        cat = category_for_tech(registry, "NonExistentTech")
        assert cat == "tooling"


class TestEnforceabilityFlags:
    def test_tooling_decisions(self, registry: TechnologyRegistry):
        assert is_tooling_decision(registry, "Docker")
        assert is_tooling_decision(registry, "GitHub Actions")
        assert not is_tooling_decision(registry, "FastAPI")

    def test_supporting_only_decisions(self, registry: TechnologyRegistry):
        assert is_supporting_only(registry, "PostgreSQL")
        assert is_supporting_only(registry, "Redis")
        assert is_supporting_only(registry, "Alembic")
        assert not is_supporting_only(registry, "FastAPI")


class TestRegistryFileEvidence:
    def test_file_evidence_rules(self, registry: TechnologyRegistry):
        assert "Dockerfile" in registry.file_evidence
        rule = registry.file_evidence["Dockerfile"]
        assert rule.technology == "Docker"
        assert rule.level == "strong"
        assert rule.role == "runtime"

    def test_dir_evidence_rules(self, registry: TechnologyRegistry):
        dir_rules = registry.dir_evidence
        dir_names = [d.directory for d in dir_rules]
        assert "routers" in dir_names
        assert "migrations" in dir_names
        assert "tasks" in dir_names

    def test_language_evidence(self, registry: TechnologyRegistry):
        lang_globs = [l.glob for l in registry.language_evidence]
        assert "*.go" in lang_globs
        assert "*.rs" in lang_globs
        assert "*.ts" in lang_globs


class TestRegistrySchemaVersion:
    def test_yaml_has_schema_version(self):
        path = Path(__file__).parents[2] / "src" / "decisiondrift" / "bootstrap" / "default_registry.yaml"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data.get("schema_version") == 1
