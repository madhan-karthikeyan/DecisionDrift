from __future__ import annotations

import json
import os
from typing import Any

from decisiondrift.classification.models import ClassificationInput, ClassificationResult
from decisiondrift.classification.prompts import (
    CLASSIFICATION_SCHEMA,
    SYSTEM_PROMPT,
    build_user_prompt,
)
from decisiondrift.models.schema import Classification, EvidenceStrength, Finding


class Classifier:
    def __init__(self, model: str = "gpt-4o", api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("DECISIONDRIFT_LLM_API_KEY")
        self.base_url = base_url

    def classify(self, inputs: list[ClassificationInput]) -> list[ClassificationResult]:
        if not self.api_key:
            return self._fallback(inputs)

        return self._classify_with_llm(inputs)

    def _fallback(self, inputs: list[ClassificationInput]) -> list[ClassificationResult]:
        return [
            ClassificationResult(
                finding=self._build_finding(
                    adr=inp.adr,
                    symbol=inp.symbol,
                    classification="needs_human_review",
                    evidence_strength="low",
                    reasoning="No LLM API key configured. Manual review required.",
                    suggested_action="Set DECISIONDRIFT_LLM_API_KEY or review manually.",
                )
            )
            for inp in inputs
        ]

    def _classify_with_llm(self, inputs: list[ClassificationInput]) -> list[ClassificationResult]:
        try:
            from openai import OpenAI
        except ImportError:
            print("Warning: openai package not installed, falling back to needs_human_review")
            return self._fallback(inputs)

        kwargs = {"api_key": self.api_key, "timeout": 120}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        client = OpenAI(**kwargs)
        results: list[ClassificationResult] = []

        for inp in inputs:
            result = self._classify_one(client, inp)
            results.append(result)

        return results

    def _classify_one(self, client: Any, inp: ClassificationInput) -> ClassificationResult:
        prompt = build_user_prompt(
            adr_title=inp.adr.title,
            adr_rationale=inp.adr.rationale,
            adr_exceptions=inp.adr.exceptions,
            symbol_name=inp.symbol.name,
            symbol_type=inp.symbol.kind,
            file_path=inp.symbol.file,
            diff_hunk=inp.symbol.diff_hunk,
        )

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            data = json.loads(content)
        except Exception as e:
            print(f"Warning: LLM classification failed: {e}")
            return ClassificationResult(
                finding=self._build_finding(
                    adr=inp.adr,
                    symbol=inp.symbol,
                    classification="needs_human_review",
                    evidence_strength="low",
                    reasoning=f"LLM call failed: {e}",
                    suggested_action="Review manually or retry.",
                )
            )

        classification = data.get("classification", "needs_human_review")
        evidence_strength = data.get("evidence_strength", "low")

        if classification not in ("violates", "likely_violates", "ambiguous", "not_applicable", "needs_human_review"):
            classification = "needs_human_review"
        if evidence_strength not in ("high", "medium", "low"):
            evidence_strength = "low"

        return ClassificationResult(
            finding=self._build_finding(
                adr=inp.adr,
                symbol=inp.symbol,
                classification=classification,
                evidence_strength=evidence_strength,
                reasoning=data.get("reasoning", ""),
                suggested_action=data.get("suggested_action", ""),
            )
        )

    def _build_finding(
        self,
        adr: ClassificationInput.adr,  # type: ignore
        symbol: ClassificationInput.symbol,  # type: ignore
        classification: str,
        evidence_strength: str,
        reasoning: str,
        suggested_action: str,
    ) -> Finding:
        return Finding(
            adr_id=adr.id,
            adr_title=adr.title,
            severity=adr.severity,
            confidence={"high": 0.9, "medium": 0.6, "low": 0.3}.get(evidence_strength, 0.0),
            evidence_strength=evidence_strength,
            symbol_name=symbol.name,
            file_path=symbol.file,
            classification=classification,
            reasoning=reasoning,
            suggested_action=suggested_action,
        )
