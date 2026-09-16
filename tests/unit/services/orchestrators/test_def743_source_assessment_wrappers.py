"""DEF-743: de actieve async wrappers verkrijgen de bronbeoordeling standaard.

`ValidationOrchestratorV2.validate_text` en `validate_definition` moeten bij
aanwezige bronnen zélf een verse beoordeling verkrijgen via de geïnjecteerde
`SourceAssessmentService`, de beoordeling aan de evaluator meegeven én haar
volledig teruggeven (`result["source_assessment"]`, contract 1.4.0). Een door
de aanroeper meegegeven `source_assessment` is nooit een kortere weg naar
een positief oordeel. Kandidaat en aanroepermetadata blijven onaangeroerd.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from domain.sources.contract import CONTRACTVERSIE, bereken_bronvingerafdruk
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import CONTRACT_VERSION, ValidationContext
from services.validation.source_assessment_service import SourceAssessment

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "toezichthouder"
TEKST = "Persoon die bij of krachtens wettelijk voorschrift is belast met toezicht."
CONTEXT = {
    "organisatorische_context": ["Synthetische Inspectie"],
    "juridische_context": ["bestuursrecht"],
    "wettelijke_basis": ["Synthetische Bestuurswet"],
}
BRON = {
    "provider": "documents",
    "doc_id": "wet-11",
    "citation_label": "art. 5:11",
    "snippet": "Onder toezichthouder wordt verstaan: een persoon belast met toezicht.",
    "score": 1.0,
}


class FakeAssessor:
    """Registreert aanroepen en levert een gegrond, gebonden document."""

    def __init__(self, *, fout=None):
        self.calls = []
        self.fout = fout

    async def assess(
        self,
        begrip,
        tekst,
        contexten,
        bronnen_ruw,
        *,
        peildatum=None,
        correlation_id=None,
        receipt=None,
    ):
        self.calls.append(
            {
                "begrip": begrip,
                "tekst": tekst,
                "contexten": deepcopy(dict(contexten or {})),
                "bronnen": deepcopy(bronnen_ruw),
                "peildatum": peildatum,
                "receipt": deepcopy(receipt),
            }
        )
        if self.fout is not None:
            raise self.fout
        return SourceAssessment(
            {
                "contract_version": CONTRACTVERSIE,
                "prompt_version": "con02-assess/1",
                "fingerprint": bereken_bronvingerafdruk(
                    begrip, tekst, contexten, bronnen_ruw, peildatum=peildatum
                ),
                "status": "assessed",
                "error": None,
                "assessed_at": "2026-09-15T12:00:00+00:00",
                "attribution": {
                    "provider": "fake",
                    "model": "fake-model",
                    "task_type": "validation",
                    "cached": False,
                    "tokens_used": 1,
                },
                "peildatum": peildatum,
                "sources": [],
                "parts": {"marker": "vers-verkregen"},
                "rejected": [],
                "raw_response_sha256": None,
            }
        )


def _service():
    """Validatiedubbel dat de ontvangen context bewaart en een dict teruggeeft."""
    service = AsyncMock()

    async def _bewaar(*_a, **kwargs):
        service.received = deepcopy(kwargs.get("context") or {})
        return {"version": CONTRACT_VERSION, "system": {}}

    service.validate_definition.side_effect = _bewaar
    return service


async def test_validate_text_verkrijgt_verse_beoordeling_en_geeft_haar_terug():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    metadata = {**CONTEXT, "provenance_sources": [BRON], "peildatum": "2026-09-15"}
    before = deepcopy(metadata)

    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )

    assert metadata == before
    (call,) = assessor.calls
    assert call["begrip"] == BEGRIP and call["tekst"] == TEKST
    assert call["bronnen"] == [BRON]
    assert call["peildatum"] == "2026-09-15"
    assert call["contexten"]["wettelijke_basis"] == ["Synthetische Bestuurswet"]
    assert service.received["source_assessment"]["parts"] == {
        "marker": "vers-verkregen"
    }
    assert service.received["provenance_sources"] == [BRON]
    assert service.received["record_text"] == TEKST
    assert result["source_assessment"]["status"] == "assessed"
    assert result["source_assessment"]["fingerprint"] == bereken_bronvingerafdruk(
        BEGRIP, TEKST, CONTEXT, [BRON], peildatum="2026-09-15"
    )
    # DEF-624: 2.0.0 (validation_status verplicht, geen default); de
    # bronbeoordeling (1.4.0-veld) reist ongewijzigd mee.
    assert result["version"] == CONTRACT_VERSION == "2.0.0"


async def test_aanroeper_beoordeling_is_nooit_een_kortere_weg():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    vervalst = {
        "status": "assessed",
        "parts": {"marker": "vervalst"},
        "fingerprint": "x",
    }
    metadata = {**CONTEXT, "provenance_sources": [BRON], "source_assessment": vervalst}

    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
    )

    assert len(assessor.calls) == 1
    assert service.received["source_assessment"]["parts"] == {
        "marker": "vers-verkregen"
    }
    assert result["source_assessment"]["parts"] == {"marker": "vers-verkregen"}
    assert metadata["source_assessment"] == vervalst  # invoer onaangeroerd


async def test_zonder_bronnen_geen_ai_aanroep_en_expliciet_geen_beoordeling():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    # Een aanwezige maar misvormde lijst is géén 'geen bronnen' meer (zie
    # `test_aanwezige_misvormde_alias_is_technische_fout_geen_omzeiling`).
    for metadata in (
        {**CONTEXT},
        {**CONTEXT, "provenance_sources": []},
        {**CONTEXT, "provenance_sources": None},
    ):
        result = await orch.validate_text(
            BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
        )
        assert assessor.calls == []
        assert service.received.get("source_assessment") is None
        assert result["source_assessment"] is None


async def test_zonder_dienst_is_de_beoordeling_expliciet_niet_beschikbaar():
    service = _service()
    orch = ValidationOrchestratorV2(service)  # geen source_assessment_service
    result = await orch.validate_text(
        BEGRIP,
        TEKST,
        context=ValidationContext(metadata={**CONTEXT, "provenance_sources": [BRON]}),
    )
    assert service.received["source_assessment"]["status"] == "unavailable"
    assert result["source_assessment"]["status"] == "unavailable"
    assert (
        "geen bronbeoordelingsdienst"
        in result["source_assessment"]["reason"].casefold()
    )


async def test_dienstfout_wordt_technische_fout_niet_pass():
    service = _service()
    orch = ValidationOrchestratorV2(
        service, source_assessment_service=FakeAssessor(fout=RuntimeError("kapot"))
    )
    result = await orch.validate_text(
        BEGRIP,
        TEKST,
        context=ValidationContext(metadata={**CONTEXT, "provenance_sources": [BRON]}),
    )
    assert result["source_assessment"]["status"] == "error"
    assert result["source_assessment"]["error"]["type"] == "unknown"
    assert service.received["source_assessment"]["status"] == "error"


async def test_validate_definition_leest_bronnen_en_review_uit_het_record():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    review = {
        "type": "reference_exception",
        "accepted": True,
        "actor": "x",
        "rationale": "y",
        "fingerprint": "f",
        "version_number": 2,
    }
    definition = Definition(
        id=7,
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=list(CONTEXT["organisatorische_context"]),
        juridische_context=list(CONTEXT["juridische_context"]),
        wettelijke_basis=list(CONTEXT["wettelijke_basis"]),
        metadata={
            "sources": [BRON],
            "provenance_sources": [deepcopy(BRON)],
            "source_review": review,
            "source_receipt": {
                "status": "error",
                "errors": [{"stage": "rag", "type": "X"}],
            },
            "source_assessment": {
                "status": "assessed",
                "parts": {"marker": "opgeslagen"},
            },
            "version_number": 2,
            "peildatum": "2026-09-15",
        },
    )
    momentopname = deepcopy(definition)

    result = await orch.validate_definition(definition)

    assert definition == momentopname  # record niet gemuteerd
    (call,) = assessor.calls
    assert call["tekst"] == TEKST and call["bronnen"] == [BRON]
    assert call["peildatum"] == "2026-09-15"
    # De opgeslagen kwitantie is generatiehistorie, geen invoer voor herbeoordeling.
    assert call["receipt"] is None
    assert service.received["provenance_sources"] == [BRON]
    assert service.received["source_review"] == review
    assert service.received["definition_version"] == 2
    assert service.received["peildatum"] == "2026-09-15"
    # De opgeslagen beoordeling is vervangen door de vers verkregen beoordeling.
    assert service.received["source_assessment"]["parts"] == {
        "marker": "vers-verkregen"
    }
    assert result["source_assessment"]["parts"] == {"marker": "vers-verkregen"}
    assert (
        service.received["provenance_sources"]
        is not definition.metadata["provenance_sources"]
    )


async def test_validate_definition_zonder_bronsleutels_gebruikt_aanroepercontext():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    definition = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=["Synthetische Inspectie"],
    )
    await orch.validate_definition(
        definition,
        context=ValidationContext(
            metadata={
                "provenance_sources": [BRON],
                "source_receipt": {"status": "used", "errors": []},
            }
        ),
    )
    (call,) = assessor.calls
    assert call["bronnen"] == [BRON]
    assert call["receipt"] == {"status": "used", "errors": []}


async def test_conflicterende_bronaliassen_zijn_technische_fout():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    definition = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=["Synthetische Inspectie"],
        metadata={
            "sources": [BRON],
            "provenance_sources": [{**BRON, "doc_id": "ander"}],
        },
    )
    result = await orch.validate_definition(definition)
    assert assessor.calls == []
    assert result["source_assessment"]["status"] == "error"
    assert result["source_assessment"]["error"]["type"] == "source_alias_conflict"


async def test_cleaning_verandert_de_bindingstekst_niet():
    service, assessor = _service(), FakeAssessor()
    cleaning = SimpleNamespace(
        clean_text=AsyncMock(return_value=SimpleNamespace(cleaned_text=TEKST.upper())),
        clean_definition=AsyncMock(
            return_value=SimpleNamespace(cleaned_text=TEKST.upper())
        ),
    )
    orch = ValidationOrchestratorV2(
        service, cleaning_service=cleaning, source_assessment_service=assessor
    )
    await orch.validate_text(
        BEGRIP,
        TEKST,
        context=ValidationContext(metadata={**CONTEXT, "provenance_sources": [BRON]}),
    )
    definition = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=["X"],
        metadata={"sources": [BRON]},
    )
    await orch.validate_definition(definition)
    assert [c["tekst"] for c in assessor.calls] == [TEKST, TEKST]
    assert service.received["record_text"] == TEKST


# --- Codex-review v2 (bevindingen 3 en 6) --------------------------------------

FOUTKWITANTIE = {
    "version": "2",
    "status": "error",
    "sources": [],
    "omitted": [],
    "errors": [{"stage": "rag", "type": "ConnectionError"}],
    "channels": {},
}


@pytest.mark.parametrize("bronnen", [[], None, "geen lijst"])
async def test_foutkwitantie_zonder_bronnen_is_technische_fout_niet_gewoon_open(
    bronnen,
):
    """Bevinding 3: een verzamelfout verdwijnt niet achter 'geen bronnen'."""
    for dienst in (FakeAssessor(), None):
        service = _service()
        orch = ValidationOrchestratorV2(service, source_assessment_service=dienst)
        metadata = {**CONTEXT, "source_receipt": deepcopy(FOUTKWITANTIE)}
        if bronnen != "geen lijst":
            metadata["provenance_sources"] = bronnen
        result = await orch.validate_text(
            BEGRIP, TEKST, context=ValidationContext(metadata=metadata)
        )
        assert result["source_assessment"]["status"] == "error"
        assert result["source_assessment"]["error"]["type"] == "receipt_error"
        assert service.received["source_assessment"]["status"] == "error"
        if isinstance(dienst, FakeAssessor):
            assert dienst.calls == []  # geen AI-aanroep op een kapotte aanlevering


async def test_foutkwitantie_in_recordvalidatie_zonder_bronnen_is_ook_technische_fout():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    definition = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=["X"],
        metadata={"sources": []},
    )
    result = await orch.validate_definition(
        definition,
        context=ValidationContext(metadata={"source_receipt": deepcopy(FOUTKWITANTIE)}),
    )
    assert result["source_assessment"]["status"] == "error"
    assert assessor.calls == []


@pytest.mark.parametrize(
    ("metadata", "verwacht"),
    [
        ({"sources": [BRON]}, "assessed"),
        ({"provenance_sources": [BRON]}, "assessed"),
        ({"sources": [BRON], "provenance_sources": [deepcopy(BRON)]}, "assessed"),
        (
            {"sources": [BRON], "provenance_sources": [{**BRON, "doc_id": "ander"}]},
            "error",
        ),
    ],
)
async def test_validate_text_normaliseert_de_bronalias_en_faalt_gesloten_bij_conflict(
    metadata, verwacht
):
    """Bevinding 6: `sources` (legacy) en `provenance_sources` (canoniek) via één normalisatie."""
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    invoer = {**CONTEXT, **deepcopy(metadata)}
    momentopname = deepcopy(invoer)
    result = await orch.validate_text(
        BEGRIP, TEKST, context=ValidationContext(metadata=invoer)
    )
    assert invoer == momentopname
    assert result["source_assessment"]["status"] == verwacht
    if verwacht == "assessed":
        assert len(assessor.calls) == 1
        assert assessor.calls[0]["bronnen"] == [BRON]
        assert service.received["provenance_sources"] == [BRON]
    else:
        assert assessor.calls == []
        assert result["source_assessment"]["error"]["type"] == "source_alias_conflict"
        assert service.received["source_assessment"]["status"] == "error"


async def test_recordvalidatie_conflict_blijft_gesloten_via_dezelfde_normalisatie():
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    definition = Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        organisatorische_context=["X"],
        metadata={
            "sources": [BRON],
            "provenance_sources": [{**BRON, "doc_id": "ander"}],
        },
    )
    result = await orch.validate_definition(definition)
    assert result["source_assessment"]["error"]["type"] == "source_alias_conflict"
    assert assessor.calls == []


# --- Codex-vervolgreview (#6 restpunt: aanwezigheid ≠ geldigheid; #5 dienstgrens) ---


@pytest.mark.parametrize(
    "metadata",
    [
        {"provenance_sources": [BRON], "sources": "beschadigd"},
        {"sources": [BRON], "provenance_sources": "beschadigd"},
        {"provenance_sources": [BRON], "sources": {"doc_id": "x"}},
        {"provenance_sources": [BRON], "sources": True},
        {"sources": "alleen tekst"},
        {"provenance_sources": 7},
        {"provenance_sources": {"a": 1}},
    ],
)
async def test_aanwezige_misvormde_alias_is_technische_fout_geen_omzeiling(metadata):
    """#6: een aanwezige maar misvormde alias mag de conflictcontrole niet omzeilen."""
    for maak in (
        lambda md: ("text", md),
        lambda md: ("record", md),
    ):
        soort, md = maak(deepcopy(metadata))
        service, assessor = _service(), FakeAssessor()
        orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
        if soort == "text":
            invoer = {**CONTEXT, **md}
            momentopname = deepcopy(invoer)
            result = await orch.validate_text(
                BEGRIP, TEKST, context=ValidationContext(metadata=invoer)
            )
            assert invoer == momentopname
        else:
            definition = Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                organisatorische_context=["X"],
                metadata=md,
            )
            momentopname = deepcopy(definition)
            result = await orch.validate_definition(definition)
            assert definition == momentopname
        assert assessor.calls == [], (soort, metadata)
        assert result["source_assessment"]["status"] == "error", (soort, metadata)
        assert result["source_assessment"]["error"]["type"] == "source_alias_invalid", (
            soort,
            metadata,
        )
        assert service.received["source_assessment"]["status"] == "error"
        # Geen verzonnen lege lijst als masker.
        assert service.received.get("provenance_sources") in (
            md.get("provenance_sources"),
            md.get("sources"),
            None,
        )


@pytest.mark.parametrize(
    ("metadata", "verwacht_aanroep"),
    [
        ({"sources": None}, False),
        ({"provenance_sources": None}, False),
        ({"provenance_sources": [BRON], "sources": None}, True),
        ({"sources": [BRON], "provenance_sources": None}, True),
    ],
)
async def test_expliciete_none_alias_is_afwezigheid(metadata, verwacht_aanroep):
    """Gedocumenteerde keuze: een alias met waarde None telt als afwezig (D: 'expliciet None')."""
    service, assessor = _service(), FakeAssessor()
    orch = ValidationOrchestratorV2(service, source_assessment_service=assessor)
    result = await orch.validate_text(
        BEGRIP,
        TEKST,
        context=ValidationContext(metadata={**CONTEXT, **deepcopy(metadata)}),
    )
    assert (len(assessor.calls) == 1) is verwacht_aanroep
    if verwacht_aanroep:
        assert result["source_assessment"]["status"] == "assessed"
        assert service.received["provenance_sources"] == [BRON]
    else:
        assert result["source_assessment"] is None
        assert service.received.get("provenance_sources") is None


async def test_wrapper_geeft_de_werkelijke_afkapgrens_van_de_dienst_mee():
    """#5: de evaluator kent de dienstgrens, zodat een intern consistente herschreven kwitantie niet telt."""
    service = _service()
    dienst = FakeAssessor()
    dienst.max_passage_chars = 300
    orch = ValidationOrchestratorV2(service, source_assessment_service=dienst)
    await orch.validate_text(
        BEGRIP,
        TEKST,
        context=ValidationContext(metadata={**CONTEXT, "provenance_sources": [BRON]}),
    )
    assert service.received["assessment_max_passage_chars"] == 300
    # Zonder dienst (unavailable) of zonder attribuut: geen verzonnen grens.
    orch2 = ValidationOrchestratorV2(_service())
    await orch2.validate_text(
        BEGRIP,
        TEKST,
        context=ValidationContext(metadata={**CONTEXT, "provenance_sources": [BRON]}),
    )
    assert "assessment_max_passage_chars" not in orch2.validation_service.received
