"""DEF-743: één bronbasis door de hele generatieketen (offline, echte validatie).

`DefinitionOrchestratorV2.create_definition` met gemockte AI/prompt/cleaning/
repository, maar met de echte `ValidationOrchestratorV2` →
`ModularValidationService` (echte regelset) en een deterministische fake
`SourceAssessmentService`. Bewijst dat dezelfde aangeleverde bronset — gekoppeld
aan de kwitantie van de promptservice — de validatie bereikt, dat de
verkregen beoordeling vóór opslag op de definitie staat en dat CON-02 geen
herstelroute activeert. Geen echt model, geen productiedatabase.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.sources.contract import (
    CONTRACTVERSIE,
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_VERWIJZING,
    bereken_bronvingerafdruk,
)
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from services.validation.source_assessment_service import (
    SourceAssessment,
    SourceAssessmentService,
)
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

BEGRIP = "archiefkaart"
PASSAGE = (
    "Een archiefkaart beschrijft één verzameling documenten van een archiefvormer."
)
DEFINITIE = "Beschrijving van één verzameling documenten van een archiefvormer."
DOCUMENT = {
    "doc_id": "upload-01",
    "filename": "register.txt",
    "citation_label": "§ 2",
    "snippet": PASSAGE,
    "score": 1.0,
    "selection_basis": "term_match",
}
OMITTED_DOC = {
    "doc_id": "upload-02",
    "filename": "bijlage.txt",
    "snippet": "Een bijlage die niet in de prompt paste.",
    "score": 0.2,
}
RECEIPT = {
    "version": "1",
    "status": "used",
    "sources": [
        {
            "nr": 1,
            "source_type": "document",
            "source_id": "upload-01",
            "identity": {
                "doc_id": "upload-01",
                "filename": "register.txt",
                "citation_label": "§ 2",
            },
            "retrieval_score": 1.0,
            "content": "Een archiefkaart beschrijft één verzameling documenten",
            "content_hash": "sha256:x",
            "sanitized": False,
            "truncated": True,
            "xml": '<bron nr="1" …>',
            "used_in_prompt": True,
        }
    ],
    "omitted": [
        {
            "source_type": "document",
            "source_id": "upload-02",
            "identity": {"doc_id": "upload-02"},
            "reason": "budget",
        }
    ],
    "errors": [],
    "channels": {"document": {"enabled": True, "supplied": 2, "used": 1}},
}


class FakeAssessor:
    def __init__(self, *, verdict="pass"):
        self.calls = []
        self.verdict = verdict

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
                "tekst": tekst,
                "bronnen": deepcopy(bronnen_ruw),
                "receipt": deepcopy(receipt),
                "peildatum": peildatum,
            }
        )
        canoniek = canoniseer_bronnen(bronnen_ruw)
        fingerprint = bereken_bronvingerafdruk(
            begrip, tekst, contexten, canoniek, peildatum=peildatum
        )
        gebruikt = next(
            (b for b in canoniek if b.used_in_prompt), canoniek[0] if canoniek else None
        )
        quote = gebruikt.passage[:40] if gebruikt else ""
        bewijs = (
            [
                {
                    "source_id": gebruikt.source_id,
                    "quote": quote,
                    "locator": gebruikt.locator,
                }
            ]
            if gebruikt
            else []
        )

        def deel(status, **extra):
            return {
                "status": status,
                "reason": "synthetisch",
                "uncertainty": None,
                "evidence": bewijs,
                **extra,
            }

        return SourceAssessment(
            {
                "contract_version": CONTRACTVERSIE,
                "prompt_version": "con02-assess/1",
                "fingerprint": fingerprint,
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
                "sources": [b.als_dict() for b in canoniek],
                "parts": {
                    ONDERDEEL_GEZAG: deel(
                        "pass",
                        sources=[
                            {
                                "source_id": b["source_id"],
                                "profile": "vakpublicatie",
                                "applicable": True,
                                "reason": "synthetisch",
                            }
                            for b in bewijs
                        ],
                    ),
                    ONDERDEEL_STEUN: deel(
                        self.verdict,
                        claims=[
                            {
                                "aspect": "kenmerk",
                                "text": "verzameling documenten",
                                "supported": self.verdict == "pass",
                                "source_id": b["source_id"],
                            }
                            for b in bewijs
                        ],
                    ),
                    ONDERDEEL_VERWIJZING: deel(
                        "pass",
                        sources=[
                            {
                                "source_id": b["source_id"],
                                "locatable": True,
                                "reason": "synthetisch",
                            }
                            for b in bewijs
                        ],
                    ),
                },
                "rejected": [],
                "raw_response_sha256": None,
            }
        )


@pytest.fixture
def generate(monkeypatch):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )

    async def run(
        *,
        documents=None,
        receipt=RECEIPT,
        assessor=None,
        cleaned=DEFINITIE,
        options=None,
        enhancement=None,
    ):
        assessor = assessor or FakeAssessor()
        prompt = AsyncMock()
        prompt.build_generation_prompt.return_value = PromptResult(
            text="Offline",
            token_count=1,
            components_used=(),
            feedback_integrated=False,
            optimization_applied=False,
            metadata=(
                {"source_receipt": deepcopy(receipt)} if receipt is not None else {}
            ),
        )
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE,
            cleaned_text=cleaned,
            was_cleaned=cleaned != DEFINITIE,
        )
        validation = ValidationOrchestratorV2(
            ModularValidationService(
                get_toetsregel_manager(), repository=NullDefinitionRepository()
            ),
            source_assessment_service=assessor,
        )
        repo = MagicMock()
        repo.save.return_value = 42
        orch = DefinitionOrchestratorV2(
            prompt_service=prompt,
            ai_service=ai,
            validation_service=validation,
            cleaning_service=cleaning,
            repository=repo,
            enhancement_service=enhancement,
            config=OrchestratorConfig(
                enable_feedback_loop=False, enable_enhancement=enhancement is not None
            ),
        )
        response = await orch.create_definition(
            GenerationRequest(
                id="con02-offline",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["Testregistratie"],
                options=options,
            ),
            context={
                "documents": {
                    "snippets": deepcopy(
                        [DOCUMENT, OMITTED_DOC] if documents is None else documents
                    )
                }
            },
        )
        assert response.success, response.error
        return SimpleNamespace(
            response=response,
            assessor=assessor,
            repo=repo,
            definition=repo.save.call_args.args[0],
        )

    return run


async def test_zelfde_bronset_met_kwitantie_bereikt_validatie_en_metadata(generate):
    result = await generate(options={"peildatum": "2026-09-15"})
    (call,) = result.assessor.calls
    assert call["tekst"] == DEFINITIE
    assert call["receipt"] == RECEIPT
    assert call["peildatum"] == "2026-09-15"
    per_id = {b["doc_id"]: b for b in call["bronnen"]}
    assert per_id["upload-01"]["used_in_prompt"] is True
    assert (
        per_id["upload-01"]["prompt_content"]
        == "Een archiefkaart beschrijft één verzameling documenten"
    )
    assert per_id["upload-01"]["truncated"] is True
    assert per_id["upload-01"]["snippet"] == PASSAGE
    assert per_id["upload-02"]["used_in_prompt"] is False
    assert per_id["upload-02"]["omitted_reason"] == "budget"

    md = result.definition.metadata
    assert md["sources"] == call["bronnen"]
    assert md["provenance_sources"] == md["sources"]
    assert md["provenance_sources"] is not md["sources"]
    assert md["source_receipt"] == RECEIPT
    assert md["source_review"] is None
    assert md["peildatum"] == "2026-09-15"
    assert md["generation_id"] == "con02-offline"
    assessment = md["source_assessment"]
    assert assessment["status"] == "assessed"
    assert assessment["fingerprint"] == bereken_bronvingerafdruk(
        BEGRIP,
        DEFINITIE,
        {"organisatorische_context": ["Testregistratie"]},
        call["bronnen"],
        peildatum="2026-09-15",
    )
    # Bewijs uit de werkelijk verzonden (afgekapte) inhoud, gebonden aan de kandidaat.
    canoniek = canoniseer_bronnen(md["provenance_sources"])
    assert next(
        b for b in canoniek if b.source_id == "doc:upload-01"
    ).content_hash == bereken_inhoudshash(
        "Een archiefkaart beschrijft één verzameling documenten"
    )

    raw = result.response.validation_result
    assert raw["source_assessment"] == assessment
    assert raw["rule_statuses"]["CON-02"] == "pass"
    assert raw["rule_results"]["CON-02"]["fingerprint"] == assessment["fingerprint"]
    assert raw["overall_score"] is None


async def test_kwitantiefout_is_technische_fout_en_blokkeert(generate):
    kapot = {
        **RECEIPT,
        "status": "error",
        "sources": [],
        "errors": [{"stage": "document", "type": "ValueError"}],
    }

    class Echt(FakeAssessor):
        async def assess(self, *a, receipt=None, **kw):
            self.calls.append({"receipt": receipt})
            return await SourceAssessmentService(AsyncMock()).assess(
                *a, receipt=receipt, **kw
            )

    result = await generate(receipt=kapot, assessor=Echt())
    md = result.definition.metadata
    assert md["source_assessment"]["status"] == "error"
    assert md["source_assessment"]["error"]["type"] == "receipt_error"
    raw = result.response.validation_result
    assert raw["rule_statuses"]["CON-02"] == "error"
    assert raw["is_acceptable"] is False
    result.repo.save.assert_called_once()  # opslag als concept blijft, oordeel niet


async def test_zonder_kwitantie_blijft_de_aangeleverde_lijst_zoals_pakket_a_haar_levert(
    generate,
):
    result = await generate(receipt=None)
    (call,) = result.assessor.calls
    assert [b["doc_id"] for b in call["bronnen"]] == ["upload-01", "upload-02"]
    assert all("prompt_content" not in b for b in call["bronnen"])
    assert result.definition.metadata["source_receipt"] is None
    assert result.definition.metadata["source_assessment"]["status"] == "assessed"


async def test_gewijzigde_kandidaat_krijgt_eigen_beoordeling_gebonden_aan_eindtekst(
    generate,
):
    """De validatie schoont (mutatie) → hertoetsing van de eindtekst met verse beoordeling."""
    result = await generate(cleaned=DEFINITIE.lower())
    md = result.definition.metadata
    eind = result.definition.definitie
    assert md["source_assessment"]["fingerprint"] == bereken_bronvingerafdruk(
        BEGRIP,
        eind,
        {"organisatorische_context": ["Testregistratie"]},
        md["provenance_sources"],
        peildatum=None,
    )
    assert result.assessor.calls[-1]["tekst"] == eind
    assert (
        result.response.validation_result["rule_results"]["CON-02"]["fingerprint"]
        == md["source_assessment"]["fingerprint"]
    )


async def test_con02_fail_activeert_geen_automatisch_herstel(generate):
    enhancement = AsyncMock()
    enhancement.enhance_definition.return_value = "verbeterde tekst"
    result = await generate(
        assessor=FakeAssessor(verdict="fail"), enhancement=enhancement
    )
    raw = result.response.validation_result
    assert raw["rule_statuses"]["CON-02"] == "fail"
    assert any(v["code"] == "CON-02" for v in raw["violations"])
    # Andere overtredingen kunnen herstel vragen, CON-02 zelf nooit.
    for call in enhancement.enhance_definition.await_args_list:
        assert all(v.get("code") != "CON-02" for v in call.args[1])
    assert result.definition.metadata["source_review"] is None


async def test_container_injecteert_de_bronbeoordelingsdienst(tmp_path):
    from services.container import ContainerConfigs, ServiceContainer
    from services.validation.source_assessment_service import SourceAssessmentService

    container = ServiceContainer(
        {
            **ContainerConfigs.testing(),
            "db_path": str(tmp_path / "def743.db"),
            "use_json_rules": True,
        }
    )
    try:
        dienst = container.source_assessment_service()
        assert isinstance(dienst, SourceAssessmentService)
        assert container.source_assessment_service() is dienst
        assert dienst._ai_service is container.ai_service()
        assert dienst._model_router is container.model_router()
        orchestrator = container.orchestrator()
        assert orchestrator.source_assessment_service is dienst
        assert orchestrator.validation_service.source_assessment_service is dienst
    finally:
        repository = container._instances.get("repository")
        verbinding = getattr(getattr(repository, "legacy_repo", None), "_db", None)
        staat = getattr(getattr(verbinding, "_thread_local", None), "state", None)
        if staat is not None:
            staat.close()
        container.reset()
