from __future__ import annotations

from pathlib import Path

from decisiondrift.rules.scanner import (
    _scan_requirements_txt,
    _scan_pyproject_toml,
    _scan_package_json,
    scan_imports,
)


class TestDependencyScanners:
    def test_requirements_txt(self, tmp_path: Path):
        f = tmp_path / "requirements.txt"
        f.write_text("flask==2.0\nredis>=4.0\npydantic>=2.0,<3.0\n# comment\n-e .\n")
        pkgs = _scan_requirements_txt(tmp_path)
        assert "flask" in pkgs
        assert "redis" in pkgs
        assert "pydantic" in pkgs
        assert len(pkgs) == 3

    def test_requirements_txt_missing(self, tmp_path: Path):
        pkgs = _scan_requirements_txt(tmp_path)
        assert pkgs == []

    def test_pyproject_toml(self, tmp_path: Path):
        f = tmp_path / "pyproject.toml"
        f.write_text('''[project]
name = "test"
dependencies = [
    "flask>=2.0",
    "redis",
]
''')
        pkgs = _scan_pyproject_toml(tmp_path)
        assert "flask" in pkgs
        assert "redis" in pkgs

    def test_pyproject_toml_missing(self, tmp_path: Path):
        pkgs = _scan_pyproject_toml(tmp_path)
        assert pkgs == []

    def test_package_json(self, tmp_path: Path):
        f = tmp_path / "package.json"
        f.write_text('{"dependencies": {"express": "^4.0", "react": "^18.0"}}')
        pkgs = _scan_package_json(tmp_path)
        assert "express" in pkgs
        assert "react" in pkgs
        assert len(pkgs) == 2

    def test_package_json_missing(self, tmp_path: Path):
        pkgs = _scan_package_json(tmp_path)
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
