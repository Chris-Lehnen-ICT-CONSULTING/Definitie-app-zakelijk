"""DEF-768: de importroute bereikt ESS-05 en kan geen oordeel of besluit injecteren.

Echte `DefinitionImportService` op een tijdelijke SQLite, echte
`ValidationOrchestratorV2` → `ModularValidationService`, fake
`Ess05AssessmentService`. Bewijst: de importvalidatie verkrijgt de
onderscheidsbeoordeling met de repository-buren uit dezelfde context; een
geïmporteerde definitie zonder bevestigde buur is open (nooit pass); velden
`ess05_*` in de importpayload bereiken validatie noch opslag.
"""

from __future__ import annotations

import pytest

from services.definition_import_service import DefinitionImportService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def768_fakes import FakeEss05Assessor
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

ORG = "Synthetische Uitleendienst"
PAYLOAD = {
    "begrip": "lener",
    "definitie": "Persoon met een actuele lening bij de instelling.",
    "categorie": "type",
    "organisatorische_context": [ORG],
    # Nooit een kortere weg: deze velden horen niet bij een import.
    "ess05_assessment": {"status": "assessed", "fingerprint": "x"},
    "ess05_buren": [{"term": "klant", "herkomst": "gebruiker", "bevestigd": True}],
}


@pytest.fixture
def opzet(tmp_path):
    repo = DefinitionRepository(str(tmp_path / "ess05-import.db"))
    bestaand = repo.save(
        Definition(
            begrip="klant",
            definitie="Persoon die iets afneemt.",
            categorie="type",
            organisatorische_context=[ORG],
            metadata={"status": "draft", "created_by": "tester"},
        )
    )
    assessor = FakeEss05Assessor(scenario="pass")
    validator = ValidationOrchestratorV2(
        ModularValidationService(get_toetsregel_manager(), repository=repo),
        ess05_assessment_service=assessor,
        ess05_burenbron=repo,
    )
    return DefinitionImportService(repo, validator), repo, assessor, bestaand


async def test_importvalidatie_verkrijgt_beoordeling_met_repositoryburen(opzet):
    service, _repo, assessor, bestaand = opzet
    preview = await service.validate_single(dict(PAYLOAD))
    (call,) = assessor.calls
    assert [(b.id, b.herkomst, b.bevestigd) for b in call["buren"]] == [
        (f"repository:{bestaand}", "repository", False)
    ]
    validatie = preview.validation
    assert validatie["ess05_assessment"]["status"] == "assessed"
    assert validatie["ess05_assessment"]["fingerprint"] != "x"
    # Een onbevestigde repository-buur: open met één vraag, nooit pass.
    assert validatie["rule_statuses"]["ESS-05"] == "review_required"
    assert "ESS-05" not in validatie["passed_rules"]


async def test_import_slaat_geen_geinjecteerd_oordeel_of_besluit_op(opzet):
    service, repo, _assessor, _bestaand = opzet
    result = await service.import_single(dict(PAYLOAD), created_by="tester")
    assert result.success, result.error
    opgeslagen = repo.get(result.definition_id)
    for sleutel in ("ess05_assessment", "ess05_buren", "ess05_lege_ruimte"):
        assert sleutel not in opgeslagen.metadata
