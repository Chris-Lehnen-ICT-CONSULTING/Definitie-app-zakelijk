"""
Unit tests voor context afkortingen expansie in voorbeelden module.

Test dat afkortingen zoals ZM, OM, etc. correct worden geëxpandeerd
naar volledige namen in alle voorbeelden functies.
"""

from unittest.mock import Mock, patch

import pytest

from src.voorbeelden.voorbeelden import (
    _expand_context_abbreviations,
    genereer_praktijkvoorbeelden,
    genereer_tegenvoorbeelden,
    genereer_voorbeeld_zinnen,
)


class TestContextAbbreviationExpansion:
    """Test suite voor afkortingen expansie."""

    def test_expand_single_abbreviation(self):
        """Test dat een enkele afkorting correct wordt geëxpandeerd."""
        result = _expand_context_abbreviations(["ZM"])
        assert result == "ZM (Zittende Magistratuur)"

    def test_expand_multiple_abbreviations(self):
        """Test dat meerdere afkortingen correct worden geëxpandeerd."""
        result = _expand_context_abbreviations(["ZM", "OM"])
        assert "ZM (Zittende Magistratuur)" in result
        assert "OM (Openbaar Ministerie)" in result

    def test_expand_mixed_abbreviations_and_regular_text(self):
        """Test dat mix van afkortingen en reguliere tekst correct wordt verwerkt."""
        result = _expand_context_abbreviations(["ZM", "Strafrecht"])
        assert "ZM (Zittende Magistratuur)" in result
        assert "Strafrecht" in result

    def test_expand_no_abbreviations(self):
        """Test dat reguliere tekst zonder afkortingen ongewijzigd blijft."""
        result = _expand_context_abbreviations(["Strafrecht", "Civiel recht"])
        assert result == "Strafrecht, Civiel recht"

    def test_expand_empty_list(self):
        """Test dat lege lijst correct wordt afgehandeld."""
        result = _expand_context_abbreviations([])
        assert result == "geen"

    def test_expand_none_list(self):
        """Test dat None lijst correct wordt afgehandeld."""
        result = _expand_context_abbreviations(None)
        assert result == "geen"

    def test_all_known_abbreviations(self):
        """Test alle bekende afkortingen."""
        known_abbreviations = [
            "OM",
            "ZM",
            "3RO",
            "DJI",
            "NP",
            "FIOD",
            "Justid",
            "KMAR",
            "CJIB",
            "AVG",
        ]

        for abbr in known_abbreviations:
            result = _expand_context_abbreviations([abbr])
            assert abbr in result  # Afkorting zelf is aanwezig
            assert "(" in result  # Bevat uitleg tussen haakjes
            assert ")" in result

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_voorbeeld_zinnen_uses_expansion(self, mock_create):
        """Test dat genereer_voorbeeld_zinnen afkortingen expandeert in prompt."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Voorbeeld zin 1\nVoorbeeld zin 2"))
        ]
        mock_create.return_value = mock_response

        # Call functie met afkorting
        context_dict = {
            "organisatorisch": ["ZM"],
            "juridisch": ["Strafrecht"],
            "wettelijk": ["WvSv artikel 12"],
        }

        genereer_voorbeeld_zinnen("test begrip", "test definitie", context_dict)

        # Verify dat prompt de geëxpandeerde context bevat
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "ZM (Zittende Magistratuur)" in called_prompt
        assert "Strafrecht" in called_prompt  # Reguliere tekst blijft ongewijzigd

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_praktijkvoorbeelden_uses_expansion(self, mock_create):
        """Test dat genereer_praktijkvoorbeelden afkortingen expandeert in prompt."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="1. Voorbeeld 1\n2. Voorbeeld 2"))
        ]
        mock_create.return_value = mock_response

        # Call functie met afkorting
        context_dict = {
            "organisatorisch": ["OM", "ZM"],
            "juridisch": [],
            "wettelijk": [],
        }

        genereer_praktijkvoorbeelden(
            "test begrip", "test definitie", context_dict, aantal=2
        )

        # Verify dat prompt de geëxpandeerde context bevat
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "OM (Openbaar Ministerie)" in called_prompt
        assert "ZM (Zittende Magistratuur)" in called_prompt

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_tegenvoorbeelden_uses_expansion(self, mock_create):
        """Test dat genereer_tegenvoorbeelden afkortingen expandeert in prompt."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="1. Tegenvoorbeeld 1\n2. Tegenvoorbeeld 2"))
        ]
        mock_create.return_value = mock_response

        # Call functie met afkorting
        context_dict = {
            "organisatorisch": ["DJI"],
            "juridisch": [],
            "wettelijk": [],
        }

        genereer_tegenvoorbeelden(
            "test begrip", "test definitie", context_dict, aantal=2
        )

        # Verify dat prompt de geëxpandeerde context bevat
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "DJI (Dienst Justitiële Inrichtingen)" in called_prompt

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_expansion_with_multiple_context_types(self, mock_create):
        """Test dat expansie werkt voor alle context types (org, jur, wet)."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Voorbeeld"))]
        mock_create.return_value = mock_response

        # Call functie met afkortingen in alle context types
        context_dict = {
            "organisatorisch": ["ZM", "OM"],
            "juridisch": ["AVG"],  # AVG is ook een afkorting
            "wettelijk": ["WvSv"],
        }

        genereer_voorbeeld_zinnen("test begrip", "test definitie", context_dict)

        # Verify dat alle context types geëxpandeerd zijn
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "ZM (Zittende Magistratuur)" in called_prompt
        assert "OM (Openbaar Ministerie)" in called_prompt
        assert "AVG (Algemene verordening gegevensbescherming)" in called_prompt
        assert "WvSv" in called_prompt  # Niet-bekende afkorting blijft ongewijzigd


class TestSynoniemenAntonieменToelichting:
    """Test dat synoniemen, antoniemen en toelichting ook afkortingen expanderen."""

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_synoniemen_uses_expansion(self, mock_create):
        """Test dat genereer_synoniemen afkortingen expandeert in prompt."""
        # Mock OpenAI response
        from src.voorbeelden.voorbeelden import genereer_synoniemen

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="synoniem1\nsynoniem2"))]
        mock_create.return_value = mock_response

        # Call functie met afkorting
        context_dict = {
            "organisatorisch": ["KMAR"],
            "juridisch": [],
            "wettelijk": [],
        }

        genereer_synoniemen("test begrip", "test definitie", context_dict)

        # Verify dat prompt de geëxpandeerde context bevat
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "KMAR (Koninklijke Marechaussee)" in called_prompt

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_antoniemen_uses_expansion(self, mock_create):
        """Test dat genereer_antoniemen afkortingen expandeert in prompt."""
        # Mock OpenAI response
        from src.voorbeelden.voorbeelden import genereer_antoniemen

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="antoniem1\nantoniem2"))]
        mock_create.return_value = mock_response

        # Call functie met afkorting
        context_dict = {
            "organisatorisch": ["CJIB"],
            "juridisch": [],
            "wettelijk": [],
        }

        genereer_antoniemen("test begrip", "test definitie", context_dict)

        # Verify dat prompt de geëxpandeerde context bevat
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "CJIB (Centraal Justitieel Incassobureau)" in called_prompt

    @patch("src.voorbeelden.voorbeelden._client.chat.completions.create")
    def test_toelichting_uses_expansion(self, mock_create):
        """Test dat genereer_toelichting afkortingen expandeert in prompt."""
        # Mock OpenAI response
        from src.voorbeelden.voorbeelden import genereer_toelichting

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Dit is de toelichting."))]
        mock_create.return_value = mock_response

        # Call functie met afkorting
        context_dict = {
            "organisatorisch": ["FIOD"],
            "juridisch": ["AVG"],
            "wettelijk": [],
        }

        genereer_toelichting("test begrip", "test definitie", context_dict)

        # Verify dat prompt de geëxpandeerde context bevat
        called_prompt = mock_create.call_args[1]["messages"][0]["content"]
        assert "FIOD (Fiscale Inlichtingen- en Opsporingsdienst)" in called_prompt
        assert "AVG (Algemene verordening gegevensbescherming)" in called_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
