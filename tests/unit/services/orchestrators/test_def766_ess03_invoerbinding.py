"""DEF-766: de bedoelde betekenis moet de ESS-03-beoordeling werkelijk bereiken (R1/R2).

Twee transportlekken in de orchestrators, offline bewezen:

* **R1** — `create_definition` geeft de `betekenisverduidelijking` mee via de
  `ValidationContext`, maar het tussentijdse `Definition` uit
  `_toets_kandidaat` draagt geen generatieregistratie. De recordverrijking
  wist daarop de aangeleverde verduidelijking, zodat ESS-03 zonder de bedoelde
  betekenis oordeelt. De opslag bewaart haar wél: bij heropenen is het
  oordeel onmiddellijk historisch (`review_required`) in plaats van actueel.
* **R2** — `validate_text` neemt het afzonderlijke argument
  `ontologische_categorie` niet op in de context die naar ESS-03 en de
  vingerafdruk gaat. Een gewijzigde categorie bereikt de beoordelaar niet en
  maakt de vorige beoordeling niet ongeldig: de cache levert opnieuw een pass.

De keten draait echt: `DefinitionOrchestratorV2` → `ValidationOrchestratorV2`
→ `ModularValidationService` (echte regelset) → echte `Ess03AssessmentService`
met echte prompt-, parser- en cachelaag, op een tijdelijke SQLite-database.
Gesimuleerd zijn alleen de AI/netwerkgrens (`generate_definition`) en de voor
deze vraag irrelevante generatie-afhankelijkheden (promptbouw, opschoning,
voorbeelden). Geen echt model, geen netwerk, geen productiedatabase.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from domain.ess03.contract import Intentie, bereken_ess03_vingerafdruk
from services.definition_edit_service import (
    ess03_intentie_van_definition,
    ess03_uitkomst_van_definition,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    Definition,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.ess03_assessment_service import Ess03AssessmentService
from services.validation.interfaces import ValidationContext, ValidationRequest
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "boekexemplaar"
TEKST = "Afzonderlijk fysiek exemplaar van een boek dat in de collectie is opgenomen."
CITAAT = "Afzonderlijk fysiek exemplaar"
ORG = ["Synthetische Bibliotheek"]
VERDUIDELIJKING = (
    "Alleen de fysiek afzonderlijke boekexemplaren worden geteld; niet de edities."
)
ANDERE_VERDUIDELIJKING = "Ook elke editie telt als een afzonderlijk exemplaar."
PROVIDER = "fakeprovider"
MODEL = "routed-validation"


class FakeEss03AI:
    """De AI/netwerkgrens van de beoordelingsdienst; legt elke aanroep vast.

    Contract van `AIServiceInterface.generate_definition` zoals de dienst het
    gebruikt: een `AIGenerationResult` met het kale JSON-antwoord als tekst en
    het werkelijk gebruikte model. Het model is dat van de router, zodat de
    beoordelingsbinding actueel is en een historische uitkomst nooit door een
    modelverschil in de proefopstelling ontstaat.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.default_model = MODEL

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        uitvoer = {
            "verdict": "pass",
            "applicability": "applicable",
            "unit": "het afzonderlijke fysieke exemplaar",
            "reason": "De definitie benoemt het afzonderlijke fysieke exemplaar.",
            "evidence": [{"location": "definition", "quote": CITAAT}],
            "missing_information": None,
            "question": None,
            "uncertainty": None,
        }
        return AIGenerationResult(
            text=json.dumps(uitvoer, ensure_ascii=False),
            model=MODEL,
            tokens_used=11,
            generation_time=0.0,
        )


class FakeRouter:
    def get_model(self, task_type):
        return PROVIDER, MODEL


def _dienst() -> tuple[Ess03AssessmentService, FakeEss03AI]:
    ai = FakeEss03AI()
    return Ess03AssessmentService(ai, model_router=FakeRouter()), ai


def _wrapper(dienst: Ess03AssessmentService) -> ValidationOrchestratorV2:
    return ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        ess03_assessment_service=dienst,
    )


@pytest.fixture
def genereer(monkeypatch, tmp_path):
    """Draai de echte generatieketen naar een tijdelijke SQLite-database."""
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )

    async def run(
        *, verduidelijking: str | None = None, categorie: str | None = "type"
    ):
        from services.prompts.modules.context_awareness_module import (
            verduidelijking_datalijn,
        )

        dienst, ai = _dienst()
        prompttekst = "Offline"
        if verduidelijking and verduidelijking.strip():
            # De generatie weigert vóór het model als het antwoord niet
            # volledig in de prompt staat (DEF-751); de fake respecteert dat.
            prompttekst += " " + verduidelijking_datalijn(verduidelijking)
        prompt = AsyncMock()
        prompt.build_generation_prompt.return_value = PromptResult(
            text=prompttekst,
            token_count=1,
            components_used=(),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )
        generatie_ai = AsyncMock()
        generatie_ai.generate_definition.return_value = AIGenerationResult(
            text=TEKST, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=TEKST, cleaned_text=TEKST, was_cleaned=False
        )
        db = str(tmp_path / "ess03-invoerbinding.db")
        orchestrator = DefinitionOrchestratorV2(
            prompt_service=prompt,
            ai_service=generatie_ai,
            validation_service=_wrapper(dienst),
            cleaning_service=cleaning,
            repository=DefinitionRepository(db),
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=False
            ),
        )
        response = await orchestrator.create_definition(
            GenerationRequest(
                id="def766-invoerbinding",
                begrip=BEGRIP,
                ontologische_categorie=categorie,
                organisatorische_context=list(ORG),
                betekenisverduidelijking=verduidelijking,
            ),
            context={},
        )
        assert response.success, response.error
        # Heropenen met een vérse repository-instantie: alleen wat werkelijk
        # is opgeslagen telt.
        record = DefinitionRepository(db).get(response.definition.id)
        return SimpleNamespace(
            response=response,
            ai=ai,
            dienst=dienst,
            db=db,
            record=record,
            beoordeling=(response.definition.metadata or {})["ess03_assessment"],
            registratie=(record.metadata or {}).get("generation_prompt_data") or {},
        )

    return run


def _replay(record: Definition, dienst: Ess03AssessmentService) -> dict:
    return ess03_uitkomst_van_definition(record, dienst.binding())


# --- R1: de betekenisverduidelijking door de generatieketen ---------------------------


async def test_generatie_stuurt_de_betekenisverduidelijking_naar_de_beoordeling(
    genereer,
):
    uit = await genereer(verduidelijking=VERDUIDELIJKING)

    (call,) = uit.ai.calls
    assert VERDUIDELIJKING in call["prompt"], (
        "de aangeleverde betekenisverduidelijking staat niet als materiaal in "
        "de ESS-03-beoordelingsprompt"
    )
    assert uit.beoordeling["input"]["intentie"]["betekenisverduidelijking"] == (
        VERDUIDELIJKING
    )


async def test_beoordeling_uit_generatie_blijft_actueel_na_opslaan_en_heropenen(
    genereer,
):
    uit = await genereer(verduidelijking=VERDUIDELIJKING)

    replay = _replay(uit.record, uit.dienst)
    assert replay["status"] == "pass", replay["review"]["assessment"]["reason"]
    assert replay["review"]["assessment"]["historical"] is False
    assert replay["review"]["assessment"]["applied"] is True


async def test_betekenis_is_identiek_in_beoordeling_opslag_en_herberekende_vingerafdruk(
    genereer,
):
    """De genormaliseerde tekst is dezelfde in alle drie de vindplaatsen."""
    uit = await genereer(verduidelijking=f"  {VERDUIDELIJKING}\n")

    bij_beoordeling = uit.beoordeling["input"]["intentie"]["betekenisverduidelijking"]
    opgeslagen = uit.registratie["betekenisverduidelijking"]
    bij_heropenen = ess03_intentie_van_definition(uit.record).betekenisverduidelijking
    assert bij_beoordeling == VERDUIDELIJKING
    assert opgeslagen.strip() == VERDUIDELIJKING
    assert bij_heropenen == VERDUIDELIJKING
    assert uit.beoordeling["fingerprint"] == bereken_ess03_vingerafdruk(
        uit.record.begrip,
        uit.record.definitie,
        {
            "organisatorische_context": list(uit.record.organisatorische_context or []),
            "juridische_context": list(uit.record.juridische_context or []),
            "wettelijke_basis": list(uit.record.wettelijke_basis or []),
        },
        [],
        intentie=ess03_intentie_van_definition(uit.record),
    )


async def test_gewijzigde_betekenisverduidelijking_maakt_het_oordeel_historisch(
    genereer,
):
    """De stale-bescherming blijft: een andere bedoeling is een andere vraag."""
    uit = await genereer(verduidelijking=VERDUIDELIJKING)
    registratie = dict(uit.registratie)
    registratie["betekenisverduidelijking"] = ANDERE_VERDUIDELIJKING
    uit.record.metadata["generation_prompt_data"] = registratie

    replay = _replay(uit.record, uit.dienst)
    assert replay["status"] == "review_required"
    assert replay["review"]["assessment"]["historical"] is True


async def test_bewust_gewiste_betekenisverduidelijking_maakt_het_oordeel_historisch(
    genereer,
):
    """Leegmaken is een echte wijziging; de oude bedoeling keert niet terug."""
    uit = await genereer(verduidelijking=VERDUIDELIJKING)
    registratie = dict(uit.registratie)
    registratie["betekenisverduidelijking"] = ""
    uit.record.metadata["generation_prompt_data"] = registratie

    assert ess03_intentie_van_definition(uit.record).betekenisverduidelijking is None
    replay = _replay(uit.record, uit.dienst)
    assert replay["status"] == "review_required"
    assert replay["review"]["assessment"]["historical"] is True


async def test_kandidaat_zonder_registratie_neemt_geen_betekenis_uit_de_aanroepercontext():
    """Fail-closed: zonder eigen registratie verzint de recordroute niets.

    Ook oude records missen de sleutel; een algemene terugval vanuit de
    aanroepercontext zou daar een vreemde of vervallen bedoeling activeren.
    """
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)

    await wrapper.validate_definition(
        Definition(
            begrip=BEGRIP,
            definitie=TEKST,
            organisatorische_context=list(ORG),
            ontologische_categorie="type",
        ),
        context=ValidationContext(
            metadata={"betekenisverduidelijking": VERDUIDELIJKING}
        ),
    )

    (call,) = ai.calls
    assert VERDUIDELIJKING not in call["prompt"]


async def test_recordbetekenis_gaat_voor_een_andere_betekenis_in_de_aanroepercontext():
    """Het record is de bron van zijn eigen bedoeling; een aanroeper overschrijft haar niet."""
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)

    await wrapper.validate_definition(
        Definition(
            begrip=BEGRIP,
            definitie=TEKST,
            organisatorische_context=list(ORG),
            metadata={
                "generation_prompt_data": {"betekenisverduidelijking": VERDUIDELIJKING}
            },
        ),
        context=ValidationContext(
            metadata={"betekenisverduidelijking": ANDERE_VERDUIDELIJKING}
        ),
    )

    (call,) = ai.calls
    assert VERDUIDELIJKING in call["prompt"]
    assert ANDERE_VERDUIDELIJKING not in call["prompt"]


async def test_een_beoordeling_zonder_betekenis_blijft_historisch_op_een_record_met_betekenis():
    """Geen stille herbinding: eerder verkeerd gebonden oordelen blijven historisch.

    Alleen opnieuw beoordelen herstelt de binding — de correctie migreert
    bestaande beoordelingen niet.
    """
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)
    kaal = Definition(
        begrip=BEGRIP, definitie=TEKST, organisatorische_context=list(ORG)
    )
    resultaat = await wrapper.validate_definition(kaal, context=None)
    beoordeling = resultaat["ess03_assessment"]
    assert beoordeling["status"] == "assessed"

    met_betekenis = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=list(ORG),
        metadata={
            "ess03_assessment": beoordeling,
            "generation_prompt_data": {"betekenisverduidelijking": VERDUIDELIJKING},
        },
    )
    replay = _replay(met_betekenis, dienst)
    assert replay["status"] == "review_required"
    assert replay["review"]["assessment"]["historical"] is True
    assert len(ai.calls) == 1


# --- R2: het afzonderlijke categorieargument -----------------------------------------


async def _toets(wrapper, categorie, *, metadata=None):
    return await wrapper.validate_text(
        begrip=BEGRIP,
        text=TEKST,
        ontologische_categorie=categorie,
        context=(
            None if metadata is None else ValidationContext(metadata=dict(metadata))
        ),
    )


def _doc(resultaat) -> dict:
    return resultaat["ess03_assessment"]


async def test_categorieargument_bereikt_de_beoordeling_en_de_vingerafdruk():
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)

    doc = _doc(await _toets(wrapper, "type"))

    assert doc["input"]["intentie"]["categorie"] == "type"
    assert doc["fingerprint"] == bereken_ess03_vingerafdruk(
        BEGRIP, TEKST, {"record_text": TEKST}, [], intentie=Intentie(categorie="type")
    )
    assert len(ai.calls) == 1, "per toetsing hoort precies één beoordelingsaanroep"
    regel = next(
        r
        for r in ai.calls[0]["prompt"].splitlines()
        if r.startswith("Opgegeven categorie")
    )
    assert regel.endswith("type")


async def test_gewijzigd_categorieargument_vraagt_een_nieuwe_beoordeling():
    """Type → proces is andere betekenisinvoer: geen cache-hit, andere binding."""
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)

    eerste = _doc(await _toets(wrapper, "type"))
    tweede = _doc(await _toets(wrapper, "proces"))

    assert len(ai.calls) == 2
    assert eerste["fingerprint"] != tweede["fingerprint"]
    assert tweede["input"]["intentie"]["categorie"] == "proces"
    assert tweede["attribution"]["cached"] is False


async def test_gelijk_categorieargument_hergebruikt_de_beoordeling_uit_de_cache():
    """Dezelfde invoer herhaalt als geldige cache-hit: nul extra modelaanroepen."""
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)

    eerste = _doc(await _toets(wrapper, "proces"))
    tweede = _doc(await _toets(wrapper, "proces"))

    assert len(ai.calls) == 1
    assert eerste["fingerprint"] == tweede["fingerprint"]
    assert tweede["attribution"]["cached"] is True
    assert tweede["judgment"]["verdict"] == eerste["judgment"]["verdict"]


async def test_expliciet_categorieargument_gaat_voor_aanroepermetadata():
    dienst, _ = _dienst()
    wrapper = _wrapper(dienst)

    doc = _doc(
        await _toets(wrapper, "proces", metadata={"ontologische_categorie": "type"})
    )

    assert doc["input"]["intentie"]["categorie"] == "proces"


async def test_zonder_categorieargument_blijft_de_categorie_uit_de_metadata_gelden():
    """Bestaande betekenis/precedentie: niet meegegeven is geen ontkenning."""
    dienst, _ = _dienst()
    wrapper = _wrapper(dienst)

    doc = _doc(await _toets(wrapper, None, metadata={"ontologische_categorie": "type"}))

    assert doc["input"]["intentie"]["categorie"] == "type"


async def test_expliciet_leeg_categorieargument_wist_de_categorie_van_de_aanroeper():
    """Expliciet leeg = geen categorie; zelfde binding als zonder categorie."""
    dienst, _ = _dienst()
    wrapper = _wrapper(dienst)

    leeg = _doc(await _toets(wrapper, "", metadata={"ontologische_categorie": "type"}))
    zonder = _doc(await _toets(wrapper, None))

    assert leeg["input"]["intentie"]["categorie"] is None
    assert leeg["fingerprint"] == zonder["fingerprint"]


async def test_expliciet_leeg_categorieargument_raakt_de_aparte_categorie_niet():
    """`categorie` is een ander recordveld, geen alias van het argument.

    Het contract leest de betekenisclaim als `ontologische_categorie or
    categorie` (`domain.ess03.contract.intentie_uit_context`). Een leeg
    argument wist daarom de ontologische claim van de aanroeper, maar laat
    diens losse `categorie`-waarde staan; die precedentie verandert hier niet.
    """
    dienst, _ = _dienst()
    wrapper = _wrapper(dienst)

    doc = _doc(await _toets(wrapper, "", metadata={"categorie": "type"}))

    assert doc["input"]["intentie"]["categorie"] == "type"


async def test_batch_validate_geeft_het_categorieargument_per_item_door():
    dienst, ai = _dienst()
    wrapper = _wrapper(dienst)

    resultaten = await wrapper.batch_validate(
        [
            ValidationRequest(begrip=BEGRIP, text=TEKST, ontologische_categorie="type"),
            ValidationRequest(
                begrip=BEGRIP, text=TEKST, ontologische_categorie="proces"
            ),
        ]
    )

    categorieen = [_doc(r)["input"]["intentie"]["categorie"] for r in resultaten]
    assert categorieen == ["type", "proces"]
    assert len(ai.calls) == 2


async def test_recordroute_gebruikt_de_recordcategorie_en_negeert_aanroepermetadata():
    dienst, _ = _dienst()
    wrapper = _wrapper(dienst)

    resultaat = await wrapper.validate_definition(
        Definition(
            begrip=BEGRIP,
            definitie=TEKST,
            organisatorische_context=list(ORG),
            ontologische_categorie="proces",
        ),
        context=ValidationContext(metadata={"ontologische_categorie": "type"}),
    )

    assert _doc(resultaat)["input"]["intentie"]["categorie"] == "proces"
