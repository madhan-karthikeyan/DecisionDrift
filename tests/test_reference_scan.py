from __future__ import annotations

from decisiondrift.impact.models import ChangedSymbol
from decisiondrift.impact.reference_scan import generate_search_terms


class TestGenerateSearchTerms:
    def test_symbol_name_included(self):
        symbols = [
            ChangedSymbol(
                name="UserRepository", symbol_type="class", file_path="repositories/user.py", start_line=1, end_line=10
            )
        ]
        terms = generate_search_terms(symbols)
        assert "UserRepository" in terms

    def test_file_path_components(self):
        symbols = [
            ChangedSymbol(
                name="get_user",
                symbol_type="function",
                file_path="backend/services/user_service.py",
                start_line=1,
                end_line=5,
            )
        ]
        terms = generate_search_terms(symbols)
        assert "backend" in terms
        assert "services" in terms
        assert "user_service" in terms

    def test_underscore_parts(self):
        symbols = [
            ChangedSymbol(
                name="create_user", symbol_type="function", file_path="services/user.py", start_line=1, end_line=5
            )
        ]
        terms = generate_search_terms(symbols)
        assert "create" in terms
        assert "user" in terms

    def test_camelcase_breakdown(self):
        symbols = [
            ChangedSymbol(
                name="PostgresAdapter", symbol_type="class", file_path="adapters/postgres.py", start_line=1, end_line=10
            )
        ]
        terms = generate_search_terms(symbols)
        assert "PostgresAdapter" in terms
        assert "Postgres" in terms
        assert "Adapter" in terms

    def test_no_duplicates(self):
        symbols = [
            ChangedSymbol(
                name="UserService", symbol_type="class", file_path="services/user_service.py", start_line=1, end_line=10
            ),
            ChangedSymbol(
                name="get_user",
                symbol_type="function",
                file_path="services/user_service.py",
                start_line=12,
                end_line=15,
            ),
        ]
        terms = generate_search_terms(symbols)
        assert len(terms) == len(set(t.lower() for t in terms))

    def test_empty_symbols(self):
        assert generate_search_terms([]) == []
