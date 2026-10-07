"""DEF-835 besluit 14 (optie A) — INT-02-antwoordschema via de API.

Bewezen: het vastgepinde antwoordschema is exact de bestaande gesloten
WP1-uitvoerstructuur (velden, volgorde, enums, nullability), zijn hash is
procesonafhankelijk (ook onder een andere PYTHONHASHSEED), het blijft binnen
de gedocumenteerde grenzen van structured outputs, alle geldige
ontwerpvoorbeelden voldoen en de v6-respons van C105 (extra passageveld
`reason`) niet. De dienst stuurt het schema mee, eist dat de AI-laag het
verzonden schema en precies één tekstblok bevestigt, weigert vóór de aanroep
een schema dat niet bij de pin hoort en meldt een niet-ondersteunde
combinatie met een eigen reden zonder verzending.

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
    FUNCTIES,
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
from utils.async_api import RateLimitConfig

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/def835_int02_ontwerpgevallen.json").read_text("utf-8")
)
SLEUTEL = "sk-ant-offline-def835-schema-000000000000"

#: Vastgepinde, volgordegevoelige hash van het INT-02-antwoordschema
#: (`services.ai.base_client.response_schema_sha256`, dezelfde functie
#: waarmee de AI-laag het verzonden schema bevestigt).
#: Na de Codex-review (P2, grondvarianten); de eerste pin was `2b1ac6a8…f96191`.
SCHEMA_SHA256 = "72adfe7428b67bf0fd999520581f0fc2cbe801101e1e8e6df300179405511f17"
VORIGE_SCHEMA_SHA256 = (
    "2b1ac6a869c0b989287c421ee66d40a204fcca0ffe41c6971d6d0ed896f96191"
)
#: Promptvolgorde (systeemprompt "met precies deze velden").
TOPVOLGORDE = [
    "verdict",
    "passages",
    "reason",
    "question",
    "uncertainty",
    "scope_reason",
    "coverage",
]
PASSAGEVOLGORDE = ["quote", "function", "ground"]
GRONDVOLGORDE = ["field", "ref", "quote"]
GRONDVELDEN = {
    "kern",
    "begrip",
    "bedoeling",
    "organisatorische_context",
    "juridische_context",
    "wettelijke_basis",
    "bron",
}
#: Systeemprompt onder /3 (test_def835_int02_dienstregel); /4 wijzigt hem niet.
SYSTEEMPROMPT_V3_SHA256 = (
    "da4a4112b580da2924b5940ac2723ef5e177ad48ef15890b66d8d91f285a7ca6"
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

#: Letterlijk de modeltekst van C105 in kwalificatieproef v6
#: (`kwalificatieproef-v6/regressie-bundel.json`, `antwoorden.C105`): inhoud
#: juist, maar een extra veld `reason` in de passage.
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


def _modelresponsen(knoop: Any) -> list[dict[str, Any]]:
    """Alle niet-lege `modelrespons`-waarden in de ontwerpfixture, diep."""
    gevonden: list[dict[str, Any]] = []
    if isinstance(knoop, dict):
        for sleutel, waarde in knoop.items():
            if sleutel == "modelrespons" and waarde is not None:
                gevonden.append(waarde)
            else:
                gevonden.extend(_modelresponsen(waarde))
    elif isinstance(knoop, list):
        for item in knoop:
            gevonden.extend(_modelresponsen(item))
    return gevonden


def _geldig() -> dict[str, Any]:
    return {
        "verdict": "fail",
        "passages": [
            {
                "quote": "q",
                "function": "actor_prescription",
                "ground": {
                    "field": "organisatorische_context",
                    "ref": 0,
                    "quote": None,
                },
            }
        ],
        "reason": "r",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }


# --- 1. het schema zelf -----------------------------------------------------------


def _grondvarianten() -> list[dict[str, Any]]:
    grond = _schema()["properties"]["passages"]["items"]["properties"]["ground"]
    assert set(grond) == {"anyOf"}, "ground hoort een anyOf van varianten te zijn"
    return grond["anyOf"]


def test_schema_is_de_gesloten_wp1_structuur_in_promptvolgorde():
    schema = _schema()
    assert schema["type"] == "object"
    assert list(schema["properties"]) == TOPVOLGORDE
    passage = schema["properties"]["passages"]
    assert passage["type"] == "array"
    assert list(passage["items"]["properties"]) == PASSAGEVOLGORDE
    for variant in _grondvarianten():
        assert list(variant["properties"]) == GRONDVOLGORDE
        assert set(variant["properties"]) == contract._GRONDVELDEN
    # Gesloten en volledig verplicht: elk object, ook elke grondvariant.
    for object_ in _objecten(schema):
        assert object_["type"] == "object"
        assert object_["additionalProperties"] is False
        assert object_["required"] == list(object_["properties"])
    # Dezelfde veldensets als de bestaande contractcontrole.
    assert set(schema["properties"]) == contract._UITVOERVELDEN
    assert set(passage["items"]["properties"]) == contract._PASSAGEVELDEN


def test_enums_komen_uit_de_constanten_en_zijn_gesorteerd():
    schema = _schema()
    top = schema["properties"]
    passage = top["passages"]["items"]["properties"]
    for veld, constanten in (
        (top["verdict"], VERDICTS),
        (top["uncertainty"], ONZEKERHEDEN),
        (top["coverage"], DEKKINGEN),
        (passage["function"], FUNCTIES),
    ):
        assert veld == {"type": "string", "enum": sorted(constanten)}
    velden = [v["properties"]["field"]["enum"] for v in _grondvarianten()]
    assert all(enum == sorted(enum) for enum in velden)
    # De varianten verdelen de grondvelden zonder overlap.
    assert sorted(f for enum in velden for f in enum) == sorted(GRONDVELDEN)
    assert set(contract._GRONDLABEL) | {"bron"} == GRONDVELDEN


#: P2 (Codex-review 07-10): `ground` volgt exact de koppeling veld → ref van
#: `_controleer_grondvorm`: scalaire velden ref null, contextvelden ref integer,
#: bron ref tekst. In promptvolgorde: scalair, context, bron.
_NUL_OF_TEKST = {"anyOf": [{"type": "string"}, {"type": "null"}]}
VERWACHTE_GROND = {
    "anyOf": [
        {
            "type": "object",
            "properties": {
                "field": {"type": "string", "enum": sorted(velden)},
                "ref": ref,
                "quote": _NUL_OF_TEKST,
            },
            "required": ["field", "ref", "quote"],
            "additionalProperties": False,
        }
        for velden, ref in (
            (("kern", "begrip", "bedoeling"), {"type": "null"}),
            (
                ("organisatorische_context", "juridische_context", "wettelijke_basis"),
                {"type": "integer"},
            ),
            (("bron",), {"type": "string"}),
        )
    ]
}


def test_ground_is_een_unie_van_gesloten_varianten_volgens_het_contract():
    grond = _schema()["properties"]["passages"]["items"]["properties"]["ground"]
    assert grond == VERWACHTE_GROND
    # Dezelfde indeling als de code: scalaire en contextvelden uit het contract.
    [scalair, context, bron] = _grondvarianten()
    assert set(scalair["properties"]["field"]["enum"]) == set(
        contract._SCALAIRE_GRONDEN
    )
    assert set(context["properties"]["field"]["enum"]) == set(contract._CONTEXTVELDEN)
    assert bron["properties"]["field"]["enum"] == ["bron"]


def test_nullables_via_anyof():
    schema = _schema()
    top = schema["properties"]
    assert top["reason"] == {"type": "string"}
    assert top["question"] == _NUL_OF_TEKST
    assert top["scope_reason"] == _NUL_OF_TEKST
    for variant in _grondvarianten():
        assert variant["properties"]["quote"] == _NUL_OF_TEKST
    passage = top["passages"]["items"]["properties"]
    assert passage["quote"] == {"type": "string"}


def _grond(field: str, ref: Any, quote: Any = None) -> dict[str, Any]:
    data = _geldig()
    data["passages"][0]["ground"] = {"field": field, "ref": ref, "quote": quote}
    return data


@pytest.mark.parametrize(
    ("field", "ref"),
    [("kern", "willekeurig"), ("bron", None), ("juridische_context", None)],
)
def test_bevestigde_review_combinaties_zijn_niet_schema_conform(field, ref):
    afwijkend = _grond(field, ref)
    assert not voldoet(afwijkend, _schema())
    with pytest.raises(contract._AfwijzingError):
        contract._controleer_structuur(afwijkend)


@pytest.mark.parametrize(
    ("field", "ref"),
    [
        ("kern", None),
        ("begrip", None),
        ("bedoeling", None),
        ("organisatorische_context", 0),
        ("juridische_context", 2),
        ("wettelijke_basis", 1),
        ("bron", "B1"),
    ],
)
@pytest.mark.parametrize("quote", [None, "letterlijk citaat"])
def test_elke_grondvariant_heeft_een_geldig_conform_voorbeeld(field, ref, quote):
    geldig = _grond(field, ref, quote)
    assert voldoet(geldig, _schema())
    contract._controleer_structuur(geldig)  # ook de code accepteert de vorm


def _alleen_in_code(field: str, ref: Any) -> bool:
    """Gedocumenteerde, toegestane afwijkingen: schema-conform, code weigert (veilig).

    - een lege of alleen-witruimte bron-ID (`_gevuld`);
    - een context-index als getal zonder breukdeel van het type float (`0.0`,
      `1.0`): volgens JSON Schema een `integer`, maar `_is_int` eist een
      Python-int.
    Bereik van de index, bestaan van de bron en letterlijkheid/uniciteit van
    citaten toetst de code ná de vorm. Typebewust: `0.0 == 0` in Python.
    """
    if field == "bron":
        return isinstance(ref, str) and not ref.strip()
    if field in contract._CONTEXTVELDEN:
        return isinstance(ref, float) and ref.is_integer()
    return False


def test_schema_en_contractvorm_zijn_gelijk_over_de_hele_grondmatrix():
    for field in sorted(GRONDVELDEN):
        for ref in (None, 0, 3, -1, 0.0, 1.0, "B1", "", " ", True, 1.5, [], {}):
            for quote in (None, "x", 1):
                data = _grond(field, ref, quote)
                schema_ok = voldoet(data, _schema())
                try:
                    contract._controleer_structuur(data)
                    code_ok = True
                except contract._AfwijzingError:
                    code_ok = False
                if _alleen_in_code(field, ref) and quote != 1:
                    assert (schema_ok, code_ok) == (True, False), (field, ref)
                else:
                    assert schema_ok == code_ok, (field, ref, quote)


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
    # Unies: question, scope_reason, ground (3 varianten) en per variant quote.
    assert (optioneel, unies) == (0, 6)


def test_schemahash_is_gepind_en_volgordegevoelig():
    schema = _schema()
    assert response_schema_sha256(schema) == _pin() == SCHEMA_SHA256
    assert SCHEMA_SHA256 != VORIGE_SCHEMA_SHA256  # P2 wijzigt het schema
    omgekeerd = deepcopy(schema)
    omgekeerd["properties"] = dict(reversed(list(schema["properties"].items())))
    assert omgekeerd == schema  # dict-gelijk, maar
    assert response_schema_sha256(omgekeerd) != SCHEMA_SHA256  # ander schema


_SUBPROCES = (
    "import json; "
    "from domain.int02 import contract as c; "
    "from services.ai.base_client import response_schema_sha256 as h; "
    "print(json.dumps({'hash': h(c.ANTWOORDSCHEMA), "
    "'pin': c.ANTWOORDSCHEMA_SHA256, 'rauw': list(c.FUNCTIES)}))"
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


# --- 2. voorbeelden tegen het schema ------------------------------------------------


def test_alle_geldige_ontwerpvoorbeelden_voldoen_aan_het_schema():
    responsen = _modelresponsen(FIXTURE)
    assert len(responsen) >= 9
    for respons in responsen:
        # Vooraf: de bestaande contractcontrole accepteert de vorm.
        contract._controleer_structuur(respons)
        assert voldoet(respons, _schema()), respons


def test_v6_respons_van_c105_met_passagereden_voldoet_niet():
    respons = json.loads(V6_C105_TEKST)
    assert set(respons["passages"][0]) == {"quote", "function", "ground", "reason"}
    assert not voldoet(respons, _schema())
    # Zonder het extra veld voldoet dezelfde inhoud wel: alleen dat veld is fout.
    zonder = deepcopy(respons)
    del zonder["passages"][0]["reason"]
    assert voldoet(zonder, _schema())


def test_v6_respons_van_c105_blijft_onder_het_contract_invalid_output():
    """De contractcontrole is ongewijzigd: zonder schema bleef dit een error."""
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
    document = beoordeel(invoer, configuratie, json.loads(V6_C105_TEKST), uitvoering)
    assert (document.status, document.foutcategorie) == ("error", "invalid_output")
    zonder = json.loads(V6_C105_TEKST)
    del zonder["passages"][0]["reason"]
    assert beoordeel(invoer, configuratie, zonder, uitvoering).status == "fail"


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
        (("passages", 0, "ground", "start"), 0),
        (("verdict",), ...),
        (("coverage",), ...),
        (("passages", 0, "ground", "ref"), ...),
        (("verdict",), "voldoet"),
        (("uncertainty",), None),
        (("passages", 0, "function"), "criterium"),
        (("passages", 0, "ground", "field"), "context"),
        (("passages", 0, "ground", "ref"), True),
        (("passages", 0, "ground", "ref"), 1.5),
        (("question",), 1),
        (("passages",), {}),
        (("reason",), None),
    ],
    ids=lambda w: repr(w)[:30],
)
def test_schema_weigert_wat_de_gesloten_contractvorm_weigert(pad, waarde):
    afwijkend = _met(pad, waarde)
    assert voldoet(_geldig(), _schema())
    assert not voldoet(afwijkend, _schema())
    with pytest.raises(contract._AfwijzingError):
        contract._controleer_structuur(afwijkend)


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
    return {
        "verdict": "fail",
        "passages": [
            {
                "quote": PASSAGE,
                "function": "actor_prescription",
                "ground": {"field": "kern", "ref": None, "quote": None},
            }
        ],
        "reason": "De passage schrijft de behandelaar een handeling voor.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }


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


def test_promptversie_vier_met_ongewijzigde_prompttekst():
    assert dienstmodule.PROMPT_VERSION == "def835-int02-prompt/4"
    # Dezelfde systeemprompt als onder /3: /4 = zelfde tekst + schemaroute.
    # (De dienstregeltest bindt de prompt met zijn eigen invoer; de systeemprompt
    # is invoeronafhankelijk.)
    systeem, _ = bouw_int02_prompt(_invoer(), laad_int02_norm())
    assert hashlib.sha256(systeem.encode("utf-8")).hexdigest() == (
        SYSTEEMPROMPT_V3_SHA256
    )


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
