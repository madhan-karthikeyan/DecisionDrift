from __future__ import annotations

from enum import Enum
from pathlib import Path

from decisiondrift.adr.writer import write_adr
from decisiondrift.bootstrap.architecture import ArchitectureModel
from decisiondrift.bootstrap.detectors import DetectedTechnology
from decisiondrift.models.schema import ConfidenceLevel, DecisionRecord


class ADRSuggestion:
    def __init__(self, tech: DetectedTechnology, adr: DecisionRecord, rules: list[dict]):
        self.tech = tech
        self.adr = adr
        self.rules = rules

    def dry_run_text(self) -> str:
        lines = [
            f"[{self.adr.confidence.value.upper() if self.adr.confidence else 'MEDIUM'}] {self.adr.title}",
            "",
            f"  Rationale: {self.adr.rationale[:120]}{'...' if len(self.adr.rationale) > 120 else ''}",
            "",
            "  Evidence:",
        ]
        for e in self.tech.evidence:
            lines.append(f"    - {e}")
        if self.rules:
            lines.append("")
            lines.append("  Suggested Rules:")
            for r in self.rules:
                lines.append(f"    - type: {r['type']}, match: {r['match']}, action: {r['action']}")
        lines.append("")
        return "\n".join(lines)


ADR_TEMPLATES: dict[str, tuple[str, str, str, float]] = {
    # technology_name -> (title_suffix, rationale_template, prohibitions_format, base_confidence)
    "FastAPI": (
        "for Async HTTP Services",
        "FastAPI provides async-native HTTP handling with automatic OpenAPI documentation. "
        "All HTTP endpoints should use FastAPI's dependency injection and Pydantic validation. "
        "Avoid mixing in synchronous frameworks for new endpoints.",
        "flask, django",
        0.90,
    ),
    "Flask": (
        "as Web Framework",
        "Flask provides a lightweight, extensible foundation for HTTP services. "
        "The application should follow the Flask application factory pattern for testability.",
        "fastapi, django",
        0.90,
    ),
    "Django": (
        "as Web Framework",
        "Django provides a full-featured MVC framework with built-in ORM, admin, and authentication. "
        "Follow Django's project structure and use its ORM for all database access.",
        "flask, fastapi",
        0.90,
    ),
    "PostgreSQL": (
        "for Database",
        "PostgreSQL provides reliable, ACID-compliant persistence with strong JSON support and "
        "advanced indexing. All persistent data should be stored in PostgreSQL.",
        "mysql, sqlite, mongodb",
        0.85,
    ),
    "Redis": (
        "for Caching and Session Storage",
        "Redis provides fast in-memory data structures suitable for caching, session storage, "
        "and rate limiting. Do not use Redis as a primary database or message queue.",
        "",
        0.80,
    ),
    "Celery": (
        "for Async Task Processing",
        "Celery with Redis or RabbitMQ broker enables non-blocking execution of long-running "
        "tasks. Use Celery for background jobs, email sending, and external API calls.",
        "rq, huey",
        0.90,
    ),
    "SQLAlchemy": (
        "as ORM",
        "SQLAlchemy provides a mature ORM with strong migration support. All database access "
        "should go through SQLAlchemy models and sessions. Avoid raw SQL queries.",
        "peewee, pony",
        0.85,
    ),
    "JWT": (
        "for Authentication",
        "JWT provides stateless, scoped authentication tokens suitable for API-based "
        "architectures. Tokens should include role claims and have short expiration.",
        "session-based-auth",
        0.80,
    ),
    "Docker": (
        "for Containerization",
        "Docker provides consistent environments across development, testing, and production. "
        "All services should be containerized and defined in docker-compose for local dev.",
        "",
        0.90,
    ),
    "Kubernetes": (
        "for Orchestration",
        "Kubernetes manages container deployment, scaling, and service discovery in production. "
        "All deployments should define resource limits, health checks, and rolling updates.",
        "",
        0.80,
    ),
    "Alembic": (
        "for Database Migrations",
        "Alembic provides version-controlled, reversible database migrations. Each schema "
        "change should be a new migration rather than manual ALTER TABLE statements.",
        "",
        0.85,
    ),
    "MongoDB": (
        "for Document Storage",
        "MongoDB provides flexible document storage for semi-structured data. Use for "
        "content management, analytics events, and configuration data. Not for relational data.",
        "",
        0.80,
    ),
    "React": (
        "for Frontend",
        "React provides component-based UI development with a virtual DOM for performance. "
        "Follow React patterns for state management and component composition.",
        "vue, angular, jquery",
        0.85,
    ),
    "Vue": (
        "for Frontend",
        "Vue provides progressive, incrementally-adoptable frontend framework. "
        "Use Vue's composition API for component logic and Pinia for state management.",
        "react, angular, jquery",
        0.85,
    ),
    "pytest": (
        "for Testing",
        "pytest provides a robust testing framework with fixtures, parametrization, and plugins. "
        "All code should have tests using pytest. Aim for >80% coverage on critical paths.",
        "unittest, nose",
        0.80,
    ),
    "Prometheus": (
        "for Monitoring",
        "Prometheus provides time-series monitoring and alerting. All services should expose "
        "metrics endpoints for request latency, error rates, and resource usage.",
        "",
        0.80,
    ),
    "Sentry": (
        "for Error Tracking",
        "Sentry provides real-time error tracking and performance monitoring. All services "
        "should integrate Sentry for exception capture and performance tracing.",
        "",
        0.80,
    ),
}


def generate_suggestions(
    model: ArchitectureModel,
    existing_adr_ids: set[str],
    existing_adr_titles: set[str],
    next_id: int,
) -> list[ADRSuggestion]:
    """Generate ADR + rule suggestions from an architecture model using templates."""
    suggestions: list[ADRSuggestion] = []
    num = next_id

    for tech in model.findings:
        if tech.confidence < 0.5:
            continue

        template = ADR_TEMPLATES.get(tech.name)
        if not template:
            continue

        title_suffix, rationale, prohibitions_str, base_conf = template
        title = f"Use {tech.name} {title_suffix}"

        if _is_duplicate(title, existing_adr_titles):
            continue

        adr_id = f"ADR-{num:04d}"
        num += 1

        prohibitions = [p.strip() for p in prohibitions_str.split(",") if p.strip()]

        conf_level = ConfidenceLevel.HIGH if base_conf >= 0.85 else (
            ConfidenceLevel.MEDIUM if base_conf >= 0.7 else ConfidenceLevel.LOW
        )

        adr = DecisionRecord(
            id=adr_id,
            title=title,
            status="proposed",
            severity="medium" if base_conf >= 0.8 else "low",
            type=tech.category,
            source="bootstrap",
            rationale=f"## Context\n\nThe repository uses {tech.name} ({tech.category}).\n\n"
                      f"## Decision (candidate)\n\n{tech.name} is detected with "
                      f"{tech.confidence:.0%} confidence based on {tech.evidence[0] if tech.evidence else 'structure analysis'}.\n\n"
                      f"{rationale}\n\n"
                      f"## Confidence\n\n{tech.confidence:.0%} (structural detection). "
                      f"This rationale is inferred, not confirmed by the team.",
            prohibitions=prohibitions,
            keywords=[tech.name.lower(), tech.category],
            evidence=tech.evidence,
            confidence=conf_level,
        )

        rules = []
        for p in prohibitions:
            rules.append({"type": "dependency", "match": p, "action": "block"})
            rules.append({"type": "import", "match": p, "action": "block"})

        suggestions.append(ADRSuggestion(tech=tech, adr=adr, rules=rules))

    return suggestions


def apply_suggestions(
    suggestions: list[ADRSuggestion],
    adr_dir: str | Path,
) -> int:
    """Write suggested ADRs to disk."""
    adr_path = Path(adr_dir)
    adr_path.mkdir(parents=True, exist_ok=True)
    written = 0
    for s in suggestions:
        path = adr_path / f"{s.adr.id}.md"
        metadata = s.adr.model_dump(exclude={"embedding", "rationale"})
        for k, v in metadata.items():
            if isinstance(v, Enum):
                metadata[k] = v.value
        write_adr(path, metadata, s.adr.rationale)
        written += 1
    return written


def _is_duplicate(title: str, existing_titles: set[str]) -> bool:
    tl = title.lower()
    for et in existing_titles:
        if tl == et.lower():
            return True
    return False
