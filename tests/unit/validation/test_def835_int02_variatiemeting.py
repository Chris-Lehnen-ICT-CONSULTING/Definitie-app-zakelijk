"""DEF-835 — variatiemeting C107 (besluit 11), volledig offline getoetst.

Het meetscript staat in het O2-dossier
(`goldset-voorbereiding/variatiemeting-c107-v1/variatiemeting.py`) en gebruikt
de echte keten van de proefrunner. Alleen de netwerkgrens is een
`httpx.MockTransport` (nep-AI); sockets zijn in elke test geblokkeerd.
Bewezen: harde grens van 5 runs, weigering van een bestaande uitvoermap,
zonder `--live` geen verzending en geen sleutel, kostenstop vóór verzending,
geen herhaling na een fout, alleen C107 in het verzoek, herkomst en
samenvatting. Niet bewezen: gedrag van de echte provider.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path

import httpx
import pytest

from domain.int02.contract import grondbronnen, maak_invoer
from tests.fixtures.def835_int02_v4 import naar_v4

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
O2 = (
    ROOT
    / "docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925"
    / "gedeeld/uitvoering/o2/goldset-voorbereiding"
)
SCRIPT = O2 / "variatiemeting-c107-v1" / "variatiemeting.py"
SLEUTEL = "sk-ant-offline-GEHEIM-SLEUTEL-0123456789"
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/def835_int02_ontwerpgevallen.json").read_text("utf-8")
)
C107 = next(g for g in FIXTURE["gevallen"] if g["id"] == "C107")
#: `meting.payload_sha256` van C107 in kwalificatieproef v5
#: (`goldset-freeze-v1/kwalificatieproef-v5/regressie-resultaat.json`). Sinds
#: prompt /4 (besluit 14) is de payload bewust anders: de v5-payload plus
#: alleen het antwoordschema; de meting van 07-10-2026 is historisch.
V5_PAYLOAD_C107 = "6f3507192174a0a90d22c8f5d8da35a87cad1d9180f159b1f5f14f9072789866"


def _laad_script():
    spec = importlib.util.spec_from_file_location("def835_int02_variatiemeting", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


v = _laad_script()


@pytest.fixture(autouse=True)
def geen_netwerk(monkeypatch):
    """Elke socketverbinding faalt: de tests bewijzen nul netwerk."""

    def weiger(*args, **kwargs):
        msg = "netwerk is in deze test verboden"
        raise AssertionError(msg)

    monkeypatch.setattr(socket.socket, "connect", weiger)
    monkeypatch.setattr(socket, "create_connection", weiger)
    monkeypatch.setattr(socket, "getaddrinfo", weiger)


def _usage(invoer=3574, uitvoer=418):
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


def _antwoord(**usage):
    """Nep-AI: het review_required-antwoord van C107 uit de ontwerpfixture.

    Sinds contract /4 (besluit 16) in /4-vorm via `naar_v4`: beschrijvende
    kern, de eerste grondbron laat de functie open.
    """
    respons = naar_v4(C107["invoer"], C107["modelrespons"])
    return {
        "id": "msg_offline",
        "type": "message",
        "role": "assistant",
        "model": "claude-opus-5",
        "content": [
            {
                "type": "text",
                "text": json.dumps(respons, ensure_ascii=False),
            }
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": _usage(**usage),
    }


class NepAI:
    """Nep-Anthropic-API; registreert elk verzoek."""

    def __init__(self, antwoorden):
        self.verzoeken: list[dict] = []
        self._antwoorden = list(antwoorden)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.verzoeken.append(
            {"pad": request.url.path, "body": json.loads(request.content)}
        )
        if request.url.path.endswith("/count_tokens"):
            return httpx.Response(200, json={"input_tokens": 3574})
        antwoord = self._antwoorden.pop(0)
        if isinstance(antwoord, httpx.Response):
            return antwoord
        return httpx.Response(200, json=antwoord)

    def inferenties(self):
        return [r for r in self.verzoeken if r["pad"] == "/v1/messages"]


async def _live(uitvoer, nep, **kw):
    return await v.voer_uit(
        uitvoer,
        live=True,
        sleutel=lambda: SLEUTEL,
        binnen=httpx.MockTransport(nep),
        **kw,
    )


def _runs(uitvoer: Path) -> list[dict]:
    return [json.loads(r) for r in (uitvoer / "runs.jsonl").read_text().splitlines()]


# --- begrenzing ---------------------------------------------------------------------


@pytest.mark.parametrize("aantal", ["0", "6", "50", "-1", "vijf"])
def test_cli_weigert_aantal_buiten_1_tot_5(tmp_path, aantal):
    with pytest.raises(SystemExit) as fout:
        v.main(["--aantal", aantal, "--uitvoer", str(tmp_path / "uit")])
    assert fout.value.code == 2
    assert not (tmp_path / "uit").exists()


@pytest.mark.parametrize("aantal", [0, 6, True, 5.0])
async def test_voer_uit_weigert_aantal_buiten_grens(tmp_path, aantal):
    nep = NepAI([])
    with pytest.raises(v.MetingGeweigerdError):
        await _live(tmp_path / "uit", nep, aantal=aantal)
    assert nep.verzoeken == []
    assert not (tmp_path / "uit").exists()


def test_standaard_is_vijf_en_maximum_is_vijf():
    assert v.STANDAARD_AANTAL == 5
    assert v.MAX_AANTAL == 5
    assert v.KOSTENSTOP_USD == 0.50


# --- uitvoermap ---------------------------------------------------------------------


async def test_bestaande_uitvoermap_wordt_geweigerd(tmp_path):
    uitvoer = tmp_path / "uit"
    uitvoer.mkdir()
    (uitvoer / "ouder.txt").write_text("blijft")
    nep = NepAI([_antwoord()])
    with pytest.raises(v.MetingGeweigerdError) as fout:
        await _live(uitvoer, nep, aantal=1)
    assert fout.value.reden == "uitvoermap_bestaat"
    assert nep.verzoeken == []
    assert sorted(p.name for p in uitvoer.iterdir()) == ["ouder.txt"]


def test_cli_bestaande_uitvoermap_geeft_exit_2(tmp_path):
    (tmp_path / "uit").mkdir()
    assert v.main(["--uitvoer", str(tmp_path / "uit")]) == 2
    assert list((tmp_path / "uit").iterdir()) == []


# --- dry-run ------------------------------------------------------------------------


async def test_zonder_live_wordt_niets_verstuurd_en_geen_sleutel_gelezen(tmp_path):
    nep = NepAI([_antwoord()])
    gelezen = []

    def sleutel():
        gelezen.append(True)
        return SLEUTEL

    uitvoer = tmp_path / "dry"
    data = await v.voer_uit(uitvoer, sleutel=sleutel, binnen=httpx.MockTransport(nep))
    assert nep.verzoeken == []
    assert gelezen == []
    assert data["modus"] == "dry-run"
    assert data["inferenties"] == 0
    assert data["telverzoeken"] == 0
    assert data["opgevangen_zonder_verzending"] == 1
    assert data["stopreden"] is None
    assert sorted(p.name for p in uitvoer.iterdir()) == [
        "herkomst.json",
        "samenvatting.json",
    ]


def test_cli_dryrun_is_standaard(tmp_path):
    assert v.main(["--uitvoer", str(tmp_path / "dry")]) == 0
    herkomst = json.loads((tmp_path / "dry" / "herkomst.json").read_text())
    assert herkomst["modus"] == "dry-run"
    assert herkomst["aantal"] == 5


async def test_herkomst_bindt_script_contract_dienst_en_systeemprompt(tmp_path):
    from services.validation.int02_assessment_service import (
        bouw_int02_prompt,
        laad_int02_norm,
    )

    uitvoer = tmp_path / "dry"
    await v.voer_uit(uitvoer)
    herkomst = json.loads((uitvoer / "herkomst.json").read_text())

    def sha(pad):
        return hashlib.sha256(pad.read_bytes()).hexdigest()

    assert herkomst["script_sha256"] == sha(SCRIPT)
    assert herkomst["contract_sha256"] == sha(ROOT / "src/domain/int02/contract.py")
    assert herkomst["dienst_sha256"] == sha(
        ROOT / "src/services/validation/int02_assessment_service.py"
    )
    systeem, _ = bouw_int02_prompt(
        v.runner.lees_invoer(C107["invoer"]), laad_int02_norm()
    )
    assert (
        herkomst["systeemprompt_sha256"]
        == hashlib.sha256(systeem.encode("utf-8")).hexdigest()
    )
    assert len(herkomst["git_head"] or "") == 40
    assert herkomst["model"] == "claude-opus-5"
    assert herkomst["profiel_id"] == "def835-kwalificatieproef-opus5-v1"
    assert herkomst["promptversie"] == "def835-int02-prompt/6"
    # Het script legt de actieve contractversie vast. De live-meting van
    # 07-10-2026 liep onder /2 (live-v1/herkomst.json); sinds besluit 16 is het /4,
    # sinds besluit 22 /5.
    assert herkomst["contractversie"] == "def835-int02-assessment/5"
    assert herkomst["limieten"]["max_uitvoertokens"] == 6000
    assert herkomst["limieten"]["deadline_seconden"] == 120.0
    assert "label" not in json.dumps(herkomst)


def _v5_payload_c107() -> dict:
    """De vastgelegde v5-payload van C107 (`kwalificatie-payloads-v5.json`)."""
    pad = O2 / "goldset-freeze-v1" / "kwalificatie-payloads-v5.json"
    [geval] = [
        g for g in json.loads(pad.read_text("utf-8"))["gevallen"] if g["id"] == "C107"
    ]
    ruw = geval["payload"].encode("utf-8")
    assert hashlib.sha256(ruw).hexdigest() == V5_PAYLOAD_C107
    return json.loads(ruw)


def _met_schema(body: dict) -> None:
    """Besluit 14 en 16 (prompt /5) ten opzichte van de v5-payload.

    Erbij: exact het vastgepinde schema. Anders: de systeemprompt (/5) en het
    gebruikersbericht (plus de grondbronsleutels). De overige velden (model,
    limieten, sampling) zijn bytegelijk aan de v5-payload.
    """
    from domain.int02.contract import ANTWOORDSCHEMA, ANTWOORDSCHEMA_SHA256
    from services.ai.base_client import response_schema_sha256
    from services.validation.int02_assessment_service import (
        bouw_int02_prompt,
        laad_int02_norm,
    )

    assert body["output_config"] == {
        "format": {"type": "json_schema", "schema": ANTWOORDSCHEMA}
    }
    schema = body["output_config"]["format"]["schema"]
    assert response_schema_sha256(schema) == ANTWOORDSCHEMA_SHA256
    v5 = _v5_payload_c107()
    systeem, data = bouw_int02_prompt(
        v.runner.lees_invoer(C107["invoer"]), laad_int02_norm()
    )
    assert body["system"] == systeem != v5["system"]
    assert body["messages"] == [{"role": "user", "content": data}] != v5["messages"]
    gewijzigd = {"output_config", "system", "messages"}
    zonder = {k: w for k, w in body.items() if k not in gewijzigd}
    assert zonder == {k: w for k, w in v5.items() if k not in gewijzigd}


async def test_dryrun_payload_is_niet_meer_die_van_kwalificatieproef_v5(tmp_path):
    # Bewust gesprongen struikeldraad: onder prompt /4 reist het schema mee,
    # dus de variatiemeting van 07-10-2026 (v5-payload) is niet meer
    # bytevergelijkbaar met de actuele keten.
    uitvoer = tmp_path / "dry"
    await v.voer_uit(uitvoer)
    herkomst = json.loads((uitvoer / "herkomst.json").read_text())
    assert herkomst["payload_sha256"] != V5_PAYLOAD_C107


async def test_live_verstuurt_v5_payload_met_prompt_vijf_en_schema(tmp_path):
    nep = NepAI([_antwoord()])
    await _live(tmp_path / "live", nep, aantal=1)
    [verzoek] = nep.inferenties()
    ruw = json.dumps(verzoek["body"])
    # Geen geval-ID en geen label in het verzoek.
    assert "C107" not in ruw and "review_required" not in ruw
    _met_schema(verzoek["body"])
    [run] = _runs(tmp_path / "live")
    assert run["payload_sha256"] != V5_PAYLOAD_C107


# --- live met nep-AI ----------------------------------------------------------------


async def test_live_vijf_runs_alleen_c107_zonder_sleutel_in_uitvoer(tmp_path, caplog):
    nep = NepAI([_antwoord() for _ in range(5)])
    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, nep)
    assert data["aantal_uitgevoerd"] == 5
    assert data["inferenties"] == 5
    assert data["telverzoeken"] == 5
    assert data["stopreden"] is None
    assert data["telling"] == {"review_required/insufficient_information": 5}
    assert data["kosten_usd_conservatief"] == pytest.approx(5 * 0.02832)
    # Elk verzoek bevat uitsluitend de invoer van C107 en haar grondbronsleutels.
    sleutels = list(grondbronnen(maak_invoer(**C107["invoer"])))
    for verzoek in nep.inferenties():
        [bericht] = verzoek["body"]["messages"]
        assert json.loads(bericht["content"]) == {
            "invoer": C107["invoer"],
            "grondbronnen": sleutels,
        }
    runs = _runs(uitvoer)
    assert [r["run"] for r in runs] == [1, 2, 3, 4, 5]
    eerste = runs[0]
    assert eerste["verdict"] == "insufficient_information"
    assert eerste["uncertainty"] == "decisive"
    assert eerste["vraag_gesteld"] is True
    assert (
        eerste["passages"][0]["quote"] == C107["modelrespons"]["passages"][0]["quote"]
    )
    # Bekende beperking van het afgeronde meetscript (v1): het legt de /3-velden
    # `function` en `ground` vast; onder /4 levert het model `kernvorm` en
    # `bronfuncties`, die het script niet registreert.
    assert eerste["passages"][0]["function"] is None
    assert eerste["usage"] == {"input_tokens": 3574, "output_tokens": 418}
    assert eerste["gerapporteerd_model"] == "claude-opus-5"
    assert eerste["promptversie"] == "def835-int02-prompt/6"
    assert eerste["contractversie"] == "def835-int02-assessment/5"
    for bestand in uitvoer.iterdir():
        assert SLEUTEL not in bestand.read_text()
    assert SLEUTEL not in caplog.text


async def test_kostenstop_stopt_voor_verzending(tmp_path):
    # 5.000 uitvoertokens: $0,1429 per call. Na 2 calls ($0,2857) past de volle
    # reservering ($0,23) niet meer onder $0,50; call 3 wordt niet verstuurd.
    nep = NepAI([_antwoord(uitvoer=5000) for _ in range(5)])
    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, nep)
    assert data["stopreden"] == "kostenstop"
    assert data["inferenties"] == 2
    assert len(nep.inferenties()) == 2
    assert len(_runs(uitvoer)) == 2
    assert data["kosten_usd_conservatief"] <= v.KOSTENSTOP_USD


async def test_geen_herhaling_na_providerfout(tmp_path):
    fout = httpx.Response(500, json={"type": "error", "error": {"type": "api_error"}})
    nep = NepAI([fout, _antwoord(), _antwoord()])
    uitvoer = tmp_path / "live"
    data = await _live(uitvoer, nep, aantal=3)
    assert len(nep.inferenties()) == 1
    assert data["inferenties"] == 1
    assert data["aantal_uitgevoerd"] == 1
    assert data["stopreden"] is not None
    [run] = _runs(uitvoer)
    assert run["status"] == "error"
    assert run["uitkomst"].startswith("error/")
    # Zonder betrouwbare boeking telt de volle reservering.
    assert data["kosten_usd_conservatief"] == pytest.approx(0.23)


async def test_tweede_poging_binnen_een_run_wordt_niet_verstuurd(tmp_path, monkeypatch):
    """Ook als de keten zelf zou herhalen: maximaal één inferentie per run."""
    nep = NepAI([_antwoord(), _antwoord()])
    echte_bouw = v.runner._bouw_dienst

    def bouw_met_herhaling(*args, **kwargs):
        dienst, http = echte_bouw(*args, **kwargs)
        assess = dienst.assess

        async def tweemaal(invoer, **kw):
            await assess(invoer, **kw)
            return await assess(invoer, **kw)

        dienst.assess = tweemaal
        return dienst, http

    # Ook de dry-run-voorbereiding vangt dan tweemaal dezelfde payload op;
    # dat verstuurt niets en verandert de payloadhash niet.
    monkeypatch.setattr(v.runner, "_bouw_dienst", bouw_met_herhaling)
    data = await _live(tmp_path / "live", nep, aantal=2)
    assert len(nep.inferenties()) == 1
    assert data["stopreden"] == "inferentielimiet"
    # De ene verstuurde call blijft conservatief geboekt.
    assert data["kosten_usd_conservatief"] == pytest.approx(0.02832)
