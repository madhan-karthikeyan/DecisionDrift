from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.supersession import resolve_active
from decisiondrift.impact.models import ChangedSymbol
from decisiondrift.impact.reference_scan import generate_search_terms
from decisiondrift.retrieval.keyword import KeywordBackend

DATA_DIR = Path(__file__).parent / "data"
ADR_DIR = Path(__file__).parent.parent / "repos" / "hospital-management-system-V2" / "docs" / "adr"


@pytest.fixture(scope="module")
def decisions():
    records = load_adrs(str(ADR_DIR))
    return resolve_active(records)


@pytest.fixture(scope="module")
def queries():
    with open(DATA_DIR / "queries.yaml") as f:
        data = yaml.safe_load(f)
    return data["queries"]


class TestRetrievalAccuracy:
    def test_all_queries_have_expected_adrs_in_top_5(self, decisions, queries):
        backend = KeywordBackend()
        failures = []

        for q in queries:
            symbol = ChangedSymbol(
                name=q["symbol_name"],
                symbol_type="function",
                file_path=q["file_path"],
                start_line=1,
                end_line=10,
            )
            terms = generate_search_terms([symbol])
            results = backend.query(terms, decisions, top_k=5)
            result_ids = {r.adr_id for r in results}

            for expected in q["expected_adrs"]:
                if expected not in result_ids:
                    failures.append(f"  {q['symbol_name']} ({q['file_path']}) → expected {expected} not in top-5")

        assert not failures, "Retrieval failures:\n" + "\n".join(failures)

    def test_top_result_contains_primary_adr(self, decisions, queries):
        backend = KeywordBackend()
        failures = []

        for q in queries:
            symbol = ChangedSymbol(
                name=q["symbol_name"],
                symbol_type="function",
                file_path=q["file_path"],
                start_line=1,
                end_line=10,
            )
            terms = generate_search_terms([symbol])
            results = backend.query(terms, decisions, top_k=5)

            if not results:
                failures.append(f"  {q['symbol_name']} ({q['file_path']}) → no results")
                continue

            primary = q["expected_adrs"][0]
            if results[0].adr_id != primary:
                top = results[0]
                failures.append(
                    f"  {q['symbol_name']} ({q['file_path']}) → "
                    f"top result is {top.adr_id} ({top.score}), expected {primary}"
                )

        assert not failures, "Top result mismatches:\n" + "\n".join(failures)
