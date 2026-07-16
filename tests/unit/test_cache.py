from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from decisiondrift.bootstrap.cache import (
    BootstrapCache,
    CacheProvenance,
    CachedTechnologyProfile,
    is_stale,
    load_project_cache,
    save_project_cache,
)


class TestCacheRoundTrip:
    def test_save_and_load(self, tmp_path: Path):
        cache = BootstrapCache(schema_version=1)
        entry = CachedTechnologyProfile(
            technology="TestTech",
            ecosystem="Python",
            category="framework",
            decision_type="technology_choice",
            aliases=["test"],
            prohibitions=["other"],
            rationale="test rationale",
            confidence=0.9,
            provenance=CacheProvenance(
                provider="test",
                model="test-model",
                generated_at="2026-07-16T12:00:00",
            ),
            last_validated="2026-07-16",
        )
        cache.technology_cache["test_tech"] = entry
        save_project_cache(tmp_path, cache)

        loaded = load_project_cache(tmp_path)
        assert "test_tech" in loaded.technology_cache
        loaded_entry = loaded.technology_cache["test_tech"]
        assert loaded_entry.technology == "TestTech"
        assert loaded_entry.category == "framework"
        assert loaded_entry.confidence == 0.9

    def test_empty_cache(self, tmp_path: Path):
        cache = load_project_cache(tmp_path / "nonexistent")
        assert len(cache.technology_cache) == 0
        assert cache.schema_version == 1

    def test_stale_entry(self):
        entry = CachedTechnologyProfile(
            technology="OldTech",
            ecosystem="",
            category="framework",
            decision_type="technology_choice",
            aliases=[],
            prohibitions=[],
            rationale="",
            confidence=0.5,
            provenance=CacheProvenance(
                provider="test",
                model="test",
                generated_at="2020-01-01",
            ),
            last_validated="2020-01-01",
            ttl_days=1,
        )
        assert is_stale(entry)

    def test_fresh_entry(self):
        entry = CachedTechnologyProfile(
            technology="FreshTech",
            ecosystem="",
            category="framework",
            decision_type="technology_choice",
            aliases=[],
            prohibitions=[],
            rationale="",
            confidence=0.5,
            provenance=CacheProvenance(
                provider="test",
                model="test",
                generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
            last_validated=datetime.date.today().isoformat(),
            ttl_days=365,
        )
        assert not is_stale(entry)

    def test_no_last_validated_is_stale(self):
        entry = CachedTechnologyProfile(
            technology="NoDate",
            ecosystem="",
            category="framework",
            decision_type="technology_choice",
            aliases=[],
            prohibitions=[],
            rationale="",
            confidence=0.5,
            provenance=CacheProvenance(
                provider="test",
                model="test",
                generated_at="",
            ),
            last_validated="",
        )
        assert is_stale(entry)
