"""DEF-768 R16 — mechanismeproef bewijsregels: registratie, invoer en fase, offline.

Opdracht Chris 28-09 ("ga hier mee verder",
logs/def768/bewijsregels-gebruikersopdracht-v1.json) en het startmandaat (max
12 appcalls / USD 4,50): drie gevallen A/B/C, elk één broninterpretatie plus ten
hoogste drie geïsoleerde controles; max 12 stappen, plafond USD 4,32,
cumulatief 391 + 12 = 403. Geen retry/reserve/cache. Een geldigheidsfout of
afgewezen controle stopt alleen het eigen geval; alleen een technische fout of
providerweigering stopt de proef.

De provider is een fake die per rol antwoordt: de interpretatie met vooraf
vastgelegde, juiste feiten (die van de domeintests, op het materiaal van het
geval), elke controle met een vaste uitkomst. Dit bewijst runnermechaniek en de
consistentie van de verwachtingen bij een juiste interpretatie, geen
modelkwaliteit. Geen netwerk, geen echte of betaalde call.
"""

from __future__ import annotations

import asyncio
import copy
import dataclasses
import json
import re
import sys
from pathlib import Path

import pytest

from services.ai.base_client import ChatResponse
from tests.unit.domain import test_def768_bewijsregels as dt
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _FakeProvider
from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek
from tests.unit.scripts.test_def768_r8_proef import _omgeving8
from tests.unit.scripts.test_def768_r9_proef import _r8_boek
from tests.unit.scripts.test_def768_r10_proef import (
    HUIDIG_CONTRACT,
    TOESTEMMING,
    TOESTEMMING_SHA256,
    _r9_boek,
    _sha,
)
from tests.unit.scripts.test_def768_r11_proef import _r10_boek
from tests.unit.scripts.test_def768_r12_microproef import _r11_boek
from tests.unit.scripts.test_def768_r13_herkenbare_gevallen import _r12_boek
from tests.unit.scripts.test_def768_r14_herproef import _r13_boek
from tests.unit.scripts.test_def768_r15_lokale_proef import _keten15, _r14_boek

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r16_bewijsregel_invoer as mk16
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

from domain.ess05 import lokale_controle as lc
from services.validation.ess05_bewijsregel_service import interpretatiesysteemprompt

R16_ID = "DEF-768-AI-20260928-R16"
R16_MAP = ROOT / "reports" / R16_ID
B16 = R16_MAP / "bewijsregel-invoer-v1.json"
B16_SHA256 = "11730986c6e5faf4afedb811426fae26856c234bb96315efb3bb9b3b30111cd2"
#: Het bewijsregelcontract waarop R16 (historisch, uitgevoerd 28-09) gepind blijft.
#: Sinds het R16-herstel (v4, prompt /2) weigert de runner R16 fail-closed.
R16_CONTRACT_V3 = {
    "bewijsregel_version": "ess05-bewijsregels/3",
    "interpretation_schema_version": "ess05-interpretatie/2",
    "render_version": "ess05-bewijsregels-render/2",
    "interpretation_prompt_version": "ess05-interpretatie-prompt/1",
    "interpretation_system_prompt_sha256": (
        "bb54d872c104766b0ef4095f1efacfe05c960846669098bbe7f2fff8ae1e4a8e"
    ),
}
LOGS = ROOT / "logs" / "def768"
OPDRACHT = LOGS / "bewijsregels-gebruikersopdracht-v1.json"
MANDAAT = LOGS / "bewijsregels-start-en-mandaat-v1.md"
BESLUIT16 = LOGS / "ronde16-bewijsregels-budgetbesluit-v2.json"
BESLUIT16_SHA256 = "0ed01e3616a54396f764ecf4a7747665825dd94a662f14e48d09ac798bcfa18f"
#: De echte R15-stand: vier betaalde stappen, USD 0,066325.
R15_KOSTEN_NUSD = 66_325_000
#: USD 25 − werkelijke R8–R15-kosten (2,836365).
KADERREST_NUSD = 22_163_635_000
#: De werkgrens van het startmandaat voor dit mechanisme (USD 4,50).
WERKGRENS_NUSD = 4_500_000_000
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
               "R12", "R13", "R14", "R15")  # fmt: skip
V = "validation"
W = "ess05_verification"
_PAKKETHASH = re.compile(r'<controlepakket packet_hash="([0-9a-f]{64})">')

besluit_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (BESLUIT16, OPDRACHT, MANDAAT, TOESTEMMING)),
    reason="git-ignored besluiten ontbreken",
)
r16_invoer_nodig = pytest.mark.skipif(
    not (B16.is_file() and mk16.R13_GEVALLEN.is_file()),
    reason="git-ignored R13/R16-invoer ontbreekt",
)

#: De modelvelden van H3 (R13), hier als vaste testinvoer.
BRONTEKST = (
    "Lokale testwerkinstructie van de Servicedesk ICT-middelen, alleen voor deze "
    "beoordelingstest. " + dt.BRON_A
)
H3 = {
    "id": "R16-A",
    "begrip": "uitleen",
    "tekst": dt.DEFINITIE,
    "toelichting": None,
    "categorie": None,
    "context": {"organisatorische_context": ["Servicedesk ICT-middelen"],
                "juridische_context": [], "wettelijke_basis": []},
    "bronnen": [{"provider": "documents", "doc_id": "testwerkinstructie-apparatuuruitgifte",
                 "title": "Lokale testwerkinstructie apparatuuruitgifte Servicedesk ICT-middelen",
                 "snippet": BRONTEKST}],
    "buren": [{"term": "verhuur", "definitie": dt.BUUR_A, "herkomst": "gebruiker",
               "bevestigd": True}],
}  # fmt: skip
BRON_ID = "source:doc:testwerkinstructie-apparatuuruitgifte"
VERWACHT = {
    "A": {"uitkomst": "review_required", "fout_soort": None, "buur_oordeel": "open",
          "aanroepen": 4},
    "B": {"uitkomst": "error", "fout_soort": "dekking_ontbreekt", "buur_oordeel": None,
          "aanroepen": 1},
    "C": {"uitkomst": "pass", "fout_soort": None, "buur_oordeel": "onderscheiden",
          "aanroepen": 4},
}  # fmt: skip


def _gevallen() -> dict[str, dict]:
    return {"A": H3, "B": H3, "C": mk16._geval_c(H3)}


def _items(namen=("A", "B", "C")) -> list[dict]:
    gevallen = _gevallen()
    return [
        mk16._item(
            naam,
            gevallen[naam],
            variant=f"variant {naam}",
            synthetisch=naam != "A",
            onvolledig=[BRON_ID] if naam == "B" else [],
            verwacht=VERWACHT[naam],
            herkomst={"bron": "test"},
        )
        for naam in namen
    ]


def _invoerdata(items) -> dict:
    return {
        "schema": mk16.INVOERSCHEMA,
        "contract": runner.bewijsregel_contractidentiteit(),
        "items": items,
    }


def _b_invoer(tmp_path: Path, items=None) -> tuple[Path, list[dict]]:
    items = _items() if items is None else items
    pad = tmp_path / "b-invoer.json"
    pad.write_text(json.dumps(_invoerdata(items)), encoding="utf-8")
    return pad, items


def _juiste_interpretatie(user: str) -> str:
    """De vooraf vastgelegde, juiste feiten van de domeintests op dit materiaal."""
    ruw = (
        dt._interpretatie_c()
        if "permanent ter beschikking" in user
        else dt._interpretatie_a()
    )
    buur = re.search(r"- (gebruiker:[0-9a-f]+): verhuur", user).group(1)
    tekst = json.dumps(ruw, ensure_ascii=False)
    tekst = tekst.replace(dt.BUURMATERIAAL, f"neighbour:{buur}")
    tekst = tekst.replace(json.dumps(dt.BUUR), json.dumps(buur))
    return tekst.replace(dt.BRON, BRON_ID)


class _BewijsProvider(_FakeProvider):
    """Interpretatie: juiste feiten; controle: vaste uitkomst per volgnummer."""

    def __init__(self, *, controle=lambda n: "supported", stop=None, fout_bij=None):
        super().__init__()
        self.controle = controle
        self.stop = stop
        self.fout_bij = fout_bij
        self.berichten: list[tuple[str, str]] = []

    async def chat_completion(self, messages, model, **kwargs):
        system = next(m.content for m in messages if m.role == "system")
        user = "\n".join(m.content for m in messages if m.role != "system")
        self.berichten.append((system, user))
        self.aanroepen.append({"model": model, **kwargs})
        if self.fout_bij is not None and len(self.berichten) == self.fout_bij:
            raise ConnectionError("netwerk weg")
        if system == interpretatiesysteemprompt():
            tekst = _juiste_interpretatie(user)
        else:
            tekst = json.dumps({
                "schema_version": lc.LOKAAL_VERIFICATIESCHEMA,
                "packet_hash": _PAKKETHASH.search(user).group(1),
                "checks": [{"item": lc.CONTROLE_ITEM,
                            "outcome": self.controle(len(self.berichten)),
                            "finding": "Synthetische bevinding."}],
            })  # fmt: skip
        return ChatResponse(
            text=tekst, tokens_used=10, model=model, stop_reason=self.stop
        )


def _r15_boek(root: Path, *, kosten: int = R15_KOSTEN_NUSD):
    """Een R15-grootboek zoals het echte: vier lokale controles, elk één stap."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R15)
    binding = {"dataset_sha256": "a" * 64, "herhaal_ids": [], "code_sha256": "b" * 64,
               "config_sha256": "c" * 64, "freeze_sha256": "d" * 64}  # fmt: skip
    for naam in ("L-N1", "L-P1", "L-N2", "L-P2"):
        poging = f"lokale_verificatie|{naam}|1"
        res = boek.reserveer("lokale_verificatie", f"{poging}/verificatie",
                             invoer_sha256="a" * 64, poging=poging, stap="verificatie",
                             vorige_stap=None, task_type=W, binding=binding)  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                   kosten_werkelijk_nusd=kosten // 4)  # fmt: skip
        boek.registreer_geval("lokale_verificatie", poging, geaccepteerd=False,
                              reden="r15", technisch_afgerond=True)  # fmt: skip
    return boek


def _keten16(tmp_path: Path):
    r15 = runner.Proefopslag(tmp_path / "r15")
    _r15_boek(r15.root)
    return (r15, *_keten15(tmp_path))


def _bestaande_keten16(tmp_path: Path):
    namen = ("r15", "r14", "r13", "r12", "r11", "r10", "r9", "r8", "r7", "r6", "r5",
             "r4", "r3", "r2", "r1")  # fmt: skip
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag16(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r16")


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag16(tmp_path).grootboek
    if not pad.exists():
        return []
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


def _freeze(omg, tmp_path: Path, proef) -> Path:
    pad = tmp_path / "freeze-b.json"
    if not pad.exists():
        pad.write_text(
            json.dumps(runner.freezevelden(omg, proef, "b")), encoding="utf-8"
        )
    return pad


def _huidig16(**kw):
    """R16-mechaniek op het huidige bewijsregelcontract (R16 zelf is op v3 gepind)."""
    return dataclasses.replace(
        runner.PROEVEN["R16"],
        bewijsregel_contract=runner.bewijsregel_contractidentiteit(),
        **kw,
    )


def _b16(omg, tmp_path, pad, *, nieuw=True, **kw):
    proef = _huidig16(b_invoer_sha256=_sha(pad))
    return asyncio.run(
        runner.voer_b_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag16(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef),
            voorganger_opslag=(
                _keten16(tmp_path) if nieuw else _bestaande_keten16(tmp_path)
            ),
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _records(tmp_path: Path) -> list[dict]:
    (callmap,) = (tmp_path / "uit").glob("bewijsregels-*/calls")
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(callmap.glob("*.json"))
    ]


# --- identiteit en kosten -------------------------------------------------------------------


class TestIdentiteit:
    def test_drie_gevallen_max_vier_stappen_cumulatief_403(self):
        r16 = gb.R16
        assert r16.proef_id == R16_ID
        assert dict(r16.fasecaps) == {"bewijsregels": 12}
        assert (r16.reserve_max, r16.totaal_max) == (0, 12)
        assert r16.voorganger is gb.R15
        assert r16.cumulatief_max == 403 == 391 + 12
        assert r16.modelstappen_per_geval == 4
        assert dict(r16.fasestappen) == {"bewijsregels": (V, W, W, W)}
        assert dict(r16.fasevolgorde) == {"bewijsregels": ()}
        assert (r16.stop_bij_eerste_fout, r16.stop_alleen_technisch) == (True, True)
        assert r16.vroege_stop_toegestaan is True
        assert [(g.naam, set(g.fases), g.herhaal_aantal) for g in r16.eindgroepen] == [
            ("b", {"bewijsregels"}, 0)
        ]
        assert [t for t, _ in runner._B_STAPPEN] == list(
            r16.fasestappen["bewijsregels"]
        )

    def test_zelfde_model_en_grenzen_plafond_4_32_onder_4_50(self):
        kb16, kb8 = gb.R16.kostenbewaking, gb.R8.kostenbewaking
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb16, veld) == getattr(kb8, veld), veld
        assert dict(kb16.bytegrens) == dict(kb8.bytegrens)
        per_geval = kb16.stapgrens_nusd(V) + 3 * kb16.stapgrens_nusd(W)
        assert per_geval == 315_000_000 + 3 * 375_000_000
        assert kb16.plafond_nusd == gb.begroting_nusd(gb.R16) == 3 * per_geval
        assert kb16.plafond_nusd == 4_320_000_000 <= WERKGRENS_NUSD
        assert kb16.plafond_nusd <= KADERREST_NUSD
        assert gb.R16.kostenkader_nusd == 25_000_000_000

    def test_oudere_rondes_ongewijzigd(self):
        assert (gb.R15.totaal_max, gb.R15.cumulatief_max) == (4, 391)
        assert gb.R15.kostenbewaking.plafond_nusd == 1_500_000_000
        for naam in OUDE_RONDES:
            assert runner.PROEVEN[naam].identiteit.vroege_stop_toegestaan is False, naam
            assert runner.PROEVEN[naam].bewijsregel_contract is None, naam

    def test_cumulatief_403_past_404_niet(self, tmp_path):
        keten = [
            _r15_boek(tmp_path / "r15"),
            _r14_boek(tmp_path / "r14"),
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
        assert sum(b.samenvatting()["totaal"] for b in keten) == 391
        boek = gb.Grootboek.nieuw(_opslag16(tmp_path).grootboek, gb.R16)
        gb.controleer_cumulatief(boek, keten, 12)
        with pytest.raises(gb.BudgetSchendingError, match="403"):
            gb.controleer_cumulatief(boek, keten, 13)

    @pytest.mark.skipif(
        not all(runner.PROEVEN[n].opslag.grootboek.is_file() for n in OUDE_RONDES),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_391_calls_usd_2_836365_en_r15_kop(self, tmp_path):
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed(OUDE_RONDES)
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 391
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:8])
        assert lopend == 2_836_365_000 == 25_000_000_000 - KADERREST_NUSD
        assert keten[0].kostenstand()["lopend_nusd"] == R15_KOSTEN_NUSD
        assert keten[0].samenvatting()["onafgesloten"] == 0
        assert keten[0].samenvatting()["kop_sha256"] == runner.R15_KOP_SHA256
        runner._controleer_voorgangerkop(runner.PROEVEN["R16"], tuple(keten))
        boek = gb.Grootboek.nieuw(_opslag16(tmp_path).grootboek, gb.R16)
        gb.controleer_cumulatief(boek, keten, 12)
        with pytest.raises(gb.BudgetSchendingError, match="403"):
            gb.controleer_cumulatief(boek, keten, 13)


class TestVroegeStop:
    """Alleen R16 accepteert een geval met minder stappen dan de vaste reeks."""

    BINDING = {"dataset_sha256": "a" * 64, "herhaal_ids": [], "code_sha256": "b" * 64,
               "config_sha256": "c" * 64, "freeze_sha256": "d" * 64}  # fmt: skip

    def _eerste_stap(self, boek, fase, taak):
        poging = f"{fase}|X|1"
        res = boek.reserveer(fase, f"{poging}/s1", invoer_sha256="a" * 64, poging=poging,
                             stap="s1", vorige_stap=None, task_type=taak,
                             binding=self.BINDING)  # fmt: skip
        boek.sluit(
            res["seq"], "voltooid", netwerk_gestart=True, kosten_werkelijk_nusd=1
        )
        return poging

    def test_r16_accepteert_een_van_vier(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "g.jsonl", gb.R16)
        poging = self._eerste_stap(boek, "bewijsregels", V)
        boek.registreer_geval("bewijsregels", poging, geaccepteerd=True, reden="vroeg",
                              technisch_afgerond=True)  # fmt: skip

    def test_r13_weigert_een_van_twee(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "g.jsonl", gb.R13)
        poging = self._eerste_stap(boek, "ontwikkeling", V)
        with pytest.raises(gb.BudgetSchendingError, match="geaccepteerd met 1 van 2"):
            boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="x",
                                  technisch_afgerond=True)  # fmt: skip


# --- registratie en besluit -----------------------------------------------------------------


class TestRegistratie:
    def test_r16_geregistreerd_met_invoer_besluit_en_drie_contracten(self):
        proef = runner.PROEVEN["R16"]
        assert proef.identiteit is gb.R16
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R16_MAP
        assert proef.b_invoer_sha256 == B16_SHA256
        assert (proef.t_ontwikkelinvoer_sha256, proef.v_invoer_sha256,
                proef.l_invoer_sha256) == (None, None, None)  # fmt: skip
        assert proef.budgetbesluit == BESLUIT16
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        assert dict(proef.contract) == HUIDIG_CONTRACT
        assert dict(proef.lokaal_contract) == runner.lokale_contractidentiteit()
        # Historisch gepind op v3; de huidige code (v4) draagt dat contract niet meer.
        assert dict(proef.bewijsregel_contract) == R16_CONTRACT_V3
        assert runner.bewijsregel_contractidentiteit() != R16_CONTRACT_V3
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST_NUSD
        assert proef.voorganger_kop_sha256 == runner.R15_KOP_SHA256
        runner._controleer_contract(_omgeving8(_BewijsProvider()), proef)
        runner._controleer_lokaal_contract(proef)
        with pytest.raises(gb.BudgetSchendingError, match="geen call gestart"):
            runner._controleer_bewijsregel_contract(proef)

    def test_r15_registratie_ongewijzigd(self):
        proef = runner.PROEVEN["R15"]
        assert proef.b_invoer_sha256 is None
        assert proef.voorganger_kop_sha256 == runner.R14_KOP_SHA256
        assert proef.l_invoer_sha256 == runner.R15_L_INVOER_SHA256

    @pytest.mark.parametrize("veld", sorted(runner.R16_BEWIJSREGEL_CONTRACT))
    def test_afwijkend_bewijsregelcontract_geweigerd(self, veld):
        vast = {**runner.PROEVEN["R16"].bewijsregel_contract, veld: "anders"}
        proef = dataclasses.replace(runner.PROEVEN["R16"], bewijsregel_contract=vast)
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            runner._controleer_bewijsregel_contract(proef)

    def test_voorgangerkop_exact(self, tmp_path):
        boek = _r15_boek(tmp_path / "r15")
        kop = boek.samenvatting()["kop_sha256"]
        proef = dataclasses.replace(runner.PROEVEN["R16"], voorganger_kop_sha256=kop)
        runner._controleer_voorgangerkop(proef, (boek,))
        ander = _r15_boek(tmp_path / "ander", kosten=R15_KOSTEN_NUSD + 4)
        with pytest.raises(gb.BudgetSchendingError, match="voorgangergrootboek"):
            runner._controleer_voorgangerkop(proef, (ander,))

    def test_freezegroep_b_bindt_product_lokaal_en_bewijsregelcontract(self):
        omg = _omgeving8(_BewijsProvider())
        velden = runner.freezevelden(omg, runner.PROEVEN["R16"], "b")
        assert (velden["groep"], velden["proef_id"]) == ("b", R16_ID)
        for sleutel, waarde in {
            **HUIDIG_CONTRACT,
            **runner.lokale_contractidentiteit(),
            **runner.bewijsregel_contractidentiteit(),
        }.items():
            assert velden[sleutel] == waarde, sleutel

    def test_codemanifest_bevat_regels_en_dienst(self):
        manifest = runner.codemanifest()
        assert "src/domain/ess05/bewijsregels.py" in manifest
        assert "src/services/validation/ess05_bewijsregel_service.py" in manifest

    @besluit_nodig
    def test_besluit_gebonden_aan_opdracht_mandaat_en_past_op_r16(self):
        assert _sha(BESLUIT16) == BESLUIT16_SHA256 == runner.R16_BUDGETBESLUIT_SHA256
        data = json.loads(BESLUIT16.read_text(encoding="utf-8"))
        bron = json.loads(OPDRACHT.read_text(encoding="utf-8"))
        assert data["bron_sha256"] == _sha(OPDRACHT)
        assert data["startmandaat_sha256"] == _sha(MANDAAT)
        assert (
            data["gebruikersantwoord"]
            == bron["gebruikersantwoord"]
            == "ga hier mee verder"
        )
        mandaat = MANDAAT.read_text(encoding="utf-8")
        assert "cumulatief391" in mandaat and "resterend22.163635" in mandaat
        assert (data["extra_modelaanroepen_max"], data["cumulatief_max"],
                data["historisch_verbruik"], data["reserve"]) == (12, 403, 391, 0)  # fmt: skip
        assert runner._nusd(data["kostenbudget_usd"]) == 4_320_000_000
        assert runner._nusd(data["kaderrest_usd"]) == KADERREST_NUSD
        assert data["r15_grootboekkop_sha256"] == runner.R15_KOP_SHA256
        assert data["verwacht_modelstappen"] == sum(
            v["aanroepen"] for v in VERWACHT.values()
        )
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R16"]) == (
            runner.R16_BUDGETBESLUIT_SHA256
        )

    @besluit_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 13},
            {"cumulatief_max": 404},
            {"historisch_verbruik": 390},
            {"reserve": 1},
            {"kostenbudget_usd": "4.500000"},
            {"kaderrest_usd": "22.163636"},
            {"r15_verbruik_usd": "0.066326"},
            {"r15_verbruik_usd": None},
            {"r15_verbruik_modelstappen": 5},
            {"fasen_modelstappen_max": {"bewijsregels": 13}},
        ],
    )
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        data = json.loads(BESLUIT16.read_text(encoding="utf-8"))
        for sleutel, waarde in anders.items():
            if waarde is None:
                data.pop(sleutel)
            else:
                data[sleutel] = waarde
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        proef = dataclasses.replace(
            runner.PROEVEN["R16"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)


# --- bewijsregelfase: stappen, stopregel en records (offline) -------------------------------


class TestBewijsregelFase:
    def test_juiste_interpretatie_geeft_elke_verwachting_in_negen_stappen(
        self, tmp_path
    ):
        pad, items = _b_invoer(tmp_path)
        provider = _BewijsProvider()
        samenvatting = _b16(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 9 == samenvatting["modelstappen_gestart"]
        systemen = [s == interpretatiesysteemprompt() for s, _ in provider.berichten]
        assert systemen == [True, False, False, False, True, True, False, False, False]
        reserveringen = _soort(tmp_path, "reservering")
        assert [r["stap"] for r in reserveringen] == [
            "interpretatie", "controle_1", "controle_2", "controle_3", "interpretatie",
            "interpretatie", "controle_1", "controle_2", "controle_3",
        ]  # fmt: skip
        assert [r["task_type"] for r in reserveringen] == [V, W, W, W, V, V, W, W, W]
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"], len(g["seqs"]))
                for g in gevallen] == [(True, True, 4), (True, True, 1), (True, True, 4)]  # fmt: skip
        records = _records(tmp_path)
        assert [r["gekregen"] for r in records] == [VERWACHT[n] for n in "ABC"]
        eenheden = ["kern", "doel", f"buur:{items[0]['buren'][0][0]}"]
        assert [[c["eenheid"] for c in r["controles"]] for r in records] == [
            eenheden, [], eenheden,
        ]  # fmt: skip
        eerste = records[0]
        assert eerste["schema"] == "def768-ess05-bewijsregelcall/1"
        assert eerste["prompt"]["komt_overeen_met_dienst"] is True
        assert eerste["contract"] == runner.bewijsregel_contractidentiteit()
        assert "Bereik:" in eerste["tekst"]
        assert records[1]["regelfout"]["soort"] == "dekking_ontbreekt"
        assert samenvatting["grootboek_na"]["gestopt"] is False
        assert {c["max_tokens"] for c in provider.aanroepen} == {3000}
        assert len({c["model"] for c in provider.aanroepen}) == 1
        # Verwachtingen en ID's staan nooit in een modelpayload.
        for _, user in provider.berichten:
            assert "review_required" not in user and "dekking_ontbreekt" not in user

    def test_afgewezen_controle_stopt_alleen_het_eigen_geval(self, tmp_path):
        pad, _ = _b_invoer(tmp_path)
        provider = _BewijsProvider(
            controle=lambda n: "unsupported" if n == 2 else "supported"
        )
        samenvatting = _b16(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 2 + 1 + 4
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"], len(g["seqs"]))
                for g in gevallen] == [(False, True, 2), (True, True, 1), (True, True, 4)]  # fmt: skip
        assert "semantische_controle_mislukt" in gevallen[0]["reden"]
        assert samenvatting["grootboek_na"]["gestopt"] is False

    def test_technische_fout_stopt_duurzaam_zonder_retry(self, tmp_path):
        pad, _ = _b_invoer(tmp_path)
        provider = _BewijsProvider(fout_bij=2)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _b16(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 2  # geen retry, geen volgend geval
        (geval,) = _soort(tmp_path, "geval")
        assert (geval["geaccepteerd"], geval["technisch_afgerond"]) == (False, False)
        tweede = _BewijsProvider()
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _b16(_omgeving8(tweede), tmp_path, pad, nieuw=False)
        assert tweede.berichten == []

    def test_providerweigering_stopt(self, tmp_path):
        pad, _ = _b_invoer(tmp_path)
        provider = _BewijsProvider(stop="refusal")
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _b16(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 1
        (geval,) = _soort(tmp_path, "geval")
        assert (geval["geaccepteerd"], geval["technisch_afgerond"]) == (False, False)
        assert "refusal" in geval["reden"]

    def test_vierde_geval_boven_de_fasecap_geweigerd(self, tmp_path):
        items = _items(("A", "B", "C", "A"))
        items[3] = {**items[3], "id": "D"}
        pad, _ = _b_invoer(tmp_path, items)
        provider = _BewijsProvider()
        with pytest.raises(
            gb.BudgetSchendingError,
            match="plan vraagt 16 calls; fasecap bewijsregels laat nog 12",
        ):
            _b16(_omgeving8(provider), tmp_path, pad)
        assert provider.berichten == []

    def test_technische_herhaling_geweigerd(self, tmp_path):
        pad, _ = _b_invoer(tmp_path)
        provider = _BewijsProvider()
        with pytest.raises(gb.BudgetSchendingError, match="technische herhaling"):
            _b16(_omgeving8(provider), tmp_path, pad,
                 technische_herhalingen=("bewijsregels|A|1",))  # fmt: skip
        assert provider.berichten == []

    def test_andere_invoer_dan_de_gepinde_geweigerd(self, tmp_path):
        pad, _ = _b_invoer(tmp_path)
        with pytest.raises(
            gb.BudgetSchendingError, match="vastgelegde bewijsregelinvoer"
        ):
            asyncio.run(
                runner.voer_b_fase(
                    _omgeving8(_BewijsProvider()),
                    gevallenpad=pad,
                    uitmap=tmp_path / "uit",
                    opslag=_opslag16(tmp_path),
                    proef=_huidig16(),
                    voorganger_opslag=_keten16(tmp_path),
                    nieuw_grootboek=True,
                )
            )
        assert not _opslag16(tmp_path).grootboek.exists()


# --- validatie van de bewijsregelinvoer -----------------------------------------------------


class TestBInvoer:
    def test_geldige_invoer_opnieuw_gebonden(self):
        gebonden = runner.valideer_b_invoer(
            _invoerdata(_items()), _omgeving8(_BewijsProvider())
        )
        assert [bi.sleutel for bi in gebonden] == [f"bewijsregels|{n}|1" for n in "ABC"]
        assert [sorted(bi.invoer.onvolledig) for bi in gebonden] == [[], [BRON_ID], []]

    @pytest.mark.parametrize(
        ("wijzig", "melding"),
        [
            (lambda i: i["geval"].update(tekst="iets anders"), "geval_sha256"),
            (lambda i: i["materiaal_sha256"].update(definition="0" * 64), "materiaal"),
            (lambda i: i.update(prompt_sha256="0" * 64), "interpretatieprompt"),
            (lambda i: i.update(buren=[]), "precies één buur"),
            (lambda i: i.update(onvolledig=["definition"]), "onvolledig"),
            (lambda i: i.update(onvolledig=["source:doc:onbekend"]), "onvolledig"),
            (lambda i: i["verwacht"].update(uitkomst="open"), "verwachting"),
            (lambda i: i["verwacht"].update(fout_soort="x"), "verwachting"),
            (lambda i: i["verwacht"].update(buur_oordeel=None), "verwachting"),
            (lambda i: i["verwacht"].update(aanroepen=5), "verwachting"),
            (lambda i: i["verwacht"].update(extra=1), "exact de velden"),
        ],
    )  # fmt: skip
    def test_gemanipuleerd_item_geweigerd(self, wijzig, melding):
        items = copy.deepcopy(_items())
        wijzig(items[0])
        with pytest.raises(pi.InvoerfoutError, match=melding):
            runner.valideer_b_invoer(_invoerdata(items), _omgeving8(_BewijsProvider()))

    def test_verwisselde_verwachting_blijft_geldig_maar_niet_geaccepteerd(
        self, tmp_path
    ):
        # De runner valideert vorm, niet inhoud: de oracle is de inhoudsreview.
        items = _items()
        items[0]["verwacht"], items[2]["verwacht"] = (
            items[2]["verwacht"],
            items[0]["verwacht"],
        )
        pad, _ = _b_invoer(tmp_path, items)
        _b16(_omgeving8(_BewijsProvider()), tmp_path, pad)
        gevallen = _soort(tmp_path, "geval")
        assert [g["geaccepteerd"] for g in gevallen] == [False, True, False]

    def test_ander_contract_geweigerd(self):
        data = _invoerdata(_items())
        data["contract"] = {
            **data["contract"],
            "bewijsregel_version": "ess05-bewijsregels/2",
        }
        with pytest.raises(pi.InvoerfoutError, match="ander bewijsregelcontract"):
            runner.valideer_b_invoer(data, _omgeving8(_BewijsProvider()))

    def test_dubbele_ids_geweigerd(self):
        items = _items()
        items[1] = {**items[1], "id": "A"}
        with pytest.raises(pi.InvoerfoutError, match="dubbele"):
            runner.valideer_b_invoer(_invoerdata(items), _omgeving8(_BewijsProvider()))

    @pytest.mark.parametrize(
        "data", [None, {}, {"schema": "iets/1", "items": [{}]},
                 {"schema": mk16.INVOERSCHEMA, "items": []}],
    )  # fmt: skip
    def test_verkeerd_schema_geweigerd(self, data):
        with pytest.raises(pi.InvoerfoutError, match="schema"):
            runner.valideer_b_invoer(data, _omgeving8(_BewijsProvider()))


# --- de echte, gepinde R16-invoer -----------------------------------------------------------


@r16_invoer_nodig
class TestEchteInvoer:
    def test_gepind_deterministisch_en_gelabeld(self):
        assert _sha(B16) == B16_SHA256 == runner.R16_B_INVOER_SHA256
        data = json.loads(B16.read_text(encoding="utf-8"))
        assert data["contract"] == R16_CONTRACT_V3
        # De maker op de huidige code wijkt alleen af in contract en prompthash.
        nu = mk16.maak_bewijsregel_invoer()
        assert nu["contract"] == runner.bewijsregel_contractidentiteit()
        zonder = [{k: v for k, v in i.items() if k != "prompt_sha256"}
                  for i in data["items"]]  # fmt: skip
        assert [{k: v for k, v in i.items() if k != "prompt_sha256"}
                for i in nu["items"]] == zonder  # fmt: skip
        assert [(i["id"], i["synthetisch"], i["verwacht"]) for i in data["items"]] == [
            ("A", False, VERWACHT["A"]),
            ("B", True, VERWACHT["B"]),
            ("C", True, VERWACHT["C"]),
        ]
        assert [i["label"] == mk16.LABEL for i in data["items"]] == [False, True, True]
        # A en B delen exact het geval; alleen de app-markering verschilt.
        a, b, c = data["items"]
        assert (
            a["geval"] == b["geval"] and a["materiaal_sha256"] == b["materiaal_sha256"]
        )
        assert (a["onvolledig"], b["onvolledig"]) == ([], [BRON_ID])
        # A is H3 ongewijzigd (modelvelden); C wijkt alleen in bronzin en buurdefinitie af.
        assert {k: a["geval"][k] for k in mk16._MODELVELDEN} == {
            k: v for k, v in H3.items() if k != "id"
        }
        assert c["geval"] == mk16._geval_c(a["geval"])

    def test_historische_invoer_geweigerd_onder_het_huidige_contract(self, tmp_path):
        data = json.loads(B16.read_text(encoding="utf-8"))
        with pytest.raises(pi.InvoerfoutError, match="ander bewijsregelcontract"):
            runner.valideer_b_invoer(data, _omgeving8(_BewijsProvider()))
        pad = tmp_path / "b16.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        provider = _BewijsProvider()
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            asyncio.run(
                runner.voer_b_fase(
                    _omgeving8(provider),
                    gevallenpad=pad,
                    uitmap=tmp_path / "uit",
                    opslag=_opslag16(tmp_path),
                    proef=runner.PROEVEN["R16"],
                    voorganger_opslag=_keten16(tmp_path),
                    nieuw_grootboek=True,
                )
            )
        assert provider.berichten == []
        assert not _opslag16(tmp_path).grootboek.exists()

    def test_droog_op_de_geregistreerde_r16_weigert(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="bewijsregelcontract"):
            runner.main(["--proef", "R16", "--fase", "bewijsregels",
                         "--gevallen", str(B16), "--uitmap", str(tmp_path),
                         "--droog"])  # fmt: skip
        assert not list(tmp_path.rglob("droogrun.json"))
        assert not list(tmp_path.rglob("*.jsonl"))
