from __future__ import annotations

from pydantic import BaseModel

from decisiondrift.models.schema import DecisionRecord, Finding, ImpactedSymbol


class ClassificationInput(BaseModel):
    adr: DecisionRecord
    symbol: ImpactedSymbol
    diff_hunk: str


class ClassificationResult(BaseModel):
    finding: Finding

    @property
    def adr_id(self) -> str:
        return self.finding.adr_id

    @property
    def classification(self) -> str:
        return self.finding.classification
