from __future__ import annotations

from pathlib import Path

from decisiondrift.rules.scanner import scan_dependencies, scan_imports
from decisiondrift.utils.dependency_parser import (
    parse_build_gradle_kts,
    parse_composer_json,
    parse_csproj,
    parse_gemfile,
    parse_gemfile_lock,
    parse_package_json,
    parse_package_swift,
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

    def test_scan_nested_dependencies(self, tmp_path: Path):
        """Regression: Bug #2 — recursive scanning should find nested dep files."""
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "requirements.txt").write_text("flask\ncelery\n")
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text('{"dependencies": {"react": "^18.0", "vue": "^3.0"}}')
        pkgs = scan_dependencies(tmp_path)
        assert "flask" in pkgs
        assert "celery" in pkgs
        assert "react" in pkgs
        assert "vue" in pkgs

    def test_scan_nested_dependencies_excludes_node_modules(self, tmp_path: Path):
        """Regression: Bug #2 — should skip node_modules even when nested."""
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "requirements.txt").write_text("flask\n")
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.json").write_text('{"dependencies": {"malicious": "^1.0"}}')
        pkgs = scan_dependencies(tmp_path)
        assert "flask" in pkgs
        assert "malicious" not in pkgs

    def test_scan_nested_dependencies_dedup(self, tmp_path: Path):
        """Regression: Bug #2 — same dep in multiple files should appear once."""
        (tmp_path / "requirements.txt").write_text("flask\n")
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "requirements.txt").write_text("flask\ncelery\n")
        pkgs = scan_dependencies(tmp_path)
        assert "flask" in pkgs
        assert "celery" in pkgs
        assert pkgs.count("flask") == 1


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


class TestRubyDependencyParser:
    def test_gemfile(self, tmp_path: Path):
        f = tmp_path / "Gemfile"
        f.write_text('source "https://rubygems.org"\ngem "rails"\ngem "rspec", group: :test\n')
        deps = parse_gemfile(f)
        names = [d for d, _r in deps]
        assert "rails" in names
        assert "rspec" in names

    def test_gemfile_lock(self, tmp_path: Path):
        f = tmp_path / "Gemfile.lock"
        f.write_text("GEM\n  specs:\n    rails (7.0.0)\n    rspec (3.12.0)\n")
        deps = parse_gemfile_lock(f)
        names = [d for d, _r in deps]
        assert "rails" in names
        assert "rspec" in names

    def test_gemfile_missing(self, tmp_path: Path):
        assert parse_gemfile(tmp_path / "Gemfile") == []


class TestPHPDependencyParser:
    def test_composer_json(self, tmp_path: Path):
        f = tmp_path / "composer.json"
        f.write_text('{"require": {"laravel/framework": "^10.0"}, "require-dev": {"phpunit/phpunit": "^10.0"}}')
        deps = parse_composer_json(f)
        names = [d for d, _r in deps]
        assert "laravel/framework" in names
        assert "phpunit/phpunit" in names
        assert len(names) == 2

    def test_composer_json_missing(self, tmp_path: Path):
        assert parse_composer_json(tmp_path / "composer.json") == []


class TestCSharpDependencyParser:
    def test_csproj(self, tmp_path: Path):
        f = tmp_path / "test.csproj"
        f.write_text('<Project><ItemGroup><PackageReference Include="Newtonsoft.Json" Version="13.0.1" /></ItemGroup></Project>')
        deps = parse_csproj(f)
        names = [d for d, _r in deps]
        assert "Newtonsoft.Json" in names

    def test_csproj_missing(self, tmp_path: Path):
        assert parse_csproj(tmp_path / "test.csproj") == []


class TestKotlinDependencyParser:
    def test_build_gradle_kts(self, tmp_path: Path):
        f = tmp_path / "build.gradle.kts"
        f.write_text('dependencies { implementation("org.jetbrains.kotlin:kotlin-stdlib") testImplementation("io.kotest:kotest-runner-junit5:5.5.0") }')
        deps = parse_build_gradle_kts(f)
        names = [d for d, _r in deps]
        assert "org.jetbrains.kotlin:kotlin-stdlib" in names
        assert "io.kotest:kotest-runner-junit5:5.5.0" in names

    def test_build_gradle_kts_missing(self, tmp_path: Path):
        assert parse_build_gradle_kts(tmp_path / "build.gradle.kts") == []


class TestSwiftDependencyParser:
    def test_package_swift(self, tmp_path: Path):
        f = tmp_path / "Package.swift"
        f.write_text('let package = Package(name: "App", dependencies: [.package(url: "https://github.com/vapor/vapor.git", from: "4.0.0")])')
        deps = parse_package_swift(f)
        names = [d for d, _r in deps]
        assert "vapor" in names

    def test_package_swift_missing(self, tmp_path: Path):
        assert parse_package_swift(tmp_path / "Package.swift") == []


class TestAggregatedScanner:
    def test_scan_ruby_and_php_deps(self, tmp_path: Path):
        (tmp_path / "Gemfile").write_text('gem "rails"\n')
        (tmp_path / "composer.json").write_text('{"require": {"laravel/framework": "^10.0"}}')
        pkgs = scan_dependencies(tmp_path)
        assert "rails" in pkgs
        assert "laravel/framework" in pkgs

    def test_scan_csharp_kotlin_swift_deps(self, tmp_path: Path):
        (tmp_path / "app.csproj").write_text('<Project><PackageReference Include="Newtonsoft.Json" /></Project>')
        (tmp_path / "build.gradle.kts").write_text('dependencies { implementation("ktor") }')
        (tmp_path / "Package.swift").write_text('let p = Package(name: "A", dependencies: [.package(url: "https://github.com/vapor/vapor.git")])')
        pkgs = scan_dependencies(tmp_path)
        assert "Newtonsoft.Json" in pkgs
        assert "ktor" in pkgs
        assert "vapor" in pkgs
