"""DEF-768 B2 — R18-invoer A/C/D/E met orakel (offline, geen aanroepen).

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B2,
met de aanvullingen van de opdracht: rapportmap
`reports/DEF-768-AI-20260928-R18/`; A en C exact uit de R17-invoer (sha256
cda6080d…fab4); D en E SYNTHETISCH, GEEN MODELUITVOER met exact de plantekst
en -orakels; in het orakel van E staat dat `review_required` alleen telt als
de voorwaarde behouden is. Binding aan de berekende contractidentiteit.

De juiste interpretaties voor A en C zijn de synthetisch herbonden R17-
interpretaties (`gecorrigeerd-R17-{A,C}.json`, omgezet met de testhulp
`naar_eenheden`); die voor D en E zijn hier vooraf opgesteld. Geen
modeluitvoer, geen netwerk.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys

import pytest

from tests.unit.domain.test_def768_bewijsregels import naar_eenheden
from tests.unit.scripts.test_def768_bewijsscorer import (
    BUUR,
    D_BRON,
    E_BRON,
    INLEIDING,
    ORAKEL_A,
    ORAKEL_D,
    ORAKEL_E,
    _d_juist,
    _e,
    _u,
)
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))
sys.path.insert(0, str(ROOT / "src"))

import bewijsscorer as bs
import maak_r18_bewijsregel_invoer as mk18
import migreer_r7_naar_v2 as mig

from domain.ess05 import bewijsregels as br
from services.validation.ess05_bewijsregel_service import (
    Ess05BewijsregelService,
    bouw_interpretatieprompt,
    interpretatiesysteemprompt,
)
from services.validation.ess05_verification_service import prompthash

R17_MAP = ROOT / "reports" / "DEF-768-AI-20260928-R17"
R17_INVOER = R17_MAP / "bewijsregel-invoer-v1.json"
R17_INVOER_SHA256 = "cda6080dd160399cd605487890738ada5bbbfcedb62680cabeca59bf860bfab4"
REPRODUCTIE = R17_MAP / "oorzakenonderzoek-ess05-v1-reproductie"
R18_INVOER = ROOT / "reports" / "DEF-768-AI-20260928-R18" / "bewijsregel-invoer-v1.json"
LABEL = "SYNTHETISCH, GEEN MODELUITVOER"
ORAKEL_C = {
    "kenmerken": {
        "tijdelijk": {
            "doel": {"toestand": ["bevestigd"], "eenheden": ["Uitleen:"]},
            "verhuur": {"toestand": ["ontkend"], "eenheden": ["Verhuur:", BUUR]},
        }
    },
    "dragend": ["tijdelijk"],
    "uitkomst": ["pass"],
}
#: Velden die voor A en C exact uit de R17-invoer komen.
R17_VELDEN = (
    "variant",
    "synthetisch",
    "label",
    "geval",
    "geval_sha256",
    "materiaal_sha256",
    "buren",
    "onvolledig",
)
TERUGGAAFZIN = "de medewerker geeft de apparatuur daarna terug"
# De maker leest de git-ignored R17-invoer en -reproductie (zoals R16/R17-tests).
pytestmark.append(
    pytest.mark.skipif(
        not (R17_INVOER.is_file() and REPRODUCTIE.is_dir()),
        reason="git-ignored R17-invoer of -reproductie ontbreekt",
    )
)


def _sha(pad) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def invoer():
    return mk18.maak_bewijsregel_invoer()


def _items(invoer) -> dict:
    return {i["id"]: i for i in invoer["items"]}


def _r17() -> dict:
    return {i["id"]: i for i in json.loads(R17_INVOER.read_text("utf-8"))["items"]}


def _vergelijking(item) -> br.Vergelijkingsinvoer:
    materiaal, buren, _ = mig.verificatiemateriaal(item["geval"])
    return br.Vergelijkingsinvoer(
        term=item["geval"]["begrip"],
        materiaal=materiaal,
        buren=tuple((b.id, b.term) for b in buren),
        onvolledig=frozenset(item["onvolledig"]),
    )


def _gecorrigeerd(naam, vergelijking) -> dict:
    ruw = json.loads((REPRODUCTIE / f"gecorrigeerd-R17-{naam}.json").read_text("utf-8"))
    ruw = naar_eenheden(ruw, vergelijking)
    ruw["schema_version"] = br.INTERPRETATIESCHEMA
    return ruw


class TestVorm:
    def test_schema_contract_en_vier_items(self, invoer):
        assert invoer["schema"] == "def768-ess05-bewijsregel-invoer/2"
        assert [i["id"] for i in invoer["items"]] == ["A", "C", "D", "E"]
        assert invoer["contract"] == Ess05BewijsregelService.contractidentiteit()

    def test_contract_draagt_de_berekende_systeemprompthash(self, invoer):
        # Zoals Ess05BewijsregelService.contractidentiteit: prompthash(system, "").
        berekend = prompthash(interpretatiesysteemprompt(), "")
        assert invoer["contract"]["interpretation_system_prompt_sha256"] == berekend
        assert invoer["contract"]["interpretation_prompt_version"] == (
            "ess05-interpretatie-prompt/4"
        )
        assert invoer["contract"]["bewijsregel_version"] == "ess05-bewijsregels/6"

    def test_itemvelden(self, invoer):
        velden = {
            "id",
            "variant",
            "synthetisch",
            "label",
            "geval",
            "geval_sha256",
            "materiaal_sha256",
            "buren",
            "onvolledig",
            "prompt_sha256",
            "herhalingen",
            "orakel",
            "herkomst",
        }
        for item in invoer["items"]:
            assert set(item) == velden
            assert item["herhalingen"] == 3
            assert item["onvolledig"] == []
        assert sum(i["herhalingen"] for i in invoer["items"]) == 12

    def test_prompthash_uit_de_huidige_interpretatieprompt(self, invoer):
        for item in invoer["items"]:
            system, user = bouw_interpretatieprompt(_vergelijking(item))
            assert item["prompt_sha256"] == prompthash(system, user)
        assert len({i["prompt_sha256"] for i in invoer["items"]}) == 4

    def test_definitie_context_en_begrip_gelijk_voor_alle_items(self, invoer):
        for item in invoer["items"]:
            geval = item["geval"]
            assert geval["begrip"] == "uitleen"
            assert geval["tekst"] == _r17()["A"]["geval"]["tekst"]
            assert geval["context"]["organisatorische_context"] == [
                "Servicedesk ICT-middelen"
            ]
            assert geval["bronnen"][0]["snippet"].startswith(INLEIDING + " ")


class TestAenC:
    def test_r17_invoer_is_de_gepinde(self):
        assert _sha(R17_INVOER) == R17_INVOER_SHA256
        assert mk18.R17_INVOER_SHA256 == R17_INVOER_SHA256

    @pytest.mark.parametrize("naam", ["A", "C"])
    def test_gevalinhoud_exact_uit_r17(self, invoer, naam):
        nieuw, oud = _items(invoer)[naam], _r17()[naam]
        assert {k: nieuw[k] for k in R17_VELDEN} == {k: oud[k] for k in R17_VELDEN}
        assert (
            nieuw["herkomst"]["bron"]
            == "reports/DEF-768-AI-20260928-R17/bewijsregel-invoer-v1.json"
        )
        assert nieuw["herkomst"]["sha256"] == R17_INVOER_SHA256
        assert nieuw["herkomst"]["oorspronkelijk"] == oud["herkomst"]

    def test_orakels_exact_uit_het_plan(self, invoer):
        assert _items(invoer)["A"]["orakel"] == ORAKEL_A
        assert _items(invoer)["C"]["orakel"] == ORAKEL_C

    def test_afwijkende_r17_invoer_is_een_makerfout(self, tmp_path, monkeypatch):
        vals = tmp_path / "r17.json"
        vals.write_bytes(R17_INVOER.read_bytes() + b" ")
        monkeypatch.setattr(mk18, "R17_INVOER", vals)
        with pytest.raises(mk18.MakerfoutError, match="gepinde hash"):
            mk18.maak_bewijsregel_invoer()


class TestDenE:
    @pytest.mark.parametrize(("naam", "bron"), [("D", D_BRON), ("E", E_BRON)])
    def test_synthetisch_met_exact_de_plantekst(self, invoer, naam, bron):
        item, a = _items(invoer)[naam], _r17()["A"]
        assert item["synthetisch"] is True
        assert item["label"] == LABEL
        assert item["geval"]["bronnen"][0]["snippet"] == bron
        assert item["geval"]["id"] == f"R18-{naam}"
        # Alles behalve id en bronsnippet gelijk aan R17-A (buur: definitie van A).
        zonder = copy.deepcopy(item["geval"])
        zonder["id"] = a["geval"]["id"]
        zonder["bronnen"][0]["snippet"] = a["geval"]["bronnen"][0]["snippet"]
        assert zonder == a["geval"]
        assert item["buren"] == a["buren"]
        assert LABEL in item["herkomst"]["label"]

    def test_orakel_d_exact_uit_het_plan(self, invoer):
        assert _items(invoer)["D"]["orakel"] == ORAKEL_D

    def test_orakel_e_plan_plus_voorwaarderegel(self, invoer):
        orakel = _items(invoer)["E"]["orakel"]
        assert {k: orakel[k] for k in ORAKEL_E} == ORAKEL_E
        assert "review_required" in orakel["voorwaarde_vereist_voor"]
        assert set(orakel["voorwaarde_vereist_voor"]) <= set(orakel["uitkomst"])
        assert "review_required" in orakel["toelichting"]
        assert "voorwaarde_behouden" in orakel["toelichting"]

    def test_teruggaafzin_twee_keer_in_d(self):
        assert D_BRON.count(TERUGGAAFZIN) == 2

    @pytest.mark.parametrize("naam", ["A", "C", "D", "E"])
    def test_elk_orakelprefix_raakt_precies_een_eenheid(self, invoer, naam):
        item = _items(invoer)[naam]
        vergelijking = _vergelijking(item)
        teksten = [
            vergelijking.materiaal[r.material_id][r.start : r.end]
            for r in vergelijking.eenheden().values()
            if not r.material_id.startswith("neighbour:")
        ]
        for per_onderwerp in item["orakel"]["kenmerken"].values():
            for verwacht in per_onderwerp.values():
                for prefix in verwacht["eenheden"]:
                    if prefix == BUUR:
                        continue
                    assert sum(t.startswith(prefix) for t in teksten) == 1, prefix


class TestScoren:
    """Offline: de juiste interpretaties geven M-d en M-b; blind hergebruik niet."""

    @pytest.mark.parametrize("naam", ["A", "C"])
    def test_herbonden_r17_interpretatie(self, invoer, naam):
        item = _items(invoer)[naam]
        vergelijking = _vergelijking(item)
        score = bs.scoor(
            _gecorrigeerd(naam, vergelijking), vergelijking, item["orakel"]
        )
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is True
        assert score["m_c_dragend_ok"] is True
        assert score["f7_afwijkingen"] == []

    def test_d_juist(self, invoer):
        item = _items(invoer)["D"]
        vergelijking = _vergelijking(item)
        score = bs.scoor(_d_juist(vergelijking), vergelijking, item["orakel"])
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is True
        assert score["m_c_dragend_ok"] is True

    def test_d_blind_hergebruik(self, invoer):
        item = _items(invoer)["D"]
        vergelijking = _vergelijking(item)
        ruw = _d_juist(vergelijking, ("Uitleen:",))
        score = bs.scoor(ruw, vergelijking, item["orakel"])
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is False

    def test_e_juist_met_behouden_voorwaarde(self, invoer):
        item = _items(invoer)["E"]
        vergelijking = _vergelijking(item)
        ruw = _e(vergelijking, ("bevestigd", ["Uitleen:"], ["bij storing"]))
        score = bs.scoor(ruw, vergelijking, item["orakel"])
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is True
        assert score["voorwaarde_behouden"] is True

    def test_e_zonder_voorwaarde_is_niet_behouden(self, invoer):
        item = _items(invoer)["E"]
        vergelijking = _vergelijking(item)
        score = bs.scoor(
            _e(vergelijking, ("bevestigd", ["Uitleen:"])), vergelijking, item["orakel"]
        )
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["voorwaarde_behouden"] is False

    def test_eenheden_in_de_prompt_van_d(self, invoer):
        """De twee teruggaafzinnen zitten elk in een eigen (Uitleen-/Verhuur-)eenheid."""
        vergelijking = _vergelijking(_items(invoer)["D"])
        _, prompt = bouw_interpretatieprompt(vergelijking)
        for prefix in ("Uitleen:", "Voor uitleen betaalt", "Verhuur:", "Voor verhuur"):
            assert f"[{_u(vergelijking, prefix)}] {prefix}" in prompt


class TestSchrijven:
    def test_doel_wordt_niet_overschreven(self, tmp_path):
        doel = tmp_path / "invoer.json"
        doel.write_text("bestaand", encoding="utf-8")
        with pytest.raises(FileExistsError):
            mk18.main(["--doel", str(doel)])
        assert doel.read_text(encoding="utf-8") == "bestaand"

    def test_schrijft_deterministisch(self, tmp_path, invoer):
        doel = tmp_path / "invoer.json"
        assert mk18.main(["--doel", str(doel)]) == 0
        assert json.loads(doel.read_text(encoding="utf-8")) == invoer

    def test_standaarddoel_in_de_r18_map(self):
        assert mk18.DOEL == R18_INVOER


@pytest.mark.skipif(not R18_INVOER.is_file(), reason="git-ignored R18-invoer ontbreekt")
class TestVastgelegdeInvoer:
    def test_vastgelegde_invoer_gelijk_aan_de_maker(self, invoer):
        tekst = R18_INVOER.read_text(encoding="utf-8")
        assert tekst == json.dumps(invoer, ensure_ascii=False, indent=2) + "\n"
