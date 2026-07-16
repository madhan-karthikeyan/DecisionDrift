from __future__ import annotations

import re
from pathlib import Path

from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.supersession import resolve_active
from decisiondrift.classification.classifier import Classifier
from decisiondrift.classification.models import ClassificationInput
from decisiondrift.config import load_config
from decisiondrift.impact.reference_scan import generate_search_terms
from decisiondrift.impact.service import analyze_diff
from decisiondrift.models.schema import ImpactedSymbol, ReviewResult
from decisiondrift.retrieval.keyword import KeywordBackend
from decisiondrift.retrieval.embedding import HAS_FASTEMBED, EmbeddingBackend


def _extract_hunks(diff_text: str) -> dict[str, str]:
    """Extract diff hunks grouped by file path from a unified diff."""
    hunks: dict[str, str] = {}
    current_file: str | None = None
    current_hunk_lines: list[str] = []

    for line in diff_text.splitlines():
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            if current_file and current_hunk_lines:
                hunks[current_file] = "\n".join(current_hunk_lines)
            current_file = m.group(1)
            current_hunk_lines = []
            continue

        if current_file is None:
            continue

        m2 = re.match(r"^@@", line)
        if m2:
            if current_hunk_lines:
                if current_file:
                    hunks[current_file] = (hunks.get(current_file, "") + "\n" + "\n".join(current_hunk_lines)).strip()
            current_hunk_lines = [line]
            continue

        if current_hunk_lines is not None:
            current_hunk_lines.append(line)

    if current_file and current_hunk_lines:
        existing = hunks.get(current_file, "")
        joined = "\n".join(current_hunk_lines)
        hunks[current_file] = (existing + "\n" + joined).strip()

    return hunks


def run_review(
    diff_text: str,
    repo_path: str | Path = ".",
    adr_dir: str = "docs/adr",
    config: dict | None = None,
) -> ReviewResult:
    if config is None:
        config = load_config()

    classifier = Classifier(
        model=config["llm"]["model"],
        api_key=config["llm"]["api_key"],
        base_url=config["llm"].get("base_url"),
    )
    llm_available = classifier.llm.available()

    impact = analyze_diff(diff_text, repo_path=repo_path)

    if not llm_available:
        return ReviewResult(
            files_scanned=len(impact.files),
            symbols_analyzed=len(impact.symbols),
            llm_available=False,
        )

    if not impact.symbols:
        return ReviewResult(
            files_scanned=len(impact.files),
            symbols_analyzed=len(impact.symbols),
        )

    decisions = load_adrs(adr_dir, status_filter={"accepted"})
    active = resolve_active(decisions)

    if not active:
        return ReviewResult(
            files_scanned=len(impact.files),
            symbols_analyzed=len(impact.symbols),
        )

    hunks = _extract_hunks(diff_text)

    threshold = config.get("similarity_threshold", 0.5)
    top_k = config.get("top_k", 5)
    max_pairs = config.get("max_pairs_per_pr", 15)
    embedding_model = config.get("embedding_model", "BAAI/bge-small-en-v1.5")

    keyword_backend = KeywordBackend()
    embedding_backend = EmbeddingBackend(model_name=embedding_model) if HAS_FASTEMBED else None
    inputs: list[ClassificationInput] = []
    pairs_used = 0

    for symbol in impact.symbols:
        if pairs_used >= max_pairs:
            break
        terms = generate_search_terms([symbol])
        results = keyword_backend.query(terms, active, top_k=top_k)
        above_threshold = [r for r in results if r.score >= threshold]

        if not above_threshold and embedding_backend:
            results = embedding_backend.query(terms, active, top_k=top_k)
            above_threshold = [r for r in results if r.score >= threshold]

        for r in above_threshold:
            if pairs_used >= max_pairs:
                break
            if r.score < threshold:
                continue
            adr = next(d for d in active if d.id == r.adr_id)
            impacted = ImpactedSymbol(
                name=symbol.name,
                kind=symbol.symbol_type,
                file=symbol.file_path,
                diff_hunk=hunks.get(symbol.file_path, ""),
            )
            inputs.append(ClassificationInput(adr=adr, symbol=impacted, diff_hunk=""))
            pairs_used += 1

    classifications = classifier.classify(inputs)

    return ReviewResult(
        findings=[r.finding for r in classifications],
        files_scanned=len(impact.files),
        symbols_analyzed=len(impact.symbols),
        adrs_considered=len(active),
    )
