#!/usr/bin/env python3
"""Generate benchmark repositories and expected outputs for Bootstrap V3 validation.

Creates minimal repositories that emulate real-world applications across various languages.
Also generates expected outputs (ADR titles, detected technologies) in benchmarks/expected.
"""

import json
from pathlib import Path


def create_fixture(
    base_dir: Path,
    expected_dir: Path,
    name: str,
    files: dict[str, str],
    expected_techs: list[str],
    expected_adrs: list[str],
):
    """Helper to create a repository and its expected output."""
    repo_path = base_dir / name
    repo_path.mkdir(parents=True, exist_ok=True)

    for file_path, content in files.items():
        full_path = repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.strip() + "\n")

    expected_file = expected_dir / f"{name}.json"
    expected_data = {
        "expected_technologies": expected_techs,
        "expected_adrs": expected_adrs,
    }
    expected_file.write_text(json.dumps(expected_data, indent=2) + "\n")
    print(f"Created fixture: {name}")


def main():
    benchmarks_dir = Path(__file__).parent.parent / "benchmarks"
    repos_dir = benchmarks_dir / "repos"
    expected_dir = benchmarks_dir / "expected"

    repos_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    # 1. FastAPI + SQLAlchemy + Docker
    create_fixture(
        repos_dir,
        expected_dir,
        "fastapi-sample",
        {
            "pyproject.toml": """
[project]
name = "fastapi-sample"
dependencies = [
    "fastapi>=0.100.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.11.0",
]
            """,
            "Dockerfile": """
FROM python:3.11-slim
WORKDIR /app
COPY . .
            """,
            "src/main.py": """
from fastapi import FastAPI
app = FastAPI()
            """,
        },
        expected_techs=["FastAPI", "SQLAlchemy", "Alembic", "Docker", "Python"],
        expected_adrs=[
            "Use Python as the primary backend language",
            "Use FastAPI for HTTP APIs",
            "Use SQLAlchemy for relational persistence",
        ],
    )

    # 2. Flask + SQLAlchemy + JWT
    create_fixture(
        repos_dir,
        expected_dir,
        "flask-sample",
        {
            "requirements.txt": """
flask==2.3.2
Flask-SQLAlchemy==3.0.5
PyJWT==2.8.0
            """,
            "app.py": """
from flask import Flask
app = Flask(__name__)
            """,
        },
        expected_techs=["Flask", "SQLAlchemy", "JWT", "Python"],
        expected_adrs=[
            "Use Python as the primary backend language",
            "Use Flask as Web Framework",
            "Use JWT for API Authentication",
        ],
    )

    # 3. Express + Redis
    create_fixture(
        repos_dir,
        expected_dir,
        "express-sample",
        {
            "package.json": """
{
  "name": "express-sample",
  "dependencies": {
    "express": "^4.18.2",
    "redis": "^4.6.7"
  }
}
            """,
            "index.js": """
const express = require('express');
const app = express();
            """,
        },
        expected_techs=["Express", "Redis", "NPM", "JavaScript"],
        expected_adrs=[
            "Use JavaScript as the primary language",
            "Use Express for Node HTTP Services",
        ],
    )

    # 4. Django + Celery + PostgreSQL
    create_fixture(
        repos_dir,
        expected_dir,
        "django-sample",
        {
            "requirements.txt": """
Django==4.2.0
celery==5.3.0
psycopg2-binary==2.9.6
            """,
            "manage.py": """
# Django minimal manage.py
            """,
        },
        expected_techs=["Django", "Celery", "PostgreSQL", "Python"],
        expected_adrs=[
            "Use Python as the primary backend language",
            "Use Django as Web Framework",
            "Use Celery for asynchronous jobs",
        ],
    )

    # 5. Go + Gin + Docker
    create_fixture(
        repos_dir,
        expected_dir,
        "go-sample",
        {
            "go.mod": """
module example.com/go-sample

go 1.20

require (
	github.com/gin-gonic/gin v1.9.1
)
            """,
            "main.go": """
package main
import "github.com/gin-gonic/gin"
func main() {}
            """,
            "Dockerfile": """
FROM golang:1.20
            """,
        },
        expected_techs=["Go", "Gin", "Docker"],
        expected_adrs=[
            "Use Go as the primary backend language",
            "Use Gin as the backend framework",
        ],
    )

    print(f"\nCreated 5 benchmark fixtures in {repos_dir}")


if __name__ == "__main__":
    main()
