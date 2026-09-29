"""DEF-768 B2 — R18-invoer A/C/D/E met orakel (offline, geen aanroepen).

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B2,
met de aanvullingen van de opdracht: rapportmap
`reports/DEF-768-AI-20260928-R18/`; A en C exact uit de R17-invoer (sha256
cda6080d…fab4); D en E SYNTHETISCH, GEEN MODELUITVOER met exact de plantekst
en -orakels; het orakel van E laat alleen `error/buiten_bereik` toe, en het
voorwaardeoordeel is sinds aanvulling v4 (besluit optie 2) altijd van Chris.
Binding aan de berekende contractidentiteit.

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
    _e_met_m,
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
R18_MAP = ROOT / "reports" / "DEF-768-AI-20260928-R18"
#: Aanvulling v7 (F7 = ja): A-orakel met twee juiste antwoorden, zonder f7-veld.
R18_INVOER = R18_MAP / "bewijsregel-invoer-v6.json"
#: De vijfde invoer (schema /6, A-orakel met f7-veld): blijft ongewijzigd staan.
R18_INVOER_V5 = R18_MAP / "bewijsregel-invoer-v5.json"
R18_INVOER_V5_SHA256 = (
    "b2c3c34dbe91d0c8b49746d8438793f3994b098620700ea4cbfe9f4a7619d8c4"
)
#: De vierde invoer (schema /5, geregistreerde formuleringen): blijft ongewijzigd staan.
R18_INVOER_V4 = R18_MAP / "bewijsregel-invoer-v4.json"
R18_INVOER_V4_SHA256 = (
    "75c975806704520bd3abee39f7a7525dab2722fad14fde24ad48f676ce92f135"
)
#: De derde invoer (schema /4, behoud via aanhef): blijft ongewijzigd staan.
R18_INVOER_V3 = R18_MAP / "bewijsregel-invoer-v3.json"
R18_INVOER_V3_SHA256 = (
    "21c1ad911cbe13b02c377c2799f17b4e0475f9e9a006d39f87ec96f2bc5a09ac"
)
#: De eerste invoer (schema /2, orakelveld `eenheden`): blijft ongewijzigd staan.
R18_INVOER_V1 = R18_MAP / "bewijsregel-invoer-v1.json"
R18_INVOER_V1_SHA256 = (
    "fe6bd5d1ce58405cc4560ce0956996b4bc0d7e3d3bbefe086f9b9fdc04873598"
)
#: De tweede invoer (schema /3, E ook review_required): blijft ongewijzigd staan.
R18_INVOER_V2 = R18_MAP / "bewijsregel-invoer-v2.json"
R18_INVOER_V2_SHA256 = (
    "fab905cc9d81f803401ebb35409ade36ce63fb6fd4162adfbb55153c78978932"
)
AANVULLING = (
    ROOT
    / "docs"
    / "plans"
    / "2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1-aanvulling-v7.md"
)
LABEL = "SYNTHETISCH, GEEN MODELUITVOER"
ORAKEL_C = {
    "kenmerken": {
        "tijdelijk": {
            "doel": {"toestand": ["bevestigd"], "vereist": ["Uitleen:"], "toegestaan": []},
            "verhuur": {"toestand": ["ontkend"], "vereist": ["Verhuur:", BUUR],
                        "toegestaan": []},
        }
    },
    "dragend": ["tijdelijk"],
    "uitkomst": ["pass"],
}  # fmt: skip
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
        assert invoer["schema"] == "def768-ess05-bewijsregel-invoer/7"
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

    def test_orakels_exact_uit_de_aanvulling(self, invoer):
        assert _items(invoer)["A"]["orakel"] == ORAKEL_A
        assert _items(invoer)["C"]["orakel"] == ORAKEL_C

    def test_orakel_a_f7_ja_twee_gekoppelde_antwoorden(self, invoer):
        """Aanvulling v7 (F7 = ja): kosteloos/verhuur onbesproken ↔ review_required
        of ontkend ↔ pass; bewijs alleen uit de eenheden met de buurnaam; geen f7."""
        orakel = _items(invoer)["A"]["orakel"]
        verhuur = orakel["kenmerken"]["kosteloos"]["verhuur"]
        assert verhuur == {
            "toestand": ["onbesproken", "ontkend"],
            "vereist": [],
            "toegestaan": ["Verhuur:", BUUR],
            "uitkomst_per_toestand": {
                "onbesproken": ["review_required"],
                "ontkend": ["pass"],
            },
        }
        assert orakel["uitkomst"] == ["review_required", "pass"]
        assert '"f7"' not in json.dumps(invoer)

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

    def test_orakel_d_exact_uit_de_aanvulling(self, invoer):
        """C3: betaalzin vereist; Uitleen-/Verhuur-zin en buurbeschrijving alleen context."""
        assert _items(invoer)["D"]["orakel"] == ORAKEL_D
        verhuur = ORAKEL_D["kenmerken"]["kosteloos"]["verhuur"]
        assert BUUR not in verhuur["vereist"] and BUUR in verhuur["toegestaan"]

    def test_orakel_e_voorwaardeoordeel_van_chris(self, invoer):
        """Aanvulling v4 (besluit optie 2): alleen error/buiten_bereik is juist; het
        voorwaardeoordeel is altijd van Chris; geen lexicale orakelvelden meer."""
        orakel = _items(invoer)["E"]["orakel"]
        assert orakel == {**ORAKEL_E, "toelichting": orakel["toelichting"]}
        assert set(orakel) == {"kenmerken", "dragend", "voorwaarde", "uitkomst",
                               "toelichting"}  # fmt: skip
        assert orakel["uitkomst"] == ["error/buiten_bereik"]
        for woord in ("aanvulling v4", "Chris", "handmatig_beoordelen",
                      "error/buiten_bereik", "niet geslaagd"):  # fmt: skip
            assert woord in orakel["toelichting"], woord
        assert "Uitleen: bij storing stelt" in mk18.BRON_E

    @pytest.mark.parametrize("naam", ["A", "C", "D", "E"])
    def test_orakel_past_op_de_invoer(self, invoer, naam):
        item = _items(invoer)[naam]
        bs.controleer_orakel(item["orakel"], _vergelijking(item))

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
                for prefix in [*verwacht["vereist"], *verwacht["toegestaan"]]:
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
        assert "f7_afwijkingen" not in score

    def test_a_verhuur_betaald_met_het_invoerorakel(self, invoer):
        """F7 = ja: de herbonden R17-A met kosteloos/verhuur ontkend (buurbeschrijving)
        geeft pass en is geslaagd, net als het voorzichtige onbesproken-antwoord."""
        item = _items(invoer)["A"]
        vergelijking = _vergelijking(item)
        ruw = _gecorrigeerd("A", vergelijking)
        kid = bs._kenmerk_id(ruw, "kosteloos")
        (k2,) = [a for a in ruw["antwoorden"]
                 if a["kenmerk_id"] == kid and a["onderwerp"] != br.DOEL]  # fmt: skip
        k2.update(toestand="ontkend", citaten=[_u(vergelijking, BUUR)])
        score = bs.scoor(ruw, vergelijking, item["orakel"])
        assert score["m_d"]["uitkomst"] == "pass"
        assert bs.runoordeel(score, item["orakel"])["categorie"] == "geslaagd"

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

    def test_d_codex_reproducties_met_het_invoerorakel(self, invoer):
        """B3: alleen de buurbeschrijving bij verhuur draagt niet; B4: Uitleen-zin
        plus betaalzin draagt wel (met het orakel uit de invoer zelf)."""
        item = _items(invoer)["D"]
        vergelijking = _vergelijking(item)
        alleen_buur = _d_juist(vergelijking)
        (k2,) = [a for a in alleen_buur["antwoorden"]
                 if a["kenmerk_id"] == "K2" and a["onderwerp"] != "doel"]  # fmt: skip
        k2["citaten"] = [_u(vergelijking, BUUR)]
        assert (
            bs.scoor(alleen_buur, vergelijking, item["orakel"])["m_b_dragend_ok"]
            is False
        )
        beide = _d_juist(vergelijking, ("Uitleen:", "Voor uitleen betaalt"))
        score = bs.scoor(beide, vergelijking, item["orakel"])
        assert score["m_b_dragend_ok"] is True
        assert bs.runoordeel(score, item["orakel"])["categorie"] == "geslaagd"

    def test_e_juist_wacht_op_het_oordeel_van_chris(self, invoer):
        """Aanvulling v4: ook de juiste interpretatie is nooit automatisch geslaagd."""
        item = _items(invoer)["E"]
        vergelijking = _vergelijking(item)
        ruw = _e(vergelijking, ("bevestigd", ["Uitleen:"], ["bij storing"]))
        score = bs.scoor(ruw, vergelijking, item["orakel"])
        assert score["m_d"]["ok"] is True
        assert score["m_b_dragend_ok"] is True
        assert score["voorwaarde_behouden"] is False
        oordeel = bs.runoordeel(score, item["orakel"])
        assert (oordeel["categorie"], oordeel["m_d_telt"]) == (
            "handmatig_beoordelen",
            False,
        )

    def test_e_zonder_voorwaarde_is_niet_behouden(self, invoer):
        item = _items(invoer)["E"]
        vergelijking = _vergelijking(item)
        score = bs.scoor(
            _e(vergelijking, ("bevestigd", ["Uitleen:"])), vergelijking, item["orakel"]
        )
        assert score["m_d"]["uitkomst"] == "review_required"
        assert score["m_d"]["ok"] is False
        assert score["voorwaarde_behouden"] is False

    def test_e_codex_hercontrole_met_het_invoerorakel(self, invoer):
        """B2-rest: 'onafhankelijk van storing' als bevestigd M-kenmerk slaagt niet."""
        item = _items(invoer)["E"]
        vergelijking = _vergelijking(item)
        score = bs.scoor(
            _e_met_m(vergelijking, "onafhankelijk van storing"),
            vergelijking,
            item["orakel"],
        )
        assert score["voorwaarde_behouden"] is False
        oordeel = bs.runoordeel(score, item["orakel"])
        assert oordeel["categorie"] != "geslaagd" and oordeel["m_d_telt"] is False

    @pytest.mark.parametrize(
        "voorwaarden",
        [["bij afwezigheid van storing"], ["als storing ontbreekt"],
         ["bij storing of op verzoek"], ["bij de storingsdienst"],
         ["bij storing", "deze voorwaarde is optioneel"],
         ["bij storing", "als storing ontbreekt"], ["bij storing", "of op verzoek"]],
    )  # fmt: skip
    def test_e_codex_hercontroles_v2_v3_met_het_invoerorakel(self, invoer, voorwaarden):
        """B2-rest-2 en -3: aanhef of combinatie slaagt nooit automatisch."""
        item = _items(invoer)["E"]
        vergelijking = _vergelijking(item)
        ruw = _e(vergelijking, ("bevestigd", ["Uitleen:"], voorwaarden))
        score = bs.scoor(ruw, vergelijking, item["orakel"])
        assert score["voorwaarde_status"] == "handmatig_beoordelen"
        oordeel = bs.runoordeel(score, item["orakel"])
        assert oordeel["categorie"] != "geslaagd" and oordeel["m_d_telt"] is False

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
        """Aanvulling v7: een nieuw bestand -v6; -v1 t/m -v5 worden nooit overschreven."""
        assert mk18.DOEL == R18_INVOER
        assert mk18.DOEL not in (
            R18_INVOER_V1, R18_INVOER_V2, R18_INVOER_V3, R18_INVOER_V4, R18_INVOER_V5
        )  # fmt: skip

    def test_schema_opgehoogd(self):
        assert mk18.INVOERSCHEMA == "def768-ess05-bewijsregel-invoer/7"

    def test_aanvulling_gepind_in_de_herkomst(self, invoer):
        assert invoer["herkomst"]["aanvulling"] == {
            "pad": "docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1-aanvulling-v7.md",
            "sha256": _sha(AANVULLING),
        }
        assert _sha(AANVULLING) == mk18.AANVULLING_SHA256

    def test_afwijkende_aanvulling_is_een_makerfout(self, tmp_path, monkeypatch):
        vals = tmp_path / "aanvulling.md"
        vals.write_bytes(AANVULLING.read_bytes() + b" ")
        monkeypatch.setattr(mk18, "AANVULLING", vals)
        with pytest.raises(mk18.MakerfoutError, match="gepinde hash"):
            mk18.maak_bewijsregel_invoer()


@pytest.mark.skipif(not R18_INVOER.is_file(), reason="git-ignored R18-invoer ontbreekt")
class TestVastgelegdeInvoer:
    def test_vastgelegde_invoer_gelijk_aan_de_maker(self, invoer):
        tekst = R18_INVOER.read_text(encoding="utf-8")
        assert tekst == json.dumps(invoer, ensure_ascii=False, indent=2) + "\n"

    @pytest.mark.skipif(not R18_INVOER_V1.is_file(), reason="R18-invoer v1 ontbreekt")
    def test_v1_ongewijzigd_en_ongeldig_onder_de_nieuwe_orakelstructuur(self):
        assert _sha(R18_INVOER_V1) == R18_INVOER_V1_SHA256
        v1 = {i["id"]: i for i in json.loads(R18_INVOER_V1.read_text("utf-8"))["items"]}
        with pytest.raises(bs.OrakelfoutError, match="velden"):
            bs.controleer_orakel(v1["D"]["orakel"], _vergelijking(v1["D"]))

    @pytest.mark.skipif(not R18_INVOER_V2.is_file(), reason="R18-invoer v2 ontbreekt")
    def test_v2_ongewijzigd_met_het_oude_e_orakel(self):
        assert _sha(R18_INVOER_V2) == R18_INVOER_V2_SHA256
        data = json.loads(R18_INVOER_V2.read_text("utf-8"))
        assert data["schema"] == "def768-ess05-bewijsregel-invoer/3"
        v2 = {i["id"]: i for i in data["items"]}
        assert "review_required" in v2["E"]["orakel"]["uitkomst"]

    @pytest.mark.skipif(not R18_INVOER_V3.is_file(), reason="R18-invoer v3 ontbreekt")
    def test_v3_ongewijzigd_zonder_geregistreerde_formuleringen(self):
        assert _sha(R18_INVOER_V3) == R18_INVOER_V3_SHA256
        data = json.loads(R18_INVOER_V3.read_text("utf-8"))
        assert data["schema"] == "def768-ess05-bewijsregel-invoer/4"
        v3 = {i["id"]: i for i in data["items"]}
        assert "voorwaarde_formuleringen" not in v3["E"]["orakel"]

    @pytest.mark.skipif(not R18_INVOER_V4.is_file(), reason="R18-invoer v4 ontbreekt")
    def test_v4_ongewijzigd_en_ongeldig_onder_aanvulling_v4(self):
        """De lexicale orakelvelden van v4 zijn nu een orakelfout."""
        assert _sha(R18_INVOER_V4) == R18_INVOER_V4_SHA256
        data = json.loads(R18_INVOER_V4.read_text("utf-8"))
        assert data["schema"] == "def768-ess05-bewijsregel-invoer/5"
        v4 = {i["id"]: i for i in data["items"]}
        assert "voorwaarde_formuleringen" in v4["E"]["orakel"]
        with pytest.raises(bs.OrakelfoutError, match="velden"):
            bs.controleer_orakel(v4["E"]["orakel"], _vergelijking(v4["E"]))

    @pytest.mark.skipif(not R18_INVOER_V5.is_file(), reason="R18-invoer v5 ontbreekt")
    def test_v5_ongewijzigd_en_ongeldig_onder_aanvulling_v7(self):
        """F7 = ja: het f7-veld van het A-orakel in v5 is nu een orakelfout."""
        assert _sha(R18_INVOER_V5) == R18_INVOER_V5_SHA256
        data = json.loads(R18_INVOER_V5.read_text("utf-8"))
        assert data["schema"] == "def768-ess05-bewijsregel-invoer/6"
        v5 = {i["id"]: i for i in data["items"]}
        assert v5["A"]["orakel"]["kenmerken"]["kosteloos"]["verhuur"]["f7"] == [
            "ontkend"
        ]
        with pytest.raises(bs.OrakelfoutError, match="velden"):
            bs.controleer_orakel(v5["A"]["orakel"], _vergelijking(v5["A"]))
