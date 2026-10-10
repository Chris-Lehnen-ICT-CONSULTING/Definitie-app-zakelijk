"""DEF-835 — variatiemeting v9 op de ontwikkelset (besluit 21), volledig offline getoetst.

Het meetscript staat in het O2-dossier
(`goldset-voorbereiding/variatiemeting-v9/variatiemeting_v9.py`) en gebruikt
de echte keten van de proefrunner. De AI-dienst is gemockt aan de netwerkgrens
(`httpx.MockTransport`, nep-AI); sockets zijn in elke test geblokkeerd.
Bewezen: zonder `--live` geen call en geen sleutel, het kostenplafond van
US$3,00 vóór verzending, hard maximaal 48 calls, alleen ontwikkelgevallen
(geen hold-outbestand geopend), de controle op promptversie /6 en schemahash
`d3ad029e…`, de regels per call en de samenvatting. Niet bewezen: gedrag van
de echte provider.
"""

from __future__ import annotations

import builtins
import importlib.util
import io
import json
import socket
import sys
from pathlib import Path

import httpx
import pytest

from tests.fixtures.def835_int02_v4 import respons_voor_status

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
O2 = (
    ROOT
    / "docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925"
    / "gedeeld/uitvoering/o2/goldset-voorbereiding"
)
SCRIPT = O2 / "variatiemeting-v9" / "variatiemeting_v9.py"
SLEUTEL = "sk-ant-offline-GEHEIM-SLEUTEL-v9-0123456789"
ONTWIKKELING = json.loads(
    (O2 / "goldset-freeze-v1" / "ontwikkeling-v1.json").read_text("utf-8")
)
LABEL = {g["id"]: g["label"]["status"] for g in ONTWIKKELING["gevallen"]}
ID_BIJ_KERN = {g["geval"]["kern"]: g["id"] for g in ONTWIKKELING["gevallen"]}
#: Volgorde van manifest v9 (en van fase 2 van kwalificatieproef v9).
VOLGORDE = [
    "G011", "G015", "G019", "G027", "G030", "G039", "G007", "G021",
    "G037", "G041", "G046", "G055", "G008", "G012", "G036", "G048",
    "G050", "G052", "G042", "G045", "G047", "G060", "G070", "G076",
]  # fmt: skip
VERBODEN = ("holdout", "hold-out", "hold_out", "kwalificatie-payloads")


def _laad_script():
    spec = importlib.util.spec_from_file_location(
        "def835_int02_variatiemeting_v9", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


v = _laad_script()
#: Het echte `lees_manifest`: manifest v9 met de ketenhashes van de v9-meting.
_ECHT_LEES_MANIFEST = v.lees_manifest


@pytest.fixture(autouse=True)
def keten_gepind(monkeypatch):
    """Pin de ketenbestanden van manifest v9 op die van de werkboom.

    Na de v9-meting is de keten gewijzigd (besluit 22: contract /5); het script
    weigert dan terecht (`test_gewijzigde_keten_wordt_geweigerd_zonder_calls`).
    De andere tests toetsen het gedrag van het script los van latere
    codewijzigingen: alleen `identiteit.bestanden` wordt vervangen; de echte
    manifestcontrole (hash, prompt-, schema- en contractversie) draait wel.
    """

    def gepind():
        manifest = _ECHT_LEES_MANIFEST()
        manifest["identiteit"]["bestanden"] = {
            pad: v._sha((v.REPO / pad).read_bytes())
            for pad in manifest["identiteit"]["bestanden"]
        }
        return manifest

    monkeypatch.setattr(v, "lees_manifest", gepind)


@pytest.fixture(autouse=True)
def geen_netwerk(monkeypatch):
    """Elke socketverbinding faalt: de tests bewijzen nul netwerk."""

    def weiger(*args, **kwargs):
        msg = "netwerk is in deze test verboden"
        raise AssertionError(msg)

    monkeypatch.setattr(socket.socket, "connect", weiger)
    monkeypatch.setattr(socket, "create_connection", weiger)
    monkeypatch.setattr(socket, "getaddrinfo", weiger)


@pytest.fixture
def dotenv_uit(monkeypatch):
    """Zoals de aanroeper van een live meting: geen .env laden."""
    monkeypatch.setenv("DEFINITIE_DISABLE_DOTENV", "1")


def _usage(invoer=5800, uitvoer=400):
    return {
        "input_tokens": invoer,
        "output_tokens": uitvoer,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "inference_geo": "global",
        "output_tokens_details": {"thinking_tokens": 0},
        "server_tool_use": None,
        "service_tier": "standard",
    }


def _bericht(tekst: str, **usage) -> dict:
    return {
        "id": "msg_offline",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5",
        "content": [{"type": "text", "text": tekst}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": _usage(**usage),
    }


class NepAI:
    """Gemockte AI-dienst: kiest per geval en poging een status; registreert alles.

    `kies(geval_id, poging)` geeft een status (`pass`/`fail`/`review_required`),
    de tekst `"ongeldig"` (geen geldige uitvoer) of een `httpx.Response`.
    """

    def __init__(self, kies=None, **usage):
        self.verzoeken: list[dict] = []
        self.pogingen: dict[str, int] = {}
        self._kies = kies or (lambda geval_id, poging: LABEL[geval_id])
        self._usage = usage

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.verzoeken.append({"pad": request.url.path, "body": body})
        if request.url.path.endswith("/count_tokens"):
            return httpx.Response(200, json={"input_tokens": 5800})
        invoer = json.loads(body["messages"][0]["content"])["invoer"]
        geval_id = ID_BIJ_KERN[invoer["kern"]]
        poging = self.pogingen[geval_id] = self.pogingen.get(geval_id, 0) + 1
        keuze = self._kies(geval_id, poging)
        if isinstance(keuze, httpx.Response):
            return keuze
        if keuze == "ongeldig":
            return httpx.Response(200, json=_bericht("{}", **self._usage))
        tekst = json.dumps(respons_voor_status(invoer, keuze), ensure_ascii=False)
        return httpx.Response(200, json=_bericht(tekst, **self._usage))

    def inferenties(self):
        return [r for r in self.verzoeken if r["pad"] == "/v1/messages"]


async def _live(uitvoer, nep, **kw):
    return await v.voer_uit(
        uitvoer,
        live=True,
        sleutel=kw.pop("sleutel", lambda: SLEUTEL),
        binnen=httpx.MockTransport(nep),
        **kw,
    )


def _calls(uitvoer: Path) -> list[dict]:
    return [json.loads(r) for r in (uitvoer / "calls.jsonl").read_text().splitlines()]


# --- begrenzing ---------------------------------------------------------------------


def test_constanten_van_besluit_21():
    assert v.STANDAARD_HERHALINGEN == 2
    assert v.MAX_CALLS == 48
    assert v.MAX_HERHALINGEN == 2
    assert v.KOSTENPLAFOND_USD == 3.00
    assert v.VERWACHTE_PROMPTVERSIE == "def835-int02-prompt/6"
    assert v.VERWACHTE_SCHEMAHASH == (
        "d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715"
    )


@pytest.mark.parametrize("herhalingen", ["0", "3", "48", "-1", "twee"])
def test_cli_weigert_herhalingen_buiten_grens(tmp_path, herhalingen):
    with pytest.raises(SystemExit) as fout:
        v.main(["--herhalingen", herhalingen, "--uitvoer", str(tmp_path / "uit")])
    assert fout.value.code == 2
    assert not (tmp_path / "uit").exists()


@pytest.mark.parametrize("herhalingen", [0, 3, True, 2.0])
async def test_meer_dan_48_calls_of_ongeldig_aantal_wordt_geweigerd(
    tmp_path, dotenv_uit, herhalingen
):
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError):
        await _live(tmp_path / "uit", nep, herhalingen=herhalingen)
    assert nep.verzoeken == []
    assert not (tmp_path / "uit").exists()


# --- droge run ----------------------------------------------------------------------


async def test_zonder_live_geen_call_geen_sleutel_en_geen_uitvoer(tmp_path, caplog):
    nep = NepAI()
    gelezen = []

    def sleutel():
        gelezen.append(True)
        return SLEUTEL

    caplog.set_level("INFO", logger=v.logger.name)
    data = await v.voer_uit(
        tmp_path / "uit", sleutel=sleutel, binnen=httpx.MockTransport(nep)
    )
    assert nep.verzoeken == []
    assert gelezen == []
    assert not (tmp_path / "uit").exists()
    assert data["modus"] == "dry-run"
    assert data["inferenties"] == data["telverzoeken"] == 0
    assert data["opgevangen_zonder_verzending"] == 24
    raming = data["raming"]
    assert raming["calls"] == 48
    assert raming["reservering_per_call_usd"] == pytest.approx(0.23)
    assert raming["calls_binnen_plafond_bij_volle_reservering"] == 13
    # v9 fase 2 draaide 17 gevallen; de 7 andere krijgen het v9-gemiddelde.
    assert raming["gevallen_zonder_v9_meting"] == VOLGORDE[17:]
    assert 1.5 < raming["verwacht_usd"] < v.KOSTENPLAFOND_USD
    for geval_id in VOLGORDE:
        assert geval_id in caplog.text
    assert "gelijk aan manifest v9" in caplog.text


def test_cli_droge_run_is_standaard():
    assert v.main([]) == 0


async def test_droge_run_controleert_payloads_tegen_manifest_v9(monkeypatch):
    echte = v._ontwikkelhashes

    def vervalst(manifest):
        hashes = echte(manifest)
        hashes["G050"] = {**hashes["G050"], "payload_sha256": "0" * 64}
        return hashes

    monkeypatch.setattr(v, "_ontwikkelhashes", vervalst)
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await v.voer_uit(None)
    assert fout.value.reden == "payload_afwijkend_van_manifest_v9"


# --- promptversie en schemahash -----------------------------------------------------


async def test_andere_promptversie_stopt_zonder_calls(
    tmp_path, dotenv_uit, monkeypatch
):
    import services.validation.int02_assessment_service as dienst

    monkeypatch.setattr(dienst, "PROMPT_VERSION", "def835-int02-prompt/5")
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(tmp_path / "uit", nep)
    assert fout.value.reden == "promptversie_afwijkend"
    assert nep.verzoeken == []
    assert not (tmp_path / "uit").exists()


async def test_gewijzigde_keten_wordt_geweigerd_zonder_calls(
    tmp_path, dotenv_uit, monkeypatch
):
    """De meting hoort bij v9: wijkt een ketenbestand af van manifest v9 (zoals
    `contract.py` sinds besluit 22), dan weigert het script vóór elke call."""
    monkeypatch.setattr(v, "lees_manifest", _ECHT_LEES_MANIFEST)
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(tmp_path / "uit", nep)
    assert fout.value.reden == "ketenbestand_afwijkend"
    assert nep.verzoeken == []
    assert not (tmp_path / "uit").exists()


@pytest.fixture
def contract_en_dienst():
    """Beide modules vooraf geladen.

    De dienst bindt pin en schema bij import. Wordt hij pas geïmporteerd
    terwijl een test het contract patcht (de runner importeert de keten
    binnen `_proefomgeving`), dan houdt hij de valse waarde ook na de test.
    """
    import services.validation.int02_assessment_service as dienst
    from domain.int02 import contract

    return contract, dienst


@pytest.mark.parametrize("module", [0, 1], ids=["contract", "dienst"])
async def test_andere_schemapin_stopt_zonder_calls(
    tmp_path, dotenv_uit, monkeypatch, contract_en_dienst, module
):
    monkeypatch.setattr(contract_en_dienst[module], "ANTWOORDSCHEMA_SHA256", "f" * 64)
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(tmp_path / "uit", nep)
    assert fout.value.reden == "schemahash_afwijkend"
    assert nep.verzoeken == []
    assert not (tmp_path / "uit").exists()


@pytest.mark.parametrize("module", [0, 1], ids=["contract", "dienst"])
async def test_ander_schema_bij_dezelfde_pin_stopt_zonder_calls(
    tmp_path, dotenv_uit, monkeypatch, contract_en_dienst, module
):
    doel = contract_en_dienst[module]
    schema = {**doel.ANTWOORDSCHEMA, "description": "gewijzigd"}
    monkeypatch.setattr(doel, "ANTWOORDSCHEMA", schema)
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(tmp_path / "uit", nep)
    assert fout.value.reden == "schemahash_afwijkend"
    assert nep.verzoeken == []


# --- alleen ontwikkelgevallen -------------------------------------------------------


@pytest.fixture
def geopend(monkeypatch):
    """Registreert elk pad dat via open() geopend wordt."""
    paden: list[str] = []
    echte_open = io.open

    def registreer(bestand, *args, **kwargs):
        paden.append(str(bestand))
        return echte_open(bestand, *args, **kwargs)

    monkeypatch.setattr(io, "open", registreer)
    monkeypatch.setattr(builtins, "open", registreer)
    return paden


async def test_alleen_ontwikkelset_gelezen_nooit_een_holdoutbestand(
    tmp_path, dotenv_uit, geopend
):
    await v.voer_uit(None)
    await _live(tmp_path / "live", NepAI(), herhalingen=1)
    namen = [Path(p).name.lower() for p in geopend]
    assert "ontwikkeling-v1.json" in namen
    assert not [n for n in namen if any(deel in n for deel in VERBODEN)]
    assert "kwalificatie-gevallen-v1.json" not in namen


async def test_holdoutpad_wordt_geweigerd_voor_het_openen(
    tmp_path, monkeypatch, geopend
):
    pad = tmp_path / "holdout-v1.json"
    pad.write_text(json.dumps(ONTWIKKELING))
    geopend.clear()
    monkeypatch.setattr(v, "ONTWIKKELING_PAD", pad)
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await v.voer_uit(None)
    assert fout.value.reden == "verboden_bestand"
    assert str(pad) not in geopend


async def test_geval_buiten_de_ontwikkelset_wordt_geweigerd(tmp_path, monkeypatch):
    data = json.loads(json.dumps(ONTWIKKELING))
    vreemd = json.loads(json.dumps(data["gevallen"][0]))
    vreemd["id"] = vreemd["geval"]["id"] = "G002"  # een hold-out-ID uit manifest v9
    data["gevallen"].append(vreemd)
    pad = tmp_path / "ontwikkeling-test.json"
    pad.write_text(json.dumps(data))
    monkeypatch.setattr(v, "ONTWIKKELING_PAD", pad)
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await v.voer_uit(None)
    assert fout.value.reden == "geval_buiten_ontwikkelset"


# --- sleutel ------------------------------------------------------------------------


async def test_live_zonder_dotenv_uitschakeling_wordt_geweigerd(tmp_path, monkeypatch):
    monkeypatch.delenv("DEFINITIE_DISABLE_DOTENV", raising=False)
    gelezen = []
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(tmp_path / "uit", nep, sleutel=lambda: gelezen.append(1) or SLEUTEL)
    assert fout.value.reden == "dotenv_niet_uitgeschakeld"
    assert gelezen == []
    assert nep.verzoeken == []


async def test_live_zonder_uitvoermap_wordt_geweigerd(dotenv_uit):
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(None, nep)
    assert fout.value.reden == "uitvoermap_ontbreekt"
    assert nep.verzoeken == []


def test_sleutel_komt_alleen_uit_de_omgeving(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", SLEUTEL)
    assert v.lees_sleutel_uit_omgeving() == SLEUTEL
    monkeypatch.setenv("ANTHROPIC_API_KEY", "  ")
    assert v.lees_sleutel_uit_omgeving() is None
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert v.lees_sleutel_uit_omgeving() is None


async def test_live_zonder_sleutel_in_omgeving_wordt_geweigerd(
    tmp_path, dotenv_uit, monkeypatch
):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    nep = NepAI()
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await v.voer_uit(tmp_path / "uit", live=True, binnen=httpx.MockTransport(nep))
    assert fout.value.reden == "sleutel_ontbreekt"
    assert nep.verzoeken == []
    assert not (tmp_path / "uit").exists()


# --- live met gemockte dienst -------------------------------------------------------


async def test_live_twee_herhalingen_48_calls_met_regel_per_call(
    tmp_path, dotenv_uit, monkeypatch, caplog
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", SLEUTEL)
    nep = NepAI()
    uitvoer = tmp_path / "live"
    data = await v.voer_uit(uitvoer, live=True, binnen=httpx.MockTransport(nep))
    assert data["inferenties"] == data["telverzoeken"] == 48
    assert data["stopreden"] is None
    assert data["kosten_usd_conservatief"] == pytest.approx(48 * 0.039)
    assert len(nep.inferenties()) == 48
    calls = _calls(uitvoer)
    assert [(c["geval"], c["herhaling"]) for c in calls] == [
        (g, h) for h in (1, 2) for g in VOLGORDE
    ]
    eerste = calls[0]
    for veld in (
        "label",
        "status",
        "modelverdict",
        "uncertainty",
        "passages",
        "afleiding",
        "omzetting",
        "foutcategorie",
        "kosten_usd",
        "duur_ms",
        "ruw_antwoord",
    ):
        assert veld in eerste
    assert eerste["geval"] == "G011" and eerste["label"] == "pass"
    assert eerste["status"] == "pass" and eerste["modelverdict"] == "pass"
    assert eerste["passages"][0]["kernvorm"] == "no_act"
    assert {"bron", "function"} == set(eerste["passages"][0]["bronfuncties"][0])
    assert eerste["kosten_usd"] == pytest.approx(0.039)
    assert json.loads(eerste["ruw_antwoord"])["model"] == "claude-opus-5"
    assert eerste["promptversie"] == "def835-int02-prompt/6"
    # De payload van elke call is die van manifest v9 voor dat geval.
    herkomst = json.loads((uitvoer / "herkomst.json").read_text())
    per_id = {g["id"]: g["payload_sha256"] for g in herkomst["gevallen"]}
    assert all(c["payload_sha256"] == per_id[c["geval"]] for c in calls)
    assert sorted(p.name for p in uitvoer.iterdir()) == [
        "calls.jsonl",
        "herkomst.json",
        "samenvatting.json",
        "samenvatting.md",
    ]
    for bestand in uitvoer.iterdir():
        assert SLEUTEL not in bestand.read_text()
    assert SLEUTEL not in caplog.text


async def test_kostenplafond_stopt_voor_de_call_die_het_kan_overschrijden(
    tmp_path, dotenv_uit
):
    # 5.000 uitvoertokens: US$0,154 per call. Na 18 calls (US$2,772) past de
    # volle reservering (US$0,23) niet meer onder US$3,00: call 19 gaat niet uit.
    nep = NepAI(uitvoer=5000)
    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, nep)
    assert data["stopreden"] == "kostenplafond"
    assert data["inferenties"] == 18
    assert len(nep.inferenties()) == 18
    assert len(_calls(uitvoer)) == 18
    assert data["kosten_usd_conservatief"] == pytest.approx(18 * 0.154)
    assert data["kosten_usd_conservatief"] + 0.23 > v.KOSTENPLAFOND_USD
    assert data["kosten_usd_conservatief"] <= v.KOSTENPLAFOND_USD


async def test_providerfout_stopt_zonder_herhaling(tmp_path, dotenv_uit):
    fout = httpx.Response(500, json={"type": "error", "error": {"type": "api_error"}})
    nep = NepAI(lambda geval_id, poging: fout if geval_id == "G019" else "pass")
    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, nep)
    assert len(nep.inferenties()) == 3
    assert data["stopreden"] is not None
    assert [c["status"] for c in _calls(uitvoer)][-1] == "error"
    # Zonder betrouwbare boeking telt de volle reservering.
    assert data["kosten_usd_conservatief"] == pytest.approx(2 * 0.039 + 0.23)


async def test_uitvoerfout_van_het_model_wordt_vastgelegd_en_meting_gaat_door(
    tmp_path, dotenv_uit
):
    nep = NepAI(
        lambda geval_id, poging: "ongeldig" if geval_id == "G030" else LABEL[geval_id]
    )
    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, nep, herhalingen=1)
    assert data["stopreden"] is None
    assert data["inferenties"] == 24
    [g030] = [c for c in _calls(uitvoer) if c["geval"] == "G030"]
    assert g030["status"] == "error"
    assert g030["foutcategorie"] == "invalid_output"
    assert g030["ruw_antwoord"] is not None


# --- samenvatting -------------------------------------------------------------------


def _kern(status, functies=None, kernvorm="no_act"):
    """Kern zoals `kern_uit_document`; `functies` = {bron: functie} of lijst per passage."""
    if functies is None:
        return {"status": status, "heeft_oordeel": False, "passages": []}
    passages = functies if isinstance(functies, list) else [functies]
    return {
        "status": status,
        "heeft_oordeel": True,
        "passages": [
            {
                "kernvorm": kernvorm,
                "bronfuncties": [{"bron": b, "function": f} for b, f in p.items()],
            }
            for p in passages
        ],
    }


def test_samenvatting_telt_wissels_en_onterechte_passes_per_run():
    gevallen = [
        ("G011", "pass"),
        ("G050", "fail"),
        ("G030", "pass"),
        ("G070", "review_required"),
    ]
    runs = {
        "v9-fase2": {
            "G011": _kern("pass", {"bron/B1": "criterion"}),
            "G050": _kern(
                "pass",
                [
                    {"bron/B1": "derivation", "bron/B2": "derivation"},
                    {"bron/B1": "criterion", "bron/B2": "criterion"},
                ],
            ),
            "G030": _kern(
                "review_required",
                {"bron/B1": "criterion", "bron/B2": "actor_prescription"},
            ),
        },
        "h1": {
            "G011": _kern("pass", {"bron/B1": "criterion"}),
            "G050": _kern(
                "review_required",
                [
                    {"bron/B1": "derivation", "bron/B2": "derivation"},
                    {"bron/B1": "discretionary_decision_rule", "bron/B2": "criterion"},
                ],
            ),
            "G030": _kern("pass", {"bron/B1": "criterion", "bron/B2": "criterion"}),
            "G070": _kern("pass", {"bron/B1": "criterion"}),
        },
        "h2": {
            "G011": _kern("pass", {"bron/B1": "criterion"}),
            "G050": _kern("error"),  # geen oordeel: telt niet mee voor bronfuncties
            "G030": _kern("pass", {"bron/B1": "criterion", "bron/B2": "criterion"}),
            "G070": _kern("review_required", {"bron/B1": "unclear"}),
        },
    }
    data, md = v.maak_samenvatting(gevallen, runs, {"modus": "live"})
    assert data["per_run"]["v9-fase2"] == {
        "gedraaid": 3,
        "juist": 1,
        "onterechte_passes": ["G050"],
        "kritieke_false_passes": ["G050"],
    }
    assert data["per_run"]["h1"]["onterechte_passes"] == ["G070"]
    assert data["per_run"]["h1"]["kritieke_false_passes"] == []
    assert data["per_run"]["h2"]["onterechte_passes"] == []
    assert data["per_run"]["h2"]["juist"] == 3
    assert data["gevallen_met_wisselende_status"] == ["G050", "G030", "G070"]
    assert data["gevallen_met_wisselende_bronfuncties"] == ["G050", "G030", "G070"]
    per_geval = {g["geval"]: g for g in data["per_geval"]}
    assert per_geval["G011"]["stabiel"] is True
    assert per_geval["G011"]["wisselende_bronfuncties"] == {}
    # G050: B1 wisselt (criterion ↔ discretionary_decision_rule bij P2); B2 niet.
    assert per_geval["G050"]["wisselende_bronfuncties"] == {
        "bron/B1": {
            "v9-fase2": "derivation|criterion",
            "h1": "derivation|discretionary_decision_rule",
        }
    }
    assert per_geval["G030"]["wisselende_bronfuncties"] == {
        "bron/B2": {
            "v9-fase2": "actor_prescription",
            "h1": "criterion",
            "h2": "criterion",
        }
    }
    assert per_geval["G070"]["statussen"] == {"h1": "pass", "h2": "review_required"}
    # Markdown: een rij per geval, niet gedraaid zichtbaar, afwijkingen gemarkeerd.
    assert "| G011 | pass | `pass` | `pass` | `pass` | ja | — |" in md
    assert "| G070 | review_required | niet gedraaid | `pass` ✘ |" in md
    assert (
        "B1: v9-fase2 derivation·criterion / h1 derivation·discretionary_decision_rule"
        in md
    )
    assert "| onterechte passes | 1 (G050) | 1 (G070) | 0 |" in md
    assert "Gevallen met wisselende status: 3 (G050, G030, G070)." in md


def test_samenvatting_een_enkele_waarneming_is_niet_stabiel_of_wisselend():
    data, _ = v.maak_samenvatting(
        [("G076", "review_required")],
        {
            "v9-fase2": {},
            "h1": {"G076": _kern("review_required", {"bron/B1": "unclear"})},
        },
        {},
    )
    [geval] = data["per_geval"]
    assert geval["stabiel"] is None
    assert geval["wisselende_bronfuncties"] == {}
    assert data["gevallen_met_wisselende_status"] == []


async def test_live_samenvatting_bevat_v9_fase2_en_beide_herhalingen(
    tmp_path, dotenv_uit
):
    # G050: h1 review (eerste bron unclear), h2 pass; de rest volgt het label.
    def kies(geval_id, poging):
        if geval_id == "G050":
            return "review_required" if poging == 1 else "pass"
        return LABEL[geval_id]

    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, NepAI(kies))
    assert data["runs"] == ["v9-fase2", "h1", "h2"]
    assert data["per_run"]["v9-fase2"]["gedraaid"] == 17
    assert data["per_run"]["v9-fase2"]["onterechte_passes"] == ["G050"]
    assert data["per_run"]["h1"]["onterechte_passes"] == []
    assert data["per_run"]["h2"]["kritieke_false_passes"] == ["G050"]
    assert "G050" in data["gevallen_met_wisselende_status"]
    assert "G050" in data["gevallen_met_wisselende_bronfuncties"]
    md = (uitvoer / "samenvatting.md").read_text()
    assert "| G050 | fail | `pass` ✘ | `review_required` ✘ | `pass` ✘ | **nee** |" in md
    assert "| G076 | review_required | niet gedraaid |" in md
