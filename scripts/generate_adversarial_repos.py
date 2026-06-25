#!/usr/bin/env python3
"""Generate adversarial test repositories for Bootstrap V3 validation.

Creates minimal repositories that test specific edge cases where Bootstrap
should NOT generate ADRs. Success is correct suppression, not ADR generation.
"""

from pathlib import Path


def create_library_with_fastapi_examples(base_dir: Path) -> Path:
    """Library repo with FastAPI only in examples/."""
    repo_path = base_dir / "library-with-fastapi-examples"
    repo_path.mkdir(exist_ok=True)

    # Main library files
    (repo_path / "pyproject.toml").write_text("""
[project]
name = "my-library"
version = "0.1.0"
""")

    (repo_path / "src" / "mylib").mkdir(parents=True, exist_ok=True)
    (repo_path / "src" / "mylib" / "__init__.py").write_text("""
def my_function():
    return "hello"
""")

    # Examples directory with FastAPI
    examples_dir = repo_path / "examples"
    examples_dir.mkdir(exist_ok=True)

    (examples_dir / "requirements.txt").write_text("""
fastapi==0.104.1
uvicorn==0.24.0
""")

    (examples_dir / "fastapi_app.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "hello"}
""")

    return repo_path


def create_flask_tests_only(base_dir: Path) -> Path:
    """Repo with Flask only in test dependencies."""
    repo_path = base_dir / "flask-tests-only"
    repo_path.mkdir(exist_ok=True)

    (repo_path / "pyproject.toml").write_text("""
[project]
name = "my-app"
version = "0.1.0"

[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "flask>=3.0",
]
""")

    (repo_path / "src" / "myapp").mkdir(parents=True, exist_ok=True)
    (repo_path / "src" / "myapp" / "__init__.py").write_text("""
def my_function():
    return "hello"
""")

    # Tests directory
    tests_dir = repo_path / "tests"
    tests_dir.mkdir(exist_ok=True)

    (tests_dir / "test_example.py").write_text("""
from myapp import my_function

def test_my_function():
    assert my_function() == "hello"
""")

    return repo_path


def create_dockerfile_no_service(base_dir: Path) -> Path:
    """Repo with Dockerfile but no actual service."""
    repo_path = base_dir / "dockerfile-no-service"
    repo_path.mkdir(exist_ok=True)

    (repo_path / "Dockerfile").write_text("""
FROM python:3.11-slim
WORKDIR /app
COPY . .
CMD ["python", "setup.py"]
""")

    (repo_path / "setup.py").write_text("""
from setuptools import setup

setup(
    name="data-processor",
    version="0.1.0",
    py_modules=["processor"],
)
""")

    (repo_path / "processor.py").write_text("""
def process_data(data):
    return data.upper()
""")

    return repo_path


def create_redis_optional_only(base_dir: Path) -> Path:
    """Repo with Redis as optional dependency only."""
    repo_path = base_dir / "redis-optional-only"
    repo_path.mkdir(exist_ok=True)

    (repo_path / "pyproject.toml").write_text("""
[project]
name = "my-app"
version = "0.1.0"

[project.optional-dependencies]
redis = [
    "redis>=5.0",
]
""")

    (repo_path / "src" / "myapp").mkdir(parents=True, exist_ok=True)
    (repo_path / "src" / "myapp" / "__init__.py").write_text("""
def my_function():
    return "hello"
""")

    return repo_path


def create_monorepo_unrelated_apps(base_dir: Path) -> Path:
    """Monorepo with multiple unrelated applications."""
    repo_path = base_dir / "monorepo-unrelated-apps"
    repo_path.mkdir(exist_ok=True)

    # App 1: Python CLI
    app1_dir = repo_path / "apps" / "cli-tool"
    app1_dir.mkdir(parents=True, exist_ok=True)

    (app1_dir / "pyproject.toml").write_text("""
[project]
name = "cli-tool"
version = "0.1.0"
""")

    (app1_dir / "cli.py").write_text("""
def main():
    print("CLI tool")
""")

    # App 2: JavaScript frontend
    app2_dir = repo_path / "apps" / "web-frontend"
    app2_dir.mkdir(parents=True, exist_ok=True)

    (app2_dir / "package.json").write_text("""
{
  "name": "web-frontend",
  "version": "0.1.0",
  "dependencies": {
    "react": "^18.0"
  }
}
""")

    (app2_dir / "index.js").write_text("""
console.log("Web frontend");
""")

    # App 3: Go service
    app3_dir = repo_path / "apps" / "go-service"
    app3_dir.mkdir(parents=True, exist_ok=True)

    (app3_dir / "go.mod").write_text("""
module go-service

go 1.21
""")

    (app3_dir / "main.go").write_text("""
package main

func main() {
    println("Go service")
}
""")

    return repo_path


def create_framework_impl_deps(base_dir: Path) -> Path:
    """Framework repo with many implementation dependencies."""
    repo_path = base_dir / "framework-impl-deps"
    repo_path.mkdir(exist_ok=True)

    (repo_path / "pyproject.toml").write_text("""
[project]
name = "my-framework"
version="0.1.0"

dependencies = [
    "sqlalchemy>=2.0",
    "redis>=5.0",
    "celery>=5.0",
    "pyjwt>=2.0",
]
""")

    (repo_path / "src" / "myframework").mkdir(parents=True, exist_ok=True)
    (repo_path / "src" / "myframework" / "__init__.py").write_text("""
class Framework:
    def __init__(self):
        pass
""")

    return repo_path


def create_sdk_optional_db(base_dir: Path) -> Path:
    """SDK with optional database integrations."""
    repo_path = base_dir / "sdk-optional-db"
    repo_path.mkdir(exist_ok=True)

    (repo_path / "pyproject.toml").write_text("""
[project]
name = "my-sdk"
version="0.1.0"

[project.optional-dependencies]
postgresql = [
    "psycopg2>=2.9",
    "sqlalchemy>=2.0",
]
mysql = [
    "pymysql>=1.0",
    "sqlalchemy>=2.0",
]
""")

    (repo_path / "src" / "mysdk").mkdir(parents=True, exist_ok=True)
    (repo_path / "src" / "mysdk" / "__init__.py").write_text("""
class SDK:
    def __init__(self):
        pass
""")

    return repo_path


def create_frontend_docs_only(base_dir: Path) -> Path:
    """Frontend package used only for documentation."""
    repo_path = base_dir / "frontend-docs-only"
    repo_path.mkdir(exist_ok=True)

    (repo_path / "package.json").write_text("""
{
  "name": "docs-frontend",
  "version": "0.1.0",
  "dependencies": {
    "react": "^18.0"
  },
  "scripts": {
    "build": "echo 'Building docs'"
  }
}
""")

    docs_dir = repo_path / "docs"
    docs_dir.mkdir(exist_ok=True)

    (docs_dir / "index.html").write_text("""
<!DOCTYPE html>
<html>
<head><title>Documentation</title></head>
<body>
  <div id="root"></div>
</body>
</html>
""")

    return repo_path


def main():
    """Generate all adversarial test repositories."""
    base_dir = Path(__file__).parent.parent / "repos" / "adversarial"
    base_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating adversarial test repositories in {base_dir}")

    repos = [
        create_library_with_fastapi_examples(base_dir),
        create_flask_tests_only(base_dir),
        create_dockerfile_no_service(base_dir),
        create_redis_optional_only(base_dir),
        create_monorepo_unrelated_apps(base_dir),
        create_framework_impl_deps(base_dir),
        create_sdk_optional_db(base_dir),
        create_frontend_docs_only(base_dir),
    ]

    print(f"Created {len(repos)} adversarial test repositories:")
    for repo_path in repos:
        print(f"  - {repo_path.name}")

    print("\nTo run adversarial benchmark:")
    print("  python scripts/run_bootstrap_benchmark.py --spec benchmarks/adversarial.yaml")


if __name__ == "__main__":
    main()
