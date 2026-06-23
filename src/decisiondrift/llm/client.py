from __future__ import annotations

import json
import os
from typing import Any


class LLMResponseError(Exception):
    """Raised when the LLM returns an empty response, invalid JSON, or a transport error."""


class LLMClient:
    """Shared LLM client for all DecisionDrift components.

    Wraps the OpenAI-compatible API (works with OpenAI, Groq, Ollama, etc.).
    Both review classification and bootstrap synthesis use this client.

    Usage:
        client = LLMClient(api_key="...", model="gpt-4o")
        if client.available():
            result = client.complete_json(prompt)
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("DECISIONDRIFT_LLM_API_KEY")
        self.base_url = base_url

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        """Send a prompt and return the raw text response."""
        result = self._call(prompt, system_prompt=system_prompt, **kwargs)
        content = result.choices[0].message.content
        if not content:
            raise LLMResponseError("Empty response from LLM")
        return content

    def complete_json(self, prompt: str, system_prompt: str | None = None, **kwargs) -> dict[str, Any]:
        """Send a prompt and return parsed JSON.

        Raises LLMResponseError if the response is empty or not valid JSON.
        """
        result = self._call(
            prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
            **kwargs,
        )
        content = result.choices[0].message.content
        if not content:
            raise LLMResponseError("Empty response from LLM")
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMResponseError(f"Invalid JSON response: {e}") from e

    def _call(self, prompt: str, system_prompt: str | None = None, **kwargs) -> Any:
        """Internal: make the API call."""
        if not self.api_key:
            raise LLMResponseError(
                "No API key configured. Set DECISIONDRIFT_LLM_API_KEY or pass api_key."
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise LLMResponseError(
                "openai package not installed. Run: pip install openai"
            )

        client_kwargs: dict[str, Any] = {"api_key": self.api_key, "timeout": 120}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        client = OpenAI(**client_kwargs)
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        create_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
        }
        if "response_format" in kwargs:
            create_kwargs["response_format"] = kwargs["response_format"]

        return client.chat.completions.create(**create_kwargs)
