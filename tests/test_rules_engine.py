from __future__ import annotations

from pathlib import Path

from decisiondrift.models.schema import DecisionRecord
from decisiondrift.rules.engine import (
    _extract_deps_from_file,
    _scan_api_calls,
    _scan_imports_in_diff,
    enforce_from_adrs,
)
from decisiondrift.rules.models import Action


class TestDependencyExtraction:
    def test_requirements_txt(self, tmp_path: Path):
        f = tmp_path / "requirements.txt"
        f.write_text("flask==2.0\nredis>=4.0\n# comment\n-e .\n")
        deps = _extract_deps_from_file(f)
        assert "flask" in deps
        assert "redis" in deps
        assert len(deps) == 2

    def test_pyproject_toml(self, tmp_path: Path):
        f = tmp_path / "pyproject.toml"
        f.write_text("""[project]
name = "test"
dependencies = [
    "flask>=2.0",
    "redis",
]
""")
        deps = _extract_deps_from_file(f)
        assert "flask" in deps
        assert "redis" in deps


class TestImportScanning:
    def test_scan_imports_in_python_file(self, tmp_path: Path):
        py_file = tmp_path / "app.py"
        py_file.write_text("import flask\nfrom redis import StrictRedis\nimport os\n")
        from decisiondrift.impact.models import ChangedFile

        files = [ChangedFile(path="app.py", language="python", change_type="modified")]
        imports = _scan_imports_in_diff(files, tmp_path)
        import_names = [imp for imp, _ in imports]
        assert "flask" in import_names
        assert "redis" in import_names
        assert "os" in import_names


class TestAPIScanning:
    def test_scan_api_calls(self, tmp_path: Path):
        py_file = tmp_path / "service.py"
        py_file.write_text("""
result = db.session.execute(query)
cache.get(key)
app.run(debug=True)
""")
        calls = _scan_api_calls(py_file)
        assert "db.session.execute" in calls
        assert "cache.get" in calls
        assert "app.run" in calls

    def test_empty_file(self, tmp_path: Path):
        py_file = tmp_path / "empty.py"
        py_file.write_text("")
        calls = _scan_api_calls(py_file)
        assert calls == []

    def test_missing_file(self, tmp_path: Path):
        calls = _scan_api_calls(tmp_path / "nonexistent.py")
        assert calls == []


class TestDiffEnforcement:
    def test_block_on_dependency_violation(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("flask==2.0\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- a/requirements.txt\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+flask==2.0\n"
        adrs = [
            DecisionRecord(
                id="ADR-0001",
                title="Use FastAPI",
                status="accepted",
                severity="high",
                prohibitions=["flask"],
            )
        ]
        result = enforce_from_adrs(adrs, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0
        assert result.findings[0].action == Action.BLOCK
        assert result.findings[0].match_value == "flask"

    def test_no_violations(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi==0.100\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- a/requirements.txt\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+fastapi==0.100\n"
        adrs = [
            DecisionRecord(
                id="ADR-0001",
                title="Use FastAPI",
                status="accepted",
                severity="high",
                prohibitions=["flask"],
            )
        ]
        result = enforce_from_adrs(adrs, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) == 0

    def test_empty_diff(self, tmp_path: Path):
        adrs = [
            DecisionRecord(
                id="ADR-0001",
                title="Use FastAPI",
                status="accepted",
                severity="high",
                prohibitions=["flask"],
            )
        ]
        result = enforce_from_adrs(adrs, repo_path=str(tmp_path), diff_text="")
        assert len(result.findings) == 0


class TestRepoEnforcement:
    def test_full_repo_scan_detects_prohibited_import(self, tmp_path: Path):
        py_file = tmp_path / "app.py"
        py_file.write_text("import flask\n")
        req = tmp_path / "requirements.txt"
        req.write_text("flask==2.0\n")
        adrs = [
            DecisionRecord(
                id="ADR-0001",
                title="Use FastAPI",
                status="accepted",
                severity="high",
                prohibitions=["flask"],
            )
        ]
        result = enforce_from_adrs(adrs, repo_path=str(tmp_path))
        assert len(result.findings) > 0
        match_types = {f.rule_type.value for f in result.findings}
        assert "dependency" in match_types
        assert "import" in match_types
