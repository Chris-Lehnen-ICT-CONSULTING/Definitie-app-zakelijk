"""DEF-835 WP5a: INT-02 (O2) via de generatie- en recordwrapper (eerst rood).

`ValidationOrchestratorV2` krijgt een optionele, expliciet geïnjecteerde
`int02_assessment_service`. De wrapper roept haar uitsluitend aan als de
actieve regelset INT-02 werkelijk op `decision_rule_assessment` zet (gelezen
via `ModularValidationService.evaluator_voor`), bouwt de WP1-invoer zelf uit
exact de getoetste kern en context, en geeft het verse WP1-document met zijn
configuratie aan de evaluator. Het document komt onveranderd in
`rule_results['INT-02']`.

Wat de aanroeper onder `int02_document`, `int02_configuratie` of
`int02_assessment` meegeeft, wordt altijd weggegooid: nooit een kortere weg
naar pass/fail. De normale O1-route doet nul INT-02-aanroepen, ook met een
geïnjecteerde dienst. Fouten van dienst, vorm of binding worden `error`,
zonder uitzonderingstekst in de log.

De O2-regelset is een tijdelijke kopie; het actieve `INT-02.json` blijft O1.
De modelresponsen zijn handmatig (ontwerpgevallen C105/C107/C112/C117): zij
bewijzen de ketenmapping, niets over modelkwaliteit. Opslag en herladen (C118)
vallen buiten dit pakket.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from domain.int02.contract import (
    CONTRACTVERSIE,
    MELDING_E,
    MELDING_NE,
    MELDING_NIET_BEOORDEELD,
    Configuratie,
    Uitvoering,
    beoordeel,
    maak_invoer,
)
from services.ai.base_client import response_schema_sha256
from services.interfaces import AIGenerationResult, Definition, GenerationRequest
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.int02_assessment_service import (
    Budget,
    Int02AssessmentService,
    Modelprofiel,
)
from services.validation.interfaces import ValidationContext
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def835_int02_v4 import naar_v4
from toetsregels.manager import ToetsregelManager

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[4]
REGELS = ROOT / "src" / "toetsregels" / "regels"
GEVALLEN = json.loads(
    (ROOT / "tests" / "fixtures" / "def835_int02_ontwerpgevallen.json").read_text(
        "utf-8"
    )
)["gevallen"]

PROVIDER = "fakeprovider"
MODEL = "fake-int02-model"
#: Synthetische configuratie van de fake-dienst; geen echt profiel.
CONFIG = Configuratie(
    normhash="a" * 64,
    promptversie="def835-wp5a-fixture/1",
    routeringshash="b" * 64,
    provider=PROVIDER,
    model=MODEL,
)
VOLTOOID = Uitvoering(actor="ai", status="completed")
#: Synthetische uitzonderingstekst die nooit in een log mag komen.
GEHEIM = "GEHEIME-UITZONDERINGSTEKST-wp5a met invoerfragment"


def _geval(geval_id: str, variant: str | None = None) -> dict[str, Any]:
    for geval in GEVALLEN:
        if geval["id"] == geval_id and geval.get("variant") == variant:
            return copy.deepcopy(geval)
    raise AssertionError(f"ontwerpgeval {geval_id}/{variant} ontbreekt")


C105 = _geval("C105")
BEGRIP = C105["invoer"]["begrip"]
KERN = C105["invoer"]["kern"]
BEDOELING = C105["invoer"]["bedoeling"]
CONTEXT = {
    "organisatorische_context": list(C105["invoer"]["organisatorische_context"]),
    "juridische_context": [],
    "wettelijke_basis": [],
}


def _invoer(kern: str = KERN, **over):
    velden = {
        "begrip": BEGRIP,
        "kern": kern,
        "bedoeling": BEDOELING,
        **copy.deepcopy(CONTEXT),
        "bronnen": [],
    }
    velden.update(over)
    return maak_invoer(**velden)


def _v4(respons: Any, invoer: Any = None) -> Any:
    """Een /3-respons (fixture of hieronder) in /4-vorm bij `invoer` (standaard `_invoer()`)."""
    return naar_v4(_invoer() if invoer is None else invoer, respons)


def _metadata(**over) -> dict[str, Any]:
    metadata: dict[str, Any] = {**copy.deepcopy(CONTEXT), "int02_bedoeling": BEDOELING}
    metadata.update(over)
    return metadata


def _pass_respons(kern: str = KERN) -> dict[str, Any]:
    return {
        "verdict": "pass",
        "passages": [
            {
                "quote": kern,
                "function": "criterion",
                "ground": {"field": "kern", "ref": None, "quote": None},
            }
        ],
        "reason": "Synthetische pass voor de mapping; geen modeloordeel.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }


def _na_respons() -> dict[str, Any]:
    return {
        "verdict": "not_applicable",
        "passages": [],
        "reason": "Synthetische reikwijdtegrond.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": "Synthetische tekst buiten het definitietoetsbereik.",
        "coverage": "none",
    }


@dataclass(frozen=True)
class _Beoordeling:
    """Zelfde publieke vorm als `Int02Beoordeling` voor de wrapper: `.document`."""

    document: Any


_GEEN = object()


class FakeDienst:
    """INT-02-dienstgrens: legt elke ontvangen invoer vast; geen model.

    F2: `configuratie()` is de publieke snapshot (standaard `CONFIG`; een
    uitzondering wordt opgeworpen). Het document wordt gebonden aan
    `document_config`, anders aan de snapshot zoals die bij `assess` geldt;
    `wijzig_naar` wisselt de snapshot tijdens de aanroep.
    """

    def __init__(
        self,
        respons=None,
        *,
        fout=None,
        resultaat=_GEEN,
        invoer=None,
        snapshot: Any = CONFIG,
        document_config: Configuratie | None = None,
        wijzig_naar: Configuratie | None = None,
    ):
        self.respons = C105["modelrespons"] if respons is None else respons
        self.fout = fout
        self.resultaat = resultaat
        self.andere_invoer = invoer
        self.snapshot = snapshot
        self.document_config = document_config
        self.wijzig_naar = wijzig_naar
        self.calls: list[Any] = []
        self.snapshots_gelezen = 0
        self.snapshots_voor_assess: list[int] = []

    def configuratie(self):
        self.snapshots_gelezen += 1
        if isinstance(self.snapshot, BaseException):
            raise self.snapshot
        return self.snapshot

    async def assess(self, invoer, *, correlation_id=None):
        self.calls.append(invoer)
        self.snapshots_voor_assess.append(self.snapshots_gelezen)
        if self.wijzig_naar is not None:
            self.snapshot = self.wijzig_naar
        if self.fout is not None:
            raise self.fout
        if self.resultaat is not _GEEN:
            return self.resultaat
        doel = invoer if self.andere_invoer is None else self.andere_invoer
        config = self.document_config or (
            self.snapshot if isinstance(self.snapshot, Configuratie) else CONFIG
        )
        return _Beoordeling(beoordeel(doel, config, _v4(self.respons, doel), VOLTOOID))


# --- regelsets ------------------------------------------------------------------


def _schrijf_regelmap(doel: Path, *, o2: bool) -> Path:
    doel.mkdir()
    for pad in sorted(REGELS.glob("*.json")):
        tekst = pad.read_text("utf-8")
        if o2 and pad.stem == "INT-02":
            data = json.loads(tekst)
            data["runtime_contract"].update(
                {
                    "evaluator": "decision_rule_assessment",
                    "automation_status": "automated",
                }
            )
            tekst = json.dumps(data, ensure_ascii=False, indent=2)
        (doel / pad.name).write_text(tekst, "utf-8")
    return doel


@pytest.fixture(scope="module")
def o2_manager(tmp_path_factory: pytest.TempPathFactory) -> ToetsregelManager:
    """Expliciete proefconfiguratie: alleen INT-02 wijst naar O2."""
    regels = _schrijf_regelmap(
        tmp_path_factory.mktemp("def835_wp5a_wrappers") / "regels", o2=True
    )
    return ToetsregelManager(base_dir=str(regels.parent))


@pytest.fixture(scope="module")
def o2_service(o2_manager) -> ModularValidationService:
    return ModularValidationService(toetsregel_manager=o2_manager)


@pytest.fixture(scope="module")
def o1_service() -> ModularValidationService:
    """De actieve regelset (INT-02 = judgment_review)."""
    return ModularValidationService(toetsregel_manager=ToetsregelManager())


def _int02(resultaat: dict[str, Any]) -> dict[str, Any]:
    return resultaat["rule_results"]["INT-02"]


def _record(kern: Any = KERN) -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=kern,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        metadata={"version_number": 1},
    )


async def _via_tekst(orch, kern: str = KERN, **metadata) -> dict[str, Any]:
    return await orch.validate_text(
        BEGRIP, kern, context=ValidationContext(metadata=_metadata(**metadata))
    )


async def _via_record(orch, kern: Any = KERN, **metadata) -> dict[str, Any]:
    return await orch.validate_definition(
        _record(kern),
        ValidationContext(metadata={"int02_bedoeling": BEDOELING, **metadata}),
    )


ROUTES = [pytest.param(_via_tekst, id="tekst"), pytest.param(_via_record, id="record")]


# --- O1 blijft actief: nul INT-02-aanroepen ---------------------------------------


@pytest.mark.parametrize("route", ROUTES)
async def test_o1_regelset_doet_nul_int02_aanroepen(o1_service, route):
    dienst = FakeDienst(_pass_respons())
    losse_dienst = FakeDienst(_pass_respons())
    orch = ValidationOrchestratorV2(o1_service, int02_assessment_service=dienst)
    los_document = beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID)

    resultaat = await route(
        orch,
        int02_document=los_document,
        int02_configuratie=CONFIG,
        int02_assessment=los_document.als_dict(),
        int02_assessment_service=losse_dienst,
    )

    assert dienst.calls == []
    assert losse_dienst.calls == []
    assert resultaat["rule_statuses"]["INT-02"] != "pass"
    assert resultaat["rule_results"].get("INT-02", {}).get("assessment") is None


# --- aanroepermetadata is nooit een kortere weg ------------------------------------


@pytest.mark.parametrize("route", ROUTES)
async def test_meegegeven_document_zonder_dienst_geeft_nooit_een_oordeel(
    o2_service, route
):
    # Zonder geïnjecteerde dienst blijft INT-02 expliciet open, ook als de
    # aanroeper een geldig, aan exact deze invoer gebonden document meegeeft.
    orch = ValidationOrchestratorV2(o2_service)
    los_document = beoordeel(_invoer(), CONFIG, _pass_respons(), VOLTOOID)

    resultaat = await route(
        orch,
        int02_document=los_document,
        int02_configuratie=CONFIG,
        int02_assessment=los_document.als_dict(),
    )

    detail = _int02(resultaat)
    assert detail["status"] == "review_required"
    assert detail["review"]["actuality"] == "not_assessed"
    assert detail["parts"][0]["reason"] == MELDING_NIET_BEOORDEELD
    assert detail["assessment"] is None


@pytest.mark.parametrize("route", ROUTES)
async def test_verse_beoordeling_vervangt_meegegeven_document(o2_service, route):
    dienst = FakeDienst()  # C105: adviserende fail
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
    los_document = beoordeel(_invoer(), CONFIG, _v4(_pass_respons()), VOLTOOID)

    resultaat = await route(
        orch, int02_document=los_document, int02_configuratie=CONFIG
    )

    (invoer,) = dienst.calls
    assert invoer == _invoer()
    verwacht = beoordeel(invoer, CONFIG, _v4(C105["modelrespons"], invoer), VOLTOOID)
    detail = _int02(resultaat)
    assert detail["status"] == "fail"
    assert detail["review"]["actuality"] == "current"
    assert detail["assessment"] == verwacht.als_dict()


# --- exacte kern ----------------------------------------------------------------------


class _AgressieveCleaning:
    """Cleaning die de tekst zichtbaar wijzigt; mag INT-02 niet raken."""

    def clean_text(self, tekst):
        return " ".join(str(tekst).split()).upper()


async def test_kern_is_bytegelijk_de_getoetste_tekst_zonder_cleaning(o2_manager):
    kern = "  De medewerker laat de  aanvrager toe. "
    service = ModularValidationService(
        toetsregel_manager=o2_manager, cleaning_service=_AgressieveCleaning()
    )
    dienst = FakeDienst(_pass_respons(kern))
    orch = ValidationOrchestratorV2(service, int02_assessment_service=dienst)

    resultaat = await _via_tekst(orch, kern, record_text="een andere tekst")

    (invoer,) = dienst.calls
    assert invoer.kern == kern
    detail = _int02(resultaat)
    assert detail["status"] == "pass"
    assert detail["assessment"]["invoer"]["kern"] == kern


async def test_recordkern_is_gezaghebbend(o2_service):
    dienst = FakeDienst()
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    await _via_record(orch, KERN, record_text="Verouderde aanroepertekst.")

    (invoer,) = dienst.calls
    assert invoer.kern == KERN
    assert invoer.organisatorische_context == tuple(CONTEXT["organisatorische_context"])


async def test_ongeldige_recordkern_is_fout_zonder_terugval(o2_service):
    # Een aanwezige recordkern die geen tekst is: geen terugval op de
    # aanroepertekst, geen aanroep, en een technische fout zonder oordeel.
    dienst = FakeDienst(_pass_respons())
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_record(orch, None, record_text=KERN)

    assert dienst.calls == []
    assert resultaat["rule_statuses"]["INT-02"] == "error"
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["assessment"] is None


async def test_recordkern_van_verkeerd_type_bereikt_de_dienst_niet(o2_service):
    # Een getal laat de bestaande modulaire service zelf degraderen; ook dan
    # geen aanroep en geen INT-02-oordeel.
    dienst = FakeDienst(_pass_respons())
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_record(orch, 42, record_text=KERN)

    assert dienst.calls == []
    assert resultaat["validation_status"] != "validated"
    assert "INT-02" not in resultaat.get("rule_results", {})


# --- NE en expliciet open ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("kern", "context"),
    [
        pytest.param("", CONTEXT, id="lege-kern"),
        pytest.param("Toelating:", CONTEXT, id="label-zonder-kern"),
        pytest.param(
            KERN,
            {
                "organisatorische_context": [],
                "juridische_context": [],
                "wettelijke_basis": [],
            },
            id="geen-context",
        ),
    ],
)
async def test_lege_kern_of_ontbrekende_context_is_ne_zonder_aanroep(
    o2_service, kern, context
):
    dienst = FakeDienst(_pass_respons())
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_tekst(orch, kern, **copy.deepcopy(context))

    assert dienst.calls == []
    assert resultaat["rule_statuses"]["INT-02"] == "not_evaluated"
    assert _int02(resultaat)["status"] == "not_evaluated"


# --- fouten van dienst, vorm en binding ----------------------------------------------------


FOUTDIENSTEN = [
    pytest.param(lambda: FakeDienst(fout=RuntimeError(GEHEIM)), id="uitzondering"),
    pytest.param(
        lambda: FakeDienst(resultaat={"status": "pass", "melding": GEHEIM}),
        id="vorm-dict",
    ),
    pytest.param(lambda: FakeDienst(resultaat=_Beoordeling(None)), id="vorm-leeg"),
    pytest.param(
        lambda: FakeDienst(
            _pass_respons("Een andere kern."), invoer=_invoer("Een andere kern.")
        ),
        id="binding-andere-invoer",
    ),
]


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("maak_dienst", FOUTDIENSTEN)
async def test_dienst_vorm_en_bindingsfout_zijn_error(
    o2_service, route, maak_dienst, caplog
):
    dienst = maak_dienst()
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    with caplog.at_level(logging.DEBUG):
        resultaat = await route(orch)

    assert len(dienst.calls) == 1  # geen herstel- of tweede aanroep
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["assessment"] is None
    assert GEHEIM not in caplog.text
    assert "GEHEIME" not in json.dumps(resultaat, default=str)


# --- de echte WP2-dienst met handmatige fake-respons (C105/C107/C112/C117) -----------------


class FakeRouter:
    def get_model(self, task_type):
        return PROVIDER, MODEL

    def accepts_temperature(self, model, provider=None):
        return True

    def thinking_default_on(self, model, provider=None):
        return False


class FakeAI:
    """AI-grens met één handmatige respons per aanroep; telt aanroepen."""

    def __init__(self, respons):
        self.respons = respons
        self.calls = 0

    async def generate_definition(self, prompt, **kwargs):
        self.calls += 1
        return AIGenerationResult(
            text=json.dumps(self.respons, ensure_ascii=False),
            model=kwargs.get("model"),
            tokens_used=None,
            generation_time=0.01,
            cached=False,
            metadata={"stop_reason": "end_turn", **_schemabevestiging(kwargs)},
        )


def _schemabevestiging(kwargs: dict) -> dict:
    """Zoals AIServiceV2 (besluit 14): bij een meegegeven antwoordschema de
    lokale schemahash en de bloktypen van de respons."""
    schema = kwargs.get("response_schema")
    if schema is None:
        return {}
    return {
        "response_schema_sha256": response_schema_sha256(schema),
        "content_block_types": ["text"],
    }


def _profiel(**over) -> Modelprofiel:
    velden = {
        "profiel_id": "wp5a-fixture-offline",
        "provider": PROVIDER,
        "model": MODEL,
        "kwalificatie": "testfixture; geen kwaliteitsclaim",
    }
    velden.update(over)
    return Modelprofiel(**velden)


def _budget() -> Budget:
    return Budget(
        max_uitvoertokens=800,
        deadline_seconden=5.0,
        max_invoertekens_veld=2000,
        max_invoertekens_totaal=6000,
        max_antwoordtekens=20000,
    )


class Spion:
    """Delegeert naar de echte dienst en bewaart het teruggegeven resultaat."""

    def __init__(self, dienst):
        self.dienst = dienst
        self.resultaten: list[Any] = []

    def configuratie(self):
        return self.dienst.configuratie()

    async def assess(self, invoer, **kwargs):
        resultaat = await self.dienst.assess(invoer, **kwargs)
        self.resultaten.append(resultaat)
        return resultaat


def _geval_metadata(geval) -> dict[str, Any]:
    invoer = geval["invoer"]
    return {
        "organisatorische_context": list(invoer["organisatorische_context"]),
        "juridische_context": list(invoer["juridische_context"]),
        "wettelijke_basis": list(invoer["wettelijke_basis"]),
        "int02_bedoeling": invoer["bedoeling"],
        "int02_bronnen": copy.deepcopy(invoer["bronnen"]),
    }


@pytest.mark.parametrize(
    ("geval_id", "status", "aanvaard"),
    [
        pytest.param(("C105", None), "fail", True, id="C105-fail"),
        pytest.param(("C107", None), "review_required", True, id="C107-onvoldoende"),
        pytest.param(("C112", None), "pass", True, id="C112-pass"),
        pytest.param(("C117", "verzonnen-citaat"), "error", False, id="C117-citaat"),
    ],
)
async def test_ontwerpgevallen_via_echte_dienst_en_modulaire_service(
    o2_service, geval_id, status, aanvaard
):
    geval = _geval(*geval_id)
    respons = _v4(geval["modelrespons"], maak_invoer(**geval["invoer"]))
    ai = FakeAI(respons)
    spion = Spion(
        Int02AssessmentService(ai, FakeRouter(), profiel=_profiel(), budget=_budget())
    )
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=spion)
    context = ValidationContext(metadata=_geval_metadata(geval))

    resultaat = await orch.validate_text(
        geval["invoer"]["begrip"], geval["invoer"]["kern"], context=context
    )

    assert ai.calls == 1
    (beoordeling,) = spion.resultaten
    assert beoordeling.document.status == status == geval["verwacht"]["status"]
    detail = _int02(resultaat)
    assert detail["status"] == status
    assert detail["parts"][0]["reason"] == beoordeling.document.melding
    if aanvaard:
        assert detail["assessment"] == beoordeling.document.als_dict()
        # Contract /4: het oordeel is de modelrespons plus afgeleide posities en
        # het dienstblok.
        oordeel = copy.deepcopy(detail["assessment"]["oordeel"])
        assert oordeel.pop("dienst")["modelstatus"] == status
        kern = geval["invoer"]["kern"]
        for passage in oordeel["passages"]:
            assert kern[passage.pop("start") : passage.pop("end")] == passage["quote"]
            for bronfunctie in passage["bronfuncties"]:
                bronfunctie.pop("start"), bronfunctie.pop("end")
        assert oordeel == respons
        assert detail["assessment"]["invoer"] == geval["invoer"]
    else:
        assert beoordeling.document.foutcategorie == "invalid_citation"
        assert detail["assessment"] is None

    # Opnieuw toetsen van exact dezelfde invoer: een geaccepteerd oordeel komt
    # uit de dienstcache, nooit een tweede modelaanroep; een fout is nooit
    # gecachet en wordt ook niet binnen één toetsing hersteld.
    await orch.validate_text(
        geval["invoer"]["begrip"], geval["invoer"]["kern"], context=context
    )
    assert ai.calls == (1 if aanvaard else 2)


async def test_ontbrekend_profiel_blijft_expliciet_open_zonder_modelaanroep(
    o2_service,
):
    ai = FakeAI(_v4(C105["modelrespons"]))
    dienst = Int02AssessmentService(ai, FakeRouter(), profiel=None, budget=_budget())
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_tekst(orch)

    assert ai.calls == 0
    detail = _int02(resultaat)
    assert detail["status"] == "review_required"
    assert detail["review"]["actuality"] == "not_assessed"


async def test_not_applicable_komt_via_de_wrapper_in_rule_results(o2_service):
    dienst = FakeDienst(_na_respons())
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_record(orch)

    detail = _int02(resultaat)
    assert detail["status"] == "not_applicable"
    oordeel = detail["assessment"]["oordeel"]
    assert oordeel.pop("dienst")["afleiding"] == "niet_van_toepassing"
    assert oordeel == _v4(_na_respons())


# --- generatieroute (DefinitionOrchestratorV2) ------------------------------------------------


class _Repo:
    pass


async def test_generatieroute_toetst_exact_de_kandidaat(o2_service):
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    dienst = FakeDienst()
    wrapper = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)
    orch = DefinitionOrchestratorV2(
        ai_service=object(),
        cleaning_service=object(),
        repository=_Repo(),
        validation_service=wrapper,
    )
    verzoek = GenerationRequest(
        id="wp5a-gen",
        begrip=BEGRIP,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
    )

    kandidaat, ruw, _ = await orch._toets_kandidaat(
        verzoek,
        KERN,
        ValidationContext(metadata={"int02_bedoeling": BEDOELING}),
        "wp5a-gen",
    )

    assert kandidaat == KERN
    (invoer,) = dienst.calls
    assert invoer == _invoer()
    assert ruw["rule_results"]["INT-02"]["status"] == "fail"
    assert (
        ruw["rule_results"]["INT-02"]["assessment"]
        == beoordeel(
            invoer, CONFIG, _v4(C105["modelrespons"], invoer), VOLTOOID
        ).als_dict()
    )


def test_definitie_orchestrator_geeft_int02_dienst_door_zonder_default():
    from services.orchestrators.definition_orchestrator_v2 import (
        DefinitionOrchestratorV2,
    )

    dienst = FakeDienst()
    met = DefinitionOrchestratorV2(
        ai_service=object(),
        cleaning_service=object(),
        repository=_Repo(),
        int02_assessment_service=dienst,
    )
    assert met.validation_service.int02_assessment_service is dienst

    zonder = DefinitionOrchestratorV2(
        ai_service=object(), cleaning_service=object(), repository=_Repo()
    )
    # Geen lazy default: zonder expliciete injectie bestaat er geen INT-02-dienst.
    assert zonder.int02_assessment_service is None
    assert zonder.validation_service.int02_assessment_service is None


# --- F1 (review WP5a): NE en ongeldige invoer zonder context -------------------
#
# Zonder context onderschepte de service INT-02 vóór de O2-evaluator (oude
# DEF-771-uitkomst op `cleaned_text`). Via de volledige keten moet de
# O2-evaluator zelf beslissen op de oorspronkelijke kern: exacte NE-melding in
# O2-vorm, of `error` bij ongeldige aanwezige kern/bedoeling — nooit een
# aanroep.


class _VasteCleaning:
    """Cleaning die altijd dezelfde tekst oplevert; mag INT-02 niet raken."""

    def __init__(self, tekst: str) -> None:
        self.tekst = tekst

    def clean_text(self, _tekst):
        return self.tekst


GEEN_CONTEXT = {
    "organisatorische_context": [],
    "juridische_context": [],
    "wettelijke_basis": [],
}


@pytest.mark.parametrize(
    ("kern", "cleaning", "extra", "recordroute", "ontbreekt"),
    [
        pytest.param(KERN, "", {}, False, "context", id="kern-cleaning-leeg"),
        pytest.param("", KERN, {}, False, "kern en context", id="leeg-cleaning-kern"),
        pytest.param(None, None, {}, True, None, id="recordkern-none"),
        pytest.param(
            KERN, None, {"int02_bedoeling": 42}, False, None, id="bedoeling-getal"
        ),
    ],
)
async def test_f1_zonder_context_beslist_de_o2_evaluator_zonder_aanroep(
    o2_manager, kern, cleaning, extra, recordroute, ontbreekt
):
    service = ModularValidationService(
        toetsregel_manager=o2_manager,
        cleaning_service=_VasteCleaning(cleaning) if cleaning is not None else None,
    )
    dienst = FakeDienst(_pass_respons())
    orch = ValidationOrchestratorV2(service, int02_assessment_service=dienst)
    metadata = {**copy.deepcopy(GEEN_CONTEXT), **extra}

    if recordroute:
        record = _record(kern)
        record.organisatorische_context = []
        resultaat = await orch.validate_definition(
            record, ValidationContext(metadata=_metadata(**metadata))
        )
    else:
        resultaat = await _via_tekst(orch, kern, **metadata)

    assert dienst.calls == []
    detail = _int02(resultaat)
    status = "not_evaluated" if ontbreekt else "error"
    melding = (
        MELDING_NE.replace("{kern/context}", ontbreekt) if ontbreekt else MELDING_E
    )
    # Eerst status en exacte melding, daarna de O2-documentvorm.
    assert resultaat["rule_statuses"]["INT-02"] == status
    assert detail["status"] == status
    assert [deel["reason"] for deel in detail["parts"]] == [melding]
    assert detail["contract_version"] == CONTRACTVERSIE
    assert detail["review"] == {"actuality": None}
    assert detail["assessment"] is None
    (deel,) = detail["parts"]
    assert deel["id"] == "beoordeling"


# --- F2 (review WP5a): onafhankelijke configuratiesnapshot vóór de aanroep ------
#
# De verwachte WP1-configuratie komt uit de publieke dienstsnapshot die de
# wrapper vóór `assess` vastlegt — nooit uit het teruggegeven document. Een
# afwijkende binding, een ontbrekende of ongeldige snapshot of een wijziging
# rond de aanroep is `error` zonder oordeel.


async def test_f2_reviewerrepro_oud_document_voor_ander_model_is_error(o2_service):
    oud = await Int02AssessmentService(
        FakeAI(_v4(_pass_respons())), FakeRouter(), profiel=_profiel(), budget=_budget()
    ).assess(_invoer())
    assert oud.document.status == "pass"

    class _NieuweRouter(FakeRouter):
        def get_model(self, task_type):
            return PROVIDER, "fake-new-model"

    class _GeeftOudResultaat(Int02AssessmentService):
        async def assess(self, invoer, **kwargs):
            return oud

    nieuwe_ai = FakeAI(_v4(_pass_respons()))
    dienst = _GeeftOudResultaat(
        nieuwe_ai,
        _NieuweRouter(),
        profiel=_profiel(model="fake-new-model"),
        budget=_budget(),
    )
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_tekst(orch)

    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["review"] == {"actuality": None}
    assert detail["assessment"] is None
    assert nieuwe_ai.calls == 0


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    ("veld", "waarde"),
    [
        ("normhash", "c" * 64),
        ("normversie", "def771-int02/9"),
        ("promptversie", "andere-prompt/1"),
        ("routeringshash", "d" * 64),
        ("provider", "anderprovider"),
        ("model", "ander-model"),
    ],
)
async def test_f2_documentbinding_afwijkend_van_snapshot_is_error(
    o2_service, route, veld, waarde
):
    dienst = FakeDienst(
        _pass_respons(), document_config=replace(CONFIG, **{veld: waarde})
    )
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await route(orch)

    assert len(dienst.calls) == 1
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["assessment"] is None


class _ZonderSnapshot:
    """Dienst zonder publieke snapshot; `assess` zou een pass geven."""

    def __init__(self):
        self.binnen = FakeDienst(_pass_respons())
        self.calls = self.binnen.calls

    async def assess(self, invoer, **kwargs):
        return await self.binnen.assess(invoer, **kwargs)


class _NietAanroepbareSnapshot(_ZonderSnapshot):
    configuratie = CONFIG


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    "maak_dienst",
    [
        pytest.param(_ZonderSnapshot, id="ontbreekt"),
        pytest.param(_NietAanroepbareSnapshot, id="niet-aanroepbaar"),
        pytest.param(lambda: FakeDienst(_pass_respons(), snapshot=None), id="none"),
        pytest.param(
            lambda: FakeDienst(_pass_respons(), snapshot=asdict(CONFIG)), id="dict"
        ),
        pytest.param(
            lambda: FakeDienst(_pass_respons(), snapshot=RuntimeError(GEHEIM)),
            id="uitzondering",
        ),
    ],
)
async def test_f2_ontbrekende_of_ongeldige_snapshot_is_error_zonder_aanroep(
    o2_service, route, maak_dienst, caplog
):
    dienst = maak_dienst()
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    with caplog.at_level(logging.DEBUG):
        resultaat = await route(orch)

    assert dienst.calls == []
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["assessment"] is None
    assert GEHEIM not in caplog.text


@pytest.mark.parametrize("route", ROUTES)
async def test_f2_snapshotwijziging_tijdens_aanroep_is_nooit_current(o2_service, route):
    dienst = FakeDienst(
        _pass_respons(), wijzig_naar=replace(CONFIG, model="gewisseld-model")
    )
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await route(orch)

    assert len(dienst.calls) == 1
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["review"] == {"actuality": None}
    assert detail["assessment"] is None


async def test_f2_routerwissel_tussen_snapshot_en_aanroep_is_error(o2_service):
    class _WisselendeRouter(FakeRouter):
        """Eerste routering (de snapshot) het profielmodel, daarna een ander."""

        def __init__(self):
            self.aantal = 0

        def get_model(self, task_type):
            self.aantal += 1
            return PROVIDER, MODEL if self.aantal == 1 else "gewisseld-model"

    ai = FakeAI(_v4(_pass_respons()))
    dienst = Int02AssessmentService(
        ai, _WisselendeRouter(), profiel=_profiel(), budget=_budget()
    )
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_tekst(orch)

    assert ai.calls == 0
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["assessment"] is None


async def test_f2_snapshot_wordt_voor_de_aanroep_vastgelegd(o2_service):
    dienst = FakeDienst(_pass_respons())
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    resultaat = await _via_tekst(orch)

    assert dienst.snapshots_voor_assess == [1]
    detail = _int02(resultaat)
    assert detail["status"] == "pass"
    assert detail["review"]["actuality"] == "current"
    assert detail["assessment"] == (
        beoordeel(_invoer(), CONFIG, _v4(_pass_respons()), VOLTOOID).als_dict()
    )


# --- F2-restpunt en F4 (herreview WP5a F2/F3) -----------------------------------
#
# F2-restpunt: ook een wijziging ná de interne routering, tijdens de awaited
# modelcall, mag nooit pass/current worden. De wrapper leest daarom na de
# aanroep opnieuw de publieke snapshot en eist dat die geldig is en gelijk aan
# de voor-snapshot. F4: ook het ophalen van `configuratie` zelf valt binnen de
# veilige foutgrens.


class _WijzigendeRouter(FakeRouter):
    thinking = False

    def thinking_default_on(self, model, provider=None):
        return self.thinking


class _WijzigtTijdensAI(FakeAI):
    """Wijzigt het routerbeleid tijdens de awaited modelcall (na de routering)."""

    def __init__(self, router):
        super().__init__(_v4(_pass_respons()))
        self.router = router

    async def generate_definition(self, prompt, **kwargs):
        await asyncio.sleep(0)
        self.router.thinking = True
        return await super().generate_definition(prompt, **kwargs)


@pytest.mark.parametrize("route", ROUTES)
async def test_f2_beleidswijziging_tijdens_modelcall_is_error(o2_service, route):
    router = _WijzigendeRouter()
    ai = _WijzigtTijdensAI(router)
    spion = Spion(
        Int02AssessmentService(ai, router, profiel=_profiel(), budget=_budget())
    )
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=spion)

    resultaat = await route(orch)

    assert ai.calls == 1  # geen extra modelcall
    (beoordeling,) = spion.resultaten
    assert beoordeling.document.status == "pass"  # de dienst zelf gaf een oordeel
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["review"] == {"actuality": None}
    assert detail["assessment"] is None


@pytest.mark.parametrize("route", ROUTES)
async def test_f2_stabiele_configuratie_blijft_pass_current(o2_service, route):
    router = _WijzigendeRouter()
    ai = FakeAI(_v4(_pass_respons()))
    orch = ValidationOrchestratorV2(
        o2_service,
        int02_assessment_service=Int02AssessmentService(
            ai, router, profiel=_profiel(), budget=_budget()
        ),
    )

    resultaat = await route(orch)

    assert ai.calls == 1
    detail = _int02(resultaat)
    assert detail["status"] == "pass"
    assert detail["review"]["actuality"] == "current"
    assert detail["assessment"]["binding"]["model"] == MODEL


class _NaSnapshot(FakeDienst):
    """Voor-snapshot geldig (`CONFIG`); elke latere snapshot is `na`."""

    def __init__(self, na):
        super().__init__(_pass_respons())
        self.na = na

    def configuratie(self):
        self.snapshots_gelezen += 1
        waarde = CONFIG if self.snapshots_gelezen == 1 else self.na
        if isinstance(waarde, BaseException):
            raise waarde
        return waarde


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    "na",
    [
        pytest.param(replace(CONFIG, model="na-model"), id="gewijzigd"),
        pytest.param(None, id="none"),
        pytest.param(asdict(CONFIG), id="dict"),
        pytest.param(RuntimeError(GEHEIM), id="uitzondering"),
    ],
)
async def test_f2_ongeldige_of_afwijkende_na_snapshot_is_error(
    o2_service, route, na, caplog
):
    dienst = _NaSnapshot(na)
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    with caplog.at_level(logging.DEBUG):
        resultaat = await route(orch)

    # Eerst de uitkomst, daarna het mechanisme (voor- en na-snapshot).
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["assessment"] is None
    assert GEHEIM not in caplog.text
    assert len(dienst.calls) == 1
    assert dienst.snapshots_gelezen == 2


class _FalendeSnapshotProperty:
    """Het ophalen van `configuratie` zelf faalt (F4-foutinjectie)."""

    def __init__(self):
        self.calls: list[Any] = []

    @property
    def configuratie(self):
        raise RuntimeError(GEHEIM)

    async def assess(self, invoer, **kwargs):  # pragma: no cover - mag niet
        self.calls.append(invoer)
        raise AssertionError("assess mag niet worden bereikt")


@pytest.mark.parametrize("route", ROUTES)
async def test_f4_falend_ophalen_van_snapshot_is_error_zonder_aanroep(
    o2_service, route, caplog
):
    dienst = _FalendeSnapshotProperty()
    orch = ValidationOrchestratorV2(o2_service, int02_assessment_service=dienst)

    with caplog.at_level(logging.DEBUG):
        resultaat = await route(orch)

    assert dienst.calls == []
    assert resultaat["validation_status"] == "validated"
    detail = _int02(resultaat)
    assert detail["status"] == "error"
    assert detail["parts"][0]["reason"] == MELDING_E
    assert detail["assessment"] is None
    assert GEHEIM not in caplog.text
    assert "GEHEIME" not in json.dumps(resultaat, default=str)
