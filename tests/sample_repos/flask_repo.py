from __future__ import annotations

from pathlib import Path


def create_flask_repo(root: Path) -> Path:
    repo = root / "flask-app"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "app").mkdir(exist_ok=True)
    (repo / "app" / "__init__.py").write_text("from flask import Flask\n\napp = Flask(__name__)\n")
    (repo / "app" / "views.py").write_text(
        "from flask import jsonify\n\n@app.route('/health')\ndef health():\n    return jsonify({'status': 'ok'})\n"
    )
    (repo / "requirements.txt").write_text("flask==3.0\nredis==5.0\nsqlalchemy==2.0\npytest==8.0\n")
    (repo / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (repo / ".gitkeep").write_text("")
    return repo


def create_flask_repo_with_adrs(root: Path) -> tuple[Path, list[str]]:
    repo = create_flask_repo(root)
    adr_dir = repo / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)

    adr_paths = []
    adr1 = adr_dir / "ADR-0001.md"
    adr1.write_text(
        "---\n"
        "id: ADR-0001\n"
        "title: Use Flask as Web Framework\n"
        "status: accepted\n"
        "severity: high\n"
        "source: bootstrap\n"
        "prohibitions:\n"
        "  - fastapi\n"
        "  - django\n"
        "keywords:\n"
        "  - flask\n"
        "  - framework\n"
        "---\n"
        "# ADR-0001: Use Flask as Web Framework\n\n"
        "Flask is the chosen web framework.\n"
    )
    adr_paths.append(str(adr1))

    adr2 = adr_dir / "ADR-0002.md"
    adr2.write_text(
        "---\n"
        "id: ADR-0002\n"
        "title: Use SQLAlchemy for Database Access\n"
        "status: accepted\n"
        "severity: medium\n"
        "source: manual\n"
        "prohibitions:\n"
        "  - peewee\n"
        "  - pony\n"
        "keywords:\n"
        "  - sqlalchemy\n"
        "  - database\n"
        "---\n"
        "# ADR-0002: Use SQLAlchemy for Database Access\n\n"
        "SQLAlchemy is the ORM for all database access.\n"
    )
    adr_paths.append(str(adr2))

    return repo, adr_paths
