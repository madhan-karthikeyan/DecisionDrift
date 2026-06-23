from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from decisiondrift.bootstrap.structure_scan import ProjectStructure

Confidence = Literal["high", "medium", "low"]


@dataclass
class PatternDefinition:
    name: str
    confidence: Confidence
    indicators: list[str]  # dir or file names whose presence suggests this pattern
    description: str = ""  # human-readable summary
    template_context: str = ""  # default context block for generated ADR
    template_rationale: str = ""  # default rationale block for generated ADR
    template_keywords: list[str] = field(default_factory=list)


@dataclass
class PatternMatch:
    pattern: PatternDefinition
    confidence: Confidence
    evidence: list[str]  # matching paths in the repo
    reason: str  # why this pattern was detected


REGISTRY: list[PatternDefinition] = [
    # --- Web framework ---
    PatternDefinition(
        name="Use Flask as Web Framework",
        confidence="high",
        indicators=["requirements.txt", "run.py", "__init__.py"],
        template_context="The project structure includes Flask-specific entry points and configuration files, suggesting Flask as the primary web framework.",
        template_rationale="Flask provides a lightweight, extensible foundation with a large ecosystem of extensions. The application should follow the Flask application factory pattern (create_app()) for testability and configuration flexibility.",
        template_keywords=["flask", "web framework", "application", "http"],
    ),
    # --- SQLAlchemy ---
    PatternDefinition(
        name="Use SQLAlchemy as ORM",
        confidence="high",
        indicators=["models", "extensions.py"],
        template_context="The project has a models/ directory and extensions.py referencing db initialization, indicating SQLAlchemy is used as the ORM.",
        template_rationale="SQLAlchemy provides a mature, feature-rich ORM with strong migration support via Alembic. Models should use db.Model as the base class.",
        template_keywords=["sqlalchemy", "orm", "database", "models"],
    ),
    # --- Celery ---
    PatternDefinition(
        name="Use Celery for Async Tasks",
        confidence="high",
        indicators=["tasks", "celery_worker.py"],
        template_context="The project has a tasks/ directory and a celery worker entry point, indicating Celery is used for asynchronous task processing.",
        template_rationale="Celery with Redis as broker enables non-blocking execution of long-running or non-critical operations via task.delay(). Tasks should be organized by domain.",
        template_keywords=["celery", "async", "task", "worker", "background"],
    ),
    # --- Alembic Migrations ---
    PatternDefinition(
        name="Use Alembic for Database Migrations",
        confidence="high",
        indicators=["alembic.ini", "migrations"],
        template_context="The project has a migrations/ directory and alembic.ini, indicating schema migrations are managed with Alembic.",
        template_rationale="Alembic provides version-controlled, reversible database migrations. Each schema change should be a new migration rather than manual ALTER TABLE statements.",
        template_keywords=["alembic", "migrations", "database", "schema"],
    ),
    # --- Flask Blueprints ---
    PatternDefinition(
        name="Use Flask Blueprints for Modular Routes",
        confidence="high",
        indicators=["api", "routes.py", "__init__.py"],
        template_context="The project organizes API routes into domain-specific blueprint modules under api/ with their own routes.py files.",
        template_rationale="Flask Blueprints enable domain-separated route registration, keeping the application modular and maintainable as the API grows.",
        template_keywords=["flask", "blueprints", "routes", "modular"],
    ),
    # --- Utility Module Pattern ---
    PatternDefinition(
        name="Use Shared Utility Modules",
        confidence="medium",
        indicators=["utils"],
        template_context="The project has a utils/ directory containing shared helper modules for cross-cutting concerns such as caching, decorators, and notifications.",
        template_rationale="Centralizing cross-cutting concerns in a utils/ package avoids duplication and provides a single location for shared logic. Utilities should remain stateless and well-tested.",
        template_keywords=["utils", "helpers", "shared", "utilities"],
    ),
    # --- Separate Frontend ---
    PatternDefinition(
        name="Separate Frontend Application",
        confidence="high",
        indicators=["package.json", "vite.config.js", "vite.config.ts", "frontend"],
        template_context="The project has a separate frontend/ directory with its own package.json and build configuration (Vite, webpack, etc.).",
        template_rationale="A separate frontend application enables independent deployment, type-checking (with TypeScript), and modern frontend tooling. The backend serves as a JSON API only.",
        template_keywords=["frontend", "spa", "vite", "vue", "react"],
    ),
    # --- RBAC ---
    PatternDefinition(
        name="Use Role-Based Access Control",
        confidence="medium",
        indicators=["decorators.py", "auth"],
        template_context="The project has auth-related modules and decorator utilities, suggesting role-based or permission-based access control.",
        template_rationale="Role-based access control ensures that different user roles (admin, doctor, patient) have appropriate permissions. Access checks should be centralized in decorators.",
        template_keywords=["rbac", "auth", "authorization", "roles", "permissions"],
    ),
    # --- Docker ---
    PatternDefinition(
        name="Use Docker for Containerization",
        confidence="high",
        indicators=["Dockerfile", "docker-compose.yml"],
        template_context="The project includes Docker configuration for containerized deployment.",
        template_rationale="Docker provides consistent environments across development, testing, and production. All services should be defined in docker-compose for local development.",
        template_keywords=["docker", "container", "deployment"],
    ),
    # --- JWT ---
    PatternDefinition(
        name="Use JWT for Authentication",
        confidence="medium",
        indicators=["auth", "jwt"],
        template_context="The project has auth-related modules, indicating token-based authentication is in use.",
        template_rationale="JWT provides stateless, scoped authentication tokens suitable for API-based architectures. Tokens should be short-lived and include role claims.",
        template_keywords=["jwt", "authentication", "auth", "tokens"],
    ),
    # --- Redis Caching ---
    PatternDefinition(
        name="Use Redis for Caching",
        confidence="medium",
        indicators=["cache.py", "redis"],
        template_context="The project has caching utilities and likely integrates with Redis for distributed caching.",
        template_rationale="Redis provides fast in-memory caching to reduce database load and improve API response times. Cache keys should follow a consistent naming convention.",
        template_keywords=["redis", "cache", "caching", "performance"],
    ),
]


def match_patterns(structure: ProjectStructure) -> list[PatternMatch]:
    matches: list[PatternMatch] = []

    for pattern in REGISTRY:
        evidence: list[str] = []
        for indicator in pattern.indicators:
            if structure.has_file(indicator):
                evidence.append(indicator)
            elif structure.has_subdir(indicator):
                matching = [d for d in structure.dirs if indicator in d]
                evidence.extend(matching[:3])  # cap at 3 evidence paths

        if not evidence:
            continue

        reason = f"Found indicators: {', '.join(evidence[:4])}"
        matches.append(PatternMatch(
            pattern=pattern,
            confidence=pattern.confidence,
            evidence=evidence,
            reason=reason,
        ))

    return matches
