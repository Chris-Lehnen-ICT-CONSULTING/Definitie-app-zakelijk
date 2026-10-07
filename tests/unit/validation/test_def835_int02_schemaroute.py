"""DEF-835 besluit 14 (optie A) en 16 — INT-02-antwoordschema via de API.

Bewezen: het vastgepinde antwoordschema is exact de gesloten uitvoervorm van
contract /4 (besluit 16: per passage `kernvorm` en per grondbron een
`function` met citaat, het eigen `verdict` als laatste veld), in die volgorde
en met gesorteerde enums; zijn hash is procesonafhankelijk (ook onder een
andere PYTHONHASHSEED); het blijft binnen de gedocumenteerde grenzen van
structured outputs (≤24 optionele velden, ≤16 unies); schema en
structuurcontrole van de code zijn gelijk over een matrix van bronfunctie- en
kernvormwaarden; de v6-respons van C105 voldoet niet. De dienst stuurt het
schema mee, eist dat de AI-laag het verzonden schema en precies één tekstblok
bevestigt, weigert vóór de aanroep een schema dat niet bij de pin hoort en
meldt een niet-ondersteunde combinatie met een eigen reden zonder verzending.

Niet bewezen: dat de echte API het schema accepteert (pas live, fase 1) of
hoe het model zich onder de grammatica gedraagt.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from anthropic import AsyncAnthropic

from domain.int02 import contract
from domain.int02.contract import (
    DEKKINGEN,
    ONZEKERHEDEN,
    VERDICTS,
    Configuratie,
    Uitvoering,
    beoordeel,
    maak_invoer,
)
from services.ai.anthropic_client import AnthropicClient
from services.ai.base_client import (
    AIStructuredOutputUnsupportedError,
    response_schema_sha256,
)
from services.ai.model_router import ModelRouter
from services.ai_service_v2 import AIServiceV2
from services.interfaces import AIGenerationResult, AIServiceError
from services.validation import int02_assessment_service as dienstmodule
from services.validation.int02_assessment_service import (
    Budget,
    Int02AssessmentService,
    Modelprofiel,
    bouw_int02_prompt,
    laad_int02_norm,
)
from tests.fixtures.def835_int02_v4 import passage, respons_voor_status, uitvoer
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/def835_int02_ontwerpgevallen.json").read_text("utf-8")
)
SLEUTEL = "sk-ant-offline-def835-schema-000000000000"

#: Vastgepinde, volgordegevoelige hash van het INT-02-antwoordschema /4
#: (`services.ai.base_client.response_schema_sha256`, dezelfde functie
#: waarmee de AI-laag het verzonden schema bevestigt).
SCHEMA_SHA256 = "d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715"
#: De pin van het /3-schema (besluit 14, na de Codex-review) en de eerste pin.
VORIGE_SCHEMA_SHA256 = (
    "72adfe7428b67bf0fd999520581f0fc2cbe801101e1e8e6df300179405511f17",
    "2b1ac6a869c0b989287c421ee66d40a204fcca0ffe41c6971d6d0ed896f96191",
)
#: Systeemprompt onder /3 en /4 (test_def835_int02_dienstregel); /5 wijzigt hem.
SYSTEEMPROMPT_V3_SHA256 = (
    "da4a4112b580da2924b5940ac2723ef5e177ad48ef15890b66d8d91f285a7ca6"
)
#: SHA-256 van de systeemprompt van def835-int02-prompt/5 (besluit 16).
SYSTEEMPROMPT_V5_SHA256 = (
    "3047bb1a34f878e77bd434d668d870f0dfcfb92e3e948ac0caee77af9c2d2b70"
)
#: Toegestane sleutelwoorden (subset die structured outputs ondersteunt).
SLEUTELWOORDEN = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "anyOf",
}

_NUL_OF_TEKST = {"anyOf": [{"type": "string"}, {"type": "null"}]}
#: Ontwerp §2.2 letterlijk: eerst de passages met kernvorm en bronfuncties,
#: dan de onderbouwing, als laatste het eigen modelverdict.
VERWACHT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "passages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "kernvorm": {
                        "type": "string",
                        "enum": [
                            "descriptive_act",
                            "discretion_form",
                            "instruction",
                            "no_act",
                            "obligation_form",
                        ],
                    },
                    "bronfuncties": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "bron": {"type": "string"},
                                "function": {
                                    "type": "string",
                                    "enum": [
                                        "actor_prescription",
                                        "criterion",
                                        "derivation",
                                        "discretionary_decision_rule",
                                        "not_a_criterion",
                                        "not_addressed",
                                        "unclear",
                                    ],
                                },
                                "quote": _NUL_OF_TEKST,
                            },
                            "required": ["bron", "function", "quote"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["quote", "kernvorm", "bronfuncties"],
                "additionalProperties": False,
            },
        },
        "reason": {"type": "string"},
        "question": _NUL_OF_TEKST,
        "uncertainty": {"type": "string", "enum": ["decisive", "non_decisive", "none"]},
        "coverage": {"type": "string", "enum": ["complete", "none", "partial"]},
        "scope_reason": _NUL_OF_TEKST,
        "verdict": {
            "type": "string",
            "enum": ["fail", "insufficient_information", "not_applicable", "pass"],
        },
    },
    "required": [
        "passages",
        "reason",
        "question",
        "uncertainty",
        "coverage",
        "scope_reason",
        "verdict",
    ],
    "additionalProperties": False,
}

#: Letterlijk de modeltekst van C105 in kwalificatieproef v6
#: (`kwalificatieproef-v6/regressie-bundel.json`, `antwoorden.C105`): /3-vorm
#: met een extra veld `reason` in de passage.
V6_C105_TEKST = (
    '{"verdict":"fail","passages":[{"quote":"De medewerker laat de aanvrager '
    'toe.","function":"actor_prescription","ground":{"field":"bedoeling",'
    '"ref":null,"quote":"opdracht aan medewerker"},"reason":"De kern schrijft '
    "een actor (de medewerker) een handeling voor in plaats van het begrip "
    "'toelating' af te bakenen met kenmerken of een deterministische afleiding; "
    "de bevestigde bedoeling bevestigt dat het om een opdracht aan de medewerker "
    'gaat."}],"reason":"De enige passage in de kern formuleert geen '
    "begripskenmerken van 'toelating', maar een handeling van een actor; de "
    "bevestigde bedoeling ('opdracht aan medewerker') draagt zelfstandig de "
    "functie als actorvoorschrift. Daarmee functioneert de definitiekern als "
    'handelingsvoorschrift en niet als begripsafbakening.","question":null,'
    '"uncertainty":"none","scope_reason":null,"coverage":"complete"}'
)


def _schema() -> dict[str, Any]:
    schema = getattr(contract, "ANTWOORDSCHEMA", None)
    if not isinstance(schema, dict):
        pytest.fail("domain.int02.contract.ANTWOORDSCHEMA ontbreekt")
    return schema


def _pin() -> str:
    pin = getattr(contract, "ANTWOORDSCHEMA_SHA256", None)
    if not isinstance(pin, str):
        pytest.fail("domain.int02.contract.ANTWOORDSCHEMA_SHA256 ontbreekt")
    return pin


def _structuur(data: Any) -> bool:
    """De structuurcontrole van contract /4 (vorm, typen, enums; geen semantiek)."""
    controle = getattr(contract, "_controleer_structuur_v4", None)
    if controle is None:
        pytest.fail("domain.int02.contract._controleer_structuur_v4 ontbreekt")
    try:
        controle(data)
    except contract._AfwijzingError:
        return False
    return True


# --- een kleine, strikte validator voor de gebruikte schemasubset ------------------


def _type_klopt(waarde: Any, soort: str) -> bool:
    if soort == "object":
        return isinstance(waarde, dict)
    if soort == "array":
        return isinstance(waarde, list)
    if soort == "string":
        return isinstance(waarde, str)
    if soort == "integer":
        # JSON Schema (Draft 2020-12): elk getal zonder breukdeel, dus ook 0.0
        # en 1.0; true/false zijn geen getallen.
        if isinstance(waarde, bool):
            return False
        if isinstance(waarde, float):
            return math.isfinite(waarde) and waarde.is_integer()
        return isinstance(waarde, int)
    if soort == "null":
        return waarde is None
    pytest.fail(f"onbekend type in schema: {soort}")
    return False


def voldoet(waarde: Any, schema: dict[str, Any]) -> bool:
    """Valideer tegen de subset type/properties/required/additionalProperties/
    items/enum/anyOf; elk ander sleutelwoord laat de test falen."""
    onbekend = set(schema) - SLEUTELWOORDEN
    if onbekend:
        pytest.fail(f"validator kent sleutelwoord(en) niet: {sorted(onbekend)}")
    if "anyOf" in schema:
        return any(voldoet(waarde, optie) for optie in schema["anyOf"])
    soort = schema["type"]
    soorten = soort if isinstance(soort, list) else [soort]
    if not any(_type_klopt(waarde, s) for s in soorten):
        return False
    if "enum" in schema and waarde not in schema["enum"]:
        return False
    if isinstance(waarde, dict) and "properties" in schema:
        eigenschappen = schema["properties"]
        if schema.get("additionalProperties") is False and set(waarde) - set(
            eigenschappen
        ):
            return False
        if any(veld not in waarde for veld in schema.get("required", [])):
            return False
        return all(
            voldoet(waarde[veld], eigenschappen[veld])
            for veld in waarde
            if veld in eigenschappen
        )
    if isinstance(waarde, list) and "items" in schema:
        return all(voldoet(item, schema["items"]) for item in waarde)
    return True


def _objecten(schema: Any) -> list[dict[str, Any]]:
    """Alle objectschema's (met properties), diep."""
    gevonden: list[dict[str, Any]] = []
    if isinstance(schema, dict):
        if "properties" in schema:
            gevonden.append(schema)
        for waarde in schema.values():
            gevonden.extend(_objecten(waarde))
    elif isinstance(schema, list):
        for item in schema:
            gevonden.extend(_objecten(item))
    return gevonden


def _schemas(schema: Any) -> list[dict[str, Any]]:
    """Alle (sub)schema's, diep; `properties` is een mapping, geen schema."""
    if not isinstance(schema, dict):
        return []
    gevonden = [schema]
    for sleutel, waarde in schema.items():
        if sleutel == "properties":
            for sub in waarde.values():
                gevonden.extend(_schemas(sub))
        elif sleutel == "items":
            gevonden.extend(_schemas(waarde))
        elif sleutel == "anyOf":
            for sub in waarde:
                gevonden.extend(_schemas(sub))
    return gevonden


def _geldig() -> dict[str, Any]:
    return {
        "passages": [
            {
                "quote": "q",
                "kernvorm": "descriptive_act",
                "bronfuncties": [
                    {"bron": "bron/B1", "function": "criterion", "quote": "c"}
                ],
            }
        ],
        "reason": "r",
        "question": None,
        "uncertainty": "none",
        "coverage": "complete",
        "scope_reason": None,
        "verdict": "pass",
    }


# --- 1. het schema zelf -----------------------------------------------------------


def test_schema_is_exact_de_gesloten_vorm_van_contract_vier():
    schema = _schema()
    assert schema == VERWACHT_SCHEMA
    # Ook de eigenschapsvolgorde (dict-gelijkheid negeert die).
    assert json.dumps(schema) == json.dumps(VERWACHT_SCHEMA)
    assert list(schema["properties"])[-1] == "verdict"  # eigen verdict als laatste


def test_schema_en_contractconstanten_zijn_dezelfde_velden_en_enums():
    schema = _schema()
    top = schema["properties"]
    passage_ = top["passages"]["items"]
    bronfunctie = passage_["properties"]["bronfuncties"]["items"]
    assert set(top) == contract._UITVOERVELDEN
    assert set(passage_["properties"]) == contract._PASSAGEVELDEN_V4
    assert set(bronfunctie["properties"]) == contract._BRONFUNCTIEVELDEN
    for veld, constanten in (
        (top["verdict"], VERDICTS),
        (top["uncertainty"], ONZEKERHEDEN),
        (top["coverage"], DEKKINGEN),
        (passage_["properties"]["kernvorm"], contract.KERNVORMEN),
        (bronfunctie["properties"]["function"], contract.BRONFUNCTIES),
    ):
        assert veld == {"type": "string", "enum": sorted(constanten)}
    # Gesloten en volledig verplicht: elk object.
    for object_ in _objecten(schema):
        assert object_["type"] == "object"
        assert object_["additionalProperties"] is False
        assert object_["required"] == list(object_["properties"])


def test_bronfuncties_zijn_de_functies_van_drie_plus_not_a_criterion_en_zwijgen():
    verwacht = contract.FUNCTIES | {"not_a_criterion", "not_addressed"}
    assert verwacht == contract.BRONFUNCTIES
    assert len(contract.KERNVORMEN) == 5


def test_schema_blijft_binnen_de_grenzen_van_structured_outputs():
    schema = _schema()
    sleutelwoorden = {k for sub in _schemas(schema) for k in sub}
    # Geen min/maxLength, pattern, format, $ref of andere sleutelwoorden.
    assert sleutelwoorden <= SLEUTELWOORDEN
    optioneel = sum(
        len(o["properties"]) - len(o["required"]) for o in _objecten(schema)
    )
    unies = sum(
        1
        for sub in _schemas(schema)
        if "anyOf" in sub or isinstance(sub.get("type"), list)
    )
    assert optioneel <= 24
    assert unies <= 16
    # Unies: question, scope_reason en bronfuncties[].quote.
    assert (optioneel, unies) == (0, 3)


def test_schemahash_is_gepind_en_volgordegevoelig():
    schema = _schema()
    assert response_schema_sha256(schema) == _pin() == SCHEMA_SHA256
    assert SCHEMA_SHA256 not in VORIGE_SCHEMA_SHA256  # /4 is een ander schema
    omgekeerd = deepcopy(schema)
    omgekeerd["properties"] = dict(reversed(list(schema["properties"].items())))
    assert omgekeerd == schema  # dict-gelijk, maar
    assert response_schema_sha256(omgekeerd) != SCHEMA_SHA256  # ander schema


_SUBPROCES = (
    "import json; "
    "from domain.int02 import contract as c; "
    "from services.ai.base_client import response_schema_sha256 as h; "
    "print(json.dumps({'hash': h(c.ANTWOORDSCHEMA), "
    "'pin': c.ANTWOORDSCHEMA_SHA256, 'rauw': list(c.BRONFUNCTIES)}))"
)


def test_schemahash_is_stabiel_in_subprocessen_met_andere_hashseed():
    """Frozenset-volgorde hangt af van PYTHONHASHSEED; het schema niet."""
    uitkomsten = []
    for seed in ("0", "1", "2", "3", "4", "5", "6", "7"):
        omgeving = {
            **os.environ,
            "PYTHONHASHSEED": seed,
            "PYTHONPATH": str(ROOT / "src"),
        }
        proces = subprocess.run(
            [sys.executable, "-c", _SUBPROCES],
            capture_output=True,
            text=True,
            env=omgeving,
            cwd=ROOT,
            timeout=60,
            check=False,
        )
        assert proces.returncode == 0, proces.stderr[-2000:]
        uitkomsten.append(json.loads(proces.stdout.strip().splitlines()[-1]))
    assert {u["hash"] for u in uitkomsten} == {SCHEMA_SHA256}
    assert {u["pin"] for u in uitkomsten} == {SCHEMA_SHA256}
    # De test discrimineert: de ruwe frozenset-volgorde verschilt wél per seed,
    # dus een ongesorteerde enum zou hier een andere hash geven.
    assert len({tuple(u["rauw"]) for u in uitkomsten}) > 1


# --- 2. schema en code over een matrix ------------------------------------------------


def _bronfunctie(bron: Any, functie: Any, quote: Any) -> dict[str, Any]:
    data = _geldig()
    data["passages"][0]["bronfuncties"] = [
        {"bron": bron, "function": functie, "quote": quote}
    ]
    return data


def test_schema_en_structuurcontrole_zijn_gelijk_over_de_bronfunctiematrix():
    functies = sorted(contract.BRONFUNCTIES) + ["criterium", "", None, 1, True]
    for bron in ("bron/B1", "bedoeling", "", " ", None, 1, True, ["bron/B1"]):
        for functie in functies:
            for quote in (None, "x", "", 1, True, ["x"]):
                data = _bronfunctie(bron, functie, quote)
                assert voldoet(data, _schema()) == _structuur(data), (
                    bron,
                    functie,
                    quote,
                )


@pytest.mark.parametrize(
    "kernvorm",
    sorted(
        {
            "descriptive_act",
            "discretion_form",
            "instruction",
            "no_act",
            "obligation_form",
        }
    )
    + ["imperative", "", None, 1, ["no_act"]],
    ids=repr,
)
def test_schema_en_structuurcontrole_zijn_gelijk_over_de_kernvormen(kernvorm):
    data = _geldig()
    data["passages"][0]["kernvorm"] = kernvorm
    assert voldoet(data, _schema()) == _structuur(data)


def test_bronfunctieobject_zonder_veld_of_met_extra_veld_is_overal_ongeldig():
    for wijziging in (
        lambda bf: bf.pop("quote"),
        lambda bf: bf.pop("bron"),
        lambda bf: bf.pop("function"),
        lambda bf: bf.update({"start": 0}),
        lambda bf: bf.update({"reason": "x"}),
    ):
        data = _geldig()
        wijziging(data["passages"][0]["bronfuncties"][0])
        assert not voldoet(data, _schema())
        assert not _structuur(data)


def test_door_de_helper_gebouwde_uitvoer_voldoet_aan_schema_en_structuur():
    invoeren = [
        invoer
        for geval in FIXTURE["gevallen"]
        for invoer in (
            [v["invoer"] for v in geval["versies"]]
            if "versies" in geval
            else [geval["invoer"]]
        )
        if invoer["kern"].strip() and invoer["organisatorische_context"]
    ]
    assert len(invoeren) >= 9
    for invoer in invoeren:
        for status in ("pass", "fail", "review_required"):
            respons = respons_voor_status(invoer, status)
            assert voldoet(respons, _schema()), (invoer["begrip"], status)
            assert _structuur(respons), (invoer["begrip"], status)


def test_v6_respons_van_c105_voldoet_niet_en_is_onder_het_contract_invalid_output():
    respons = json.loads(V6_C105_TEKST)
    assert not voldoet(respons, _schema())
    zonder = deepcopy(respons)
    del zonder["passages"][0]["reason"]
    assert not voldoet(zonder, _schema())  # /3-vorm past niet in /4
    geval = next(g for g in FIXTURE["gevallen"] if g["id"] == "C105")
    invoer = maak_invoer(**geval["invoer"])
    configuratie = Configuratie(
        normhash="a" * 64,
        promptversie="def835-int02-prompt/testfixture",
        routeringshash="b" * 64,
        provider="anthropic",
        model="claude-opus-5",
    )
    uitvoering = Uitvoering(actor="ai", status="completed")
    for data in (respons, zonder):
        document = beoordeel(invoer, configuratie, data, uitvoering)
        assert (document.status, document.foutcategorie) == ("error", "invalid_output")


def _met(pad: tuple, waarde: Any) -> dict[str, Any]:
    data = _geldig()
    doel: Any = data
    for stap in pad[:-1]:
        doel = doel[stap]
    if waarde is ...:
        del doel[pad[-1]]
    else:
        doel[pad[-1]] = waarde
    return data


@pytest.mark.parametrize(
    ("pad", "waarde"),
    [
        (("extra",), "x"),
        (("passages", 0, "reason"), "x"),
        (("passages", 0, "start"), 0),
        (("passages", 0, "function"), "criterion"),
        (("passages", 0, "bronfuncties", 0, "start"), 0),
        (("verdict",), ...),
        (("coverage",), ...),
        (("passages", 0, "kernvorm"), ...),
        (("passages", 0, "bronfuncties"), ...),
        (("verdict",), "voldoet"),
        (("uncertainty",), None),
        (("passages", 0, "kernvorm"), "zin"),
        (("passages", 0, "bronfuncties", 0, "function"), "criterium"),
        (("passages", 0, "bronfuncties", 0, "bron"), 0),
        (("passages", 0, "bronfuncties"), {}),
        (("question",), 1),
        (("passages",), {}),
        (("reason",), None),
    ],
    ids=lambda w: repr(w)[:30],
)
def test_schema_weigert_wat_de_gesloten_contractvorm_weigert(pad, waarde):
    afwijkend = _met(pad, waarde)
    assert voldoet(_geldig(), _schema())
    assert _structuur(_geldig())
    assert not voldoet(afwijkend, _schema())
    assert not _structuur(afwijkend)


# --- 3. de dienst -------------------------------------------------------------------

PROVIDER = "fakeprovider"
MODEL = "fake-int02-model"
KERN = "Aanvraag die de behandelaar moet afwijzen bij een ontbrekende bijlage."
PASSAGE = "de behandelaar moet afwijzen bij een ontbrekende bijlage"


def _invoer():
    return maak_invoer(
        begrip="aanvraag",
        kern=KERN,
        bedoeling="Een verzoek om een besluit.",
        organisatorische_context=["Synthetische Dienst"],
        juridische_context=[],
        wettelijke_basis=[],
        bronnen=[],
    )


def _fail() -> dict[str, Any]:
    """De kern neemt de plicht in moetvorm over en alle grondbronnen zwijgen."""
    return uitvoer(
        [passage(_invoer(), PASSAGE, "obligation_form")],
        "fail",
        reason="De passage schrijft de behandelaar een handeling voor.",
    )


def _profiel(provider=PROVIDER, model=MODEL) -> Modelprofiel:
    return Modelprofiel(
        profiel_id="fixture-schemaroute-1",
        provider=provider,
        model=model,
        kwalificatie="testfixture; geen kwaliteitsclaim",
    )


def _budget() -> Budget:
    return Budget(
        max_uitvoertokens=800,
        deadline_seconden=5.0,
        max_invoertekens_veld=2000,
        max_invoertekens_totaal=6000,
        max_antwoordtekens=20000,
    )


class FakeRouter:
    def __init__(self, provider=PROVIDER, model=MODEL):
        self.provider, self.model = provider, model

    def get_model(self, task_type):
        return self.provider, self.model

    def accepts_temperature(self, model, provider=None):
        return True

    def thinking_default_on(self, model, provider=None):
        return False


_BEVESTIG = object()


class FakeAI:
    """AI-grens die, net als `AIServiceV2`, bij een meegegeven schema de
    schemahash en de bloktypen in de metadata meldt (tenzij overschreven)."""

    def __init__(
        self,
        *uitkomsten,
        stop_reason="end_turn",
        schemahash: Any = _BEVESTIG,
        bloktypen: Any = ("text",),
    ):
        self.uitkomsten = list(uitkomsten)
        self.calls: list[dict] = []
        self.stop_reason = stop_reason
        self.schemahash = schemahash
        self.bloktypen = bloktypen

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        uitkomst = self.uitkomsten.pop(0) if self.uitkomsten else _fail()
        if isinstance(uitkomst, BaseException):
            raise uitkomst
        metadata: dict[str, Any] = {"stop_reason": self.stop_reason}
        schema = kwargs.get("response_schema")
        if schema is not None:
            if self.schemahash is _BEVESTIG:
                metadata["response_schema_sha256"] = response_schema_sha256(schema)
            elif self.schemahash is not None:
                metadata["response_schema_sha256"] = self.schemahash
            if self.bloktypen is not None:
                metadata["content_block_types"] = list(self.bloktypen)
        return AIGenerationResult(
            text=json.dumps(uitkomst, ensure_ascii=False),
            model=kwargs.get("model"),
            tokens_used=None,
            generation_time=0.01,
            cached=False,
            metadata=metadata,
        )


def _dienst(ai, router=None, profiel=None) -> Int02AssessmentService:
    return Int02AssessmentService(
        ai,
        router or FakeRouter(),
        profiel=profiel or _profiel(),
        budget=_budget(),
    )


def test_promptversie_vijf_met_gewijzigde_prompttekst():
    """Besluit 16: /5 vraagt kernvorm en bronfuncties; de tekst van /3 en /4
    is daarmee vervangen (de pin van /5 staat in de prompttest)."""
    assert dienstmodule.PROMPT_VERSION == "def835-int02-prompt/5"
    systeem, _ = bouw_int02_prompt(_invoer(), laad_int02_norm())
    digest = hashlib.sha256(systeem.encode("utf-8")).hexdigest()
    assert digest != SYSTEEMPROMPT_V3_SHA256
    # Herreview Codex P3: ook een exacte pin op de /5-systeemprompt.
    assert digest == SYSTEEMPROMPT_V5_SHA256


async def test_dienst_stuurt_het_vastgepinde_schema_mee():
    ai = FakeAI(_fail())
    resultaat = await _dienst(ai).assess(_invoer())
    assert len(ai.calls) == 1
    verzonden = ai.calls[0].get("response_schema")
    assert verzonden == _schema()
    assert response_schema_sha256(verzonden) == SCHEMA_SHA256
    assert (resultaat.status, resultaat.reden) == ("fail", None)


@pytest.mark.parametrize(
    ("schemahash", "bloktypen", "reden"),
    [
        (None, ("text",), "schema_unconfirmed"),
        ("0" * 64, ("text",), "schema_unconfirmed"),
        (123, ("text",), "schema_unconfirmed"),
        (_BEVESTIG, None, "unexpected_content_blocks"),
        (_BEVESTIG, (), "unexpected_content_blocks"),
        (_BEVESTIG, ("text", "text"), "unexpected_content_blocks"),
        (_BEVESTIG, ("thinking", "text"), "unexpected_content_blocks"),
    ],
    ids=[
        "geen-hash",
        "andere-hash",
        "geen-tekst-hash",
        "geen-bloktypen",
        "nul-blokken",
        "twee-tekstblokken",
        "thinking-blok",
    ],
)
async def test_onbevestigd_schema_of_afwijkende_blokken_geeft_geen_oordeel(
    schemahash, bloktypen, reden
):
    ai = FakeAI(_fail(), _fail(), schemahash=schemahash, bloktypen=bloktypen)
    dienst = _dienst(ai)
    eerste = await dienst.assess(_invoer())
    tweede = await dienst.assess(_invoer())
    assert eerste.status == "error"
    assert eerste.reden == reden
    assert eerste.document.foutcategorie == "invalid_output"
    assert eerste.document.oordeel is None
    # Nooit gecachet: de tweede beoordeling gaat opnieuw naar het model.
    assert tweede.gecachet is False
    assert len(ai.calls) == 2


async def test_refusal_met_bevestigd_schema_blijft_fail_closed():
    ai = FakeAI(_fail(), stop_reason="refusal")
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.status == "error"
    assert resultaat.reden == "unconfirmed_completion"
    assert resultaat.document.oordeel is None


@pytest.mark.parametrize(
    "fout",
    [
        AIStructuredOutputUnsupportedError("niet ondersteund; niets verzonden"),
        "verpakt",
    ],
    ids=["direct", "verpakt-door-ai-laag"],
)
async def test_niet_ondersteund_schema_eigen_reden_en_niets_verstuurd(fout):
    if fout == "verpakt":
        try:
            try:
                raise AIStructuredOutputUnsupportedError("GEHEIM-DETAIL-Q7")
            except AIStructuredOutputUnsupportedError as binnen:
                raise AIServiceError("AI API error") from binnen
        except AIServiceError as buiten:
            fout = buiten
    ai = FakeAI(fout)
    resultaat = await _dienst(ai).assess(_invoer())
    assert resultaat.reden == "structured_output_unsupported"
    assert resultaat.status == "review_required"
    assert resultaat.document.reden == "not_assessed"
    assert resultaat.document.uitvoering.status == "not_executed"
    assert resultaat.document.uitvoering.transportpogingen == 0
    assert resultaat.document.oordeel is None
    assert resultaat.uitzonderingstype == type(fout).__name__
    assert "GEHEIM-DETAIL-Q7" not in repr(resultaat)


async def test_schema_dat_niet_bij_de_pin_hoort_gaat_niet_naar_de_ai(monkeypatch):
    ander = deepcopy(_schema())
    ander["properties"]["verdict"]["enum"].append("misschien")
    monkeypatch.setattr(dienstmodule, "ANTWOORDSCHEMA", ander, raising=False)
    ai = FakeAI(_fail())
    resultaat = await _dienst(ai).assess(_invoer())
    assert ai.calls == []
    assert resultaat.reden == "schema_mismatch"
    assert resultaat.document.uitvoering.status == "not_executed"
    assert resultaat.document.uitvoering.transportpogingen == 0


# --- 4. de echte keten tot in de SDK-body ----------------------------------------------


@pytest.fixture
def anthropic_actief(monkeypatch):
    monkeypatch.setattr(
        ModelRouter, "active_provider", property(lambda self: "anthropic")
    )
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_CUSTOM_HEADERS", raising=False)


def _routing() -> dict[str, Any]:
    config = yaml.safe_load((ROOT / "config" / "config.yaml").read_text("utf-8"))
    routing = deepcopy(config["model_routing"])
    routing["providers"] = {
        "anthropic": {"critical": "claude-opus-5", "standard": "claude-opus-5"},
        "openai": {"critical": "gpt-5.2", "standard": "gpt-5-mini"},
    }
    return routing


class SDKGrens:
    """Netwerkgrens onder de échte Anthropic-SDK; legt elk request vast."""

    def __init__(self, *antwoorden):
        self.antwoorden = list(antwoorden)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        tekst = json.dumps(self.antwoorden.pop(0), ensure_ascii=False)
        return httpx.Response(
            200,
            json={
                "id": "msg_offline_def835",
                "type": "message",
                "role": "assistant",
                "model": "claude-opus-5",
                "content": [{"type": "text", "text": tekst}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 11, "output_tokens": 22},
            },
        )


def _echte_keten(grens: SDKGrens, routing: dict[str, Any]) -> Int02AssessmentService:
    router = ModelRouter(routing)
    client = AnthropicClient(
        api_key=SLEUTEL, timeout=5.0, max_retries=0, model_router=router
    )
    client._sdk_opties["http_client"] = httpx.AsyncClient(
        transport=httpx.MockTransport(grens)
    )
    client._client = AsyncAnthropic(**client._sdk_opties)
    ai = AIServiceV2(
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True,
        ai_client=client,
        model_router=router,
    )
    return _dienst(ai, router, _profiel("anthropic", "claude-opus-5"))


async def test_echte_keten_body_draagt_exact_het_schema_zonder_beta(anthropic_actief):
    grens = SDKGrens(_fail())
    resultaat = await _echte_keten(grens, _routing()).assess(_invoer())
    assert resultaat.status == "fail"
    assert resultaat.reden is None
    [verzoek] = grens.requests
    body = json.loads(verzoek.content)  # behoudt de sleutelvolgorde
    assert body["output_config"] == {
        "format": {"type": "json_schema", "schema": _schema()}
    }
    assert response_schema_sha256(body["output_config"]["format"]["schema"]) == (
        SCHEMA_SHA256
    )
    assert body.get("thinking") == {"type": "disabled"}
    assert not any(naam.lower() == "anthropic-beta" for naam in verzoek.headers)
    assert "response_schema_sha256" not in verzoek.content.decode("utf-8")


async def test_echte_keten_zonder_capability_verstuurt_niets(anthropic_actief):
    routing = _routing()
    del routing["capabilities"]["anthropic"]["structured_outputs"]
    grens = SDKGrens(_fail())
    resultaat = await _echte_keten(grens, routing).assess(_invoer())
    assert grens.requests == []
    assert resultaat.reden == "structured_output_unsupported"
    assert resultaat.document.uitvoering.status == "not_executed"
    assert resultaat.document.uitvoering.transportpogingen == 0
