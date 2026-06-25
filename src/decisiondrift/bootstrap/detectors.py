from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from decisiondrift.bootstrap.structure_scan import ProjectStructure


@dataclass
class DetectedTechnology:
    category: str
    name: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


@dataclass
class DetectionContext:
    repo_path: Path
    deps: list[str]
    imports: list[str]
    structure: ProjectStructure


TECHNOLOGY_REGISTRY: list[
    tuple[str, str, list[str] | None, list[str] | None, list[str] | None, float, float, float]
] = [
    # (category, name, dep_names, import_names, indicator_files, dep_conf, import_conf, file_conf)
    # --- Frameworks ---
    ("framework", "FastAPI", ["fastapi", "uvicorn"], None, None, 0.95, 0.90, 0.0),
    ("framework", "Flask", ["flask"], ["flask"], None, 0.95, 0.90, 0.0),
    ("framework", "Django", ["django"], None, ["manage.py"], 0.95, 0.90, 0.60),
    ("framework", "Express", ["express"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Next.js", ["next"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Nuxt.js", ["nuxt"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Spring Boot", ["spring-boot"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Gin", ["gin-gonic/gin"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Echo", ["labstack/echo"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Rocket", ["rocket"], None, None, 0.85, 0.00, 0.0),
    ("framework", "Actix", ["actix-web"], None, None, 0.85, 0.00, 0.0),
    ("framework", "Tokio", ["tokio"], None, None, 0.85, 0.00, 0.0),
    ("framework", "NestJS", ["@nestjs/core"], None, None, 0.90, 0.00, 0.0),
    ("framework", "Strapi", ["@strapi/strapi"], None, ["favicon.png"], 0.90, 0.00, 0.60),
    # --- Databases ---
    ("database", "PostgreSQL", ["psycopg2", "psycopg", "asyncpg", "pg", "libpq", "pq"], None, None, 0.85, 0.00, 0.0),
    (
        "database",
        "MySQL",
        ["mysqlclient", "mysql-connector", "pymysql", "mysql2", "mariadb"],
        None,
        None,
        0.85,
        0.00,
        0.0,
    ),
    ("database", "SQLite", ["sqlite3", "sqlite", "better-sqlite3"], None, None, 0.80, 0.00, 0.0),
    ("database", "MongoDB", ["pymongo", "mongodb", "mongoose", "mongo"], None, None, 0.85, 0.00, 0.0),
    # --- ORMs ---
    ("orm", "SQLAlchemy", ["sqlalchemy"], None, None, 0.90, 0.85, 0.0),
    ("orm", "Prisma", ["@prisma/client", "prisma"], None, None, 0.90, 0.00, 0.0),
    ("orm", "Sequelize", ["sequelize"], None, None, 0.85, 0.00, 0.0),
    ("orm", "Mongoose", ["mongoose"], None, None, 0.85, 0.00, 0.0),
    ("orm", "TypeORM", ["typeorm"], None, None, 0.85, 0.00, 0.0),
    ("orm", "GORM", ["gorm.io/gorm"], None, None, 0.85, 0.00, 0.0),
    ("orm", "Diesel", ["diesel"], None, None, 0.85, 0.00, 0.0),
    ("orm", "ActiveRecord", ["activerecord"], None, None, 0.85, 0.00, 0.0),
    # --- Caches ---
    ("cache", "Redis", ["redis", "ioredis", "django-redis"], None, None, 0.85, 0.80, 0.0),
    ("cache", "Memcached", ["pymemcache", "memcached", "django-pymemcache"], None, None, 0.80, 0.00, 0.0),
    # --- Message Queues ---
    ("queue", "Celery", ["celery"], None, ["celery.py"], 0.90, 0.85, 0.85),
    ("queue", "RQ", ["rq", "redis-queue"], None, None, 0.80, 0.00, 0.0),
    ("queue", "Sidekiq", ["sidekiq"], None, None, 0.85, 0.00, 0.0),
    ("queue", "Bull", ["bull", "bullmq"], None, None, 0.80, 0.00, 0.0),
    ("queue", "RabbitMQ", ["pika", "amqp", "rabbitmq", "bunny", "amqp-client"], None, None, 0.80, 0.00, 0.0),
    ("queue", "Kafka", ["kafka-python", "confluent-kafka", "kafka-node", "kafka"], None, None, 0.80, 0.00, 0.0),
    # --- Languages ---
    ("language", "Go", ["go", "golang"], None, ["go.mod"], 0.60, 0.00, 0.95),
    (
        "language",
        "Python",
        ["python"],
        None,
        ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
        0.60,
        0.00,
        0.90,
    ),
    ("language", "Rust", ["rust"], None, ["Cargo.toml"], 0.60, 0.00, 0.95),
    ("language", "JavaScript", None, None, ["package.json"], 0.00, 0.00, 0.90),
    # --- ML ---
    ("framework", "PyTorch", ["torch", "pytorch"], None, None, 0.90, 0.00, 0.0),
    # --- DevOps ---
    ("framework", "Argo CD", ["github.com/argoproj/argo-cd"], None, None, 0.90, 0.00, 0.0),
    # --- Authentication ---
    ("auth", "JWT", ["pyjwt", "jwt", "jsonwebtoken", "golang-jwt", "jjwt"], None, None, 0.80, 0.75, 0.0),
    ("auth", "OAuth", ["authlib", "oauthlib", "passport", "oauth2"], None, None, 0.70, 0.00, 0.0),
    ("auth", "Devise", ["devise"], None, None, 0.85, 0.00, 0.0),
    ("auth", "Passport", ["passport"], None, None, 0.85, 0.00, 0.0),
    # --- Frontend ---
    ("frontend", "React", ["react", "react-dom"], None, None, 0.90, 0.00, 0.0),
    ("frontend", "Vue", ["vue"], None, None, 0.90, 0.00, 0.0),
    ("frontend", "Svelte", ["svelte"], None, None, 0.90, 0.00, 0.0),
    ("frontend", "Angular", ["@angular/core"], None, None, 0.90, 0.00, 0.0),
    # --- CSS Frameworks ---
    ("css", "Tailwind CSS", ["tailwindcss"], None, None, 0.85, 0.00, 0.0),
    ("css", "Bootstrap", ["bootstrap"], None, None, 0.80, 0.00, 0.0),
    # --- Testing ---
    ("testing", "pytest", ["pytest"], None, None, 0.85, 0.00, 0.0),
    ("testing", "Jest", ["jest"], None, None, 0.85, 0.00, 0.0),
    ("testing", "RSpec", ["rspec", "rspec-rails"], None, None, 0.85, 0.00, 0.0),
    ("testing", "Mocha", ["mocha"], None, None, 0.80, 0.00, 0.0),
    ("testing", "JUnit", ["junit"], None, None, 0.80, 0.00, 0.0),
    # --- Container / Infrastructure ---
    ("container", "Docker", None, None, ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"], 0.0, 0.0, 0.95),
    ("container", "Kubernetes", None, None, [".kube", "k8s"], 0.0, 0.0, 0.85),
    # --- CI ---
    ("ci", "GitHub Actions", None, None, [".github/workflows"], 0.0, 0.0, 0.90),
    ("ci", "GitLab CI", None, None, [".gitlab-ci.yml"], 0.0, 0.0, 0.90),
    # --- Migrations ---
    ("migration", "Alembic", ["alembic"], None, ["alembic.ini", "migrations"], 0.90, 0.0, 0.85),
    # --- Monitoring ---
    ("monitoring", "Prometheus", ["prometheus-client"], None, None, 0.80, 0.00, 0.0),
    ("monitoring", "Sentry", ["sentry-sdk"], None, None, 0.80, 0.00, 0.0),
]


def _match_dep(dl: str, dn: str) -> bool:
    """Match a dependency string against a detector name.

    Supports:
      - Exact match: 'flask' == 'flask'
      - Submodule: 'sqlalchemy.orm' starts with 'sqlalchemy.'
      - Go module: 'github.com/gin-gonic/gin' ends with '/gin-gonic/gin'
      - Java artifact: 'spring-boot-starter-web' starts with 'spring-boot-'
      - Python extras: 'psycopg[binary]' starts with 'psycopg'
    """
    if dl == dn:
        return True
    if dl.startswith(dn + ".") or dl.startswith(dn + "-") or dl.startswith(dn + "_"):
        return True
    if dl.endswith("/" + dn):
        return True
    # Handle extras like psycopg[binary] -> psycopg
    bracket = dl.find("[")
    if bracket > 0 and dl[:bracket] == dn:
        return True
    return False


def detect_technologies(ctx: DetectionContext) -> list[DetectedTechnology]:
    """Run all technology detectors against a repo context."""
    findings: list[DetectedTechnology] = []
    seen: set[str] = set()

    for cat, name, dep_names, import_names, file_names, dep_conf, imp_conf, file_conf in TECHNOLOGY_REGISTRY:
        evidence: list[str] = []
        best_conf = 0.0

        if dep_names:
            for dep in ctx.deps:
                dl = dep.lower()
                if any(_match_dep(dl, dn.lower()) for dn in dep_names):
                    evidence.append(f"dependency: {dep}")
                    best_conf = max(best_conf, dep_conf)
                    break

        if import_names and ctx.imports:
            for imp in ctx.imports:
                il = imp.lower()
                if il in [n.lower() for n in import_names]:
                    evidence.append(f"import: {imp}")
                    best_conf = max(best_conf, imp_conf)
                    break

        if file_names:
            for fn in file_names:
                if ctx.structure.has_file(fn) or ctx.structure.has_subdir(fn):
                    evidence.append(f"file: {fn}")
                    best_conf = max(best_conf, file_conf)
                    break

        if evidence and name not in seen:
            seen.add(name)
            findings.append(
                DetectedTechnology(
                    category=cat,
                    name=name,
                    confidence=best_conf,
                    evidence=evidence,
                )
            )

    findings.sort(key=lambda f: f.confidence, reverse=True)
    return findings


def collect_deps(repo_path: Path) -> list[str]:
    """Collect all dependencies from various dependency files."""
    deps: list[str] = []
    seen: set[str] = set()
    scanners = [
        _scan_requirements_txt,
        _scan_pyproject_toml_deps,
        _scan_setup_py,
        _scan_package_json_deps,
        _scan_go_mod_deps,
        _scan_cargo_toml_deps,
        _scan_pom_xml,
        _scan_build_gradle,
        _scan_tox_ini,
        _scan_noxfile,
    ]
    for scanner in scanners:
        for dep in scanner(repo_path):
            d = dep.lower().strip()
            if d and d not in seen:
                seen.add(d)
                deps.append(d)
    return deps


_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        ".tox",
        ".nox",
        "dist",
        "build",
        ".eggs",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".gradle",
        ".idea",
        ".vscode",
    }
)


def _find_files(repo: Path, filename: str) -> list[Path]:
    """Recursively find all files matching `filename`, excluding noise dirs."""
    results: list[Path] = []
    try:
        for f in repo.rglob(filename):
            parts = f.relative_to(repo).parts[:-1]
            if any(p in _EXCLUDE_DIRS or p.startswith(".") for p in parts):
                continue
            results.append(f)
    except (OSError, ValueError):
        pass
    return results


def _scan_requirements_txt(repo: Path) -> list[str]:
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "requirements.txt"):
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                pkg = re.split(r"[=<>!~\[ ]", line)[0].strip()
                if pkg:
                    pkgs.append(pkg)
        except OSError:
            pass
    return pkgs


def _scan_pyproject_toml_deps(repo: Path) -> list[str]:
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "pyproject.toml"):
        try:
            import tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (ImportError, OSError, ValueError):
            continue
        proj = data.get("project", {})
        for dep in proj.get("dependencies", []):
            if isinstance(dep, str):
                pkg = re.split(r"[=<>!~\[ ]", dep)[0].strip()
                if pkg:
                    pkgs.append(pkg)
        for group in proj.get("optional-dependencies", {}).values():
            if isinstance(group, list):
                for dep in group:
                    if isinstance(dep, str):
                        pkg = re.split(r"[=<>!~\[ ]", dep)[0].strip()
                        if pkg:
                            pkgs.append(pkg)
        # PEP 735 dependency-groups
        for group in data.get("dependency-groups", {}).values():
            if isinstance(group, list):
                for dep in group:
                    if isinstance(dep, str):
                        pkg = re.split(r"[=<>!~\[ ]", dep)[0].strip()
                        if pkg:
                            pkgs.append(pkg)
    return pkgs


def _scan_package_json_deps(repo: Path) -> list[str]:
    pkgs: list[str] = []
    for path in _find_files(repo, "package.json"):
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            for pkg in data.get(key, {}):
                pkgs.append(pkg)
    return pkgs


def _scan_go_mod_deps(repo: Path) -> list[str]:
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "go.mod"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            # Extract module name (the repo's own Go module)
            mm = re.match(r"module\s+(\S+)", text)
            if mm:
                pkgs.append(mm.group(1))
            # Extract dependency paths
            for line in text.splitlines():
                m = re.match(r"\t([^\s]+)\s+v", line)
                if m:
                    pkgs.append(m.group(1))
        except OSError:
            pass
    return pkgs


def _scan_cargo_toml_deps(repo: Path) -> list[str]:
    pkgs: list[str] = []
    for path in _find_files(repo, "Cargo.toml"):
        try:
            import tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (ImportError, OSError, ValueError):
            continue
        # Extract the crate's own package name
        pkg_info = data.get("package", {})
        if isinstance(pkg_info, dict) and "name" in pkg_info:
            pkgs.append(pkg_info["name"])
        # Extract dependency names
        for dep in data.get("dependencies", {}):
            pkgs.append(dep)
    return pkgs


def _scan_pom_xml(repo: Path) -> list[str]:
    """Parse Maven POM files for artifact IDs (spring-boot, mysql-connector, etc.)"""
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "pom.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"<artifactId>([^<]+)</artifactId>", text):
                pkgs.append(m.group(1))
        except OSError:
            pass
    return pkgs


def _scan_build_gradle(repo: Path) -> list[str]:
    """Parse Gradle build files for dependency declarations."""
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "build.gradle") + _find_files(repo, "build.gradle.kts"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            # Match: implementation 'group:artifact:version' or implementation("group:artifact:version")
            for m in re.finditer(r"['\"]([^'\"]+):([^'\"]+):[^'\"]+['\"]", text):
                pkgs.append(m.group(2))
            # Match: id 'org.springframework.boot' or id("org.springframework.boot")
            for m in re.finditer(r"id\s+['\"]([^'\"]+)['\"]", text):
                pkgs.append(m.group(1))
        except OSError:
            pass
    return pkgs


def _scan_tox_ini(repo: Path) -> list[str]:
    """Parse tox.ini for test dependency extras (pytest, etc.)"""
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "tox.ini"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            in_deps = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("deps") or stripped.startswith("extras"):
                    in_deps = True
                    continue
                if in_deps:
                    if stripped.startswith("[") or stripped.startswith("env"):
                        in_deps = False
                        continue
                    if stripped and not stripped.startswith("#") and not stripped.startswith(";"):
                        pkg = re.split(r"[=<>!~\[ ]", stripped)[0].strip()
                        if pkg:
                            pkgs.append(pkg)
        except OSError:
            pass
    return pkgs


def _scan_noxfile(repo: Path) -> list[str]:
    """Parse noxfile.py for installed packages (pytest, etc.)."""
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "noxfile.py") + _find_files(repo, "noxfile"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'["\']([a-z][a-z0-9_-]*)["\']', text):
                pkgs.append(m.group(1))
        except OSError:
            pass
    return pkgs


def _scan_setup_py(repo: Path) -> list[str]:
    """Parse setup.py for install_requires and extras_require."""
    import re

    pkgs: list[str] = []
    for path in _find_files(repo, "setup.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            # Extract strings from install_requires and extras_require
            for m in re.finditer(r'["\']([a-zA-Z][a-zA-Z0-9_.-]*)["\']', text):
                pkg = m.group(1)
                if pkg and not pkg.startswith("_") and len(pkg) > 2:
                    pkgs.append(pkg)
        except OSError:
            pass
    return pkgs
