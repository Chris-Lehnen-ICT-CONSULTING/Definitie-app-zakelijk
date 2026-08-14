"""Eén gedeelde contextnormalisatie (DEF-672, vervroegd uit DEF-622).

Context is en blijft gestructureerde metadata naast de definitie. De
normalisatie hier bepaalt wanneer twee contextverzamelingen *dezelfde* context
zijn, en wordt gedeeld door de opslag en de duplicaatvergelijking.

Twee vormen, één regelset:

- `canoniseer_contextlijst` levert de vorm die wordt **opgeslagen**: getrimd,
  zonder lege waarden, ontdubbeld en deterministisch gesorteerd — met de
  oorspronkelijke schrijfwijze intact, want `DJI`, `OM` en `KMAR` zijn
  eigennamen die in de UI leesbaar moeten blijven.
- `contextsleutel` levert de **vergelijkingssleutel**: dezelfde vorm, Unicode
  gecasefold. Dat maakt de vergelijking hoofdletter-, whitespace-, volgorde- en
  duplicaat-onafhankelijk zonder dat de opslag onleesbaar wordt.

Geen aliasmapping in deze wijziging: `DJI` en `Dienst Justitiële Inrichtingen`
blijven verschillende contextwaarden.
"""

from __future__ import annotations

import pytest

from domain.context.normalisatie import (
    canoniseer_contextlijst,
    contextsleutel,
)

pytestmark = [pytest.mark.unit]


class TestCanoniekeVorm:
    """De opgeslagen vorm: opgeruimd, maar leesbaar."""

    def test_trimt_whitespace(self):
        assert canoniseer_contextlijst(["  DJI  ", "\tOM\n"]) == ["DJI", "OM"]

    def test_verwijdert_lege_waarden(self):
        assert canoniseer_contextlijst(["DJI", "", "   ", None]) == ["DJI"]

    def test_ontdubbelt_hoofdletteronafhankelijk(self):
        # Twee schrijfwijzen van dezelfde context zijn één waarde.
        assert canoniseer_contextlijst(["DJI", "dji", " Dji "]) == ["DJI"]

    def test_eerste_schrijfwijze_blijft_staan(self):
        # Bewust: de opslag mag niet casefolden, want dan wordt "DJI" in de UI
        # "dji". De vergelijking casefoldt wél (zie contextsleutel).
        assert canoniseer_contextlijst(["dji", "DJI"]) == ["dji"]

    def test_sorteert_deterministisch_en_volgorde_onafhankelijk(self):
        een = canoniseer_contextlijst(["strafrecht", "Awb", "DJI"])
        twee = canoniseer_contextlijst(["DJI", "strafrecht", "Awb"])
        assert een == twee
        assert een == ["Awb", "DJI", "strafrecht"]

    def test_is_idempotent(self):
        eenmaal = canoniseer_contextlijst([" OM ", "dji", "OM"])
        assert canoniseer_contextlijst(eenmaal) == eenmaal

    @pytest.mark.parametrize("leeg", [None, [], (), ""])
    def test_lege_invoer_levert_lege_lijst(self, leeg):
        assert canoniseer_contextlijst(leeg) == []


class TestVergelijkingssleutel:
    """De sleutel: gelijk voor alles wat dezelfde context betekent."""

    def test_hoofdletters_maken_geen_verschil(self):
        assert contextsleutel(["DJI"]) == contextsleutel(["dji"])

    def test_volgorde_maakt_geen_verschil(self):
        assert contextsleutel(["DJI", "OM"]) == contextsleutel(["OM", "DJI"])

    def test_whitespace_maakt_geen_verschil(self):
        assert contextsleutel(["  DJI "]) == contextsleutel(["DJI"])

    def test_duplicaten_maken_geen_verschil(self):
        assert contextsleutel(["DJI", "DJI", "dji"]) == contextsleutel(["DJI"])

    def test_lege_waarden_maken_geen_verschil(self):
        assert contextsleutel(["DJI", "", None, "  "]) == contextsleutel(["DJI"])

    def test_alle_vier_variaties_tegelijk(self):
        rommelig = ["  om ", "DJI", "dji", "", None, "OM"]
        assert contextsleutel(rommelig) == contextsleutel(["DJI", "OM"])

    def test_verschillende_context_verschilt(self):
        assert contextsleutel(["DJI"]) != contextsleutel(["OM"])

    def test_deelverzameling_is_niet_gelijk(self):
        # Identiteit is de hele verzameling, niet een overlap.
        assert contextsleutel(["DJI"]) != contextsleutel(["DJI", "OM"])

    def test_unicode_casefold_niet_alleen_lower(self):
        # casefold() vouwt de Duitse scherpe s naar 'ss'; lower() doet dat niet.
        # Zonder casefold zou deze assertie falen.
        assert contextsleutel(["STRASSE"]) == contextsleutel(["Straße"])

    def test_sleutel_is_hashbaar_en_vergelijkbaar(self):
        # De sleutel wordt als dict-/set-lid gebruikt in de duplicaatcontrole.
        assert {contextsleutel(["DJI"]): 1}[contextsleutel(["dji"])] == 1

    def test_geen_aliasmapping(self):
        # Expliciet buiten scope van deze wijziging; zou een alias wél worden
        # gemapt, dan verandert de duplicaatidentiteit stilzwijgend.
        assert contextsleutel(["DJI"]) != contextsleutel(
            ["Dienst Justitiële Inrichtingen"]
        )


class TestSleutelVolgtDeCanoniekeVorm:
    """Eén regelset: de sleutel is de gecasefolde canonieke vorm."""

    @pytest.mark.parametrize(
        "waarden",
        [
            ["DJI", "OM"],
            ["  strafrecht", "Awb", "awb"],
            [],
            ["Straße", "STRASSE"],
        ],
    )
    def test_sleutel_is_casefold_van_canoniek(self, waarden):
        verwacht = tuple(
            sorted(waarde.casefold() for waarde in canoniseer_contextlijst(waarden))
        )
        assert contextsleutel(waarden) == verwacht
