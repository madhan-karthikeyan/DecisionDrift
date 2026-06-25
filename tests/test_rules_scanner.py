from __future__ import annotations

from pathlib import Path

from decisiondrift.rules.scanner import scan_dependencies, scan_imports
from decisiondrift.utils.dependency_parser import (
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)


class TestDependencyParsers:
    def test_requirements_txt(self, tmp_path: Path):
        f = tmp_path / "requirements.txt"
        f.write_text("flask==2.0\nredis>=4.0\npydantic>=2.0,<3.0\n# comment\n-e .\n")
        pkgs = parse_requirements_txt(f)
        assert "flask" in pkgs
        assert "redis" in pkgs
        assert "pydantic" in pkgs
        assert len(pkgs) == 3

    def test_requirements_txt_missing(self, tmp_path: Path):
        pkgs = parse_requirements_txt(tmp_path / "requirements.txt")
        assert pkgs == []

    def test_pyproject_toml(self, tmp_path: Path):
        f = tmp_path / "pyproject.toml"
        f.write_text("""[project]
name = "test"
dependencies = [
    "flask>=2.0",
    "redis",
]
""")
        deps = parse_pyproject_toml(f)
        names = [d for d, _r in deps]
        assert "flask" in names
        assert "redis" in names

    def test_pyproject_toml_missing(self, tmp_path: Path):
        deps = parse_pyproject_toml(tmp_path / "pyproject.toml")
        assert deps == []

    def test_package_json(self, tmp_path: Path):
        f = tmp_path / "package.json"
        f.write_text('{"dependencies": {"express": "^4.0", "react": "^18.0"}}')
        deps = parse_package_json(f)
        names = [d for d, _r in deps]
        assert "express" in names
        assert "react" in names
        assert len(names) == 2

    def test_package_json_missing(self, tmp_path: Path):
        deps = parse_package_json(tmp_path / "package.json")
        assert deps == []

    def test_scan_dependencies_aggregates(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("flask\nredis\n")
        (tmp_path / "pyproject.toml").write_text("""[project]
name = "test"
dependencies = ["celery"]
""")
        pkgs = scan_dependencies(tmp_path)
        assert "flask" in pkgs
        assert "redis" in pkgs
        assert "celery" in pkgs

    def test_scan_dependencies_empty(self, tmp_path: Path):
        pkgs = scan_dependencies(tmp_path)
        assert pkgs == []


class TestImportScanner:
    def test_scan_imports(self, tmp_path: Path):
        (tmp_path / "app.py").write_text("import flask\nfrom redis import StrictRedis\nimport os\n")
        imports = scan_imports(tmp_path)
        assert "flask" in imports
        assert "redis" in imports
        assert "os" in imports

    def test_scan_imports_skips_excluded_dirs(self, tmp_path: Path):
        venv = tmp_path / ".venv"
        venv.mkdir(parents=True)
        (venv / "lib.py").write_text("import malicious\n")
        (tmp_path / "app.py").write_text("import flask\n")
        imports = scan_imports(tmp_path)
        assert "flask" in imports
        assert "malicious" not in imports

    def test_scan_imports_empty(self, tmp_path: Path):
        imports = scan_imports(tmp_path)
        assert imports == []
