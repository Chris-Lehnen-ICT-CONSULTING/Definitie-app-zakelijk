"""DEF-768 R10 — gerichte proef na het R9-bewijsherstel: registratie en V7, offline.

Besluit van Chris (26-09, "ja", logs/def768/ronde10-herproefgoedkeuring-v1.json)
op logs/def768/bewijsherstel-vervolgproef-voorstel-v1.md: max 65 modelstappen
(2 ontwikkeling = alleen R720, 7 verifier-only, 40 t_eind, 16 t_herhaling),
reserve 0, cumulatief met R1–R9 max 427 (362 + 65), routerplafond USD
24,722355 zodat R8 (USD 0,098735) + R9 (USD 0,178910) + R10 binnen het
oorspronkelijke kader van USD 25 blijft.

- R10 is een eigen identiteit met eigen opslag; R1–R9 blijven gesloten, via de
  CLI én programmatisch (ook een heropende kopie start niets);
- het budgetbesluit is gepind en draagt het oorspronkelijke 68/25-besluit, het
  R9-besluit en de payloadtoestemming (alle op hash gepind) mee;
- het kostenkader telt de werkelijke R8- én R9-kosten uit hun grootboeken mee;
- R10 legt de gereviewde contractidentiteit vast (`ess05-assess/16`,
  `ess05-verify/3`, `ess05-answer/1`), ook in de freeze;
- de ontwikkelinvoer is exact de R9-selectie (alleen R720);
- V7: de zes R8-items ongewijzigd behalve hun verificatieprompthash (verify/3),
  plus V-N4 = het ongewijzigde R9-R720-concept met foutdrager `claim:C5`.

Na de inhoudelijke stop op R720 (26-09, NO-GO op claim C3) is R10 gesloten,
ook via de geregistreerde route. Besluit, contract (`/16`, `/3`) en V7 blijven
historisch gepind; de code draagt sinds het C3-herstel `ess05-assess/17` en
`ess05-verify/4`, dus R10 past niet meer op de huidige code. De offline
mechaniektests draaien daarom op een kopie van R10 met de huidige
contractidentiteit (`_r10`); V7 bindt de verify/3-prompt en wordt onder verify/4
geweigerd. De V-mechaniek draait op een onder de huidige code herbouwde V7.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import hashlib
import json
import shutil
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import (
    ROOT,
    _AnderValidatiemodel,
    _gevallenbestand,
)
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import (
    _keten as _keten_tot_r7,
    _omgeving8,
    _R8Provider,
)
from tests.unit.scripts.test_def768_r9_proef import R8_KOSTEN_NUSD, _r8_boek

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import migreer_r7_naar_v2 as mig
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

try:  # de V7-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r10_verificatie_invoer as mk10
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk10 = None

R10_ID = "DEF-768-AI-20260926-R10"
R10_MAP = ROOT / "reports" / R10_ID
V7 = R10_MAP / "verificatie-invoer-v1.json"
R8_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R8"
R8_VINVOER = R8_MAP / "verificatie-invoer-v1.json"
R8_VINVOER_SHA256 = "ddece7dbbdf928be8c89aca819e110ea0e8ad6e45aaf6ce582fe27c7528d155c"
R9_MAP = ROOT / "reports" / "DEF-768-AI-20260926-R9"
R9_SELECTIE = R9_MAP / "ontwikkelselectie-v1.json"
R9_SELECTIE_SHA256 = "4e11ebe579ba9852217951fdf21466dc3131f2ba925f49fb7114b242eef3439d"
R9_RECORD = (
    R9_MAP
    / "ontwikkeling-20260926T055126989046Z"
    / "calls"
    / "001-ontwikkeling-R720.json"
)
R9_RECORD_SHA256 = "8995634a5615828a03300b8274fc535ffe49ca1f64b2badd71ccffeb6c7a0a8c"
R9_CONCEPT_HASH = "9faab46592a6aeab83589b18f689e456ab2e96c0fa7b3750e06054844e5f46cf"
STOP9 = R9_MAP / "inhoudelijke-stop-v1.json"
STOP9_SHA256 = "0766cbbede67808e733f73b99a44e28586f76b82db6e80b75f64da985f03d23b"
LOGS = ROOT / "logs" / "def768"
INHOUD9 = LOGS / "ronde9-r720-inhoudscontrole-result-v1.md"
INHOUD9_SHA256 = "e520ee2aed691ac9b3aef23224688e31ef15e8cbef40f7d53c029dc18abc6b80"
BESLUIT10 = LOGS / "ronde10-herproefgoedkeuring-v1.json"
BESLUIT10_SHA256 = "7ca9ca3ec1c864c86a50f5b27ba51ef262174e6840dba2dd310afde04b0157a8"
BESLUIT9 = LOGS / "ronde9-herproefgoedkeuring-v1.json"
BESLUIT9_SHA256 = "89ea16dddc7bb4403d4aa6f6fdaebc385f8fb40c40e1d6698b98bcd321765018"
BESLUIT8 = LOGS / "ronde8-budgetgoedkeuring-v1.json"
BESLUIT8_SHA256 = "bf82cd3bfd6cea12fc0d3d97df2305c922fdde8c19fb84db6f0a1e3320195d17"
TOESTEMMING = LOGS / "ronde8-anthropic-versturingstoestemming-v1.json"
TOESTEMMING_SHA256 = "a118986fa8c05161beb4f1b8eae642cc5b8ba05cb879519b289a734f26ac3a08"
#: De echte R9-stand: twee betaalde stappen, geval (automatisch) geaccepteerd.
R9_KOSTEN_NUSD = 178_910_000
CONTRACT10 = {
    "prompt_version": "ess05-assess/16",
    "verification_prompt_version": "ess05-verify/3",
    "answer_schema_version": "ess05-answer/1",
    "concept_schema_version": "ess05-concept/1",
    "verification_schema_version": "ess05-verification/1",
}
#: De huidige code (answer/3): beide promptversies en het antwoordschema verschillen.
HUIDIG_CONTRACT = {
    **CONTRACT10,
    "prompt_version": "ess05-assess/19",
    "verification_prompt_version": "ess05-verify/4",
    "answer_schema_version": "ess05-answer/3",
}
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10")
V = "validation"
W = "ess05_verification"

besluiten_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (BESLUIT10, BESLUIT9, BESLUIT8, TOESTEMMING)),
    reason="git-ignored besluiten ontbreken",
)
r9_bronnen_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (R8_VINVOER, R9_RECORD, R9_SELECTIE, STOP9, INHOUD9)),
    reason="git-ignored R8/R9-bronnen ontbreken",
)
v7_nodig = pytest.mark.skipif(
    not V7.is_file(), reason="git-ignored V7-invoer ontbreekt"
)


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _stand(pad: Path) -> str | None:
    """sha256 van een canoniek bestand, of None; tests mogen het nooit raken."""
    return _sha(pad) if Path(pad).exists() else None


def _r10(**anders) -> runner.Proef:
    """R10-kopie met de huidige contractidentiteit (het echte R10 blijft /16 + /3)."""
    anders.setdefault("contract", MappingProxyType(HUIDIG_CONTRACT))
    return dataclasses.replace(runner.PROEVEN["R10"], **anders)


def _r9_boek(root: Path, *, kosten: int | None = R9_KOSTEN_NUSD, gesloten=True):
    """Een R9-grootboek zoals het echte: twee betaalde stappen, geval geaccepteerd."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R9)
    poging = "ontwikkeling|R720|1"
    delen = (None, None) if kosten is None else (kosten // 2, kosten - kosten // 2)
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


def _keten10(tmp_path: Path, *, r9=None, r8=None):
    """(R9-, R8- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r9_opslag = runner.Proefopslag(tmp_path / "r9")
    r8_opslag = runner.Proefopslag(tmp_path / "r8")
    _r9_boek(r9_opslag.root, **(r9 or {}))
    _r8_boek(r8_opslag.root, **(r8 or {}))
    return (r9_opslag, r8_opslag, *_keten_tot_r7(tmp_path))


def _bestaande_keten10(tmp_path: Path):
    namen = ("r9", "r8", "r7", "r6", "r5", "r4", "r3", "r2", "r1")
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag10(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r10")


def _regels10(tmp_path: Path) -> list[dict]:
    pad = _opslag10(tmp_path).grootboek
    return [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    return [r for r in _regels10(tmp_path) if r["soort"] == soort]


def _t10(omg, tmp_path, pad, *, fase="ontwikkeling", nieuw=True, proef=None,
         keten=None, **kw):  # fmt: skip
    if keten is None:
        keten = _keten10(tmp_path) if nieuw else _bestaande_keten10(tmp_path)
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag10(tmp_path),
            proef=proef or _r10(t_ontwikkelinvoer_sha256=_sha(pad)),
            voorganger_opslag=keten,
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _besluit10(tmp_path: Path, **anders) -> Path:
    data = json.loads(BESLUIT10.read_text(encoding="utf-8"))
    for sleutel, waarde in anders.items():
        if waarde is None:
            data.pop(sleutel, None)
        else:
            data[sleutel] = waarde
    pad = tmp_path / "besluit10.json"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


def _ontwikkeling10_geaccepteerd(tmp_path: Path) -> gb.Grootboek:
    boek = gb.Grootboek.nieuw(_opslag10(tmp_path).grootboek, gb.R10)
    poging = "ontwikkeling|R720|1"
    for index, (taak, naam) in enumerate(((V, "beoordeling"), (W, "verificatie"))):
        res = boek.reserveer("ontwikkeling", f"{poging}/{naam}", invoer_sha256="a" * 64,
                             poging=poging, stap=naam,
                             vorige_stap="beoordeling" if index else None,
                             task_type=taak)  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
    boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="test")
    return boek


def _v10(omg, tmp_path, pad, *, ontwikkeling=True, proef=None):
    proef = proef or _r10(v_invoer_sha256=_sha(pad))
    if ontwikkeling:
        _ontwikkeling10_geaccepteerd(tmp_path)
    freeze = tmp_path / "freeze-v.json"
    freeze.write_text(
        json.dumps(runner.freezevelden(omg, proef, "v")), encoding="utf-8"
    )
    return asyncio.run(
        runner.voer_v_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag10(tmp_path),
            proef=proef,
            freeze=freeze,
            voorganger_opslag=_keten10(tmp_path),
            nieuw_grootboek=not ontwikkeling,
        )
    )


def _v_gevallen(tmp_path) -> list[dict]:
    return [g for g in _soort(tmp_path, "geval") if g["fase"] == "verificatie_alleen"]


def _v7() -> dict:
    return json.loads(V7.read_text(encoding="utf-8"))


def _v7_huidig(tmp_path: Path) -> tuple[Path, list[dict]]:
    """V7 opnieuw gebouwd onder de huidige code (alleen de prompthashes wijken af)."""
    pad = tmp_path / "v7-huidig.json"
    assert mk10.main(["--doel", str(pad)]) == 0
    return pad, json.loads(pad.read_text(encoding="utf-8"))["items"]


def _foutdragers(items) -> dict[str, dict[str, str]]:
    """Stubverifier: elk fout item wijst exact zijn eerste foutdrager af."""
    return {
        i["concept_hash"]: {i["foutdragende_items"][0]: "unsupported"}
        for i in items
        if i["soort"] == "fout"
    }


# --- identiteit en grootboek ------------------------------------------------------------


class TestIdentiteit:
    def test_r10_caps_reserve_voorganger_en_cumulatief(self):
        r10 = gb.R10
        assert r10.proef_id == R10_ID
        assert dict(r10.fasecaps) == {
            "ontwikkeling": 2,
            "verificatie_alleen": 7,
            "t_eind": 40,
            "t_herhaling": 16,
        }
        assert (r10.reserve_max, r10.totaal_max) == (0, 65)
        assert r10.voorganger is gb.R9
        assert r10.cumulatief_max == 427 == 362 + 65
        assert r10.modelstappen_per_geval == 2

    def test_zelfde_stappen_volgorde_stop_en_gedeelde_binding_als_r9(self):
        r10 = gb.R10
        assert dict(r10.fasestappen) == dict(gb.R9.fasestappen)
        assert dict(r10.fasevolgorde) == dict(gb.R9.fasevolgorde)
        assert r10.eindgroepen == gb.R9.eindgroepen
        assert r10.bindingsvelden == gb.R9.bindingsvelden
        assert (r10.stop_bij_eerste_fout, r10.gedeelde_codebinding) == (True, True)

    def test_kostenbewaking_zelfde_model_en_grenzen_gezamenlijk_kader(self):
        kb10, kb8 = gb.R10.kostenbewaking, gb.R8.kostenbewaking
        assert kb10.plafond_nusd == 24_722_355_000
        assert gb.R10.kostenkader_nusd == 25_000_000_000
        assert (
            kb10.plafond_nusd + R8_KOSTEN_NUSD + R9_KOSTEN_NUSD
            == gb.R10.kostenkader_nusd
        )
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb10, veld) == getattr(kb8, veld), veld
        assert kb10.max_tokens == 3000
        assert dict(kb10.bytegrens) == dict(kb8.bytegrens)

    def test_begroting_past_binnen_het_resterende_plafond(self):
        # 1 + 20 + 8 volledige ketens à 0,69 plus 7 verificaties à 0,375.
        assert gb.begroting_nusd(gb.R10) == 22_635_000_000
        assert gb.begroting_nusd(gb.R10) <= gb.R10.kostenbewaking.plafond_nusd

    def test_r9_en_ouder_ongewijzigd(self):
        r9 = gb.R9
        assert (r9.totaal_max, r9.reserve_max, r9.cumulatief_max) == (64, 0, 424)
        assert r9.kostenbewaking.plafond_nusd == 24_901_265_000
        assert (r9.kostenkader_nusd, r9.voorganger) == (25_000_000_000, gb.R8)
        assert (gb.R8.totaal_max, gb.R8.cumulatief_max) == (68, 427)
        assert gb.R8.kostenbewaking.plafond_nusd == 25_000_000_000
        assert gb.R8.kostenkader_nusd is None

    def test_r10_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "r10" / "callgrootboek.jsonl", gb.R10)
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(boek.pad, gb.R9)
        assert gb.Grootboek.open(boek.pad, gb.R10).identiteit is gb.R10


class TestCumulatiefEnKostenkader:
    def test_cumulatief_427_past_428_niet(self, tmp_path):
        # 362 werkelijke R1–R9-calls: vijf rondes à 57, twee à 37, R8 één, R9 twee.
        voorgangers = [_r9_boek(tmp_path / "r9"), _r8_boek(tmp_path / "r8")]
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
        assert sum(b.samenvatting()["totaal"] for b in voorgangers) == 362
        boek = gb.Grootboek.nieuw(tmp_path / "r10" / "callgrootboek.jsonl", gb.R10)
        gb.controleer_cumulatief(boek, voorgangers, 65)
        with pytest.raises(gb.BudgetSchendingError, match="427"):
            gb.controleer_cumulatief(boek, voorgangers, 66)

    def _keten_boeken(self, tmp_path, **kw):
        opslagen = _keten10(tmp_path, **kw)
        identiteiten = gb.voorgangerketen(gb.R10)
        return [
            gb.Grootboek.lees(o.grootboek, i)
            for o, i in zip(opslagen, identiteiten, strict=True)
        ]

    def test_kostenkader_met_de_werkelijke_r8_en_r9_kosten_precies_25(self, tmp_path):
        keten = self._keten_boeken(tmp_path)
        assert [b.kostenstand()["lopend_nusd"] for b in keten[:2]] == [
            R9_KOSTEN_NUSD,
            R8_KOSTEN_NUSD,
        ]
        boek = gb.Grootboek.nieuw(tmp_path / "r10" / "callgrootboek.jsonl", gb.R10)
        gb.controleer_cumulatief(boek, keten, 1)

    @pytest.mark.parametrize(
        "kw",
        [
            {"r9": {"kosten": R9_KOSTEN_NUSD + 1}},  # één nanodollar meer dan bewezen
            {"r8": {"kosten": R8_KOSTEN_NUSD + 1}},
            {"r9": {"kosten": None}},  # onbekende kosten tellen met hun stapgrens
            {"r9": {"gesloten": False}},  # onafgesloten (crash) telt met haar grens
        ],
    )
    def test_kostenkader_weigert_zodra_r8_of_r9_meer_telt(self, tmp_path, kw):
        keten = self._keten_boeken(tmp_path, **kw)
        boek = gb.Grootboek.nieuw(tmp_path / "r10" / "callgrootboek.jsonl", gb.R10)
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            gb.controleer_cumulatief(boek, keten, 1)

    def test_kostenkader_boven_25_start_niets(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        keten = _keten10(tmp_path, r9={"kosten": R9_KOSTEN_NUSD + 1})
        with pytest.raises(gb.BudgetSchendingError, match="kostenkader"):
            _t10(_omgeving8(provider), tmp_path, pad, keten=keten)
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []


# --- registratie en sluiting van R1–R9 ---------------------------------------------------


class TestRegistratie:
    def test_r10_geregistreerd_met_eigen_opslag_invoer_en_besluit(self):
        proef = runner.PROEVEN["R10"]
        assert proef.identiteit is gb.R10
        # Gesloten na de inhoudelijke stop op R720 (C3); de registratie blijft.
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (False, True)
        assert proef.opslag.root == R10_MAP
        # Ontwikkeling: exact de oorspronkelijke R9-selectie (alleen R720).
        assert proef.t_ontwikkelinvoer_sha256 == R9_SELECTIE_SHA256
        assert runner.R9_T_ONTWIKKELINVOER_SHA256 == R9_SELECTIE_SHA256
        assert proef.v_invoer_sha256 == runner.R10_V_INVOER_SHA256
        assert proef.v_invoer_sha256 != R8_VINVOER_SHA256
        assert proef.g_ontwikkelinvoer_sha256 is None
        assert (proef.budgetbesluit, proef.budgetbesluit_sha256) == (
            BESLUIT10,
            BESLUIT10_SHA256,
        )
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        assert dict(proef.contract) == CONTRACT10

    def test_r10_dicht_besluiten_en_contracten_behouden(self):
        # Alleen R11 (eigen besluit na het C3-herstel) is open; zie de R11-tests.
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == [
            "R11",
            "R12",
            "R13",
            "R14",
            "R15",
        ]
        r10 = runner.PROEVEN["R10"]
        assert (r10.budgetbesluit_sha256, dict(r10.contract)) == (
            BESLUIT10_SHA256,
            CONTRACT10,
        )
        r9, r8 = runner.PROEVEN["R9"], runner.PROEVEN["R8"]
        assert (r9.budgetbesluit_sha256, r8.budgetbesluit_sha256) == (
            BESLUIT9_SHA256,
            BESLUIT8_SHA256,
        )
        assert r9.contract["prompt_version"] == "ess05-assess/15"
        assert r8.contract is None

    @pytest.mark.parametrize("naam", OUDE_RONDES)
    def test_oude_ronde_gesloten_via_de_cli(self, monkeypatch, tmp_path, capsys, naam):
        def verboden(**_kw):
            raise AssertionError(f"geen live omgeving voor gesloten {naam}")

        mappen = (R8_MAP, R9_MAP, R10_MAP)
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

    @pytest.mark.parametrize("naam", ["R8", "R9", "R10"])
    def test_heropende_kopie_van_een_oude_ronde_start_niets(self, tmp_path, naam):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        kopie = dataclasses.replace(runner.PROEVEN[naam], echt_toegestaan=True)
        with pytest.raises(gb.BudgetSchendingError, match="geregistreerde"):
            runner._controleer_registratie(omg, kopie)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError):
            asyncio.run(runner.voer_t_fase(
                omg, fase="ontwikkeling", gevallenpad=pad, uitmap=tmp_path / "uit",
                opslag=runner.Proefopslag(tmp_path / "x"), proef=kopie,
                voorganger_opslag=None, nieuw_grootboek=True,
            ))  # fmt: skip
        assert provider.aanroepen == []
        assert not (tmp_path / "x" / "callgrootboek.jsonl").exists()

    @besluiten_nodig
    def test_cli_echt_bouwt_de_live_omgeving_op_productiegrenzen(
        self, monkeypatch, tmp_path
    ):
        # Hypothetisch open R10 met de huidige code: de productiegrenzen
        # (3000 tokens, 60 s) blijven; gestopt vóór client, grootboek en netwerk.
        monkeypatch.setitem(runner.PROEVEN, "R10", _r10(echt_toegestaan=True))
        gebouwd = {}
        voor = _stand(R10_MAP / "callgrootboek.jsonl")

        class _GestoptError(Exception):
            pass

        def _live(**kw):
            gebouwd.update(kw)
            raise _GestoptError  # vóór client, grootboek en netwerk

        monkeypatch.setattr(runner, "live_omgeving", _live)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(_GestoptError):
            runner.main(["--proef", "R10", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert gebouwd == {
            "timeout": 60,
            "max_tokens_t": 3000,
            "verifier_max_tokens": 3000,
        }
        assert _stand(R10_MAP / "callgrootboek.jsonl") == voor

    @besluiten_nodig
    def test_geregistreerde_route_dicht_op_sluiting_en_contract(self):
        # Alleen de sluiting en het historische contract houden R10 dicht; het
        # besluit, de grenzen en de kostenroute passen nog.
        proef = runner.PROEVEN["R10"]
        omg = dataclasses.replace(_omgeving8(_R8Provider()), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, proef.opslag, proef)
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner._controleer_contract(omg, proef)
        runner._controleer_goedkeuring(omg, proef)
        runner._controleer_productiegrenzen(omg, proef)
        runner._controleer_kostenroute(omg, proef)
        assert runner._besluit_voor(omg, proef) == BESLUIT10_SHA256

    def test_echt_buiten_de_canonieke_opslag_geweigerd(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            _t10(omg, tmp_path, pad, proef=_r10(echt_toegestaan=True))
        assert provider.aanroepen == []
        assert not _opslag10(tmp_path).grootboek.exists()


class TestGeenVerruiming:
    @pytest.mark.parametrize(
        "anders",
        [{"max_tokens_t": 4000}, {"timeout": 90}, {"verifier_max_tokens": 6000}],
    )
    def test_token_of_timeoutverruiming_voor_grootboek_geweigerd(
        self, tmp_path, anders
    ):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="productiegrenzen"):
            _t10(_omgeving8(provider, **anders), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag10(tmp_path).grootboek.exists()

    def test_modelwissel_voor_grootboek_geweigerd(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="model"):
            _t10(_omgeving8(provider, router=_AnderValidatiemodel()), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag10(tmp_path).grootboek.exists()

    def test_technische_herhaling_geweigerd(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError):
            _t10(_omgeving8(provider), tmp_path, pad,
                 technische_herhalingen=("ontwikkeling|D0|1",))  # fmt: skip
        assert provider.aanroepen == []


# --- budgetbesluit ----------------------------------------------------------------------


class TestBudgetbesluit:
    @besluiten_nodig
    def test_besluit_past_op_r10_en_draagt_het_gezamenlijke_kader(self):
        assert (
            runner.controleer_budgetbesluit(runner.PROEVEN["R10"]) == BESLUIT10_SHA256
        )
        # De oudere besluiten blijven zelf geldig voor hun eigen identiteit.
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R9"]) == BESLUIT9_SHA256
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R8"]) == BESLUIT8_SHA256

    @besluiten_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 66},
            {"cumulatief_max": 428},
            {"historisch_verbruik": 363},
            {"reserve": 1},
            {"kostenbudget_usd": "24.722356"},
            {"fasen_modelstappen_max": {"ontwikkeling": 2, "verificatie_alleen": 8,
                                        "t_eind": 40, "t_herhaling": 16}},
            {"gebruikersantwoord": ""},
            {"oorspronkelijk_kostenbudget_usd": "26.00"},
            {"oorspronkelijk_extra_budget": 69},
            {"oorspronkelijk_cumulatief_plafond": 428},
            {"r8_verbruik_usd": "0.098734"},
            {"r9_verbruik_usd": "0.178911"},
            {"r9_verbruik_usd": None},
            {"r8_verbruik_modelstappen": 2},
            {"r9_verbruik_modelstappen": 1},
            {"r9_verbruik_modelstappen": None},
        ],
    )  # fmt: skip
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        pad = _besluit10(tmp_path, **anders)
        proef = _r10(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)

    @besluiten_nodig
    def test_ongepind_of_ontbrekend_besluit_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r10(budgetbesluit=_besluit10(tmp_path)))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r10(budgetbesluit=tmp_path / "geen.json"))

    @besluiten_nodig
    @pytest.mark.parametrize(("naam", "bron"), [("R9", BESLUIT9), ("R8", BESLUIT8)])
    def test_gewijzigd_eerder_besluit_weigert_r10(
        self, monkeypatch, tmp_path, naam, bron
    ):
        kopie = tmp_path / f"besluit-{naam}.json"
        kopie.write_text(bron.read_text(encoding="utf-8") + " ", encoding="utf-8")
        oud = dataclasses.replace(runner.PROEVEN[naam], budgetbesluit=kopie)
        monkeypatch.setitem(runner.PROEVEN, naam, oud)
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(runner.PROEVEN["R10"])

    @besluiten_nodig
    @pytest.mark.parametrize(
        "anders",
        [None, {"budget_calls_max": 65}, {"budget_usd_max": 30}, {"user_reply": ""}],
    )
    def test_payloadtoestemming_gepind_en_passend(self, tmp_path, anders):
        data = json.loads(TOESTEMMING.read_text(encoding="utf-8"))
        data.update(anders or {})
        pad = tmp_path / "toestemming.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        # None: ongewijzigde inhoud, maar niet de gepinde bytes.
        sha = _sha(pad) if anders else TOESTEMMING_SHA256
        proef = _r10(payloadtoestemming=pad, payloadtoestemming_sha256=sha)
        with pytest.raises(gb.BudgetSchendingError, match="toestemming"):
            runner.controleer_budgetbesluit(proef)


# --- prompt- en antwoordcontract, freeze --------------------------------------------------


class TestContract:
    def test_r10_contract_historisch_de_code_draagt_het_huidige(self):
        omg = _omgeving8(_R8Provider())
        assert dict(runner.PROEVEN["R10"].contract) == CONTRACT10
        assert runner.contractidentiteit(omg) == HUIDIG_CONTRACT
        assert {k for k in CONTRACT10 if CONTRACT10[k] != HUIDIG_CONTRACT[k]} == {
            "prompt_version",
            "verification_prompt_version",
            "answer_schema_version",
        }
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner._controleer_contract(omg, runner.PROEVEN["R10"])
        runner._controleer_contract(omg, _r10())

    @pytest.mark.parametrize(
        ("doel", "naam", "waarde"),
        [
            ("services.validation.ess05_assessment_service.Ess05AssessmentService",
             "PROMPT_VERSION", "ess05-assess/15"),
            ("services.validation.ess05_verification_service.Ess05VerificationService",
             "PROMPT_VERSION", "ess05-verify/2"),
            ("domain.ess05.bewijs", "ANTWOORDSCHEMA", "ess05-answer/1"),
        ],
    )  # fmt: skip
    def test_andere_code_voor_grootboek_geweigerd(
        self, monkeypatch, tmp_path, doel, naam, waarde
    ):
        monkeypatch.setattr(f"{doel}.{naam}", waarde)
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            _t10(_omgeving8(provider), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag10(tmp_path).grootboek.exists()

    def test_freeze_pint_het_contract_voor_v_en_t(self):
        omg = _omgeving8(_R8Provider())
        v, t = (runner.freezevelden(omg, _r10(), g) for g in ("v", "t"))
        for velden in (v, t):
            assert velden["proef_id"] == R10_ID
            assert {k: velden[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        assert {k for k in v if v[k] != t[k]} == {"groep"}

    def test_r9_freeze_geldt_niet_voor_r10(self, tmp_path):
        omg = _omgeving8(_R8Provider())
        pad = tmp_path / "freeze-r9.json"
        pad.write_text(json.dumps(runner.freezevelden(omg, runner.PROEVEN["R9"], "t")),
                       encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="proef_id"):
            runner.controleer_freeze(pad, omg, _r10(), "t",
                                     dataset_sha256="a" * 64, herhaal_ids=[])  # fmt: skip


# --- fasegrenzen, freeze en stop ----------------------------------------------------------


def _tot_en_met_v(tmp_path: Path):
    """Offline: ontwikkeling geaccepteerd en zeven V-items (V-fase), dan klaar voor T."""
    from tests.unit.scripts.test_def768_r8_proef import _v_invoer

    pad, items = _v_invoer(tmp_path, ("goed", "fout") * 3 + ("fout",))
    provider = _R8Provider(uitkomsten=_foutdragers(items))
    omg = _omgeving8(provider)
    _v10(omg, tmp_path, pad)
    assert [g["geaccepteerd"] for g in _v_gevallen(tmp_path)] == [True] * 7
    return omg, provider


class TestFasegrenzen:
    def test_twee_ontwikkelgevallen_boven_de_fasecap_geweigerd(self, tmp_path):
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="fasecap ontwikkeling"):
            _t10(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 2))
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []

    def test_ontwikkeling_alleen_op_de_r9_selectie(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="T-ontwikkelselectie"):
            _t10(_omgeving8(provider), tmp_path, pad, proef=_r10())
        assert provider.aanroepen == []

    def test_acht_v_items_boven_de_fasecap_geweigerd(self, tmp_path):
        from tests.unit.scripts.test_def768_r8_proef import _v_invoer

        pad, items = _v_invoer(tmp_path, ("goed", "fout") * 4)
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        with pytest.raises(gb.BudgetSchendingError, match="fasecap verificatie_alleen"):
            _v10(_omgeving8(provider), tmp_path, pad)
        assert provider.aanroepen == []

    def test_t_eind_boven_de_fasecap_geweigerd(self, tmp_path):
        omg, provider = _tot_en_met_v(tmp_path)
        voor = len(provider.aanroepen)
        freeze = tmp_path / "freeze-t.json"
        freeze.write_text(json.dumps(runner.freezevelden(omg, _r10(), "t")),
                          encoding="utf-8")  # fmt: skip
        with pytest.raises(gb.BudgetSchendingError, match="fasecap t_eind"):
            _t10(omg, tmp_path, _gevallenbestand(tmp_path, 21, "eind.json"),
                 fase="t_eind", nieuw=False, proef=_r10(), freeze=freeze)  # fmt: skip
        assert len(provider.aanroepen) == voor
        assert [
            r for r in _soort(tmp_path, "reservering") if r["fase"] == "t_eind"
        ] == []

    def test_t_eind_zonder_freeze_geweigerd(self, tmp_path):
        omg, provider = _tot_en_met_v(tmp_path)
        voor = len(provider.aanroepen)
        with pytest.raises(gb.BudgetSchendingError, match="freeze"):
            _t10(omg, tmp_path, _gevallenbestand(tmp_path, 20, "e.json"),
                 fase="t_eind", nieuw=False, proef=_r10())  # fmt: skip
        assert len(provider.aanroepen) == voor

    def test_niet_geaccepteerd_r720_stopt_r10_duurzaam(self, tmp_path):
        provider = _R8Provider(onderscheid="not_distinguished")
        pad = _gevallenbestand(tmp_path, 1)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _t10(_omgeving8(provider), tmp_path, pad)
        assert len(provider.aanroepen) == 2
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _t10(_omgeving8(provider), tmp_path, pad, nieuw=False)
        assert len(provider.aanroepen) == 2

    def test_ontwikkeling_een_geval_twee_stappen_met_keten_incl_r9(self, tmp_path):
        provider = _R8Provider()
        uitkomst = _t10(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 1))
        assert provider.stappen == ["beoordeling", "verificatie"]
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is True, geval["reden"]
        # Samenvatting: aanroepen_gestart telt gevallen; het grootboek telt stappen.
        assert uitkomst["aanroepen_gestart"] == 1
        assert uitkomst["grootboek_na"]["netwerk_gestart"] == 2
        voorganger = uitkomst["voorganger_grootboek"]
        assert voorganger["proef_id"] == gb.R9.proef_id
        assert voorganger["keten"][:2] == [
            {"proef_id": gb.R9.proef_id, "totaal": 2},
            {"proef_id": gb.R8.proef_id, "totaal": 1},
        ]
        assert voorganger["cumulatief_max"] == 427
        assert uitkomst["grootboek_na"]["kosten"]["plafond_nusd"] == 24_722_355_000


# --- V7: maker, bronbinding en offline verifier-only ---------------------------------------


class TestV7Maker:
    def test_maker_bronnen_en_doel_gepind(self):
        assert (mk10.R8_VINVOER, mk10.R8_VINVOER_SHA256) == (
            R8_VINVOER,
            R8_VINVOER_SHA256,
        )
        assert (mk10.R9_CALLRECORD, mk10.R9_CALLRECORD_SHA256) == (
            R9_RECORD,
            R9_RECORD_SHA256,
        )
        assert (mk10.R9_SELECTIE, mk10.R9_SELECTIE_SHA256) == (
            R9_SELECTIE,
            R9_SELECTIE_SHA256,
        )
        assert (mk10.INHOUDSCONTROLE, mk10.INHOUDSCONTROLE_SHA256) == (
            INHOUD9,
            INHOUD9_SHA256,
        )
        assert (mk10.STOPBESLUIT, mk10.STOPBESLUIT_SHA256) == (STOP9, STOP9_SHA256)
        assert mk10.DOEL == V7
        assert (mk10.N4_ID, mk10.N4_FOUTDRAGER) == ("V-N4", "claim:C5")

    @r9_bronnen_nodig
    @v7_nodig
    def test_vastgelegde_v7_reproduceerbaar_en_gepind(self, tmp_path):
        assert _sha(V7) == runner.R10_V_INVOER_SHA256
        doel = tmp_path / "v7.json"
        assert mk10.main(["--doel", str(doel)]) == 0
        # Sinds verify/4 (C3-herstel) verschilt alleen de prompthash per item;
        # de rest is de bevroren V7 (de herkomst noemt het huidige contract).
        nieuw, vast = json.loads(doel.read_text(encoding="utf-8")), _v7()
        assert nieuw["herkomst"]["contract"] == HUIDIG_CONTRACT
        assert vast["herkomst"]["contract"] == CONTRACT10
        for n, v in zip(nieuw["items"], vast["items"], strict=True):
            assert {k for k in n if n[k] != v[k]} == {"verificatieprompt_sha256"}

    @r9_bronnen_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        doel = tmp_path / "v7.json"
        assert mk10.main(["--doel", str(doel)]) == 0
        with pytest.raises(FileExistsError):
            mk10.main(["--doel", str(doel)])

    @r9_bronnen_nodig
    @pytest.mark.parametrize(
        ("bron", "melding"),
        [
            ("r8_vinvoer", "R8-V-invoer"),
            ("callrecord", "callrecord"),
            ("selectie", "ontwikkelselectie"),
            ("inhoudscontrole", "inhoudscontrole"),
            ("stopbesluit", "stopbesluit"),
        ],
    )
    def test_gewijzigde_bron_geweigerd(self, tmp_path, bron, melding):
        standaard = {
            "r8_vinvoer": R8_VINVOER,
            "callrecord": R9_RECORD,
            "selectie": R9_SELECTIE,
            "inhoudscontrole": INHOUD9,
            "stopbesluit": STOP9,
        }
        kopie = tmp_path / "bron"
        shutil.copyfile(standaard[bron], kopie)
        with kopie.open("a", encoding="utf-8") as f:
            f.write(" ")
        with pytest.raises(mk10.MakerfoutError, match=melding):
            mk10.maak_verificatie_invoer(**{bron: kopie})

    @r9_bronnen_nodig
    @pytest.mark.parametrize(
        "mutatie",
        [
            "concepttekst",  # het bewaarde concept wijkt af van de afleiding
            "ruw",  # het ruwe antwoord hoort niet bij de vastgelegde hash
            "c5_premissen",  # C5 is niet de vastgestelde gevolgtrekking
        ],
    )
    def test_n4_zonder_reparatie_of_herlabeling(self, mutatie):
        record = json.loads(R9_RECORD.read_text(encoding="utf-8"))
        (geval,) = json.loads(R9_SELECTIE.read_text(encoding="utf-8"))["gevallen"]
        record = copy.deepcopy(record)
        concept = record["beoordelingsdocument"]["concept"]
        c5 = next(c for c in concept["claims"] if c["id"] == "C5")
        if mutatie == "concepttekst":
            c5["text"] = c5["text"].split(";")[0] + "."
        elif mutatie == "ruw":
            record["ruw_antwoord"] += " "
        else:
            c5["premises"] = ["C1"]
        with pytest.raises(mk10.MakerfoutError):
            mk10.n4_item(record, geval, bron={})


@v7_nodig
@r9_bronnen_nodig
class TestV7Invoer:
    def test_zes_r8_items_alleen_de_prompthash_herberekend(self):
        oud = json.loads(R8_VINVOER.read_text(encoding="utf-8"))["items"]
        nieuw = _v7()["items"]
        assert [i["id"] for i in nieuw] == [i["id"] for i in oud] + ["V-N4"]
        for n, o in zip(nieuw[:6], oud, strict=True):
            assert list(n) == list(o)
            assert {k for k in n if n[k] != o[k]} == {"verificatieprompt_sha256"}
            zonder = {k: v for k, v in n.items() if k != "verificatieprompt_sha256"}
            assert pi.sha_json(zonder) == pi.sha_json(
                {k: v for k, v in o.items() if k != "verificatieprompt_sha256"}
            )

    def test_prompthash_hoort_bij_de_historische_verify_3(self):
        """V7 bindt verify/3; onder de huidige code (verify/4) wijkt elke hash af."""
        from services.validation.ess05_assessment_service import laad_ess05_norm

        norm = laad_ess05_norm()
        for item in _v7()["items"]:
            _, _, regels = mig.verificatiemateriaal(item["geval"], norm)
            system, user = mig._verificatieprompt(item["concept"], regels, norm)
            assert "<bewijsroutes>" in user
            assert (
                hashlib.sha256((system + "\n␞\n" + user).encode()).hexdigest()
                != item["verificatieprompt_sha256"]
            )

    def test_v_n4_is_het_ongewijzigde_r9_concept(self):
        record = json.loads(R9_RECORD.read_text(encoding="utf-8"))
        doc = record["beoordelingsdocument"]
        (geval,) = json.loads(R9_SELECTIE.read_text(encoding="utf-8"))["gevallen"]
        n4 = _v7()["items"][6]
        assert (n4["id"], n4["soort"], n4["foutdragende_items"]) == (
            "V-N4",
            "fout",
            ["claim:C5"],
        )
        assert n4["concept"] == doc["concept"]
        assert n4["concept_hash"] == doc["concept_derivation"]["concept_hash"]
        assert n4["concept_hash"] == R9_CONCEPT_HASH
        assert n4["geval"] == geval
        assert n4["geval_sha256"] == record["geval_sha256"] == pi.sha_json(geval)
        assert n4["materiaal_sha256"] == doc["concept_derivation"]["material"]
        c5 = next(c for c in n4["concept"]["claims"] if c["id"] == "C5")
        assert (c5["role"], c5["premises"]) == ("inference", ["C1", "C4"])
        assert "het gedeelde eindpunt op de oorspronkelijke laadplaats" in c5["text"]

    def test_v_n4_bron_en_herkomst_gebonden(self):
        record = json.loads(R9_RECORD.read_text(encoding="utf-8"))
        data = _v7()
        bron = data["items"][6]["bron"]
        assert bron["callrecord"] == str(R9_RECORD.relative_to(ROOT))
        assert bron["callrecord_sha256"] == R9_RECORD_SHA256
        assert (bron["sleutel"], bron["seq"]) == ("ontwikkeling|R720|1", 1)
        assert bron["ruw_antwoord"] == record["ruw_antwoord"]
        assert bron["ruw_antwoord_sha256"] == record["ruw_antwoord_sha256"]
        assert (bron["prompt_version"], bron["verification_prompt_version"]) == (
            "ess05-assess/15",
            "ess05-verify/2",
        )
        # Het historische verifieroordeel blijft zichtbaar: C5 werd vrijgegeven.
        assert bron["historisch_verifieroordeel"]["item"] == "claim:C5"
        assert bron["historisch_verifieroordeel"]["outcome"] == "supported"
        assert bron["ontwikkelselectie"]["sha256"] == R9_SELECTIE_SHA256
        assert bron["inhoudscontrole"] == {
            "pad": str(INHOUD9.relative_to(ROOT)),
            "sha256": INHOUD9_SHA256,
        }
        assert bron["inhoudelijke_stop"] == {
            "pad": str(STOP9.relative_to(ROOT)),
            "sha256": STOP9_SHA256,
        }
        herkomst = data["herkomst"]
        assert herkomst["r8_verificatie_invoer"]["sha256"] == R8_VINVOER_SHA256
        assert herkomst["contract"] == CONTRACT10
        assert data["schema"] == mig.INVOERSCHEMA

    def test_runner_weigert_v7_onder_de_huidige_code(self):
        with pytest.raises(pi.InvoerfoutError, match="verificatieprompt wijkt af"):
            runner.valideer_v_invoer(_v7(), _omgeving8(_R8Provider()))

    @pytest.mark.parametrize(
        ("fase", "pad"), [("verificatie_alleen", V7), ("ontwikkeling", R9_SELECTIE)]
    )
    def test_droog_geregistreerde_r10_weigert_op_het_contract(
        self, tmp_path, fase, pad
    ):
        with pytest.raises(gb.BudgetSchendingError, match="contract"):
            runner.main(["--proef", "R10", "--fase", fase, "--gevallen", str(pad),
                         "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    def test_droog_v7_onder_huidige_code_geweigerd(self, monkeypatch, tmp_path):
        monkeypatch.setitem(runner.PROEVEN, "R10", _r10())
        with pytest.raises(pi.InvoerfoutError, match="verificatieprompt wijkt af"):
            runner.main(["--proef", "R10", "--fase", "verificatie_alleen",
                         "--gevallen", str(V7), "--uitmap", str(tmp_path),
                         "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    def test_droog_r9_selectie_onder_r10(self, monkeypatch, tmp_path):
        # Materiaalcompatibiliteit onder de huidige code (kopie met huidig contract).
        monkeypatch.setitem(runner.PROEVEN, "R10", _r10())
        code = runner.main(["--proef", "R10", "--fase", "ontwikkeling", "--gevallen",
                            str(R9_SELECTIE), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        # geplande_calls telt gevallen (één geval = twee modelstappen).
        assert (droog["proef_id"], droog["geplande_calls"]) == (R10_ID, 1)
        assert [i["sleutel"] for i in droog["items"]] == ["ontwikkeling|R720|1"]

    def test_r8_v_invoer_geweigerd_voor_r10(self, monkeypatch, tmp_path):
        monkeypatch.setitem(runner.PROEVEN, "R10", _r10())
        with pytest.raises(gb.BudgetSchendingError, match="verifier-only-invoer"):
            runner.main(["--proef", "R10", "--fase", "verificatie_alleen", "--gevallen",
                         str(R8_VINVOER), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("*"))

    def test_v7_zeven_items_c5_afgewezen_geaccepteerd(self, tmp_path):
        pad, items = _v7_huidig(tmp_path)
        provider = _R8Provider(uitkomsten=_foutdragers(items))
        uitkomst = _v10(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"] * 7
        assert [g["geaccepteerd"] for g in _v_gevallen(tmp_path)] == [True] * 7
        assert uitkomst["aanroepen_gestart"] == 7
        assert uitkomst["grootboek_na"]["netwerk_gestart"] == 2 + 7

    def test_vrijgegeven_c5_stopt_de_proef(self, tmp_path):
        pad, items = _v7_huidig(tmp_path)
        provider = _R8Provider(uitkomsten=_foutdragers(items[:6]))
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v10(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"] * 7
        gevallen = _v_gevallen(tmp_path)
        assert [g["geaccepteerd"] for g in gevallen] == [True] * 6 + [False]
