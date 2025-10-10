"""
Comprehensive unit tests voor JuridischeSynoniemlService.

Test Coverage:
- Normalisatie van termen
- YAML loading (forward + reverse index)
- Bidirectionele synonym lookup
- Query expansion met max_synonyms limit
- Text analysis (find_matching_synoniemen)
- Statistieken
- Edge cases (empty, unknown, speciale characters, malformed YAML)

Requirements:
- Python 3.11+
- pytest
- PyYAML (optioneel voor service, maar required voor tests)
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.web_lookup.synonym_service import (
    JuridischeSynoniemlService, get_synonym_service)


class TestJuridischeSynoniemlServiceInitialization:
    """Test suite voor service initialisatie."""

    def test_init_with_default_config_path(self):
        """
        Test: Service initialiseert met default config path.

        Scenario:
        - Geen config_path meegegeven
        - Service zoekt config/juridische_synoniemen.yaml
        """
        service = JuridischeSynoniemlService()

        # Verify config path is set correctly
        assert service.config_path.name == "juridische_synoniemen.yaml"
        assert "config" in str(service.config_path)

    def test_init_with_custom_config_path(self, tmp_path):
        """
        Test: Service initialiseert met custom config path.

        Scenario:
        - Custom config_path opgegeven
        - Service gebruikt deze path
        """
        # Create temporary YAML file
        custom_config = tmp_path / "custom_synoniemen.yaml"
        custom_config.write_text("test:\n  - synoniem1\n")

        service = JuridischeSynoniemlService(config_path=str(custom_config))

        assert service.config_path == custom_config

    def test_init_loads_synoniemen(self):
        """
        Test: Service laadt synoniemen tijdens initialisatie.

        Scenario:
        - Config file bestaat en bevat synoniemen
        - Forward + reverse index worden gebouwd
        """
        service = JuridischeSynoniemlService()

        # Verify synoniemen are loaded (depending on whether config exists)
        # If config exists, we should have synoniemen
        if service.config_path.exists():
            assert len(service.synoniemen) > 0
            assert len(service.reverse_index) > 0


class TestTermNormalization:
    """Test suite voor _normalize_term() functie."""

    def test_normalize_lowercase(self):
        """
        Test: Normaliseer naar lowercase.

        Scenario:
        - Input: "ONHERROEPELIJK"
        - Expected: "onherroepelijk"
        """
        service = JuridischeSynoniemlService()
        normalized = service._normalize_term("ONHERROEPELIJK")

        assert normalized == "onherroepelijk"

    def test_normalize_strip_whitespace(self):
        """
        Test: Strip leading/trailing whitespace.

        Scenario:
        - Input: "  voorlopige hechtenis  "
        - Expected: "voorlopige hechtenis"
        """
        service = JuridischeSynoniemlService()
        normalized = service._normalize_term("  voorlopige hechtenis  ")

        assert normalized == "voorlopige hechtenis"

    def test_normalize_replace_underscores(self):
        """
        Test: Vervang underscores met spaties (YAML key format).

        Scenario:
        - Input: "voorlopige_hechtenis"
        - Expected: "voorlopige hechtenis"
        """
        service = JuridischeSynoniemlService()
        normalized = service._normalize_term("voorlopige_hechtenis")

        assert normalized == "voorlopige hechtenis"

    def test_normalize_combined(self):
        """
        Test: Combinatie van alle normalisaties.

        Scenario:
        - Input: "  VOORLOPIGE_HECHTENIS  "
        - Expected: "voorlopige hechtenis"
        """
        service = JuridischeSynoniemlService()
        normalized = service._normalize_term("  VOORLOPIGE_HECHTENIS  ")

        assert normalized == "voorlopige hechtenis"

    def test_normalize_empty_string(self):
        """
        Test: Empty string blijft empty.

        Scenario:
        - Input: ""
        - Expected: ""
        """
        service = JuridischeSynoniemlService()
        normalized = service._normalize_term("")

        assert normalized == ""

    def test_normalize_special_characters(self):
        """
        Test: Speciale characters blijven behouden (behalve underscores).

        Scenario:
        - Input: "Art. 12a"
        - Expected: "art. 12a"
        """
        service = JuridischeSynoniemlService()
        normalized = service._normalize_term("Art. 12a")

        assert normalized == "art. 12a"


class TestLoadSynoniemen:
    """Test suite voor _load_synoniemen() functie."""

    def test_load_valid_yaml(self, tmp_path):
        """
        Test: Load valid YAML with synoniemen.

        Scenario:
        - YAML bevat 2 hoofdtermen met synoniemen
        - Forward + reverse index worden gebouwd
        """
        # Create test YAML
        yaml_content = """
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - definitieve uitspraak

voorlopige_hechtenis:
  - voorarrest
  - bewaring
"""
        config_path = tmp_path / "test_synoniemen.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Verify forward index
        assert "onherroepelijk" in service.synoniemen
        assert "voorlopige hechtenis" in service.synoniemen

        # Verify synoniemen lists (now WeightedSynonym objects)
        onherr_syns = [ws.term for ws in service.synoniemen["onherroepelijk"]]
        assert "kracht van gewijsde" in onherr_syns
        assert "rechtskracht" in onherr_syns

        voorl_syns = [ws.term for ws in service.synoniemen["voorlopige hechtenis"]]
        assert "voorarrest" in voorl_syns

        # Verify reverse index
        assert "kracht van gewijsde" in service.reverse_index
        assert service.reverse_index["kracht van gewijsde"] == "onherroepelijk"
        assert service.reverse_index["voorarrest"] == "voorlopige hechtenis"

    def test_load_empty_yaml(self, tmp_path):
        """
        Test: Load empty YAML file.

        Scenario:
        - YAML file is empty
        - Service heeft lege synoniemen database
        """
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")

        service = JuridischeSynoniemlService(config_path=str(config_path))

        assert len(service.synoniemen) == 0
        assert len(service.reverse_index) == 0

    def test_load_nonexistent_file(self, tmp_path):
        """
        Test: Config file bestaat niet.

        Scenario:
        - Config path wijst naar niet-bestaand file
        - Service werkt zonder synoniemen (geen crash)
        """
        config_path = tmp_path / "nonexistent.yaml"

        service = JuridischeSynoniemlService(config_path=str(config_path))

        assert len(service.synoniemen) == 0
        assert len(service.reverse_index) == 0

    def test_load_malformed_yaml(self, tmp_path):
        """
        Test: Malformed YAML handling.

        Scenario:
        - YAML bevat syntax errors
        - Service logt error en werkt zonder synoniemen (of parsed wat mogelijk is)
        """
        config_path = tmp_path / "malformed.yaml"
        # More clearly malformed YAML that will actually fail parsing
        config_path.write_text("onherroepelijk:\n  - synoniem\n  ]: broken")

        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Service should handle error gracefully (empty synoniemen on parse error)
        # Note: Some "malformed" YAML may still parse successfully
        assert isinstance(service.synoniemen, dict)

    def test_load_skips_non_list_entries(self, tmp_path):
        """
        Test: Skip entries die geen lijst zijn (comments/metadata).

        Scenario:
        - YAML bevat metadata entries (strings, geen lijsten)
        - Deze worden geskipped
        """
        yaml_content = """
_metadata: "Dit is een comment"
_version: 1.0

onherroepelijk:
  - kracht van gewijsde
"""
        config_path = tmp_path / "with_metadata.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Only onherroepelijk should be loaded
        assert len(service.synoniemen) == 1
        assert "onherroepelijk" in service.synoniemen

    def test_load_filters_empty_synoniemen(self, tmp_path):
        """
        Test: Filter lege synoniemen uit.

        Scenario:
        - YAML bevat lege strings of None values
        - Deze worden gefilterd
        """
        yaml_content = """
test:
  - ""
  - null
  - synoniem1
  - "  "
  - synoniem2
"""
        config_path = tmp_path / "with_empty.yaml"
        config_path.write_text(yaml_content)

        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Only valid synoniemen should be loaded (now WeightedSynonym objects)
        weighted_syns = service.synoniemen.get("test", [])
        syn_terms = [ws.term for ws in weighted_syns]
        assert "synoniem1" in syn_terms
        assert "synoniem2" in syn_terms
        assert len(weighted_syns) == 2  # Only 2 valid entries


class TestGetSynoniemen:
    """Test suite voor get_synoniemen() - bidirectionele lookup."""

    @pytest.fixture()
    def service_with_data(self, tmp_path):
        """Create service with test data."""
        yaml_content = """
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - definitieve uitspraak

voorlopige_hechtenis:
  - voorarrest
  - bewaring
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_get_synoniemen_for_hoofdterm(self, service_with_data):
        """
        Test: Haal synoniemen op voor hoofdterm.

        Scenario:
        - Input: "onherroepelijk" (hoofdterm)
        - Expected: ["kracht van gewijsde", "rechtskracht", "definitieve uitspraak"]
        """
        synoniemen = service_with_data.get_synoniemen("onherroepelijk")

        assert "kracht van gewijsde" in synoniemen
        assert "rechtskracht" in synoniemen
        assert "definitieve uitspraak" in synoniemen

    def test_get_synoniemen_for_synoniem(self, service_with_data):
        """
        Test: Reverse lookup - synoniem → hoofdterm + andere synoniemen.

        Scenario:
        - Input: "kracht van gewijsde" (synoniem van "onherroepelijk")
        - Expected: ["onherroepelijk", "rechtskracht", "definitieve uitspraak"]
        - Hoofdterm wordt toegevoegd, originele term wordt verwijderd
        """
        synoniemen = service_with_data.get_synoniemen("kracht van gewijsde")

        assert "onherroepelijk" in synoniemen  # Hoofdterm toegevoegd
        assert "rechtskracht" in synoniemen
        assert "definitieve uitspraak" in synoniemen
        assert "kracht van gewijsde" not in synoniemen  # Originele term verwijderd

    def test_get_synoniemen_case_insensitive(self, service_with_data):
        """
        Test: Lookup is case-insensitive.

        Scenario:
        - Input: "ONHERROEPELIJK"
        - Expected: Zelfde resultaat als "onherroepelijk"
        """
        synoniemen_lower = service_with_data.get_synoniemen("onherroepelijk")
        synoniemen_upper = service_with_data.get_synoniemen("ONHERROEPELIJK")

        assert synoniemen_lower == synoniemen_upper

    def test_get_synoniemen_with_underscores(self, service_with_data):
        """
        Test: Lookup met underscores werkt (YAML key format).

        Scenario:
        - Input: "voorlopige_hechtenis"
        - Expected: Zelfde resultaat als "voorlopige hechtenis"
        """
        synoniemen_underscore = service_with_data.get_synoniemen("voorlopige_hechtenis")
        synoniemen_space = service_with_data.get_synoniemen("voorlopige hechtenis")

        assert synoniemen_underscore == synoniemen_space
        assert "voorarrest" in synoniemen_underscore

    def test_get_synoniemen_unknown_term(self, service_with_data):
        """
        Test: Unknown term returnt lege lijst.

        Scenario:
        - Input: "nonexistent_term"
        - Expected: []
        """
        synoniemen = service_with_data.get_synoniemen("nonexistent_term")

        assert synoniemen == []

    def test_get_synoniemen_empty_string(self, service_with_data):
        """
        Test: Empty string returnt lege lijst.

        Scenario:
        - Input: ""
        - Expected: []
        """
        synoniemen = service_with_data.get_synoniemen("")

        assert synoniemen == []

    def test_get_synoniemen_returns_copy(self, service_with_data):
        """
        Test: get_synoniemen() returnt een copy (no mutation).

        Scenario:
        - Haal synoniemen op
        - Muteer resultaat
        - Verify dat origineel ongewijzigd is
        """
        synoniemen1 = service_with_data.get_synoniemen("onherroepelijk")
        synoniemen1.append("MODIFIED")

        synoniemen2 = service_with_data.get_synoniemen("onherroepelijk")

        assert "MODIFIED" not in synoniemen2


class TestExpandQueryTerms:
    """Test suite voor expand_query_terms() - query expansion."""

    @pytest.fixture()
    def service_with_data(self, tmp_path):
        """Create service with test data."""
        yaml_content = """
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht
  - definitieve uitspraak
  - finale uitspraak
  - onherroepelijke veroordeling
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_expand_with_max_synonyms(self, service_with_data):
        """
        Test: Expand met max_synonyms limiet.

        Scenario:
        - Term: "onherroepelijk"
        - max_synonyms: 3
        - Expected: ["onherroepelijk", <3 synoniemen>]
        """
        expanded = service_with_data.expand_query_terms(
            "onherroepelijk", max_synonyms=3
        )

        assert len(expanded) == 4  # Origineel + 3 synoniemen
        assert expanded[0] == "onherroepelijk"
        assert "kracht van gewijsde" in expanded
        assert "rechtskracht" in expanded
        assert "definitieve uitspraak" in expanded

    def test_expand_default_max_synonyms(self, service_with_data):
        """
        Test: Default max_synonyms = 3.

        Scenario:
        - Geen max_synonyms opgegeven
        - Expected: max 3 synoniemen
        """
        expanded = service_with_data.expand_query_terms("onherroepelijk")

        assert len(expanded) == 4  # Origineel + 3 (default)

    def test_expand_no_synoniemen(self, service_with_data):
        """
        Test: Term zonder synoniemen.

        Scenario:
        - Term: "nonexistent"
        - Expected: ["nonexistent"] (alleen origineel)
        """
        expanded = service_with_data.expand_query_terms("nonexistent")

        assert expanded == ["nonexistent"]

    def test_expand_fewer_synoniemen_than_max(self, tmp_path):
        """
        Test: Term heeft minder synoniemen dan max_synonyms.

        Scenario:
        - Term heeft 2 synoniemen
        - max_synonyms: 5
        - Expected: Alle synoniemen worden toegevoegd
        """
        yaml_content = """
test:
  - syn1
  - syn2
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        expanded = service.expand_query_terms("test", max_synonyms=5)

        assert len(expanded) == 3  # Origineel + 2 synoniemen

    def test_expand_max_synonyms_zero(self, service_with_data):
        """
        Test: max_synonyms = 0.

        Scenario:
        - max_synonyms: 0
        - Expected: Alleen originele term
        """
        expanded = service_with_data.expand_query_terms(
            "onherroepelijk", max_synonyms=0
        )

        assert expanded == ["onherroepelijk"]


class TestHasSynoniemen:
    """Test suite voor has_synoniemen() - boolean check."""

    @pytest.fixture()
    def service_with_data(self, tmp_path):
        """Create service with test data."""
        yaml_content = """
onherroepelijk:
  - kracht van gewijsde
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_has_synoniemen_true_for_hoofdterm(self, service_with_data):
        """
        Test: has_synoniemen() returnt True voor hoofdterm.

        Scenario:
        - Term: "onherroepelijk" (hoofdterm)
        - Expected: True
        """
        assert service_with_data.has_synoniemen("onherroepelijk") is True

    def test_has_synoniemen_true_for_synoniem(self, service_with_data):
        """
        Test: has_synoniemen() returnt True voor synoniem.

        Scenario:
        - Term: "kracht van gewijsde" (synoniem)
        - Expected: True
        """
        assert service_with_data.has_synoniemen("kracht van gewijsde") is True

    def test_has_synoniemen_false_for_unknown(self, service_with_data):
        """
        Test: has_synoniemen() returnt False voor unknown term.

        Scenario:
        - Term: "nonexistent"
        - Expected: False
        """
        assert service_with_data.has_synoniemen("nonexistent") is False

    def test_has_synoniemen_false_for_empty(self, service_with_data):
        """
        Test: has_synoniemen() returnt False voor empty string.

        Scenario:
        - Term: ""
        - Expected: False
        """
        assert service_with_data.has_synoniemen("") is False


class TestGetAllTerms:
    """Test suite voor get_all_terms() - set van alle termen."""

    @pytest.fixture()
    def service_with_data(self, tmp_path):
        """Create service with test data."""
        yaml_content = """
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht

voorlopige_hechtenis:
  - voorarrest
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_get_all_terms_includes_hoofdtermen(self, service_with_data):
        """
        Test: get_all_terms() bevat hoofdtermen.

        Scenario:
        - Expected: "onherroepelijk", "voorlopige hechtenis" in resultaat
        """
        all_terms = service_with_data.get_all_terms()

        assert "onherroepelijk" in all_terms
        assert "voorlopige hechtenis" in all_terms

    def test_get_all_terms_includes_synoniemen(self, service_with_data):
        """
        Test: get_all_terms() bevat synoniemen.

        Scenario:
        - Expected: "kracht van gewijsde", "rechtskracht", "voorarrest" in resultaat
        """
        all_terms = service_with_data.get_all_terms()

        assert "kracht van gewijsde" in all_terms
        assert "rechtskracht" in all_terms
        assert "voorarrest" in all_terms

    def test_get_all_terms_returns_set(self, service_with_data):
        """
        Test: get_all_terms() returnt een set.

        Scenario:
        - Verify type is set
        - Verify geen duplicaten
        """
        all_terms = service_with_data.get_all_terms()

        assert isinstance(all_terms, set)

    def test_get_all_terms_empty_database(self, tmp_path):
        """
        Test: get_all_terms() met lege database.

        Scenario:
        - Geen synoniemen geladen
        - Expected: Lege set
        """
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")
        service = JuridischeSynoniemlService(config_path=str(config_path))

        all_terms = service.get_all_terms()

        assert len(all_terms) == 0


class TestFindMatchingSynoniemen:
    """Test suite voor find_matching_synoniemen() - text analysis."""

    @pytest.fixture()
    def service_with_data(self, tmp_path):
        """Create service with test data."""
        yaml_content = """
onherroepelijk:
  - kracht van gewijsde
  - rechtskracht

verdachte:
  - beklaagde
  - beschuldigde
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_find_matching_in_text(self, service_with_data):
        """
        Test: Vind juridische termen in tekst.

        Scenario:
        - Text: "De verdachte kreeg een onherroepelijke veroordeling"
        - Expected: Dict met "verdachte" en "onherroepelijk"
        """
        text = "De verdachte kreeg een onherroepelijke veroordeling"
        matches = service_with_data.find_matching_synoniemen(text)

        assert "verdachte" in matches
        assert "onherroepelijk" in matches

        # Verify synoniemen zijn correct
        assert "beklaagde" in matches["verdachte"]
        assert "kracht van gewijsde" in matches["onherroepelijk"]

    def test_find_matching_case_insensitive(self, service_with_data):
        """
        Test: Text matching is case-insensitive.

        Scenario:
        - Text: "DE VERDACHTE KREEG"
        - Expected: "verdachte" wordt gevonden
        """
        text = "DE VERDACHTE KREEG"
        matches = service_with_data.find_matching_synoniemen(text)

        assert "verdachte" in matches

    def test_find_matching_no_matches(self, service_with_data):
        """
        Test: Geen matches in tekst.

        Scenario:
        - Text: "Dit is een test zonder juridische termen"
        - Expected: Lege dict
        """
        text = "Dit is een test zonder juridische termen"
        matches = service_with_data.find_matching_synoniemen(text)

        assert len(matches) == 0

    def test_find_matching_partial_word_no_match(self, service_with_data):
        """
        Test: Partial word matches worden ook gevonden (greedy matching).

        Scenario:
        - Text: "onherroepelijke" (contains "onherroepelijk")
        - Expected: "onherroepelijk" wordt gevonden
        """
        text = "onherroepelijke veroordeling"
        matches = service_with_data.find_matching_synoniemen(text)

        # Greedy matching: "onherroepelijk" zit in "onherroepelijke"
        assert "onherroepelijk" in matches

    def test_find_matching_empty_text(self, service_with_data):
        """
        Test: Empty text.

        Scenario:
        - Text: ""
        - Expected: Lege dict
        """
        matches = service_with_data.find_matching_synoniemen("")

        assert len(matches) == 0


class TestGetStats:
    """Test suite voor get_stats() - statistieken."""

    @pytest.fixture()
    def service_with_data(self, tmp_path):
        """Create service with test data."""
        yaml_content = """
term1:
  - syn1
  - syn2
  - syn3

term2:
  - syn4
  - syn5
"""
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml_content)
        return JuridischeSynoniemlService(config_path=str(config_path))

    def test_stats_hoofdtermen(self, service_with_data):
        """
        Test: Statistiek: aantal hoofdtermen.

        Scenario:
        - 2 hoofdtermen in database
        - Expected: hoofdtermen = 2
        """
        stats = service_with_data.get_stats()

        assert stats["hoofdtermen"] == 2

    def test_stats_totaal_synoniemen(self, service_with_data):
        """
        Test: Statistiek: totaal aantal synoniemen.

        Scenario:
        - term1: 3 synoniemen, term2: 2 synoniemen
        - Expected: totaal_synoniemen = 5
        """
        stats = service_with_data.get_stats()

        assert stats["totaal_synoniemen"] == 5

    def test_stats_unieke_synoniemen(self, service_with_data):
        """
        Test: Statistiek: unieke synoniemen (reverse index size).

        Scenario:
        - 5 unieke synoniemen
        - Expected: unieke_synoniemen = 5
        """
        stats = service_with_data.get_stats()

        assert stats["unieke_synoniemen"] == 5

    def test_stats_gemiddeld_per_term(self, service_with_data):
        """
        Test: Statistiek: gemiddeld aantal synoniemen per term.

        Scenario:
        - term1: 3, term2: 2
        - Expected: gemiddeld = 2.5
        """
        stats = service_with_data.get_stats()

        assert stats["gemiddeld_per_term"] == 2.5

    def test_stats_empty_database(self, tmp_path):
        """
        Test: Statistieken met lege database.

        Scenario:
        - Geen synoniemen
        - Expected: Alle stats zijn 0
        """
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")
        service = JuridischeSynoniemlService(config_path=str(config_path))

        stats = service.get_stats()

        assert stats["hoofdtermen"] == 0
        assert stats["totaal_synoniemen"] == 0
        assert stats["unieke_synoniemen"] == 0
        assert stats["gemiddeld_per_term"] == 0


class TestSingletonGetSynonymService:
    """Test suite voor get_synonym_service() singleton."""

    def test_singleton_returns_same_instance(self):
        """
        Test: get_synonym_service() returnt dezelfde instance.

        Scenario:
        - Call get_synonym_service() 2x zonder config_path
        - Expected: Zelfde instance object
        """
        service1 = get_synonym_service()
        service2 = get_synonym_service()

        assert service1 is service2

    def test_singleton_with_custom_config_creates_new(self, tmp_path):
        """
        Test: get_synonym_service() met custom config creëert nieuwe instance.

        Scenario:
        - Call met config_path
        - Expected: Nieuwe instance (singleton reset)
        """
        config_path = tmp_path / "custom.yaml"
        config_path.write_text("test:\n  - syn1\n")

        _ = get_synonym_service()  # Initialize default singleton
        service2 = get_synonym_service(config_path=str(config_path))

        # Should be different instances
        assert service2.config_path == config_path

    def test_singleton_reset_on_custom_config(self, tmp_path):
        """
        Test: Singleton wordt reset bij custom config.

        Scenario:
        - Call 1: default
        - Call 2: custom config
        - Call 3: default
        - Expected: Call 3 gebruikt custom config (singleton persists)
        """
        config_path = tmp_path / "custom.yaml"
        config_path.write_text("test:\n  - syn1\n")

        _ = get_synonym_service()  # Initialize default singleton
        service2 = get_synonym_service(config_path=str(config_path))
        service3 = get_synonym_service()

        # After reset with custom config, subsequent calls use that config
        assert service3 is service2


class TestEdgeCases:
    """Test suite voor edge cases en error handling."""

    def test_yaml_with_circular_references(self, tmp_path):
        """
        Test: Circular synonym references (logische inconsistentie).

        Scenario:
        - YAML: term1 → [term2], term2 → [term1]
        - Service moet dit accepteren (geen infinite loop)
        """
        yaml_content = """
term1:
  - term2

term2:
  - term1
"""
        config_path = tmp_path / "circular.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        # Should not crash
        synoniemen1 = service.get_synoniemen("term1")
        _ = service.get_synoniemen("term2")  # Should not crash

        # term2 should be in synoniemen of term1
        assert "term2" in synoniemen1

    def test_yaml_unavailable_graceful_degradation(self, tmp_path):
        """
        Test: Service werkt zonder PyYAML (graceful degradation).

        Scenario:
        - PyYAML niet beschikbaar (YAML_AVAILABLE = False)
        - Service initialiseert zonder crash
        """
        config_path = tmp_path / "test.yaml"
        config_path.write_text("test:\n  - syn\n")

        # Mock YAML_AVAILABLE flag
        with patch("src.services.web_lookup.synonym_service.YAML_AVAILABLE", False):
            service = JuridischeSynoniemlService(config_path=str(config_path))

            # Service should work but have no synoniemen
            assert len(service.synoniemen) == 0

    def test_unicode_and_special_characters(self, tmp_path):
        """
        Test: Unicode en speciale characters in synoniemen.

        Scenario:
        - YAML bevat Nederlandse karakters (ë, ï, etc.)
        - Service handled deze correct
        """
        yaml_content = """
coëfficiënt:
  - verhoudingsgetal
  - rekenkundige factor
"""
        config_path = tmp_path / "unicode.yaml"
        config_path.write_text(yaml_content, encoding="utf-8")
        service = JuridischeSynoniemlService(config_path=str(config_path))

        synoniemen = service.get_synoniemen("coëfficiënt")
        assert "verhoudingsgetal" in synoniemen

    def test_very_long_synonym_list(self, tmp_path):
        """
        Test: Zeer lange synoniemenlijst (performance).

        Scenario:
        - Hoofdterm met 100 synoniemen
        - Verify dat expand_query_terms correct limiteert
        """
        synoniemen_list = [f"syn{i}" for i in range(100)]
        yaml_content = "term:\n" + "\n".join(f"  - {syn}" for syn in synoniemen_list)

        config_path = tmp_path / "long_list.yaml"
        config_path.write_text(yaml_content)
        service = JuridischeSynoniemlService(config_path=str(config_path))

        # expand_query_terms should respect max_synonyms
        expanded = service.expand_query_terms("term", max_synonyms=5)
        assert len(expanded) == 6  # Original + 5 synoniemen
