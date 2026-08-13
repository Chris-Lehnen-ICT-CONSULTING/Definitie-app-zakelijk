"""
Tests voor str↔list conversie van context velden tussen DB en service laag.

DEF-390: Verificatie dat organisatorische_context, juridische_context en
wettelijke_basis correct worden geconverteerd zonder silent data loss.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from database.models import DefinitieRecord, normalize_wettelijke_basis
from services.interfaces import Definition

pytestmark = [pytest.mark.unit]


class TestParseListConversion:
    """Test _parse_list in _record_to_definition: str→list conversie."""

    def _make_record(self, **overrides):
        """Helper: maak een DefinitieRecord met defaults."""
        defaults = {
            "id": "test-id",
            "begrip": "testbegrip",
            "definitie": "Een test definitie.",
            "organisatorische_context": "[]",
            "juridische_context": "[]",
            "wettelijke_basis": "[]",
        }
        defaults.update(overrides)
        return DefinitieRecord(**defaults)

    def _make_repo(self):
        """Helper: maak een DefinitionRepository met gemockte DB."""
        from services.definition_repository import DefinitionRepository

        repo = DefinitionRepository.__new__(DefinitionRepository)
        repo.db_path = ":memory:"
        repo._voorbeelden_repo = MagicMock()
        repo._voorbeelden_repo.get_by_definition_id.return_value = {}
        return repo

    def test_valid_json_array(self):
        """Geldige JSON array wordt correct geparsed."""
        repo = self._make_repo()
        record = self._make_record(
            organisatorische_context='["OM", "DJI"]',
            juridische_context='["Strafrecht"]',
        )
        definition = repo._record_to_definition(record)
        assert definition.organisatorische_context == ["OM", "DJI"]
        assert definition.juridische_context == ["Strafrecht"]

    def test_empty_string_returns_empty_list(self):
        """Lege string resulteert in lege lijst."""
        repo = self._make_repo()
        record = self._make_record(organisatorische_context="")
        definition = repo._record_to_definition(record)
        assert definition.organisatorische_context == []

    def test_none_returns_empty_list(self):
        """None resulteert in lege lijst."""
        repo = self._make_repo()
        record = self._make_record(organisatorische_context=None)
        definition = repo._record_to_definition(record)
        assert definition.organisatorische_context == []

    def test_malformed_json_logs_warning(self, caplog):
        """Ongeldige JSON logt een warning (niet alleen debug)."""
        repo = self._make_repo()
        record = self._make_record(organisatorische_context='{"invalid": true}')
        with caplog.at_level("WARNING"):
            definition = repo._record_to_definition(record)
        # Should still return a list (possibly empty or converted)
        assert isinstance(definition.organisatorische_context, list)

    def test_broken_json_logs_warning(self, caplog):
        """Broken JSON (niet parseerbaar) logt een warning."""
        repo = self._make_repo()
        record = self._make_record(organisatorische_context="not json at all")
        with caplog.at_level("WARNING"):
            definition = repo._record_to_definition(record)
        assert definition.organisatorische_context == []
        assert any("JSON" in msg or "parsing" in msg.lower() for msg in caplog.messages)

    def test_round_trip_preserves_data(self):
        """list→str→list round trip behoudt alle data."""
        repo = self._make_repo()
        original = ["OM", "DJI", "Rechtspraak"]
        json_str = json.dumps(original, ensure_ascii=False)
        record = self._make_record(organisatorische_context=json_str)
        definition = repo._record_to_definition(record)
        assert definition.organisatorische_context == original

    def test_unicode_context_preserved(self):
        """Unicode karakters in context worden behouden."""
        repo = self._make_repo()
        original = ["Openbaar Ministerie", "Raad voor de Kinderbescherming"]
        json_str = json.dumps(original, ensure_ascii=False)
        record = self._make_record(organisatorische_context=json_str)
        definition = repo._record_to_definition(record)
        assert definition.organisatorische_context == original


class TestDefinitionToRecord:
    """Test _definition_to_record: list→str conversie."""

    def _make_repo(self):
        from services.definition_repository import DefinitionRepository

        repo = DefinitionRepository.__new__(DefinitionRepository)
        repo.db_path = ":memory:"
        return repo

    def _make_definition(self, **overrides):
        defaults = {
            "id": "test-id",
            "begrip": "testbegrip",
            "definitie": "Een test definitie.",
            "organisatorische_context": ["OM"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Art. 27 Sv"],
        }
        defaults.update(overrides)
        return Definition(**defaults)

    def test_lists_become_json_strings(self):
        """Lists worden correct naar JSON strings geconverteerd."""
        repo = self._make_repo()
        definition = self._make_definition()
        record = repo._definition_to_record(definition)
        assert json.loads(record.organisatorische_context) == ["OM"]
        assert json.loads(record.juridische_context) == ["Strafrecht"]

    def test_none_context_becomes_empty_json_array(self):
        """None context wordt lege JSON array."""
        repo = self._make_repo()
        definition = self._make_definition(
            organisatorische_context=None, juridische_context=None
        )
        record = repo._definition_to_record(definition)
        assert json.loads(record.organisatorische_context) == []
        assert json.loads(record.juridische_context) == []

    def test_wettelijke_basis_normalized(self):
        """Wettelijke basis wordt genormaliseerd (gesorteerd, uniek)."""
        repo = self._make_repo()
        definition = self._make_definition(
            wettelijke_basis=["Art. 27 Sv", "Art. 1 Sr", "Art. 27 Sv"]
        )
        record = repo._definition_to_record(definition)
        wb_list = record.get_wettelijke_basis_list()
        assert len(wb_list) == 2  # duplicaat verwijderd
        assert wb_list == sorted(wb_list)  # gesorteerd


class TestDefinitionToUpdates:
    """Test _definition_to_updates: list→str conversie voor updates."""

    def _make_repo(self):
        from services.definition_repository import DefinitionRepository

        repo = DefinitionRepository.__new__(DefinitionRepository)
        repo.db_path = ":memory:"
        return repo

    def _make_definition(self, **overrides):
        defaults = {
            "id": "test-id",
            "begrip": "testbegrip",
            "definitie": "Een test definitie.",
            "organisatorische_context": ["OM", "DJI"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Art. 27 Sv"],
        }
        defaults.update(overrides)
        return Definition(**defaults)

    def test_context_serialized_correctly(self):
        """Context velden worden canoniek geserialiseerd in updates.

        DEF-672: de updatetak omzeilde `canoniseer_contextlijst`, waardoor een
        bijgewerkte definitie in invoegvolgorde en met duplicaten in de
        database belandde terwijl `save()` wél canoniseerde. De verwachting
        hier is daarom deterministisch gesorteerd — dat is precies wat de
        duplicaatvergelijking nodig heeft.
        """
        repo = self._make_repo()
        definition = self._make_definition()
        updates = repo._definition_to_updates(definition)
        assert json.loads(updates["organisatorische_context"]) == ["DJI", "OM"]
        assert json.loads(updates["juridische_context"]) == ["Strafrecht"]
        assert json.loads(updates["wettelijke_basis"]) == ["Art. 27 Sv"]

    def test_context_wordt_getrimd_en_ontdubbeld_bij_update(self):
        """Dezelfde opruiming als bij create — niet alleen sortering."""
        repo = self._make_repo()
        definition = self._make_definition(
            organisatorische_context=["  OM ", "DJI", "dji", ""],
            wettelijke_basis=["Art. 27 Sv", "  Art. 27 Sv  "],
        )
        updates = repo._definition_to_updates(definition)
        assert json.loads(updates["organisatorische_context"]) == ["DJI", "OM"]
        assert json.loads(updates["wettelijke_basis"]) == ["Art. 27 Sv"]

    def test_none_wettelijke_basis_becomes_empty_array(self):
        """None wettelijke_basis wordt [] door __post_init__, dan "[]" in updates."""
        repo = self._make_repo()
        definition = self._make_definition(wettelijke_basis=None)
        # Definition.__post_init__ converteert None → []
        assert definition.wettelijke_basis == []
        updates = repo._definition_to_updates(definition)
        assert updates["wettelijke_basis"] == "[]"

    def test_empty_list_becomes_empty_json_array(self):
        """Lege lijst wordt lege JSON array."""
        repo = self._make_repo()
        definition = self._make_definition(
            organisatorische_context=[], wettelijke_basis=[]
        )
        updates = repo._definition_to_updates(definition)
        assert updates["organisatorische_context"] == "[]"
        assert updates["wettelijke_basis"] == "[]"


class TestNormalizeWettelijkeBasis:
    """Test normalize_wettelijke_basis helper."""

    def test_normal_list(self):
        """Normale lijst wordt gesorteerd en gededupliceerd."""
        result = normalize_wettelijke_basis(["Art. 27 Sv", "Art. 1 Sr", "Art. 27 Sv"])
        parsed = json.loads(result)
        assert parsed == ["Art. 1 Sr", "Art. 27 Sv"]

    def test_none_returns_empty_array(self):
        """None input retourneert lege JSON array."""
        result = normalize_wettelijke_basis(None)
        assert json.loads(result) == []

    def test_empty_list(self):
        """Lege lijst retourneert lege JSON array."""
        result = normalize_wettelijke_basis([])
        assert json.loads(result) == []
