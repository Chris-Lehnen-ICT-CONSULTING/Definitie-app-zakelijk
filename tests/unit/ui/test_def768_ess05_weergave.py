"""DEF-768 WP4: de weergave van ESS-05 zonder cijfer, met vraag, buren en herkomst.

Zuivere tekstfuncties van `validation_view` (geen Streamlit-sessie nodig):
de samenvatting heet 'AI-beoordeling' (niet 'bron'), de ene vraag, de
burenlijst met herkomst en bevestiging, modelvoorstellen als onbevestigd en
een afgewezen lege-ruimtebevestiging worden benoemd; het onderdeel draagt de
herkomst ('AI-beoordeling' of 'deskundige bevestiging').
"""

from __future__ import annotations

import pytest

from ui.components.validation_view import _HERKOMSTLABEL, _review_regels

pytestmark = [pytest.mark.unit]

REVIEW = {
    "assessment": {
        "status": "assessed",
        "applied": True,
        "model": "fake-model",
        "provider": "fake",
        "rejected": 0,
    },
    "neighbours": [
        {
            "id": "gebruiker:a",
            "term": "werknemer",
            "herkomst": "gebruiker",
            "bevestigd": True,
        },
        {
            "id": "repository:9",
            "term": "klant",
            "herkomst": "repository",
            "bevestigd": False,
        },
    ],
    "question": "Is ‘klant’ een verwant begrip dat deze definitie moet uitsluiten?",
    "proposals": [
        {"term": "borg", "herkomst": "model", "bevestigd": False, "reason": "r"}
    ],
    "empty_space_rejected": "bevestiging geldt niet meer",
}


def test_herkomstlabels_voor_ess05():
    assert _HERKOMSTLABEL["ess05_assessment"] == "AI-beoordeling"
    assert _HERKOMSTLABEL["ess05_empty_space"] == "deskundige bevestiging"


def test_reviewregels_noemen_vraag_buren_voorstellen_en_lege_ruimte():
    regels = _review_regels(REVIEW)
    tekst = "\n".join(regels)
    assert "🤖 AI-beoordeling toegepast (fake · fake-model)" in tekst
    assert "AI-bronbeoordeling" not in tekst
    assert "Vraag: Is ‘klant’" in tekst
    assert "werknemer (gebruiker, bevestigd)" in tekst
    assert "klant (repository, onbevestigd)" in tekst
    assert "Voorstel: borg (model, onbevestigd)" in tekst
    assert "bevestiging geldt niet meer" in tekst


def test_zonder_buren_wordt_dat_expliciet_gemeld():
    regels = _review_regels({"neighbours": [], "question": None, "proposals": []})
    assert any("geen verwante begrippen" in r for r in regels)
