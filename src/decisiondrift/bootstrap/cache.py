from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

CACHE_DIR = ".decisiondrift"
CACHE_FILENAME = "cache.yaml"
GLOBAL_CONFIG_DIR = Path.home() / ".config" / "decisiondrift"
GLOBAL_CACHE_PATH = GLOBAL_CONFIG_DIR / CACHE_FILENAME

DEFAULT_TTL_DAYS = 365


@dataclass
class CacheProvenance:
    provider: str
    model: str
    generated_at: str


@dataclass
class CachedTechnologyProfile:
    technology: str
    ecosystem: str
    category: str
    decision_type: str
    aliases: list[str]
    prohibitions: list[str]
    rationale: str
    confidence: float
    provenance: CacheProvenance
    last_validated: str = ""
    ttl_days: int = DEFAULT_TTL_DAYS


@dataclass
class BootstrapCache:
    schema_version: int = 1
    technology_cache: dict[str, CachedTechnologyProfile] = field(default_factory=dict)


def load_project_cache(repo_path: Path) -> BootstrapCache:
    cache_path = repo_path / CACHE_DIR / CACHE_FILENAME
    if cache_path.exists():
        return _load_cache_file(cache_path)
    return BootstrapCache()


def load_global_cache() -> BootstrapCache:
    if GLOBAL_CACHE_PATH.exists():
        return _load_cache_file(GLOBAL_CACHE_PATH)
    return BootstrapCache()


def _load_cache_file(path: Path) -> BootstrapCache:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    cache = BootstrapCache(schema_version=raw.get("schema_version", 1))
    for key, entry in raw.get("technology_cache", {}).items():
        prov = entry.get("provenance", {})
        cache.technology_cache[key] = CachedTechnologyProfile(
            technology=entry.get("technology", key),
            ecosystem=entry.get("ecosystem", ""),
            category=entry.get("category", "unknown"),
            decision_type=entry.get("decision_type", ""),
            aliases=entry.get("aliases", []),
            prohibitions=entry.get("prohibitions", []),
            rationale=entry.get("rationale", ""),
            confidence=entry.get("confidence", 0.5),
            provenance=CacheProvenance(
                provider=prov.get("provider", "unknown"),
                model=prov.get("model", "unknown"),
                generated_at=prov.get("generated_at", ""),
            ),
            last_validated=entry.get("last_validated", ""),
            ttl_days=entry.get("ttl_days", DEFAULT_TTL_DAYS),
        )
    return cache


def _cache_to_dict(cache: BootstrapCache) -> dict[str, Any]:
    tech_cache = {}
    for key, entry in cache.technology_cache.items():
        tech_cache[key] = {
            "technology": entry.technology,
            "ecosystem": entry.ecosystem,
            "category": entry.category,
            "decision_type": entry.decision_type,
            "aliases": entry.aliases,
            "prohibitions": entry.prohibitions,
            "rationale": entry.rationale,
            "confidence": entry.confidence,
            "provenance": asdict(entry.provenance),
            "last_validated": entry.last_validated,
            "ttl_days": entry.ttl_days,
        }
    return {
        "schema_version": cache.schema_version,
        "technology_cache": tech_cache,
    }


def save_project_cache(repo_path: Path, cache: BootstrapCache) -> None:
    cache_dir = repo_path / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILENAME
    with open(cache_path, "w") as f:
        yaml.dump(_cache_to_dict(cache), f, default_flow_style=False)


def save_global_cache(cache: BootstrapCache) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(GLOBAL_CACHE_PATH, "w") as f:
        yaml.dump(_cache_to_dict(cache), f, default_flow_style=False)


def cache_entry(entry: CachedTechnologyProfile) -> dict[str, Any]:
    today = datetime.date.today().isoformat()
    entry.last_validated = today
    return {
        "technology": entry.technology,
        "ecosystem": entry.ecosystem,
        "category": entry.category,
        "decision_type": entry.decision_type,
        "aliases": entry.aliases,
        "prohibitions": entry.prohibitions,
        "rationale": entry.rationale,
        "confidence": entry.confidence,
        "provenance": asdict(entry.provenance),
        "last_validated": today,
        "ttl_days": entry.ttl_days,
    }


def is_stale(entry: CachedTechnologyProfile) -> bool:
    if not entry.last_validated:
        return True
    try:
        validated = datetime.date.fromisoformat(entry.last_validated)
        delta = datetime.date.today() - validated
        return delta.days > entry.ttl_days
    except (ValueError, TypeError):
        return True
