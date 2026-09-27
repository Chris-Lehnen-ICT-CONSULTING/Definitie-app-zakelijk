"""DEF-768 R15 — fase A bewijsisolatie: registratie en lokale fase, offline.

Opdracht Chris 27-09 ("Akkoord om het zo op te pakken",
logs/def768/isolatie-gebruikersopdracht-v1.json): vier lokale controles (twee
negatief, twee positief), elk één afzonderlijk verzoek; max 4 calls, USD 1,50,
cumulatief 387 + 4 = 391 binnen 430/USD 25. Geen retry/reserve/cache. Alle vier
lopen ongeacht de semantische uitkomst; alleen een technische fout of een
providerweigering stopt.

Providergrens is een fake die alleen het pakket ziet dat de lokale prompt
draagt; bewijst runnermechaniek, geen modelkwaliteit. Geen netwerk, geen echte
of betaalde call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import html
import json
import re
import sys
from pathlib import Path

import pytest

from services.ai.base_client import ChatResponse
from tests.unit.scripts.test_def768_ess05_proefrunner import (
    ROOT,
    _FakeProvider,
    _gevallenbestand,
)
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
from tests.unit.scripts.test_def768_r14_herproef import _keten14, _r13_boek

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_r15_lokale_invoer as mk15
import migreer_r7_naar_v2 as mig
import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

from domain.ess05 import lokale_controle as lc

R15_ID = "DEF-768-AI-20260928-R15"
R15_MAP = ROOT / "reports" / R15_ID
L15 = R15_MAP / "lokale-invoer-v1.json"
L15_SHA256 = "823cd361884823f777fa4cb1d6343aefc164de08884437649887720460fdc14c"
LOGS = ROOT / "logs" / "def768"
OPDRACHT = LOGS / "isolatie-gebruikersopdracht-v1.json"
BESLUIT15 = LOGS / "ronde15-lokale-verificatie-budgetbesluit-v1.json"
#: De echte R14-stand: elf betaalde stappen, USD 1,100450.
R14_KOSTEN_NUSD = 1_100_450_000
#: USD 25 − werkelijke R8–R14-kosten (2,770040).
KADERREST_NUSD = 22_229_960_000
OUDE_RONDES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11",
               "R12", "R13", "R14")  # fmt: skip
V = "validation"
W = "ess05_verification"
_PAKKETHASH = re.compile(r'<controlepakket packet_hash="([0-9a-f]{64})">')
_PAKKETBLOK = re.compile(
    r'<controlepakket packet_hash="[0-9a-f]{64}">\n(.*?)\n</controlepakket>', re.S
)

besluit_nodig = pytest.mark.skipif(
    not all(p.is_file() for p in (BESLUIT15, OPDRACHT, TOESTEMMING)),
    reason="git-ignored besluiten ontbreken",
)
r15_invoer_nodig = pytest.mark.skipif(
    not (L15.is_file() and mk15.V14.is_file()),
    reason="git-ignored R14/R15-invoer ontbreekt",
)


def _r14_boek(root: Path, *, kosten: int = R14_KOSTEN_NUSD):
    """Een R14-grootboek zoals het echte: 11 stappen (H4 alleen beoordeling)."""
    boek = gb.Grootboek.nieuw(root / "callgrootboek.jsonl", gb.R14)
    per_stap = kosten // 11
    binding = {"dataset_sha256": "a" * 64, "herhaal_ids": [], "code_sha256": "b" * 64,
               "config_sha256": "c" * 64, "freeze_sha256": "d" * 64}  # fmt: skip
    for i in range(1, 6):
        poging, vorige = f"ontwikkeling|H{i}|1", None
        stappen = (
            (("beoordeling", V),)
            if i == 4
            else (("beoordeling", V), ("verificatie", W))
        )
        for stap, taak in stappen:
            res = boek.reserveer("ontwikkeling", f"{poging}/{stap}", invoer_sha256="a" * 64,
                                 poging=poging, stap=stap, vorige_stap=vorige,
                                 task_type=taak, binding=binding)  # fmt: skip
            boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                       kosten_werkelijk_nusd=per_stap)  # fmt: skip
            vorige = stap
        boek.registreer_geval("ontwikkeling", poging, geaccepteerd=i not in (3, 4),
                              reden="r14", technisch_afgerond=True)  # fmt: skip
    for naam in ("V-N6", "V-N7"):
        poging = f"verificatie_alleen|{naam}|1"
        res = boek.reserveer("verificatie_alleen", f"{poging}/verificatie",
                             invoer_sha256="e" * 64, poging=poging, stap="verificatie",
                             vorige_stap=None, task_type=W,
                             binding={**binding, "dataset_sha256": "e" * 64})  # fmt: skip
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True,
                   kosten_werkelijk_nusd=per_stap)  # fmt: skip
        boek.registreer_geval("verificatie_alleen", poging, geaccepteerd=False,
                              reden="r14", technisch_afgerond=True)  # fmt: skip
    return boek


def _keten15(tmp_path: Path):
    """(R14-, R13- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r14 = runner.Proefopslag(tmp_path / "r14")
    _r14_boek(r14.root)
    return (r14, *_keten14(tmp_path))


def _bestaande_keten15(tmp_path: Path):
    namen = ("r14", "r13", "r12", "r11", "r10", "r9", "r8", "r7", "r6", "r5", "r4",
             "r3", "r2", "r1")  # fmt: skip
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _opslag15(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r15")


def _soort(tmp_path: Path, soort: str) -> list[dict]:
    pad = _opslag15(tmp_path).grootboek
    if not pad.exists():
        return []
    regels = [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]
    return [r for r in regels if r["soort"] == soort]


# --- synthetische lokale invoer en fake provider -------------------------------------------


def _l_invoer(tmp_path: Path, n: int = 4) -> tuple[Path, list[dict]]:
    """Synthetische lokale invoer via dezelfde itembouw als de R15-maker.

    Afwisselend negatief (fragment of te smalle premissen) en positief; elk item
    een eigen pakket op het materiaal van een synthetisch geval.
    """
    from services.validation.ess05_assessment_service import laad_ess05_norm

    norm = laad_ess05_norm()
    (geval,) = json.loads(_gevallenbestand(tmp_path, 1, "lg.json").read_text())[
        "gevallen"
    ]
    materiaal, buren, _ = mig.verificatiemateriaal(geval, norm)
    termen = {b.id: b.term for b in buren}
    bron = {
        "geval": geval,
        "geval_sha256": pi.sha_json(geval),
        "materiaal_sha256": {m: _sha_tekst(t) for m, t in materiaal.items()},
    }
    kern = materiaal["definition"]
    items = []
    for i in range(n):
        soort = "negatief" if i % 2 == 0 else "positief"
        uitspraak = f"Synthetische uitspraak {i} over de kern."
        if i % 4 < 2:
            eind = kern.index(" met") if soort == "negatief" else len(kern)
            pakket = lc.bouw_materiaalpakket(
                uitspraak,
                [lc.Citaatverwijzing("definition", 0, eind)],
                materiaal,
                buurtermen=termen,
            )
        else:
            premissen = ["Synthetische premisse A."]
            if soort == "positief":
                premissen.append("Synthetische premisse B.")
            pakket = lc.bouw_gevolgtrekkingspakket(uitspraak, premissen)
        items.append(mk15._item(f"L-{i}", soort, bron, pakket, {"bron": "synthetisch"}))
    pad = tmp_path / "l-invoer.json"
    pad.write_text(
        json.dumps({"schema": mk15.INVOERSCHEMA, "items": items}), encoding="utf-8"
    )
    return pad, items


def _sha_tekst(tekst: str) -> str:
    import hashlib

    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


class _LokaalProvider(_FakeProvider):
    """Antwoordt per pakket; ziet alleen wat de lokale prompt draagt."""

    def __init__(self, *, uitkomsten=None, standaard="supported", stop=None,
                 fout_bij=None):  # fmt: skip
        super().__init__()
        self.uitkomsten = uitkomsten or {}
        self.standaard = standaard
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
        pakket = _PAKKETHASH.search(user).group(1)
        tekst = json.dumps(
            {
                "schema_version": lc.LOKAAL_VERIFICATIESCHEMA,
                "packet_hash": pakket,
                "checks": [
                    {
                        "item": lc.CONTROLE_ITEM,
                        "outcome": self.uitkomsten.get(pakket, self.standaard),
                        "finding": "Synthetische bevinding.",
                    }
                ],
            }
        )
        return ChatResponse(
            text=tekst, tokens_used=10, model=model, stop_reason=self.stop
        )


def _freeze(omg, tmp_path: Path, proef) -> Path:
    pad = tmp_path / "freeze-l.json"
    if not pad.exists():
        pad.write_text(
            json.dumps(runner.freezevelden(omg, proef, "l")), encoding="utf-8"
        )
    return pad


def _l15(omg, tmp_path, pad, *, nieuw=True, **kw):
    proef = dataclasses.replace(runner.PROEVEN["R15"], l_invoer_sha256=_sha(pad))
    return asyncio.run(
        runner.voer_l_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag15(tmp_path),
            proef=proef,
            freeze=_freeze(omg, tmp_path, proef),
            voorganger_opslag=(
                _keten15(tmp_path) if nieuw else _bestaande_keten15(tmp_path)
            ),
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _uitkomsten_per_verwachting(items, *, omgekeerd=False) -> dict[str, str]:
    tegen = {"supported": "unsupported", "unsupported": "supported"}
    return {
        i["pakket_hash"]: tegen[i["verwacht"]] if omgekeerd else i["verwacht"]
        for i in items
    }


# --- identiteit en kosten -------------------------------------------------------------------


class TestIdentiteit:
    def test_vier_lokale_stappen_cumulatief_391(self):
        r15 = gb.R15
        assert r15.proef_id == R15_ID
        assert dict(r15.fasecaps) == {"lokale_verificatie": 4}
        assert (r15.reserve_max, r15.totaal_max) == (0, 4)
        assert r15.voorganger is gb.R14
        assert r15.cumulatief_max == 391 == 387 + 4
        assert r15.modelstappen_per_geval == 1
        assert dict(r15.fasestappen) == {"lokale_verificatie": (W,)}
        assert dict(r15.fasevolgorde) == {"lokale_verificatie": ()}
        assert (r15.stop_bij_eerste_fout, r15.stop_alleen_technisch) == (True, True)
        assert [(g.naam, set(g.fases), g.herhaal_aantal) for g in r15.eindgroepen] == [
            ("l", {"lokale_verificatie"}, 0)
        ]

    def test_zelfde_model_en_grenzen_plafond_1_50(self):
        kb15, kb8 = gb.R15.kostenbewaking, gb.R8.kostenbewaking
        for veld in ("model", "tarief_invoer_nusd", "tarief_uitvoer_nusd",
                     "max_tokens", "overhead_tokens"):  # fmt: skip
            assert getattr(kb15, veld) == getattr(kb8, veld), veld
        assert dict(kb15.bytegrens) == dict(kb8.bytegrens)
        assert kb15.plafond_nusd == gb.begroting_nusd(gb.R15) == 4 * 375_000_000
        assert kb15.plafond_nusd == 1_500_000_000 <= KADERREST_NUSD
        assert gb.R15.kostenkader_nusd == 25_000_000_000

    def test_r14_ongewijzigd(self):
        assert (gb.R14.totaal_max, gb.R14.cumulatief_max) == (12, 388)
        assert gb.R14.kostenbewaking.plafond_nusd == 4_200_000_000

    def test_cumulatief_391_past_392_niet(self, tmp_path):
        keten = [
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
        assert sum(b.samenvatting()["totaal"] for b in keten) == 387
        boek = gb.Grootboek.nieuw(_opslag15(tmp_path).grootboek, gb.R15)
        gb.controleer_cumulatief(boek, keten, 4)
        with pytest.raises(gb.BudgetSchendingError, match="391"):
            gb.controleer_cumulatief(boek, keten, 5)

    @pytest.mark.skipif(
        not all(runner.PROEVEN[n].opslag.grootboek.is_file() for n in OUDE_RONDES),
        reason="git-ignored echte grootboeken ontbreken",
    )
    def test_echte_grootboeken_387_calls_usd_2_770040_en_r14_kop(self, tmp_path):
        keten = [
            gb.Grootboek.lees(runner.PROEVEN[n].opslag.grootboek, runner.PROEVEN[n].identiteit)
            for n in reversed(OUDE_RONDES)
        ]  # fmt: skip
        assert sum(b.samenvatting()["totaal"] for b in keten) == 387
        lopend = sum(b.kostenstand()["lopend_nusd"] for b in keten[:7])
        assert lopend == 2_770_040_000 == 25_000_000_000 - KADERREST_NUSD
        assert keten[0].kostenstand()["lopend_nusd"] == R14_KOSTEN_NUSD
        assert keten[0].samenvatting()["kop_sha256"] == runner.R14_KOP_SHA256
        runner._controleer_voorgangerkop(runner.PROEVEN["R15"], tuple(keten))
        boek = gb.Grootboek.nieuw(_opslag15(tmp_path).grootboek, gb.R15)
        gb.controleer_cumulatief(boek, keten, 4)
        with pytest.raises(gb.BudgetSchendingError, match="391"):
            gb.controleer_cumulatief(boek, keten, 5)


# --- registratie en besluit -----------------------------------------------------------------


class TestRegistratie:
    def test_r15_geregistreerd_met_eigen_invoer_besluit_en_beide_contracten(self):
        proef = runner.PROEVEN["R15"]
        assert proef.identiteit is gb.R15
        assert (proef.echt_toegestaan, proef.freeze_vereist) == (True, True)
        assert proef.opslag.root == R15_MAP
        assert proef.l_invoer_sha256 == L15_SHA256
        assert proef.t_ontwikkelinvoer_sha256 is None
        assert proef.v_invoer_sha256 is None
        assert proef.budgetbesluit == BESLUIT15
        assert (proef.payloadtoestemming, proef.payloadtoestemming_sha256) == (
            TOESTEMMING,
            TOESTEMMING_SHA256,
        )
        # De productketen blijft ongewijzigd; het lokale contract komt erbij.
        assert dict(proef.contract) == HUIDIG_CONTRACT
        assert dict(proef.lokaal_contract) == runner.lokale_contractidentiteit()
        assert proef.kaderverruiming_modelstappen == 0
        assert proef.kaderrest_nusd == KADERREST_NUSD
        assert proef.voorganger_kop_sha256 == runner.R14_KOP_SHA256
        runner._controleer_contract(_omgeving8(_LokaalProvider()), proef)
        runner._controleer_lokaal_contract(proef)

    @pytest.mark.parametrize(
        "veld",
        [
            "local_verification_prompt_version",
            "local_packet_schema_version",
            "local_verification_schema_version",
            "local_system_prompt_material_sha256",
            "local_system_prompt_inference_sha256",
        ],
    )
    def test_afwijkend_lokaal_contract_geweigerd(self, veld):
        vast = {**runner.PROEVEN["R15"].lokaal_contract, veld: "anders"}
        proef = dataclasses.replace(runner.PROEVEN["R15"], lokaal_contract=vast)
        with pytest.raises(gb.BudgetSchendingError, match="lokale contractidentiteit"):
            runner._controleer_lokaal_contract(proef)

    def test_voorgangerkop_exact(self, tmp_path):
        boek = _r14_boek(tmp_path / "r14")
        kop = boek.samenvatting()["kop_sha256"]
        proef = dataclasses.replace(runner.PROEVEN["R15"], voorganger_kop_sha256=kop)
        runner._controleer_voorgangerkop(proef, (boek,))
        for keten in ((), None):
            with pytest.raises(gb.BudgetSchendingError, match="voorgangergrootboek"):
                runner._controleer_voorgangerkop(proef, keten)
        # Eén afwijkende kostenregel geeft een andere kop.
        ander = _r14_boek(tmp_path / "ander", kosten=R14_KOSTEN_NUSD + 11)
        assert ander.samenvatting()["kop_sha256"] != kop
        with pytest.raises(gb.BudgetSchendingError, match="voorgangergrootboek"):
            runner._controleer_voorgangerkop(proef, (ander,))

    def test_freezegroep_l_bindt_product_en_lokaal_contract(self):
        omg = _omgeving8(_LokaalProvider())
        velden = runner.freezevelden(omg, runner.PROEVEN["R15"], "l")
        assert velden["groep"] == "l"
        assert velden["proef_id"] == R15_ID
        for sleutel, waarde in {
            **HUIDIG_CONTRACT,
            **runner.lokale_contractidentiteit(),
        }.items():
            assert velden[sleutel] == waarde, sleutel

    @besluit_nodig
    def test_besluit_gebonden_aan_opdracht_en_past_op_r15(self):
        data = json.loads(BESLUIT15.read_text(encoding="utf-8"))
        bron = json.loads(OPDRACHT.read_text(encoding="utf-8"))
        assert data["bron_sha256"] == _sha(OPDRACHT)
        assert data["gebruikersantwoord"] == bron["gebruiker_letterlijk"]
        assert data["extra_modelaanroepen_max"] == bron["fase_a_sdk_calls"] == 4
        assert data["historisch_verbruik"] == bron["baseline_sdk_calls"] == 387
        assert data["cumulatief_max"] == bron["fase_a_cumulatief_max"] == 391
        assert runner._nusd(data["kostenbudget_usd"]) == runner._nusd(
            bron["fase_a_operationele_usd_cap"]
        )
        assert runner._nusd(data["kaderrest_usd"]) == runner._nusd(25) - runner._nusd(
            bron["baseline_usd_sinds_r8"]
        )
        assert data["r14_grootboekkop_sha256"] == runner.R14_KOP_SHA256
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R15"]) == (
            runner.R15_BUDGETBESLUIT_SHA256
        )

    @besluit_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 5},
            {"cumulatief_max": 392},
            {"historisch_verbruik": 386},
            {"reserve": 1},
            {"kostenbudget_usd": "1.500001"},
            {"kaderrest_usd": "22.229961"},
            {"r14_verbruik_usd": "1.100451"},
            {"r14_verbruik_usd": None},
            {"r14_verbruik_modelstappen": 12},
            {"fasen_modelstappen_max": {"lokale_verificatie": 5}},
        ],
    )
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        data = json.loads(BESLUIT15.read_text(encoding="utf-8"))
        for sleutel, waarde in anders.items():
            if waarde is None:
                data.pop(sleutel)
            else:
                data[sleutel] = waarde
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps(data), encoding="utf-8")
        proef = dataclasses.replace(
            runner.PROEVEN["R15"], budgetbesluit=pad, budgetbesluit_sha256=_sha(pad)
        )
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)


# --- lokale fase: stopregel en afzonderlijke verzoeken (offline) ----------------------------


class TestLokaleFase:
    def test_vier_afzonderlijke_verzoeken_met_alleen_het_eigen_pakket(self, tmp_path):
        pad, items = _l_invoer(tmp_path)
        provider = _LokaalProvider(uitkomsten=_uitkomsten_per_verwachting(items))
        samenvatting = _l15(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 4
        for (system, user), item in zip(provider.berichten, items, strict=True):
            assert item["pakket_hash"] in user
            anderen = [i for i in items if i is not item]
            assert not any(a["pakket"]["uitspraak"] in user for a in anderen)
            assert "verwacht" not in user and item["id"] not in user
            assert _sha_tekst(system) in runner.lokale_contractidentiteit().values()
            (blok,) = _PAKKETBLOK.findall(user)
            assert json.loads(html.unescape(blok)) == item["pakket"]
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"]) for g in gevallen] == [
            (True, True)
        ] * 4
        assert len(_soort(tmp_path, "reservering")) == 4
        assert samenvatting["grootboek_na"]["gestopt"] is False
        assert samenvatting["lokaal_contract"] == runner.lokale_contractidentiteit()
        assert "geen volledig geverifieerd concept" in samenvatting["bereik"]
        assert [c["model"] for c in provider.aanroepen] == [
            provider.aanroepen[0]["model"]
        ] * 4
        assert {c["max_tokens"] for c in provider.aanroepen} == {3000}

    def test_verkeerde_uitkomst_stopt_niet_en_blijft_zichtbaar(self, tmp_path):
        pad, items = _l_invoer(tmp_path)
        provider = _LokaalProvider(
            uitkomsten=_uitkomsten_per_verwachting(items, omgekeerd=True)
        )
        samenvatting = _l15(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 4
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"]) for g in gevallen] == [
            (False, True)
        ] * 4
        assert samenvatting["grootboek_na"]["gestopt"] is False
        (callmap,) = (tmp_path / "uit").glob("lokale_verificatie-*/calls")
        records = sorted(callmap.glob("*.json"))
        assert len(records) == 4
        eerste = json.loads(records[0].read_text(encoding="utf-8"))
        assert eerste["schema"] == "def768-ess05-lokalecall/1"
        assert eerste["prompt"]["komt_overeen_met_dienst"] is True
        assert eerste["lokale_verificatie"]["uitkomst"] == "supported"
        assert eerste["acceptatie"]["geaccepteerd"] is False

    def test_undetermined_is_geen_supported(self, tmp_path):
        pad, _ = _l_invoer(tmp_path)
        provider = _LokaalProvider(standaard="undetermined")
        _l15(_omgeving8(provider), tmp_path, pad)
        gevallen = _soort(tmp_path, "geval")
        assert [g["geaccepteerd"] for g in gevallen] == [False] * 4
        assert all("undetermined" in g["reden"] for g in gevallen)

    def test_technische_fout_stopt_duurzaam_zonder_retry(self, tmp_path):
        pad, items = _l_invoer(tmp_path)
        provider = _LokaalProvider(
            uitkomsten=_uitkomsten_per_verwachting(items), fout_bij=2
        )
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _l15(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 2  # geen retry, geen derde item
        gevallen = _soort(tmp_path, "geval")
        assert [(g["geaccepteerd"], g["technisch_afgerond"]) for g in gevallen] == [
            (True, True),
            (False, False),
        ]
        tweede = _LokaalProvider()
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _l15(_omgeving8(tweede), tmp_path, pad, nieuw=False)
        assert tweede.berichten == []

    def test_providerweigering_stopt(self, tmp_path):
        pad, _ = _l_invoer(tmp_path)
        provider = _LokaalProvider(stop="refusal")
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _l15(_omgeving8(provider), tmp_path, pad)
        assert len(provider.berichten) == 1
        (geval,) = _soort(tmp_path, "geval")
        assert (geval["geaccepteerd"], geval["technisch_afgerond"]) == (False, False)
        assert "weigering door de provider" in geval["reden"]

    def test_vijfde_pakket_boven_de_fasecap_geweigerd(self, tmp_path):
        pad, _ = _l_invoer(tmp_path, n=5)
        provider = _LokaalProvider()
        with pytest.raises(
            gb.BudgetSchendingError,
            match="plan vraagt 5 calls; fasecap lokale_verificatie laat nog 4",
        ):
            _l15(_omgeving8(provider), tmp_path, pad)
        assert provider.berichten == []

    def test_technische_herhaling_geweigerd(self, tmp_path):
        pad, _ = _l_invoer(tmp_path)
        provider = _LokaalProvider()
        with pytest.raises(gb.BudgetSchendingError, match="technische herhaling"):
            _l15(_omgeving8(provider), tmp_path, pad,
                 technische_herhalingen=("lokale_verificatie|L-0|1",))  # fmt: skip
        assert provider.berichten == []

    def test_andere_invoer_dan_de_gepinde_geweigerd(self, tmp_path):
        pad, _ = _l_invoer(tmp_path)
        omg = _omgeving8(_LokaalProvider())
        with pytest.raises(gb.BudgetSchendingError, match="vastgelegde lokale invoer"):
            asyncio.run(
                runner.voer_l_fase(
                    omg,
                    gevallenpad=pad,
                    uitmap=tmp_path / "uit",
                    opslag=_opslag15(tmp_path),
                    proef=runner.PROEVEN["R15"],
                    voorganger_opslag=_keten15(tmp_path),
                    nieuw_grootboek=True,
                )
            )
        assert not _opslag15(tmp_path).grootboek.exists()


# --- validatie van de lokale invoer ---------------------------------------------------------


def _gewijzigd(items, index, wijzig) -> dict:
    kopie = json.loads(json.dumps(items))
    wijzig(kopie[index])
    return {"schema": mk15.INVOERSCHEMA, "items": kopie}


class TestLInvoer:
    def test_geldige_invoer_opnieuw_gebonden(self, tmp_path):
        _, items = _l_invoer(tmp_path)
        omg = _omgeving8(_LokaalProvider())
        gebonden = runner.valideer_l_invoer(
            {"schema": mk15.INVOERSCHEMA, "items": items}, omg
        )
        assert [li.sleutel for li in gebonden] == [
            f"lokale_verificatie|L-{i}|1" for i in range(4)
        ]
        assert [li.pakket.hash for li in gebonden] == [i["pakket_hash"] for i in items]

    @pytest.mark.parametrize(
        ("wijzig", "melding"),
        [
            (lambda i: i["geval"].update(term="ander"), "geval_sha256"),
            (lambda i: i["materiaal_sha256"].update(definition="0" * 64), "materiaal"),
            (lambda i: i["pakket"].update(uitspraak="Iets anders."), "vastgelegde pakket"),
            (lambda i: i.update(pakket_hash="0" * 64), "vastgelegde pakket"),
            (lambda i: i["specificatie"].update(uitspraak="Iets anders."), "vastgelegde pakket"),
            (lambda i: i["specificatie"]["citaten"][0].update(end=3), "vastgelegde pakket"),
            (lambda i: i["specificatie"]["citaten"][0].update(end=10_000), "niet op te bouwen"),
            (lambda i: i["binding"]["citaten"][0].update(start=1), "binding"),
            (lambda i: i.update(prompt_sha256="0" * 64), "lokale prompt"),
            (lambda i: i.update(verwacht="supported"), "verwachting"),
            (lambda i: i.update(verwacht="undetermined"), "verwachting"),
            (lambda i: i["specificatie"].update(rol="absence"), "onbekende rol"),
        ],
    )  # fmt: skip
    def test_gemanipuleerd_item_geweigerd(self, tmp_path, wijzig, melding):
        _, items = _l_invoer(tmp_path)
        data = _gewijzigd(items, 0, wijzig)
        with pytest.raises(pi.InvoerfoutError, match=melding):
            runner.valideer_l_invoer(data, _omgeving8(_LokaalProvider()))

    def test_verwisselde_pakkethashes_geweigerd(self, tmp_path):
        _, items = _l_invoer(tmp_path)
        kopie = json.loads(json.dumps(items))
        kopie[0]["pakket_hash"], kopie[1]["pakket_hash"] = (
            kopie[1]["pakket_hash"],
            kopie[0]["pakket_hash"],
        )
        with pytest.raises(pi.InvoerfoutError, match="vastgelegde pakket"):
            runner.valideer_l_invoer(
                {"schema": mk15.INVOERSCHEMA, "items": kopie},
                _omgeving8(_LokaalProvider()),
            )

    @pytest.mark.parametrize("dubbel", ["id", "pakket_hash"])
    def test_dubbele_ids_of_pakketten_geweigerd(self, tmp_path, dubbel):
        _, items = _l_invoer(tmp_path)
        kopie = json.loads(json.dumps(items))
        kopie[1][dubbel] = kopie[0][dubbel]
        with pytest.raises(pi.InvoerfoutError, match="dubbele"):
            runner.valideer_l_invoer(
                {"schema": mk15.INVOERSCHEMA, "items": kopie},
                _omgeving8(_LokaalProvider()),
            )

    @pytest.mark.parametrize(
        "data",
        [None, {}, {"schema": "iets/1", "items": [{}]},
         {"schema": mk15.INVOERSCHEMA, "items": []}],
    )  # fmt: skip
    def test_verkeerd_schema_geweigerd(self, data):
        with pytest.raises(pi.InvoerfoutError, match="schema"):
            runner.valideer_l_invoer(data, _omgeving8(_LokaalProvider()))


# --- de echte, gepinde R15-invoer -----------------------------------------------------------


@r15_invoer_nodig
class TestEchteInvoer:
    def test_gepind_deterministisch_en_gelabeld(self):
        assert _sha(L15) == L15_SHA256 == runner.R15_L_INVOER_SHA256
        tekst = json.dumps(mk15.maak_lokale_invoer(), ensure_ascii=False, indent=2)
        assert tekst + "\n" == L15.read_text(encoding="utf-8")
        data = json.loads(tekst)
        assert [(i["id"], i["soort"], i["verwacht"]) for i in data["items"]] == [
            ("L-N1", "negatief", "unsupported"),
            ("L-P1", "positief", "supported"),
            ("L-N2", "negatief", "unsupported"),
            ("L-P2", "positief", "supported"),
        ]
        for item in data["items"]:
            label = item["herkomst"].get("label")
            assert (label == mk15.LABEL) is (item["soort"] == "positief")
            # Hashes, ID's en verwachtingen staan buiten de modelpayload.
            payload = json.dumps(item["pakket"], ensure_ascii=False)
            for buiten in (item["id"], item["verwacht"], item["herkomst"]["doelclaim"],
                           *item["materiaal_sha256"].values()):  # fmt: skip
                assert buiten not in payload
        # De negatieven zijn de ongewijzigde R14-doelclaims; historisch supported.
        for naam in ("L-N1", "L-N2"):
            (item,) = [i for i in data["items"] if i["id"] == naam]
            assert item["herkomst"]["afleiding"] == "ongewijzigd"
            assert item["herkomst"]["historisch_r14"]["outcome"] == "supported"
        per_id = {i["id"]: i for i in data["items"]}
        for neg, pos in (("L-N1", "L-P1"), ("L-N2", "L-P2")):
            assert (
                per_id[neg]["pakket"]["uitspraak"] == per_id[pos]["pakket"]["uitspraak"]
            )
            assert per_id[neg]["pakket_hash"] != per_id[pos]["pakket_hash"]

    def test_runner_bindt_de_items_aan_de_huidige_code(self):
        data = json.loads(L15.read_text(encoding="utf-8"))
        items = runner.valideer_l_invoer(data, _omgeving8(_LokaalProvider()))
        assert [li.sleutel for li in items] == [
            f"lokale_verificatie|{n}|1" for n in ("L-N1", "L-P1", "L-N2", "L-P2")
        ]

    def test_droog_op_de_geregistreerde_r15(self, tmp_path):
        code = runner.main(["--proef", "R15", "--fase", "lokale_verificatie",
                            "--gevallen", str(L15), "--uitmap", str(tmp_path),
                            "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-lokale_verificatie-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert droog["proef_id"] == R15_ID
        assert droog["geplande_calls"] == 4
        assert droog["echte_calls"] == 0
        freeze = droog["freezevelden"]
        assert (freeze["groep"], freeze["dataset_sha256"]) == ("l", L15_SHA256)
        assert {k: freeze[k] for k in HUIDIG_CONTRACT} == HUIDIG_CONTRACT
        assert droog["lokaal_contract"] == runner.lokale_contractidentiteit()
        assert not list(tmp_path.rglob("*.jsonl"))
