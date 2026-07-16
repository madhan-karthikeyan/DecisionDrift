from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from decisiondrift.bootstrap.cache import (
    BootstrapCache,
    CachedTechnologyProfile,
    CacheProvenance,
    is_stale,
    load_global_cache,
    load_project_cache,
    save_global_cache,
    save_project_cache,
)
from decisiondrift.bootstrap.registry import (
    TechnologyRegistry,
    governance_template_for_tech,
    resolve_technology,
)
from decisiondrift.bootstrap.v3 import Evidence
from decisiondrift.llm.client import LLMClient, LLMResponseError

TECH_RECOGNITION_PROMPT = """Analyze this technology usage in a repository.

Dependency declarations:
{dep_evidence}

Import/usages:
{import_evidence}

File/directory evidence:
{file_evidence}

Context:
  Repository role: {repo_role}
  Other detected technologies: {nearby_techs}

Return ONLY valid JSON matching this schema:
{{
  "technology": "<canonical technology name>",
  "ecosystem": "<programming language or platform>",
  "category": "<framework|language|database|orm|cache|queue|frontend|auth|monitoring|testing|ci|container|migration|runtime|tooling|css>",
  "decision_type": "<technology_choice|runtime_policy|data_access|deployment_policy|testing_policy|boundary_policy>",
  "aliases": ["<alternative names>"],
  "prohibitions": ["<competing technologies to block>"],
  "rationale": "<why this technology is used in this repo>",
  "confidence": <0.0-1.0>
}}"""

TEMPLATE_GENERATION_PROMPT = """Generate an ADR (Architecture Decision Record) template for this technology.

Technology: {technology}
Ecosystem: {ecosystem}
Category: {category}
Evidence: {evidence_summary}

Return ONLY valid JSON matching this schema:
{{
  "decision_type": "<technology_choice|runtime_policy|data_access|deployment_policy|testing_policy|boundary_policy>",
  "title": "<ADR title>",
  "prohibitions": ["<competing technologies to block>"],
  "rationale": "<why this decision was made>",
  "confidence": <0.0-1.0>
}}"""


@dataclass
class RecognitionResult:
    technology: str
    ecosystem: str
    category: str
    decision_type: str
    aliases: list[str]
    prohibitions: list[str]
    rationale: str
    confidence: float
    llm_generated: bool = False


class KnowledgeProvider:
    """Abstracts LLM-based technology recognition and ADR template generation.

    Wraps LLMClient and provides deterministic fallback via the registry.
    Respects cache layers: project cache > global cache > bundled registry.
    """

    def __init__(
        self,
        registry: TechnologyRegistry,
        llm_client: LLMClient | None = None,
        repo_path: str | None = None,
        min_llm_confidence: float = 0.6,
        cache_templates: bool = False,
    ):
        self.registry = registry
        self.llm = llm_client
        self.repo_path = repo_path
        self.min_llm_confidence = min_llm_confidence
        self.cache_templates = cache_templates

        self.project_cache: BootstrapCache | None = None
        self.global_cache: BootstrapCache | None = None
        if repo_path:
            self.project_cache = load_project_cache(repo_path)
            self.global_cache = load_global_cache()

    def recognize_technology(
        self,
        dep_value: str,
        evidence: list[Evidence] | None = None,
        repo_role: str = "unknown",
        nearby_techs: list[str] | None = None,
    ) -> RecognitionResult | None:
        dep_lower = dep_value.lower()

        result = self._registry_lookup(dep_lower)
        if result:
            return result

        result = self._cache_lookup(dep_lower)
        if result:
            return result

        if self.llm and self.llm.available():
            result = self._llm_recognize(dep_value, evidence, repo_role, nearby_techs or [])
            if result and result.confidence >= self.min_llm_confidence:
                self._write_cache(result.technology, dep_lower, result, is_template=False)
                return result
            if result:
                return RecognitionResult(
                    technology=result.technology,
                    ecosystem=result.ecosystem,
                    category=result.category,
                    decision_type=result.decision_type,
                    aliases=result.aliases,
                    prohibitions=result.prohibitions,
                    rationale=result.rationale,
                    confidence=result.confidence,
                    llm_generated=True,
                )

        return None

    def generate_template(
        self,
        tech_name: str,
        ecosystem: str = "",
        category: str = "",
        evidence_summary: str = "",
    ) -> RecognitionResult | None:
        cached = self._template_cache_lookup(tech_name)
        if cached:
            return cached

        if self.llm and self.llm.available():
            result = self._llm_generate_template(tech_name, ecosystem, category, evidence_summary)
            if result and result.confidence >= self.min_llm_confidence:
                if self.cache_templates:
                    self._write_cache(tech_name, tech_name.lower(), result, is_template=True)
                return result

        return None

    def _registry_lookup(self, dep_lower: str) -> RecognitionResult | None:
        resolved = resolve_technology(self.registry, dep_lower)
        if not resolved:
            return None
        name, category = resolved
        template = governance_template_for_tech(self.registry, name)
        return RecognitionResult(
            technology=name,
            ecosystem=self.registry.technologies.get(name, name).ecosystem if isinstance(self.registry.technologies.get(name), object) else "",
            category=category,
            decision_type=template.decision_type if template else "technology_choice",
            aliases=[],
            prohibitions=template.prohibitions if template else [],
            rationale=template.rationale if template else "",
            confidence=self.registry.technologies[name].confidence if name in self.registry.technologies else 0.8,
            llm_generated=False,
        )

    def _cache_lookup(self, dep_lower: str) -> RecognitionResult | None:
        for cache in (self.project_cache, self.global_cache):
            if cache and dep_lower in cache.technology_cache:
                entry = cache.technology_cache[dep_lower]
                if is_stale(entry):
                    continue
                return RecognitionResult(
                    technology=entry.technology,
                    ecosystem=entry.ecosystem,
                    category=entry.category,
                    decision_type=entry.decision_type,
                    aliases=entry.aliases,
                    prohibitions=entry.prohibitions,
                    rationale=entry.rationale,
                    confidence=entry.confidence,
                    llm_generated=True,
                )
        return None

    def _template_cache_lookup(self, tech_name: str) -> RecognitionResult | None:
        key = f"__template__{tech_name}"
        for cache in (self.project_cache, self.global_cache):
            if cache and key in cache.technology_cache:
                entry = cache.technology_cache[key]
                if is_stale(entry):
                    continue
                return RecognitionResult(
                    technology=entry.technology,
                    ecosystem=entry.ecosystem,
                    category=entry.category,
                    decision_type=entry.decision_type,
                    aliases=entry.aliases,
                    prohibitions=entry.prohibitions,
                    rationale=entry.rationale,
                    confidence=entry.confidence,
                    llm_generated=True,
                )
        return None

    def _build_prompt(self, dep_value: str, evidence: list[Evidence] | None, repo_role: str, nearby_techs: list[str]) -> str:
        dep_lines = f"- {dep_value}"
        imp_lines = ""
        file_lines = ""

        if evidence:
            dep_evs = [e for e in evidence if e.kind == "dependency" and e.value == dep_value]
            imp_evs = [e for e in evidence if e.kind == "import"]
            file_evs = [e for e in evidence if e.kind in {"file", "directory"}]

            if dep_evs:
                dep_lines = "\n".join(f"- {e.value} ({e.source_path})" for e in dep_evs[:5])
            if imp_evs:
                imp_lines = "\n".join(f"- {e.value} ({e.source_path})" for e in imp_evs[:5])
            if file_evs:
                file_lines = "\n".join(f"- {e.value} ({e.source_path})" for e in file_evs[:5])

        return TECH_RECOGNITION_PROMPT.format(
            dep_evidence=dep_lines or f"- {dep_value}",
            import_evidence=imp_lines or "(none)",
            file_evidence=file_lines or "(none)",
            repo_role=repo_role or "unknown",
            nearby_techs=", ".join(nearby_techs[:8]) or "none detected",
        )

    def _llm_recognize(
        self,
        dep_value: str,
        evidence: list[Evidence] | None,
        repo_role: str,
        nearby_techs: list[str],
    ) -> RecognitionResult | None:
        if not self.llm:
            return None
        prompt = self._build_prompt(dep_value, evidence, repo_role, nearby_techs)
        return self._call_llm_with_retry(prompt)

    def _llm_generate_template(
        self,
        tech_name: str,
        ecosystem: str,
        category: str,
        evidence_summary: str,
    ) -> RecognitionResult | None:
        if not self.llm:
            return None
        prompt = TEMPLATE_GENERATION_PROMPT.format(
            technology=tech_name,
            ecosystem=ecosystem,
            category=category,
            evidence_summary=evidence_summary or "(no evidence summary)",
        )
        return self._call_llm_with_retry(prompt)

    def _call_llm_with_retry(self, prompt: str) -> RecognitionResult | None:
        if not self.llm:
            return None
        for attempt in range(2):
            try:
                raw = self.llm.complete_json(
                    prompt,
                    system_prompt="You are an expert technology analyst. Respond with valid JSON only, no markdown, no explanation.",
                )
                result = self._parse_llm_response(raw)
                if result:
                    return result
            except LLMResponseError:
                if attempt == 0:
                    continue
        return None

    def _parse_llm_response(self, raw: dict[str, Any]) -> RecognitionResult | None:
        try:
            technology = raw.get("technology", "")
            if not technology:
                return None
            category = raw.get("category", "tooling")
            valid_categories = {
                "framework", "language", "database", "orm", "cache", "queue",
                "frontend", "auth", "monitoring", "testing", "ci", "container",
                "migration", "runtime", "tooling", "css",
            }
            if category not in valid_categories:
                category = "tooling"

            decision_type = raw.get("decision_type", "technology_choice")
            valid_types = {
                "technology_choice", "runtime_policy", "data_access",
                "deployment_policy", "testing_policy", "boundary_policy",
            }
            if decision_type not in valid_types:
                decision_type = "technology_choice"

            confidence = float(raw.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))

            return RecognitionResult(
                technology=technology,
                ecosystem=raw.get("ecosystem", ""),
                category=category,
                decision_type=decision_type,
                aliases=raw.get("aliases", []),
                prohibitions=raw.get("prohibitions", []),
                rationale=raw.get("rationale", ""),
                confidence=confidence,
                llm_generated=True,
            )
        except (ValueError, TypeError, AttributeError):
            return None

    def _write_cache(self, tech_name: str, dep_key: str, result: RecognitionResult, is_template: bool = False) -> None:
        key = f"__template__{tech_name}" if is_template else dep_key
        prov = CacheProvenance(
            provider=self.llm.api_key.split("_")[0] if self.llm and self.llm.api_key else "unknown",
            model=self.llm.model if self.llm else "unknown",
            generated_at=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        entry = CachedTechnologyProfile(
            technology=result.technology,
            ecosystem=result.ecosystem,
            category=result.category,
            decision_type=result.decision_type,
            aliases=result.aliases,
            prohibitions=result.prohibitions,
            rationale=result.rationale,
            confidence=result.confidence,
            provenance=prov,
            last_validated=datetime.date.today().isoformat(),
        )
        if self.project_cache is not None:
            self.project_cache.technology_cache[key] = entry
            from pathlib import Path
            if self.repo_path:
                save_project_cache(Path(self.repo_path), self.project_cache)
        if self.global_cache is not None:
            self.global_cache.technology_cache[key] = entry
            save_global_cache(self.global_cache)
