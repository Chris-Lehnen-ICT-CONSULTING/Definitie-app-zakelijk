"""Regressietests DEF-553: begrip-invoervalidatie vóór generatie.

TC-GEN-03 toonde aan dat betekenisloze invoer (`asdf!@#$%^&*() zeer
langgggg...`) de volledige pipeline doorliep: quality-gate valid=True,
opgeslagen als concept. De quality-gate toetst alleen de gegenereerde
definitietekst, niet het begrip zelf. Fix: grens-validatie van het
begrip in de generation-handler — ongeldige invoer wordt afgewezen
met een duidelijke melding vóórdat er iets gegenereerd of opgeslagen
wordt.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from ui.handlers.definition_generation_handler import (
    DefinitionGenerationHandler,
    validate_begrip_input,
)

pytestmark = [pytest.mark.unit]

GAT_ROMMEL = "asdf!@#$%^&*() zeer langgggg..."


class TestValidateBegripInput:
    """Pure functie: geldige begrippen → None, ongeldige → afwijsreden."""

    @pytest.mark.parametrize(
        "begrip",
        [
            "overeenkomst",
            "e-mail",
            "ne bis in idem",
            "artikel 12-procedure",
            "P&O-beleid",
            "(straf)recht",
            "identiteitsvaststelling, herhaald",
            "Militaire Ambtenarenwet 1931",
            "'s-Gravenhaags begrip",
            "café-exploitatie",
        ],
    )
    def test_geldige_begrippen_passeren(self, begrip: str) -> None:
        assert validate_begrip_input(begrip) is None

    @pytest.mark.parametrize(
        ("begrip", "reden_fragment"),
        [
            ("", "begrip in"),
            ("   ", "begrip in"),
            (GAT_ROMMEL, "ongeldige tekens"),
            ("!!!", "letter"),
            ("12345", "letter"),
            ("a" * 101, "te lang"),
            ("begrip 💡", "ongeldige tekens"),
            ("<script>alert(1)</script>", "ongeldige tekens"),
        ],
    )
    def test_ongeldige_begrippen_worden_afgewezen(
        self, begrip: str, reden_fragment: str
    ) -> None:
        reden = validate_begrip_input(begrip)
        assert reden is not None, f"{begrip!r} had afgewezen moeten worden (DEF-553)"
        assert reden_fragment in reden


class TestHandlerWeigertOngeldigBegrip:
    """Handler: ongeldig begrip → melding, géén generatie, géén opslag."""

    def _handler(self) -> DefinitionGenerationHandler:
        return DefinitionGenerationHandler(
            checker=MagicMock(),
            definition_service=MagicMock(),
            repository=MagicMock(),
        )

    def test_rommel_begrip_blokkeert_voor_alle_services(self) -> None:
        handler = self._handler()
        mock_st = MagicMock()
        mock_st.error = Mock()
        mock_sm = MagicMock()

        handler.handle_definition_generation(
            GAT_ROMMEL,
            {"organisatorische_context": ["OM"]},
            _st=mock_st,
            _sm=mock_sm,
        )

        mock_st.error.assert_called_once()
        melding = mock_st.error.call_args[0][0]
        assert "ongeldige tekens" in melding
        # Geen generatie, geen duplicate-check, geen opslag (DEF-553)
        handler.definition_service.generate_definition.assert_not_called()
        handler.checker.check_definitie.assert_not_called()
        handler.repository.assert_not_called()
        mock_st.spinner.assert_not_called()

    def test_geldig_begrip_passeert_de_invoervalidatie(self) -> None:
        """Geldig begrip komt vóórbij de invoer-gate (strandt daarna pas
        op de klassieke classificatie-gate — bewijst dat de nieuwe check
        geldige invoer niet blokkeert)."""
        handler = self._handler()
        mock_st = MagicMock()
        mock_st.error = Mock()
        mock_sm = MagicMock()
        mock_sm.get_value = Mock(return_value=None)  # geen classificatie

        handler.handle_definition_generation(
            "overeenkomst",
            {"organisatorische_context": ["OM"]},
            _st=mock_st,
            _sm=mock_sm,
        )

        melding = mock_st.error.call_args[0][0]
        assert "Ontologische categorie" in melding  # de oude gate, niet de nieuwe
