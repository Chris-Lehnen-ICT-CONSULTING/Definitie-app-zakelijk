"""DEF-768 R12 — kleine beslissende praktijkvergelijking: registratie, volgorde, stop.

Besluit van Chris (26-09, "Ja akkoord", logs/def768/answer2-microproef-goedkeuring-v1.json):
maximaal 4 SDK-calls. Eerst verify/4 op de oorspronkelijke R9-C5 (V-N4) en
daarna R10-C3 (V-N5) uit V8; alleen als beide `unsupported` op hun eigen
foutdrager krijgen, één R720-antwoord door beoordeling + verificatie. Reserve
0, geen retry, stop bij de eerste mislukking; cumulatief 365 + 4 = 369 binnen
het bestaande 430/USD 25-kader; lokaal plafond USD 1,44 (de volledige
stapbegroting van precies deze vier stappen).

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import shutil
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _gevallenbestand
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import _omgeving8, _R8Provider, _v_invoer
from tests.unit.scripts.test_def768_r9_proef import R8_KOSTEN_NUSD, _r8_boek
from tests.unit.scripts.test_def768_r10_proef import (
    BESLUIT8,
    BESLUIT9,
    BESLUIT10,
    HUIDIG_CONTRACT,
    R9_KOSTEN_NUSD,
    R9_SELECTIE,
    R9_SELECTIE_SHA256,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    _foutdragers,
    _r9_boek,
    _sha,
    _stand,
)
from tests.unit.scripts.test_def768_r11_proef import (
    BESLUIT11,
    R10_KOSTEN_NUSD,
    R11_CONTRACT,
    V8,
    _keten11,
    _r10_boek,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import run_ess05_proef as runner

try:  # de R12-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r12_verificatie_invoer as mk12
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk12 = None

R12_ID = "DEF-768-AI-20260926-R12"
#: Het bij R12 gepinde contract (assess/18, answer/2); sinds answer/3 historisch.
R12_CONTRACT_GEPIND = {
    **HUIDIG_CONTRACT,
    "prompt_version": "ess05-assess/18",
    "answer_schema_version": "ess05-answer/2",
}
R12_MAP = ROOT / "reports" / R12_ID
R11_MAP = ROOT / "reports" / "DEF-768-AI-20260926-R11"
V12 = R12_MAP / "verificatie-invoer-v1.json"
V12_SHA256 = "4a9474c57a7547ca91783f06247759929401f9f27e55fdb8cb835fdfb559f85a"
V8_SHA256 = "d25bae233b6cc35760c8e86ae3d83b35b262ad0bcc1fa9cb4e864d40fec30164"
LOGS = ROOT / "logs" / "def768"
GOEDKEURING = LOGS / "answer2-microproef-goedkeuring-v1.json"
BESLUIT12 = LOGS / "ronde12-microproef-budgetbesluit-v1.json"
BESLUIT12_SHA256 = "356ef64c1bce4c26dbe1e35355d04d5367d2695c0c73529673e2ba2e2a9da04a"
#: De echte R11-stand: één betaalde stap (R720-beoordeling), daarna gestopt (C10).
R11_KOSTEN_NUSD = 102_160_000
#: USD 25 − werkelijke R8–R11-kosten (0,572770).
KADERREST_NUSD = 24_427_230_000
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11")
V = "validation"
W = "ess05_verification"

besluiten_nodig = pytest.mark.skipif(
    not all(
        p.is_file()
        for p in (BESLUIT12, BESLUIT11, BESLUIT10, BESLUIT9, BESLUIT8, TOESTEMMING)
    ),
    reason="git-ignored besluiten ontbreken",
)
v12_nodig = pytest.mark.skipif(
    not (V12.is_file() and V8.is_file()), reason="git-ignored V8/R12-invoer ontbreekt"
)


def _r11_boek(root: Path, *, kosten: int | None = R11_KOSTEN_NUSD):
    """Een R11-grootboek zoals het echte: één betaalde stap, geval niet geaccepteerd."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R11)
    poging = "ontwikkeling|R720|1"
    res = boek.reserveer("ontwikkeling", f"{poging}/beoordeling", invoer_sha256="a" * 64,
                         poging=poging, stap="beoordeling", vorige_stap=None,
                         task_type=V)  # fmt: skip
    boek.sluit(res["seq"], "modelfout", netwerk_gestart=True,
               kosten_werkelijk_nusd=kosten)  # fmt: skip
    boek.registreer_geval("ontwikkeling", poging, geaccepteerd=False, reden="C10")
    return boek


def _keten12(tmp_path: Path, *, r11=None, **kw):
    """(R11-, R10- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r11_opslag = runner.Proefopslag(tmp_path / "r11")
    _r11_boek(r11_opslag.root, **(r11 or {}))
    return (r11_opslag, *_keten11(tmp_path, **kw))


def _bestaande_keten12(tmp_path: Path):
    namen = ("r11", "r10", "r9", "r8", "r7", "r6", "r5", "r4", "r3", "r2", "r1")
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag12(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r12")


def _r12(**anders) -> runner.Proef:
    # Mechaniek op de huidige code (zoals `_r11`); het gepinde R12-contract
    # (answer/2) weigert sinds answer/3 fail-closed.
    anders.setdefault("contract", MappingProxyType(HUIDIG_CONTRACT))
    return dataclasses.replace(runner.PROEVEN["R12"], **anders)


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag12(tmp_path).grootboek
    if not pad.exists():
        return []
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


def _freeze(omg, tmp_path: Path, proef, groep: str = "v") -> Path:
    pad = tmp_path / f"freeze-{groep}.json"
    if not pad.exists():
        pad.write_text(
            json.dumps(runner.freezevelden(omg, proef, groep)), encoding="utf-8"
        )
    return pad


def _v12(omg, tmp_path, pad, *, proef=None, nieuw=True):
    proef = proef or _r12(v_invoer_sha256=_sha(pad))
    keten = _keten12(tmp_path) if nieuw else _bestaande_keten12(tmp_path)
    return asyncio.run(
        runner.voer_v_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag12(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef),
            voorganger_opslag=keten,
            nieuw_grootboek=nieuw,
        )
    )


_O_FREEZE = object()  # standaard: een verse o-freeze uit de huidige omgeving


def _t12(omg, tmp_path, pad, *, nieuw=False, freeze=_O_FREEZE, **kw):
    keten = _keten12(tmp_path) if nieuw else _bestaande_keten12(tmp_path)
    proef = _r12(t_ontwikkelinvoer_sha256=_sha(pad))
    if freeze is _O_FREEZE:  # R12-01: ook R720 hangt aan een freeze
        freeze = _freeze(omg, tmp_path, proef, "o")
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase="ontwikkeling",
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag12(tmp_path),
            proef=proef,
            freeze=freeze,
            voorganger_opslag=keten,
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


@pytest.fixture
def v12(tmp_path):
    if not V12.is_file():
        pytest.skip("git-ignored R12-invoer ontbreekt")
    pad = tmp_path / "v12.json"
    shutil.copyfile(V12, pad)
    return pad, json.loads(pad.read_text(encoding="utf-8"))


def _reserveringen(tmp_path) -> list[str]:
    return [r["poging"] for r in _soort(tmp_path, "reservering")]


# --- identiteit, caps en kosten -----------------------------------------------------------


class TestIdentiteit:
    def test_vier_stappen_reserve_nul_voorganger_r11_cumulatief_369(self):
        r12 = gb.R12
        assert r12.proef_id == R12_ID
        assert dict(r12.fasecaps) == {"verificatie_alleen": 2, "ontwikkeling": 2}
        assert (r12.reserve_max, r12.totaal_max) == (0, 4)
        assert r12.voorganger is gb.R11
        assert r12.cumulatief_max == 369 == 365 + 4
        assert r12.modelstappen_per_geval == 2

    def test_eerst_twee_verificaties_dan_een_r720_met_stop(self):
        r12 = gb.R12
        assert dict(r12.fasestappen) == {
            "verificatie_alleen": (W,),
            "ontwikkeling": (V, W),
        }
        assert dict(r12.fasevolgorde) == {
            "verificatie_alleen": (),
            "ontwikkeling": ("verificatie_alleen",),
        }
        assert (r12.stop_bij_eerste_fout, r12.gedeelde_codebinding) == (True, True)
        # V én R720 elk een eindgroep met freeze (R12-01); geen T-eind of T-herhaling.
        assert [(g.naam, set(g.fases), g.herhaal_aantal) for g in r12.eindgroepen] == [
            ("v", {"verificatie_alleen"}, 0),
            ("o", {"ontwikkeling"}, 0),
        ]
        assert "t_eind" not in r12.fasecaps and "t_herhaling" not in r12.fasecaps

    def test_zelfde_model_tokens_en_bytegrenzen_lokaal_plafond_1_44(self):
        kb12, kb8 = gb.R12.kostenbewaking, gb.R8.kostenbewaking
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb12, veld) == getattr(kb8, veld), veld
        assert kb12.max_tokens == 3000
        assert dict(kb12.bytegrens) == dict(kb8.bytegrens)
        # Plafond = de volledige stapbegroting van precies deze vier stappen.
        assert gb.begroting_nusd(gb.R12) == 2 * 375_000_000 + 315_000_000 + 375_000_000
        assert kb12.plafond_nusd == gb.begroting_nusd(gb.R12) == 1_440_000_000
        assert kb12.plafond_nusd <= 2_000_000_000  # mandaat: maximaal USD 2
        assert gb.R12.kostenkader_nusd == 25_000_000_000

    def test_r11_en_ouder_ongewijzigd(self):
        assert (gb.R11.totaal_max, gb.R11.cumulatief_max) == (66, 430)
        assert gb.R11.kostenbewaking.plafond_nusd == 24_529_390_000
        assert (gb.R10.totaal_max, gb.R10.cumulatief_max) == (65, 427)

    def test_r12_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "r12" / "callgrootboek.jsonl", gb.R12)
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(boek.pad, gb.R11)
        assert gb.Grootboek.open(boek.pad, gb.R12).identiteit is gb.R12


class TestCumulatiefEnKostenkader:
    def _keten_boeken(self, tmp_path, **kw):
        opslagen = _keten12(tmp_path, **kw)
        return [
            gb.Grootboek.lees(o.grootboek, i)
            for o, i in zip(opslagen, gb.voorgangerketen(gb.R12), strict=True)
        ]

    def test_cumulatief_369_past_370_niet(self, tmp_path):
        # 365 werkelijke R1–R11-calls: vijf rondes à 57, twee à 37, R8 één,
        # R9 twee, R10 twee, R11 één.
        keten = [
            _r11_boek(tmp_path / "r11"),
            _r10_boek(tmp_path / "r10"),
            _r9_boek(tmp_path / "r9"),
            _r8_boek(tmp_path / "r8"),
        ]
        for naam, identiteit, n in (
            ("r7", gb.R7, 37),
            ("r6", gb.R6, 37),
            ("r5", gb.R5, 57),
            ("r4", gb.R4, 57),
            ("r3", gb.R3, 57),
            ("r2", gb.R2, 57),
            ("r1", gb.R1, 57),
        ):
            keten_boek(tmp_path / naam, identiteit, n)
            keten.append(
                gb.Grootboek.lees(tmp_path / naam / "callgrootboek.jsonl", identiteit)
            )
        assert sum(b.samenvatting()["totaal"] for b in keten) == 365
        boek = gb.Grootboek.nieuw(tmp_path / "r12" / "callgrootboek.jsonl", gb.R12)
        gb.controleer_cumulatief(boek, keten, 4)
        with pytest.raises(gb.BudgetSchendingError, match="369"):
            gb.controleer_cumulatief(boek, keten, 5)

    def test_kostenkader_met_de_werkelijke_r8_tot_r11_kosten(self, tmp_path):
        keten = self._keten_boeken(tmp_path)
        assert [b.kostenstand()["lopend_nusd"] for b in keten[:4]] == [
            R11_KOSTEN_NUSD,
            R10_KOSTEN_NUSD,
            R9_KOSTEN_NUSD,
            R8_KOSTEN_NUSD,
        ]
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:4])
        assert lopend + KADERREST_NUSD == 25_000_000_000
        boek = gb.Grootboek.nieuw(tmp_path / "r12" / "callgrootboek.jsonl", gb.R12)
        gb.controleer_cumulatief(boek, keten, 1)

    def test_kostenkader_weigert_als_voorgangers_boven_de_kaderrest_komen(
        self, tmp_path
    ):
        # R11 telt zoveel dat R11 + lokaal plafond boven USD 25 komt.
        teveel = (
            25_000_000_000
            - 1_440_000_000
            - (R10_KOSTEN_NUSD + R9_KOSTEN_NUSD + R8_KOSTEN_NUSD)
            + 1
        )
        keten = self._keten_boeken(tmp_path, r11={"kosten": teveel})
        boek = gb.Grootboek.nieuw(tmp_path / "r12" / "callgrootboek.jsonl", gb.R12)
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            gb.controleer_cumulatief(boek, keten, 1)

    @pytest.mark.skipif(
        not all(runner.PROEVEN[n].opslag.grootboek.is_file() for n in OUDE_RONDES),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_365_calls_usd_0_572770_vier_passen_vijf_niet(
        self, tmp_path
    ):
        """De werkelijke keten R11 … R1 (alleen lezen)."""
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed(OUDE_RONDES)
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 365
        lopend = [b.kostenstand()["lopend_nusd"] for b in keten[:4]]
        assert lopend == [R11_KOSTEN_NUSD, R10_KOSTEN_NUSD, R9_KOSTEN_NUSD,
                          R8_KOSTEN_NUSD]  # fmt: skip
        assert sum(lopend) == 572_770_000
        boek = gb.Grootboek.nieuw(tmp_path / "r12" / "callgrootboek.jsonl", gb.R12)
        gb.controleer_cumulatief(boek, keten, 4)
        with pytest.raises(gb.BudgetSchendingError, match="369"):
            gb.controleer_cumulatief(boek, keten, 5)


# --- registratie ------------------------------------------------------------------------


class TestRegistratie:
    def test_r12_geregistreerd_met_eigen_opslag_invoer_besluit_en_contract(self):
        proef = runner.PROEVEN["R12"]
        assert proef.identiteit is gb.R12
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R12_MAP
        # R720: exact de oorspronkelijke R9-selectie; V: de R12-selectie uit V8.
        assert proef.t_ontwikkelinvoer_sha256 == R9_SELECTIE_SHA256
        assert proef.v_invoer_sha256 == runner.R12_V_INVOER_SHA256 == V12_SHA256
        assert proef.g_ontwikkelinvoer_sha256 is None
        assert proef.budgetbesluit == BESLUIT12
        assert proef.budgetbesluit_sha256 == runner.R12_BUDGETBESLUIT_SHA256
        assert runner.R12_BUDGETBESLUIT_SHA256 == BESLUIT12_SHA256
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        # Het huidige contract (answer/2), geen verruiming, expliciete kaderrest.
        assert dict(proef.contract) == R12_CONTRACT_GEPIND
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST_NUSD

    def test_oude_registraties_ongewijzigd(self):
        """R1–R10 gesloten; R11 ongewijzigd (gestopt grootboek, contract answer/1)."""
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == [
            "R11",
            "R12",
            "R13",
            "R14",
            "R15",
        ]
        r11 = runner.PROEVEN["R11"]
        assert dict(r11.contract) == R11_CONTRACT
        assert r11.kaderverruiming_modelstappen == 3
        assert all(p.kaderrest_nusd is None for n, p in runner.PROEVEN.items()
                   if n not in ("R12", "R13", "R14", "R15"))  # fmt: skip

    def test_kopie_van_r12_start_geen_echte_call(self):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="geregistreerde"):
            runner._controleer_registratie(omg, _r12(kaderrest_nusd=None))
        assert provider.aanroepen == []

    @besluiten_nodig
    def test_echte_poorten_van_r12_weigeren_sinds_answer3_op_het_contract(self):
        """R12 blijft geregistreerd, maar het gepinde answer/2-contract weigert."""
        proef = runner.PROEVEN["R12"]
        omg = dataclasses.replace(_omgeving8(_R8Provider()), echt=True)
        runner._controleer_opslag(omg, proef.opslag, proef)
        runner._controleer_goedkeuring(omg, proef)
        runner._controleer_productiegrenzen(omg, proef)
        runner._controleer_kostenroute(omg, proef)
        with pytest.raises(gb.BudgetSchendingError, match="contractidentiteit"):
            runner._controleer_contract(omg, proef)
        assert runner._besluit_voor(omg, proef) == BESLUIT12_SHA256

    @besluiten_nodig
    def test_cli_echt_r12_bouwt_de_live_omgeving_op_productiegrenzen(
        self, monkeypatch, tmp_path
    ):
        gebouwd = {}
        voor = _stand(R12_MAP / "callgrootboek.jsonl")

        class _GestoptError(Exception):
            pass

        def _live(**kw):
            gebouwd.update(kw)
            raise _GestoptError  # vóór client, grootboek en netwerk

        monkeypatch.setattr(runner, "live_omgeving", _live)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(_GestoptError):
            runner.main(["--proef", "R12", "--fase", "verificatie_alleen",
                         "--gevallen", str(pad), "--echt"])  # fmt: skip
        assert gebouwd == {"timeout": 60, "max_tokens_t": 3000,
                           "verifier_max_tokens": 3000}  # fmt: skip
        assert _stand(R12_MAP / "callgrootboek.jsonl") == voor

    @pytest.mark.parametrize("fase", ["t_eind", "t_herhaling", "g", "g_ontwikkeling"])
    def test_andere_fases_bestaan_niet_in_r12(self, tmp_path, capsys, fase):
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(SystemExit) as fout:
            runner.main(["--proef", "R12", "--fase", fase, "--gevallen", str(pad),
                         "--g-invoer", str(pad), "--droog"])  # fmt: skip
        assert fout.value.code == 2
        assert "bestaat niet in ronde R12" in capsys.readouterr().err


# --- budgetbesluit en kaderrest ---------------------------------------------------------


def _besluit12(tmp_path: Path, bron: Path = BESLUIT12, **anders) -> Path:
    data = json.loads(bron.read_text(encoding="utf-8"))
    for sleutel, waarde in anders.items():
        if waarde is None:
            data.pop(sleutel, None)
        else:
            data[sleutel] = waarde
    pad = tmp_path / f"besluit-{bron.stem}.json"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


@besluiten_nodig
class TestBudgetbesluit:
    def test_besluit_gebonden_aan_het_goedkeuringsbewijs(self):
        data = json.loads(BESLUIT12.read_text(encoding="utf-8"))
        bron = json.loads(GOEDKEURING.read_text(encoding="utf-8"))
        assert _sha(BESLUIT12) == runner.R12_BUDGETBESLUIT_SHA256
        assert data["bron"] == "logs/def768/answer2-microproef-goedkeuring-v1.json"
        assert data["bron_sha256"] == _sha(GOEDKEURING)
        assert data["gebruikersantwoord"] == bron["user_message"] == "Ja akkoord"
        assert bron["operational_scope"]["max_sdk_calls"] == 4
        assert bron["operational_scope"]["reserve_calls"] == 0
        assert (data["extra_modelaanroepen_max"], data["cumulatief_max"]) == (4, 369)
        assert (data["kostenbudget_usd"], data["kaderrest_usd"]) == (
            "1.440000",
            "24.427230",
        )
        # Geen verruiming en nooit de 66-callproef of plafond 431.
        assert not {k for k in data if k in runner._VERRUIMINGSVELDEN}
        assert "66" not in json.dumps(data["fasen_modelstappen_max"])

    def test_besluit_past_op_r12_en_eerdere_besluiten_blijven_geldig(self):
        assert (
            runner.controleer_budgetbesluit(runner.PROEVEN["R12"]) == BESLUIT12_SHA256
        )
        for naam in ("R11", "R10", "R9", "R8"):
            proef = runner.PROEVEN[naam]
            assert runner.controleer_budgetbesluit(proef) == proef.budgetbesluit_sha256

    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 5},
            {"extra_modelaanroepen_max": 66},
            {"cumulatief_max": 370},
            {"cumulatief_max": 431},
            {"historisch_verbruik": 364},
            {"reserve": 1},
            {"kostenbudget_usd": "2.00"},
            {"kostenbudget_usd": "1.440001"},
            {"fasen_modelstappen_max": {"verificatie_alleen": 2, "ontwikkeling": 4}},
            {"fasen_modelstappen_max": {"verificatie_alleen": 2, "ontwikkeling": 2,
                                        "t_eind": 0}},
            {"gebruikersantwoord": ""},
            {"kaderrest_usd": "24.427231"},
            {"kaderrest_usd": None},
            {"r11_verbruik_usd": "0.102161"},
            {"r11_verbruik_usd": "0.102159"},  # ook te laag weigert (exact kader)
            {"r11_verbruik_usd": None},
            {"r11_verbruik_modelstappen": 2},
            {"r8_verbruik_usd": "0.098734"},
            {"oorspronkelijk_kostenbudget_usd": "26.00"},
            {"oorspronkelijk_cumulatief_plafond": 430},
            {"goedgekeurde_verruiming_modelaanroepen": 3},
            {"nieuw_cumulatief_plafond": 431},
        ],
    )  # fmt: skip
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        pad = _besluit12(tmp_path, **anders)
        proef = _r12(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)

    def test_ongepind_of_ontbrekend_besluit_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r12(budgetbesluit=_besluit12(tmp_path)))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r12(budgetbesluit=tmp_path / "geen.json"))

    def test_zonder_geregistreerde_kaderrest_past_het_lage_plafond_niet(self):
        """Zonder kaderrest geldt de oude regel: verbruik + plafond == USD 25."""
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r12(kaderrest_nusd=None))

    def test_plafond_boven_de_kaderrest_geweigerd(self, tmp_path):
        # Verbruik zo hoog dat de kaderrest (0,97) onder het plafond (1,44) ligt.
        pad = _besluit12(tmp_path, r11_verbruik_usd="23.559390",
                         kaderrest_usd="0.970000")  # fmt: skip
        proef = _r12(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad),
                     kaderrest_nusd=970_000_000)  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="kaderrest"):
            runner.controleer_budgetbesluit(proef)

    def test_kaderrest_opent_geen_eerdere_ronde(self, tmp_path):
        """Een ronde zonder geregistreerde kaderrest weigert een besluit dat er
        een noemt; de exacte R9–R11-regel blijft."""
        pad = _besluit12(tmp_path, BESLUIT11, kaderrest_usd="24.529390")
        proef = dataclasses.replace(
            runner.PROEVEN["R11"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="kaderrest"):
            runner.controleer_budgetbesluit(proef)


# --- volgorde, caps en stopregel (offline) ----------------------------------------------


class TestVolgordeEnStop:
    def test_r720_voor_de_verificaties_geweigerd(self, tmp_path):
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="verificatie_alleen"):
            _t12(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 1),
                 nieuw=True)  # fmt: skip
        assert provider.aanroepen == []
        assert _reserveringen(tmp_path) == []

    def test_drie_v_items_boven_de_fasecap_geweigerd(self, tmp_path):
        pad, items = _v_invoer(tmp_path, ("fout", "fout", "fout"))
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        with pytest.raises(gb.BudgetSchendingError, match="fasecap verificatie_alleen"):
            _v12(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == []

    def test_verificatie_alleen_zonder_freeze_geweigerd(self, tmp_path):
        pad, items = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        with pytest.raises(gb.BudgetSchendingError, match="freeze"):
            asyncio.run(runner.voer_v_fase(
                _omgeving8(provider), gevallenpad=pad, uitmap=tmp_path / "uit",
                opslag=_opslag12(tmp_path), proef=_r12(v_invoer_sha256=_sha(pad)),
                freeze=None, voorganger_opslag=_keten12(tmp_path), nieuw_grootboek=True,
            ))  # fmt: skip
        assert provider.stappen == []

    def test_vier_stappen_dan_is_alles_op(self, tmp_path):
        """V (2) → R720 (2) = 4; daarna start geen enkele stap meer."""
        pad, items = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        omg = _omgeving8(provider)
        _v12(omg, tmp_path, pad)
        _t12(omg, tmp_path, _gevallenbestand(tmp_path, 1))
        assert provider.stappen == ["verificatie", "verificatie", "beoordeling",
                                    "verificatie"]  # fmt: skip
        assert all(g["geaccepteerd"] for g in _soort(tmp_path, "geval"))
        assert len(_reserveringen(tmp_path)) == 4
        # Hetzelfde geval opnieuw: overgeslagen (één sleutel = één poging).
        opnieuw = _t12(omg, tmp_path, _gevallenbestand(tmp_path, 1, "zelfde.json"))
        assert opnieuw["aanroepen_gestart"] == 0
        # Een nieuw ontwikkelbestand: sinds R12-01 al geweigerd op de eindbinding
        # (andere dataset), vóór fasecap, reservering en netwerk.
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding van de eerste"):
            _t12(omg, tmp_path, _gevallenbestand(tmp_path, 2, "tweede.json"))
        assert len(provider.stappen) == 4
        assert len(_reserveringen(tmp_path)) == 4

    def test_kostenplan_laat_na_de_verificaties_maar_een_r720_toe(self, tmp_path):
        """Onafhankelijk van de fasecap: het lokale plafond dekt geen vijfde stap."""
        boek = gb.Grootboek.nieuw(_opslag12(tmp_path).grootboek, gb.R12)
        for naam in ("V-N4", "V-N5"):  # onbekende kosten tellen met hun stapgrens
            poging = f"verificatie_alleen|{naam}|1"
            res = boek.reserveer("verificatie_alleen", f"{poging}/verificatie",
                                 invoer_sha256="a" * 64, poging=poging,
                                 stap="verificatie", vorige_stap=None, task_type=W,
                                 binding={"dataset_sha256": "a" * 64, "herhaal_ids": [],
                                          "code_sha256": "b" * 64,
                                          "config_sha256": "c" * 64,
                                          "freeze_sha256": "d" * 64})  # fmt: skip
            boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
            boek.registreer_geval("verificatie_alleen", poging, geaccepteerd=True,
                                  reden="test")  # fmt: skip
        runner._controleer_kostenplan(boek, "ontwikkeling", 1)
        with pytest.raises(gb.BudgetSchendingError, match="kostenplan"):
            runner._controleer_kostenplan(boek, "ontwikkeling", 2)

    def test_technische_mislukking_stopt_zonder_retry(self, tmp_path):
        class _Onbereikbaar(_R8Provider):
            async def chat_completion(self, messages, model, **kwargs):
                self.stappen.append("verificatie")
                raise ConnectionError("netwerk weg")

        pad, _ = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _Onbereikbaar()
        with pytest.raises(gb.BudgetSchendingError):
            _v12(_omgeving8(provider), tmp_path, pad)
        assert len(provider.stappen) == 1  # geen retry, geen tweede item
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is False
        # Geen reserve en geen technische herhaling in de V-fase.
        with pytest.raises(gb.BudgetSchendingError):
            asyncio.run(runner.voer_v_fase(
                _omgeving8(_R8Provider()), gevallenpad=pad, uitmap=tmp_path / "uit",
                opslag=_opslag12(tmp_path), proef=_r12(v_invoer_sha256=_sha(pad)),
                freeze=tmp_path / "freeze-v.json",
                voorganger_opslag=_bestaande_keten12(tmp_path), nieuw_grootboek=False,
                technische_herhalingen=(geval["poging"],),
            ))  # fmt: skip
        assert len(_reserveringen(tmp_path)) == 1


# --- R12-01: R720 aan dezelfde code en configuratie als V --------------------------------

_BINDING_V = {
    "dataset_sha256": "a" * 64,
    "herhaal_ids": [],
    "code_sha256": "b" * 64,
    "config_sha256": "c" * 64,
    "freeze_sha256": "d" * 64,
}


def _v_geaccepteerd_in_grootboek(tmp_path: Path) -> gb.Grootboek:
    """Twee geaccepteerde V-gevallen, gebonden aan code b… en configuratie c…."""
    boek = gb.Grootboek.nieuw(_opslag12(tmp_path).grootboek, gb.R12)
    for naam in ("V-N4", "V-N5"):
        poging = f"verificatie_alleen|{naam}|1"
        res = boek.reserveer("verificatie_alleen", f"{poging}/verificatie",
                             invoer_sha256="a" * 64, poging=poging,
                             stap="verificatie", vorige_stap=None, task_type=W,
                             binding=_BINDING_V)  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
        boek.registreer_geval("verificatie_alleen", poging, geaccepteerd=True,
                              reden="test")  # fmt: skip
    return boek


def _o_binding(**anders) -> dict:
    binding = {**_BINDING_V, "dataset_sha256": "e" * 64, "freeze_sha256": "1" * 64}
    binding.update(anders)
    return binding


def _drift(monkeypatch, soort: str) -> None:
    """Code- of configuratiedrift ná de V-fase (labels en contract gelijk)."""
    if soort == "code":
        monkeypatch.setattr(runner, "code_sha256", lambda: "f" * 64)
    else:
        echt = runner.effectieve_config
        monkeypatch.setattr(
            runner, "effectieve_config", lambda omg: {**echt(omg), "drift": 1}
        )


class TestR720Codebinding:
    """R12-01 (review): R720 gebruikt vóór reservering en netwerk dezelfde bevroren
    code- en effectieve-configuratiebinding als de voorafgaande V-fase."""

    def test_grootboek_zonder_binding_geweigerd(self, tmp_path):
        """De reproductie uit de review: geen binding werd stil aanvaard."""
        boek = _v_geaccepteerd_in_grootboek(tmp_path)
        boek.controleer_fasestart("ontwikkeling")
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            boek.controleer_binding("ontwikkeling", "e" * 64, None)

    @pytest.mark.parametrize(
        ("anders", "veld"),
        [({"code_sha256": "f" * 64}, "code_sha256"),
         ({"config_sha256": "9" * 64}, "config_sha256")],
    )  # fmt: skip
    def test_grootboek_weigert_code_of_configuratiedrift(self, tmp_path, anders, veld):
        boek = _v_geaccepteerd_in_grootboek(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match=veld):
            boek.controleer_binding("ontwikkeling", "e" * 64, _o_binding(**anders))

    def test_grootboek_staat_gelijke_binding_toe(self, tmp_path):
        boek = _v_geaccepteerd_in_grootboek(tmp_path)
        assert boek.controleer_binding("ontwikkeling", "e" * 64, _o_binding()) == (
            _o_binding()
        )

    def test_historische_ontwikkelfases_ongewijzigd(self):
        for identiteit in (gb.R8, gb.R9, gb.R10, gb.R11):
            assert identiteit.eindgroep("ontwikkeling") is None

    def _na_v(self, tmp_path):
        pad, items = _v_invoer(tmp_path, ("fout", "fout"))
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        omg = _omgeving8(provider)
        _v12(omg, tmp_path, pad)
        assert len(provider.stappen) == 2
        return omg, provider, _gevallenbestand(tmp_path, 1)

    def test_gelijke_binding_r720_bindt_aan_v(self, tmp_path):
        omg, provider, pad = self._na_v(tmp_path)
        _t12(omg, tmp_path, pad)
        assert provider.stappen == ["verificatie"] * 2 + ["beoordeling", "verificatie"]
        bindingen = [r["binding"] for r in _soort(tmp_path, "reservering")]
        assert all(b is not None for b in bindingen)
        for veld in ("code_sha256", "config_sha256"):
            assert len({b[veld] for b in bindingen}) == 1, veld
        # R720 heeft een eigen dataset en een eigen freeze (groep o).
        assert bindingen[2]["dataset_sha256"] == _sha(pad)
        assert bindingen[2]["freeze_sha256"] != bindingen[0]["freeze_sha256"]

    @pytest.mark.parametrize(
        ("soort", "veld"), [("code", "code_sha256"), ("config", "config_sha256")]
    )
    def test_drift_met_passende_freeze_door_het_grootboek_geweigerd(
        self, monkeypatch, tmp_path, soort, veld
    ):
        """Ook een freeze die de drift zelf vastlegt, opent R720 niet."""
        omg, provider, pad = self._na_v(tmp_path)
        _drift(monkeypatch, soort)
        with pytest.raises(gb.BudgetSchendingError, match=f"{veld}.*gedeelde"):
            _t12(omg, tmp_path, pad)
        assert len(provider.stappen) == 2
        assert len(_reserveringen(tmp_path)) == 2

    @pytest.mark.parametrize(
        ("soort", "veld"),
        [("code", "code_sha256"), ("config", "effectieve_config_sha256")],
    )
    def test_drift_na_de_freeze_door_de_freeze_geweigerd(
        self, monkeypatch, tmp_path, soort, veld
    ):
        omg, provider, pad = self._na_v(tmp_path)
        freeze = _freeze(omg, tmp_path, _r12(t_ontwikkelinvoer_sha256=_sha(pad)), "o")
        _drift(monkeypatch, soort)
        with pytest.raises(gb.BudgetSchendingError, match=f"past niet.*{veld}"):
            _t12(omg, tmp_path, pad, freeze=freeze)
        assert len(provider.stappen) == 2
        assert len(_reserveringen(tmp_path)) == 2

    def test_zonder_freeze_geweigerd(self, tmp_path):
        omg, provider, pad = self._na_v(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="--freeze is verplicht"):
            _t12(omg, tmp_path, pad, freeze=None)
        assert len(provider.stappen) == 2

    @pytest.mark.parametrize("groep", ["v", "t"])
    def test_verkeerde_freeze_geweigerd(self, tmp_path, groep):
        omg, provider, pad = self._na_v(tmp_path)
        verkeerd = _freeze(omg, tmp_path, _r12(), groep)
        with pytest.raises(gb.BudgetSchendingError, match="groep"):
            _t12(omg, tmp_path, pad, freeze=verkeerd)
        assert len(provider.stappen) == 2
        assert len(_reserveringen(tmp_path)) == 2

    def test_onleesbare_freeze_geweigerd(self, tmp_path):
        omg, provider, pad = self._na_v(tmp_path)
        kapot = tmp_path / "kapot.json"
        kapot.write_text("{", encoding="utf-8")
        with pytest.raises(gb.BudgetSchendingError, match="onleesbaar"):
            _t12(omg, tmp_path, pad, freeze=kapot)
        assert len(provider.stappen) == 2


# --- de echte R12-invoer: V-N4 dan V-N5 (offline, fake verifier) ------------------------


@v12_nodig
class TestEchteInvoer:
    def test_eerst_r9_c5_dan_r10_c3_beide_gedetecteerd(self, tmp_path, v12):
        pad, data = v12
        provider = _R8Provider(uitkomsten=_foutdragers(data["items"]))
        uitkomst = _v12(_omgeving8(provider), tmp_path, pad)
        assert _reserveringen(tmp_path) == [
            "verificatie_alleen|V-N4|1",
            "verificatie_alleen|V-N5|1",
        ]
        assert [
            (g["poging"], g["geaccepteerd"]) for g in _soort(tmp_path, "geval")
        ] == [
            ("verificatie_alleen|V-N4|1", True),
            ("verificatie_alleen|V-N5|1", True),
        ]
        assert uitkomst["aanroepen_gestart"] == 2
        assert uitkomst["grootboek_na"]["kosten"]["plafond_nusd"] == 1_440_000_000

    @pytest.mark.parametrize(
        ("index", "uitkomst", "reden"),
        [
            (0, {"claim:C5": "undetermined"}, "unsupported"),
            (0, {}, "niet gedetecteerd"),
            (0, {"completeness": "unsupported"}, "buiten de foutdragende items"),
            (1, {"claim:C3": "undetermined"}, "unsupported"),
            (1, {}, "niet gedetecteerd"),
            (1, {"claim:C5": "unsupported"}, "buiten de foutdragende items"),
        ],
    )
    def test_eerste_mislukking_stopt_alles(self, tmp_path, v12, index, uitkomst, reden):
        pad, data = v12
        uitkomsten = _foutdragers(data["items"])
        uitkomsten[data["items"][index]["concept_hash"]] = uitkomst
        provider = _R8Provider(uitkomsten=uitkomsten)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v12(_omgeving8(provider), tmp_path, pad)
        # V-N4 mislukt: V-N5 start niet; daarna ook geen R720.
        assert provider.stappen == ["verificatie"] * (index + 1)
        laatste = _soort(tmp_path, "geval")[-1]
        assert laatste["geaccepteerd"] is False and reden in laatste["reden"]
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _t12(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 1))
        assert provider.stappen == ["verificatie"] * (index + 1)

    def test_schemaweigering_is_geen_detectie(self, tmp_path, v12):
        pad, data = v12
        provider = _R8Provider(
            uitkomsten=_foutdragers(data["items"]), hash_per_concept={"alle": "0" * 64}
        )
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v12(_omgeving8(provider), tmp_path, pad)
        (geval,) = _soort(tmp_path, "geval")
        assert "schemaweigering" in geval["reden"]
        assert provider.stappen == ["verificatie"]

    def test_v8_zelf_geweigerd_voor_r12(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="verifier-only-invoer"):
            runner.main(["--proef", "R12", "--fase", "verificatie_alleen", "--gevallen",
                         str(V8), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    def test_droog_r12_invoer_en_r9_selectie(self, monkeypatch, tmp_path):
        # Mechaniek onder de huidige code (kopie met huidig contract), zoals R11.
        monkeypatch.setitem(runner.PROEVEN, "R12", _r12())
        code = runner.main(["--proef", "R12", "--fase", "verificatie_alleen",
                            "--gevallen", str(V12), "--uitmap", str(tmp_path / "v"),
                            "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = (tmp_path / "v").glob("droog-verificatie_alleen-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R12_ID, 2)
        assert [i["sleutel"] for i in droog["items"]] == [
            "verificatie_alleen|V-N4|1",
            "verificatie_alleen|V-N5|1",
        ]
        grens = gb.R12.kostenbewaking.bytegrens[W]
        assert all(i["payload_bytes"] <= grens for i in droog["items"])
        freeze = droog["freezevelden"]
        assert (freeze["groep"], freeze["proef_id"]) == ("v", R12_ID)
        assert {k: freeze[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        if R9_SELECTIE.is_file():
            code = runner.main(["--proef", "R12", "--fase", "ontwikkeling",
                                "--gevallen", str(R9_SELECTIE), "--uitmap",
                                str(tmp_path / "o"), "--droog"])  # fmt: skip
            assert code == 0
            (bestand,) = (tmp_path / "o").glob("droog-ontwikkeling-*/droogrun.json")
            droog = json.loads(bestand.read_text(encoding="utf-8"))
            assert [i["sleutel"] for i in droog["items"]] == ["ontwikkeling|R720|1"]
            # R12-01: ook R720 krijgt freezevelden (groep o, eigen dataset) met
            # exact de code, configuratie en prompts van de V-freeze.
            o = droog["freezevelden"]
            assert (o["groep"], o["proef_id"]) == ("o", R12_ID)
            assert (o["dataset_sha256"], o["herhaal_ids"]) == (R9_SELECTIE_SHA256, [])
            verschil = {k for k in o if o[k] != freeze.get(k)}
            assert verschil == {"groep", "dataset_sha256"}
        assert not list(tmp_path.rglob("*.jsonl"))


# --- de R12-invoermaker ------------------------------------------------------------------


class TestMaker:
    def test_bron_selectie_en_doel_gepind(self):
        assert (mk12.V8, mk12.V8_SHA256) == (V8, V8_SHA256)
        assert mk12.SELECTIE == (("V-N4", "claim:C5"), ("V-N5", "claim:C3"))
        assert mk12.DOEL == V12

    @v12_nodig
    def test_vastgelegde_invoer_reproduceerbaar_en_gepind(self, tmp_path):
        doel = tmp_path / "v12.json"
        assert mk12.main(["--doel", str(doel)]) == 0
        # Sinds answer/3 legt de maker het huidige contract vast; verder
        # reproduceert hij de gepinde (answer/2-)invoer exact.
        nieuw = json.loads(doel.read_text(encoding="utf-8"))
        oud = json.loads(V12.read_text(encoding="utf-8"))
        assert nieuw["herkomst"].pop("contract") == HUIDIG_CONTRACT
        assert oud["herkomst"].pop("contract") == R12_CONTRACT_GEPIND
        assert nieuw == oud
        assert _sha(V12) == runner.R12_V_INVOER_SHA256 == V12_SHA256
        assert _sha(V8) == V8_SHA256  # V8 alleen gelezen

    @v12_nodig
    def test_items_exact_uit_v8_originele_concepten_met_historisch_oordeel(self):
        data = json.loads(V12.read_text(encoding="utf-8"))
        v8 = {i["id"]: i for i in json.loads(V8.read_text(encoding="utf-8"))["items"]}
        assert [i["id"] for i in data["items"]] == ["V-N4", "V-N5"]
        assert all(i == v8[i["id"]] for i in data["items"])
        historisch = [i["bron"]["historisch_verifieroordeel"] for i in data["items"]]
        assert [(h["item"], h["outcome"]) for h in historisch] == [
            ("claim:C5", "supported"),
            ("claim:C3", "supported"),
        ]
        assert data["herkomst"]["r11_verificatie_invoer"]["sha256"] == V8_SHA256
        assert data["herkomst"]["contract"] == R12_CONTRACT_GEPIND

    @v12_nodig
    def test_invoer_bindt_aan_de_huidige_code(self):
        items = runner.valideer_v_invoer(
            json.loads(V12.read_text(encoding="utf-8")), _omgeving8(_R8Provider())
        )
        assert [v.sleutel for v in items] == [
            "verificatie_alleen|V-N4|1",
            "verificatie_alleen|V-N5|1",
        ]

    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        doel = tmp_path / "bestaat.json"
        doel.write_text("{}", encoding="utf-8")
        with pytest.raises(FileExistsError):
            mk12.main(["--doel", str(doel)])
        assert doel.read_text(encoding="utf-8") == "{}"

    def test_gewijzigde_v8_geweigerd(self, tmp_path):
        kopie = tmp_path / "v8.json"
        kopie.write_bytes(V8.read_bytes() + b" " if V8.is_file() else b"{}")
        with pytest.raises(mk12.MakerfoutError, match="V8"):
            mk12.maak_verificatie_invoer(v8=kopie)


def test_maker_leest_de_verborgen_eindset_niet():
    bron = (ROOT / "scripts" / "ess05" / "maak_r12_verificatie_invoer.py").read_text(
        encoding="utf-8"
    )
    assert "eindset" not in bron.lower()
    assert "answer2_uit_" not in bron  # geen getransformeerde fixture als bron
