from __future__ import annotations

from pathlib import Path

from decisiondrift.bootstrap.patterns import REGISTRY, match_patterns
from decisiondrift.bootstrap.structure_scan import scan_repo

HMS_V2 = Path(__file__).parent.parent / "repos" / "hospital-management-system-V2"


class TestPatternDefinitions:
    def test_registry_has_known_patterns(self):
        names = [p.name for p in REGISTRY]
        assert "Use Flask as Web Framework" in names
        assert "Use SQLAlchemy as ORM" in names
        assert "Use Celery for Async Tasks" in names
        assert "Use Alembic for Database Migrations" in names
        assert "Use Flask Blueprints for Modular Routes" in names
        assert "Use Shared Utility Modules" in names


class TestPatternMatcher:
    def test_matches_flask(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        match_names = [m.pattern.name for m in matches]
        assert "Use Flask as Web Framework" in match_names

    def test_matches_sqlalchemy(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        match_names = [m.pattern.name for m in matches]
        assert "Use SQLAlchemy as ORM" in match_names

    def test_matches_celery(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        match_names = [m.pattern.name for m in matches]
        assert "Use Celery for Async Tasks" in match_names

    def test_matches_alembic(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        match_names = [m.pattern.name for m in matches]
        assert "Use Alembic for Database Migrations" in match_names

    def test_matches_flask_blueprints(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        match_names = [m.pattern.name for m in matches]
        assert "Use Flask Blueprints for Modular Routes" in match_names

    def test_matches_separate_frontend(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        match_names = [m.pattern.name for m in matches]
        assert "Separate Frontend Application" in match_names

    def test_match_has_evidence(self):
        structure = scan_repo(HMS_V2)
        matches = match_patterns(structure)
        for m in matches:
            assert len(m.evidence) > 0

    def test_empty_structure_returns_no_matches(self):
        from decisiondrift.bootstrap.structure_scan import ProjectStructure

        empty = ProjectStructure(root="/tmp")
        matches = match_patterns(empty)
        assert matches == []
