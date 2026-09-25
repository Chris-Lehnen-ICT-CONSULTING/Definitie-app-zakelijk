"""DEF-768 WP4: de expertacties op de ESS-05-burenlijst, zuiver en zonder UI.

Bevestigen, afwijzen (met grond), een buur toevoegen, een modelvoorstel
overnemen en een lege vergelijkingsruimte bevestigen leveren een nieuwe
opgeslagen burenlijst of bevestiging op; de invoer wordt nooit gemuteerd.
Elk besluit draagt actor en tijdstip; een afwijzing en een lege ruimte
vereisen een grond. De bevestigingsstatus valt buiten de vingerafdruk: een
besluit vraagt geen nieuwe modelaanroep.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from domain.ess05.contract import (
    CONTRACTVERSIE,
    OngeldigeBurenlijstError,
    bereken_ess05_vingerafdruk,
    lege_ruimte_geldig,
    normaliseer_buren,
    stel_burenlijst_samen,
)
from domain.ess05.expertacties import (
    bevestig_buur,
    bevestig_lege_ruimte,
    neem_voorstel_over,
    voeg_buur_toe,
    wijs_buur_af,
)

pytestmark = [pytest.mark.unit]

AT = "2026-09-23T12:00:00+00:00"
OPGESLAGEN = [
    {
        "id": "gebruiker:werknemer",
        "term": "werknemer",
        "definitie": "Persoon met een arbeidsovereenkomst.",
        "herkomst": "gebruiker",
        "bevestigd": True,
    }
]
REPOSITORYBUUR = {
    "id": "repository:9",
    "term": "klant",
    "definitie": "Persoon die iets afneemt.",
    "herkomst": "repository",
    "bevestigd": False,
}
ACTIEF = [OPGESLAGEN[0], REPOSITORYBUUR]


def test_bevestigen_van_een_repositorybuur_legt_een_besluit_vast():
    voor = deepcopy(OPGESLAGEN)
    na = bevestig_buur(OPGESLAGEN, ACTIEF, "repository:9", actor="deskundige", at=AT)
    assert voor == OPGESLAGEN
    besluit = next(b for b in na if b["id"] == "repository:9")
    assert besluit["bevestigd"] is True
    assert (besluit["actor"], besluit["at"]) == ("deskundige", AT)
    actief, _ = stel_burenlijst_samen(
        na, [{"id": 9, "begrip": "klant", "definitie": "x"}]
    )
    assert {b.id: b.bevestigd for b in actief}["repository:9"] is True


def test_afwijzen_vereist_grond_en_haalt_de_buur_uit_de_actieve_lijst():
    with pytest.raises(ValueError, match="grond"):
        wijs_buur_af(OPGESLAGEN, ACTIEF, "repository:9", actor="d", at=AT, grond=" ")
    na = wijs_buur_af(
        OPGESLAGEN, ACTIEF, "repository:9", actor="d", at=AT, grond="Geen rol hier."
    )
    actief, afgewezen = stel_burenlijst_samen(
        na, [{"id": 9, "begrip": "klant", "definitie": "x"}]
    )
    assert [b.term for b in actief] == ["werknemer"]
    assert afgewezen == ("klant",)


def test_onbekende_buur_is_een_fout():
    with pytest.raises(OngeldigeBurenlijstError):
        bevestig_buur(OPGESLAGEN, ACTIEF, "model:onbekend", actor="d", at=AT)


def test_toevoegen_door_gebruiker_is_bevestigd_en_uniek():
    na = voeg_buur_toe(OPGESLAGEN, "borg", "Persoon die instaat.", actor="d", at=AT)
    nieuw = na[-1]
    assert (nieuw["herkomst"], nieuw["bevestigd"], nieuw["term"]) == (
        "gebruiker",
        True,
        "borg",
    )
    normaliseer_buren(na)  # geldig
    with pytest.raises(OngeldigeBurenlijstError, match="al"):
        voeg_buur_toe(na, "Borg", None, actor="d", at=AT)
    with pytest.raises(OngeldigeBurenlijstError):
        voeg_buur_toe(na, "  ", None, actor="d", at=AT)


def test_modelvoorstel_overnemen_als_onbevestigde_of_bevestigde_buur():
    voorstel = {
        "id": "model:abc",
        "term": "zekerheidsgever",
        "definitie": None,
        "herkomst": "model",
        "bevestigd": False,
    }
    onbevestigd = neem_voorstel_over(OPGESLAGEN, voorstel, actor="d", at=AT)
    assert onbevestigd[-1]["bevestigd"] is False
    assert onbevestigd[-1]["herkomst"] == "model"
    bevestigd = neem_voorstel_over(
        OPGESLAGEN, voorstel, actor="d", at=AT, bevestigd=True
    )
    assert bevestigd[-1]["bevestigd"] is True


def test_besluit_verandert_de_vingerafdruk_niet():
    context = {"organisatorische_context": ["X"]}
    voor = bereken_ess05_vingerafdruk(
        "lener", "tekst", context, [], buren=normaliseer_buren(ACTIEF)
    )
    na_lijst = bevestig_buur(OPGESLAGEN, ACTIEF, "repository:9", actor="d", at=AT)
    actief, _ = stel_burenlijst_samen(
        na_lijst,
        [{"id": 9, "begrip": "klant", "definitie": REPOSITORYBUUR["definitie"]}],
    )
    assert (
        bereken_ess05_vingerafdruk("lener", "tekst", context, [], buren=actief) == voor
    )


def test_lege_ruimte_bevestigen_is_gebonden_en_gemotiveerd():
    with pytest.raises(ValueError, match="grond"):
        bevestig_lege_ruimte("f" * 64, grond="", actor="d", at=AT)
    bevestiging = bevestig_lege_ruimte(
        "f" * 64, grond="Enig begrip in dit register.", actor="d", at=AT
    )
    assert bevestiging["contract_version"] == CONTRACTVERSIE
    assert lege_ruimte_geldig(bevestiging, "f" * 64)
    assert not lege_ruimte_geldig(bevestiging, "0" * 64)
