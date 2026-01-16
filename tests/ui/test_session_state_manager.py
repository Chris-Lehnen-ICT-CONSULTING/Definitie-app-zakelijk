"""
Tests for SessionStateManager - DEF-225

Comprehensive test coverage for the centralized session state management.
Target: 80%+ coverage for src/ui/session_state.py

Refactored with:
- Shared fixtures from conftest.py (eliminates 7x duplicate fixture code)
- Parametrized tests for type variations
- Edge case tests for defensive behavior
"""

from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# Core Operations Tests
# =============================================================================


class TestSessionStateManagerCore:
    """Tests for core get/set/clear operations."""

    # =========================================================================
    # get_value tests
    # =========================================================================

    def test_get_value_returns_existing_value(self, mock_streamlit_session):
        """get_value returns stored value when key exists."""
        mock_streamlit_session.session_state["test_key"] = "test_value"
        result = mock_streamlit_session.manager.get_value("test_key")
        assert result == "test_value"

    def test_get_value_returns_default_when_key_missing(self, mock_streamlit_session):
        """get_value returns default when key doesn't exist."""
        result = mock_streamlit_session.manager.get_value(
            "nonexistent", "default_value"
        )
        assert result == "default_value"

    def test_get_value_returns_none_when_no_default(self, mock_streamlit_session):
        """get_value returns None when key missing and no default given."""
        result = mock_streamlit_session.manager.get_value("nonexistent")
        assert result is None

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("empty_string", ""),
            ("zero", 0),
            ("false", False),
            ("empty_list", []),
        ],
    )
    def test_get_value_returns_falsy_values_correctly(
        self, mock_streamlit_session, key, value
    ):
        """get_value distinguishes between falsy values and missing keys."""
        mock_streamlit_session.session_state[key] = value
        assert mock_streamlit_session.manager.get_value(key) == value

    def test_get_value_with_complex_types(self, mock_streamlit_session):
        """get_value works with dict, list, nested structures."""
        complex_value = {"nested": {"data": [1, 2, 3]}}
        mock_streamlit_session.session_state["complex"] = complex_value
        assert mock_streamlit_session.manager.get_value("complex") == complex_value

    # =========================================================================
    # set_value tests (parametrized)
    # =========================================================================

    @pytest.mark.parametrize(
        ("key", "value", "description"),
        [
            ("key", "value", "string"),
            ("number", 42, "integer"),
            ("float_key", 3.14, "float"),
            ("list_key", [1, 2, 3], "list"),
            ("dict_key", {"a": 1, "b": 2}, "dict"),
            ("nullable", None, "None"),
            ("bool_key", True, "boolean"),
        ],
    )
    def test_set_value_stores_various_types(
        self, mock_streamlit_session, key, value, description
    ):
        """set_value stores {description} values correctly."""
        mock_streamlit_session.manager.set_value(key, value)
        assert mock_streamlit_session.session_state[key] == value

    def test_set_value_overwrites_existing(self, mock_streamlit_session):
        """set_value overwrites existing values."""
        mock_streamlit_session.session_state["key"] = "old"
        mock_streamlit_session.manager.set_value("key", "new")
        assert mock_streamlit_session.session_state["key"] == "new"

    # =========================================================================
    # clear_value tests
    # =========================================================================

    def test_clear_value_removes_existing_key(self, mock_streamlit_session):
        """clear_value removes key from session state."""
        mock_streamlit_session.session_state["to_delete"] = "value"
        mock_streamlit_session.manager.clear_value("to_delete")
        assert "to_delete" not in mock_streamlit_session.session_state

    def test_clear_value_noop_for_missing_key(self, mock_streamlit_session):
        """clear_value does nothing for non-existent keys."""
        mock_streamlit_session.manager.clear_value("nonexistent")
        assert "nonexistent" not in mock_streamlit_session.session_state

    def test_clear_value_only_removes_specified_key(self, mock_streamlit_session):
        """clear_value only removes the specified key, not others."""
        mock_streamlit_session.session_state["keep"] = "value1"
        mock_streamlit_session.session_state["delete"] = "value2"
        mock_streamlit_session.manager.clear_value("delete")
        assert "keep" in mock_streamlit_session.session_state
        assert "delete" not in mock_streamlit_session.session_state


# =============================================================================
# Definition Results Tests
# =============================================================================


class TestSessionStateManagerDefinitionResults:
    """Tests for definition result management methods."""

    def test_update_definition_results_sets_all_fields(self, mock_streamlit_session):
        """update_definition_results sets all definition fields."""
        mock_streamlit_session.manager.update_definition_results(
            definitie_origineel="original",
            definitie_gecorrigeerd="corrected",
            marker="TYPE",
            beoordeling_gen=["good", "quality"],
        )

        assert mock_streamlit_session.session_state["definitie_origineel"] == "original"
        assert (
            mock_streamlit_session.session_state["definitie_gecorrigeerd"]
            == "corrected"
        )
        assert mock_streamlit_session.session_state["gegenereerd"] == "original"
        assert mock_streamlit_session.session_state["marker"] == "TYPE"
        assert mock_streamlit_session.session_state["beoordeling_gen"] == [
            "good",
            "quality",
        ]

    def test_update_definition_results_without_beoordeling(
        self, mock_streamlit_session
    ):
        """update_definition_results works without beoordeling_gen."""
        mock_streamlit_session.manager.update_definition_results(
            definitie_origineel="original",
            definitie_gecorrigeerd="corrected",
        )

        assert mock_streamlit_session.session_state["definitie_origineel"] == "original"
        assert (
            mock_streamlit_session.session_state["definitie_gecorrigeerd"]
            == "corrected"
        )
        assert "beoordeling_gen" not in mock_streamlit_session.session_state

    def test_update_definition_results_with_empty_list_does_not_update(
        self, mock_streamlit_session
    ):
        """update_definition_results with empty beoordeling_gen=[] does NOT update (truthy check)."""
        mock_streamlit_session.session_state["beoordeling_gen"] = ["existing"]
        mock_streamlit_session.manager.update_definition_results(
            definitie_origineel="original",
            definitie_gecorrigeerd="corrected",
            beoordeling_gen=[],
        )
        assert mock_streamlit_session.session_state["beoordeling_gen"] == ["existing"]

    def test_has_generated_definition_true_when_exists(self, mock_streamlit_session):
        """has_generated_definition returns True when valid definition exists."""
        mock_streamlit_session.session_state["definitie_gecorrigeerd"] = (
            "A valid definition"
        )
        assert mock_streamlit_session.manager.has_generated_definition() is True

    @pytest.mark.parametrize(
        ("value", "reason"),
        [
            ("", "empty string"),
            ("ab", "too short (2 chars)"),
            ("   ", "whitespace only"),
            ("  a  ", "single char with whitespace"),
        ],
    )
    def test_has_generated_definition_false_for_invalid_values(
        self, mock_streamlit_session, value, reason
    ):
        """has_generated_definition returns False for {reason}."""
        mock_streamlit_session.session_state["definitie_gecorrigeerd"] = value
        assert mock_streamlit_session.manager.has_generated_definition() is False

    def test_has_generated_definition_false_when_missing(self, mock_streamlit_session):
        """has_generated_definition returns False when key doesn't exist."""
        assert mock_streamlit_session.manager.has_generated_definition() is False

    @pytest.mark.parametrize(
        ("value", "description"),
        [
            (12345, "integer"),
            (["a", "b", "c"], "list"),
            ({"key": "value"}, "dict"),
            (None, "None"),
        ],
    )
    def test_has_generated_definition_false_for_non_string_types(
        self, mock_streamlit_session, value, description
    ):
        """has_generated_definition returns False for {description} (isinstance check)."""
        mock_streamlit_session.session_state["definitie_gecorrigeerd"] = value
        assert mock_streamlit_session.manager.has_generated_definition() is False

    def test_clear_definition_results_resets_all_fields(self, mock_streamlit_session):
        """clear_definition_results resets all definition-related fields."""
        mock_streamlit_session.session_state["definitie_origineel"] = "original"
        mock_streamlit_session.session_state["definitie_gecorrigeerd"] = "corrected"
        mock_streamlit_session.session_state["gegenereerd"] = "generated"
        mock_streamlit_session.session_state["marker"] = "TYPE"
        mock_streamlit_session.session_state["beoordeling_gen"] = ["test"]

        mock_streamlit_session.manager.clear_definition_results()

        assert mock_streamlit_session.session_state["definitie_origineel"] == ""
        assert mock_streamlit_session.session_state["definitie_gecorrigeerd"] == ""
        assert mock_streamlit_session.session_state["gegenereerd"] == ""
        assert mock_streamlit_session.session_state["marker"] == ""
        assert mock_streamlit_session.session_state["beoordeling_gen"] == []

    def test_clear_definition_results_with_partial_state(self, mock_streamlit_session):
        """clear_definition_results handles partial state (only some keys exist)."""
        mock_streamlit_session.session_state["definitie_origineel"] = "original"
        mock_streamlit_session.session_state["marker"] = "TYPE"

        mock_streamlit_session.manager.clear_definition_results()

        assert mock_streamlit_session.session_state["definitie_origineel"] == ""
        assert mock_streamlit_session.session_state["marker"] == ""

    def test_clear_definition_results_with_empty_state(self, mock_streamlit_session):
        """clear_definition_results handles completely empty state."""
        mock_streamlit_session.manager.clear_definition_results()


# =============================================================================
# AI Content Tests
# =============================================================================


class TestSessionStateManagerAIContent:
    """Tests for AI content update methods."""

    def test_update_ai_content_sets_all_fields(self, mock_streamlit_session):
        """update_ai_content sets all AI-generated fields."""
        mock_streamlit_session.manager.update_ai_content(
            voorbeeld_zinnen=["zin1", "zin2"],
            praktijkvoorbeelden=["pv1"],
            tegenvoorbeelden=["tv1"],
            toelichting="uitleg",
            synoniemen="syn1, syn2",
            antoniemen="ant1",
            bronnen_gebruikt="bron1\nbron2",
        )

        assert mock_streamlit_session.session_state["voorbeeld_zinnen"] == [
            "zin1",
            "zin2",
        ]
        assert mock_streamlit_session.session_state["praktijkvoorbeelden"] == ["pv1"]
        assert mock_streamlit_session.session_state["tegenvoorbeelden"] == ["tv1"]
        assert mock_streamlit_session.session_state["toelichting"] == "uitleg"
        assert mock_streamlit_session.session_state["synoniemen"] == "syn1, syn2"
        assert mock_streamlit_session.session_state["antoniemen"] == "ant1"
        assert (
            mock_streamlit_session.session_state["bronnen_gebruikt"] == "bron1\nbron2"
        )

    def test_update_ai_content_partial_update(self, mock_streamlit_session):
        """update_ai_content only updates provided fields."""
        mock_streamlit_session.session_state["voorbeeld_zinnen"] = ["original"]

        mock_streamlit_session.manager.update_ai_content(synoniemen="new_syn")

        assert mock_streamlit_session.session_state["voorbeeld_zinnen"] == ["original"]
        assert mock_streamlit_session.session_state["synoniemen"] == "new_syn"

    def test_update_ai_content_skips_none_values(self, mock_streamlit_session):
        """update_ai_content doesn't update fields with None values."""
        mock_streamlit_session.session_state["toelichting"] = "existing"

        mock_streamlit_session.manager.update_ai_content(toelichting=None)

        assert mock_streamlit_session.session_state["toelichting"] == "existing"

    def test_update_ai_content_skips_empty_lists(self, mock_streamlit_session):
        """update_ai_content doesn't update with empty lists."""
        mock_streamlit_session.session_state["voorbeeld_zinnen"] = ["existing"]

        mock_streamlit_session.manager.update_ai_content(voorbeeld_zinnen=[])

        assert mock_streamlit_session.session_state["voorbeeld_zinnen"] == ["existing"]

    def test_update_ai_content_empty_string_does_not_update(
        self, mock_streamlit_session
    ):
        """update_ai_content with empty string "" does NOT update (falsy check)."""
        mock_streamlit_session.session_state["toelichting"] = "existing"
        mock_streamlit_session.session_state["synoniemen"] = "existing_syn"

        mock_streamlit_session.manager.update_ai_content(toelichting="", synoniemen="")

        assert mock_streamlit_session.session_state["toelichting"] == "existing"
        assert mock_streamlit_session.session_state["synoniemen"] == "existing_syn"

    def test_update_ai_content_whitespace_string_updates(self, mock_streamlit_session):
        """update_ai_content with whitespace " " DOES update (truthy)."""
        mock_streamlit_session.session_state["toelichting"] = "existing"

        mock_streamlit_session.manager.update_ai_content(toelichting="   ")

        assert mock_streamlit_session.session_state["toelichting"] == "   "


# =============================================================================
# Export Data Tests
# =============================================================================


class TestSessionStateManagerExportData:
    """Tests for export data retrieval."""

    def test_get_export_data_returns_complete_structure(self, mock_streamlit_session):
        """get_export_data returns all expected fields."""
        mock_streamlit_session.session_state["begrip"] = "test_term"
        mock_streamlit_session.session_state["definitie_gecorrigeerd"] = "test_def"
        mock_streamlit_session.session_state["definitie_origineel"] = "original_def"
        mock_streamlit_session.session_state["marker"] = "TYPE"
        mock_streamlit_session.session_state["beoordeling_gen"] = ["pass"]
        mock_streamlit_session.session_state["bronnen_gebruikt"] = "bron1\nbron2"

        with patch.object(
            mock_streamlit_session.manager,
            "get_context_dict",
            return_value={
                "organisatorisch": ["OM"],
                "juridisch": ["Strafrecht"],
                "wettelijk": [],
            },
        ):
            result = mock_streamlit_session.manager.get_export_data()

        assert result["begrip"] == "test_term"
        assert result["definitie_gecorrigeerd"] == "test_def"
        assert result["definitie_origineel"] == "original_def"
        assert result["metadata"]["marker"] == "TYPE"
        assert result["toetsresultaten"] == ["pass"]
        assert result["bronnen"] == ["bron1", "bron2"]

    def test_get_export_data_handles_missing_values(self, mock_streamlit_session):
        """get_export_data handles missing session state gracefully."""
        with patch.object(
            mock_streamlit_session.manager,
            "get_context_dict",
            return_value={"organisatorisch": [], "juridisch": [], "wettelijk": []},
        ):
            result = mock_streamlit_session.manager.get_export_data()

        assert result["begrip"] == ""
        assert result["definitie_gecorrigeerd"] == ""
        assert result["bronnen"] == []


# =============================================================================
# Initialization Tests
# =============================================================================


class TestSessionStateManagerInitialization:
    """Tests for session state initialization."""

    @pytest.mark.parametrize(
        "expected_key",
        [
            "gegenereerd",
            "beoordeling_gen",
            "aangepaste_definitie",
            "voorbeeld_zinnen",
            "praktijkvoorbeelden",
            "tegenvoorbeelden",
            "toelichting",
            "synoniemen",
            "antoniemen",
            "editing_definition_id",
        ],
    )
    def test_default_values_contains_key(self, mock_streamlit_session, expected_key):
        """DEFAULT_VALUES contains the expected key: {expected_key}."""
        assert expected_key in mock_streamlit_session.manager.DEFAULT_VALUES

    def test_initialize_session_state_sets_defaults(self, mock_streamlit_session):
        """initialize_session_state sets all default values."""
        with patch("ui.cached_services.initialize_services_once"):
            mock_streamlit_session.manager.initialize_session_state()

        assert "gegenereerd" in mock_streamlit_session.session_state
        assert mock_streamlit_session.session_state["gegenereerd"] == ""
        assert mock_streamlit_session.session_state["beoordeling_gen"] == []

    def test_initialize_session_state_preserves_existing(self, mock_streamlit_session):
        """initialize_session_state doesn't overwrite existing values."""
        mock_streamlit_session.session_state["gegenereerd"] = "existing_value"

        with patch("ui.cached_services.initialize_services_once"):
            mock_streamlit_session.manager.initialize_session_state()

        assert mock_streamlit_session.session_state["gegenereerd"] == "existing_value"


# =============================================================================
# Force Cleanup Voorbeelden Tests
# =============================================================================


class TestForceCleanupVoorbeelden:
    """Tests for force_cleanup_voorbeelden function."""

    @pytest.mark.parametrize(
        "suffix",
        [
            "_vz_edit",
            "_pv_edit",
            "_tv_edit",
            "_syn_edit",
            "_ant_edit",
            "_tol_edit",
            "_examples",
        ],
    )
    def test_cleanup_removes_voorbeelden_key_by_suffix(
        self, mock_streamlit_cleanup, suffix
    ):
        """force_cleanup_voorbeelden removes key with suffix {suffix}."""
        cleanup_func, session_state = mock_streamlit_cleanup
        key = f"edit_106{suffix}"
        session_state[key] = "value"
        session_state["other_key"] = "keep"

        cleanup_func("edit_106")

        assert key not in session_state
        assert session_state["other_key"] == "keep"

    def test_cleanup_handles_empty_state(self, mock_streamlit_cleanup):
        """force_cleanup_voorbeelden handles empty session state."""
        cleanup_func, session_state = mock_streamlit_cleanup
        cleanup_func("edit_999")
        assert len(session_state) == 0

    def test_cleanup_only_affects_matching_prefix(self, mock_streamlit_cleanup):
        """force_cleanup_voorbeelden only affects keys with matching prefix."""
        cleanup_func, session_state = mock_streamlit_cleanup
        session_state["edit_100_vz_edit"] = "def100"
        session_state["edit_200_vz_edit"] = "def200"

        cleanup_func("edit_100")

        assert "edit_100_vz_edit" not in session_state
        assert session_state["edit_200_vz_edit"] == "def200"

    def test_cleanup_preserves_non_voorbeelden_keys(self, mock_streamlit_cleanup):
        """force_cleanup_voorbeelden preserves keys without voorbeelden indicators."""
        cleanup_func, session_state = mock_streamlit_cleanup
        session_state["edit_106_vz_edit"] = "delete_me"
        session_state["edit_106_other"] = "keep_me"
        session_state["edit_106_data"] = "keep_me_too"

        cleanup_func("edit_106")

        assert "edit_106_vz_edit" not in session_state
        assert session_state["edit_106_other"] == "keep_me"
        assert session_state["edit_106_data"] == "keep_me_too"


# =============================================================================
# Context Dict Tests
# =============================================================================


class TestSessionStateManagerContextDict:
    """Tests for get_context_dict method."""

    def test_get_context_dict_fallback_on_adapter_error(self, mock_streamlit_session):
        """get_context_dict falls back to legacy when adapter fails."""
        # DEF-252: Use correct session state keys matching ContextManager
        mock_streamlit_session.session_state["organisatorische_context"] = ["OM"]
        mock_streamlit_session.session_state["juridische_context"] = ["Strafrecht"]
        mock_streamlit_session.session_state["wettelijke_basis"] = ["WvSv"]

        # DEF-252: Use specific exception type (not generic Exception)
        with patch(
            "ui.helpers.context_adapter.get_context_adapter",
            side_effect=AttributeError("Test error"),
        ):
            result = mock_streamlit_session.manager.get_context_dict()

        assert result["organisatorisch"] == ["OM"]
        assert result["juridisch"] == ["Strafrecht"]
        assert result["wettelijk"] == ["WvSv"]

    def test_get_context_dict_uses_adapter_when_available(self, mock_streamlit_session):
        """get_context_dict uses adapter when available."""
        mock_adapter = MagicMock()
        # Fixed: method was renamed from to_generation_request to get_merged_context
        mock_adapter.get_merged_context.return_value = {
            "organisatorische_context": ["DJI"],
            "juridische_context": ["Civiel"],
            "wettelijke_basis": ["BW"],
        }

        with patch(
            "ui.helpers.context_adapter.get_context_adapter",
            return_value=mock_adapter,
        ):
            result = mock_streamlit_session.manager.get_context_dict()

        assert result["organisatorisch"] == ["DJI"]
        assert result["juridisch"] == ["Civiel"]
        assert result["wettelijk"] == ["BW"]

    def test_get_context_dict_with_missing_keys_in_adapter_response(
        self, mock_streamlit_session
    ):
        """get_context_dict handles incomplete adapter response (.get() fallback)."""
        mock_adapter = MagicMock()
        # Fixed: method was renamed from to_generation_request to get_merged_context
        mock_adapter.get_merged_context.return_value = {
            "organisatorische_context": ["DJI"],
        }

        with patch(
            "ui.helpers.context_adapter.get_context_adapter",
            return_value=mock_adapter,
        ):
            result = mock_streamlit_session.manager.get_context_dict()

        assert result["organisatorisch"] == ["DJI"]
        assert result["juridisch"] == []
        assert result["wettelijk"] == []

    def test_get_context_dict_with_empty_adapter_response(self, mock_streamlit_session):
        """get_context_dict handles empty adapter response."""
        mock_adapter = MagicMock()
        # Fixed: method was renamed from to_generation_request to get_merged_context
        mock_adapter.get_merged_context.return_value = {}

        with patch(
            "ui.helpers.context_adapter.get_context_adapter",
            return_value=mock_adapter,
        ):
            result = mock_streamlit_session.manager.get_context_dict()

        assert result["organisatorisch"] == []
        assert result["juridisch"] == []
        assert result["wettelijk"] == []
