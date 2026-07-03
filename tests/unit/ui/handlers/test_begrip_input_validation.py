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
            "artikel 6:162 BW",  # wetsartikel-notatie met dubbele punt
            "3:15 BW",
            "P&O-beleid",
            "en/of-constructie",
            "(straf)recht",
            "identiteitsvaststelling, herhaald",
            "Militaire Ambtenarenwet 1931",
            "'s-Gravenhaags begrip",
            "’s-Gravenhaagse notatie",  # curly apostrof (U+2019)
            "café-exploitatie",
            "a" * 100,  # grens-geldig: exact de maximale lengte
        ],
    )
    def test_geldige_begrippen_passeren(self, begrip: str) -> None:
        assert validate_begrip_input(begrip) is None

    @pytest.mark.parametrize(
        ("begrip", "reden_fragment"),
        [
            ("", "voer eerst een begrip in"),
            ("   ", "voer eerst een begrip in"),
            (GAT_ROMMEL, "ongeldige tekens"),
            ("!!!", "minimaal één letter"),
            ("12345", "minimaal één letter"),
            ("×÷", "minimaal één letter"),  # U+00D7/U+00F7 zijn geen letters
            ("a×b", "ongeldige tekens"),  # × zit ook niet in de allowlist
            ("a" * 101, "te lang"),  # grens-ongeldig: net over het maximum
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

    def test_afwijzing_wordt_gelogd(self, caplog: pytest.LogCaptureFixture) -> None:
        handler = self._handler()
        with caplog.at_level(
            "WARNING", logger="ui.handlers.definition_generation_handler"
        ):
            handler.handle_definition_generation(
                GAT_ROMMEL, {}, _st=MagicMock(), _sm=MagicMock()
            )
        weigeringen = [r for r in caplog.records if "Generatie geweigerd" in r.message]
        assert len(weigeringen) == 1

    def test_duplicate_check_weigert_ongeldig_begrip(self) -> None:
        """Zusterpad (review #352): dezelfde gate geldt voor de duplicate-check."""
        handler = self._handler()
        mock_st = MagicMock()
        mock_st.error = Mock()

        handler.handle_duplicate_check(GAT_ROMMEL, {}, _st=mock_st, _sm=MagicMock())

        mock_st.error.assert_called_once()
        assert "ongeldige tekens" in mock_st.error.call_args[0][0]
        handler.checker.check_definitie.assert_not_called()
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
