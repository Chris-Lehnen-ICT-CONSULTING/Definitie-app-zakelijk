"""DEF-622 batch 5: opslag/readback van de beoordeling en de exportaansluiting.

* Readback: de drie contextlijsten en de vastgelegde CON-01-beoordeling komen
  via `DefinitionRepository.get()` terug en reizen door de orchestrator mee
  naar de validatieservice, zodat CON-01 de expertbeoordeling herkent. Een
  gewijzigd concept hergebruikt geen oud oordeel (vingerafdruk).
* Export: `ExportService` valideerde vóór export met `context=None`; nu
  reizen de drie opgeslagen lijsten en de beoordeling mee. Of de exportgate
  daarna slaagt hangt af van de algemene gate (totaalscore, DEF-630); dat is
  hier bewust geen assertie — de spy-orchestrator meldt acceptabel.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieStatus
from services.definition_repository import DefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-expert"
TEKST = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"


def _repo(tmp_path) -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / "readback.db"))


def _record(definitie: str = TEKST) -> DefinitieRecord:
    return DefinitieRecord(
        begrip="keurmerk",
        definitie=definitie,
        categorie="type",
        organisatorische_context='["Stichting Zilver"]',
        juridische_context='["privaatrecht"]',
        wettelijke_basis='["Regeling Z"]',
        status=DefinitieStatus.REVIEW.value,
    )


def _leg_beoordeling_vast(repo: DefinitionRepository, definitie_id: int) -> str:
    from domain.context.contract import beoordeel_context
    from domain.context.normalisatie import lees_contextwaarden

    rec = repo.get_definitie(definitie_id)
    assert rec is not None
    uitkomst = beoordeel_context(
        rec.begrip,
        rec.definitie,
        {
            "organisatorische_context": lees_contextwaarden(
                rec.organisatorische_context
            ),
            "juridische_context": lees_contextwaarden(rec.juridische_context),
            "wettelijke_basis": lees_contextwaarden(rec.wettelijke_basis),
        },
    )
    naam = next(p for p in uitkomst.parts if p.evidence)
    assert repo.set_context_review(
        definitie_id,
        {
            "fingerprint": uitkomst.fingerprint,
            "actor": ACTOR,
            "version_number": rec.version_number,
            "decisions": {
                naam.id: {"function": "necessary", "reason": "Exclusieve uitgever."}
            },
        },
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    return uitkomst.fingerprint


def _echte_orchestrator() -> ValidationOrchestratorV2:
    from services.null_repository import NullDefinitionRepository
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    return ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        )
    )


class TestReadback:
    def test_lijsten_en_beoordeling_komen_terug(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(_record())
        vingerafdruk = _leg_beoordeling_vast(repo, did)

        definition = repo.get(did)
        assert definition is not None
        assert definition.organisatorische_context == ["Stichting Zilver"]
        assert definition.juridische_context == ["privaatrecht"]
        assert definition.wettelijke_basis == ["Regeling Z"]
        review = definition.metadata["context_review"]
        assert review["actor"] == ACTOR
        assert review["fingerprint"] == vingerafdruk

    @pytest.mark.asyncio
    async def test_beoordeling_reist_mee_naar_validatie_en_vervalt_bij_wijziging(
        self, tmp_path
    ):
        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(_record())
        _leg_beoordeling_vast(repo, did)
        orchestrator = _echte_orchestrator()

        beoordeeld = await orchestrator.validate_definition(repo.get(did))
        assert beoordeeld["rule_statuses"]["CON-01"] == "pass"
        assert beoordeeld["rule_results"]["CON-01"]["review"]["applied"] is True

        # Gewijzigd concept: de oude beoordeling hoort er niet meer bij.
        assert repo.legacy_repo.update_definitie(
            did, {"definitie": TEKST + " aan erkende leden"}
        )
        gewijzigd = await orchestrator.validate_definition(repo.get(did))
        assert gewijzigd["rule_statuses"]["CON-01"] == "review_required"
        assert gewijzigd["rule_results"]["CON-01"]["review"]["applied"] is False


class TestExportAansluiting:
    @pytest.mark.asyncio
    async def test_export_valideert_met_opgeslagen_context_en_beoordeling(
        self, tmp_path
    ):
        from services.export_service import ExportFormat, ExportService

        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(_record())
        vingerafdruk = _leg_beoordeling_vast(repo, did)
        record = repo.get_definitie(did)

        spy = AsyncMock()
        spy.validate_text.return_value = {
            "version": "1.3.0",
            "is_acceptable": True,
            "system": {},
        }
        service = ExportService(
            repository=repo.legacy_repo,
            export_dir=str(tmp_path / "exports"),
            validation_orchestrator=spy,
            enable_validation_gate=True,
        )
        await service.export_definitie_async(
            definitie_record=record, format=ExportFormat.TXT
        )

        aanroep = spy.validate_text.call_args.kwargs
        context: Any = aanroep["context"]
        assert context is not None
        assert context.metadata["organisatorische_context"] == ["Stichting Zilver"]
        assert context.metadata["juridische_context"] == ["privaatrecht"]
        assert context.metadata["wettelijke_basis"] == ["Regeling Z"]
        assert context.metadata["context_review"]["fingerprint"] == vingerafdruk
        assert context.metadata["definition_id"] == did
