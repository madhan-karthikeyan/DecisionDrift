from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from decisiondrift.models.schema import ConfidenceLevel


class RuleType(StrEnum):
    DEPENDENCY = "dependency"
    IMPORT = "import"
    API = "api"
    PATH = "path"
    CONFIG = "config"


class Action(StrEnum):
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    WARN = "warn"
    INFO = "info"


class Rule(BaseModel):
    id: str
    type: RuleType
    match: str
    action: Action
    source_adr: str
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    description: str = ""


class RuleSet(BaseModel):
    rules: list[Rule] = []

    def by_type(self, rule_type: RuleType) -> list[Rule]:
        return [r for r in self.rules if r.type == rule_type]

    def for_adr(self, adr_id: str) -> list[Rule]:
        return [r for r in self.rules if r.source_adr == adr_id]


class RuleMatch(BaseModel):
    rule: Rule
    matched_value: str
    file_path: str | None = None
    line_number: int | None = None


class EnforcementFinding(BaseModel):
    adr_id: str
    adr_title: str
    rule_id: str
    rule_type: RuleType
    action: Action
    severity: Literal["critical", "high", "medium", "low"]
    match_value: str
    file_path: str | None = None
    description: str = ""


class EnforcementResult(BaseModel):
    findings: list[EnforcementFinding] = []
    files_scanned: int = 0
    dependencies_scanned: int = 0
    imports_scanned: int = 0
    rules_evaluated: int = 0
