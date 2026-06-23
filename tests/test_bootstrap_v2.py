from __future__ import annotations

from pathlib import Path

from decisiondrift.bootstrap.architecture import ArchitectureModel
from decisiondrift.bootstrap.detectors import (
    DetectionContext,
    DetectedTechnology,
    _scan_requirements_txt,
    _scan_pyproject_toml_deps,
    _scan_package_json_deps,
    collect_deps,
    detect_technologies,
)
from decisiondrift.bootstrap.structure_scan import ProjectStructure, scan_repo


class TestCollectDeps:
    def test_requirements_txt(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("flask==2.0\nredis>=4.0\n")
        deps = collect_deps(tmp_path)
        assert "flask" in deps
        assert "redis" in deps

    def test_pyproject_toml_deps(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["fastapi>=0.100", "uvicorn"]\n'
        )
        deps = collect_deps(tmp_path)
        assert "fastapi" in deps
        assert "uvicorn" in deps

    def test_package_json(self, tmp_path: Path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"express": "^4.0", "react": "^18.0"}}'
        )
        deps = collect_deps(tmp_path)
        assert "express" in deps
        assert "react" in deps

    def test_no_dep_files(self, tmp_path: Path):
        deps = collect_deps(tmp_path)
        assert deps == []


class TestDetectTechnologies:
    def test_detect_fastapi_from_dep(self):
        ctx = DetectionContext(
            repo_path=Path("/fake"),
            deps=["fastapi", "uvicorn"],
            imports=[],
            structure=ProjectStructure(root="/fake"),
        )
        findings = detect_technologies(ctx)
        names = [f.name for f in findings]
        assert "FastAPI" in names

    def test_detect_flask_from_import(self):
        ctx = DetectionContext(
            repo_path=Path("/fake"),
            deps=[],
            imports=["flask"],
            structure=ProjectStructure(root="/fake"),
        )
        findings = detect_technologies(ctx)
        names = [f.name for f in findings]
        assert "Flask" in names

    def test_detect_docker_from_file(self, tmp_path: Path):
        (tmp_path / "Dockerfile").write_text("FROM python")
        structure = scan_repo(tmp_path)
        ctx = DetectionContext(
            repo_path=tmp_path,
            deps=[],
            imports=[],
            structure=structure,
        )
        findings = detect_technologies(ctx)
        names = [f.name for f in findings]
        assert "Docker" in names

    def test_detect_no_technologies(self):
        ctx = DetectionContext(
            repo_path=Path("/fake"),
            deps=[],
            imports=[],
            structure=ProjectStructure(root="/fake"),
        )
        findings = detect_technologies(ctx)
        assert len(findings) == 0

    def test_detect_multiple_technologies(self, tmp_path: Path):
        (tmp_path / "Dockerfile").write_text("FROM python")
        (tmp_path / "requirements.txt").write_text("fastapi\ncelery\n")
        structure = scan_repo(tmp_path)
        ctx = DetectionContext(
            repo_path=tmp_path,
            deps=collect_deps(tmp_path),
            imports=[],
            structure=structure,
        )
        findings = detect_technologies(ctx)
        names = [f.name for f in findings]
        assert "FastAPI" in names
        assert "Celery" in names
        assert "Docker" in names


class TestMatchDep:
    def test_exact_match(self):
        from decisiondrift.bootstrap.detectors import _match_dep
        assert _match_dep("flask", "flask")
        assert _match_dep("fastapi", "fastapi")

    def test_submodule_match(self):
        from decisiondrift.bootstrap.detectors import _match_dep
        assert _match_dep("sqlalchemy.orm", "sqlalchemy")
        assert _match_dep("sqlalchemy.ext.declarative", "sqlalchemy")

    def test_go_module_match(self):
        from decisiondrift.bootstrap.detectors import _match_dep
        assert _match_dep("github.com/gin-gonic/gin", "gin-gonic/gin")
        assert _match_dep("github.com/goccy/go-json", "go-json")

    def test_java_artifact_match(self):
        from decisiondrift.bootstrap.detectors import _match_dep
        assert _match_dep("spring-boot-starter-web", "spring-boot")
        assert _match_dep("spring-boot-starter-actuator", "spring-boot")

    def test_extras_match(self):
        from decisiondrift.bootstrap.detectors import _match_dep
        assert _match_dep("psycopg[binary]", "psycopg")
        assert _match_dep("pydantic[email]", "pydantic")

    def test_no_match(self):
        from decisiondrift.bootstrap.detectors import _match_dep
        assert not _match_dep("flask", "django")
        assert not _match_dep("requests", "fastapi")


class TestArchitectureModel:
    def test_empty_model(self):
        model = ArchitectureModel([])
        assert model.count() == 0
        assert model.summary() is not None
        assert model.coverage(set()) == 0.0

    def test_model_with_findings(self):
        findings = [
            DetectedTechnology(category="framework", name="FastAPI", confidence=0.9, evidence=["dep: fastapi"]),
            DetectedTechnology(category="cache", name="Redis", confidence=0.8, evidence=["dep: redis"]),
        ]
        model = ArchitectureModel(findings)
        assert model.count() == 2
        assert len(model.by_category("framework")) == 1

    def test_coverage(self):
        findings = [
            DetectedTechnology(category="framework", name="FastAPI", confidence=0.9, evidence=[]),
            DetectedTechnology(category="cache", name="Redis", confidence=0.8, evidence=[]),
            DetectedTechnology(category="queue", name="Celery", confidence=0.9, evidence=[]),
        ]
        model = ArchitectureModel(findings)
        # 2 out of 3 covered
        cov = model.coverage({"fastapi", "redis"})
        assert cov == 2.0 / 3.0

    def test_coverage_no_findings(self):
        model = ArchitectureModel([])
        assert model.coverage({"fastapi"}) == 0.0

    def test_architecture_json(self):
        findings = [
            DetectedTechnology(category="framework", name="FastAPI", confidence=0.95, evidence=["dep: fastapi"]),
            DetectedTechnology(category="cache", name="Redis", confidence=0.80, evidence=["dep: redis"]),
        ]
        model = ArchitectureModel(findings)
        aj = model.architecture_json()
        assert aj["schema_version"] == "1"
        assert len(aj["technologies"]) == 2
        techs = {t["name"]: t for t in aj["technologies"]}
        assert techs["FastAPI"]["category"] == "framework"
        assert techs["FastAPI"]["confidence"] == 0.95
        assert techs["Redis"]["evidence"] == ["dep: redis"]

    def test_report_missing(self):
        findings = [
            DetectedTechnology(category="cache", name="Redis", confidence=0.85, evidence=[]),
            DetectedTechnology(category="queue", name="Celery", confidence=0.9, evidence=[]),
        ]
        model = ArchitectureModel(findings)
        missing = model.report_missing({"redis"})
        assert "Celery" in missing
        assert "Redis" not in missing
