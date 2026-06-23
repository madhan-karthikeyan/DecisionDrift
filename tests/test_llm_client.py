from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from decisiondrift.llm.client import LLMClient, LLMResponseError


class TestLLMClientInit:
    def test_available_with_api_key(self):
        client = LLMClient(api_key="sk-test")
        assert client.available()

    def test_not_available_without_api_key(self):
        client = LLMClient(api_key=None)
        assert not client.available()

    def test_available_from_env(self, monkeypatch):
        monkeypatch.setenv("DECISIONDRIFT_LLM_API_KEY", "sk-env")
        client = LLMClient()
        assert client.available()

    def test_not_available_from_env(self, monkeypatch):
        monkeypatch.delenv("DECISIONDRIFT_LLM_API_KEY", raising=False)
        client = LLMClient()
        assert not client.available()

    def test_default_model(self):
        client = LLMClient(api_key="sk-test")
        assert client.model == "gpt-4o"

    def test_custom_model(self):
        client = LLMClient(model="gpt-4o-mini", api_key="sk-test")
        assert client.model == "gpt-4o-mini"


class TestLLMClientComplete:
    def test_complete_raises_without_key(self):
        client = LLMClient(api_key=None)
        with patch.object(client, "_call") as mock_call:
            mock_call.side_effect = LLMResponseError("No API key configured")
            with pytest.raises(LLMResponseError):
                client.complete("test prompt")

    def test_complete_returns_text(self, monkeypatch):
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "hello world"

        with patch.object(client, "_call", return_value=mock_response):
            result = client.complete("test prompt")
            assert result == "hello world"

    def test_complete_empty_response_raises(self, monkeypatch):
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.choices[0].message.content = None

        with patch.object(client, "_call", return_value=mock_response):
            with pytest.raises(LLMResponseError, match="Empty response"):
                client.complete("test prompt")


class TestLLMClientCompleteJSON:
    def test_complete_json_returns_dict(self, monkeypatch):
        client = LLMClient(api_key="sk-test")
        expected = {"adrs": [{"title": "Use FastAPI"}]}
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(expected)

        with patch.object(client, "_call", return_value=mock_response):
            result = client.complete_json("test prompt")
            assert result == expected

    def test_complete_json_invalid_json_raises(self, monkeypatch):
        client = LLMClient(api_key="sk-test")
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "not json"

        with patch.object(client, "_call", return_value=mock_response):
            with pytest.raises(LLMResponseError, match="Invalid JSON"):
                client.complete_json("test prompt")
