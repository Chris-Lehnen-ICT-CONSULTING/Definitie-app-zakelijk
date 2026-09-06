"""Tests voor category regeneration functionaliteit.

DEF-519 — contractmapping van de oude naar de actuele route:

* de oude node riep `DefinitionGeneratorTab._trigger_regeneration_with_category`
  aan met categoriecodes ACT/ENT en verwachtte een `regenerate_with_category`-
  vlag. Die methode bestaat daar niet meer; de tab delegeert naar
  `CategoryRenderer`;
* de actieve knoppen (category_renderer.py:289/370) roepen
  `_direct_regenerate_definition` aan — dat is de route die hier getoetst wordt,
  met codes uit `OntologischeCategorie`;
* `CategoryRenderer._trigger_regeneration_with_category` bestaat nog maar is
  sinds US-445 deprecated: het toont een handmatige instructie en voert niets
  uit. Zo wordt het hier ook getoetst.

Geen verwijderde regeneratieservice herbouwd. State loopt via de échte
`SessionStateManager` op een verse, geïsoleerde `st.session_state`.
"""

from unittest.mock import Mock, patch

import pytest
import streamlit as st

from domain.ontological_categories import OntologischeCategorie
from ui.components.category_regeneration_helper import CategoryRegenerationHelper
from ui.components.category_renderer import CategoryRenderer
from ui.components.definition_generator_tab import DefinitionGeneratorTab
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.regression]


class TestCategoryRegeneration:
    """Test class voor category regeneration flow."""

    @pytest.fixture
    def mock_checker(self):
        """Mock DefinitieChecker."""
        return Mock()

    @pytest.fixture
    def generator_tab(self, mock_checker):
        """DefinitionGeneratorTab instance; repositoryfabriek als grens gepatcht."""
        with patch("database.definitie_repository.get_definitie_repository"):
            return DefinitionGeneratorTab(mock_checker)

    @pytest.fixture
    def verse_sessiestate(self):
        """Verse, geïsoleerde `st.session_state`.

        `patch.object` zet de oorspronkelijke state terug bij het verlaten van de
        scope, dus ook wanneer een assertie faalt.
        """
        with patch.object(st, "session_state", {}):
            yield st.session_state

    def test_old_trigger_is_now_category_renderer_route(self, generator_tab):
        """Mapping: de oude tab-trigger is weg, de renderer draagt de route."""
        assert not hasattr(
            DefinitionGeneratorTab, "_trigger_regeneration_with_category"
        )
        assert isinstance(generator_tab.category_renderer, CategoryRenderer)
        assert hasattr(generator_tab.category_renderer, "_direct_regenerate_definition")

    def test_direct_regeneration_sets_category_and_clears_stale_state(
        self, verse_sessiestate
    ):
        """De actieve route: categorie zetten, stale state wissen, opties bewaren."""

        renderer = CategoryRenderer()
        nieuwe = OntologischeCategorie.PROCES.value
        oude = OntologischeCategorie.TYPE.value

        SessionStateManager.set_value("last_generation_result", {"definitie": "oud"})
        SessionStateManager.set_value("selected_definition", {"id": 7})
        SessionStateManager.set_value("last_check_result", {"duplicaat": True})
        SessionStateManager.set_value(
            "generation_options",
            {
                "force_generate": True,
                "force_duplicate": True,
                "include_examples": True,
                "model": "sonnet",
            },
        )

        with (
            patch.object(st, "success", create=True) as mock_success,
            patch.object(st, "rerun", create=True) as mock_rerun,
        ):
            renderer._direct_regenerate_definition(
                begrip="TestBegrip",
                new_category=nieuwe,
                old_category=oude,
                saved_record=None,
                generation_result={},
            )

        assert SessionStateManager.get_value("manual_ontological_category") == nieuwe
        for sleutel in (
            "last_generation_result",
            "selected_definition",
            "last_check_result",
        ):
            assert sleutel not in verse_sessiestate

        opties = SessionStateManager.get_value("generation_options")
        assert "force_generate" not in opties
        assert "force_duplicate" not in opties
        # Ongerelateerde opties blijven ongemoeid.
        assert opties["include_examples"] is True
        assert opties["model"] == "sonnet"

        assert SessionStateManager.get_value("trigger_auto_generation") is True
        mock_success.assert_called_once()
        assert nieuwe in str(mock_success.call_args)
        mock_rerun.assert_called_once()

    def test_deprecated_trigger_only_instructs(self, verse_sessiestate):
        """De bewaarde US-445-methode instrueert; ze voert niets uit."""
        renderer = CategoryRenderer()
        nieuwe = OntologischeCategorie.RESULTAAT.value

        with (
            patch.object(st, "info", create=True) as mock_info,
            patch.object(st, "rerun", create=True) as mock_rerun,
        ):
            renderer._trigger_regeneration_with_category(
                begrip="TestBegrip",
                new_category=nieuwe,
                old_category=OntologischeCategorie.TYPE.value,
                saved_record=None,
            )

        mock_info.assert_called_once()
        assert nieuwe in str(mock_info.call_args)
        # Geen state gezet en geen rerun: instructie, geen uitvoering.
        assert verse_sessiestate == {}
        mock_rerun.assert_not_called()

    def test_category_regeneration_helper_check(self, verse_sessiestate):
        """Helper levert het verzoek en consumeert het echt eenmalig."""
        test_data = {
            "begrip": "TestBegrip",
            "category": OntologischeCategorie.EXEMPLAAR.value,
            "feedback": "Test feedback",
        }
        SessionStateManager.set_value("regenerate_with_category", test_data)

        with patch.object(st, "info", create=True) as mock_info:
            eerste = CategoryRegenerationHelper.check_for_regeneration_request()
            tweede = CategoryRegenerationHelper.check_for_regeneration_request()

        assert eerste == test_data
        assert tweede is None
        assert "regenerate_with_category" not in verse_sessiestate
        mock_info.assert_called_once()

    def test_category_regeneration_helper_no_request(self, verse_sessiestate):
        """Zonder verzoek: geen resultaat, geen output, geen statewijziging."""
        verse_sessiestate["andere_sleutel"] = "blijft"

        with patch.object(st, "info", create=True) as mock_info:
            result = CategoryRegenerationHelper.check_for_regeneration_request()

        assert result is None
        mock_info.assert_not_called()
        assert verse_sessiestate == {"andere_sleutel": "blijft"}
