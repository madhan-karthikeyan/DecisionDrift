from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from decisiondrift.models.schema import ConfidenceLevel, DecisionRecord
from decisiondrift.rules.models import Action, Rule, RuleSet, RuleType

# =============================================================================
# Mock LLM utilities
# =============================================================================


class MockLLMClient:
    """Mock LLM client that returns canned JSON responses."""

    def __init__(self, responses: list[dict[str, Any]] | None = None):
        self.responses = responses or []
        self.call_count = 0
        self._available = True

    def available(self) -> bool:
        return self._available

    def set_available(self, val: bool):
        self._available = val

    def complete_json(self, prompt: str, **kwargs) -> dict[str, Any]:
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return {"decisions": []}

    def complete(self, prompt: str, **kwargs) -> str:
        return json.dumps(self.complete_json(prompt, **kwargs))


@pytest.fixture
def mock_llm_client():
    return MockLLMClient()


@pytest.fixture
def mock_llm_patch(mock_llm_client):
    with patch("decisiondrift.llm.client.LLMClient") as mock:
        mock.return_value = mock_llm_client
        yield mock


# =============================================================================
# Sample repository fixtures
# =============================================================================


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "empty_repo"
    repo.mkdir()
    (repo / ".gitkeep").write_text("")
    return repo


@pytest.fixture
def flask_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "flask_app"
    repo.mkdir()
    (repo / "app").mkdir()
    (repo / "app" / "__init__.py").write_text("from flask import Flask\napp = Flask(__name__)\n")
    (repo / "app" / "views.py").write_text(
        "from flask import jsonify\n@app.route('/health')\ndef health():\n    return jsonify(ok=True)\n"
    )
    (repo / "requirements.txt").write_text("flask==3.0\nredis==5.0\npytest==8.0\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_health(client):\n    pass\n")
    (repo / "Dockerfile").write_text("FROM python:3.12\n")
    return repo


@pytest.fixture
def fastapi_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "fastapi_app"
    repo.mkdir()
    (repo / "app").mkdir()
    (repo / "app" / "main.py").write_text(
        "from fastapi import FastAPI\nfrom app.routers import users\n\napp = FastAPI()\napp.include_router(users.router)\n"
    )
    (repo / "app" / "routers").mkdir()
    (repo / "app" / "routers" / "__init__.py").write_text("")
    (repo / "app" / "routers" / "users.py").write_text("from fastapi import APIRouter\nrouter = APIRouter()\n")
    (repo / "app" / "services").mkdir()
    (repo / "app" / "db").mkdir()
    (repo / "app" / "db" / "__init__.py").write_text("from sqlalchemy import create_engine\n")
    (repo / "requirements.txt").write_text(
        "fastapi==0.110\nuvicorn==0.29\nsqlalchemy==2.0\npsycopg2==2.9\nredis==5.0\ncelery==5.3\npytest==8.0\n"
    )
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "fastapi-app"\ndependencies = ["fastapi", "uvicorn", "sqlalchemy"]\n'
    )
    (repo / "Dockerfile").write_text("FROM python:3.12\n")
    (repo / "alembic.ini").write_text("[alembic]\nscript_location = alembic\n")
    (repo / "alembic").mkdir()
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
    return repo


@pytest.fixture
def node_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "node_app"
    repo.mkdir()
    (repo / "package.json").write_text(
        '{"name": "node-app", "dependencies": {"express": "^4.18.0", "redis": "^4.0.0"}, "devDependencies": {"jest": "^29.0.0"}}\n'
    )
    (repo / "src").mkdir()
    (repo / "src" / "index.js").write_text("const express = require('express');\nconst app = express();\n")
    (repo / "Dockerfile").write_text("FROM node:20\n")
    return repo


@pytest.fixture
def java_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "java_app"
    repo.mkdir()
    (repo / "pom.xml").write_text(
        "<project><artifactId>java-app</artifactId><dependencies><dependency><artifactId>spring-boot</artifactId></dependency></dependencies></project>\n"
    )
    (repo / "src" / "main" / "java").mkdir(parents=True)
    (repo / "src" / "main" / "java" / "App.java").write_text(
        "public class App {\n    public static void main(String[] args) {}\n}\n"
    )
    return repo


@pytest.fixture
def go_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "go_app"
    repo.mkdir()
    (repo / "go.mod").write_text("module github.com/example/go-app\ngo 1.22\nrequire github.com/gin-gonic/gin v1.9.0\n")
    (repo / "main.go").write_text('package main\nimport "github.com/gin-gonic/gin"\nfunc main() {}\n')
    return repo


@pytest.fixture
def rust_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "rust_app"
    repo.mkdir()
    (repo / "Cargo.toml").write_text('[package]\nname = "rust-app"\nversion = "0.1.0"\n[dependencies]\ntokio = "1.0"\n')
    (repo / "src").mkdir()
    (repo / "src" / "main.rs").write_text('fn main() { println!("hello"); }\n')
    return repo


# =============================================================================
# ADR fixtures
# =============================================================================


@pytest.fixture
def approved_adr() -> DecisionRecord:
    return DecisionRecord(
        id="ADR-0001",
        title="Use FastAPI for HTTP APIs",
        status="accepted",
        severity="high",
        type="technology_choice",
        source="bootstrap",
        rationale="FastAPI is the chosen HTTP framework.",
        prohibitions=["flask", "django"],
        keywords=["fastapi", "framework"],
        confidence=ConfidenceLevel.HIGH,
    )


@pytest.fixture
def rejected_adr() -> DecisionRecord:
    return DecisionRecord(
        id="ADR-0002",
        title="Use Redis for Caching",
        status="rejected",
        severity="medium",
        type="runtime_policy",
        source="manual",
        rationale="Redis was discussed but rejected.",
        prohibitions=[],
        keywords=["redis", "cache"],
        rejected_reason="Team decided to use Memcached instead.",
    )


@pytest.fixture
def proposed_adr() -> DecisionRecord:
    return DecisionRecord(
        id="ADR-0003",
        title="Use PostgreSQL for Persistent Storage",
        status="proposed",
        severity="medium",
        type="data_access",
        source="bootstrap",
        rationale="PostgreSQL is proposed for all persistent storage.",
        prohibitions=["mysql", "mongodb"],
        keywords=["postgresql", "database"],
        confidence=ConfidenceLevel.MEDIUM,
    )


@pytest.fixture
def sample_rules() -> RuleSet:
    return RuleSet(
        rules=[
            Rule(
                id="R001",
                type=RuleType.DEPENDENCY,
                match="flask",
                action=Action.BLOCK,
                source_adr="ADR-0001",
                confidence=ConfidenceLevel.HIGH,
                description="Block Flask dependency",
            ),
            Rule(
                id="R002",
                type=RuleType.IMPORT,
                match="flask",
                action=Action.BLOCK,
                source_adr="ADR-0001",
                confidence=ConfidenceLevel.HIGH,
                description="Block Flask import",
            ),
            Rule(
                id="R003",
                type=RuleType.DEPENDENCY,
                match="django",
                action=Action.REQUIRE_APPROVAL,
                source_adr="ADR-0001",
                confidence=ConfidenceLevel.MEDIUM,
                description="Require approval for Django",
            ),
            Rule(
                id="R004",
                type=RuleType.PATH,
                match=r"^src/legacy/",
                action=Action.WARN,
                source_adr="ADR-0002",
                confidence=ConfidenceLevel.HIGH,
                description="Warn about legacy paths",
            ),
            Rule(
                id="R005",
                type=RuleType.CONFIG,
                match="debug=true",
                action=Action.BLOCK,
                source_adr="ADR-0003",
                confidence=ConfidenceLevel.HIGH,
                description="Block debug mode in production configs",
            ),
        ]
    )


@pytest.fixture
def sample_notes() -> str:
    return """## Architecture Meeting - 2024-03-15

We discussed the technology stack for the new payment service.

Decision:
Use Redis for caching and session storage.

Decision:
Use Celery for async task processing.

## Discussion

The team agreed that Redis is preferred for its simplicity.
Celery was chosen over RQ due to better monitoring support.
"""


# =============================================================================
# Sample ADR directory fixtures
# =============================================================================


@pytest.fixture
def adr_dir_with_records(
    tmp_path: Path, approved_adr: DecisionRecord, rejected_adr: DecisionRecord, proposed_adr: DecisionRecord
) -> Path:
    from decisiondrift.adr.writer import write_adr

    adr_dir = tmp_path / "docs" / "adr"
    adr_dir.mkdir(parents=True)

    for adr in [approved_adr, rejected_adr, proposed_adr]:
        path = adr_dir / f"{adr.id}.md"
        metadata = adr.model_dump(exclude={"embedding", "rationale"}, exclude_none=True)
        from enum import Enum

        sanitized = {}
        for k, v in metadata.items():
            if isinstance(v, Enum):
                sanitized[k] = v.value
            else:
                sanitized[k] = v
        write_adr(path, sanitized, adr.rationale)

    return adr_dir


# =============================================================================
# Mock diff text fixtures
# =============================================================================


@pytest.fixture
def sample_diff() -> str:
    return """diff --git a/requirements.txt b/requirements.txt
new file mode 100644
--- /dev/null
+++ b/requirements.txt
@@ -0,0 +1 @@
+flask==3.0
"""


@pytest.fixture
def sample_python_diff() -> str:
    return """diff --git a/app.py b/app.py
new file mode 100644
--- /dev/null
+++ b/app.py
@@ -0,0 +1,5 @@
+import flask
+from redis import StrictRedis
+
+def handler():
+    pass
"""


@pytest.fixture
def empty_diff() -> str:
    return ""
