from __future__ import annotations

from pathlib import Path

from decisiondrift.bootstrap.bootstrapper import bootstrap
from decisiondrift.bootstrap.v3 import (
    build_repository_model,
)


class TestBootstrapRepositoryScanning:
    def test_empty_repo_returns_no_candidates(self, empty_repo: Path):
        result = bootstrap(empty_repo, empty_repo / "docs/adr", dry_run=True)
        assert result == []

    def test_empty_repo_model_has_no_technologies(self, empty_repo: Path):
        model = build_repository_model(empty_repo)
        assert len(model.technologies) == 0
        assert model.repository_role == "unknown"

    def test_flask_repo_detects_flask(self, flask_repo: Path):
        model = build_repository_model(flask_repo)
        names = {t.name for t in model.technologies}
        assert "Flask" in names

    def test_flask_repo_role_is_api_service(self, flask_repo: Path):
        model = build_repository_model(flask_repo)
        assert model.repository_role == "api_service"

    def test_fastapi_repo_detects_technologies(self, fastapi_repo: Path):
        model = build_repository_model(fastapi_repo)
        names = {t.name for t in model.technologies}
        assert "FastAPI" in names
        assert "SQLAlchemy" in names
        assert "PostgreSQL" in names

    def test_node_repo_detects_express(self, node_repo: Path):
        model = build_repository_model(node_repo)
        names = {t.name for t in model.technologies}
        assert "Express" in names

    def test_go_repo_detects_go_language(self, go_repo: Path):
        model = build_repository_model(go_repo)
        names = {t.name for t in model.technologies}
        assert "Go" in names

    def test_rust_repo_detects_tokio(self, rust_repo: Path):
        model = build_repository_model(rust_repo)
        names = {t.name for t in model.technologies}
        assert "Tokio" in names

    def test_java_repo_returns_model(self, java_repo: Path):
        model = build_repository_model(java_repo)
        assert model is not None


class TestBootstrapArchitectureDetection:
    def test_nested_directories_scanned(self, tmp_path: Path):
        repo = tmp_path / "nested"
        repo.mkdir()
        (repo / "src" / "api" / "routes").mkdir(parents=True)
        (repo / "src" / "api" / "routes" / "users.py").write_text(
            "from fastapi import APIRouter\nrouter = APIRouter()\n"
        )
        (repo / "src" / "api" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        (repo / "requirements.txt").write_text("fastapi\nuvicorn\n")
        model = build_repository_model(repo)
        names = {t.name for t in model.technologies}
        assert "FastAPI" in names

    def test_unsupported_files_do_not_crash(self, tmp_path: Path):
        repo = tmp_path / "weird"
        repo.mkdir()
        (repo / "main.wat").write_text("(module)")
        (repo / "data.bin").write_bytes(b"\x00\x01\x02")
        (repo / "README.md").write_text("# Project")
        model = build_repository_model(repo)
        assert model is not None


class TestBootstrapCandidateGeneration:
    def test_fastapi_repo_generates_candidates(self, fastapi_repo: Path):
        result = bootstrap(fastapi_repo, fastapi_repo / "docs/adr", dry_run=True)
        titles = [s.adr.title for s in result]
        assert "Use FastAPI for HTTP APIs" in titles
        assert "Use SQLAlchemy for relational persistence" in titles

    def test_candidates_deduplicate_titles(self, fastapi_repo: Path):
        adr_dir = fastapi_repo / "docs/adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "ADR-0001.md").write_text(
            "---\nid: ADR-0001\ntitle: Use FastAPI for HTTP APIs\n"
            "status: accepted\nseverity: high\nsource: manual\n"
            "keywords: [fastapi, framework]\n---\n"
        )
        result = bootstrap(fastapi_repo, adr_dir, dry_run=True)
        titles = [s.adr.title for s in result]
        assert "Use FastAPI for HTTP APIs" not in titles

    def test_duplicate_technologies_not_double_counted(self, tmp_path: Path):
        repo = tmp_path / "dup-tech"
        repo.mkdir()
        (repo / "requirements.txt").write_text("flask\nflask\n")
        (repo / "app.py").write_text("import flask\n")
        model = build_repository_model(repo)
        names = {t.name for t in model.technologies}
        assert "Flask" in names
        flask_count = sum(1 for t in model.technologies if t.name == "Flask")
        assert flask_count == 1

    def test_deterministic_ordering(self, fastapi_repo: Path):
        model1 = build_repository_model(fastapi_repo)
        result1 = bootstrap(fastapi_repo, fastapi_repo / "docs/adr", dry_run=True)
        model2 = build_repository_model(fastapi_repo)
        result2 = bootstrap(fastapi_repo, fastapi_repo / "docs/adr", dry_run=True)
        t1 = [t.name for t in model1.technologies]
        t2 = [t.name for t in model2.technologies]
        assert t1 == t2
        s1 = [s.adr.title for s in result1]
        s2 = [s.adr.title for s in result2]
        assert s1 == s2


class TestBootstrapEdgeCases:
    def test_malformed_pyproject_does_not_crash(self, tmp_path: Path):
        repo = tmp_path / "malformed"
        repo.mkdir()
        (repo / "pyproject.toml").write_text("{bad toml")
        model = build_repository_model(repo)
        assert model is not None

    def test_nested_node_modules_excluded(self, tmp_path: Path):
        repo = tmp_path / "with-node-modules"
        repo.mkdir()
        (repo / "node_modules" / "express" / "index.js").mkdir(parents=True)
        (repo / "package.json").write_text('{"dependencies": {"express": "^4.0.0"}}')
        model = build_repository_model(repo)
        evidence_paths = {ev.source_path for ev in model.evidence}
        assert not any("node_modules" in p for p in evidence_paths)

    def test_only_test_deps_do_not_generate_adr(self, tmp_path: Path):
        repo = tmp_path / "test-only"
        repo.mkdir()
        (repo / "requirements.txt").write_text("pytest\npytest-cov\n")
        titles = [s.adr.title for s in bootstrap(repo, repo / "docs/adr", dry_run=True)]
        assert titles == ["Use Python as the primary backend language"]

    def test_dockerfile_only_detects_docker_but_no_enforceable_adr(self, tmp_path: Path):
        repo = tmp_path / "docker-only"
        repo.mkdir()
        (repo / "Dockerfile").write_text("FROM ubuntu:22.04\n")
        model = build_repository_model(repo)
        names = {t.name for t in model.technologies}
        assert "Docker" in names
        result = bootstrap(repo, repo / "docs/adr", dry_run=True)
        assert result == []
