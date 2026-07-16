from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from decisiondrift.bootstrap.knowledge_provider import KnowledgeProvider, RecognitionResult
from decisiondrift.bootstrap.registry import load_registry


@pytest.fixture
def registry():
    return load_registry()


class TestKnowledgeProviderNoLLM:
    def test_registry_lookup_succeeds(self, registry):
        kp = KnowledgeProvider(registry=registry)
        result = kp.recognize_technology("fastapi")
        assert result is not None
        assert result.technology == "FastAPI"
        assert not result.llm_generated

    def test_unknown_tech_returns_none(self, registry):
        kp = KnowledgeProvider(registry=registry)
        result = kp.recognize_technology("unknown_random_package")
        assert result is None

    def test_governance_template_lookup(self, registry):
        kp = KnowledgeProvider(registry=registry)
        result = kp._registry_lookup("flask")
        assert result is not None
        assert result.technology == "Flask"
        assert "fastapi" in result.prohibitions

    def test_cache_lookup_empty_without_cache(self, registry):
        kp = KnowledgeProvider(registry=registry)
        assert kp._cache_lookup("anything") is None


class TestKnowledgeProviderWithLLM:
    def test_llm_recognize_called_for_unknown(self, registry):
        mock_llm = MagicMock()
        mock_llm.available.return_value = True
        mock_llm.complete_json.return_value = {
            "technology": "SomeUnknownTech",
            "ecosystem": "Python",
            "category": "framework",
            "decision_type": "technology_choice",
            "aliases": [],
            "prohibitions": ["other"],
            "rationale": "Detected in use.",
            "confidence": 0.9,
        }
        kp = KnowledgeProvider(registry=registry, llm_client=mock_llm)
        result = kp.recognize_technology("some_unknown_lib")
        assert result is not None
        assert result.technology == "SomeUnknownTech"
        assert result.llm_generated
        assert result.confidence == 0.9

    def test_llm_low_confidence_returns_flagged(self, registry):
        mock_llm = MagicMock()
        mock_llm.available.return_value = True
        mock_llm.complete_json.return_value = {
            "technology": "LowConfTech",
            "ecosystem": "",
            "category": "tooling",
            "decision_type": "technology_choice",
            "aliases": [],
            "prohibitions": [],
            "rationale": "",
            "confidence": 0.3,
        }
        kp = KnowledgeProvider(registry=registry, llm_client=mock_llm, min_llm_confidence=0.6)
        result = kp.recognize_technology("low_conf_lib")
        assert result is not None
        assert result.confidence == 0.3

    def test_llm_invalid_json_returns_none(self, registry):
        mock_llm = MagicMock()
        mock_llm.available.return_value = True
        from decisiondrift.llm.client import LLMResponseError
        mock_llm.complete_json.side_effect = LLMResponseError("Invalid JSON")
        kp = KnowledgeProvider(registry=registry, llm_client=mock_llm)
        result = kp.recognize_technology("failing_lib")
        assert result is None

    def test_llm_not_called_when_not_available(self, registry):
        mock_llm = MagicMock()
        mock_llm.available.return_value = False
        kp = KnowledgeProvider(registry=registry, llm_client=mock_llm)
        result = kp.recognize_technology("some_lib")
        assert result is None
        mock_llm.complete_json.assert_not_called()


class TestKnowledgeProviderPromptBuilding:
    def test_build_prompt_includes_evidence(self, registry):
        from decisiondrift.bootstrap.v3 import Evidence, EvidenceRole, EvidenceLevel
        kp = KnowledgeProvider(registry=registry)
        evidence = [
            Evidence(kind="dependency", value="cool_pkg", source_path="requirements.txt",
                     role=EvidenceRole.RUNTIME, level=EvidenceLevel.MODERATE),
            Evidence(kind="import", value="cool_pkg", source_path="app/main.py",
                     role=EvidenceRole.RUNTIME, level=EvidenceLevel.STRONG),
        ]
        prompt = kp._build_prompt("cool_pkg", evidence, "api_service", ["FastAPI"])
        assert "cool_pkg" in prompt
        assert "api_service" in prompt
        assert "FastAPI" in prompt
        assert "requirements.txt" in prompt
