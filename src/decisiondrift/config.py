from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from decisiondrift.rules.models import Action, Rule, RuleSet, RuleType


def find_config(start_path: Path | None = None) -> Path | None:
    load_dotenv()
    path = start_path or Path.cwd()
    for candidate in ("decisiondrift.yml", ".decisiondrift.yml"):
        candidate_path = path / candidate
        if candidate_path.exists():
            return candidate_path
    return None


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or find_config()
    config: dict[str, Any] = {}

    if config_path and config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    config.setdefault("llm", {})
    config["llm"].setdefault("api_key", os.environ.get("DECISIONDRIFT_LLM_API_KEY"))
    config["llm"].setdefault("model", os.environ.get("DECISIONDRIFT_LLM_MODEL", "gpt-4o"))
    config["llm"].setdefault("base_url", os.environ.get("DECISIONDRIFT_LLM_BASE_URL", None))
    config.setdefault("adr_dir", "docs/adr")
    config.setdefault("max_retries", 2)
    config.setdefault("max_pairs_per_pr", 15)
    config.setdefault("wall_clock_budget_seconds", 300)
    config.setdefault("similarity_threshold", 0.5)
    config.setdefault("embedding_model", "BAAI/bge-small-en-v1.5")
    config.setdefault("rules", [])

    return config


def load_custom_rules(config: dict[str, Any] | None = None) -> RuleSet:
    if config is None:
        config = load_config()

    raw_rules = config.get("rules", [])
    if not raw_rules:
        return RuleSet(rules=[])

    rules: list[Rule] = []
    for i, raw in enumerate(raw_rules):
        match = raw.get("match", "")
        rule_type = _parse_rule_type(raw.get("type", "dependency"))
        action = _parse_action(raw.get("action", "warn"))
        description = raw.get("description", "")
        source_adr = raw.get("source_adr", f"custom-rule-{i + 1}")

        rules.append(
            Rule(
                id=f"custom-{i + 1}",
                type=rule_type,
                match=match.lower(),
                action=action,
                source_adr=source_adr,
                description=description,
            )
        )

    return RuleSet(rules=rules)


def _parse_rule_type(raw: str) -> RuleType:
    try:
        return RuleType(raw.lower())
    except ValueError:
        return RuleType.DEPENDENCY


def _parse_action(raw: str) -> Action:
    try:
        return Action(raw.lower())
    except ValueError:
        return Action.WARN
