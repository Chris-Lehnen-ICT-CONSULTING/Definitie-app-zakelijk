"""DEF-766: de ESS-03-beoordeling door de hele generatieketen (offline, echte validatie).

`DefinitionOrchestratorV2.create_definition` met gemockte AI/prompt/cleaning/
repository, maar met de echte `ValidationOrchestratorV2` →
`ModularValidationService` (echte regelset) en een deterministische fake
`Ess03AssessmentService`. Bewijst dat de gegenereerde kandidaat mét bedoelde
betekenis (opgegeven categorie) de telbaarheidsbeoordeling bereikt, dat de
verkregen beoordeling vóór opslag op de definitie staat (gebonden aan exact de
eindtekst) en dat een negatieve ESS-03-uitkomst geen herstelroute activeert en
de generatie niet laat falen. Geen echt model, geen productiedatabase.
"""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.ess03.contract import Intentie, bereken_ess03_vingerafdruk
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
from tests.fixtures.def766_fakes import FakeEss03Assessor
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
DEFINITIE = "Beschrijving van één verzameling documenten van een archiefvormer."


@pytest.fixture
def generate(monkeypatch):
    from voorbeelden import unified_voorbeelden

    monkeypatch.setattr(
        unified_voorbeelden,
        "genereer_alle_voorbeelden_async",
        AsyncMock(return_value={}),
    )

    async def run(*, scenario="pass", enhancement=None):
        assessor = FakeEss03Assessor(scenario=scenario)
        prompt = AsyncMock()
        prompt.build_generation_prompt.return_value = PromptResult(
            text="Offline",
            token_count=1,
            components_used=(),
            feedback_integrated=False,
            optimization_applied=False,
            metadata={},
        )
        ai = AsyncMock()
        ai.generate_definition.return_value = AIGenerationResult(
            text=DEFINITIE, model="offline", tokens_used=1, generation_time=0.0
        )
        cleaning = AsyncMock()
        cleaning.clean_text.return_value = CleaningResult(
            original_text=DEFINITIE, cleaned_text=DEFINITIE, was_cleaned=False
        )
        validation = ValidationOrchestratorV2(
            ModularValidationService(
                get_toetsregel_manager(), repository=NullDefinitionRepository()
            ),
            ess03_assessment_service=assessor,
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
                id="ess03-offline",
                begrip=BEGRIP,
                ontologische_categorie="type",
                organisatorische_context=["Testregistratie"],
            ),
            context={},
        )
        assert response.success, response.error
        return SimpleNamespace(
            response=response,
            assessor=assessor,
            repo=repo,
            definition=repo.save.call_args.args[0],
        )

    return run


async def test_generatie_bereikt_de_beoordeling_en_bewaart_haar_op_de_definitie(
    generate,
):
    result = await generate()
    (call,) = result.assessor.calls
    assert call["begrip"] == BEGRIP
    assert call["tekst"] == DEFINITIE
    assert call["intentie"].categorie == "type"  # de opgegeven categorie als claim
    md = result.definition.metadata
    beoordeling = md["ess03_assessment"]
    assert beoordeling["status"] == "assessed"
    assert beoordeling["fingerprint"] == bereken_ess03_vingerafdruk(
        BEGRIP,
        DEFINITIE,
        {"organisatorische_context": ["Testregistratie"]},
        [],
        intentie=Intentie(categorie="type"),
    )
    raw = result.response.validation_result
    assert raw["ess03_assessment"] == beoordeling
    assert raw["rule_statuses"]["ESS-03"] == "pass"
    assert raw["rule_results"]["ESS-03"]["fingerprint"] == beoordeling["fingerprint"]
    assert raw["overall_score"] is None


async def test_negatieve_ess03_laat_generatie_slagen_zonder_herstel(generate):
    enhancement = AsyncMock()
    enhancement.enhance_definition.return_value = "HERSCHREVEN"
    result = await generate(scenario="fail", enhancement=enhancement)
    raw = result.response.validation_result
    assert raw["rule_statuses"]["ESS-03"] == "fail"
    [violation] = [v for v in raw["violations"] if v.get("code") == "ESS-03"]
    assert violation["severity"] == "warning"
    # Andere overtredingen kunnen herstel vragen, ESS-03 zelf nooit: de
    # ESS-03-violation bereikt de hersteldienst niet (geen automatische
    # tekstwijziging op een telbaarheidsoordeel).
    for call in enhancement.enhance_definition.await_args_list:
        assert all(v.get("code") != "ESS-03" for v in call.args[1])
    # De opgeslagen beoordeling hoort bij de definitieve kandidaat.
    assert (
        result.definition.metadata["ess03_assessment"]["judgment"]["verdict"] == "fail"
    )
    assert result.definition.metadata["ess03_assessment"]["fingerprint"] == (
        raw["ess03_assessment"]["fingerprint"]
    )


async def test_niet_van_toepassing_reist_mee_zonder_pass(generate):
    result = await generate(scenario="not_applicable")
    raw = result.response.validation_result
    assert raw["rule_statuses"]["ESS-03"] == "not_applicable"
    assert "ESS-03" not in raw["passed_rules"]
    assert raw["evaluation_coverage"]["not_applicable"] == 1
    assert result.definition.metadata["ess03_assessment"]["judgment"]["verdict"] == (
        "not_applicable"
    )


async def test_technische_fout_reist_mee_als_error_niet_als_oordeel(generate):
    result = await generate(scenario="error")
    raw = result.response.validation_result
    assert raw["rule_statuses"]["ESS-03"] == "error"
    assert result.definition.metadata["ess03_assessment"]["status"] == "error"
    assert result.definition.metadata["ess03_assessment"]["judgment"] is None
    # Een geërrorde beoordeling is geen actueel bewijs: het document is
    # aanwezig als historie, maar telt bij replay niet als oordeel.
    from services.definition_edit_service import ess03_uitkomst_van_definition

    assert ess03_uitkomst_van_definition(result.definition)["status"] == "error"
