from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from decisiondrift.config import load_config
from decisiondrift.review.service import run_review

EVAL_DIR = Path(__file__).parent
PATCHES_DIR = EVAL_DIR / "patches"
REPO_DIR = Path(__file__).parent.parent.parent / "repos" / "hospital-management-system-V2"
ADR_DIR = REPO_DIR / "docs" / "adr"

HAS_API_KEY = bool(os.environ.get("DECISIONDRIFT_LLM_API_KEY"))


@pytest.fixture(scope="session")
def expectations():
    with open(EVAL_DIR / "expectations.yaml") as f:
        data = yaml.safe_load(f)
    return data["patches"]


@pytest.fixture(scope="session")
def config():
    cfg = load_config()
    cfg["similarity_threshold"] = 0.0
    cfg["top_k"] = 10
    return cfg


class TestRetrievalEvaluation:
    """Tests that the correct ADRs are retrieved for each patch."""

    @pytest.mark.parametrize(
        "patch_name",
        [
            "sqlalchemy_violation",
            "jwt_violation",
            "celery_violation",
            "rbac_violation",
            "clean_change",
        ],
    )
    def test_expected_adrs_in_top_retrieval(self, patch_name, expectations, config):
        spec = expectations[patch_name]
        patch_text = (PATCHES_DIR / spec["file"]).read_text()

        result = run_review(patch_text, repo_path=str(REPO_DIR), adr_dir=str(ADR_DIR), config=config)

        retrieved_adrs = {f.adr_id for f in result.findings}
        expected = set(spec["expected_adrs"])

        missing = expected - retrieved_adrs
        assert not missing, f"{patch_name}: expected ADRs {missing} not in retrieved set {retrieved_adrs}"

    @pytest.mark.parametrize(
        "patch_name",
        [
            "sqlalchemy_violation",
            "jwt_violation",
            "celery_violation",
            "rbac_violation",
            "clean_change",
        ],
    )
    def test_retrieval_has_files_and_symbols(self, patch_name, expectations, config):
        spec = expectations[patch_name]
        patch_text = (PATCHES_DIR / spec["file"]).read_text()

        result = run_review(patch_text, repo_path=str(REPO_DIR), adr_dir=str(ADR_DIR), config=config)

        assert result.files_scanned > 0, f"{patch_name}: no files scanned"
        assert result.symbols_analyzed > 0, f"{patch_name}: no symbols analyzed"
        assert result.adrs_considered > 0, f"{patch_name}: no ADRs considered"


class TestClassificationEvaluation:
    """Tests that the LLM classifies each patch correctly.

    Requires DECISIONDRIFT_LLM_API_KEY to be set.
    """

    @pytest.mark.skipif(not HAS_API_KEY, reason="DECISIONDRIFT_LLM_API_KEY not set")
    @pytest.mark.parametrize(
        "patch_name",
        [
            "sqlalchemy_violation",
            "jwt_violation",
            "celery_violation",
            "rbac_violation",
        ],
    )
    def test_violation_classification(self, patch_name, expectations, config):
        spec = expectations[patch_name]
        patch_text = (PATCHES_DIR / spec["file"]).read_text()

        result = run_review(patch_text, repo_path=str(REPO_DIR), adr_dir=str(ADR_DIR), config=config)

        violations = [f for f in result.findings if f.classification in ("violates", "likely_violates")]
        violation_adrs = {f.adr_id for f in violations}
        primary_expected = spec["expected_adrs"][0]

        assert primary_expected in violation_adrs, (
            f"{patch_name}: expected {primary_expected} in violations, got violations for {violation_adrs}"
        )

    @pytest.mark.skipif(not HAS_API_KEY, reason="DECISIONDRIFT_LLM_API_KEY not set")
    def test_clean_change_no_violations(self, expectations, config):
        spec = expectations["clean_change"]
        patch_text = (PATCHES_DIR / spec["file"]).read_text()

        result = run_review(patch_text, repo_path=str(REPO_DIR), adr_dir=str(ADR_DIR), config=config)

        violations = [f for f in result.findings if f.classification in ("violates", "likely_violates")]
        assert len(violations) == 0, (
            f"clean_change: expected no violations, got {len(violations)}: "
            f"{[(f.adr_id, f.classification) for f in violations]}"
        )
