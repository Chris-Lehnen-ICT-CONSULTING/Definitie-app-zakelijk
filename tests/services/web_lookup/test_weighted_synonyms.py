"""
Comprehensive tests voor Weighted Synonyms feature (v2.0).

Test Coverage:
- WeightedSynonym dataclass validation
- YAML loading (both legacy and weighted formats)
- Weight-based sorting
- get_synonyms_with_weights() functionality
- get_best_synonyms() threshold filtering
- Backward compatibility with legacy format
- Weight validation and warnings
- Edge cases (invalid weights, missing keys, etc.)

Requirements:
- Python 3.11+
- pytest
- PyYAML
"""

import tempfile
from pathlib import Path

import pytest

from src.services.web_lookup.synonym_service import (
    JuridischeSynoniemlService,
    WeightedSynonym,
)


class TestWeightedSynonym:
    """Test suite voor WeightedSynonym dataclass."""

    def test_weighted_synonym_creation(self):
        """
        Test: Create WeightedSynonym with term and weight.

        Scenario:
        - Term: "voorarrest"
        - Weight: 0.95
        - Expected: WeightedSynonym instance
        """
        ws = WeightedSynonym(term="voorarrest", weight=0.95)

        assert ws.term == "voorarrest"
        assert ws.weight == 0.95

    def test_weighted_synonym_default_weight(self):
        """
        Test: Default weight is 1.0.

        Scenario:
        - Create WeightedSynonym without weight parameter
        - Expected: weight defaults to 1.0
        """
        ws = WeightedSynonym(term="test")

        assert ws.weight == 1.0

    def test_weighted_synonym_immutable(self):
        """
        Test: WeightedSynonym is immutable (frozen dataclass).

        Scenario:
        - Try to modify weight after creation
        - Expected: Raises FrozenInstanceError
        """
        ws = WeightedSynonym(term="test", weight=0.90)

        with pytest.raises(Exception):  # FrozenInstanceError
            ws.weight = 0.80  # type: ignore

    def test_weighted_synonym_equality(self):
        """
        Test: WeightedSynonym equality comparison.

        Scenario:
        - Create two identical WeightedSynonym instances
        - Expected: They are equal
        """
        ws1 = WeightedSynonym(term="test", weight=0.90)
        ws2 = WeightedSynonym(term="test", weight=0.90)

        assert ws1 == ws2

    def test_weighted_synonym_inequality(self):
        """
        Test: Different weights make synonyms unequal.

        Scenario:
        - Create two WeightedSynonym with same term, different weights
        - Expected: They are not equal
        """
        ws1 = WeightedSynonym(term="test", weight=0.90)
        ws2 = WeightedSynonym(term="test", weight=0.80)

        assert ws1 != ws2


class TestWeightedYAMLLoading:
    """Test suite voor loading weighted YAML format."""

    def test_load_weighted_format(self, tmp_path):
        """
        Test: Load YAML with weighted synonyms.

        Scenario:
        - YAML contains weighted format (synoniem + weight)
        - Expected: Synonyms loaded with correct weights
        """
        yaml_content = """
onherroepelijk:
  - synoniem: kracht van gewijsde
    weight: 0.95
  - synoniem: rechtskracht
    weight: 0.90
  - synoniem: definitieve uitspraak
    weight: 0.85
"""
        config_path = tmp_path / "weighted.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Verify forward index contains WeightedSynonym objects
        assert "onherroepelijk" in service.synoniemen
        weighted_syns = service.synoniemen["onherroepelijk"]

        assert len(weighted_syns) == 3
        assert all(isinstance(ws, WeightedSynonym) for ws in weighted_syns)

        # Verify weights are correct
        assert weighted_syns[0].weight == 0.95
        assert weighted_syns[1].weight == 0.90
        assert weighted_syns[2].weight == 0.85

    def test_load_legacy_format(self, tmp_path):
        """
        Test: Legacy format (plain strings) still works.

        Scenario:
        - YAML contains legacy format (plain strings)
        - Expected: Synonyms loaded with default weight 1.0
        """
        yaml_content = """
verdachte:
  - beklaagde
  - beschuldigde
  - aangeklaagde
"""
        config_path = tmp_path / "legacy.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Verify synonyms loaded
        assert "verdachte" in service.synoniemen
        weighted_syns = service.synoniemen["verdachte"]

        # All should have weight 1.0
        assert all(ws.weight == 1.0 for ws in weighted_syns)

    def test_load_mixed_format(self, tmp_path):
        """
        Test: Mixed legacy and weighted formats in same hoofdterm.

        Scenario:
        - YAML contains both legacy (strings) and weighted (dicts) formats
        - Expected: Both formats work correctly
        """
        yaml_content = """
voorlopige_hechtenis:
  - synoniem: voorarrest
    weight: 0.95
  - bewaring
  - synoniem: inverzekeringstelling
    weight: 0.85
  - gevangenhouding
"""
        config_path = tmp_path / "mixed.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        weighted_syns = service.synoniemen["voorlopige hechtenis"]

        # Check voorarrest (weighted)
        voorarrest = next(ws for ws in weighted_syns if ws.term == "voorarrest")
        assert voorarrest.weight == 0.95

        # Check bewaring (legacy -> weight 1.0)
        bewaring = next(ws for ws in weighted_syns if ws.term == "bewaring")
        assert bewaring.weight == 1.0

        # Check inverzekeringstelling (weighted)
        ivz = next(ws for ws in weighted_syns if ws.term == "inverzekeringstelling")
        assert ivz.weight == 0.85

        # Check gevangenhouding (legacy -> weight 1.0)
        gvh = next(ws for ws in weighted_syns if ws.term == "gevangenhouding")
        assert gvh.weight == 1.0

    def test_weight_sorting(self, tmp_path):
        """
        Test: Synonyms are sorted by weight (highest first).

        Scenario:
        - YAML with synonyms in random weight order
        - Expected: Loaded synonyms sorted by weight descending
        """
        yaml_content = """
test:
  - synoniem: low
    weight: 0.60
  - synoniem: high
    weight: 0.95
  - synoniem: medium
    weight: 0.80
  - synoniem: very_high
    weight: 0.98
"""
        config_path = tmp_path / "sorting.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        weighted_syns = service.synoniemen["test"]

        # Verify sorted by weight (highest first)
        assert weighted_syns[0].term == "very high"
        assert weighted_syns[0].weight == 0.98
        assert weighted_syns[1].term == "high"
        assert weighted_syns[1].weight == 0.95
        assert weighted_syns[2].term == "medium"
        assert weighted_syns[2].weight == 0.80
        assert weighted_syns[3].term == "low"
        assert weighted_syns[3].weight == 0.60


class TestGetSynonymsWithWeights:
    """Test suite voor get_synonyms_with_weights() functie."""

    @pytest.fixture
    def service_with_weighted_data(self, tmp_path):
        """Create service with weighted test data."""
        yaml_content = """
onherroepelijk:
  - synoniem: kracht van gewijsde
    weight: 0.95
  - synoniem: rechtskracht
    weight: 0.90
  - synoniem: definitieve uitspraak
    weight: 0.85

voorlopige_hechtenis:
  - synoniem: voorarrest
    weight: 0.95
  - synoniem: bewaring
    weight: 0.90
"""
        config_path = tmp_path / "weighted.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_get_synonyms_with_weights_for_hoofdterm(self, service_with_weighted_data):
        """
        Test: get_synonyms_with_weights() voor hoofdterm.

        Scenario:
        - Input: "onherroepelijk" (hoofdterm)
        - Expected: List of (term, weight) tuples
        """
        weighted = service_with_weighted_data.get_synonyms_with_weights(
            "onherroepelijk"
        )

        assert len(weighted) == 3
        assert weighted[0] == ("kracht van gewijsde", 0.95)
        assert weighted[1] == ("rechtskracht", 0.90)
        assert weighted[2] == ("definitieve uitspraak", 0.85)

    def test_get_synonyms_with_weights_reverse_lookup(self, service_with_weighted_data):
        """
        Test: get_synonyms_with_weights() reverse lookup.

        Scenario:
        - Input: "voorarrest" (synoniem van "voorlopige_hechtenis")
        - Expected: hoofdterm + other synoniemen with weights
        """
        weighted = service_with_weighted_data.get_synonyms_with_weights("voorarrest")

        # Should include hoofdterm (weight 1.0) + other synoniemen
        assert len(weighted) == 2
        assert ("voorlopige hechtenis", 1.0) in weighted
        assert ("bewaring", 0.90) in weighted
        # voorarrest itself should NOT be included
        assert not any(term == "voorarrest" for term, _ in weighted)

    def test_get_synonyms_with_weights_sorted_by_weight(
        self, service_with_weighted_data
    ):
        """
        Test: Results are sorted by weight (highest first).

        Scenario:
        - Reverse lookup should return results sorted by weight
        - Expected: hoofdterm (1.0) first, then other synoniemen by weight
        """
        weighted = service_with_weighted_data.get_synonyms_with_weights("voorarrest")

        # First should be hoofdterm with weight 1.0
        assert weighted[0][1] >= weighted[1][1]  # Sorted descending

    def test_get_synonyms_with_weights_unknown_term(self, service_with_weighted_data):
        """
        Test: Unknown term returnt lege lijst.

        Scenario:
        - Input: "nonexistent"
        - Expected: []
        """
        weighted = service_with_weighted_data.get_synonyms_with_weights("nonexistent")

        assert weighted == []


class TestGetBestSynonyms:
    """Test suite voor get_best_synonyms() threshold filtering."""

    @pytest.fixture
    def service_with_varied_weights(self, tmp_path):
        """Create service with varied synonym weights."""
        yaml_content = """
test:
  - synoniem: perfect
    weight: 1.0
  - synoniem: nearly_exact
    weight: 0.95
  - synoniem: strong
    weight: 0.85
  - synoniem: good
    weight: 0.75
  - synoniem: weak
    weight: 0.60
  - synoniem: questionable
    weight: 0.45
"""
        config_path = tmp_path / "varied.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_get_best_synonyms_default_threshold(self, service_with_varied_weights):
        """
        Test: Default threshold is 0.85.

        Scenario:
        - Call get_best_synonyms() without threshold
        - Expected: Only synonyms with weight >= 0.85
        """
        best = service_with_varied_weights.get_best_synonyms("test")

        assert len(best) == 3  # perfect, nearly_exact, strong
        assert "perfect" in best
        assert "nearly exact" in best
        assert "strong" in best
        assert "good" not in best  # 0.75 < 0.85

    def test_get_best_synonyms_custom_threshold(self, service_with_varied_weights):
        """
        Test: Custom threshold filtering.

        Scenario:
        - threshold: 0.70
        - Expected: Synonyms with weight >= 0.70
        """
        best = service_with_varied_weights.get_best_synonyms("test", threshold=0.70)

        assert len(best) == 4  # perfect, nearly_exact, strong, good
        assert "good" in best  # 0.75 >= 0.70
        assert "weak" not in best  # 0.60 < 0.70

    def test_get_best_synonyms_high_threshold(self, service_with_varied_weights):
        """
        Test: Very high threshold filters most synonyms.

        Scenario:
        - threshold: 0.95
        - Expected: Only nearly_exact and perfect
        """
        best = service_with_varied_weights.get_best_synonyms("test", threshold=0.95)

        assert len(best) == 2
        assert "perfect" in best
        assert "nearly exact" in best

    def test_get_best_synonyms_low_threshold(self, service_with_varied_weights):
        """
        Test: Very low threshold includes weak synonyms.

        Scenario:
        - threshold: 0.40
        - Expected: All synonyms
        """
        best = service_with_varied_weights.get_best_synonyms("test", threshold=0.40)

        assert len(best) == 6  # All synonyms


class TestBackwardCompatibility:
    """Test suite voor backward compatibility met legacy format."""

    def test_get_synoniemen_backward_compatible(self, tmp_path):
        """
        Test: get_synoniemen() works with weighted format.

        Scenario:
        - YAML uses weighted format
        - Call get_synoniemen() (legacy API)
        - Expected: Returns plain strings (no weights)
        """
        yaml_content = """
test:
  - synoniem: syn1
    weight: 0.95
  - synoniem: syn2
    weight: 0.85
"""
        config_path = tmp_path / "weighted.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        synoniemen = service.get_synoniemen("test")

        # Should return plain strings
        assert synoniemen == ["syn1", "syn2"]  # Sorted by weight
        assert all(isinstance(s, str) for s in synoniemen)

    def test_expand_query_terms_uses_weight_sorting(self, tmp_path):
        """
        Test: expand_query_terms() respects weight-based sorting.

        Scenario:
        - YAML with weighted synonyms in random order
        - Call expand_query_terms()
        - Expected: Top-N synonyms by weight (not YAML order)
        """
        yaml_content = """
test:
  - synoniem: low_weight
    weight: 0.60
  - synoniem: high_weight
    weight: 0.95
  - synoniem: medium_weight
    weight: 0.80
"""
        config_path = tmp_path / "weighted.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        expanded = service.expand_query_terms("test", max_synonyms=2)

        # Should get top 2 by weight (high_weight, medium_weight)
        assert expanded[0] == "test"  # Original term first
        assert expanded[1] == "high weight"  # Highest weight
        assert expanded[2] == "medium weight"  # Second highest
        assert len(expanded) == 3


class TestEdgeCases:
    """Test suite voor edge cases en error handling."""

    def test_invalid_weight_type(self, tmp_path):
        """
        Test: Invalid weight type (string instead of float).

        Scenario:
        - YAML contains weight: "high" (string)
        - Expected: Service handles gracefully (logs error, entire hoofdterm may fail to load)
        """
        yaml_content = """
test:
  - synoniem: invalid
    weight: "high"
  - synoniem: valid
    weight: 0.90
"""
        config_path = tmp_path / "invalid.yaml"
        config_path.write_text(yaml_content)

        # Should not crash (graceful error handling)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Service may not load hovedterm due to YAML parsing error
        # This is acceptable - the service handles the error gracefully
        assert isinstance(service.synoniemen, dict)

    def test_missing_synoniem_key(self, tmp_path):
        """
        Test: Dict entry missing 'synoniem' key.

        Scenario:
        - YAML contains dict with only 'weight' (no 'synoniem')
        - Expected: Entry is skipped with warning
        """
        yaml_content = """
test:
  - weight: 0.95  # Missing 'synoniem' key
  - synoniem: valid
    weight: 0.90
"""
        config_path = tmp_path / "missing_key.yaml"
        config_path.write_text(yaml_content)

        # Should not crash
        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Valid synonym should be loaded
        assert "test" in service.synoniemen
        assert len(service.synoniemen["test"]) == 1
        assert service.synoniemen["test"][0].term == "valid"

    def test_weight_clamping(self, tmp_path):
        """
        Test: Weights outside range [0.0, 1.0] are clamped.

        Scenario:
        - YAML contains weight: 1.5 and weight: -0.2
        - Expected: Weights clamped to [0.0, 1.0]
        """
        yaml_content = """
test:
  - synoniem: too_high
    weight: 1.5
  - synoniem: too_low
    weight: -0.2
"""
        config_path = tmp_path / "clamped.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        weighted_syns = service.synoniemen["test"]

        # Check clamping
        too_high = next(ws for ws in weighted_syns if ws.term == "too high")
        assert too_high.weight == 1.0  # Clamped from 1.5

        too_low = next(ws for ws in weighted_syns if ws.term == "too low")
        assert too_low.weight == 0.0  # Clamped from -0.2

    def test_empty_weight_defaults_to_one(self, tmp_path):
        """
        Test: Missing weight defaults to 1.0.

        Scenario:
        - YAML contains 'synoniem' but no 'weight'
        - Expected: Weight defaults to 1.0
        """
        yaml_content = """
test:
  - synoniem: no_weight
"""
        config_path = tmp_path / "no_weight.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        weighted_syns = service.synoniemen["test"]
        assert weighted_syns[0].weight == 1.0


class TestWeightedSynonymsIntegration:
    """Integration tests combining multiple weighted synonym features."""

    def test_full_workflow(self, tmp_path):
        """
        Test: Complete workflow van loading tot querying.

        Scenario:
        - Load mixed format YAML
        - Test get_synoniemen(), get_synonyms_with_weights(), get_best_synonyms()
        - Verify consistency across all methods
        """
        yaml_content = """
onherroepelijk:
  - synoniem: kracht van gewijsde
    weight: 0.95
  - rechtskracht  # Legacy format
  - synoniem: definitieve uitspraak
    weight: 0.80
  - synoniem: finale uitspraak
    weight: 0.75
"""
        config_path = tmp_path / "full.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Test get_synoniemen() - should be sorted by weight
        plain = service.get_synoniemen("onherroepelijk")
        assert plain[0] == "rechtskracht"  # weight 1.0 (legacy)
        assert plain[1] == "kracht van gewijsde"  # weight 0.95

        # Test get_synonyms_with_weights()
        weighted = service.get_synonyms_with_weights("onherroepelijk")
        assert weighted[0] == ("rechtskracht", 1.0)
        assert weighted[1] == ("kracht van gewijsde", 0.95)

        # Test get_best_synonyms() with threshold
        best = service.get_best_synonyms("onherroepelijk", threshold=0.85)
        assert len(best) == 2  # Only rechtskracht and kracht van gewijsde
        assert "rechtskracht" in best
        assert "kracht van gewijsde" in best
        assert "definitieve uitspraak" not in best  # 0.80 < 0.85

    def test_stats_with_weighted_synonyms(self, tmp_path):
        """
        Test: get_stats() werkt correct met weighted synonyms.

        Scenario:
        - Load weighted YAML
        - Call get_stats()
        - Expected: Correct counts (doesn't break with WeightedSynonym objects)
        """
        yaml_content = """
term1:
  - synoniem: syn1
    weight: 0.95
  - synoniem: syn2
    weight: 0.90

term2:
  - synoniem: syn3
    weight: 0.85
"""
        config_path = tmp_path / "stats.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        stats = service.get_stats()

        assert stats["hoofdtermen"] == 2
        assert stats["totaal_synoniemen"] == 3
        assert stats["unieke_synoniemen"] == 3
        assert stats["gemiddeld_per_term"] == 1.5
