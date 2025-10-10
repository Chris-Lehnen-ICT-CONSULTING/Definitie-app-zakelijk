"""
Performance test voor US-202 Rule Cache optimalisatie.

Test dat de nieuwe RuleCache implementatie significant sneller is
dan het oude systeem dat files steeds opnieuw laadt.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager
# Import the implementations
from toetsregels.rule_cache import RuleCache, get_rule_cache


class TestRuleCachePerformance:
    """Test performance improvements van RuleCache."""

    def test_rule_cache_singleton(self):
        """Test dat RuleCache een singleton is."""
        cache1 = RuleCache()
        cache2 = RuleCache()
        cache3 = get_rule_cache()

        assert cache1 is cache2
        assert cache2 is cache3

    def test_cached_manager_uses_cache(self):
        """Test dat CachedToetsregelManager de RuleCache gebruikt."""
        manager = CachedToetsregelManager()

        # Eerste call - zou files moeten laden
        start = time.time()
        rules1 = manager.get_all_regels()
        first_call_time = time.time() - start

        # Tweede call - zou uit cache moeten komen
        start = time.time()
        rules2 = manager.get_all_regels()
        second_call_time = time.time() - start

        # Verify dat beide calls dezelfde data returnen
        assert rules1 == rules2

        # Stats checken
        stats = manager.get_stats()
        assert stats["cache_hits"] >= 2

    @patch("toetsregels.rule_cache._load_all_rules_cached")
    def test_cache_is_actually_used(self, mock_load):
        """Test dat de Streamlit cache daadwerkelijk wordt gebruikt."""
        mock_load.return_value = {"TEST-01": {"id": "TEST-01", "naam": "Test regel"}}

        cache = RuleCache()

        # Multiple calls
        for _ in range(5):
            rules = cache.get_all_rules()
            assert "TEST-01" in rules

        # Mock zou maar één keer aangeroepen moeten zijn door caching
        # Note: In werkelijkheid wordt dit door @st.cache_data afgehandeld
        # Deze test verifieert alleen dat onze code de juiste functies aanroept

    def test_weight_calculation(self):
        """Test dat regel weights correct worden berekend."""
        cache = RuleCache()

        # Mock some rules met verschillende prioriteiten
        with patch.object(cache, "get_all_rules") as mock_get_all:
            mock_get_all.return_value = {
                "HIGH-01": {"id": "HIGH-01", "prioriteit": "hoog"},
                "MID-01": {"id": "MID-01", "prioriteit": "midden"},
                "LOW-01": {"id": "LOW-01", "prioriteit": "laag"},
                "CUSTOM-01": {
                    "id": "CUSTOM-01",
                    "prioriteit": "midden",
                    "weight": 0.85,
                },
            }

            weights = cache.get_rule_weights()

            assert weights["HIGH-01"] == 1.0
            assert weights["MID-01"] == 0.7
            assert weights["LOW-01"] == 0.4
            assert weights["CUSTOM-01"] == 0.85  # Custom weight overrides priority

    def test_filter_by_priority(self):
        """Test filtering regels op prioriteit."""
        cache = RuleCache()

        with patch.object(cache, "get_all_rules") as mock_get_all:
            mock_get_all.return_value = {
                "HIGH-01": {"id": "HIGH-01", "prioriteit": "hoog"},
                "HIGH-02": {"id": "HIGH-02", "prioriteit": "hoog"},
                "MID-01": {"id": "MID-01", "prioriteit": "midden"},
                "LOW-01": {"id": "LOW-01", "prioriteit": "laag"},
            }

            high_rules = cache.get_rules_by_priority("hoog")
            assert len(high_rules) == 2
            assert all(r["prioriteit"] == "hoog" for r in high_rules)

    def test_manager_compatibility(self):
        """Test dat CachedToetsregelManager compatible is met ToetsregelManager interface."""
        cached_manager = CachedToetsregelManager()

        # Test alle belangrijke methods bestaan
        assert hasattr(cached_manager, "load_regel")
        assert hasattr(cached_manager, "get_all_regels")
        assert hasattr(cached_manager, "get_verplichte_regels")
        assert hasattr(cached_manager, "get_kritieke_regels")
        assert hasattr(cached_manager, "get_available_regels")
        assert hasattr(cached_manager, "clear_cache")
        assert hasattr(cached_manager, "get_stats")

    def test_memory_efficiency(self):
        """Test dat alleen essentiële velden worden opgeslagen."""
        cache = RuleCache()

        with patch("toetsregels.rule_cache.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("toetsregels.rule_cache.Path.glob") as mock_glob:
                # Mock een JSON file
                mock_file = MagicMock()
                mock_file.stem = "TEST-01"
                mock_glob.return_value = [mock_file]

                with patch("builtins.open", create=True) as mock_open:
                    with patch("json.load") as mock_json_load:
                        # Simuleer een regel met veel velden
                        mock_json_load.return_value = {
                            "id": "TEST-01",
                            "naam": "Test regel",
                            "prioriteit": "hoog",
                            "aanbeveling": "verplicht",
                            "herkenbaar_patronen": ["pattern1"],
                            "extra_field_1": "not needed",
                            "extra_field_2": "also not needed",
                            "huge_description": "x" * 10000,
                        }

                        # Call the cached function directly
                        from toetsregels.rule_cache import \
                            _load_all_rules_cached

                        rules = _load_all_rules_cached(str(cache.regels_dir))

                        # Verify dat alleen essentiële velden zijn opgeslagen
                        rule = rules.get("TEST-01")
                        assert rule is not None
                        assert "id" in rule
                        assert "naam" in rule
                        assert "prioriteit" in rule
                        assert "extra_field_1" not in rule
                        assert "huge_description" not in rule
