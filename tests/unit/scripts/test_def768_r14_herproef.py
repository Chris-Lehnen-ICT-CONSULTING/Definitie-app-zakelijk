"""DEF-768 R14 — herproef na het R13-herstel: registratie, V-stopregel en negatieven.

Opdracht Chris 27-09 ("Ok kun je het nu wel fixen?",
logs/def768/r13-herstel-gebruikersopdracht-v1.json): dezelfde vijf gevallen H1–H5
(max 10) plus twee gerichte verifier-negatieven (max 2); totaal max 12, USD 5,
cumulatief 376 + 12 = 388 binnen 430/USD 25. Geen retry/reserve/cache. De
negatieven verhinderen de vijf gevallen niet: zoals R13 stopt alleen een
technisch niet-afgerond geval, nu ook in de V-fase.

De negatieven (V-N6 uit R13-H2, V-N7 uit R13-H3) zijn synthetisch afgeleid,
geen modeluitvoer: ze komen door de answer/3-routecontrole en houden het
oorspronkelijke inhoudelijke gat, zodat de echte verifier het moet vinden.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import sys
from pathlib import Path

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import _omgeving8, _R8Provider, _v_invoer
from tests.unit.scripts.test_def768_r9_proef import _r8_boek
from tests.unit.scripts.test_def768_r10_proef import (
    HUIDIG_CONTRACT,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    _foutdragers,
    _r9_boek,
    _sha,
)
from tests.unit.scripts.test_def768_r11_proef import _r10_boek
from tests.unit.scripts.test_def768_r12_microproef import _r11_boek
from tests.unit.scripts.test_def768_r13_herkenbare_gevallen import (
    GEVALLEN,
    GEVALLEN_SHA256,
    _keten13,
    _r12_boek,
    _vijf,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r14_verificatie_invoer as mk14
import proefgrootboek as gb
import run_ess05_proef as runner

from domain.ess05 import bewijs

R14_ID = "DEF-768-AI-20260927-R14"
R14_MAP = ROOT / "reports" / R14_ID
V14 = R14_MAP / "verificatie-invoer-v1.json"
V14_SHA256 = "233fcbf0da84f897792c1e355c71d08eda237faabd92e3935950b8fd00609689"
LOGS = ROOT / "logs" / "def768"
OPDRACHT = LOGS / "r13-herstel-gebruikersopdracht-v1.json"
BESLUIT14 = LOGS / "ronde14-herproef-budgetbesluit-v1.json"
BESLUIT14_SHA256 = "5fd8af4b2e37dd5107e454c08a4956415d40d107101d6ae0ac10aa238f0b0c32"
#: De echte R13-stand: tien betaalde stappen, USD 0,993675.
R13_KOSTEN_NUSD = 993_675_000
#: USD 25 − werkelijke R8–R13-kosten (1,669590).
KADERREST_NUSD = 23_330_410_000
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
               "R12", "R13")  # fmt: skip
V = "validation"
W = "ess05_verification"
R13_FIXTURE = (
    ROOT / "tests" / "fixtures" / "ess05" / "r13_herkenbare_antwoorden_v1.json"
)
R13 = {
    g["id"]: g for g in json.loads(R13_FIXTURE.read_text(encoding="utf-8"))["gevallen"]
}

besluit_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (BESLUIT14, OPDRACHT, TOESTEMMING)),
    reason="git-ignored besluiten ontbreken",
)
r14_invoer_nodig = pytest.mark.skipif(
    not (V14.is_file() and GEVALLEN.is_file()),
    reason="git-ignored R13/R14-invoer ontbreekt",
)


def _r13_boek(root: Path, *, kosten: int = R13_KOSTEN_NUSD):
    """Een R13-grootboek zoals het echte: vijf gevallen × 2 stappen, niet gestopt."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R13)
    per_stap = kosten // 10
    for i in range(1, 6):
        poging, vorige = f"ontwikkeling|H{i}|1", None
        for stap, taak in (("beoordeling", V), ("verificatie", W)):
            res = boek.reserveer("ontwikkeling", f"{poging}/{stap}", invoer_sha256="a" * 64,
                                 poging=poging, stap=stap, vorige_stap=vorige,
                                 task_type=taak,
                                 binding={"dataset_sha256": "a" * 64, "herhaal_ids": [],
                                          "code_sha256": "b" * 64,
                                          "config_sha256": "c" * 64,
                                          "freeze_sha256": "d" * 64})  # fmt: skip
            boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                       kosten_werkelijk_nusd=per_stap)  # fmt: skip
            vorige = stap
        boek.registreer_geval("ontwikkeling", poging, geaccepteerd=i != 2,
                              reden="r13", technisch_afgerond=True)  # fmt: skip
    return boek


def _keten14(tmp_path: Path):
    """(R13-, R12- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r13 = runner.Proefopslag(tmp_path / "r13")
    _r13_boek(r13.root)
    return (r13, *_keten13(tmp_path))


def _bestaande_keten14(tmp_path: Path):
    namen = ("r13", "r12", "r11", "r10", "r9", "r8", "r7", "r6", "r5", "r4", "r3",
             "r2", "r1")  # fmt: skip
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag14(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r14")


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag14(tmp_path).grootboek
    if not pad.exists():
        return []
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


def _freeze(omg, tmp_path: Path, proef, groep: str) -> Path:
    pad = tmp_path / f"freeze-{groep}.json"
    if not pad.exists():
        pad.write_text(
            json.dumps(runner.freezevelden(omg, proef, groep)), encoding="utf-8"
        )
    return pad


def _v14(omg, tmp_path, pad, *, nieuw=True):
    proef = dataclasses.replace(runner.PROEVEN["R14"], v_invoer_sha256=_sha(pad))
    return asyncio.run(
        runner.voer_v_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag14(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef, "v"),
            voorganger_opslag=(
                _keten14(tmp_path) if nieuw else _bestaande_keten14(tmp_path)
            ),
            nieuw_grootboek=nieuw,
        )
    )


def _t14(omg, tmp_path, pad, *, nieuw=True):
    proef = dataclasses.replace(
        runner.PROEVEN["R14"], t_ontwikkelinvoer_sha256=_sha(pad)
    )
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase="ontwikkeling",
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag14(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef, "o"),
            voorganger_opslag=(
                _keten14(tmp_path) if nieuw else _bestaande_keten14(tmp_path)
            ),
            nieuw_grootboek=nieuw,
        )
    )


# --- identiteit en kosten ---------------------------------------------------------------


class TestIdentiteit:
    def test_twaalf_stappen_twee_onafhankelijke_fases_cumulatief_388(self):
        r14 = gb.R14
        assert r14.proef_id == R14_ID
        assert dict(r14.fasecaps) == {"verificatie_alleen": 2, "ontwikkeling": 10}
        assert (r14.reserve_max, r14.totaal_max) == (0, 12)
        assert r14.voorganger is gb.R13
        assert r14.cumulatief_max == 388 == 376 + 12
        assert r14.modelstappen_per_geval == 2
        assert dict(r14.fasestappen) == {
            "verificatie_alleen": (W,),
            "ontwikkeling": (V, W),
        }
        # Negatieven blokkeren de vijf gevallen niet: geen fasevolgorde.
        assert dict(r14.fasevolgorde) == {"verificatie_alleen": (), "ontwikkeling": ()}
        assert (r14.stop_bij_eerste_fout, r14.stop_alleen_technisch) == (True, True)
        assert [(g.naam, set(g.fases), g.herhaal_aantal) for g in r14.eindgroepen] == [
            ("v", {"verificatie_alleen"}, 0),
            ("o", {"ontwikkeling"}, 0),
        ]

    def test_zelfde_model_en_grenzen_plafond_4_20_onder_5(self):
        kb14, kb8 = gb.R14.kostenbewaking, gb.R8.kostenbewaking
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb14, veld) == getattr(kb8, veld), veld
        assert dict(kb14.bytegrens) == dict(kb8.bytegrens)
        begroting = 2 * 375_000_000 + 5 * (315_000_000 + 375_000_000)
        assert kb14.plafond_nusd == gb.begroting_nusd(gb.R14) == begroting
        assert kb14.plafond_nusd == 4_200_000_000
        assert kb14.plafond_nusd <= 5_000_000_000  # mandaat: max USD 5
        assert kb14.plafond_nusd <= KADERREST_NUSD
        assert gb.R14.kostenkader_nusd == 25_000_000_000

    def test_r13_en_ouder_ongewijzigd(self):
        assert (gb.R13.totaal_max, gb.R13.cumulatief_max) == (10, 376)
        assert gb.R13.kostenbewaking.plafond_nusd == 3_450_000_000
        assert (gb.R12.totaal_max, gb.R12.cumulatief_max) == (4, 369)

    def test_cumulatief_388_past_389_niet(self, tmp_path):
        keten = [
            _r13_boek(tmp_path / "r13"),
            _r12_boek(tmp_path / "r12"),
            _r11_boek(tmp_path / "r11"),
            _r10_boek(tmp_path / "r10"),
            _r9_boek(tmp_path / "r9"),
            _r8_boek(tmp_path / "r8"),
        ]
        for naam, identiteit, n in (("r7", gb.R7, 37), ("r6", gb.R6, 37),
                                    ("r5", gb.R5, 57), ("r4", gb.R4, 57),
                                    ("r3", gb.R3, 57), ("r2", gb.R2, 57),
                                    ("r1", gb.R1, 57)):  # fmt: skip
            keten_boek(tmp_path / naam, identiteit, n)
            keten.append(
                gb.Grootboek.lees(tmp_path / naam / "callgrootboek.jsonl", identiteit)
            )
        assert sum(b.samenvatting()["totaal"] for b in keten) == 376
        boek = gb.Grootboek.nieuw(_opslag14(tmp_path).grootboek, gb.R14)
        gb.controleer_cumulatief(boek, keten, 12)
        with pytest.raises(gb.BudgetSchendingError, match="388"):
            gb.controleer_cumulatief(boek, keten, 13)

    @pytest.mark.skipif(
        not all(runner.PROEVEN[n].opslag.grootboek.is_file() for n in OUDE_RONDES),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_376_calls_usd_1_669590(self, tmp_path):
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed(OUDE_RONDES)
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 376
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:6])
        assert lopend == 1_669_590_000 == 25_000_000_000 - KADERREST_NUSD
        assert keten[0].kostenstand()["lopend_nusd"] == R13_KOSTEN_NUSD
        boek = gb.Grootboek.nieuw(_opslag14(tmp_path).grootboek, gb.R14)
        gb.controleer_cumulatief(boek, keten, 12)
        with pytest.raises(gb.BudgetSchendingError, match="388"):
            gb.controleer_cumulatief(boek, keten, 13)


# --- registratie en besluit -------------------------------------------------------------


class TestRegistratie:
    def test_r14_geregistreerd_met_r13_invoer_eigen_v_besluit_en_actueel_contract(self):
        proef = runner.PROEVEN["R14"]
        assert proef.identiteit is gb.R14
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R14_MAP
        # Dezelfde H1–H5 als R13: zelfde bestand, zelfde hash.
        assert proef.t_ontwikkelinvoer_sha256 == GEVALLEN_SHA256
        assert proef.v_invoer_sha256 == V14_SHA256
        assert proef.g_ontwikkelinvoer_sha256 is None
        assert (proef.budgetbesluit, proef.budgetbesluit_sha256) == (
            BESLUIT14,
            BESLUIT14_SHA256,
        )
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        # Het gepinde contract is exact dat van de huidige code (answer/3).
        assert dict(proef.contract) == HUIDIG_CONTRACT
        assert proef.contract["answer_schema_version"] == bewijs.ANTWOORDSCHEMA
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST_NUSD

    def test_r12_en_r13_weigeren_op_hun_answer2_contract(self):
        omg = _omgeving8(_R8Provider())
        for naam in ("R12", "R13"):
            with pytest.raises(gb.BudgetSchendingError, match="contractidentiteit"):
                runner._controleer_contract(omg, runner.PROEVEN[naam])
        runner._controleer_contract(omg, runner.PROEVEN["R14"])

    @besluit_nodig
    def test_besluit_gebonden_aan_opdracht_en_past_op_r14(self):
        data = json.loads(BESLUIT14.read_text(encoding="utf-8"))
        bron = json.loads(OPDRACHT.read_text(encoding="utf-8"))
        assert data["bron_sha256"] == _sha(OPDRACHT)
        assert data["gebruikersantwoord"] == bron["gebruiker_letterlijk"]
        grens = bron["herproefgrens_coordinator"]
        assert data["extra_modelaanroepen_max"] == grens["max_sdk_calls"] == 12
        assert data["historisch_verbruik"] == grens["baseline_calls"] == 376
        assert data["cumulatief_max"] == grens["max_cumulatief_na_deze_proef"] == 388
        assert runner._nusd(data["kostenbudget_usd"]) <= runner._nusd(grens["max_usd"])
        assert runner._nusd(data["kaderrest_usd"]) == runner._nusd(25) - runner._nusd(
            grens["baseline_usd_sinds_r8"]
        )
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R14"]) == (
            BESLUIT14_SHA256
        )

    @besluit_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 13},
            {"cumulatief_max": 389},
            {"historisch_verbruik": 375},
            {"reserve": 1},
            {"kostenbudget_usd": "5.00"},
            {"kaderrest_usd": "23.330411"},
            {"r13_verbruik_usd": "0.993676"},
            {"r13_verbruik_usd": None},
            {"r13_verbruik_modelstappen": 11},
            {"fasen_modelstappen_max": {"ontwikkeling": 12}},
        ],
    )
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        data = json.loads(BESLUIT14.read_text(encoding="utf-8"))
        for sleutel, waarde in anders.items():
            if waarde is None:
                data.pop(sleutel)
            else:
                data[sleutel] = waarde
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        proef = dataclasses.replace(
            runner.PROEVEN["R14"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)


# --- V-stopregel: alleen technisch (offline) --------------------------------------------


class TestVStopregel:
    def test_gemiste_negatief_stopt_niet_en_blijft_zichtbaar(self, tmp_path):
        pad, _ = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _R8Provider()  # de stubverifier keurt alles goed: gemist
        samenvatting = _v14(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie", "verificatie"]
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"]) for g in gevallen] == [
            (False, True),
            (False, True),
        ]
        assert all("fout item vrijgegeven" in g["reden"] for g in gevallen)
        assert samenvatting["grootboek_na"]["gestopt"] is False
        assert [r["status_correct"] for r in samenvatting["resultaten"]] == [False] * 2

    def test_detectie_telt_als_geaccepteerd(self, tmp_path):
        pad, items = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        _v14(_omgeving8(provider), tmp_path, pad)
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"]) for g in gevallen] == [
            (True, True),
            (True, True),
        ]

    def test_technische_fout_stopt_duurzaam_zonder_retry(self, tmp_path):
        class _Onbereikbaar(_R8Provider):
            async def chat_completion(self, messages, model, **kwargs):
                self.stappen.append("verificatie")
                raise ConnectionError("netwerk weg")

        pad, _ = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _Onbereikbaar()
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v14(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"]  # geen retry, geen tweede item
        (geval,) = _soort(tmp_path, "geval")
        assert (geval["geaccepteerd"], geval["technisch_afgerond"]) == (False, False)
        # Ook de vijf gevallen starten daarna niet: een systeemstoring blijft stop.
        tweede = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _t14(_omgeving8(tweede), tmp_path, _vijf(tmp_path), nieuw=False)
        assert tweede.stappen == []

    def test_vijf_gevallen_na_gemiste_negatieven_toch_gemeten(self, tmp_path):
        pad, _ = _v_invoer(tmp_path, ("fout", "fout"))
        _v14(_omgeving8(_R8Provider()), tmp_path, pad)
        provider = _R8Provider()
        _t14(_omgeving8(provider), tmp_path, _vijf(tmp_path), nieuw=False)
        assert provider.stappen == ["beoordeling", "verificatie"] * 5
        assert len(_soort(tmp_path, "reservering")) == 12
        assert len(_soort(tmp_path, "geval")) == 7

    def test_derde_negatief_boven_de_fasecap_geweigerd(self, tmp_path):
        pad, _ = _v_invoer(tmp_path, ("fout", "fout", "fout"))
        provider = _R8Provider()
        with pytest.raises(
            gb.BudgetSchendingError,
            match="plan vraagt 3 calls; fasecap verificatie_alleen laat nog 2",
        ):
            _v14(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == []


# --- de twee gerichte negatieven --------------------------------------------------------


def _afgeleid(maak, gid: str):
    geval = R13[gid]
    antwoord = maak(json.loads(geval["raw_response"]))
    return antwoord, bewijs.valideer_antwoord(
        antwoord, geval["materiaal"], geval["buren"]
    )


def _claims(concept) -> dict[str, dict]:
    return {c["id"]: c for c in concept.data["claims"]}


def _citaten(concept, claim: dict) -> list[dict]:
    plaatsen = {e["id"]: e for e in concept.data["evidence"]}
    return [plaatsen[e] for e in claim["evidence"]]


class TestNegatieven:
    """Op de ongewijzigde echte R13-antwoorden (fixture), zonder reports/."""

    def test_origineel_faalt_op_answer3_de_variant_komt_erdoor(self):
        for maak, gid in ((mk14.n6_antwoord, "H2"), (mk14.n7_antwoord, "H3")):
            origineel = json.loads(R13[gid]["raw_response"])
            origineel["schema_version"] = bewijs.ANTWOORDSCHEMA
            geval = R13[gid]
            concept, fouten = bewijs.valideer_antwoord(
                origineel, geval["materiaal"], geval["buren"]
            )
            assert concept is None and fouten[0]["reason"] == "structuurfout", gid
            _, (concept, fouten) = _afgeleid(maak, gid)
            assert concept is not None, (gid, fouten)

    def test_v_n6_missing_feature_met_niet_dragend_kernfragment(self):
        antwoord, (concept, _) = _afgeleid(mk14.n6_antwoord, "H2")
        (buur,) = concept.data["neighbours"]
        claim = _claims(concept)[buur["missing_feature_claim"]]
        origineel = json.loads(R13["H2"]["raw_response"])
        assert claim["text"] == origineel["neighbours"][0]["missing_feature"]["text"]
        kern = [e for e in _citaten(concept, claim) if e["material_id"] == "definition"]
        definitie = R13["H2"]["materiaal"]["definition"]
        # Precies één kerncitaat, een strikt fragment: het toont niet wat de kern
        # als geheel mist. Het broncitaat blijft het oorspronkelijke.
        assert len(kern) == 1 and kern[0]["quote"] != definitie
        assert len(kern[0]["quote"]) < len(definitie)
        # De vrije top-level bron- en vergelijkingsclaims zijn weg (answer/3).
        assert all(
            e["material_id"] in ("definition", "context", "meaning")
            for r in concept.data["reason_claims"]
            for e in _citaten(concept, _claims(concept)[r])
        )
        assert antwoord["schema_version"] == bewijs.ANTWOORDSCHEMA

    def test_v_n7_gevolgtrekking_met_niet_dragende_kernpremisse(self):
        _, (concept, _) = _afgeleid(mk14.n7_antwoord, "H3")
        claims = _claims(concept)
        (buur,) = concept.data["neighbours"]
        (claim,) = [
            claims[r] for r in buur["reason_claims"] if claims[r]["role"] == "inference"
        ]
        origineel = [
            c
            for c in json.loads(R13["H3"]["raw_response"])["neighbours"][0]["reason"]
            if c["role"] == "inference"
        ]
        assert [claim["text"]] == [c["text"] for c in origineel]
        # Precies één premisse meer dan het origineel: de kernpremisse met het
        # genuscitaat, een strikt fragment van de definitie.
        assert len(claim["premises"]) == len(origineel[0]["premises"]) + 1
        kernpremissen = [
            p
            for p in claim["premises"]
            if any(
                e["material_id"] == "definition" for e in _citaten(concept, claims[p])
            )
        ]
        assert len(kernpremissen) == 1
        (citaat,) = _citaten(concept, claims[kernpremissen[0]])
        assert citaat["quote"] != R13["H3"]["materiaal"]["definition"]

    @pytest.mark.parametrize(
        ("maak", "gid"), [(mk14.n6_antwoord, "H1"), (mk14.n7_antwoord, "H1")]
    )
    def test_maker_weigert_een_antwoord_zonder_het_gat(self, maak, gid):
        # H1 heeft geen missing_feature en geen buurgevolgtrekking zonder kern.
        with pytest.raises(mk14.MakerfoutError):
            maak(json.loads(R13[gid]["raw_response"]))

    def test_maker_weigert_een_al_gedekte_missing_feature(self):
        antwoord = json.loads(R13["H2"]["raw_response"])
        ontbrekend = antwoord["neighbours"][0]["missing_feature"]
        ontbrekend["quotes"].insert(0, dict(antwoord["core_features"][0]))
        with pytest.raises(mk14.MakerfoutError, match="zonder kerncitaat"):
            mk14.n6_antwoord(antwoord)

    def test_bron_niet_gemuteerd(self):
        for maak, gid in ((mk14.n6_antwoord, "H2"), (mk14.n7_antwoord, "H3")):
            voor = R13[gid]["raw_response"]
            maak(json.loads(voor))
            assert (
                _sha_tekst(R13[gid]["raw_response"]) == R13[gid]["raw_response_sha256"]
            )


def _sha_tekst(tekst: str) -> str:
    import hashlib

    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


@r14_invoer_nodig
class TestEchteInvoer:
    def test_gepind_deterministisch_en_gelabeld(self):
        assert _sha(V14) == V14_SHA256 == runner.R14_V_INVOER_SHA256
        tekst = json.dumps(mk14.maak_verificatie_invoer(), ensure_ascii=False, indent=2)
        assert tekst + "\n" == V14.read_text(encoding="utf-8")
        data = json.loads(tekst)
        assert [i["id"] for i in data["items"]] == ["V-N6", "V-N7"]
        for item in data["items"]:
            assert item["soort"] == "fout"
            assert item["bron"]["label"] == mk14.LABEL
            (foutdrager,) = item["foutdragende_items"]
            assert item["bron"]["verwacht"] == {
                "item": foutdrager,
                "outcome": "unsupported",
            }
            # De oorspronkelijke verifier noemde de overeenkomstige R13-claim supported.
            historisch = item["bron"]["historische_foutdrager"]["verifieroordeel"]
            assert historisch["outcome"] == "supported"

    def test_runner_bindt_de_items_aan_de_huidige_code(self):
        data = json.loads(V14.read_text(encoding="utf-8"))
        items = runner.valideer_v_invoer(data, _omgeving8(_R8Provider()))
        assert [v.sleutel for v in items] == [
            "verificatie_alleen|V-N6|1",
            "verificatie_alleen|V-N7|1",
        ]

    @pytest.mark.parametrize(
        ("fase", "invoer", "groep", "sleutels"),
        [
            ("ontwikkeling", GEVALLEN, "o", [f"ontwikkeling|H{i}|1" for i in range(1, 6)]),
            ("verificatie_alleen", V14, "v", ["verificatie_alleen|V-N6|1",
                                               "verificatie_alleen|V-N7|1"]),
        ],
    )  # fmt: skip
    def test_droog_op_de_geregistreerde_r14(
        self, tmp_path, fase, invoer, groep, sleutels
    ):
        code = runner.main(["--proef", "R14", "--fase", fase, "--gevallen", str(invoer),
                            "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob(f"droog-{fase}-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert droog["proef_id"] == R14_ID
        assert [i["sleutel"] for i in droog["items"]] == sleutels
        freeze = droog["freezevelden"]
        assert (freeze["groep"], freeze["dataset_sha256"]) == (groep, _sha(invoer))
        assert {k: freeze[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        assert not list(tmp_path.rglob("*.jsonl"))
