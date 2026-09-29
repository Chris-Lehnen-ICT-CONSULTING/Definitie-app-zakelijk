"""DEF-768 robuustheidsronde (besluit Chris 29-09) — bewijsregels `/7`, offline.

Fixture: de drie echte P1-antwoorden (`tests/fixtures/def768_p1_echte_antwoorden_v1.json`)
op exact het materiaal dat is verzonden (hashes gecontroleerd bij het maken).

1. Een ontbrekend `voorwaarden` in een antwoord is een lege lijst; elk ander
   ontbrekend of onbekend veld blijft een schemafout.
3b. Een betekeniskenmerk (M) zonder bevestiging in de doelbetekenis wordt
   weggelaten met een diagnostische notitie; zijn antwoorden vervallen mee. Het
   keurt de run niet meer af (was: `betekenisfout`).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from domain.ess05 import app_bewijsregels as app, bewijsregels as br, contract as ec
from domain.modeluitvoer import parse_modeluitvoer

pytestmark = [pytest.mark.unit]

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / ("def768_p1_echte_antwoorden_v1.json")
)
P1 = json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]


def _invoer(rid: str) -> br.Vergelijkingsinvoer:
    r = P1[rid]
    buren = ec.normaliseer_buren(r["buren"])
    return br.Vergelijkingsinvoer(
        r["begrip"], r["verzonden_materiaal"], tuple((b.id, b.term) for b in buren)
    )


def _ruw(rid: str) -> dict:
    return app.ontsnap(parse_modeluitvoer(P1[rid]["ruwe_respons"]))


def test_bewijsregelversie_is_7():
    assert br.BEWIJSREGELVERSIE == "ess05-bewijsregels/7"
    assert br.regelcontract()["bewijsregel_version"] == "ess05-bewijsregels/7"


def test_fixture_bevat_de_p1_fouten():
    assert [P1[r]["fout_p1"]["type"] for r in ("277", "365", "278")] == [
        "betekenisfout",
        "schemafout",
        "kerndekking_onvolledig",
    ]


class TestOntbrekendeVoorwaarden:
    def test_p1_365_zonder_voorwaarden_geeft_geen_schemafout(self):
        ruw = _ruw("365")
        assert all("voorwaarden" not in a for a in ruw["antwoorden"])
        interpretatie = br.valideer_interpretatie(ruw, _invoer("365"))
        assert all(a.voorwaarden == () for a in interpretatie.antwoorden)
        assert br.bepaal(ruw, _invoer("365")).uitkomst != "error"

    @pytest.mark.parametrize("veld", ["context", "citaten", "toestand"])
    def test_ander_ontbrekend_veld_blijft_schemafout(self, veld):
        ruw = _ruw("365")
        del ruw["antwoorden"][0][veld]
        with pytest.raises(br.BewijsregelfoutError) as fout:
            br.valideer_interpretatie(ruw, _invoer("365"))
        assert fout.value.soort == "schemafout"
        assert veld in fout.value.melding

    def test_onbekend_veld_blijft_schemafout(self):
        ruw = _ruw("365")
        ruw["antwoorden"][0]["toelichting"] = "extra"
        with pytest.raises(br.BewijsregelfoutError, match="toelichting") as fout:
            br.valideer_interpretatie(ruw, _invoer("365"))
        assert fout.value.soort == "schemafout"

    def test_aanwezige_voorwaarden_blijven_getoetst(self):
        ruw = _ruw("365")
        ruw["antwoorden"][0]["voorwaarden"] = ["alleen bij twijfel"]
        with pytest.raises(br.BewijsregelfoutError, match="onbesproken") as fout:
            br.valideer_interpretatie(ruw, _invoer("365"))
        assert fout.value.soort == "schemafout"


class TestOnbevestigdeBetekenis:
    def test_p1_277_m1_m2_weggelaten_zonder_betekenisfout(self):
        interpretatie = br.valideer_interpretatie(_ruw("277"), _invoer("277"))
        assert [k.id for k in interpretatie.kenmerken] == ["K1", "K2", "K3"]
        assert {a.kenmerk_id for a in interpretatie.antwoorden} == {"K1", "K2", "K3"}
        assert [n.split(" ", 1)[0] for n in interpretatie.weggelaten] == ["M1", "M2"]
        assert "procedurele positie" in interpretatie.weggelaten[0]
        assert "doelbetekenis" in interpretatie.weggelaten[0]

    def test_p1_277_bepaalt_een_uitkomst(self):
        uitkomst = br.bepaal(_ruw("277"), _invoer("277"))
        assert uitkomst.fout is None
        assert uitkomst.uitkomst == "review_required"
        assert [k.id for k in uitkomst.kenmerken] == ["K1", "K2", "K3"]

    def test_p1_365_m1_m2_weggelaten(self):
        interpretatie = br.valideer_interpretatie(_ruw("365"), _invoer("365"))
        assert [k.id for k in interpretatie.kenmerken] == ["K1", "K2", "K3"]
        assert len(interpretatie.weggelaten) == 2

    def test_weggelaten_kenmerk_verschijnt_niet_in_de_kerncontrole(self):
        interpretatie = br.valideer_interpretatie(_ruw("277"), _invoer("277"))
        kern, *_ = br.controle_eenheden(interpretatie, _invoer("277"))
        assert kern.naam == "kern"
        tekst = json.dumps(dict(kern.pakket.inhoud), ensure_ascii=False)
        assert "procedurele positie" not in tekst
        assert "rechtsbijstand" not in tekst

    def test_bevestigd_betekeniskenmerk_blijft_staan(self):
        # Zelfde 277-antwoord met een bedoelde betekenis die M1 draagt.
        invoer = _invoer("277")
        materiaal = {
            **invoer.materiaal,
            "meaning": "Een verdachte is partij in een strafvorderlijke procedure.",
        }
        invoer = br.Vergelijkingsinvoer(invoer.term, materiaal, invoer.buren)
        uid = next(
            u for u, r in invoer.eenheden().items() if r.material_id == "meaning"
        )
        ruw = _ruw("277")
        for a in ruw["antwoorden"]:
            if (a["kenmerk_id"], a["onderwerp"]) == ("M1", "doel"):
                a.update(toestand="bevestigd", citaten=[uid])
        interpretatie = br.valideer_interpretatie(ruw, invoer)
        assert [k.id for k in interpretatie.kenmerken] == ["K1", "K2", "K3", "M1"]
        assert [n.split(" ", 1)[0] for n in interpretatie.weggelaten] == ["M2"]

    def test_conflict_in_de_doelbetekenis_is_geen_bevestiging(self):
        invoer = _invoer("277")
        materiaal = {**invoer.materiaal, "meaning": "Eén. Twee."}
        invoer = br.Vergelijkingsinvoer(invoer.term, materiaal, invoer.buren)
        ruw = _ruw("277")
        doel = next(
            a
            for a in ruw["antwoorden"]
            if (a["kenmerk_id"], a["onderwerp"]) == ("M1", "doel")
        )
        doel.update(toestand="bevestigd", citaten=["U1"])
        ruw["antwoorden"].append(
            {**copy.deepcopy(doel), "toestand": "ontkend", "citaten": ["U2"]}
        )
        interpretatie = br.valideer_interpretatie(ruw, invoer)
        assert "M1" not in {k.id for k in interpretatie.kenmerken}

    def test_zonder_doelantwoord_ook_weggelaten(self):
        ruw = _ruw("277")
        ruw["antwoorden"] = [
            a
            for a in ruw["antwoorden"]
            if (a["kenmerk_id"], a["onderwerp"]) != ("M2", "doel")
        ]
        interpretatie = br.valideer_interpretatie(ruw, _invoer("277"))
        assert "M2" not in {k.id for k in interpretatie.kenmerken}

    def test_schemafout_in_een_betekeniskenmerk_blijft_fout(self):
        ruw = _ruw("277")
        ruw["buiten_kern"][0]["id"] = "X1"
        with pytest.raises(br.BewijsregelfoutError) as fout:
            br.valideer_interpretatie(ruw, _invoer("277"))
        assert fout.value.soort == "schemafout"
