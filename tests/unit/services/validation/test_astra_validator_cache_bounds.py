"""Tests voor DEF-514: begrensde LRU-validatiecache in ASTRAValidator.

Raakt uitsluitend de cache-datastructuur; validatielogica blijft ongemoeid.
"""

from __future__ import annotations

from collections import OrderedDict

import pytest

from services.validation.astra_validator import ASTRAValidator

pytestmark = [pytest.mark.unit]


class TestValidationCacheBounds:
    def test_cache_is_bounded_ordered_structure(self):
        validator = ASTRAValidator()
        assert isinstance(validator.validation_cache, OrderedDict)
        assert ASTRAValidator.MAX_VALIDATION_CACHE_ENTRIES == 500

    def test_set_beyond_max_evicts_oldest(self):
        validator = ASTRAValidator()
        validator.MAX_VALIDATION_CACHE_ENTRIES = 3  # instance-override voor test

        for i in range(4):
            validator._cache_set(f"key{i}", f"value{i}")

        assert len(validator.validation_cache) == 3
        assert validator._cache_get("key0") is None  # oudste geëvict
        assert validator._cache_get("key3") == "value3"

    def test_get_refreshes_lru_recency(self):
        validator = ASTRAValidator()
        validator.MAX_VALIDATION_CACHE_ENTRIES = 3

        for i in range(3):
            validator._cache_set(f"key{i}", f"value{i}")

        validator._cache_get("key0")  # touch: key1 wordt LRU
        validator._cache_set("key3", "value3")

        assert validator._cache_get("key0") == "value0"
        assert validator._cache_get("key1") is None

    def test_set_existing_key_updates_without_eviction(self):
        validator = ASTRAValidator()
        validator.MAX_VALIDATION_CACHE_ENTRIES = 2
        validator._cache_set("a", 1)
        validator._cache_set("b", 2)

        validator._cache_set("a", 99)  # update, geen groei

        assert len(validator.validation_cache) == 2
        assert validator._cache_get("a") == 99
        assert validator._cache_get("b") == 2

    def test_full_default_bound_holds_at_500(self):
        validator = ASTRAValidator()
        for i in range(600):
            validator._cache_set(f"key{i}", i)
        assert len(validator.validation_cache) == 500
        assert validator._cache_get("key99") is None
        assert validator._cache_get("key100") == 100

    def test_validation_logic_untouched(self):
        """Smoke: validate_with_warnings gedraagt zich als voorheen."""
        validator = ASTRAValidator()
        result = validator.validate_with_warnings(
            {"organisatorisch": ["OM"], "wettelijk": [], "juridisch": []}
        )
        assert result.is_valid is True
        assert result.compliance_score == 1.0
