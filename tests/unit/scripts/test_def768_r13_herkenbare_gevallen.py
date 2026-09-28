"""DEF-768 R13 — vijf herkenbare gevallen door de actuele keten: registratie en voortgang.

Besluit van Chris (26-09, "Go", logs/def768/herkenbare-gevallen-goedkeuring-v1.json):
vijf onafhankelijke gevallen, elk exact eenmaal, ten hoogste 2 modelstappen per
geval (10 totaal), reserve 0, geen retry; cumulatief 366 + 10 = 376 binnen het
bestaande 430/USD 25-kader; lokaal plafond USD 3,45 (≤ USD 4). Een inhoudelijke
mismatch of een afkeuring door de bestaande appcontroles stopt de reeks niet;
een technische fout, bewakingsweigering of onzekere reservering wel.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
from pathlib import Path
from types import MappingProxyType

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _gevallenbestand
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import _omgeving8, _R8Provider
from tests.unit.scripts.test_def768_r9_proef import _r8_boek
from tests.unit.scripts.test_def768_r10_proef import (
    HUIDIG_CONTRACT,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    _r9_boek,
    _sha,
)
from tests.unit.scripts.test_def768_r11_proef import _r10_boek
from tests.unit.scripts.test_def768_r12_microproef import (
    BESLUIT12,
    R12_CONTRACT_GEPIND,
    _keten12,
    _r11_boek,
)

pytestmark = [pytest.mark.unit]

import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

R13_ID = "DEF-768-AI-20260926-R13"
R13_MAP = ROOT / "reports" / R13_ID
GEVALLEN = R13_MAP / "herkenbare-gevallen-v1.json"
GEVALLEN_SHA256 = "b212b826ef51dce8c20b5a587e57389b13e3d24ab6d590e5dcfec7e60493841b"
LOGS = ROOT / "logs" / "def768"
GOEDKEURING = LOGS / "herkenbare-gevallen-goedkeuring-v1.json"
BESLUIT13 = LOGS / "ronde13-herkenbare-gevallen-budgetbesluit-v1.json"
BESLUIT13_SHA256 = "e64c0b6ba74855905dd7c34bc356967fc53d3b18a537639079d5f65794fe4458"
#: De echte R12-stand: één betaalde stap (V-N4), daarna gestopt.
R12_KOSTEN_NUSD = 103_145_000
#: USD 25 − werkelijke R8–R12-kosten (0,675915).
KADERREST_NUSD = 24_324_085_000
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
               "R12")  # fmt: skip
V = "validation"
W = "ess05_verification"

besluiten_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (BESLUIT13, BESLUIT12, GOEDKEURING, TOESTEMMING)),
    reason="git-ignored besluiten ontbreken",
)
gevallen_nodig = pytest.mark.skipif(
    not GEVALLEN.is_file(), reason="git-ignored R13-gevallen ontbreken"
)


def _r12_boek(root: Path, *, kosten: int | None = R12_KOSTEN_NUSD):
    """Een R12-grootboek zoals het echte: één betaalde V-stap, niet geaccepteerd."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R12)
    poging = "verificatie_alleen|V-N4|1"
    res = boek.reserveer("verificatie_alleen", f"{poging}/verificatie",
                         invoer_sha256="a" * 64, poging=poging, stap="verificatie",
                         vorige_stap=None, task_type=W,
                         binding={"dataset_sha256": "a" * 64, "herhaal_ids": [],
                                  "code_sha256": "b" * 64, "config_sha256": "c" * 64,
                                  "freeze_sha256": "d" * 64})  # fmt: skip
    boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
               kosten_werkelijk_nusd=kosten)  # fmt: skip
    boek.registreer_geval("verificatie_alleen", poging, geaccepteerd=False,
                          reden="gestopt")  # fmt: skip
    return boek


def _keten13(tmp_path: Path):
    """(R12-, R11- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r12 = runner.Proefopslag(tmp_path / "r12")
    _r12_boek(r12.root)
    return (r12, *_keten12(tmp_path))


def _bestaande_keten13(tmp_path: Path):
    namen = ("r12", "r11", "r10", "r9", "r8", "r7", "r6", "r5", "r4", "r3", "r2", "r1")
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag13(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r13")


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag13(tmp_path).grootboek
    if not pad.exists():
        return []
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


def _vijf(tmp_path: Path, n: int = 5, naam="vijf.json") -> Path:
    """n onafhankelijke gevallen met een status die de fake nooit geeft."""
    pad = _gevallenbestand(tmp_path, n, naam)
    data = json.loads(pad.read_text(encoding="utf-8"))
    data.pop("herhaal_ids")
    for geval in data["gevallen"]:
        geval["verwacht"] = "not_evaluated"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


def _r13(**anders) -> runner.Proef:
    anders.setdefault("contract", MappingProxyType(HUIDIG_CONTRACT))
    return dataclasses.replace(runner.PROEVEN["R13"], **anders)


def _t13(omg, tmp_path, pad, *, nieuw=True, proef=None):
    # Mechaniek op de huidige code; het gepinde R13-contract (answer/2) weigert
    # sinds answer/3 fail-closed.
    proef = proef or _r13(t_ontwikkelinvoer_sha256=_sha(pad))
    freeze = tmp_path / "freeze-o.json"
    if not freeze.exists():
        freeze.write_text(
            json.dumps(runner.freezevelden(omg, proef, "o")), encoding="utf-8"
        )
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase="ontwikkeling",
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag13(tmp_path),
            proef=proef,
            freeze=freeze,
            voorganger_opslag=(
                _keten13(tmp_path) if nieuw else _bestaande_keten13(tmp_path)
            ),
            nieuw_grootboek=nieuw,
        )
    )


# --- identiteit en kosten ---------------------------------------------------------------


class TestIdentiteit:
    def test_tien_stappen_vijf_gevallen_reserve_nul_cumulatief_376(self):
        r13 = gb.R13
        assert r13.proef_id == R13_ID
        assert dict(r13.fasecaps) == {"ontwikkeling": 10}
        assert (r13.reserve_max, r13.totaal_max) == (0, 10)
        assert r13.voorganger is gb.R12
        assert r13.cumulatief_max == 376 == 366 + 10
        assert r13.modelstappen_per_geval == 2
        assert dict(r13.fasestappen) == {"ontwikkeling": (V, W)}
        assert dict(r13.fasevolgorde) == {"ontwikkeling": ()}
        # Duurzame stopregel, maar alleen op een technisch niet-afgerond geval.
        assert (r13.stop_bij_eerste_fout, r13.stop_alleen_technisch) == (True, True)
        assert r13.gedeelde_codebinding is True
        assert [(g.naam, set(g.fases), g.herhaal_aantal) for g in r13.eindgroepen] == [
            ("o", {"ontwikkeling"}, 0)
        ]

    def test_zelfde_model_en_grenzen_plafond_3_45_onder_4(self):
        kb13, kb8 = gb.R13.kostenbewaking, gb.R8.kostenbewaking
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb13, veld) == getattr(kb8, veld), veld
        assert dict(kb13.bytegrens) == dict(kb8.bytegrens)
        assert gb.begroting_nusd(gb.R13) == 5 * (315_000_000 + 375_000_000)
        assert kb13.plafond_nusd == gb.begroting_nusd(gb.R13) == 3_450_000_000
        assert kb13.plafond_nusd <= 4_000_000_000  # mandaat: hard max USD 4
        assert gb.R13.kostenkader_nusd == 25_000_000_000

    def test_r12_en_ouder_ongewijzigd(self):
        assert (gb.R12.totaal_max, gb.R12.cumulatief_max) == (4, 369)
        assert gb.R12.stop_bij_eerste_fout is True
        assert gb.R12.kostenbewaking.plafond_nusd == 1_440_000_000

    def test_cumulatief_376_past_377_niet(self, tmp_path):
        # 366 werkelijke R1–R12-calls.
        keten = [
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
        assert sum(b.samenvatting()["totaal"] for b in keten) == 366
        boek = gb.Grootboek.nieuw(_opslag13(tmp_path).grootboek, gb.R13)
        gb.controleer_cumulatief(boek, keten, 10)
        with pytest.raises(gb.BudgetSchendingError, match="376"):
            gb.controleer_cumulatief(boek, keten, 11)

    @pytest.mark.skipif(
        not all(runner.PROEVEN[n].opslag.grootboek.is_file() for n in OUDE_RONDES),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_366_calls_usd_0_675915(self, tmp_path):
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed(OUDE_RONDES)
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 366
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:5])
        assert lopend == 675_915_000 == 25_000_000_000 - KADERREST_NUSD
        boek = gb.Grootboek.nieuw(_opslag13(tmp_path).grootboek, gb.R13)
        gb.controleer_cumulatief(boek, keten, 10)
        with pytest.raises(gb.BudgetSchendingError, match="376"):
            gb.controleer_cumulatief(boek, keten, 11)


# --- registratie en besluit -------------------------------------------------------------


class TestRegistratie:
    def test_r13_geregistreerd_met_eigen_opslag_invoer_besluit_en_contract(self):
        proef = runner.PROEVEN["R13"]
        assert proef.identiteit is gb.R13
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R13_MAP
        assert proef.t_ontwikkelinvoer_sha256 == GEVALLEN_SHA256
        assert (proef.v_invoer_sha256, proef.g_ontwikkelinvoer_sha256) == (None, None)
        assert (proef.budgetbesluit, proef.budgetbesluit_sha256) == (
            BESLUIT13,
            BESLUIT13_SHA256,
        )
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        assert dict(proef.contract) == R12_CONTRACT_GEPIND
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST_NUSD

    def test_alleen_r13_tot_en_met_r16_stoppen_alleen_technisch(self):
        assert [
            n for n, p in runner.PROEVEN.items() if p.identiteit.stop_alleen_technisch
        ] == ["R13", "R14", "R15", "R16"]

    @besluiten_nodig
    def test_besluit_gebonden_aan_goedkeuring_en_past_op_r13(self):
        data = json.loads(BESLUIT13.read_text(encoding="utf-8"))
        bron = json.loads(GOEDKEURING.read_text(encoding="utf-8"))
        assert data["bron_sha256"] == _sha(GOEDKEURING)
        assert data["gebruikersantwoord"] == bron["gebruiker_letterlijk"] == "Go"
        scope = bron["uitwerking_coordinator"]
        assert data["extra_modelaanroepen_max"] == scope["max_sdk_calls"] == 10
        assert data["historisch_verbruik"] == scope["baseline_calls"] == 366
        assert runner._nusd(data["kostenbudget_usd"]) <= runner._nusd(scope["max_usd"])
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R13"]) == (
            BESLUIT13_SHA256
        )
        for naam in ("R12", "R11", "R10", "R9", "R8"):
            proef = runner.PROEVEN[naam]
            assert runner.controleer_budgetbesluit(proef) == proef.budgetbesluit_sha256

    @besluiten_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 11},
            {"cumulatief_max": 377},
            {"historisch_verbruik": 365},
            {"reserve": 1},
            {"kostenbudget_usd": "4.00"},
            {"kaderrest_usd": "24.324086"},
            {"r12_verbruik_usd": "0.103146"},
            {"r12_verbruik_usd": None},
            {"r12_verbruik_modelstappen": 2},
            {"fasen_modelstappen_max": {"ontwikkeling": 12}},
        ],
    )
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        data = json.loads(BESLUIT13.read_text(encoding="utf-8"))
        for sleutel, waarde in anders.items():
            if waarde is None:
                data.pop(sleutel)
            else:
                data[sleutel] = waarde
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        proef = dataclasses.replace(
            runner.PROEVEN["R13"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)


# --- stopregel in het grootboek ---------------------------------------------------------

_BINDING = {"dataset_sha256": "a" * 64, "herhaal_ids": [], "code_sha256": "b" * 64,
            "config_sha256": "c" * 64, "freeze_sha256": "d" * 64}  # fmt: skip


def _stap(boek, poging: str, naam: str, taak: str, vorige=None, *, sluit=True):
    res = boek.reserveer("ontwikkeling", f"{poging}/{naam}", invoer_sha256="a" * 64,
                         poging=poging, stap=naam, vorige_stap=vorige, task_type=taak,
                         binding=_BINDING)  # fmt: skip
    if sluit:
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)


def _geval(boek, i: int, **uitkomst):
    poging = f"ontwikkeling|H{i}|1"
    _stap(boek, poging, "beoordeling", V)
    _stap(boek, poging, "verificatie", W, "beoordeling")
    boek.registreer_geval("ontwikkeling", poging, reden="test", **uitkomst)


class TestGrootboekStopregel:
    def _boek(self, tmp_path):
        return gb.Grootboek.nieuw(_opslag13(tmp_path).grootboek, gb.R13)

    def test_inhoudelijk_niet_geaccepteerd_stopt_niet(self, tmp_path):
        boek = self._boek(tmp_path)
        _geval(boek, 1, geaccepteerd=False, technisch_afgerond=True)
        boek.controleer_fasestart("ontwikkeling")
        _geval(boek, 2, geaccepteerd=True, technisch_afgerond=True)
        assert boek.samenvatting()["gestopt"] is False

    def test_technisch_niet_afgerond_stopt_duurzaam(self, tmp_path):
        boek = self._boek(tmp_path)
        _geval(boek, 1, geaccepteerd=False, technisch_afgerond=False)
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            boek.controleer_fasestart("ontwikkeling")
        herlezen = gb.Grootboek.open(boek.pad, gb.R13)
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _stap(herlezen, "ontwikkeling|H2|1", "beoordeling", V)
        assert herlezen.samenvatting()["gestopt"] is True

    def test_open_poging_stopt(self, tmp_path):
        boek = self._boek(tmp_path)
        _stap(boek, "ontwikkeling|H1|1", "beoordeling", V, sluit=False)
        with pytest.raises(gb.BudgetSchendingError, match="zonder duurzame"):
            boek.controleer_fasestart("ontwikkeling")

    def test_technisch_afgerond_verplicht_onder_r13_en_verboden_elders(self, tmp_path):
        boek = self._boek(tmp_path)
        poging = "ontwikkeling|H1|1"
        _stap(boek, poging, "beoordeling", V)
        _stap(boek, poging, "verificatie", W, "beoordeling")
        with pytest.raises(gb.BudgetSchendingError, match="technisch_afgerond"):
            boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="x")
        r12 = gb.Grootboek.nieuw(tmp_path / "r12" / "callgrootboek.jsonl", gb.R12)
        with pytest.raises(gb.BudgetSchendingError, match="technisch_afgerond"):
            r12.registreer_geval("verificatie_alleen", "x", geaccepteerd=True,
                                 reden="x", technisch_afgerond=True)  # fmt: skip


# --- voortgang over onafhankelijke gevallen (offline) -----------------------------------


class TestVoortgang:
    def test_inhoudelijke_mismatch_stopt_de_reeks_niet(self, tmp_path):
        provider = _R8Provider()
        samenvatting = _t13(_omgeving8(provider), tmp_path, _vijf(tmp_path))
        assert provider.stappen == ["beoordeling", "verificatie"] * 5
        gevallen = _soort(tmp_path, "geval")
        assert [g["poging"] for g in gevallen] == [
            f"ontwikkeling|X-0{i}|1" for i in range(5)
        ]
        # Inhoudelijk niet geaccepteerd (mismatch), technisch wel afgerond.
        assert not any(g["geaccepteerd"] for g in gevallen)
        assert all(g["technisch_afgerond"] is True for g in gevallen)
        assert all(g["reden"].startswith("technisch afgerond") for g in gevallen)
        assert samenvatting["grootboek_na"]["gestopt"] is False
        # De inhoudelijke uitkomst blijft per geval zichtbaar: vijf mismatches.
        assert [r["status_correct"] for r in samenvatting["resultaten"]] == [False] * 5
        assert len(_soort(tmp_path, "reservering")) == 10

    def test_zelfde_mismatch_stopt_r12_wel(self):
        """Contrast: de R12-stopregel (elke niet-acceptatie) blijft ongewijzigd."""
        assert gb.R12.stop_alleen_technisch is False

    def test_appafkeuring_zonder_geforceerde_verifier_en_reeks_gaat_door(
        self, tmp_path
    ):
        class _Misvormd(_R8Provider):
            async def chat_completion(self, messages, model, **kwargs):
                antwoord = await super().chat_completion(messages, model, **kwargs)
                if self.stappen.count("beoordeling") == 2 and self.stappen[-1] == (
                    "beoordeling"
                ):
                    return dataclasses.replace(antwoord, text="geen json")
                return antwoord

        provider = _Misvormd()
        samenvatting = _t13(_omgeving8(provider), tmp_path, _vijf(tmp_path))
        # X-01: alleen de beoordeling (malformed), geen verifierstap; de rest door.
        assert provider.stappen == ["beoordeling", "verificatie", "beoordeling",
                                    *["beoordeling", "verificatie"] * 3]  # fmt: skip
        gevallen = _soort(tmp_path, "geval")
        assert len(gevallen) == 5
        assert all(g["technisch_afgerond"] is True for g in gevallen)
        assert gevallen[1]["geaccepteerd"] is False
        assert "appcontrole malformed_response" in gevallen[1]["reden"]
        assert [r["reserveringen"] for r in samenvatting["resultaten"]] == [
            2, 1, 2, 2, 2
        ]  # fmt: skip

    def test_technische_fout_stopt_duurzaam_zonder_retry(self, tmp_path):
        class _Onbereikbaar(_R8Provider):
            async def chat_completion(self, messages, model, **kwargs):
                self.stappen.append("beoordeling")
                raise ConnectionError("netwerk weg")

        provider = _Onbereikbaar()
        pad = _vijf(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _t13(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["beoordeling"]  # geen retry, geen volgend geval
        (geval,) = _soort(tmp_path, "geval")
        assert (geval["geaccepteerd"], geval["technisch_afgerond"]) == (False, False)
        assert geval["reden"].startswith("technische fout")
        # Een nieuwe aanroep hervat niets: de stopregel van het grootboek geldt.
        tweede = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _t13(_omgeving8(tweede), tmp_path, pad, nieuw=False)
        assert tweede.stappen == []
        assert len(_soort(tmp_path, "reservering")) == 1

    def test_elk_geval_exact_eenmaal(self, tmp_path):
        omg = _omgeving8(_R8Provider())
        pad = _vijf(tmp_path)
        _t13(omg, tmp_path, pad)
        opnieuw = _t13(omg, tmp_path, pad, nieuw=False)
        assert opnieuw["aanroepen_gestart"] == 0
        assert len(_soort(tmp_path, "reservering")) == 10

    def test_zes_gevallen_boven_de_fasecap_geweigerd(self, tmp_path):
        provider = _R8Provider()
        pad = _vijf(tmp_path, 6)
        with pytest.raises(
            gb.BudgetSchendingError,
            match="plan vraagt 12 calls; fasecap ontwikkeling laat nog 10",
        ):
            _t13(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == []


# --- de echte invoer --------------------------------------------------------------------


@gevallen_nodig
class TestEchteInvoer:
    def test_gepind_en_geldig(self):
        assert _sha(GEVALLEN) == GEVALLEN_SHA256
        data = json.loads(GEVALLEN.read_text(encoding="utf-8"))
        gevallen, herhaal = pi.valideer_gevallenbestand(data, herhaal_vereist=False)
        assert [g["id"] for g in gevallen] == ["H1", "H2", "H3", "H4", "H5"]
        assert herhaal == []
        assert [g["verwacht"] for g in gevallen] == [
            "pass", "fail", "review_required", "pass", "review_required"
        ]  # fmt: skip

    def test_verwachting_niet_naar_het_model_en_elk_geval_een_modelroute(self):
        data = json.loads(GEVALLEN.read_text(encoding="utf-8"))
        for geval in data["gevallen"]:
            projectie = pi.modelprojectie(geval)
            assert not {"verwacht", "verwacht_per_buur", "grond", "toegestane_vraag",
                        "doel"} & set(projectie)  # fmt: skip
            assert pi.route(projectie, None)["soort"] == "aanroep", geval["id"]

    def test_minimale_varianten_en_geen_betaalvoorwaarde_in_h3(self):
        h1, h2, h3, h4, h5 = (
            pi.modelprojectie(g)
            for g in json.loads(GEVALLEN.read_text(encoding="utf-8"))["gevallen"]
        )
        assert [k for k in h1 if h1[k] != h2[k]] == ["tekst"]
        assert [k for k in h1 if h1[k] != h3[k]] == ["bronnen", "buren"]
        assert "betal" not in json.dumps(h3, ensure_ascii=False).lower()
        assert all(b["bevestigd"] for p in (h1, h2, h3, h4) for b in p["buren"])
        assert h5["buren"] == [] and "verhuur" not in json.dumps(h5).lower()

    def test_citaten_letterlijk_uit_de_invoer(self):
        for geval in json.loads(GEVALLEN.read_text(encoding="utf-8"))["gevallen"]:
            invoer = json.dumps(pi.modelprojectie(geval), ensure_ascii=False)
            for v in geval["verwacht_per_buur"]:
                for veld in ("dragend_citaat", "ontbrekend_kenmerk"):
                    assert v[veld] is None or v[veld] in invoer, (geval["id"], veld)

    def test_droog_vijf_gevallen_tien_stappen_met_freezevelden(
        self, monkeypatch, tmp_path
    ):
        monkeypatch.setitem(runner.PROEVEN, "R13", _r13())
        code = runner.main(["--proef", "R13", "--fase", "ontwikkeling", "--gevallen",
                            str(GEVALLEN), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert droog["proef_id"] == R13_ID
        assert [i["sleutel"] for i in droog["items"]] == [
            f"ontwikkeling|H{i}|1" for i in range(1, 6)
        ]
        grens = gb.R13.kostenbewaking.bytegrens[V]
        assert all(i["payload_bytes"] <= grens for i in droog["items"])
        freeze = droog["freezevelden"]
        assert (freeze["groep"], freeze["proef_id"]) == ("o", R13_ID)
        assert (freeze["dataset_sha256"], freeze["herhaal_ids"]) == (
            GEVALLEN_SHA256,
            [],
        )
        assert {k: freeze[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_ander_bestand_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="T-ontwikkelselectie"):
            runner.main(["--proef", "R13", "--fase", "ontwikkeling", "--gevallen",
                         str(_vijf(tmp_path)), "--uitmap", str(tmp_path / "u"),
                         "--droog"])  # fmt: skip
