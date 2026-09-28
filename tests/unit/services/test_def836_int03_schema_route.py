"""DEF-836 P1 — native JSON-schema-uitvoer voor INT-03 door de échte dienstroute.

Echte `Int03AssessmentService` → echte `AIServiceV2` → echte `AsyncGPTClient`
→ echte `AnthropicClient` → echte `AsyncAnthropic`-SDK. Alleen de modelgrens
is vervangen: een `httpx.MockTransport` onder de SDK legt elk HTTP-request vast
en geeft een geplande Messages-respons. Geen netwerk, geen sleutel, geen model.

Bewezen (besluitnotitie-v3 §3 en §5, opdracht P1 punten 1–8):

* de schema-opt-in bereikt de SDK-body als ``output_config.format`` met exact
  het INT-03-antwoordschema, in de vastgelegde eigenschapsvolgorde, zonder
  hashveld; zonder opt-in ontbreekt ``output_config`` (andere gebruikers);
* het schema is gesloten, alle velden verplicht, enums/nullability behouden;
* exacte capability: alleen anthropic / https://api.anthropic.com /
  claude-opus-5 / thinking disabled; Opus 5.5, een onbekend suffix, een
  ``ANTHROPIC_BASE_URL``-omleiding, thinking niet uit of OpenAI geven vóór
  verzending een technische fout (nul requests);
* alleen ``end_turn`` met één tekstblok wordt inhoudelijk verwerkt; elke andere
  of ontbrekende stopreden, een extra blok, een ongeldige enum, een ontbrekend
  veld, twee objecten, een inconsistent oordeel of een verzonnen citaat is een
  technische fout zonder oordeel;
* promptversie ``int03-assess/3`` met het exacte formaatslot; normhash en
  contract ongewijzigd; /1 en /2 historisch; schemahash lokaal berekend,
  gepind en gecontroleerd tegen het werkelijk verzonden schema; schema in de
  cachesleutels;
* gevraagd en gemeld model apart; nul gestapelde retries; geen aanroep bij
  lege invoer.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from anthropic import AsyncAnthropic

from domain.int03.contract import (
    ANTWOORDSCHEMA,
    ANTWOORDSCHEMA_SHA256,
    CONTRACTVERSIE,
    VERDICT_FAIL,
    VERDICT_PASS,
    VERDICTS,
    VERWIJZING_DUIDELIJK,
    VERWIJZING_MEERDUIDIG,
    VERWIJZINGSSTATUSSEN,
    bereken_int03_vingerafdruk,
    valideer_beoordeling,
)
from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import (
    AIStructuredOutputUnsupportedError,
    ChatMessage,
    ChatResponse,
    response_schema_sha256,
)
from services.ai.model_router import ModelRouter
from services.ai.openai_client import OpenAIClient
from services.ai_service_v2 import AIServiceV2
from services.validation.int03_assessment_service import Int03AssessmentService
from utils.async_api import AsyncGPTClient, RateLimitConfig

pytestmark = [pytest.mark.unit]

_REPO = Path(__file__).resolve().parents[3]
#: Synthetische sleutel; bereikt geen netwerk (MockTransport).
_SLEUTEL = "sk-ant-offline-def836-000000000000"
_ANTHROPIC = "https://api.anthropic.com"
#: Door de provider gemeld model (`response.model`), bewust ≠ het gevraagde.
GEMELD_MODEL = "claude-opus-5-gemeld-offline"
VOLGORDE = ["references", "reason", "verdict", "question", "uncertainty"]

BEGRIP = "proefbegrip"
TEKST = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd."
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Organisatie"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
TOELICHTING = "Synthetische bedoelde betekenis van het proefbegrip."
#: Marker in de modeltekst: mag nooit in een log belanden (geen ruwe logging).
MARKER = "Voorbeeldnaam-DEF836"

#: Letterlijk uit verwerking-codex-v1.md, "Exacte vervanging van het formaatslot".
FORMAATSLOT = (
    "Lever één beoordeling volgens het meegegeven uitvoerschema, zonder tekst "
    "buiten het object of een tweede antwoord. Alle inhoudelijke regels hierboven "
    "blijven gelden. Geef in de velden de beoordeling van de definitie, geen "
    "uitleg over JSON of het schema.\n"
    "\n"
    "Betekenis van de velden:\n"
    "- references: de beoordeelde woorden. Elk item bevat word, passage, status, "
    "reading en candidates.\n"
    "- word: het letterlijke woord uit de definitie.\n"
    "- passage: een letterlijk fragment uit de definitie waarin dat woord staat.\n"
    "- status: de toepasselijke waarde uit het schema volgens de regels hierboven.\n"
    "- reading: interpretatie van het antecedent, of waarom het woord niet "
    "verwijzend is.\n"
    "- candidates: een lijst met per kandidaat quote, een letterlijk fragment uit "
    "de definitie, en reason, waarom die kandidaat plausibel is. Bij non_referring "
    "en no_antecedent is de lijst leeg.\n"
    "- reason: korte inhoudelijke onderbouwing in twee tot vier zinnen.\n"
    "- verdict: pass, fail of insufficient_information, overeenkomstig de "
    "verwijzingen.\n"
    "- question: precies één vraag als één zin eindigend op een vraagteken; "
    "verplicht bij insufficient_information, optioneel bij fail, anders null.\n"
    "- uncertainty: resterende onzekerheid, of null."
)


def _oordeel(**over: Any) -> dict[str, Any]:
    oordeel = {
        "references": [
            {
                "word": "het",
                "passage": "waardoor het volledig kan worden begrepen",
                "status": VERWIJZING_MEERDUIDIG,
                "reading": "twee plausibele lezingen",
                "candidates": [
                    {"quote": "Geheel", "reason": "onzijdig onderwerp"},
                    {"quote": "gebeurtenis", "reason": f"dichtbij ({MARKER})"},
                ],
            }
        ],
        "reason": f"'het' kan naar 'Geheel' of 'gebeurtenis' verwijzen ({MARKER}).",
        "verdict": VERDICT_FAIL,
        "question": None,
        "uncertainty": None,
    }
    oordeel.update(over)
    return oordeel


def _bericht(
    tekst: str | list[dict[str, Any]],
    *,
    stop_reason: str | None = "end_turn",
    model: str = GEMELD_MODEL,
) -> dict[str, Any]:
    """Een Messages-API-respons zoals de SDK die van de server ontvangt."""
    inhoud = [{"type": "text", "text": tekst}] if isinstance(tekst, str) else tekst
    return {
        "id": "msg_offline_def836",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": inhoud,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 11, "output_tokens": 22},
    }


class SDKGrens:
    """De modelgrens onder de échte SDK: legt elk request vast (methode, URL,
    body) en geeft per request de volgende geplande respons."""

    def __init__(self, *antwoorden: Any) -> None:
        self.antwoorden = list(antwoorden)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        antwoord = self.antwoorden.pop(0) if self.antwoorden else _oordeel()
        if isinstance(antwoord, httpx.Response):
            return antwoord
        if not (isinstance(antwoord, dict) and antwoord.get("type") == "message"):
            antwoord = _bericht(json.dumps(antwoord, ensure_ascii=False))
        return httpx.Response(200, json=antwoord)

    @property
    def bodies(self) -> list[dict[str, Any]]:
        # json.loads behoudt de sleutelvolgorde van de verzonden bytes.
        return [json.loads(r.content) for r in self.requests]


def _routing() -> dict[str, Any]:
    """`model_routing` uit de echte config.yaml (capabilities incl. P1)."""
    config = yaml.safe_load((_REPO / "config" / "config.yaml").read_text("utf-8"))
    return deepcopy(config["model_routing"])


@pytest.fixture
def anthropic_actief(monkeypatch):
    # De actieve provider komt anders uit de omgeving/ConfigManager.
    monkeypatch.setattr(
        ModelRouter, "active_provider", property(lambda self: "anthropic")
    )
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)


def _router(model: str = "claude-opus-5", routing: dict | None = None) -> ModelRouter:
    config = routing if routing is not None else _routing()
    config["providers"] = {
        "anthropic": {"critical": model, "standard": model},
        "openai": {"critical": "gpt-5.2", "standard": "gpt-5-mini"},
    }
    return ModelRouter(config)


def _anthropic(grens: SDKGrens, router: ModelRouter) -> AnthropicClient:
    client = AnthropicClient(
        api_key=_SLEUTEL, timeout=5.0, max_retries=0, model_router=router
    )
    # Alleen de transport onder de echte SDK; base_url blijft de SDK-default
    # of de omgevingswaarde (ANTHROPIC_BASE_URL) — precies wat de client ziet.
    client._sdk_opties["http_client"] = httpx.AsyncClient(
        transport=httpx.MockTransport(grens)
    )
    client._client = AsyncAnthropic(**client._sdk_opties)
    return client


def _keten(
    grens: SDKGrens,
    *,
    model: str = "claude-opus-5",
    routing: dict | None = None,
    ai_client: Any | None = None,
) -> tuple[Int03AssessmentService, AIServiceV2]:
    router = _router(model, routing)
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True,
        ai_client=ai_client if ai_client is not None else _anthropic(grens, router),
        model_router=router,
    )
    return Int03AssessmentService(ai, model_router=router), ai


async def _assess(service: Int03AssessmentService, *, tekst: str = TEKST):
    beoordeling = await service.assess(
        BEGRIP, tekst, CONTEXT, toelichting=TOELICHTING, correlation_id="def836-p1"
    )
    return beoordeling.als_dict()


def _alle_sleutels(waarde: Any) -> list[str]:
    if isinstance(waarde, dict):
        return [k for k, v in waarde.items() for k in (k, *_alle_sleutels(v))]
    if isinstance(waarde, list):
        return [k for item in waarde for k in _alle_sleutels(item)]
    return []


def _ordegevoelige_hash(schema: Any) -> str:
    return hashlib.sha256(
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


# --- 1. doorvoer tot in de SDK-body -------------------------------------------


async def test_sdk_body_draagt_exact_het_antwoordschema_zonder_hashveld(
    anthropic_actief,
):
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    doc = await _assess(service)

    assert len(grens.requests) == 1
    request = grens.requests[0]
    assert request.method == "POST"
    assert request.url.scheme == "https"
    assert request.url.host == "api.anthropic.com"
    assert request.url.path == "/v1/messages"
    body = grens.bodies[0]
    assert body["model"] == "claude-opus-5"
    assert body["thinking"] == {"type": "disabled"}
    assert "temperature" not in body
    assert body["max_tokens"] == 5000
    assert body["output_config"] == {
        "format": {"type": "json_schema", "schema": ANTWOORDSCHEMA}
    }
    verzonden = body["output_config"]["format"]["schema"]
    assert list(verzonden["properties"]) == VOLGORDE
    assert verzonden["required"] == VOLGORDE
    # De schemahash blijft lokaal: geen ongedocumenteerd veld naar de provider.
    assert not any("sha" in k.lower() for k in _alle_sleutels(body))
    assert ANTWOORDSCHEMA_SHA256 not in request.content.decode("utf-8")
    # Het werkelijk verzonden schema (bytes van het request) heeft de gepinde hash.
    assert _ordegevoelige_hash(verzonden) == ANTWOORDSCHEMA_SHA256

    assert doc["status"] == "assessed", doc["error"]
    assert doc["prompt_version"] == "int03-assess/3"
    assert doc["contract_version"] == CONTRACTVERSIE == "int03/1"
    assert doc["input"]["response_schema_sha256"] == ANTWOORDSCHEMA_SHA256
    assert doc["judgment"]["verdict"] == VERDICT_FAIL


async def test_systeemprompt_draagt_exact_het_formaatslot_en_geen_oud_sjabloon(
    anthropic_actief,
):
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    await _assess(service)
    systeem = grens.bodies[0]["system"]
    assert systeem.count(FORMAATSLOT) == 1
    assert systeem.endswith(FORMAATSLOT)
    # Norm-, status- en citaatregels blijven vóór het slot staan.
    assert systeem.index("Herschrijf de definitie niet.") < systeem.index(FORMAATSLOT)
    assert "Norm INT-03 (uit het regelrecord)" in systeem
    # Het oude formaatslot (/2) is volledig vervangen.
    for oud in (
        "Antwoord uitsluitend met één JSON-object",
        "Lever precies één definitief JSON-object.",
        "Controleer vóór verzending",
        '"verdict": "pass|fail|insufficient_information"',
    ):
        assert oud not in systeem, oud
    assert TEKST in grens.bodies[0]["messages"][0]["content"]


async def test_zonder_opt_in_gaat_er_geen_output_config_naar_de_sdk(anthropic_actief):
    grens = SDKGrens(_bericht("vrije tekst"))
    router = _router()
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=1),
        use_cache=False,
        ai_client=_anthropic(grens, router),
        model_router=router,
    )
    resultaat = await ai.generate_definition(prompt="p", task_type="definition_core")
    assert resultaat.text == "vrije tekst"
    (body,) = grens.bodies
    assert "output_config" not in body
    assert set(body) == {"model", "max_tokens", "thinking", "messages"}
    # Metadata van andere routes blijft ongewijzigd: alleen de stopreden.
    assert set(resultaat.metadata) <= {"stop_reason", "tokens_estimated"}


# --- 2. het schema uit het contract --------------------------------------------


def _objecten(schema: Any) -> list[dict[str, Any]]:
    if isinstance(schema, dict):
        eigen = [schema] if schema.get("type") == "object" else []
        return eigen + [o for v in schema.values() for o in _objecten(v)]
    if isinstance(schema, list):
        return [o for item in schema for o in _objecten(item)]
    return []


def test_antwoordschema_is_gesloten_volledig_verplicht_en_behoudt_enums():
    objecten = _objecten(ANTWOORDSCHEMA)
    assert len(objecten) == 3  # beoordeling, verwijzing, kandidaat
    for obj in objecten:
        assert obj["additionalProperties"] is False
        assert obj["required"] == list(obj["properties"])
    beoordeling = ANTWOORDSCHEMA["properties"]
    assert list(beoordeling) == VOLGORDE
    verwijzing = beoordeling["references"]["items"]["properties"]
    assert list(verwijzing) == ["word", "passage", "status", "reading", "candidates"]
    kandidaat = verwijzing["candidates"]["items"]["properties"]
    assert list(kandidaat) == ["quote", "reason"]
    assert set(beoordeling["verdict"]["enum"]) == set(VERDICTS)
    assert set(verwijzing["status"]["enum"]) == set(VERWIJZINGSSTATUSSEN)
    for veld in ("question", "uncertainty"):
        assert beoordeling[veld] == {"anyOf": [{"type": "string"}, {"type": "null"}]}
    # Geen nieuwe semantische eis: reading mag leeg, geen minimum aantallen.
    assert verwijzing["reading"] == {"type": "string"}
    tekst = json.dumps(ANTWOORDSCHEMA)
    for eis in ("minLength", "minItems", "maxItems", "pattern", "default"):
        assert eis not in tekst, eis


def test_schemahash_is_ordegevoelig_en_gepind():
    assert re.fullmatch(r"[0-9a-f]{64}", ANTWOORDSCHEMA_SHA256)
    assert response_schema_sha256(ANTWOORDSCHEMA) == ANTWOORDSCHEMA_SHA256
    assert _ordegevoelige_hash(ANTWOORDSCHEMA) == ANTWOORDSCHEMA_SHA256
    omgekeerd = deepcopy(ANTWOORDSCHEMA)
    omgekeerd["properties"] = dict(reversed(list(omgekeerd["properties"].items())))
    assert response_schema_sha256(omgekeerd) != ANTWOORDSCHEMA_SHA256


# --- 3. exacte capability vóór verzending ----------------------------------------


@pytest.mark.parametrize(
    "model",
    ["claude-opus-5-5", "claude-opus-5-20270101", "claude-opus-5x", "CLAUDE-OPUS-5"],
)
async def test_ander_model_dan_exact_claude_opus_5_gaat_niet_naar_de_sdk(
    anthropic_actief, model
):
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens, model=model)
    doc = await _assess(service)
    assert grens.requests == []
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "unsupported_configuration"
    assert doc["judgment"] is None


@pytest.mark.parametrize(
    "base_url",
    [
        "https://proxy.voorbeeld.test",
        "http://api.anthropic.com",
        "https://api.anthropic.com.voorbeeld.test",
        "https://api.anthropic.com:8443",
        "https://api.anthropic.com/extra",
    ],
)
async def test_omgevingsomleiding_van_de_base_url_wordt_voor_verzending_geweigerd(
    anthropic_actief, monkeypatch, base_url
):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", base_url)
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert grens.requests == []
    assert doc["error"]["type"] == "unsupported_configuration"


async def test_expliciete_standaard_base_url_in_de_omgeving_is_toegestaan(
    anthropic_actief, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", _ANTHROPIC)
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1
    assert doc["status"] == "assessed", doc["error"]


async def test_thinking_niet_uitgezet_gaat_niet_naar_de_sdk(anthropic_actief):
    routing = _routing()
    routing["capabilities"]["anthropic"]["thinking_default_on"]["model_families"] = [
        "sonnet-5"
    ]
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens, routing=routing)
    doc = await _assess(service)
    assert grens.requests == []
    assert doc["error"]["type"] == "unsupported_configuration"


async def test_openai_met_schema_geeft_een_technische_fout_voor_de_modelcall(
    anthropic_actief, monkeypatch
):
    monkeypatch.setattr(ModelRouter, "active_provider", property(lambda self: "openai"))
    grens = SDKGrens()
    openai = OpenAIClient(api_key="sk-offline-def836-00000000", max_retries=0)
    openai._sdk_opties["http_client"] = httpx.AsyncClient(
        transport=httpx.MockTransport(grens)
    )
    from openai import AsyncOpenAI

    openai._client = AsyncOpenAI(**openai._sdk_opties)
    service, _ = _keten(grens, ai_client=openai)
    doc = await _assess(service)
    assert grens.requests == []
    assert doc["error"]["type"] == "unsupported_configuration"
    with pytest.raises(AIStructuredOutputUnsupportedError):
        await openai.chat_completion(
            [ChatMessage(role="user", content="x")],
            model="gpt-5.2",
            response_schema=ANTWOORDSCHEMA,
        )
    assert grens.requests == []


def test_router_capability_is_exact_en_fail_safe(anthropic_actief):
    router = _router()
    ok = {"endpoint": _ANTHROPIC, "thinking": "disabled"}
    assert router.supports_structured_outputs("claude-opus-5", "anthropic", **ok)
    for model in ("claude-opus-5-5", "claude-opus-5-1", "opus-5", "claude-sonnet-5"):
        assert not router.supports_structured_outputs(model, "anthropic", **ok)
    assert not router.supports_structured_outputs("claude-opus-5", "openai", **ok)
    assert not router.supports_structured_outputs(
        "claude-opus-5", "anthropic", endpoint=_ANTHROPIC, thinking=None
    )
    assert not router.supports_structured_outputs(
        "claude-opus-5", "anthropic", endpoint="https://ander.test", thinking="disabled"
    )
    assert not router.supports_structured_outputs("claude-opus-5", "anthropic")
    kapot = _routing()
    kapot["capabilities"]["anthropic"]["structured_outputs"]["models"] = "claude-opus-5"
    assert not _router(routing=kapot).supports_structured_outputs(
        "claude-opus-5", "anthropic", **ok
    )


def test_config_legt_de_p1_combinatie_exact_vast_met_bron():
    capability = _routing()["capabilities"]["anthropic"]["structured_outputs"]
    assert capability["models"] == ["claude-opus-5"]
    assert capability["endpoints"] == [_ANTHROPIC]
    assert capability["thinking"] == "disabled"
    assert capability["source"].startswith("https://platform.claude.com/")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", capability["checked_at"])
    assert "model_families" not in capability  # geen substring-familie


def test_actieve_configuratie_levert_de_capability_via_from_config(
    anthropic_actief,
):
    router = ModelRouter.from_config()
    assert router.supports_structured_outputs(
        "claude-opus-5", "anthropic", endpoint=_ANTHROPIC, thinking="disabled"
    )


# --- 4. alleen end_turn met één tekstblok ------------------------------------------


@pytest.mark.parametrize(
    "stop_reason",
    ["refusal", "stop_sequence", "tool_use", "pause_turn", "iets_onbekends", None],
)
async def test_andere_of_ontbrekende_stopreden_is_technische_fout(
    anthropic_actief, caplog, stop_reason
):
    caplog.set_level(logging.DEBUG)
    geldig = json.dumps(_oordeel(), ensure_ascii=False)
    grens = SDKGrens(
        _bericht(geldig, stop_reason=stop_reason),
        _bericht(geldig, stop_reason=stop_reason),
    )
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1  # geen retry
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "malformed_response"
    assert "stop_reason" in doc["error"]["message"]
    assert doc["judgment"] is None
    assert MARKER not in caplog.text
    # Een technische fout wordt nooit gecachet.
    await _assess(service)
    assert len(grens.requests) == 2


async def test_afgekapt_antwoord_is_truncated_response(anthropic_actief):
    grens = SDKGrens(_bericht('{"references": [', stop_reason="max_tokens"))
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1
    assert doc["error"]["type"] == "truncated_response"
    assert doc["judgment"] is None


@pytest.mark.parametrize(
    "inhoud",
    [
        [
            {"type": "text", "text": json.dumps(_oordeel(), ensure_ascii=False)},
            {"type": "text", "text": json.dumps(_oordeel(), ensure_ascii=False)},
        ],
        [
            {"type": "thinking", "thinking": "denken", "signature": "sig"},
            {"type": "text", "text": json.dumps(_oordeel(), ensure_ascii=False)},
        ],
        [],
    ],
    ids=["twee-tekstblokken", "denkblok-plus-tekst", "geen-blok"],
)
async def test_afwijkende_responsvorm_is_technische_fout(anthropic_actief, inhoud):
    grens = SDKGrens(_bericht(inhoud))
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "malformed_response"
    assert doc["judgment"] is None


def _zonder(veld: str) -> dict[str, Any]:
    oordeel = _oordeel()
    del oordeel[veld]
    return oordeel


@pytest.mark.parametrize(
    "tekst",
    [
        json.dumps(_oordeel(verdict="Fail")),
        json.dumps(_oordeel(verdict="FAIL")),
        json.dumps(_zonder("uncertainty")),
        json.dumps({**_oordeel(), "score": 3}),
        json.dumps(_oordeel()) + "\n" + json.dumps(_oordeel()),
        "Hier is mijn oordeel: " + json.dumps(_oordeel()),
        json.dumps(
            _oordeel(
                references=[
                    {
                        "word": "het",
                        "passage": "waardoor het volledig kan worden begrepen",
                        "status": "Ambiguous",
                        "reading": "",
                        "candidates": [],
                    }
                ]
            )
        ),
    ],
    ids=[
        "enum-hoofdletter",
        "enum-kapitalen",
        "ontbrekend-veld",
        "extra-veld",
        "twee-objecten",
        "proza-ervoor",
        "status-hoofdletter",
    ],
)
async def test_ongeldige_structuur_is_technische_fout_zonder_normalisatie(
    anthropic_actief, tekst
):
    grens = SDKGrens(_bericht(tekst))
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "malformed_response"
    assert doc["judgment"] is None


async def test_inconsistent_oordeel_en_verzonnen_citaat_zijn_technische_fout(
    anthropic_actief,
):
    inconsistent = _oordeel(verdict=VERDICT_PASS)  # ambiguous-verwijzing bij pass
    verzonnen = _oordeel(
        references=[
            {
                "word": "het",
                "passage": "waardoor het volledig kan worden begrepen",
                "status": VERWIJZING_DUIDELIJK,
                "reading": "verwijst naar het geheel",
                "candidates": [{"quote": "niet in de definitie", "reason": "x"}],
            }
        ],
        verdict=VERDICT_PASS,
    )
    grens = SDKGrens(inconsistent, verzonnen)
    service, _ = _keten(grens)
    eerste = await _assess(service)
    tweede = await _assess(service)
    assert eerste["error"]["type"] == "malformed_response"
    assert tweede["error"]["type"] == "unverifiable_evidence"
    assert eerste["judgment"] is None and tweede["judgment"] is None


@pytest.mark.parametrize(
    "omhulling",
    [("```json\n", "\n```"), ("```\n", "\n```"), ("```JSON ", " ```")],
    ids=["json-fence", "kale-fence", "hoofdletters-een-regel"],
)
async def test_codeblok_om_geldig_json_wordt_geweigerd_zonder_retry_of_cache(
    anthropic_actief, omhulling
):
    # DEF-836 R1: ook met end_turn, één tekstblok en een bevestigd schema telt
    # alleen het kale object; het codeblok wordt niet uitgepakt.
    begin, eind = omhulling
    omhuld = begin + json.dumps(_oordeel(), ensure_ascii=False) + eind
    grens = SDKGrens(_bericht(omhuld), _bericht(omhuld))
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1  # één poging, geen retry
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "malformed_response"
    assert doc["judgment"] is None
    assert doc["attribution"]["attempts_observed"] == 1
    assert doc["attribution"]["stop_reason"] == "end_turn"
    assert service._cache == {}  # afgewezen antwoord niet in de INT-03-cache
    tweede = await _assess(service)
    assert len(grens.requests) == 2  # opnieuw toetsen gaat weer naar het model
    assert tweede["error"]["type"] == "malformed_response"


async def test_kaal_json_met_opmaak_blijft_geldig(anthropic_actief):
    # Tegenproef bij R1: witruimte en regeleinden binnen/rond het kale object
    # zijn gewoon JSON en blijven een geldig oordeel opleveren.
    grens = SDKGrens(_bericht("\n" + json.dumps(_oordeel(), indent=2) + "\n"))
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1
    assert doc["status"] == "assessed", doc["error"]


# --- 5/6. binding, cache, gevraagd en gemeld model --------------------------------


async def test_gevraagd_en_gemeld_model_apart_en_binding_actueel(anthropic_actief):
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert doc["attribution"]["provider"] == "anthropic"
    assert doc["attribution"]["model"] == "claude-opus-5"
    assert doc["attribution"]["model_reported"] == GEMELD_MODEL
    assert doc["attribution"]["stop_reason"] == "end_turn"
    assert doc["attribution"]["attempts_observed"] == 1
    fp = bereken_int03_vingerafdruk(BEGRIP, TEKST, CONTEXT, TOELICHTING)
    oordeel, _ = valideer_beoordeling(doc, fp, TEKST, binding=service.binding())
    assert oordeel is not None
    assert service.binding().prompt_version == "int03-assess/3"
    assert service.norm_sha256 == (
        "d2f0cc1c834f36b264f2c82a496e0ff3108aa358e8bc65f518870c6179d3bb2d"
    )
    for oud in ("int03-assess/1", "int03-assess/2"):
        historisch, samenvatting = valideer_beoordeling(
            {**doc, "prompt_version": oud}, fp, TEKST, binding=service.binding()
        )
        assert historisch is None
        assert samenvatting["historical"] is True


async def test_interne_cache_is_gebonden_aan_de_schemarevisie(anthropic_actief):
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    await _assess(service)
    tweede = await _assess(service)
    assert len(grens.requests) == 1
    assert tweede["attribution"]["cached"] is True
    (sleutel,) = list(service._cache)
    assert ANTWOORDSCHEMA_SHA256 in sleutel
    assert "int03-assess/3" in sleutel


async def test_schema_dat_niet_bij_de_pin_hoort_gaat_niet_naar_de_sdk(
    anthropic_actief, monkeypatch
):
    import services.validation.int03_assessment_service as dienst

    omgekeerd = deepcopy(ANTWOORDSCHEMA)
    omgekeerd["properties"] = dict(reversed(list(omgekeerd["properties"].items())))
    monkeypatch.setattr(dienst, "ANTWOORDSCHEMA", omgekeerd)
    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert grens.requests == []
    assert doc["error"]["type"] == "unsupported_configuration"


class SchemaNegerendeAI:
    """Een AI-laag die het schema niet (of een ander schema) bevestigt."""

    def __init__(self, metadata: dict[str, Any]) -> None:
        self.metadata = metadata
        self.calls: list[dict[str, Any]] = []
        self.default_model = "fake"

    async def generate_definition(self, prompt: str, **kwargs: Any):
        from services.interfaces import AIGenerationResult

        self.calls.append(kwargs)
        return AIGenerationResult(
            text=json.dumps(_oordeel()),
            model="claude-opus-5",
            tokens_used=1,
            generation_time=0.0,
            metadata=dict(self.metadata),
        )


@pytest.mark.parametrize(
    "metadata",
    [
        {"stop_reason": "end_turn", "content_block_types": ["text"]},
        {
            "stop_reason": "end_turn",
            "content_block_types": ["text"],
            "response_schema_sha256": "0" * 64,
        },
    ],
    ids=["geen-bevestiging", "ander-schema"],
)
async def test_onbevestigd_of_afwijkend_verzonden_schema_geeft_geen_oordeel(
    anthropic_actief, metadata
):
    ai = SchemaNegerendeAI(metadata)
    service = Int03AssessmentService(ai, model_router=_router())
    doc = await _assess(service)
    assert len(ai.calls) == 1
    assert ai.calls[0]["response_schema"] == ANTWOORDSCHEMA
    assert doc["status"] == "error"
    assert doc["error"]["type"] == "unsupported_configuration"
    assert doc["judgment"] is None


class Provider:
    """Providergrens voor de AI-laag-cachetests; legt de kwargs vast."""

    provider_name = "anthropic"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None, **kw
    ):
        self.calls.append({"model": model, "kw": kw})
        return ChatResponse(
            text="antwoord", tokens_used=1, model=model, stop_reason="end_turn"
        )


class OudeProvider:
    """Providerclient met de signature van vóór P1 (geen `response_schema`)."""

    provider_name = "oud"

    def __init__(self) -> None:
        self.calls = 0

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None,
        max_retries=None,
    ):  # fmt: skip
        self.calls += 1
        return ChatResponse(text="oud", tokens_used=1, model=model)


def _ai(provider: Any, *, use_cache: bool = True) -> AIServiceV2:
    class Router:
        def get_model(self, task_type):
            return "anthropic", "claude-opus-5"

    return AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=use_cache,
        ai_client=provider,
        model_router=Router(),
    )


async def test_ai_laag_cache_onderscheidt_schema_en_eigenschapsvolgorde():
    provider = Provider()
    ai = _ai(provider)
    prompt = f"def836-cache-{time.time_ns()}"
    omgekeerd = deepcopy(ANTWOORDSCHEMA)
    omgekeerd["properties"] = dict(reversed(list(omgekeerd["properties"].items())))

    await ai.generate_definition(prompt=prompt, task_type="validation")
    await ai.generate_definition(prompt=prompt, task_type="validation")
    assert len(provider.calls) == 1  # bestaande cache zonder schema intact
    await ai.generate_definition(
        prompt=prompt, task_type="validation", response_schema=ANTWOORDSCHEMA
    )
    await ai.generate_definition(
        prompt=prompt, task_type="validation", response_schema=omgekeerd
    )
    assert len(provider.calls) == 3
    assert "response_schema" not in provider.calls[0]["kw"]
    assert provider.calls[1]["kw"]["response_schema"] == ANTWOORDSCHEMA
    assert list(provider.calls[2]["kw"]["response_schema"]["properties"]) == list(
        reversed(VOLGORDE)
    )


async def test_asyncgptclient_cache_onderscheidt_schema_en_stuurt_het_alleen_mee():
    provider = Provider()
    client = AsyncGPTClient(rate_limit_config=RateLimitConfig(), client=provider)
    prompt = f"def836-gpt-{time.time_ns()}"
    await client.chat_completion(prompt, model="claude-opus-5", use_cache=True)
    await client.chat_completion(
        prompt, model="claude-opus-5", use_cache=True, response_schema=ANTWOORDSCHEMA
    )
    await client.chat_completion(
        prompt, model="claude-opus-5", use_cache=True, response_schema=ANTWOORDSCHEMA
    )
    assert len(provider.calls) == 2
    assert "response_schema" not in provider.calls[0]["kw"]
    assert provider.calls[1]["kw"]["response_schema"] == ANTWOORDSCHEMA


async def test_bestaande_providerclient_zonder_schema_parameter_blijft_werken():
    provider = OudeProvider()
    resultaat = await _ai(provider, use_cache=False).generate_definition(
        prompt="p", task_type="validation"
    )
    assert resultaat.text == "oud"
    assert provider.calls == 1


# --- 7. nul gestapelde retries en geen aanroep bij lege invoer -----------------------


async def test_serverfout_geeft_precies_een_http_request(anthropic_actief):
    overbelast = httpx.Response(
        529, json={"type": "error", "error": {"type": "overloaded_error"}}
    )
    grens = SDKGrens(overbelast, overbelast, overbelast)
    service, _ = _keten(grens)
    doc = await _assess(service)
    assert len(grens.requests) == 1
    assert doc["status"] == "error"
    assert doc["attribution"]["attempts_observed"] == 1


async def test_lege_invoer_geeft_geen_modelaanroep(anthropic_actief):
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.interfaces import ValidationContext
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    grens = SDKGrens(_oordeel())
    service, _ = _keten(grens)
    orch = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        int03_assessment_service=service,
    )
    for leeg in ("", "   ", "\n\t"):
        await orch.validate_text(BEGRIP, leeg, context=ValidationContext(metadata={}))
    assert grens.requests == []
