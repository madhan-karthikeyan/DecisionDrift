from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from decisiondrift.config import load_config
from decisiondrift.review.service import run_review

EVAL_DIR = Path(__file__).parent
PATCHES_DIR = EVAL_DIR / "patches"
REPO_DIR = Path(__file__).parent.parent.parent / "repos" / "hospital-management-system-V2"
ADR_DIR = REPO_DIR / "docs" / "adr"

HAS_API_KEY = bool(load_config()["llm"]["api_key"])


def load_expectations() -> dict[str, Any]:
    with open(EVAL_DIR / "expectations.yaml") as f:
        return yaml.safe_load(f)["patches"]


def run_patch(patch_name: str) -> tuple[Any, Any]:
    spec = load_expectations()[patch_name]
    patch_text = (PATCHES_DIR / spec["file"]).read_text()
    config = load_config()
    config["similarity_threshold"] = 0.0
    config["top_k"] = 10
    result = run_review(patch_text, repo_path=str(REPO_DIR), adr_dir=str(ADR_DIR), config=config)
    return spec, result


def compute_retrieval_metrics() -> dict:
    expectations = load_expectations()
    total = len(expectations)
    top5_hits = 0
    top1_hits = 0
    results: list[dict] = []

    for name, spec in expectations.items():
        _, result = run_patch(name)
        retrieved_adrs = {f.adr_id for f in result.findings}
        expected_set = set(spec["expected_adrs"])

        any_hit = bool(expected_set & retrieved_adrs)
        top1 = list(expected_set)[0] if expected_set else None
        top1_hit = top1 in retrieved_adrs if top1 else False

        if any_hit:
            top5_hits += 1
        if top1_hit:
            top1_hits += 1

        results.append(
            {
                "name": name,
                "expected": spec["expected_adrs"],
                "retrieved": sorted(retrieved_adrs),
                "top5_hit": any_hit,
                "top1_hit": top1_hit,
                "files_scanned": result.files_scanned,
                "symbols_analyzed": result.symbols_analyzed,
                "adrs_considered": result.adrs_considered,
            }
        )

    return {
        "total": total,
        "top5_hits": top5_hits,
        "top1_hits": top1_hits,
        "recall_at_5": top5_hits / total if total else 0.0,
        "recall_at_1": top1_hits / total if total else 0.0,
        "details": results,
    }


def compute_classification_metrics() -> dict:
    expectations = load_expectations()
    tp = 0  # violation correctly flagged as violates
    fp = 0  # non-violation flagged as violates
    fn = 0  # violation not flagged
    tn = 0  # non-violation not flagged
    results: list[dict] = []

    for name, spec in expectations.items():
        _, result = run_patch(name)
        violations = {f.adr_id for f in result.findings if f.classification in ("violates", "likely_violates")}
        expected_set = set(spec["expected_adrs"])

        is_violation_patch = spec["expected_classification"] in ("violates", "likely_violates")

        primary = list(expected_set)[0] if expected_set else None
        found = primary in violations if primary else False

        if is_violation_patch:
            if found:
                tp += 1
            else:
                fn += 1
        else:
            if found:
                fp += 1
            else:
                tn += 1

        results.append(
            {
                "name": name,
                "is_violation": is_violation_patch,
                "primary_adr": primary,
                "found_in_violations": found,
                "classifications": {f.adr_id: f.classification for f in result.findings},
            }
        )

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "details": results,
    }


class TestRetrievalMetrics:
    def test_recall_at_5(self):
        metrics = compute_retrieval_metrics()
        assert metrics["recall_at_5"] >= 0.5, (
            f"Retrieval Recall@5 = {metrics['recall_at_5']:.2f} ({metrics['top5_hits']}/{metrics['total']})"
        )

    def test_recall_at_1(self):
        metrics = compute_retrieval_metrics()
        assert metrics["recall_at_1"] >= 0.3, (
            f"Retrieval Recall@1 = {metrics['recall_at_1']:.2f} ({metrics['top1_hits']}/{metrics['total']})"
        )

    def test_all_patches_produce_findings(self):
        metrics = compute_retrieval_metrics()
        for d in metrics["details"]:
            assert d["files_scanned"] > 0, f"{d['name']}: no files scanned"
            assert d["symbols_analyzed"] > 0, f"{d['name']}: no symbols analyzed"


class TestClassificationMetrics:
    @pytest.mark.skipif(not HAS_API_KEY, reason="DECISIONDRIFT_LLM_API_KEY not set")
    def test_precision(self):
        metrics = compute_classification_metrics()
        assert metrics["precision"] >= 0.5, (
            f"Classification Precision = {metrics['precision']:.2f} "
            f"({metrics['tp']}TP / {metrics['tp'] + metrics['fp']} total)"
        )

    @pytest.mark.skipif(not HAS_API_KEY, reason="DECISIONDRIFT_LLM_API_KEY not set")
    def test_recall(self):
        metrics = compute_classification_metrics()
        assert metrics["recall"] >= 0.3, (
            f"Classification Recall = {metrics['recall']:.2f} "
            f"({metrics['tp']}TP / {metrics['tp'] + metrics['fn']} total)"
        )

    @pytest.mark.skipif(not HAS_API_KEY, reason="DECISIONDRIFT_LLM_API_KEY not set")
    def test_f1_score(self):
        metrics = compute_classification_metrics()
        assert metrics["f1"] >= 0.3, f"Classification F1 = {metrics['f1']:.2f}"
