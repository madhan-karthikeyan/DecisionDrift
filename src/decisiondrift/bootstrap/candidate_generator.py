from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from decisiondrift.adr.loader import load_adrs
from decisiondrift.adr.writer import write_adr
from decisiondrift.bootstrap.patterns import PatternMatch
from decisiondrift.models.schema import DecisionRecord


@dataclass
class CandidateADR:
    adr: DecisionRecord
    pattern_name: str
    confidence: str
    evidence: list[str]

    def dry_run_text(self) -> str:
        lines = [
            f"[{self.confidence.upper()}] {self.pattern_name}",
            "",
            "Proposed ADR:",
            f"  {self.adr.title}",
            "",
            "Context:",
            f"  {self.adr.rationale}",
            "",
            "Evidence:",
        ]
        for e in self.evidence:
            lines.append(f"  - {e}")
        lines.append("")
        return "\n".join(lines)


def _jaccard_words(a: str, b: str) -> float:
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _keyword_overlap(
    candidate_title: str,
    candidate_keywords: list[str],
    existing_title: str,
    existing_keywords: list[str],
) -> float:
    title_sim = _jaccard_words(candidate_title, existing_title)

    kw_matches = 0
    for kw in candidate_keywords:
        if kw.lower() in existing_title.lower():
            kw_matches += 1
    for kw in existing_keywords:
        if kw.lower() in candidate_title.lower():
            kw_matches += 1

    kw_set_sim = 0.0
    kw_set_a = set(k.lower() for k in candidate_keywords)
    kw_set_b = set(k.lower() for k in existing_keywords)
    if kw_set_a and kw_set_b:
        kw_set_sim = len(kw_set_a & kw_set_b) / len(kw_set_a | kw_set_b)

    score = 0.6 * title_sim + 0.2 * min(kw_matches / 4, 1.0) + 0.2 * kw_set_sim
    return score


def _is_duplicate(
    candidate_title: str,
    candidate_keywords: list[str],
    existing: list[DecisionRecord],
    threshold: float = 0.5,
) -> tuple[bool, str | None]:
    for record in existing:
        score = _keyword_overlap(
            candidate_title,
            candidate_keywords,
            record.title,
            record.keywords,
        )
        if score >= threshold:
            return True, record.id
    return False, None


def _next_id(adr_dir: str | Path) -> str:
    adr_path = Path(adr_dir)
    max_num = 0
    if adr_path.exists():
        for f in adr_path.glob("ADR-*.md"):
            m = re.match(r"^ADR-(\d{4})\.md$", f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
    return f"ADR-{max_num + 1:04d}"


def generate_candidates(
    matches: list[PatternMatch],
    adr_dir: str | Path,
    min_confidence: str = "low",
) -> list[CandidateADR]:
    adr_path = Path(adr_dir)
    all_existing = load_adrs(adr_path) if adr_path.exists() else []

    confidence_levels = {"low": 0, "medium": 1, "high": 2}
    min_level = confidence_levels.get(min_confidence, 0)

    next_num = -1
    for f in adr_path.glob("ADR-*.md") if adr_path.exists() else []:
        m = re.match(r"^ADR-(\d{4})\.md$", f.name)
        if m:
            num = int(m.group(1))
            if num > next_num:
                next_num = num
    next_num += 1

    candidates: list[CandidateADR] = []

    for match in matches:
        match_level = confidence_levels.get(match.confidence, 0)
        if match_level < min_level:
            continue

        pattern = match.pattern
        title = pattern.name

        is_dup, dup_id = _is_duplicate(title, pattern.template_keywords, all_existing)
        if is_dup:
            print(f"  Skipping {title}: already documented as {dup_id}")
            continue

        adr_id = f"ADR-{next_num:04d}"
        next_num += 1

        adr = DecisionRecord(
            id=adr_id,
            title=title,
            status="proposed",
            severity="medium" if pattern.confidence in ("high", "medium") else "low",
            source="bootstrap",
            rationale=(
                f"## Context\n\n{pattern.template_context}\n\n"
                f"## Decision (candidate)\n\n{pattern.template_rationale}\n\n"
                f"## Confidence\n\n{match.confidence.title()} (structural match), "
                f"but rationale is inferred, not confirmed by the team."
            ),
            keywords=pattern.template_keywords,
            evidence=match.evidence,
        )

        candidates.append(
            CandidateADR(
                adr=adr,
                pattern_name=pattern.name,
                confidence=pattern.confidence,
                evidence=match.evidence,
            )
        )

    return candidates


def apply_candidates(candidates: list[CandidateADR], adr_dir: str | Path) -> int:
    adr_path = Path(adr_dir)
    adr_path.mkdir(parents=True, exist_ok=True)

    written = 0
    for cand in candidates:
        path = adr_path / f"{cand.adr.id}.md"
        metadata = cand.adr.model_dump(exclude={"embedding", "rationale"}, exclude_none=True)
        body = cand.adr.rationale
        write_adr(path, metadata, body)
        written += 1

    return written
