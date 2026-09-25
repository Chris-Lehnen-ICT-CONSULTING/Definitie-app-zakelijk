"""DEF-768 R8 — gesloten proefvoorbereiding (ADR-003-keten), offline.

Voorbereiding volgens logs/def768/livevervolg-proefvoorstel-technisch-v1.md
§3/§6 met de leidende rootcorrecties: R8 blijft gesloten voor echte calls
zolang het budget (68 modelstappen, max USD 25) niet is goedgekeurd.

- ontwikkelinvoer: R720, R715 en R717 exact uit de R7-eindset;
- runner en expliciete verifier draaien op de productiegrenzen (3000 tokens,
  60 s); een afwijking wordt vóór grootboek en netwerk geweigerd;
- per geval een duurzame acceptatieregistratie; het eerste niet-geaccepteerde
  geval stopt de proef (geen verborgen herhaling);
- verifier-only-fase op de bevroren migratie-invoer; een schemaweigering telt
  niet als semantische detectie.

Providergrens is een fake; bewijst runnermechaniek, geen modelkwaliteit.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from services.ai.base_client import ChatResponse
from services.ai.model_router import ModelRouter
from tests.fixtures.def768_fakes import (
    concept_uit_spec,
    is_verificatievraag,
    materiaal_uit_prompt,
    verificatie_voor,
)
from tests.unit.scripts.test_def768_ess05_proefrunner import (
    NULCALL,
    ROOT,
    _AnderValidatiemodel,
    _FakeProvider,
    _gevallenbestand,
)
from tests.unit.scripts.test_def768_r3_proef import _boek
from tests.unit.scripts.test_def768_r7_proef import _voorgangers

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import migreer_r7_naar_v2 as mig
import proefgrootboek as gb
import run_ess05_proef as runner

try:  # de R8-maker bestaat pas na de GREEN-stap; RED faalt per test
    import maak_r8_ontwikkelinvoer as mk
except ModuleNotFoundError:  # pragma: no cover - alleen tijdens RED
    mk = None

R8_ID = "DEF-768-AI-20260925-R8"
R8_MAP = ROOT / "reports" / R8_ID
R7_MAP = ROOT / "reports" / "DEF-768-AI-20260925-R7"
R7_EINDSET = R7_MAP / "onafhankelijke-eindset-v1.json"
R8_SELECTIE = R8_MAP / "ontwikkelselectie-v1.json"
R8_VINVOER = R8_MAP / "verificatie-invoer-v1.json"
R7_EINDSET_SHA256 = "9b239e2c1b462f1e2235f9085ff85b82b5957506389d7db2f9b8b841692ee31b"
bron_nodig = pytest.mark.skipif(
    not R7_EINDSET.is_file(), reason="git-ignored R7-eindset ontbreekt"
)
T_IDS = ["R720", "R715", "R717"]


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


# --- ontwikkelinvoer ------------------------------------------------------------------------


class TestOntwikkelinvoerMaker:
    @bron_nodig
    def test_drie_gevallen_exact_uit_de_r7_eindset(self):
        selectie = mk.maak_t_selectie(R7_EINDSET.read_bytes(), bron_pad="x")
        assert [g["id"] for g in selectie["gevallen"]] == T_IDS
        bron = {g["id"]: g for g in json.loads(R7_EINDSET.read_bytes())["gevallen"]}
        for geval in selectie["gevallen"]:
            assert json.dumps(geval, sort_keys=True) == json.dumps(
                bron[geval["id"]], sort_keys=True
            ), geval["id"]
        assert "herhaal_ids" not in selectie
        assert "geen onafhankelijke gold" in selectie["status"]
        assert selectie["herkomst"]["bronnen"]["r7"]["sha256"] == R7_EINDSET_SHA256
        mk.controleer_t_selectie(selectie, R7_EINDSET.read_bytes())

    def test_vastgelegde_bronhash(self):
        assert mk.T_R7_SHA256 == R7_EINDSET_SHA256
        assert mk.T_DOEL == R8_SELECTIE

    def test_andere_bron_geweigerd(self):
        with pytest.raises(mk.SelectiefoutError, match="bronhash"):
            mk.maak_t_selectie(b"{}", bron_pad="x")

    @bron_nodig
    def test_gewijzigd_geval_geweigerd(self):
        selectie = mk.maak_t_selectie(R7_EINDSET.read_bytes(), bron_pad="x")
        selectie["gevallen"][1]["verwacht"] = "pass"
        with pytest.raises(mk.SelectiefoutError, match="R715"):
            mk.controleer_t_selectie(selectie, R7_EINDSET.read_bytes())

    @bron_nodig
    def test_doel_wordt_nooit_overschreven(self, tmp_path):
        t = tmp_path / "t.json"
        assert mk.main(["--t-doel", str(t)]) == 0
        with pytest.raises(FileExistsError):
            mk.main(["--t-doel", str(t)])


class TestVastgelegdeR8Invoer:
    @bron_nodig
    @pytest.mark.skipif(not R8_SELECTIE.is_file(), reason="R8-selectie ontbreekt")
    def test_vastgelegde_invoer_is_reproduceerbaar(self):
        vast = json.loads(R8_SELECTIE.read_text(encoding="utf-8"))
        assert vast == mk.maak_t_selectie(
            R7_EINDSET.read_bytes(), bron_pad=vast["herkomst"]["bron_pad_aanroep"]
        )

    @pytest.mark.skipif(not R8_SELECTIE.is_file(), reason="R8-selectie ontbreekt")
    def test_runner_bindt_de_vastgelegde_t_selectie(self):
        assert _sha(R8_SELECTIE) == runner.R8_T_ONTWIKKELINVOER_SHA256
        assert runner.PROEVEN["R8"].t_ontwikkelinvoer_sha256 == _sha(R8_SELECTIE)

    @pytest.mark.skipif(not R8_VINVOER.is_file(), reason="R8-V-invoer ontbreekt")
    def test_runner_bindt_de_vastgelegde_verificatie_invoer(self):
        assert _sha(R8_VINVOER) == runner.R8_V_INVOER_SHA256
        assert runner.PROEVEN["R8"].v_invoer_sha256 == _sha(R8_VINVOER)

    @bron_nodig
    @pytest.mark.skipif(not R8_VINVOER.is_file(), reason="R8-V-invoer ontbreekt")
    def test_verificatie_invoer_is_reproduceerbaar(self, tmp_path):
        doel = tmp_path / "v.json"
        assert (
            mig.main(["--doel", str(doel), "--controlelijst", str(tmp_path / "l.md")])
            == 0
        )
        assert _sha(doel) == _sha(R8_VINVOER)


# --- runner: registratie, productiegrenzen, kostenroute ------------------------------------

_CONCEPTBLOK = re.compile(
    r'<conceptoordeel candidate_hash="[0-9a-f]{64}">\n(.*?)\n</conceptoordeel>', re.S
)
_HEX64 = re.compile(r"[0-9a-f]{64}")
V = "validation"
W = "ess05_verification"


class _SDK8:
    """Fake SDK-berichtenklasse met werkelijke usage; bewaakt door de SDK-wacht."""

    usage = {"input_tokens": 100, "output_tokens": 20}
    aanroepen: list[dict] = []

    def __init__(self) -> None:
        self._client = SimpleNamespace(max_retries=0)

    async def create(self, **kwargs):
        type(self).aanroepen.append(kwargs)
        return SimpleNamespace(
            id="msg",
            model=kwargs.get("model"),
            stop_reason="end_turn",
            usage=SimpleNamespace(**type(self).usage),
        )


@pytest.fixture
def sdk_wacht():
    _SDK8.aanroepen = []
    herstel = gb.installeer_sdk_wacht(_SDK8)
    yield _SDK8
    herstel()


class _R8Provider(_FakeProvider):
    """Stap 1: geldig concept met het gekozen buurlabel; stap 2: verificatie.

    Met `sdk=True` gaat elke aanroep als echte platte-tekstpayload door de
    bewaakte (fake) SDK-klasse, zoals de Anthropic-client hem verstuurt.
    """

    def __init__(self, *, onderscheid="distinguished", uitkomsten=None, sdk=False,
                 hash_per_concept=None):  # fmt: skip
        super().__init__()
        self.onderscheid = onderscheid
        self.uitkomsten = uitkomsten or {}
        self.hash_per_concept = hash_per_concept or {}
        self.sdk = sdk
        self.stappen: list[str] = []

    def _uitkomsten(self, concept):
        """Per concepthash (sleutel van 64 hex) of voor elk concept (itemnamen)."""
        from domain.ess05.bewijs import Ess05Concept

        eigen = self.uitkomsten.get(Ess05Concept(concept).hash)
        if eigen is not None:
            return eigen
        return {k: v for k, v in self.uitkomsten.items() if not _HEX64.fullmatch(k)}

    async def chat_completion(self, messages, model, **kwargs):
        system = next(m.content for m in messages if m.role == "system")
        user = "\n".join(m.content for m in messages if m.role != "system")
        stap = "verificatie" if is_verificatievraag(user) else "beoordeling"
        self.stappen.append(stap)
        if self.sdk:
            await _SDK8().create(
                model=model,
                max_tokens=kwargs["max_tokens"],
                thinking={"type": "disabled"},
                system=system,
                messages=[{"role": "user", "content": user}],
                timeout=60.0,
            )
        if stap == "verificatie":
            concept = json.loads(html.unescape(_CONCEPTBLOK.search(user).group(1)))
            tekst = json.dumps(
                verificatie_voor(
                    concept,
                    uitkomsten=self._uitkomsten(concept),
                    candidate_hash=self.hash_per_concept.get("alle"),
                )
            )
        else:
            materiaal = materiaal_uit_prompt(user)
            buren = [
                p.removeprefix("neighbour:")
                for p in materiaal
                if p.startswith("neighbour:")
            ]
            onderscheiden = self.onderscheid == "distinguished"
            spec = {
                "lacks_differentia": not onderscheiden,
                "reason": "Synthetische reden.",
                "neighbours": [
                    {
                        "neighbour_id": b,
                        "distinction": self.onderscheid,
                        "distinguishing_feature_quote": (
                            "actuele lening" if onderscheiden else None
                        ),
                        "missing_feature": None if onderscheiden else "Kenmerk.",
                        "reason": "Synthetisch buuroordeel.",
                    }
                    for b in buren
                ],
            }
            tekst = json.dumps(concept_uit_spec(spec, materiaal))
        self.aanroepen.append({"model": model, **kwargs})
        return ChatResponse(text=tekst, tokens_used=10, model=model)


def _omgeving8(provider, *, router=None, timeout=60, max_tokens_t=3000,
               verifier_max_tokens=3000, sdk_bewaakt=False):  # fmt: skip
    return runner.bouw_omgeving(
        provider,
        router or ModelRouter.from_config(),
        timeout=timeout,
        max_tokens_t=max_tokens_t,
        verifier_max_tokens=verifier_max_tokens,
        sdk_bewaakt=sdk_bewaakt,
        geheimen=("GEHEIME-SLEUTEL-WAARDE",),
    )


def _r8(**anders) -> runner.Proef:
    return dataclasses.replace(runner.PROEVEN["R8"], **anders)


def _keten(tmp_path: Path):
    """(R7- … R1-opslag) in tmp: de volledige keten, nieuwste eerst."""
    r7 = runner.Proefopslag(tmp_path / "r7")
    _boek(r7.root, gb.R7, 2)
    return (r7, *_voorgangers(tmp_path))


def _opslag8(tmp_path: Path) -> runner.Proefopslag:
    return runner.Proefopslag(tmp_path / "r8")


def _bestaande_keten(tmp_path: Path):
    namen = ("r7", "r6", "r5", "r4", "r3", "r2", "r1")
    return tuple(runner.Proefopslag(tmp_path / n) for n in namen)


def _t8(omg, tmp_path, pad, *, fase="ontwikkeling", nieuw=True, proef=None, **kw):
    """Eerste aanroep maakt keten en grootboek; `nieuw=False` hervat beide."""
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag8(tmp_path),
            proef=proef or _r8(t_ontwikkelinvoer_sha256=_sha(pad)),
            voorganger_opslag=_keten(tmp_path) if nieuw else _bestaande_keten(tmp_path),
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _regels8(tmp_path) -> list[dict]:
    pad = _opslag8(tmp_path).grootboek
    return [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]


def _soort(tmp_path, soort) -> list[dict]:
    return [r for r in _regels8(tmp_path) if r["soort"] == soort]


BUDGETBESLUIT = ROOT / "logs" / "def768" / "ronde8-budgetgoedkeuring-v1.json"
BUDGETBESLUIT_SHA256 = (
    "bf82cd3bfd6cea12fc0d3d97df2305c922fdde8c19fb84db6f0a1e3320195d17"
)
besluit_nodig = pytest.mark.skipif(
    not BUDGETBESLUIT.is_file(), reason="git-ignored budgetbesluit ontbreekt"
)


def _besluit(tmp_path: Path, **anders) -> Path:
    """Een kopie van het budgetbesluit met gewijzigde velden (alleen strenger)."""
    data = json.loads(BUDGETBESLUIT.read_text(encoding="utf-8"))
    data.update(anders)
    pad = tmp_path / "besluit.json"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


class TestR8Registratie:
    def test_r8_geregistreerd_open_binnen_de_goedgekeurde_limieten(self):
        proef = runner.PROEVEN["R8"]
        assert proef.identiteit is gb.R8
        assert proef.echt_toegestaan is True
        assert proef.freeze_vereist is True
        assert proef.opslag.root == R8_MAP
        assert proef.t_ontwikkelinvoer_sha256 == runner.R8_T_ONTWIKKELINVOER_SHA256
        assert proef.v_invoer_sha256 == runner.R8_V_INVOER_SHA256
        assert proef.g_ontwikkelinvoer_sha256 is None
        assert runner.V_FASES == ("verificatie_alleen",)
        # De goedkeuring is gepind: pad en hash van het budgetbesluit.
        assert proef.budgetbesluit == BUDGETBESLUIT
        assert proef.budgetbesluit_sha256 == BUDGETBESLUIT_SHA256
        assert runner.R8_BUDGETBESLUIT_SHA256 == BUDGETBESLUIT_SHA256
        # Limieten ongewijzigd: 68 stappen, reserve 0, 427, USD 25.
        assert (gb.R8.totaal_max, gb.R8.reserve_max, gb.R8.cumulatief_max) == (
            68,
            0,
            427,
        )
        assert gb.R8.kostenbewaking.plafond_nusd == 25_000_000_000

    def test_alleen_r8_open_oude_rondes_gesloten(self):
        for naam in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
            assert runner.PROEVEN[naam].echt_toegestaan is False
            assert runner.PROEVEN[naam].budgetbesluit_sha256 is None
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == ["R8"]

    @besluit_nodig
    def test_budgetbesluit_past_op_de_proefidentiteit(self):
        assert runner.controleer_budgetbesluit(runner.PROEVEN["R8"]) == (
            BUDGETBESLUIT_SHA256
        )

    @besluit_nodig
    @pytest.mark.parametrize(
        "anders",
        [
            {"extra_modelaanroepen_max": 69},
            {"cumulatief_max": 428},
            {"reserve": 3},
            {"kostenbudget_usd": "30.00"},
            {"historisch_verbruik": 358},
            {"fasen_modelstappen_max": {"ontwikkeling": 7, "verificatie_alleen": 6,
                                        "t_eind": 40, "t_herhaling": 16}},
            {"gebruikersantwoord": ""},
        ],
    )  # fmt: skip
    def test_afwijkend_besluit_geweigerd(self, tmp_path, anders):
        pad = _besluit(tmp_path, **anders)
        proef = _r8(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(proef)

    @besluit_nodig
    def test_gewijzigd_of_ontbrekend_besluit_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r8(budgetbesluit=_besluit(tmp_path)))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(_r8(budgetbesluit=tmp_path / "geen.json"))
        with pytest.raises(gb.BudgetSchendingError, match="budgetbesluit"):
            runner.controleer_budgetbesluit(runner.PROEVEN["R7"])

    @besluit_nodig
    def test_echte_poorten_open_via_de_geregistreerde_route(self):
        """Zonder grootboek of netwerk: de gewone poorten laten R8 door."""
        proef = runner.PROEVEN["R8"]
        omg = dataclasses.replace(_omgeving8(_R8Provider()), echt=True)
        runner._controleer_opslag(omg, proef.opslag, proef)
        runner._controleer_goedkeuring(omg, proef)
        runner._controleer_productiegrenzen(omg, proef)
        runner._controleer_kostenroute(omg, proef)
        assert runner._besluit_voor(omg, proef) == BUDGETBESLUIT_SHA256
        offline = _omgeving8(_R8Provider())
        assert runner._besluit_voor(offline, proef) is None

    @besluit_nodig
    def test_cli_echt_r8_bouwt_de_live_omgeving_op_productiegrenzen(
        self, monkeypatch, tmp_path
    ):
        gebouwd = {}

        class _GestoptError(Exception):
            pass

        def _live(**kw):
            gebouwd.update(kw)
            raise _GestoptError  # vóór client, grootboek en netwerk

        monkeypatch.setattr(runner, "live_omgeving", _live)
        pad = _gevallenbestand(tmp_path, 3)
        with pytest.raises(_GestoptError):
            runner.main(["--proef", "R8", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--echt"])  # fmt: skip
        assert gebouwd == {
            "timeout": 60,
            "max_tokens_t": 3000,
            "verifier_max_tokens": 3000,
        }
        assert not (R8_MAP / "callgrootboek.jsonl").exists()

    @besluit_nodig
    def test_cli_weigert_een_niet_passend_besluit_voor_de_live_omgeving(
        self, monkeypatch, tmp_path, capsys
    ):
        gebouwd = []
        monkeypatch.setattr(runner, "live_omgeving", lambda **kw: gebouwd.append(kw))
        pad = _besluit(tmp_path, reserve=3)
        monkeypatch.setitem(
            runner.PROEVEN, "R8", _r8(budgetbesluit=pad, budgetbesluit_sha256=_sha(pad))
        )
        gevallen = _gevallenbestand(tmp_path, 3)
        with pytest.raises(SystemExit) as exc:
            runner.main(["--proef", "R8", "--fase", "ontwikkeling", "--gevallen",
                         str(gevallen), "--echt"])  # fmt: skip
        assert exc.value.code == 2
        assert "budgetbesluit past niet" in capsys.readouterr().err
        assert gebouwd == []  # geen sleutel, client of grootboek
        assert not (R8_MAP / "callgrootboek.jsonl").exists()

    def test_echt_buiten_de_canonieke_opslag_geweigerd(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        pad = _gevallenbestand(tmp_path, 3)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            _t8(omg, tmp_path, pad, proef=runner.PROEVEN["R8"])
        assert provider.aanroepen == []
        assert not _opslag8(tmp_path).grootboek.exists()

    def test_echt_met_een_niet_geregistreerde_kopie_geweigerd(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        pad = _gevallenbestand(tmp_path, 3)
        kopie = _r8(t_ontwikkelinvoer_sha256=_sha(pad))
        with pytest.raises(gb.BudgetSchendingError, match="geregistreerde"):
            asyncio.run(runner.voer_t_fase(omg, fase="ontwikkeling", gevallenpad=pad,
                                           uitmap=tmp_path / "uit", opslag=kopie.opslag,
                                           proef=kopie))  # fmt: skip
        assert provider.aanroepen == []
        assert not (R8_MAP / "callgrootboek.jsonl").exists()

    def test_oude_ronde_blijft_ook_programmatisch_gesloten(self, tmp_path):
        provider = _R8Provider()
        omg = dataclasses.replace(_omgeving8(provider), echt=True)
        r7 = runner.PROEVEN["R7"]
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            runner._controleer_opslag(omg, r7.opslag, r7)
        assert provider.aanroepen == []


class TestProductiegrenzen:
    def test_productiegrenzen_uit_de_diensten(self):
        assert runner.productiegrenzen() == {
            "beoordeling": {"max_tokens": 3000, "timeout_s": 60},
            "verificatie": {"max_tokens": 3000, "timeout_s": 60},
        }

    def test_expliciete_verifier_op_productiegrenzen(self):
        omg = _omgeving8(_R8Provider())
        verifier = omg.dienst.verification_service
        assert (verifier.max_tokens, verifier.timeout_seconds) == (3000, 60)
        config = runner.effectieve_config(omg)
        assert (
            config["t"]["max_tokens"] == config["t_verificatie"]["max_tokens"] == 3000
        )
        assert config["t"]["timeout_s"] == config["t_verificatie"]["timeout_s"] == 60

    @pytest.mark.parametrize(
        "anders",
        [{"max_tokens_t": 1500}, {"timeout": 30}, {"verifier_max_tokens": 6000}],
    )
    def test_afwijkende_grenzen_geweigerd_voor_grootboek(self, tmp_path, anders):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 3)
        with pytest.raises(gb.BudgetSchendingError, match="productiegrenzen"):
            _t8(_omgeving8(provider, **anders), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag8(tmp_path).grootboek.exists()

    def test_buitenste_deadline_per_modelstap(self):
        omg = _omgeving8(_R8Provider())
        assert runner._buitenste_deadline(omg, 2) == 2 * 60 + runner.MARGE_S

    def test_droog_r8_op_andere_grenzen_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 3)
        with pytest.raises(gb.BudgetSchendingError, match="productiegrenzen"):
            asyncio.run(runner.droogrun("ontwikkeling", pad, tmp_path / "d",
                                        proef=_r8(t_ontwikkelinvoer_sha256=_sha(pad)),
                                        max_tokens_t=1500))  # fmt: skip


class TestKostenroute:
    def test_ander_model_geweigerd_voor_grootboek(self, tmp_path):
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 3)
        with pytest.raises(gb.BudgetSchendingError, match="model"):
            _t8(_omgeving8(provider, router=_AnderValidatiemodel()), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag8(tmp_path).grootboek.exists()

    def test_bytegrens_preflight_voor_grootboek(self, tmp_path):
        kb = gb.R8.kostenbewaking
        oud = kb.bytegrens
        object.__setattr__(kb, "bytegrens", MappingProxyType({V: 1000, W: 1000}))
        provider = _R8Provider()
        try:
            with pytest.raises(gb.BudgetSchendingError, match="bytegrens"):
                _t8(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 3))
        finally:
            object.__setattr__(kb, "bytegrens", oud)
        assert provider.aanroepen == []
        assert not _opslag8(tmp_path).grootboek.exists()

    def test_kostenplan_voor_elke_call(self, tmp_path):
        kb = gb.R8.kostenbewaking
        object.__setattr__(kb, "plafond_nusd", 1_000_000_000)
        provider = _R8Provider()
        try:
            with pytest.raises(gb.BudgetSchendingError, match="kostenplan"):
                _t8(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 3))
        finally:
            object.__setattr__(kb, "plafond_nusd", 25_000_000_000)
        assert gb.R8.kostenbewaking.plafond_nusd == 25_000_000_000
        assert provider.aanroepen == []
        assert _soort(tmp_path, "reservering") == []

    def test_nulcallroute_geweigerd_voor_grootboek(self, tmp_path):
        nul = next(
            g
            for g in json.loads(NULCALL.read_text(encoding="utf-8"))["gevallen"]
            if g.get("verwacht_route") == "nulcall"
        )
        pad = _gevallenbestand(tmp_path, 2)
        data = json.loads(pad.read_text(encoding="utf-8"))
        data["gevallen"].append(nul)
        pad.write_text(json.dumps(data), encoding="utf-8")
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="nulcall"):
            _t8(_omgeving8(provider), tmp_path, pad)
        assert provider.aanroepen == []
        assert not _opslag8(tmp_path).grootboek.exists()


class TestAcceptatieEnStop:
    def test_geaccepteerd_geval_registreert_kosten_tokens_en_latentie(
        self, sdk_wacht, tmp_path
    ):
        provider = _R8Provider(sdk=True)
        omg = dataclasses.replace(_omgeving8(provider), sdk_bewaakt=True)
        uitkomst = _t8(omg, tmp_path, _gevallenbestand(tmp_path, 3), max_calls=1)
        assert provider.stappen == ["beoordeling", "verificatie"]
        assert len(sdk_wacht.aanroepen) == 2
        reserveringen = _soort(tmp_path, "reservering")
        assert [(r["task_type"], r["kosten_grens_nusd"]) for r in reserveringen] == [
            (V, 315_000_000),
            (W, 375_000_000),
        ]
        stapkosten = 100 * 5_000 + 20 * 25_000
        assert [a["kosten_werkelijk_nusd"] for a in _soort(tmp_path, "afsluiting")] == [
            stapkosten,
            stapkosten,
        ]
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is True, geval["reden"]
        (resultaat,) = uitkomst["resultaten"]
        assert resultaat["geaccepteerd"] is True
        assert resultaat["tokens"] == {"input": 200, "output": 40}
        assert set(resultaat["latentie_s"]) == {"beoordeling", "verificatie"}
        assert uitkomst["tokens"] == {"input": 200, "output": 40}
        assert uitkomst["grootboek_na"]["kosten"]["lopend_nusd"] == 2 * stapkosten

    def test_niet_geaccepteerd_geval_stopt_de_proef_duurzaam(self, tmp_path):
        provider = _R8Provider(onderscheid="not_distinguished")
        pad = _gevallenbestand(tmp_path, 3)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _t8(_omgeving8(provider), tmp_path, pad)
        assert len(provider.aanroepen) == 2  # één geval, geen tweede
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is False
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _t8(_omgeving8(provider), tmp_path, pad, nieuw=False)
        assert len(provider.aanroepen) == 2

    def test_hervatting_na_crash_voor_de_gevalregistratie_start_niets(
        self, monkeypatch, tmp_path
    ):
        """R8-02: stappen afgesloten, proces weg vóór registreer_geval."""
        provider = _R8Provider()
        pad = _gevallenbestand(tmp_path, 3)

        class _CrashError(Exception):
            pass

        def _crash(*_a, **_k):
            raise _CrashError

        with monkeypatch.context() as m:
            m.setattr(gb.Grootboek, "registreer_geval", _crash)
            with pytest.raises(_CrashError):
                _t8(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["beoordeling", "verificatie"]
        assert _soort(tmp_path, "geval") == []
        with pytest.raises(gb.BudgetSchendingError, match="gevaluitkomst"):
            _t8(_omgeving8(provider), tmp_path, pad, nieuw=False)
        assert provider.stappen == ["beoordeling", "verificatie"]
        assert len(_soort(tmp_path, "reservering")) == 2

    def test_onnodige_weigering_is_geen_acceptatie(self, tmp_path):
        provider = _R8Provider(uitkomsten={"completeness": "unsupported"})
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _t8(_omgeving8(provider), tmp_path, _gevallenbestand(tmp_path, 3))
        (geval,) = _soort(tmp_path, "geval")
        assert geval["geaccepteerd"] is False
        assert "vrijgegeven" in geval["reden"]


def _record(*, statussen=("voltooid", "voltooid"), doc="assessed", correct=True,
            buren=(True,)):  # fmt: skip
    return {
        "reserveringen": [{"afsluitstatus": s} for s in statussen],
        "transport": {"bewakingsweigering": None},
        "beoordelingsdocument": {"status": doc, "error": None},
        "vergelijking": {
            "status_correct": correct,
            "verwacht": "pass",
            "gekregen": "pass" if correct else "fail",
            "per_buur": [{"term": f"b{i}", "correct": c} for i, c in enumerate(buren)],
        },
    }


class TestAcceptatieregel:
    @pytest.mark.parametrize("volledig", [False, True])
    def test_volledig_correct_wordt_geaccepteerd(self, volledig):
        assert runner._t_acceptatie(_record(), volledig=volledig)[0] is True

    @pytest.mark.parametrize(
        "record",
        [
            _record(statussen=("voltooid", "modelfout")),
            _record(statussen=("voltooid",)),
            _record(doc="error"),
            _record(correct=False),
        ],
    )
    @pytest.mark.parametrize("volledig", [False, True])
    def test_fouten_worden_niet_geaccepteerd(self, record, volledig):
        assert runner._t_acceptatie(record, volledig=volledig)[0] is False

    def test_buurlabel_telt_alleen_in_de_eindfases(self):
        record = _record(buren=(True, False))
        assert runner._t_acceptatie(record, volledig=False)[0] is True
        assert runner._t_acceptatie(record, volledig=True)[0] is False


# --- verifier-only-fase ----------------------------------------------------------------


def _ontwikkeling_geaccepteerd(tmp_path: Path) -> None:
    boek = gb.Grootboek.nieuw(_opslag8(tmp_path).grootboek, gb.R8)
    for i in range(3):
        poging = f"ontwikkeling|D{i}|1"
        for index, (taak, naam) in enumerate(((V, "beoordeling"), (W, "verificatie"))):
            res = boek.reserveer("ontwikkeling", f"{poging}/{naam}", invoer_sha256="a" * 64,
                                 poging=poging, stap=naam,
                                 vorige_stap="beoordeling" if index else None,
                                 task_type=taak)  # fmt: skip
            boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
        boek.registreer_geval("ontwikkeling", poging, geaccepteerd=True, reden="test")


def _v_invoer(tmp_path: Path, soorten=("goed", "fout")) -> tuple[Path, list[dict]]:
    """Synthetische verifier-only-invoer via dezelfde itembouw als de migratie."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    norm = laad_ess05_norm()
    gevallen = json.loads(
        _gevallenbestand(tmp_path, len(soorten), "vg.json").read_text()
    )
    items = []
    for i, (geval, soort) in enumerate(zip(gevallen["gevallen"], soorten, strict=True)):
        materiaal, buren, _ = mig.verificatiemateriaal(geval, norm)
        spec = {
            "lacks_differentia": False,
            # Eigen reden per item: elk item heeft een eigen concepthash.
            "reason": f"Synthetische reden {i}.",
            "neighbours": [
                {"neighbour_id": b.id, "distinction": "distinguished",
                 "distinguishing_feature_quote": "actuele lening",
                 "reason": "Synthetisch buuroordeel."}
                for b in buren
            ],
        }  # fmt: skip
        concept = concept_uit_spec(spec, materiaal)
        fout = [f"neighbour:{buren[0].id}"] if soort == "fout" else []
        items.append(
            mig.invoeritem(
                f"V-{i}", soort, geval, concept, fout, {"bron": "synthetisch"}, norm
            )
        )
    pad = tmp_path / "v-invoer.json"
    pad.write_text(
        json.dumps({"schema": mig.INVOERSCHEMA, "items": items}), encoding="utf-8"
    )
    return pad, items


def _freeze_v(omg, tmp_path: Path, proef) -> Path:
    pad = tmp_path / "freeze-v.json"
    pad.write_text(json.dumps(runner.freezevelden(omg, proef, "v")), encoding="utf-8")
    return pad


def _v8(omg, tmp_path, pad, *, proef=None, ontwikkeling=True, **kw):
    proef = proef or _r8(v_invoer_sha256=_sha(pad))
    if ontwikkeling:
        _ontwikkeling_geaccepteerd(tmp_path)
    return asyncio.run(
        runner.voer_v_fase(
            omg,
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=_opslag8(tmp_path),
            proef=proef,
            freeze=_freeze_v(omg, tmp_path, proef),
            voorganger_opslag=_keten(tmp_path),
            nieuw_grootboek=not ontwikkeling,
            **kw,
        )
    )


def _v_gevallen(tmp_path) -> list[dict]:
    return [g for g in _soort(tmp_path, "geval") if g["fase"] == "verificatie_alleen"]


class TestVerifierOnly:
    def test_freeze_v_draagt_de_t_velden(self):
        velden = runner.freezevelden(
            _omgeving8(_R8Provider()), runner.PROEVEN["R8"], "v"
        )
        assert velden["groep"] == "v"
        assert velden["prompt_version"] == "ess05-assess/14"
        assert velden["verification_prompt_version"] == "ess05-verify/2"
        assert {"system_prompt_sha256", "norm_sha256"} <= set(velden)

    def test_goed_vrijgegeven_en_fout_gedetecteerd(self, tmp_path):
        pad, items = _v_invoer(tmp_path)
        fout = items[1]
        provider = _R8Provider(
            uitkomsten={
                fout["concept_hash"]: {fout["foutdragende_items"][0]: "unsupported"}
            }
        )
        uitkomst = _v8(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie", "verificatie"]
        v = [
            r
            for r in _soort(tmp_path, "reservering")
            if r["fase"] == "verificatie_alleen"
        ]
        assert [(r["task_type"], r["kosten_grens_nusd"]) for r in v] == [
            (W, 375_000_000),
            (W, 375_000_000),
        ]
        assert [g["geaccepteerd"] for g in _v_gevallen(tmp_path)] == [True, True]
        records = sorted((tmp_path / "uit").rglob("calls/*.json"))
        schema = {json.loads(p.read_text(encoding="utf-8"))["schema"] for p in records}
        assert schema == {"def768-ess05-verifiercall/1"}
        assert uitkomst["aanroepen_gestart"] == 2

    def test_fout_vrijgegeven_stopt(self, tmp_path):
        pad, _ = _v_invoer(tmp_path, soorten=("fout", "goed"))
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v8(_omgeving8(provider), tmp_path, pad)
        assert provider.stappen == ["verificatie"]
        (geval,) = _v_gevallen(tmp_path)
        assert geval["geaccepteerd"] is False

    def test_schemaweigering_telt_niet_als_detectie(self, tmp_path):
        pad, _ = _v_invoer(tmp_path, soorten=("fout",))
        provider = _R8Provider(hash_per_concept={"alle": "0" * 64})
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v8(_omgeving8(provider), tmp_path, pad)
        (geval,) = _v_gevallen(tmp_path)
        assert "schemaweigering" in geval["reden"]

    def test_weigering_buiten_de_foutdragers_telt_niet(self, tmp_path):
        pad, items = _v_invoer(tmp_path, soorten=("fout",))
        provider = _R8Provider(
            uitkomsten={items[0]["concept_hash"]: {"completeness": "unsupported"}}
        )
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v8(_omgeving8(provider), tmp_path, pad)
        (geval,) = _v_gevallen(tmp_path)
        assert "foutdragend" in geval["reden"]

    def test_onnodige_weigering_van_goed_item(self, tmp_path):
        pad, items = _v_invoer(tmp_path, soorten=("goed",))
        provider = _R8Provider(
            uitkomsten={items[0]["concept_hash"]: {"completeness": "undetermined"}}
        )
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _v8(_omgeving8(provider), tmp_path, pad)
        (geval,) = _v_gevallen(tmp_path)
        assert geval["geaccepteerd"] is False

    def test_voor_ontwikkeling_geweigerd(self, tmp_path):
        pad, _ = _v_invoer(tmp_path)
        provider = _R8Provider()
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkeling"):
            _v8(_omgeving8(provider), tmp_path, pad, ontwikkeling=False)
        assert provider.aanroepen == []

    @pytest.mark.parametrize(
        ("veld", "melding"),
        [
            ("concept_hash", "concept"),
            ("verificatieprompt_sha256", "verificatieprompt"),
            ("geval_sha256", "geval"),
        ],
    )
    def test_gewijzigde_binding_voor_grootboek_geweigerd(self, tmp_path, veld, melding):
        pad, items = _v_invoer(tmp_path)
        items[0][veld] = "f" * 64
        pad.write_text(json.dumps({"schema": mig.INVOERSCHEMA, "items": items}),
                       encoding="utf-8")  # fmt: skip
        provider = _R8Provider()
        with pytest.raises(Exception, match=melding):
            _v8(_omgeving8(provider), tmp_path, pad, ontwikkeling=False)
        assert provider.aanroepen == []
        assert not _opslag8(tmp_path).grootboek.exists()

    def test_freezes_v_en_t_delen_de_promptbinding_niet_de_groep(self, tmp_path):
        omg, proef = _omgeving8(_R8Provider()), runner.PROEVEN["R8"]
        v, t = (runner.freezevelden(omg, proef, g) for g in ("v", "t"))
        assert set(v) == set(t)
        assert {k for k in v if v[k] != t[k]} == {"groep"}
        # Een V-freeze geldt nooit voor T (groepsbinding blijft).
        with pytest.raises(gb.BudgetSchendingError, match="groep"):
            runner.controleer_freeze(_freeze_v(omg, tmp_path, proef), omg, proef, "t",
                                     dataset_sha256="a" * 64, herhaal_ids=[])  # fmt: skip

    def test_t_eind_na_v_met_een_eigen_freeze_per_eindgroep(self, tmp_path):
        """De geplande keten: V (freeze groep v), dan T (freeze groep t)."""
        pad, items = _v_invoer(tmp_path, ("goed", "fout") * 3)
        provider = _R8Provider(
            uitkomsten={
                i["concept_hash"]: {i["foutdragende_items"][0]: "unsupported"}
                for i in items
                if i["soort"] == "fout"
            }
        )
        omg = _omgeving8(provider)
        proef = _r8(v_invoer_sha256=_sha(pad))
        _v8(omg, tmp_path, pad, proef=proef)
        assert [g["geaccepteerd"] for g in _v_gevallen(tmp_path)] == [True] * 6
        freeze_t = tmp_path / "freeze-t.json"
        freeze_t.write_text(
            json.dumps(runner.freezevelden(omg, proef, "t")), encoding="utf-8"
        )
        voor = len(provider.stappen)
        _t8(omg, tmp_path, _gevallenbestand(tmp_path, 20, "eind.json"),
            fase="t_eind", nieuw=False, proef=proef, freeze=freeze_t,
            max_calls=1)  # fmt: skip
        assert provider.stappen[voor:] == ["beoordeling", "verificatie"]
        reserveringen = _soort(tmp_path, "reservering")
        v, *_ = [r for r in reserveringen if r["fase"] == "verificatie_alleen"]
        t, *_ = [r for r in reserveringen if r["fase"] == "t_eind"]
        for veld in ("code_sha256", "config_sha256"):
            assert t["binding"][veld] == v["binding"][veld]
        assert t["binding"]["freeze_sha256"] == _sha(freeze_t)
        assert v["binding"]["freeze_sha256"] != _sha(freeze_t)

    @pytest.mark.skipif(not R8_VINVOER.is_file(), reason="R8-V-invoer ontbreekt")
    def test_droog_echte_verificatie_invoer(self, tmp_path):
        code = runner.main(["--proef", "R8", "--fase", "verificatie_alleen", "--gevallen",
                            str(R8_VINVOER), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-verificatie_alleen-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R8_ID, 6)
        grens = gb.R8.kostenbewaking.bytegrens[W]
        assert all(i["payload_bytes"] <= grens for i in droog["items"])
        assert droog["freezevelden"]["groep"] == "v"
        assert not list(tmp_path.rglob("*.jsonl"))

    @pytest.mark.skipif(not R8_SELECTIE.is_file(), reason="R8-selectie ontbreekt")
    def test_droog_echte_ontwikkelselectie(self, tmp_path):
        code = runner.main(["--proef", "R8", "--fase", "ontwikkeling", "--gevallen",
                            str(R8_SELECTIE), "--uitmap", str(tmp_path), "--droog"])  # fmt: skip
        assert code == 0
        (bestand,) = tmp_path.glob("droog-ontwikkeling-*/droogrun.json")
        droog = json.loads(bestand.read_text(encoding="utf-8"))
        assert (droog["proef_id"], droog["geplande_calls"]) == (R8_ID, 3)
        grens = gb.R8.kostenbewaking.bytegrens[V]
        assert all(i["payload_bytes"] <= grens for i in droog["items"])
