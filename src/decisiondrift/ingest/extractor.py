from __future__ import annotations

from typing import Any

from decisiondrift.llm.client import LLMClient

EXTRACT_PROMPT = """
You are an expert technical architect. Read the following text snippet (which may be from meeting notes, RFCs, or chat) and extract any explicit architectural, technical, or process DECISIONS made.

Do not invent a decision if one is not clearly stated. If there are no decisions, return an empty list.
For each decision found, extract:
- title: A concise 3-5 word title for the decision
- decision: The actual decision rule
- rationale: The context or reason behind the decision
- confidence: "high", "medium", or "low" based on how explicitly stated the decision is

Format your response as JSON:
{
  "decisions": [
    {
      "title": "Use RabbitMQ for Queues",
      "decision": "All queue operations must use RabbitMQ instead of Redis.",
      "rationale": "Redis caused outages in 2023.",
      "confidence": "high"
    }
  ]
}
"""


def extract_candidates(text: str, client: LLMClient) -> list[dict[str, Any]]:
    if not text.strip():
        return []

    response = client.complete_json(text, system_prompt=EXTRACT_PROMPT)
    return response.get("decisions", [])
