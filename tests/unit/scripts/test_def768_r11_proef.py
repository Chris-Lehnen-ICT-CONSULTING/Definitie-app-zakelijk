"""DEF-768 R11 — gerichte proef na het R10-C3-herstel: registratie en V8, offline.

Besluit van Chris (26-09, "akkoord", logs/def768/ronde11-herproefgoedkeuring-v1.json)
op logs/def768/c3-herstel-vervolgproef-voorstel-v1.md: max 66 modelstappen
(2 ontwikkeling = alleen R720, 8 verifier-only, 40 t_eind, 16 t_herhaling),
reserve 0, cumulatief met R1–R10 max 430 (364 + 66), routerplafond USD
24,529390 zodat R8 (USD 0,098735) + R9 (USD 0,178910) + R10 (USD 0,192965) +
R11 binnen het oorspronkelijke kader van USD 25 blijft.

- R11 is een eigen identiteit met eigen opslag; R1–R10 blijven gesloten;
- het aantal stappen boven het oorspronkelijke kader (68) is exact met 3
  verruimd (71), uitsluitend via het gepinde R11-besluit; geen andere ronde of
  besluit kan een verruiming dragen; het oorspronkelijke 68/427 blijft historie;
- het kostenkader telt de werkelijke R8-, R9- én R10-kosten uit hun grootboeken;
- de code draagt het gereviewde contract `ess05-assess/17`/`ess05-verify/4`;
- de ontwikkelinvoer is exact de R9-selectie (alleen R720);
- V8: de zeven V7-items ongewijzigd behalve hun verificatieprompthash
  (verify/4), plus V-N5 = het ongewijzigde R10-R720-concept met foutdrager
  `claim:C3`; V-N4 (R9-C5) blijft negatief op `claim:C5`.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import json
import shutil
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _gevallenbestand
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import _omgeving8, _R8Provider
from tests.unit.scripts.test_def768_r9_proef import R8_KOSTEN_NUSD, _r8_boek
from tests.unit.scripts.test_def768_r10_proef import (
    BESLUIT8,
    BESLUIT8_SHA256,
    BESLUIT9,
    BESLUIT9_SHA256,
    BESLUIT10,
    BESLUIT10_SHA256,
    CONTRACT10,
    HUIDIG_CONTRACT,
    R9_KOSTEN_NUSD,
    R9_SELECTIE,
    R9_SELECTIE_SHA256,
    R10_MAP,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    V7,
    _foutdragers,
    _keten10,
    _r9_boek,
    _sha,
    _stand,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import migreer_r7_naar_v2 as mig
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

try:  # de V8-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r11_verificatie_invoer as mk11
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk11 = None

R11_ID = "DEF-768-AI-20260926-R11"
R11_MAP = ROOT / "reports" / R11_ID
V8 = R11_MAP / "verificatie-invoer-v1.json"
V7_SHA256 = "4eee1c703894d572c5c4a32664abfc5c3203d14bcf5ba994f51e06e5abf63c4d"
R10_RECORD = (
    R10_MAP
    / "ontwikkeling-20260926T104115270789Z"
    / "calls"
    / "001-ontwikkeling-R720.json"
)
R10_RECORD_SHA256 = "c4f8be4093eb76349c6d09ba18f25569d22c1942d907afef569b328ef245a975"
STOP10 = R10_MAP / "inhoudelijke-stop-v1.json"
STOP10_SHA256 = "96093ac846be54e1e3bf7d9ebf8731fe0a6175e2692a2ef68c8dbc0ea58972c4"
LOGS = ROOT / "logs" / "def768"
INHOUD10 = LOGS / "ronde10-r720-inhoudscontrole-result-v1.md"
INHOUD10_SHA256 = "353944a1969738b986853f6cbce858b75fbdcf93063c47958e236883c93f4fd5"
BESLUIT11 = LOGS / "ronde11-herproefgoedkeuring-v1.json"
#: De echte R10-stand: twee betaalde stappen (95935000 + 97030000 nUSD).
R10_KOSTEN_NUSD = 192_965_000
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10")
V = "validation"
W = "ess05_verification"

besluiten_nodig = pytest.mark.skipif(
    not all(
        p.is_file() for p in (BESLUIT11, BESLUIT10, BESLUIT9, BESLUIT8, TOESTEMMING)
    ),
    reason="git-ignored besluiten ontbreken",
)
r10_bronnen_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (V7, R10_RECORD, R9_SELECTIE, STOP10, INHOUD10)),
    reason="git-ignored R9/R10-bronnen ontbreken",
)
v8_nodig = pytest.mark.skipif(not V8.is_file(), reason="git-ignored V8 ontbreekt")


def _besluit11_sha() -> str:
    return _sha(BESLUIT11)


def _r10_boek(root: Path, *, kosten: int | None = R10_KOSTEN_NUSD, gesloten=True):
    """Een R10-grootboek zoals het echte: twee betaalde stappen, geval geaccepteerd."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R10)
    poging = "ontwikkeling|R720|1"
    delen = (None, None) if kosten is None else (95_935_000, kosten - 95_935_000)
    for index, (taak, naam) in enumerate(((V, "beoordeling"), (W, "verificatie"))):
        res = boek.reserveer("ontwikkeling", f"{poging}/{naam}", invoer_sha256="a" * 64,
                             poging=poging, stap=naam,
                             vorige_stap="beoordeling" if index else None,
                             task_type=taak)  # fmt: skip
        if index and not gesloten:
            return boek
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                   kosten_werkelijk_nusd=delen[index])  # fmt: skip
    boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="auto")
    return boek


def _keten11(tmp_path: Path, *, r10=None, **kw):
    """(R10-, R9- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r10_opslag = runner.Proefopslag(tmp_path / "r10")
    _r10_boek(r10_opslag.root, **(r10 or {}))
    return (r10_opslag, *_keten10(tmp_path, **kw))


def _bestaande_keten11(tmp_path: Path):
    namen = ("r10", "r9", "r8", "r7", "r6", "r5", "r4", "r3", "r2", "r1")
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag11(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r11")


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag11(tmp_path).grootboek
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


#: Het gepinde R11-contract (assess/17 + verify/4, answer/1). Sinds answer/2
#: draagt de code een ander contract: de echte R11-registratie weigert dan
#: fail-closed; R11 blijft bovendien gestopt in zijn grootboek.
R11_CONTRACT = {
    **CONTRACT10,
    "prompt_version": "ess05-assess/17",
    "verification_prompt_version": "ess05-verify/4",
}


def _r11(**anders) -> runner.Proef:
    """R11-kopie met de huidige contractidentiteit (het echte R11 blijft /17, answer/1)."""
    anders.setdefault("contract", MappingProxyType(HUIDIG_CONTRACT))
    return dataclasses.replace(runner.PROEVEN["R11"], **anders)


def _t11(omg, tmp_path, pad, *, fase="ontwikkeling", nieuw=True, proef=None,
         keten=None, **kw):  # fmt: skip
    if keten is None:
        keten = _keten11(tmp_path) if nieuw else _bestaande_keten11(tmp_path)
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag11(tmp_path),
            proef=proef or _r11(t_ontwikkelinvoer_sha256=_sha(pad)),
            voorganger_opslag=keten,
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _ontwikkeling11_geaccepteerd(tmp_path: Path) -> gb.Grootboek:
    boek = gb.Grootboek.nieuw(_opslag11(tmp_path).grootboek, gb.R11)
    poging = "ontwikkeling|R720|1"
    for index, (taak, naam) in enumerate(((V, "beoordeling"), (W, "verificatie"))):
        res = boek.reserveer("ontwikkeling", f"{poging}/{naam}", invoer_sha256="a" * 64,
                             poging=poging, stap=naam,
                             vorige_stap="beoordeling" if index else None,
                             task_type=taak)  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
    boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="test")
    return boek


def _v11(omg, tmp_path, pad, *, proef=None):
    proef = proef or _r11(v_invoer_sha256=_sha(pad))
    _ontwikkeling11_geaccepteerd(tmp_path)
    freeze = tmp_path / "freeze-v.json"
    freeze.write_text(
        json.dumps(runner.freezevelden(omg, proef, "v")), encoding="utf-8"
    )
    return asyncio.run(
        runner.voer_v_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag11(tmp_path),
            proef=proef,
            freeze=freeze,
            voorganger_opslag=_keten11(tmp_path),
            nieuw_grootboek=False,
        )
    )


def _v_gevallen(tmp_path) -> list[dict]:
    return [g for g in _soort(tmp_path, "geval") if g["fase"] == "verificatie_alleen"]


def _besluit11(tmp_path: Path, bron: Path = BESLUIT11, **anders) -> Path:
    data = json.loads(bron.read_text(encoding="utf-8"))
    for sleutel, waarde in anders.items():
        if waarde is None:
            data.pop(sleutel, None)
        else:
            data[sleutel] = waarde
    pad = tmp_path / f"besluit-{bron.stem}.json"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


def _v8_bouw(tmp_path: Path) -> tuple[Path, dict]:
    pad = tmp_path / "v8.json"
    assert mk11.main(["--doel", str(pad)]) == 0
    return pad, json.loads(pad.read_text(encoding="utf-8"))


# --- identiteit en grootboek ------------------------------------------------------------


class TestIdentiteit:
    def test_r11_caps_reserve_voorganger_en_cumulatief(self):
        r11 = gb.R11
        assert r11.proef_id == R11_ID
        assert dict(r11.fasecaps) == {
            "ontwikkeling": 2,
            "verificatie_alleen": 8,
            "t_eind": 40,
            "t_herhaling": 16,
        }
        assert (r11.reserve_max, r11.totaal_max) == (0, 66)
        assert r11.voorganger is gb.R10
        assert r11.cumulatief_max == 430 == 364 + 66
        assert r11.modelstappen_per_geval == 2

    def test_zelfde_stappen_volgorde_stop_en_gedeelde_binding_als_r10(self):
        r11 = gb.R11
        assert dict(r11.fasestappen) == dict(gb.R10.fasestappen)
        assert dict(r11.fasevolgorde) == dict(gb.R10.fasevolgorde)
        assert r11.eindgroepen == gb.R10.eindgroepen
        assert r11.bindingsvelden == gb.R10.bindingsvelden
        assert (r11.stop_bij_eerste_fout, r11.gedeelde_codebinding) == (True, True)

    def test_kostenbewaking_zelfde_model_en_grenzen_gezamenlijk_kader(self):
        kb11, kb8 = gb.R11.kostenbewaking, gb.R8.kostenbewaking
        assert kb11.plafond_nusd == 24_529_390_000
        assert gb.R11.kostenkader_nusd == 25_000_000_000
        assert (
            kb11.plafond_nusd + R8_KOSTEN_NUSD + R9_KOSTEN_NUSD + R10_KOSTEN_NUSD
            == gb.R11.kostenkader_nusd
        )
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb11, veld) == getattr(kb8, veld), veld
        assert kb11.max_tokens == 3000
        assert dict(kb11.bytegrens) == dict(kb8.bytegrens)

    def test_begroting_past_binnen_het_resterende_plafond(self):
        # 29 beoordelingen à 0,315 plus 37 verificaties à 0,375 (voorstel §Budget).
        assert gb.begroting_nusd(gb.R11) == 23_010_000_000
        assert gb.begroting_nusd(gb.R11) <= gb.R11.kostenbewaking.plafond_nusd

    def test_r10_en_ouder_ongewijzigd(self):
        r10 = gb.R10
        assert (r10.totaal_max, r10.reserve_max, r10.cumulatief_max) == (65, 0, 427)
        assert r10.kostenbewaking.plafond_nusd == 24_722_355_000
        assert (r10.kostenkader_nusd, r10.voorganger) == (25_000_000_000, gb.R9)
        assert (gb.R9.totaal_max, gb.R9.cumulatief_max) == (64, 424)
        assert (gb.R8.totaal_max, gb.R8.cumulatief_max) == (68, 427)

    def test_r11_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "r11" / "callgrootboek.jsonl", gb.R11)
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(boek.pad, gb.R10)
        assert gb.Grootboek.open(boek.pad, gb.R11).identiteit is gb.R11


class TestCumulatiefEnKostenkader:
    def _synthetische_keten(self, tmp_path):
        # 364 werkelijke R1–R10-calls: vijf rondes à 57, twee à 37, R8 één,
        # R9 twee, R10 twee.
        voorgangers = [
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
            voorgangers.append(
                gb.Grootboek.lees(tmp_path / naam / "callgrootboek.jsonl", identiteit)
            )
        return voorgangers

    def test_cumulatief_430_past_431_niet(self, tmp_path):
        voorgangers = self._synthetische_keten(tmp_path)
        assert sum(b.samenvatting()["totaal"] for b in voorgangers) == 364
        boek = gb.Grootboek.nieuw(tmp_path / "r11" / "callgrootboek.jsonl", gb.R11)
        gb.controleer_cumulatief(boek, voorgangers, 66)
        with pytest.raises(gb.BudgetSchendingError, match="430"):
            gb.controleer_cumulatief(boek, voorgangers, 67)

    def _keten_boeken(self, tmp_path, **kw):
        opslagen = _keten11(tmp_path, **kw)
        return [
            gb.Grootboek.lees(o.grootboek, i)
            for o, i in zip(opslagen, gb.voorgangerketen(gb.R11), strict=True)
        ]

    def test_kostenkader_met_de_werkelijke_r8_r9_en_r10_kosten_precies_25(
        self, tmp_path
    ):
        keten = self._keten_boeken(tmp_path)
        assert [b.kostenstand()["lopend_nusd"] for b in keten[:3]] == [
            R10_KOSTEN_NUSD,
            R9_KOSTEN_NUSD,
            R8_KOSTEN_NUSD,
        ]
        boek = gb.Grootboek.nieuw(tmp_path / "r11" / "callgrootboek.jsonl", gb.R11)
        gb.controleer_cumulatief(boek, keten, 1)

    @pytest.mark.parametrize(
        "kw",
        [
            {"r10": {"kosten": R10_KOSTEN_NUSD + 1}},  # één nanodollar meer
            {"r10": {"kosten": None}},  # onbekende kosten tellen met hun stapgrens
            {"r10": {"gesloten": False}},  # onafgesloten (crash) telt met haar grens
            {"r9": {"kosten": R9_KOSTEN_NUSD + 1}},
            {"r8": {"kosten": R8_KOSTEN_NUSD + 1}},
        ],
    )
    def test_kostenkader_weigert_zodra_een_voorganger_meer_telt(self, tmp_path, kw):
        keten = self._keten_boeken(tmp_path, **kw)
        boek = gb.Grootboek.nieuw(tmp_path / "r11" / "callgrootboek.jsonl", gb.R11)
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            gb.controleer_cumulatief(boek, keten, 1)

    def test_kostenkader_boven_25_start_niets(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        keten = _keten11(tmp_path, r10={"kosten": R10_KOSTEN_NUSD + 1})
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            _t11(_omgeving8(provider), tmp_path, pad, keten=keten)
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []

    @pytest.mark.skipif(
        not all(runner.PROEVEN[n].opslag.grootboek.is_file() for n in OUDE_RONDES),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_364_calls_en_usd_0_470610(self, tmp_path):
        """De werkelijke keten R10 … R1 (alleen lezen): de telling van het besluit."""
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed(OUDE_RONDES)
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 364
        assert [b.kostenstand()["lopend_nusd"] for b in keten[:3]] == [
            R10_KOSTEN_NUSD,
            R9_KOSTEN_NUSD,
            R8_KOSTEN_NUSD,
        ]
        boek = gb.Grootboek.nieuw(tmp_path / "r11" / "callgrootboek.jsonl", gb.R11)
        gb.controleer_cumulatief(boek, keten, 66)
        with pytest.raises(gb.BudgetSchendingError, match="430"):
            gb.controleer_cumulatief(boek, keten, 67)


# --- registratie en sluiting van R1–R10 ---------------------------------------------------


class TestRegistratie:
    def test_r11_geregistreerd_met_eigen_opslag_invoer_en_besluit(self):
        proef = runner.PROEVEN["R11"]
        assert proef.identiteit is gb.R11
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R11_MAP
        # Ontwikkeling: exact de oorspronkelijke R9-selectie (alleen R720).
        assert proef.t_ontwikkelinvoer_sha256 == R9_SELECTIE_SHA256
        assert proef.v_invoer_sha256 == runner.R11_V_INVOER_SHA256
        assert proef.v_invoer_sha256 != V7_SHA256
        assert proef.g_ontwikkelinvoer_sha256 is None
        assert proef.budgetbesluit == BESLUIT11
        assert proef.budgetbesluit_sha256 == runner.R11_BUDGETBESLUIT_SHA256
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        assert dict(proef.contract) == R11_CONTRACT
        # De enige ronde met een verruiming boven het oorspronkelijke kader.
        assert proef.kaderverruiming_modelstappen == 3

    def test_alleen_r11_open_en_draagt_als_enige_een_verruiming(self):
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == [
            "R11",
            "R12",
            "R13",
            "R14",
            "R15",
            "R16",
            "R17",
            "R18",
        ]
        assert {
            n: p.kaderverruiming_modelstappen
            for n, p in runner.PROEVEN.items()
            if p.kaderverruiming_modelstappen
        } == {"R11": 3}
        r10 = runner.PROEVEN["R10"]
        assert (r10.budgetbesluit_sha256, dict(r10.contract)) == (
            BESLUIT10_SHA256,
            CONTRACT10,
        )
        assert (
            runner.PROEVEN["R9"].budgetbesluit_sha256,
            runner.PROEVEN["R8"].budgetbesluit_sha256,
        ) == (BESLUIT9_SHA256, BESLUIT8_SHA256)

    @pytest.mark.parametrize("naam", OUDE_RONDES)
    def test_oude_ronde_gesloten_via_de_cli(self, monkeypatch, tmp_path, capsys, naam):
        def verboden(**_kw):
            raise AssertionError(f"geen live omgeving voor gesloten {naam}")

        mappen = (R10_MAP, R11_MAP)
        voor = [_stand(m / "callgrootboek.jsonl") for m in mappen]
        monkeypatch.setattr(runner, "live_omgeving", verboden)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(SystemExit) as fout:
            runner.main(["--proef", naam, "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert fout.value.code == 2
        assert "gesloten" in capsys.readouterr().err
        assert [_stand(m / "callgrootboek.jsonl") for m in mappen] == voor

    @pytest.mark.parametrize("naam", OUDE_RONDES)
    def test_oude_ronde_gesloten_programmatisch(self, naam):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        proef = runner.PROEVEN[naam]
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, proef.opslag, proef)
        assert provider.aanroepen == []

    def test_kopie_van_r11_start_geen_echte_call(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        kopie = _r11(kaderverruiming_modelstappen=4)
        with pytest.raises(gb.BudgetSchendingError, match="geregistreerde"):
            runner._controleer_registratie(omg, kopie)
        assert provider.aanroepen == []

    @besluiten_nodig
    def test_cli_echt_r11_bouwt_de_live_omgeving_op_productiegrenzen(
        self, monkeypatch, tmp_path
    ):
        gebouwd = {}
        voor = _stand(R11_MAP / "callgrootboek.jsonl")

        class _GestoptError(Exception):
            pass

        def _live(**kw):
            gebouwd.update(kw)
            raise _GestoptError  # vóór client, grootboek en netwerk

        monkeypatch.setattr(runner, "live_omgeving", _live)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(_GestoptError):
            runner.main(["--proef", "R11", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert gebouwd == {
            "timeout": 60,
            "max_tokens_t": 3000,
            "verifier_max_tokens": 3000,
        }
        assert _stand(R11_MAP / "callgrootboek.jsonl") == voor

    @besluiten_nodig
    def test_echte_poorten_open_behalve_het_contract_onder_answer2(self):
        proef = runner.PROEVEN["R11"]
        omg = dataclasses.replace(_omgeving8(_R8Provider()), echt=True)
        runner._controleer_opslag(omg, proef.opslag, proef)
        runner._controleer_goedkeuring(omg, proef)
        runner._controleer_productiegrenzen(omg, proef)
        runner._controleer_kostenroute(omg, proef)
        # De code draagt answer/2: de gepinde R11-registratie weigert fail-closed.
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner._controleer_contract(omg, proef)
        assert runner._besluit_voor(omg, proef) == runner.R11_BUDGETBESLUIT_SHA256

    def test_echt_buiten_de_canonieke_opslag_geweigerd(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError):
            _t11(omg, tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag11(tmp_path).grootboek.exists()


# --- budgetbesluit en de begrensde verruiming ---------------------------------------------


@besluiten_nodig
class TestBudgetbesluit:
    def test_besluit_brongetrouw_gepind(self):
        data = json.loads(BESLUIT11.read_text(encoding="utf-8"))
        assert _besluit11_sha() == runner.R11_BUDGETBESLUIT_SHA256
        # Letterlijke gebruikersreactie, zoals vastgelegd.
        assert data["gebruikersantwoord"] == "akkoord"
        assert (data["extra_modelaanroepen_max"], data["cumulatief_max"]) == (66, 430)
        assert (
            data["oorspronkelijk_extra_budget"],
            data["oorspronkelijk_cumulatief_plafond"],
            data["oorspronkelijk_kostenbudget_usd"],
        ) == (68, 427, "25.00")
        assert (
            data["goedgekeurde_verruiming_modelaanroepen"],
            data["nieuw_gezamenlijk_modelaanroepen_max"],
            data["nieuw_cumulatief_plafond"],
        ) == (3, 71, 430)

    def test_besluit_past_op_r11_en_eerdere_besluiten_blijven_geldig(self):
        assert (
            runner.controleer_budgetbesluit(runner.PROEVEN["R11"])
            == runner.R11_BUDGETBESLUIT_SHA256
        )
        for naam, sha in (
            ("R10", BESLUIT10_SHA256),
            ("R9", BESLUIT9_SHA256),
            ("R8", BESLUIT8_SHA256),
        ):
            assert runner.controleer_budgetbesluit(runner.PROEVEN[naam]) == sha

    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 67},
            {"cumulatief_max": 431},
            {"historisch_verbruik": 363},
            {"reserve": 1},
            {"kostenbudget_usd": "24.529391"},
            {"fasen_modelstappen_max": {"ontwikkeling": 2, "verificatie_alleen": 7,
                                        "t_eind": 40, "t_herhaling": 16}},
            {"gebruikersantwoord": ""},
            {"oorspronkelijk_kostenbudget_usd": "26.00"},
            # De historie blijft 68/427; de verruiming heeft eigen velden.
            {"oorspronkelijk_extra_budget": 71},
            {"oorspronkelijk_cumulatief_plafond": 430},
            {"r10_verbruik_usd": "0.192966"},
            {"r10_verbruik_usd": None},
            {"r9_verbruik_usd": "0.178911"},
            {"r8_verbruik_usd": "0.098734"},
            {"r10_verbruik_modelstappen": 3},
            {"r10_verbruik_modelstappen": None},
            {"r8_verbruik_modelstappen": 2},
            {"goedgekeurde_verruiming_modelaanroepen": 4},
            {"goedgekeurde_verruiming_modelaanroepen": None},
            {"nieuw_gezamenlijk_modelaanroepen_max": 72},
            {"nieuw_gezamenlijk_modelaanroepen_max": None},
            {"nieuw_cumulatief_plafond": 431},
            {"nieuw_cumulatief_plafond": None},
        ],
    )  # fmt: skip
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        pad = _besluit11(tmp_path, **anders)
        proef = _r11(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)

    def test_zonder_geregistreerde_verruiming_past_het_besluit_niet(self):
        # 5 verbruikt + 66 > 68: alleen de exact geregistreerde 3 opent R11.
        for verruiming in (0, 2, 4):
            proef = _r11(kaderverruiming_modelstappen=verruiming)
            with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
                runner.controleer_budgetbesluit(proef)

    def test_verruimingsvelden_openen_geen_eerdere_ronde(self, tmp_path):
        """Geen algemene verruiming: een ronde zonder geregistreerde verruiming
        weigert een besluit dat er een noemt, ook met passende waarden."""
        pad = _besluit11(
            tmp_path, BESLUIT10,
            goedgekeurde_verruiming_modelaanroepen=3,
            nieuw_gezamenlijk_modelaanroepen_max=71,
            nieuw_cumulatief_plafond=430,
        )  # fmt: skip
        proef = dataclasses.replace(
            runner.PROEVEN["R10"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="verruiming"):
            runner.controleer_budgetbesluit(proef)

    def test_ongepind_of_ontbrekend_besluit_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r11(budgetbesluit=_besluit11(tmp_path)))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r11(budgetbesluit=tmp_path / "geen.json"))

    @pytest.mark.parametrize(
        ("naam", "bron"), [("R10", BESLUIT10), ("R9", BESLUIT9), ("R8", BESLUIT8)]
    )
    def test_gewijzigd_eerder_besluit_weigert_r11(
        self, monkeypatch, tmp_path, naam, bron
    ):
        kopie = tmp_path / f"besluit-{naam}.json"
        kopie.write_text(bron.read_text(encoding="utf-8") + " ", encoding="utf-8")
        oud = dataclasses.replace(runner.PROEVEN[naam], budgetbesluit=kopie)
        monkeypatch.setitem(runner.PROEVEN, naam, oud)
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(runner.PROEVEN["R11"])

    @pytest.mark.parametrize(
        "anders",
        [None, {"budget_calls_max": 71}, {"budget_usd_max": 30}, {"user_reply": ""}],
    )
    def test_payloadtoestemming_gepind_en_ongewijzigd(self, tmp_path, anders):
        data = json.loads(TOESTEMMING.read_text(encoding="utf-8"))
        data.update(anders or {})
        pad = tmp_path / "toestemming.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        sha = _sha(pad) if anders else TOESTEMMING_SHA256
        proef = _r11(payloadtoestemming=pad, payloadtoestemming_sha256=sha)
        with pytest.raises(gb.BudgetSchendingError, match="toestemming"):
            runner.controleer_budgetbesluit(proef)


# --- prompt- en antwoordcontract, freeze --------------------------------------------------


class TestContract:
    def test_r11_contract_historisch_de_code_weigert_de_echte_r11(self):
        """answer/2: de echte R11-registratie weigert fail-closed (niet gemigreerd)."""
        omg = _omgeving8(_R8Provider())
        assert runner.contractidentiteit(omg) == HUIDIG_CONTRACT
        assert {k for k in R11_CONTRACT if R11_CONTRACT[k] != HUIDIG_CONTRACT[k]} == {
            "prompt_version",
            "answer_schema_version",
        }
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner._controleer_contract(omg, runner.PROEVEN["R11"])
        runner._controleer_contract(omg, _r11())

    def test_echte_r11_start_niets_onder_answer2(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        proef = dataclasses.replace(
            runner.PROEVEN["R11"], t_ontwikkelinvoer_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            _t11(_omgeving8(provider), tmp_path, pad, proef=proef)
        assert provider.aanroepen == []
        assert not _opslag11(tmp_path).grootboek.exists()

    def test_andere_verifyversie_voor_grootboek_geweigerd(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "services.validation.ess05_verification_service."
            "Ess05VerificationService.PROMPT_VERSION",
            "ess05-verify/3",
        )
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            _t11(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 1))
        assert provider.aanroepen == []
        assert not _opslag11(tmp_path).grootboek.exists()

    def test_freeze_pint_het_contract_voor_v_en_t(self):
        omg = _omgeving8(_R8Provider())
        v, t = (runner.freezevelden(omg, _r11(), g) for g in "vt")
        for velden in (v, t):
            assert velden["proef_id"] == R11_ID
            assert {k: velden[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        assert {k for k in v if v[k] != t[k]} == {"groep"}

    def test_r10_freeze_geldt_niet_voor_r11(self, tmp_path):
        omg = _omgeving8(_R8Provider())
        r10 = dataclasses.replace(runner.PROEVEN["R10"], contract=HUIDIG_CONTRACT)
        pad = tmp_path / "freeze-r10.json"
        pad.write_text(json.dumps(runner.freezevelden(omg, r10, "t")), encoding="utf-8")
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            runner.controleer_freeze(pad, omg, runner.PROEVEN["R11"], "t",
                                     dataset_sha256="a" * 64, herhaal_ids=[])  # fmt: skip


# --- fasegrenzen, freeze en stop ----------------------------------------------------------


def _tot_en_met_v(tmp_path: Path):
    """Offline: ontwikkeling geaccepteerd en acht V-items (V-fase), dan klaar voor T."""
    from tests.unit.scripts.test_def768_r8_proef import _v_invoer

    pad, items = _v_invoer(tmp_path, ("goed", "fout") * 3 + ("fout", "fout"))
    provider = _R8Provider(uitkomsten=_foutdragers(items))
    omg = _omgeving8(provider)
    _v11(omg, tmp_path, pad)
    assert [g["geaccepteerd"] for g in _v_gevallen(tmp_path)] == [True] * 8
    return omg, provider


class TestFasegrenzen:
    def test_twee_ontwikkelgevallen_boven_de_fasecap_geweigerd(self, tmp_path):
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="fasecap ontwikkeling"):
            _t11(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 2))
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []

    def test_ontwikkeling_alleen_op_de_r9_selectie(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="T-ontwikkelselectie"):
            _t11(_omgeving8(provider), tmp_path, pad, proef=_r11())
        assert provider.aanroepen == []

    def test_negen_v_items_boven_de_fasecap_geweigerd(self, tmp_path):
        from tests.unit.scripts.test_def768_r8_proef import _v_invoer

        pad, items = _v_invoer(tmp_path, ("goed", "fout") * 4 + ("fout",))
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        with pytest.raises(gb.BudgetSchendingError, match="fasecap verificatie_alleen"):
            _v11(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == []

    def test_acht_v_items_passen_daarna_t_eind_cap_en_freeze(self, tmp_path):
        omg, provider = _tot_en_met_v(tmp_path)
        voor = len(provider.aanroepen)
        with pytest.raises(gb.BudgetSchendingError, match="freeze"):
            _t11(omg, tmp_path, _gevallenbestand(tmp_path, 20, "e.json"),
                 fase="t_eind", nieuw=False, proef=_r11())  # fmt: skip
        freeze = tmp_path / "freeze-t.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, _r11(), "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="fasecap t_eind"):
            _t11(omg, tmp_path, _gevallenbestand(tmp_path, 21, "eind.json"),
                 fase="t_eind", nieuw=False, proef=_r11(), freeze=freeze)  # fmt: skip
        assert len(provider.aanroepen) == voor

    def test_t_eind_voor_v_geweigerd(self, tmp_path):
        provider = _R8Provider()
        omg = _omgeving8(provider)
        _ontwikkeling11_geaccepteerd(tmp_path)
        freeze = tmp_path / "freeze-t.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, _r11(), "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="verificatie_alleen"):
            _t11(omg, tmp_path, _gevallenbestand(tmp_path, 20, "e.json"),
                 fase="t_eind", nieuw=False, proef=_r11(), freeze=freeze,
                 keten=_keten11(tmp_path))  # fmt: skip
        assert provider.aanroepen == []

    def test_niet_geaccepteerd_r720_stopt_r11_duurzaam(self, tmp_path):
        provider = _R8Provider(onderscheid="not_distinguished")
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _t11(_omgeving8(provider), tmp_path, pad)
        assert len(provider.aanroepen) == 2
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _t11(_omgeving8(provider), tmp_path, pad, nieuw=False)
        assert len(provider.aanroepen) == 2

    def test_ontwikkeling_een_geval_twee_stappen_met_keten_incl_r10(self, tmp_path):
        provider = _R8Provider()
        uitkomst = _t11(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 1))
        assert provider.stappen == ["beoordeling", "verificatie"]
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is True, geval["reden"]
        # Samenvatting: aanroepen_gestart telt gevallen; het grootboek telt stappen.
        assert uitkomst["aanroepen_gestart"] == 1
        assert uitkomst["grootboek_na"]["netwerk_gestart"] == 2
        voorganger = uitkomst["voorganger_grootboek"]
        assert voorganger["proef_id"] == gb.R10.proef_id
        assert voorganger["keten"][:3] == [
            {"proef_id": gb.R10.proef_id, "totaal": 2},
            {"proef_id": gb.R9.proef_id, "totaal": 2},
            {"proef_id": gb.R8.proef_id, "totaal": 1},
        ]
        assert voorganger["cumulatief_max"] == 430
        assert uitkomst["grootboek_na"]["kosten"]["plafond_nusd"] == 24_529_390_000


# --- V8: maker, bronbinding en offline verifier-only ---------------------------------------


class TestV8Maker:
    def test_maker_bronnen_en_doel_gepind(self):
        assert (mk11.V7, mk11.V7_SHA256) == (V7, V7_SHA256)
        assert (mk11.R10_CALLRECORD, mk11.R10_CALLRECORD_SHA256) == (
            R10_RECORD,
            R10_RECORD_SHA256,
        )
        assert (mk11.R9_SELECTIE, mk11.R9_SELECTIE_SHA256) == (
            R9_SELECTIE,
            R9_SELECTIE_SHA256,
        )
        assert (mk11.INHOUDSCONTROLE, mk11.INHOUDSCONTROLE_SHA256) == (
            INHOUD10,
            INHOUD10_SHA256,
        )
        assert (mk11.STOPBESLUIT, mk11.STOPBESLUIT_SHA256) == (STOP10, STOP10_SHA256)
        assert mk11.DOEL == V8
        assert (mk11.N5_ID, mk11.N5_FOUTDRAGER) == ("V-N5", "claim:C3")

    @r10_bronnen_nodig
    @v8_nodig
    def test_vastgelegde_v8_reproduceerbaar_en_gepind(self, tmp_path):
        _, nieuw = _v8_bouw(tmp_path)
        assert _sha(V8) == runner.R11_V_INVOER_SHA256
        # Sinds answer/2 noemt de herkomst het huidige contract; al het andere,
        # ook elk item (verify/4 ongewijzigd), is exact de bevroren V8.
        vast = json.loads(V8.read_text(encoding="utf-8"))
        assert vast["herkomst"]["contract"] == R11_CONTRACT
        assert nieuw["herkomst"]["contract"] == HUIDIG_CONTRACT
        nieuw["herkomst"]["contract"] = R11_CONTRACT
        tekst = json.dumps(nieuw, ensure_ascii=False, indent=2) + "\n"
        assert tekst.encode("utf-8") == V8.read_bytes()

    @r10_bronnen_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        doel = tmp_path / "v8.json"
        assert mk11.main(["--doel", str(doel)]) == 0
        with pytest.raises(FileExistsError):
            mk11.main(["--doel", str(doel)])

    @r10_bronnen_nodig
    @pytest.mark.parametrize(
        ("bron", "melding"),
        [
            ("v7", "V7"),
            ("callrecord", "callrecord"),
            ("selectie", "ontwikkelselectie"),
            ("inhoudscontrole", "inhoudscontrole"),
            ("stopbesluit", "stopbesluit"),
        ],
    )
    def test_gewijzigde_bron_geweigerd(self, tmp_path, bron, melding):
        standaard = {
            "v7": V7,
            "callrecord": R10_RECORD,
            "selectie": R9_SELECTIE,
            "inhoudscontrole": INHOUD10,
            "stopbesluit": STOP10,
        }
        kopie = tmp_path / "bron"
        shutil.copyfile(standaard[bron], kopie)
        with kopie.open("a", encoding="utf-8") as f:
            f.write(" ")
        with pytest.raises(mk11.MakerfoutError, match=melding):
            mk11.maak_verificatie_invoer(**{bron: kopie})

    @r10_bronnen_nodig
    @pytest.mark.parametrize(
        "mutatie",
        [
            "concepttekst",  # hersteld concept: C3 zonder de ongestaafde deelzin
            "ruw",  # het ruwe antwoord hoort niet bij de vastgelegde hash
            "c3_bewijs",  # C3 met de volgzin als extra bewijs (gerepareerd)
        ],
    )
    def test_n5_zonder_reparatie_of_herlabeling(self, mutatie):
        record = copy.deepcopy(json.loads(R10_RECORD.read_text(encoding="utf-8")))
        (geval,) = json.loads(R9_SELECTIE.read_text(encoding="utf-8"))["gevallen"]
        concept = record["beoordelingsdocument"]["concept"]
        c3 = next(c for c in concept["claims"] if c["id"] == "C3")
        if mutatie == "concepttekst":
            c3["text"] = c3["text"].replace(" die onderling worden vergeleken", "")
        elif mutatie == "ruw":
            record["ruw_antwoord"] += " "
        else:
            c3["evidence"] = ["E7", "E6"]
        with pytest.raises(mk11.MakerfoutError):
            mk11.n5_item(record, geval, bron={})


@r10_bronnen_nodig
class TestV8Invoer:
    @pytest.fixture
    def v8(self, tmp_path) -> dict:
        return _v8_bouw(tmp_path)[1]

    def test_zeven_v7_items_alleen_de_prompthash_herberekend(self, v8):
        oud = json.loads(V7.read_text(encoding="utf-8"))["items"]
        nieuw = v8["items"]
        assert [i["id"] for i in nieuw] == [i["id"] for i in oud] + ["V-N5"]
        for n, o in zip(nieuw[:7], oud, strict=True):
            assert list(n) == list(o)
            assert {k for k in n if n[k] != o[k]} == {"verificatieprompt_sha256"}

    def test_vijf_negatieven_en_drie_positieven(self, v8):
        soorten = {i["id"]: (i["soort"], i["foutdragende_items"]) for i in v8["items"]}
        assert sorted(i for i, (s, _) in soorten.items() if s == "goed") == [
            "V-P1",
            "V-P2",
            "V-P3",
        ]
        assert sorted(i for i, (s, _) in soorten.items() if s == "fout") == [
            "V-N1",
            "V-N2",
            "V-N3",
            "V-N4",
            "V-N5",
        ]
        # Beide oorspronkelijke bewijsroutefouten blijven direct negatief.
        assert soorten["V-N4"] == ("fout", ["claim:C5"])
        assert soorten["V-N5"] == ("fout", ["claim:C3"])

    def test_prompthash_hoort_bij_verify_4(self, v8):
        items = runner.valideer_v_invoer(v8, _omgeving8(_R8Provider()))
        assert [v.sleutel for v in items] == [
            f"verificatie_alleen|{i}|1"
            for i in ("V-N1", "V-N2", "V-N3", "V-P1", "V-P2", "V-P3", "V-N4", "V-N5")
        ]
        assert all("<bewijsroutes>" in v.prompt[1] for v in items)

    def test_v_n5_is_het_ongewijzigde_r10_concept(self, v8):
        record = json.loads(R10_RECORD.read_text(encoding="utf-8"))
        doc = record["beoordelingsdocument"]
        (geval,) = json.loads(R9_SELECTIE.read_text(encoding="utf-8"))["gevallen"]
        n5 = v8["items"][7]
        assert n5["concept"] == doc["concept"]
        assert n5["concept_hash"] == doc["concept_derivation"]["concept_hash"]
        assert n5["geval"] == geval
        assert n5["geval_sha256"] == record["geval_sha256"] == pi.sha_json(geval)
        assert n5["materiaal_sha256"] == doc["concept_derivation"]["material"]
        c3 = next(c for c in n5["concept"]["claims"] if c["id"] == "C3")
        assert (c3["role"], c3["evidence"]) == ("material", ["E7"])
        assert c3["text"].endswith("die onderling worden vergeleken.")

    def test_v_n5_bron_en_herkomst_gebonden(self, v8):
        record = json.loads(R10_RECORD.read_text(encoding="utf-8"))
        bron = v8["items"][7]["bron"]
        assert bron["callrecord"] == str(R10_RECORD.relative_to(ROOT))
        assert bron["callrecord_sha256"] == R10_RECORD_SHA256
        assert (bron["sleutel"], bron["seq"]) == ("ontwikkeling|R720|1", 1)
        assert bron["ruw_antwoord"] == record["ruw_antwoord"]
        assert (bron["prompt_version"], bron["verification_prompt_version"]) == (
            "ess05-assess/16",
            "ess05-verify/3",
        )
        # Het historische verifieroordeel blijft zichtbaar: C3 werd vrijgegeven.
        assert bron["historisch_verifieroordeel"]["item"] == "claim:C3"
        assert bron["historisch_verifieroordeel"]["outcome"] == "supported"
        assert bron["ontwikkelselectie"]["sha256"] == R9_SELECTIE_SHA256
        assert bron["inhoudscontrole"] == {
            "pad": str(INHOUD10.relative_to(ROOT)),
            "sha256": INHOUD10_SHA256,
        }
        assert bron["inhoudelijke_stop"] == {
            "pad": str(STOP10.relative_to(ROOT)),
            "sha256": STOP10_SHA256,
        }
        herkomst = v8["herkomst"]
        assert herkomst["r10_verificatie_invoer"]["sha256"] == V7_SHA256
        assert herkomst["contract"] == HUIDIG_CONTRACT
        assert v8["schema"] == mig.INVOERSCHEMA
        # V-N4 behoudt zijn eigen R9-herkomst ongewijzigd.
        v7 = json.loads(V7.read_text(encoding="utf-8"))
        assert v8["items"][6]["bron"] == v7["items"][6]["bron"]

    def test_v7_geweigerd_voor_r11(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="verifier-only-invoer"):
            runner.main(["--proef", "R11", "--fase", "verificatie_alleen", "--gevallen",
                         str(V7), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    def test_v8_acht_items_beide_bewijsroutefouten_afgewezen(self, tmp_path, v8):
        pad = tmp_path / "v8.json"
        provider = _R8Provider(uitkomsten=_foutdragers(v8["items"]))
        uitkomst = _v11(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"] * 8
        gevallen = _v_gevallen(tmp_path)
        assert [g["geaccepteerd"] for g in gevallen] == [True] * 8
        assert uitkomst["aanroepen_gestart"] == 8
        assert uitkomst["grootboek_na"]["netwerk_gestart"] == 2 + 8

    @pytest.mark.parametrize(
        ("uitkomsten_n5", "reden"),
        [
            ({}, "niet gedetecteerd"),  # C3 vrijgegeven
            ({"completeness": "unsupported"}, "buiten de foutdragende items"),
        ],
    )
    def test_v_n5_niet_direct_gedetecteerd_stopt_de_proef(
        self, tmp_path, v8, uitkomsten_n5, reden
    ):
        pad = tmp_path / "v8.json"
        uitkomsten = _foutdragers(v8["items"])
        uitkomsten[v8["items"][7]["concept_hash"]] = uitkomsten_n5
        provider = _R8Provider(uitkomsten=uitkomsten)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v11(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"] * 8
        assert reden in _v_gevallen(tmp_path)[-1]["reden"]

    def test_schemaweigering_is_geen_detectie(self, tmp_path, v8):
        pad = tmp_path / "v8.json"
        provider = _R8Provider(
            uitkomsten=_foutdragers(v8["items"]), hash_per_concept={"alle": "0" * 64}
        )
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v11(_omgeving8(provider), tmp_path, pad)
        (geval,) = _v_gevallen(tmp_path)
        assert "schemaweigering" in geval["reden"]

    # R11-01: alleen `unsupported` op de foutdrager is een directe detectie.
    @pytest.mark.parametrize("anders", [{}, {"completeness": "unsupported"}])
    @pytest.mark.parametrize(
        ("index", "foutdrager"), [(6, "claim:C5"), (7, "claim:C3")]
    )
    def test_undetermined_op_de_foutdrager_stopt_duurzaam(
        self, tmp_path, v8, index, foutdrager, anders
    ):
        pad = tmp_path / "v8.json"
        item = v8["items"][index]
        assert item["foutdragende_items"] == [foutdrager]
        uitkomsten = _foutdragers(v8["items"])
        uitkomsten[item["concept_hash"]] = {foutdrager: "undetermined", **anders}
        provider = _R8Provider(uitkomsten=uitkomsten)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v11(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"] * (index + 1)
        laatste = _v_gevallen(tmp_path)[-1]
        assert laatste["geaccepteerd"] is False
        assert laatste["poging"] == f"verificatie_alleen|{item['id']}|1"
        assert "unsupported" in laatste["reden"]
        # Duurzaam: een nieuwe aanroep op hetzelfde grootboek start niets meer,
        # ook niet met een correcte verifier.
        herstart = _R8Provider(uitkomsten=_foutdragers(v8["items"]))
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            asyncio.run(runner.voer_v_fase(
                _omgeving8(herstart), gevallenpad=pad, uitmap=tmp_path / "uit",
                opslag=_opslag11(tmp_path), proef=_r11(v_invoer_sha256=_sha(pad)),
                freeze=tmp_path / "freeze-v.json",
                voorganger_opslag=_bestaande_keten11(tmp_path), nieuw_grootboek=False,
            ))  # fmt: skip
        assert herstart.stappen == []


def _acceptatie(soort, foutdragers, checks, *, fout=None, status="voltooid"):
    """`_v_acceptatie` op een minimaal item en verificatieresultaat (R11-01)."""
    from types import SimpleNamespace

    from domain.ess05.contract import FOUT_SEMANTISCH

    bevindingen = tuple(
        {"item": i, "outcome": o, "finding": "f"}
        for i, o in checks.items()
        if o != "supported"
    )
    resultaat = SimpleNamespace(
        goedgekeurd=not bevindingen and fout is None,
        fout=fout or (FOUT_SEMANTISCH if bevindingen else None),
        uitkomst=SimpleNamespace(bevindingen=bevindingen),
    )
    v = SimpleNamespace(item={"soort": soort, "foutdragende_items": foutdragers})
    return runner._v_acceptatie(v, resultaat, status, None)


class TestAcceptatiepoort:
    """R11-01: een fout item is alleen gedetecteerd bij `unsupported` op een
    aangewezen foutdrager; `undetermined` is onzekerheid, geen detectie."""

    @pytest.mark.parametrize("foutdrager", ["claim:C5", "claim:C3"])
    @pytest.mark.parametrize(
        ("checks", "verwacht"),
        [
            ({"F": "unsupported"}, True),
            ({"F": "unsupported", "completeness": "undetermined"}, True),
            ({"F": "undetermined"}, False),
            ({"F": "undetermined", "completeness": "unsupported"}, False),
            ({"F": "undetermined", "claim:C1": "unsupported"}, False),
            ({"completeness": "unsupported"}, False),
            ({}, False),
        ],
    )
    def test_fout_item(self, foutdrager, checks, verwacht):
        checks = {foutdrager if k == "F" else k: o for k, o in checks.items()}
        geaccepteerd, reden = _acceptatie("fout", [foutdrager], checks)
        assert geaccepteerd is verwacht, reden
        if verwacht:
            assert reden == f"bekende fout gedetecteerd op {[foutdrager]}"

    def test_undetermined_reden_noemt_de_foutdrager(self):
        geaccepteerd, reden = _acceptatie(
            "fout", ["claim:C3"], {"claim:C3": "undetermined"}
        )
        assert geaccepteerd is False
        assert "claim:C3" in reden and "undetermined" in reden

    @pytest.mark.parametrize(
        ("checks", "verwacht"),
        [({}, True), ({"claim:C1": "unsupported"}, False)],
    )
    def test_goed_item(self, checks, verwacht):
        assert _acceptatie("goed", [], checks)[0] is verwacht

    @pytest.mark.parametrize("fout", ["malformed_response", "candidate_hash_mismatch"])
    def test_schemaweigering_blijft_geen_detectie(self, fout):
        geaccepteerd, reden = _acceptatie("fout", ["claim:C3"], {}, fout=fout)
        assert geaccepteerd is False
        assert "schemaweigering" in reden


@v8_nodig
@r10_bronnen_nodig
class TestDroog:
    def test_droog_v8_onder_r11(self, monkeypatch, tmp_path):
        # Mechaniek onder de huidige code (kopie met huidig contract).
        monkeypatch.setitem(runner.PROEVEN, "R11", _r11())
        code = runner.main(["--proef", "R11", "--fase", "verificatie_alleen",
                            "--gevallen", str(V8), "--uitmap", str(tmp_path),
                            "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-verificatie_alleen-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R11_ID, 8)
        grens = gb.R11.kostenbewaking.bytegrens[W]
        assert all(i["payload_bytes"] <= grens for i in droog["items"])
        freeze = droog["freezevelden"]
        assert (freeze["groep"], freeze["proef_id"]) == ("v", R11_ID)
        assert {k: freeze[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        assert not list(tmp_path.rglob("*.jsonl"))

    def test_droog_r9_selectie_onder_r11(self, monkeypatch, tmp_path):
        monkeypatch.setitem(runner.PROEVEN, "R11", _r11())
        code = runner.main(["--proef", "R11", "--fase", "ontwikkeling", "--gevallen",
                            str(R9_SELECTIE), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        # geplande_calls telt gevallen (één geval = twee modelstappen).
        assert (droog["proef_id"], droog["geplande_calls"]) == (R11_ID, 1)
        assert [i["sleutel"] for i in droog["items"]] == ["ontwikkeling|R720|1"]


def test_v8_leest_de_verborgen_eindset_niet():
    """De maker noemt geen eindset; de onafhankelijke eindset blijft gesloten."""
    bron = (ROOT / "scripts" / "ess05" / "maak_r11_verificatie_invoer.py").read_text(
        encoding="utf-8"
    )
    assert "eindset" not in bron.lower()
