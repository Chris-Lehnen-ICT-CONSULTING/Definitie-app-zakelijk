"""DEF-622 besluit tekstvergelijking — de gedeelde renderer en zijn grenzen.

Chris' akkoord (14 september 2026): toon bij de definitie uitsluitend wanneer
de app de tekst ná generatie heeft gewijzigd exact
"De tekst is na generatie aangepast. Bekijk wijzigingen.", met een uitklapbare
vergelijking van de gegenereerde definitiekern vóór nabewerking en de
uiteindelijke tekst, toevoegingen/verwijderingen herkenbaar.

Grenzen uit dezelfde geautoriseerde vergelijking:
* geen melding bij ongewijzigde tekst;
* geen melding bij een historisch record zonder vóórtekst (geen verzonnen
  beginversie; het al opgeschoonde `definitie_origineel` is géén vóórtekst);
* geen melding wanneer de actuele tekst niet meer de generatie-eindtekst is
  (na generatie handmatig gewijzigd): een oude vergelijking wordt niet als
  wijziging van een andere actuele tekst getoond;
* modeltekst wordt letterlijk getoond (geen markdown/HTML-interpretatie).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ui.components.tekstwijziging import (
    MELDING_TEKST_AANGEPAST,
    Tekstwijziging,
    render_tekstwijziging,
    tekstwijziging_uit_bewijs,
    woordverschil,
)

pytestmark = [pytest.mark.unit]

KERN = "Handeling die door een toezichthouder wordt verricht"
EIND = "Handeling die door een bevoegde toezichthouder wordt verricht."


def _bewijs(**extra):
    bewijs = {
        "definitie_kern_geextraheerd": KERN,
        "definitie_eindtekst": EIND,
        "tekst_na_generatie_aangepast": True,
    }
    bewijs.update(extra)
    return bewijs


def test_gewijzigde_tekst_geeft_een_vergelijking():
    wijziging = tekstwijziging_uit_bewijs(_bewijs(), actuele_tekst=EIND)
    assert wijziging == Tekstwijziging(kern_voor=KERN, tekst_na=EIND)


def test_ongewijzigde_tekst_geeft_geen_melding():
    bewijs = _bewijs(
        definitie_eindtekst=KERN + ".",
        tekst_na_generatie_aangepast=False,
    )
    assert tekstwijziging_uit_bewijs(bewijs, actuele_tekst=KERN + ".") is None


@pytest.mark.parametrize(
    "bewijs",
    [
        None,
        {},
        {"prompt": "…", "model": "x"},
        {
            "definitie_origineel": "Al opgeschoonde tekst.",
            "tekst_na_generatie_aangepast": True,
        },
    ],
    ids=["geen-bewijs", "leeg", "alleen-prompt", "alleen-opgeschoond-origineel"],
)
def test_historisch_record_zonder_voortekst_geeft_geen_melding(bewijs):
    """Geen verzonnen beginversie: zonder de echte geëxtraheerde kern is er
    niets te vergelijken — ook niet met het al opgeschoonde `definitie_origineel`."""
    assert tekstwijziging_uit_bewijs(bewijs, actuele_tekst=EIND) is None


def test_stale_bewijs_na_handmatige_wijziging_geeft_geen_melding():
    """Is de actuele tekst niet meer de generatie-eindtekst, dan hoort de oude
    vergelijking niet bij wat de gebruiker nu ziet."""
    assert (
        tekstwijziging_uit_bewijs(
            _bewijs(), actuele_tekst="Handeling die de expert zelf herschreef."
        )
        is None
    )


def test_woordverschil_markeert_toevoegingen_en_verwijderingen():
    verschil = woordverschil(
        "controle die binnen Team Koper wordt uitgevoerd",
        "Controle die wordt uitgevoerd.",
    )
    assert ("-", "controle") in verschil and ("+", "Controle") in verschil
    assert ("-", "binnen") in verschil and ("-", "Team") in verschil
    assert ("-", "Koper") in verschil
    assert ("=", "die") in verschil and ("=", "wordt") in verschil
    assert ("-", "uitgevoerd") in verschil and ("+", "uitgevoerd.") in verschil


def test_renderer_toont_exacte_melding_en_letterlijke_tekst():
    st = MagicMock()
    st.expander.return_value.__enter__ = lambda s: s
    st.expander.return_value.__exit__ = lambda s, *a: False
    adversarieel = Tekstwijziging(
        kern_voor="<script>alert(1)</script> **kern** _die_ [x](y)",
        tekst_na="<b>eind</b> **kern** die.",
    )

    getoond = render_tekstwijziging(adversarieel, _st=st)

    assert getoond is True
    st.warning.assert_called_once_with(MELDING_TEKST_AANGEPAST)
    assert (
        MELDING_TEKST_AANGEPAST
        == "De tekst is na generatie aangepast. Bekijk wijzigingen."
    )
    st.expander.assert_called_once()
    # Modeltekst gaat uitsluitend door `st.text` (letterlijk); nooit door
    # markdown/html/write, waar '<script>' of '**' geïnterpreteerd zou worden.
    letterlijk = "\n".join(str(c.args[0]) for c in st.text.call_args_list)
    assert "<script>alert(1)</script> **kern** _die_ [x](y)" in letterlijk
    assert "<b>eind</b> **kern** die." in letterlijk
    assert "- <script>alert(1)</script>" in letterlijk
    assert "+ <b>eind</b>" in letterlijk
    for api in ("markdown", "html", "write", "info", "success"):
        for aanroep in getattr(st, api).call_args_list:
            assert "<script>" not in " ".join(map(str, aanroep.args))
            assert "**kern**" not in " ".join(map(str, aanroep.args))


def test_renderer_toont_niets_zonder_wijziging():
    st = MagicMock()
    assert render_tekstwijziging(None, _st=st) is False
    st.warning.assert_not_called()
    st.expander.assert_not_called()
    st.text.assert_not_called()
