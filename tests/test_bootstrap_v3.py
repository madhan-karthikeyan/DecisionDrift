from __future__ import annotations

from pathlib import Path

from decisiondrift.bootstrap.bootstrapper import bootstrap
from decisiondrift.bootstrap.v3 import (
    EvidenceLevel,
    build_repository_model,
)


def _write_payment_service(repo: Path) -> None:
    (repo / "app" / "routers").mkdir(parents=True)
    (repo / "app" / "services").mkdir()
    (repo / "app" / "db").mkdir()
    (repo / "tests").mkdir()
    (repo / "alembic").mkdir()
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "app" / "main.py").write_text("from fastapi import FastAPI\n\napp = FastAPI()\n")
    (repo / "requirements.txt").write_text("fastapi\nuvicorn\nsqlalchemy\nalembic\npsycopg2\nredis\ncelery\npytest\n")
    (repo / "Dockerfile").write_text("FROM python:3.11\n")
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: ci\n")
    (repo / "pyproject.toml").write_text('[project]\nname = "payment-service"\n')


class TestBootstrapV3Evidence:
    def test_favicon_only_strapi_is_suppressed(self, tmp_path: Path):
        (tmp_path / "favicon.png").write_text("fake")

        model = build_repository_model(tmp_path)

        strapi = next(t for t in model.technologies if t.name == "Strapi")
        assert strapi.evidence_level == EvidenceLevel.WEAK
        assert strapi.suppress_reason is not None
        assert "favicon" in strapi.suppress_reason.lower()
        assert bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True) == []

    def test_uvicorn_dependency_does_not_imply_fastapi(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("uvicorn\n")

        model = build_repository_model(tmp_path)
        names = {t.name for t in model.technologies}

        assert "Uvicorn" in names
        assert "FastAPI" not in names
        assert bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True) == []

    def test_dev_dependency_express_is_not_governance_decision(self, tmp_path: Path):
        (tmp_path / "package.json").write_text('{"devDependencies": {"express": "^4.18.0"}}')

        model = build_repository_model(tmp_path)

        express = next(t for t in model.technologies if t.name == "Express")
        assert express.role == "dev"
        assert express.suppress_reason is not None
        assert bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True) == []

    def test_test_dependency_django_is_not_repository_architecture(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "pkg"\n[project.optional-dependencies]\ntest = ["django", "pytest"]\n'
        )

        model = build_repository_model(tmp_path)

        django = next(t for t in model.technologies if t.name == "Django")
        assert django.role == "test"
        assert django.suppress_reason is not None
        assert bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True) == []

    def test_framework_repository_does_not_generate_use_self_adr(self, tmp_path: Path):
        repo = tmp_path / "gin"
        repo.mkdir()
        (repo / "go.mod").write_text("module github.com/gin-gonic/gin\n")

        model = build_repository_model(repo)

        gin = next(t for t in model.technologies if t.name == "Gin")
        assert model.repository_role == "framework"
        assert gin.suppress_reason is not None
        assert "repository product" in gin.suppress_reason
        assert bootstrap(repo, repo / "docs/adr", dry_run=True) == []


class TestBootstrapV3Governance:
    def test_fastapi_runtime_dependency_generates_enforceable_candidate(self, tmp_path: Path):
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")

        result = bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True)

        assert len(result) == 1
        assert result[0].adr.title == "Use FastAPI for HTTP APIs"
        assert {r["match"] for r in result[0].rules} == {"flask", "django"}

    def test_payment_service_generates_only_enforceable_decisions(self, tmp_path: Path):
        repo = tmp_path / "payment-service"
        repo.mkdir()
        _write_payment_service(repo)

        model = build_repository_model(repo)
        result = bootstrap(repo, repo / "docs/adr", dry_run=True)

        assert model.repository_role == "api_service"
        assert model.repository_subtype == "async_python_api"

        techs = {t.name: t for t in model.technologies}
        assert techs["FastAPI"].role == "primary"
        assert techs["FastAPI"].evidence_level == EvidenceLevel.STRONG
        assert techs["SQLAlchemy"].role == "supporting"
        assert techs["Celery"].role == "supporting"
        assert techs["pytest"].role == "test"
        assert techs["Docker"].suppress_reason is not None
        assert techs["GitHub Actions"].role == "tooling"

        assert [s.adr.title for s in result] == [
            "Use FastAPI for HTTP APIs",
            "Use SQLAlchemy for relational persistence",
            "Use Celery for asynchronous jobs",
        ]

        suppressions = {c.title: c.suppress_reason for c in model.governance_candidates if c.suppress_reason}
        assert "Use PostgreSQL for Persistent Storage" in suppressions
        assert "Use Redis for Caching" in suppressions
        assert "Use Docker for Containerized Runtime" not in [s.adr.title for s in result]
        assert "Use Alembic for Database Migrations" in suppressions

    def test_framework_repo_suppresses_implementation_technology_adrs(self, tmp_path: Path):
        repo = tmp_path / "strapi"
        repo.mkdir()
        (repo / "package.json").write_text(
            '{"dependencies": {"react": "^18.0.0", "jsonwebtoken": "^9.0.0", "@strapi/strapi": "^5.0.0"}}'
        )

        model = build_repository_model(repo)
        result = bootstrap(repo, repo / "docs/adr", dry_run=True)

        assert model.repository_role == "framework"
        assert result == []
        suppressions = {c.title: c.suppress_reason for c in model.governance_candidates if c.suppress_reason}
        assert suppressions["Use React for Frontend UI"].startswith("Framework/product repositories")
        assert suppressions["Use JWT for API Authentication"].startswith("Framework/product repositories")

    def test_library_sqlalchemy_integration_does_not_create_data_access_adr(self, tmp_path: Path):
        repo = tmp_path / "library"
        (repo / "src" / "pkg").mkdir(parents=True)
        (repo / "src" / "pkg" / "integration.py").write_text("import sqlalchemy\n")
        (repo / "pyproject.toml").write_text('[project]\nname = "library"\ndependencies = ["sqlalchemy"]\n')

        model = build_repository_model(repo)
        result = bootstrap(repo, repo / "docs/adr", dry_run=True)

        assert model.repository_role == "library"
        assert result == []
        suppressions = {c.title: c.suppress_reason for c in model.governance_candidates if c.suppress_reason}
        assert suppressions["Use SQLAlchemy for relational persistence"].startswith("Data-access evidence")

    def test_frontend_component_can_generate_scoped_react_adr(self, tmp_path: Path):
        repo = tmp_path / "product"
        (repo / "ui").mkdir(parents=True)
        (repo / "ui" / "package.json").write_text('{"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}')

        model = build_repository_model(repo)
        result = bootstrap(repo, repo / "docs/adr", dry_run=True)

        assert model.repository_role == "frontend_app"
        assert [s.adr.title for s in result] == ["Use React for Frontend UI"]
        assert result[0].rules[0]["scope_path"] == "ui"

    def test_min_confidence_filters_low_evidence_candidates(self, tmp_path: Path):
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-service"\ndependencies = ["celery", "redis"]\n')

        all_candidates = bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True, min_confidence="low")
        high_only = bootstrap(tmp_path, tmp_path / "docs/adr", dry_run=True, min_confidence="high")

        assert len(all_candidates) > 0
        assert len(high_only) <= len(all_candidates)
        assert len(high_only) == 1
        assert high_only[0].adr.title == "Use FastAPI for HTTP APIs"
