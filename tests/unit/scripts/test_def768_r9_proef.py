"""DEF-768 R9 — gerichte herproef na het R8-offsetherstel: registratie, offline.

Besluit van Chris (26-09, "Ja", logs/def768/ronde9-herproefgoedkeuring-v1.json)
op logs/def768/offsetherstel-vervolgproef-voorstel-v1.md: max 64 modelstappen
(2 ontwikkeling = alleen R720, 6 verifier-only, 40 t_eind, 16 t_herhaling),
reserve 0, cumulatief met R1–R8 max 424, routerplafond USD 24,901265 zodat
R8 (USD 0,098735) + R9 binnen het oorspronkelijke kader van USD 25 blijft.

- R9 is een eigen identiteit met eigen opslag; R8 blijft duurzaam gesloten,
  ook via zijn oude geregistreerde route; R1–R8 blijven ongewijzigd;
- het budgetbesluit is gepind en draagt het oorspronkelijke 68/25-besluit en
  de payloadtoestemming (beide hashgebonden) mee;
- het kostenkader telt de werkelijke R8-kosten uit het R8-grootboek mee;
- de code draagt de vastgelegde prompt- en antwoordcontractidentiteit
  (`ess05-assess/15`, `ess05-answer/1`), ook in de freeze;
- de ontwikkelinvoer is uitsluitend R720, exact uit de R8-selectie; de
  V-invoer is ongewijzigd die van R8.

Na de inhoudelijke stop op R720 (26-09, NO-GO op claim C5) is R9 gesloten,
ook via de geregistreerde route. Besluit en contract blijven historisch gepind
op `/15` en `/2`; de code draagt sinds het R10-C3-herstel `ess05-assess/17`
en `ess05-verify/4` (daarvoor /16 en /3), dus R9 past niet meer op de huidige
code. De offline mechaniektests draaien daarom op een kopie van R9 met de
huidige contractidentiteit (`_r9`); de bevroren R8-V-invoer bindt de
verify/2-prompt en wordt onder de huidige verify-versie geweigerd.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _gevallenbestand
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import (
    _keten as _keten_tot_r7,
    _omgeving8,
    _R8Provider,
    _v_invoer,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import run_ess05_proef as runner

try:  # de R9-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r9_ontwikkelinvoer as mk9
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk9 = None

R9_ID = "DEF-768-AI-20260926-R9"
R9_MAP = ROOT / "reports" / R9_ID
R8_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R8"
R8_SELECTIE = R8_MAP / "ontwikkelselectie-v1.json"
R8_SELECTIE_SHA256 = "d07846942171801e9e31dbd6b372023e4e1ba322a024ff2354430cec1fd291f0"
R8_VINVOER = R8_MAP / "verificatie-invoer-v1.json"
R8_VINVOER_SHA256 = "ddece7dbbdf928be8c89aca819e110ea0e8ad6e45aaf6ce582fe27c7528d155c"
R9_SELECTIE = R9_MAP / "ontwikkelselectie-v1.json"
LOGS = ROOT / "logs" / "def768"
BESLUIT9 = LOGS / "ronde9-herproefgoedkeuring-v1.json"
BESLUIT9_SHA256 = "89ea16dddc7bb4403d4aa6f6fdaebc385f8fb40c40e1d6698b98bcd321765018"
BESLUIT8 = LOGS / "ronde8-budgetgoedkeuring-v1.json"
BESLUIT8_SHA256 = "bf82cd3bfd6cea12fc0d3d97df2305c922fdde8c19fb84db6f0a1e3320195d17"
TOESTEMMING = LOGS / "ronde8-anthropic-versturingstoestemming-v1.json"
TOESTEMMING_SHA256 = "a118986fa8c05161beb4f1b8eae642cc5b8ba05cb879519b289a734f26ac3a08"
#: De echte R8-stand: één betaalde, afgewezen stap (callgrootboek ee14d4e0…).
R8_KOSTEN_NUSD = 98_735_000
CONTRACT = {
    "prompt_version": "ess05-assess/15",
    "verification_prompt_version": "ess05-verify/2",
    "answer_schema_version": "ess05-answer/1",
    "concept_schema_version": "ess05-concept/1",
    "verification_schema_version": "ess05-verification/1",
}
#: De huidige code (answer/3): beide promptversies en het antwoordschema verschillen.
HUIDIG_CONTRACT = {
    **CONTRACT,
    "prompt_version": "ess05-assess/19",
    "verification_prompt_version": "ess05-verify/4",
    "answer_schema_version": "ess05-answer/3",
}
V = "validation"
W = "ess05_verification"

besluiten_nodig = pytest.mark.skipif(
    not (BESLUIT9.is_file() and BESLUIT8.is_file() and TOESTEMMING.is_file()),
    reason="git-ignored besluiten ontbreken",
)
r8_selectie_nodig = pytest.mark.skipif(
    not R8_SELECTIE.is_file(), reason="git-ignored R8-selectie ontbreekt"
)


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _stand(pad: Path) -> str | None:
    """sha256 van een canoniek bestand, of None; tests mogen het nooit raken."""
    return _sha(pad) if Path(pad).exists() else None


def _r9(**anders) -> runner.Proef:
    """R9-kopie met de huidige contractidentiteit (het echte R9 blijft /15 + /2)."""
    anders.setdefault("contract", MappingProxyType(HUIDIG_CONTRACT))
    return dataclasses.replace(runner.PROEVEN["R9"], **anders)


def _r8_boek(root: Path, *, kosten: int | None = R8_KOSTEN_NUSD, gesloten=True):
    """Een R8-grootboek zoals het echte: één betaalde stap, geval afgewezen."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R8)
    poging = "ontwikkeling|R720|1"
    res = boek.reserveer("ontwikkeling", f"{poging}/beoordeling", invoer_sha256="a" * 64,
                         poging=poging, stap="beoordeling", vorige_stap=None,
                         task_type=V)  # fmt: skip
    if gesloten:
        boek.sluit(res["seq"], "modelfout", netwerk_gestart=True,
                   kosten_werkelijk_nusd=kosten)  # fmt: skip
        boek.registreer_geval("ontwikkeling", poging, geaccepteerd=False,
                              reden="unverifiable_evidence")  # fmt: skip
    return boek


def _keten9(tmp_path: Path, **r8):
    """(R8- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r8_opslag = runner.Proefopslag(tmp_path / "r8")
    _r8_boek(r8_opslag.root, **r8)
    return (r8_opslag, *_keten_tot_r7(tmp_path))


def _opslag9(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r9")


def _regels9(tmp_path: Path) -> list[dict]:
    pad = _opslag9(tmp_path).grootboek
    return [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    return [r for r in _regels9(tmp_path) if r["soort"] == soort]


def _t9(omg, tmp_path, pad, *, fase="ontwikkeling", nieuw=True, proef=None,
        keten=None, **kw):  # fmt: skip
    if keten is None:
        keten = _keten9(tmp_path) if nieuw else _bestaande_keten9(tmp_path)
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag9(tmp_path),
            proef=proef or _r9(t_ontwikkelinvoer_sha256=_sha(pad)),
            voorganger_opslag=keten,
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _bestaande_keten9(tmp_path: Path):
    namen = ("r8", "r7", "r6", "r5", "r4", "r3", "r2", "r1")
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _besluit9(tmp_path: Path, **anders) -> Path:
    data = json.loads(BESLUIT9.read_text(encoding="utf-8"))
    data.update(anders)
    pad = tmp_path / "besluit9.json"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


# --- identiteit en grootboek ------------------------------------------------------------


class TestIdentiteit:
    def test_r9_caps_reserve_voorganger_en_cumulatief(self):
        r9 = gb.R9
        assert r9.proef_id == R9_ID
        assert dict(r9.fasecaps) == {
            "ontwikkeling": 2,
            "verificatie_alleen": 6,
            "t_eind": 40,
            "t_herhaling": 16,
        }
        assert (r9.reserve_max, r9.totaal_max) == (0, 64)
        assert r9.voorganger is gb.R8
        assert r9.cumulatief_max == 424
        assert r9.modelstappen_per_geval == 2

    def test_zelfde_stappen_volgorde_stop_en_gedeelde_binding_als_r8(self):
        r9 = gb.R9
        assert dict(r9.fasestappen) == dict(gb.R8.fasestappen)
        assert dict(r9.fasevolgorde) == dict(gb.R8.fasevolgorde)
        assert r9.eindgroepen == gb.R8.eindgroepen
        assert r9.bindingsvelden == gb.R8.bindingsvelden
        assert (r9.stop_bij_eerste_fout, r9.gedeelde_codebinding) == (True, True)

    def test_kostenbewaking_zelfde_model_en_grenzen_lager_plafond(self):
        kb9, kb8 = gb.R9.kostenbewaking, gb.R8.kostenbewaking
        assert kb9.plafond_nusd == 24_901_265_000
        assert gb.R9.kostenkader_nusd == 25_000_000_000
        assert kb9.plafond_nusd + R8_KOSTEN_NUSD == gb.R9.kostenkader_nusd
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb9, veld) == getattr(kb8, veld), veld
        assert dict(kb9.bytegrens) == dict(kb8.bytegrens)

    def test_begroting_past_binnen_het_resterende_plafond(self):
        # 1 + 20 + 8 volledige ketens à 0,69 plus 6 verificaties à 0,375.
        assert gb.begroting_nusd(gb.R9) == 22_260_000_000
        assert gb.begroting_nusd(gb.R9) <= gb.R9.kostenbewaking.plafond_nusd

    def test_r8_en_ouder_ongewijzigd(self):
        assert (gb.R8.totaal_max, gb.R8.reserve_max, gb.R8.cumulatief_max) == (
            68,
            0,
            427,
        )
        assert gb.R8.kostenbewaking.plafond_nusd == 25_000_000_000
        assert gb.R8.kostenkader_nusd is None
        for oud in (gb.R1, gb.R2, gb.R3, gb.R4, gb.R5, gb.R6, gb.R7):
            assert oud.kostenbewaking is None and oud.kostenkader_nusd is None

    def test_r9_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "r9" / "callgrootboek.jsonl", gb.R9)
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(boek.pad, gb.R8)
        assert gb.Grootboek.open(boek.pad, gb.R9).identiteit is gb.R9


class TestCumulatiefEnKostenkader:
    def test_cumulatief_424_past_425_niet(self, tmp_path):
        # 360 werkelijke R1–R8-calls: vijf rondes à 57, twee à 37 en R8 één.
        voorgangers = [_r8_boek(tmp_path / "r8")]
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
        boek = gb.Grootboek.nieuw(tmp_path / "r9" / "callgrootboek.jsonl", gb.R9)
        gb.controleer_cumulatief(boek, voorgangers, 64)
        with pytest.raises(gb.BudgetSchendingError, match="424"):
            gb.controleer_cumulatief(boek, voorgangers, 65)

    def _keten_boeken(self, tmp_path, **r8):
        opslagen = _keten9(tmp_path, **r8)
        identiteiten = gb.voorgangerketen(gb.R9)
        return [
            gb.Grootboek.lees(o.grootboek, i)
            for o, i in zip(opslagen, identiteiten, strict=True)
        ]

    def test_kostenkader_met_de_werkelijke_r8_kosten_precies_25(self, tmp_path):
        keten = self._keten_boeken(tmp_path)
        assert keten[0].kostenstand()["lopend_nusd"] == R8_KOSTEN_NUSD
        boek = gb.Grootboek.nieuw(tmp_path / "r9" / "callgrootboek.jsonl", gb.R9)
        gb.controleer_cumulatief(boek, keten, 1)

    @pytest.mark.parametrize(
        "r8",
        [
            {"kosten": R8_KOSTEN_NUSD + 1},  # één nanodollar meer dan bewezen
            {"kosten": None},  # onbekende kosten tellen met hun stapgrens
            {"gesloten": False},  # onafgesloten (crash) telt met haar grens
        ],
    )
    def test_kostenkader_weigert_zodra_r8_meer_telt(self, tmp_path, r8):
        keten = self._keten_boeken(tmp_path, **r8)
        boek = gb.Grootboek.nieuw(tmp_path / "r9" / "callgrootboek.jsonl", gb.R9)
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            gb.controleer_cumulatief(boek, keten, 1)


# --- runnerregistratie ------------------------------------------------------------------


class TestRegistratie:
    def test_r9_geregistreerd_met_eigen_opslag_invoer_en_besluit(self):
        proef = runner.PROEVEN["R9"]
        assert proef.identiteit is gb.R9
        # Gesloten na de inhoudelijke stop op R720; de registratie blijft staan.
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (False, True)
        assert proef.opslag.root == R9_MAP
        assert proef.t_ontwikkelinvoer_sha256 == runner.R9_T_ONTWIKKELINVOER_SHA256
        # Ongewijzigde V-invoer van R8: dezelfde bestandshash.
        assert proef.v_invoer_sha256 == R8_VINVOER_SHA256 == runner.R8_V_INVOER_SHA256
        assert proef.g_ontwikkelinvoer_sha256 is None
        assert proef.budgetbesluit == BESLUIT9
        assert proef.budgetbesluit_sha256 == BESLUIT9_SHA256
        assert proef.payloadtoestemming == TOESTEMMING
        assert proef.payloadtoestemming_sha256 == TOESTEMMING_SHA256
        assert dict(proef.contract) == CONTRACT

    def test_r8_en_r9_gesloten_met_behouden_besluit(self):
        # Ook R10 is na zijn inhoudelijke stop (C3) gesloten; alleen R11 is open.
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == [
            "R11",
            "R12",
            "R13",
            "R14",
        ]
        r9 = runner.PROEVEN["R9"]
        assert (r9.budgetbesluit_sha256, dict(r9.contract)) == (
            BESLUIT9_SHA256,
            CONTRACT,
        )
        r8 = runner.PROEVEN["R8"]
        assert r8.echt_toegestaan is False
        # Het oorspronkelijke 68/25-besluit blijft gepind (grond onder R9).
        assert (r8.budgetbesluit, r8.budgetbesluit_sha256) == (
            BESLUIT8,
            BESLUIT8_SHA256,
        )
        assert r8.contract is None and r8.payloadtoestemming is None

    def test_r8_gesloten_ook_via_de_oude_geregistreerde_route(self):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        r8 = runner.PROEVEN["R8"]
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, r8.opslag, r8)
        assert provider.aanroepen == []

    def test_cli_echt_r8_geweigerd_zonder_omgeving(self, monkeypatch, tmp_path, capsys):
        def verboden(**_kw):
            raise AssertionError("geen live omgeving voor gesloten R8")

        voor = _stand(R8_MAP / "callgrootboek.jsonl")
        monkeypatch.setattr(runner, "live_omgeving", verboden)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(SystemExit) as fout:
            runner.main(["--proef", "R8", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert fout.value.code == 2
        assert "gesloten" in capsys.readouterr().err
        assert _stand(R8_MAP / "callgrootboek.jsonl") == voor

    def test_r9_gesloten_ook_via_de_geregistreerde_route(self):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        r9 = runner.PROEVEN["R9"]
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, r9.opslag, r9)
        assert provider.aanroepen == []

    def test_cli_echt_r9_geweigerd_zonder_omgeving(self, monkeypatch, tmp_path, capsys):
        def verboden(**_kw):
            raise AssertionError("geen live omgeving voor gesloten R9")

        voor = _stand(R9_MAP / "callgrootboek.jsonl")
        monkeypatch.setattr(runner, "live_omgeving", verboden)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(SystemExit) as fout:
            runner.main(["--proef", "R9", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert fout.value.code == 2
        assert "gesloten" in capsys.readouterr().err
        assert _stand(R9_MAP / "callgrootboek.jsonl") == voor

    @besluiten_nodig
    def test_cli_echt_bouwt_de_live_omgeving_op_productiegrenzen(
        self, monkeypatch, tmp_path
    ):
        # Hypothetisch open R9 met de huidige code: de productiegrenzen
        # (3000 tokens, 60 s) blijven; gestopt vóór client, grootboek en netwerk.
        monkeypatch.setitem(runner.PROEVEN, "R9", _r9(echt_toegestaan=True))
        gebouwd = {}
        voor = _stand(R9_MAP / "callgrootboek.jsonl")

        class _GestoptError(Exception):
            pass

        def _live(**kw):
            gebouwd.update(kw)
            raise _GestoptError  # vóór client, grootboek en netwerk

        monkeypatch.setattr(runner, "live_omgeving", _live)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(_GestoptError):
            runner.main(["--proef", "R9", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert gebouwd == {
            "timeout": 60,
            "max_tokens_t": 3000,
            "verifier_max_tokens": 3000,
        }
        assert _stand(R9_MAP / "callgrootboek.jsonl") == voor

    @besluiten_nodig
    def test_geregistreerde_route_dicht_op_sluiting_en_contract(self):
        # Alleen de sluiting en het historische contract houden R9 dicht; het
        # besluit, de grenzen en de kostenroute passen nog.
        proef = runner.PROEVEN["R9"]
        omg = dataclasses.replace(_omgeving8(_R8Provider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, proef.opslag, proef)
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner._controleer_contract(omg, proef)
        runner._controleer_goedkeuring(omg, proef)
        runner._controleer_productiegrenzen(omg, proef)
        runner._controleer_kostenroute(omg, proef)
        assert runner._besluit_voor(omg, proef) == BESLUIT9_SHA256

    def test_echt_buiten_de_canonieke_opslag_geweigerd(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            _t9(omg, tmp_path, pad, proef=_r9(echt_toegestaan=True))
        assert provider.aanroepen == []
        assert not _opslag9(tmp_path).grootboek.exists()


# --- budgetbesluit ----------------------------------------------------------------------


class TestBudgetbesluit:
    @besluiten_nodig
    def test_besluit_past_op_r9_en_draagt_het_oorspronkelijke_kader(self):
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R9"]) == BESLUIT9_SHA256
        # Het oorspronkelijke besluit blijft zelf geldig voor zijn eigen identiteit.
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R8"]) == BESLUIT8_SHA256

    @besluiten_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 65},
            {"cumulatief_max": 425},
            {"historisch_verbruik": 359},
            {"reserve": 1},
            {"kostenbudget_usd": "24.901266"},
            {"fasen_modelstappen_max": {"ontwikkeling": 6, "verificatie_alleen": 6,
                                        "t_eind": 40, "t_herhaling": 16}},
            {"gebruikersantwoord": ""},
            {"oorspronkelijk_kostenbudget_usd": "26.00"},
            {"r8_verbruik_usd": "0.098734"},
            {"oorspronkelijk_extra_budget": 64},
            {"r8_verbruik_modelstappen": 5},
            {"oorspronkelijk_cumulatief_plafond": 428},
        ],
    )  # fmt: skip
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        pad = _besluit9(tmp_path, **anders)
        proef = _r9(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)

    @besluiten_nodig
    def test_ongepind_of_ontbrekend_besluit_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r9(budgetbesluit=_besluit9(tmp_path)))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r9(budgetbesluit=tmp_path / "geen.json"))

    @besluiten_nodig
    def test_gewijzigd_oorspronkelijk_besluit_weigert_r9(self, monkeypatch, tmp_path):
        kopie = tmp_path / "besluit8.json"
        kopie.write_text(BESLUIT8.read_text(encoding="utf-8") + " ", encoding="utf-8")
        r8 = dataclasses.replace(runner.PROEVEN["R8"], budgetbesluit=kopie)
        monkeypatch.setitem(runner.PROEVEN, "R8", r8)
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(runner.PROEVEN["R9"])

    @besluiten_nodig
    @pytest.mark.parametrize(
        "anders",
        [None, {"budget_calls_max": 64}, {"budget_usd_max": 30}, {"user_reply": ""}],
    )
    def test_payloadtoestemming_gepind_en_passend(self, tmp_path, anders):
        data = json.loads(TOESTEMMING.read_text(encoding="utf-8"))
        data.update(anders or {})
        pad = tmp_path / "toestemming.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        # None: ongewijzigde inhoud, maar niet de gepinde bytes.
        sha = _sha(pad) if anders else TOESTEMMING_SHA256
        proef = _r9(payloadtoestemming=pad, payloadtoestemming_sha256=sha)
        with pytest.raises(gb.BudgetSchendingError, match="toestemming"):
            runner.controleer_budgetbesluit(proef)


# --- prompt- en antwoordcontract ------------------------------------------------------


class TestContract:
    def test_r9_contract_historisch_de_code_draagt_het_huidige(self):
        omg = _omgeving8(_R8Provider())
        assert dict(runner.PROEVEN["R9"].contract) == CONTRACT
        assert runner.contractidentiteit(omg) == HUIDIG_CONTRACT
        assert {k for k in CONTRACT if CONTRACT[k] != HUIDIG_CONTRACT[k]} == {
            "prompt_version",
            "verification_prompt_version",
            "answer_schema_version",
        }
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner._controleer_contract(omg, runner.PROEVEN["R9"])
        runner._controleer_contract(omg, _r9())

    @pytest.mark.parametrize(
        ("doel", "naam", "waarde"),
        [
            ("services.validation.ess05_assessment_service.Ess05AssessmentService",
             "PROMPT_VERSION", "ess05-assess/14"),
            ("domain.ess05.bewijs", "ANTWOORDSCHEMA", "ess05-answer/1"),
            ("domain.ess05.bewijs", "CONCEPTSCHEMA", "ess05-concept/2"),
        ],
    )  # fmt: skip
    def test_andere_code_voor_grootboek_geweigerd(
        self, monkeypatch, tmp_path, doel, naam, waarde
    ):
        monkeypatch.setattr(f"{doel}.{naam}", waarde)
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            _t9(_omgeving8(provider), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag9(tmp_path).grootboek.exists()

    def test_freeze_pint_het_antwoordcontract_voor_v_en_t(self):
        omg = _omgeving8(_R8Provider())
        v, t = (runner.freezevelden(omg, _r9(), g) for g in ("v", "t"))
        for velden in (v, t):
            assert velden["proef_id"] == R9_ID
            assert {k: velden[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        # V en T onderling gebonden: alleen de groep verschilt.
        assert {k for k in v if v[k] != t[k]} == {"groep"}

    def test_r8_freezevelden_niet_herschreven(self):
        velden = runner.freezevelden(
            _omgeving8(_R8Provider()), runner.PROEVEN["R8"], "t"
        )
        assert "answer_schema_version" not in velden
        assert "concept_schema_version" not in velden

    def test_r8_freeze_geldt_niet_voor_r9(self, tmp_path):
        omg = _omgeving8(_R8Provider())
        pad = tmp_path / "freeze-r8.json"
        pad.write_text(json.dumps(runner.freezevelden(omg, runner.PROEVEN["R8"], "t")),
                       encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            runner.controleer_freeze(pad, omg, runner.PROEVEN["R9"], "t",
                                     dataset_sha256="a" * 64, herhaal_ids=[])  # fmt: skip


# --- ontwikkelinvoer: alleen R720, exact uit de R8-selectie ------------------------------


class TestOntwikkelinvoer:
    def test_maker_vastgelegde_bron_doel_en_plan(self):
        assert mk9.BRON == R8_SELECTIE
        assert (
            mk9.BRON_SHA256 == R8_SELECTIE_SHA256 == runner.R8_T_ONTWIKKELINVOER_SHA256
        )
        assert mk9.T_DOEL == R9_SELECTIE
        assert mk9.T_PLAN == ("R720",)

    @r8_selectie_nodig
    def test_alleen_r720_exact_uit_de_r8_selectie(self):
        bron = R8_SELECTIE.read_bytes()
        selectie = mk9.maak_t_selectie(bron, bron_pad="x")
        (geval,) = selectie["gevallen"]
        (origineel,) = [g for g in json.loads(bron)["gevallen"] if g["id"] == "R720"]
        assert json.dumps(geval, sort_keys=True) == json.dumps(
            origineel, sort_keys=True
        )
        assert "herhaal_ids" not in selectie
        assert selectie["herkomst"]["bronnen"]["r8_selectie"]["sha256"] == (
            R8_SELECTIE_SHA256
        )
        mk9.controleer_t_selectie(selectie, bron)

    def test_andere_bron_geweigerd(self):
        with pytest.raises(mk9.SelectiefoutError, match="bronhash"):
            mk9.maak_t_selectie(b"{}", bron_pad="x")

    @r8_selectie_nodig
    @pytest.mark.parametrize("mutatie", ["gewijzigd", "extra", "ander"])
    def test_afwijkende_selectie_geweigerd(self, mutatie):
        bron = R8_SELECTIE.read_bytes()
        selectie = mk9.maak_t_selectie(bron, bron_pad="x")
        andere = [g for g in json.loads(bron)["gevallen"] if g["id"] != "R720"]
        if mutatie == "gewijzigd":
            selectie["gevallen"][0]["verwacht"] = "pass"
        elif mutatie == "extra":
            selectie["gevallen"].append(andere[0])
        else:
            selectie["gevallen"] = [andere[0]]
        with pytest.raises(mk9.SelectiefoutError):
            mk9.controleer_t_selectie(selectie, bron)

    @r8_selectie_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        doel = tmp_path / "t.json"
        assert mk9.main(["--t-doel", str(doel)]) == 0
        with pytest.raises(FileExistsError):
            mk9.main(["--t-doel", str(doel)])

    @r8_selectie_nodig
    @pytest.mark.skipif(not R9_SELECTIE.is_file(), reason="R9-selectie ontbreekt")
    def test_vastgelegde_r9_invoer_reproduceerbaar_en_gepind(self, tmp_path):
        doel = tmp_path / "t.json"
        assert mk9.main(["--t-doel", str(doel)]) == 0
        vast = json.loads(R9_SELECTIE.read_text(encoding="utf-8"))
        opnieuw = json.loads(doel.read_text(encoding="utf-8"))
        opnieuw["herkomst"]["bron_pad_aanroep"] = vast["herkomst"]["bron_pad_aanroep"]
        assert vast == opnieuw
        assert _sha(R9_SELECTIE) == runner.R9_T_ONTWIKKELINVOER_SHA256

    @r8_selectie_nodig
    def test_r8_selectie_met_drie_gevallen_geweigerd_voor_r9(self):
        with pytest.raises(gb.BudgetSchendingError, match="T-ontwikkelselectie"):
            runner._controleer_ontwikkelinvoer(
                runner.PROEVEN["R9"], "ontwikkeling", R8_SELECTIE
            )


# --- offline runs op de R9-registratie --------------------------------------------------


def _ontwikkeling9_geaccepteerd(tmp_path: Path) -> None:
    boek = gb.Grootboek.nieuw(_opslag9(tmp_path).grootboek, gb.R9)
    poging = "ontwikkeling|R720|1"
    for index, (taak, naam) in enumerate(((V, "beoordeling"), (W, "verificatie"))):
        res = boek.reserveer("ontwikkeling", f"{poging}/{naam}", invoer_sha256="a" * 64,
                             poging=poging, stap=naam,
                             vorige_stap="beoordeling" if index else None,
                             task_type=taak)  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
    boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="test")


def _v9(omg, tmp_path, pad, *, ontwikkeling=True):
    proef = _r9(v_invoer_sha256=_sha(pad))
    if ontwikkeling:
        _ontwikkeling9_geaccepteerd(tmp_path)
    freeze = tmp_path / "freeze-v.json"
    freeze.write_text(
        json.dumps(runner.freezevelden(omg, proef, "v")), encoding="utf-8"
    )
    return asyncio.run(
        runner.voer_v_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag9(tmp_path),
            proef=proef,
            freeze=freeze,
            voorganger_opslag=_keten9(tmp_path),
            nieuw_grootboek=not ontwikkeling,
        )
    )


class TestOfflineRuns:
    def test_ontwikkeling_een_geval_twee_stappen_met_keten_incl_r8(self, tmp_path):
        provider = _R8Provider()
        uitkomst = _t9(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 1))
        assert provider.stappen == ["beoordeling", "verificatie"]
        reserveringen = _soort(tmp_path, "reservering")
        assert [(r["task_type"], r["kosten_grens_nusd"]) for r in reserveringen] == [
            (V, 315_000_000),
            (W, 375_000_000),
        ]
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is True, geval["reden"]
        anker = json.loads(runner.gb.ankerpad(_opslag9(tmp_path).grootboek).read_text())
        assert anker["proef_id"] == R9_ID
        voorganger = uitkomst["voorganger_grootboek"]
        assert voorganger["proef_id"] == gb.R8.proef_id
        assert voorganger["keten"][0] == {"proef_id": gb.R8.proef_id, "totaal": 1}
        assert voorganger["cumulatief_max"] == 424
        assert uitkomst["grootboek_na"]["kosten"]["plafond_nusd"] == 24_901_265_000

    def test_twee_ontwikkelgevallen_boven_de_fasecap_geweigerd(self, tmp_path):
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="fasecap ontwikkeling"):
            _t9(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 2))
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []

    def test_kostenkader_boven_25_start_niets(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        keten = _keten9(tmp_path, kosten=R8_KOSTEN_NUSD + 1)
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            _t9(_omgeving8(provider), tmp_path, pad, keten=keten)
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []

    def test_niet_geaccepteerd_r720_stopt_r9_duurzaam(self, tmp_path):
        provider = _R8Provider(onderscheid="not_distinguished")
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _t9(_omgeving8(provider), tmp_path, pad)
        assert len(provider.aanroepen) == 2
        v_pad, _ = _v_invoer(tmp_path, ("goed",))
        omg, proef = _omgeving8(provider), _r9(v_invoer_sha256=_sha(v_pad))
        freeze = tmp_path / "freeze-v.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, proef, "v")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            asyncio.run(runner.voer_v_fase(
                omg, gevallenpad=v_pad, uitmap=tmp_path / "uit",
                opslag=_opslag9(tmp_path), proef=proef, freeze=freeze,
                voorganger_opslag=_bestaande_keten9(tmp_path),
            ))  # fmt: skip
        assert len(provider.aanroepen) == 2

    def test_v_pas_na_geaccepteerde_r720(self, tmp_path):
        pad, _ = _v_invoer(tmp_path, ("goed",))
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkeling"):
            _v9(_omgeving8(provider), tmp_path, pad, ontwikkeling=False)
        assert provider.aanroepen == []

    def test_v_zes_items_na_r720(self, tmp_path):
        pad, items = _v_invoer(tmp_path, ("goed", "fout") * 3)
        provider = _R8Provider(
            uitkomsten={
                i["concept_hash"]: {i["foutdragende_items"][0]: "unsupported"}
                for i in items
                if i["soort"] == "fout"
            }
        )
        uitkomst = _v9(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"] * 6
        gevallen = [
            g for g in _soort(tmp_path, "geval") if g["fase"] == "verificatie_alleen"
        ]
        assert [g["geaccepteerd"] for g in gevallen] == [True] * 6
        assert uitkomst["aanroepen_gestart"] == 6

    @pytest.mark.skipif(not R8_VINVOER.is_file(), reason="R8-V-invoer ontbreekt")
    @pytest.mark.skipif(not R9_SELECTIE.is_file(), reason="R9-selectie ontbreekt")
    @pytest.mark.parametrize(
        ("fase", "pad"),
        [("verificatie_alleen", R8_VINVOER), ("ontwikkeling", R9_SELECTIE)],
    )
    def test_droog_geregistreerde_r9_weigert_op_het_contract(self, tmp_path, fase, pad):
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner.main(["--proef", "R9", "--fase", fase, "--gevallen", str(pad),
                         "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    @pytest.mark.skipif(not R8_VINVOER.is_file(), reason="R8-V-invoer ontbreekt")
    def test_droog_r8_verificatie_invoer_hoort_bij_verify_2(
        self, monkeypatch, tmp_path
    ):
        """Onder de huidige code weigert de runner de bevroren invoer: haar
        verificatieprompthashes horen bij verify/2. Een nieuwe proef vraagt een
        nieuwe V-invoer (materiaal en concepten ongewijzigd)."""
        assert _sha(R8_VINVOER) == R8_VINVOER_SHA256
        monkeypatch.setitem(runner.PROEVEN, "R9", _r9())
        with pytest.raises(
            runner.pi.InvoerfoutError, match="verificatieprompt wijkt af"
        ):
            runner.main(["--proef", "R9", "--fase", "verificatie_alleen",
                         "--gevallen", str(R8_VINVOER), "--uitmap", str(tmp_path),
                         "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    @pytest.mark.skipif(not R9_SELECTIE.is_file(), reason="R9-selectie ontbreekt")
    def test_droog_vastgelegde_r9_ontwikkelselectie(self, monkeypatch, tmp_path):
        # Materiaalcompatibiliteit onder de huidige code (kopie met huidig contract).
        monkeypatch.setitem(runner.PROEVEN, "R9", _r9())
        code = runner.main(["--proef", "R9", "--fase", "ontwikkeling", "--gevallen",
                            str(R9_SELECTIE), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R9_ID, 1)
        assert [i["sleutel"] for i in droog["items"]] == ["ontwikkeling|R720|1"]
        grens = gb.R9.kostenbewaking.bytegrens[V]
        assert all(i["payload_bytes"] <= grens for i in droog["items"])

    def test_droog_weigert_andere_contractcode(self, monkeypatch, tmp_path):
        monkeypatch.setattr("domain.ess05.bewijs.ANTWOORDSCHEMA", "ess05-answer/1")
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            asyncio.run(runner.droogrun("ontwikkeling", pad, tmp_path,
                                        proef=_r9(t_ontwikkelinvoer_sha256=_sha(pad))))  # fmt: skip
