from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel

from decisiondrift import __version__


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def numeric(self) -> float:
        return {"high": 0.9, "medium": 0.6, "low": 0.3}[self.value]


class DecisionRecord(BaseModel):
    id: str
    title: str
    status: Literal["proposed", "accepted", "rejected", "deprecated", "superseded"]
    severity: Literal["critical", "high", "medium", "low"]
    type: str | None = None
    source: Literal["manual", "bootstrap", "ingest"] = "manual"
    superseded_by: str | None = None
    rejected_reason: str | None = None
    rationale: str = ""
    prohibitions: list[str] = []
    exceptions: str | None = None
    alternatives_rejected: list[str] = []
    related_links: list[str] = []
    keywords: list[str] = []
    evidence: list[str] = []
    date: str | None = None
    confidence: ConfidenceLevel | None = None
    owner: str | None = None
    review_after: str | None = None
    expires_after: str | None = None
    depends_on: str | None = None
    embedding: list[float] | None = None


class ImpactedSymbol(BaseModel):
    name: str
    kind: Literal["function", "method", "class"]
    file: str
    diff_hunk: str
    possible_callers: list[str] = []
    covering_tests: list[str] = []


Classification = Literal["violates", "likely_violates", "ambiguous", "not_applicable", "needs_human_review"]
EvidenceStrength = Literal["high", "medium", "low"]


class Finding(BaseModel):
    adr_id: str
    adr_title: str
    severity: Literal["critical", "high", "medium", "low"]
    confidence: float = 0.0
    evidence_strength: EvidenceStrength
    symbol_name: str
    file_path: str
    classification: Classification
    reasoning: str
    suggested_action: str
    retry_count: int = 0


class ReviewResult(BaseModel):
    findings: list[Finding] = []
    rule_findings: list[dict] = []
    files_scanned: int = 0
    symbols_analyzed: int = 0
    adrs_considered: int = 0
    rules_evaluated: int = 0
    llm_available: bool = True


ENFORCEMENT_ACTIONS = {
    "violates": "block",
    "likely_violates": "require_approval",
    "ambiguous": "warn",
    "not_applicable": "allow",
    "needs_human_review": "warn",
}


class ReportEnvelope(BaseModel):
    """Unified output envelope for all CLI commands.

    Every command (enforce, audit, bootstrap, init) emits this same top-level
    structure when --format json or --format sarif is used.
    """
    schema_version: int = 1
    command: str
    tool_version: str = __version__
    timestamp: str = ""
    duration_ms: int = 0
    summary: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()


ADR_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "status", "severity"],
    "properties": {
        "id": {"type": "string", "pattern": r"^ADR-\d{4}$"},
        "title": {"type": "string"},
        "status": {"enum": ["proposed", "accepted", "rejected", "deprecated", "superseded"]},
        "severity": {"enum": ["critical", "high", "medium", "low"]},
        "type": {"type": "string"},
        "source": {"enum": ["manual", "bootstrap", "ingest"]},
        "superseded_by": {"type": ["string", "null"]},
        "rejected_reason": {"type": ["string", "null"]},
        "exceptions": {"type": ["string", "null"]},
        "alternatives_rejected": {
            "type": "array",
            "items": {"type": "string"},
        },
        "related_links": {
            "type": "array",
            "items": {"type": "string"},
        },
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
        },
        "prohibitions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
        "date": {"type": ["string", "null"]},
        "confidence": {"enum": ["high", "medium", "low"]},
        "owner": {"type": "string"},
        "review_after": {"type": "string"},
        "expires_after": {"type": "string"},
        "depends_on": {"type": "string"},
    },
}
