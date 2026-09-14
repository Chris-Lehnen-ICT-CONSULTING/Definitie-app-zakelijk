"""DEF-622 koppelingenreview (6b233060f): export- en readbackaansluiting.

* K2 — de exportgate bouwde haar validatiecontext uit de export-data ná de
  merge met `additional_data`; aanvullende exportdata kon zo versie, id,
  context en beoordeling vervangen en een verlopen beoordeling laten
  gelden. De contractvelden komen nu uitsluitend uit het opgeslagen record.
* K4 — readback splitste `\\n\\nToelichting:` van de recordtekst af, maar de
  beoordeling was aan de volledige recordtekst gebonden: record-contract
  Voldoet, domein-contract Nog te beoordelen. Eén expliciete tekstbasis
  (de definitiezin, `DefinitieRecord.get_definitie_tekst()`) voor
  beoordeling, gate, readback en validatie.

Alle databases zijn tijdelijk en synthetisch.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieStatus
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.workflow_service import WorkflowService

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-expert"
ZIN = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
TOELICHTING = "Stichting Goud verleent een ander merk."


def _repo(tmp_path) -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / "koppelingen.db"))


def _record(definitie: str = ZIN) -> DefinitieRecord:
    return DefinitieRecord(
        begrip="keurmerk",
        definitie=definitie,
        categorie="type",
        organisatorische_context='["Stichting Zilver"]',
        juridische_context='["privaatrecht"]',
        wettelijke_basis='["Regeling Z"]',
        status=DefinitieStatus.REVIEW.value,
        validation_score=0.9,
    )


def _beoordeel(repo: DefinitionRepository, definitie_id: int) -> str:
    """Leg de beoordeling vast op de canonieke tekstbasis van het record."""
    from domain.context.contract import beoordeel_context
    from domain.context.normalisatie import lees_contextwaarden

    rec = repo.get_definitie(definitie_id)
    assert rec is not None
    uitkomst = beoordeel_context(
        rec.begrip,
        rec.get_definitie_tekst(),
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
            "decisions": {
                naam.id: {"function": "necessary", "reason": "Exclusieve uitgever."}
            },
        },
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    return uitkomst.fingerprint


def _echte_orchestrator():
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
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


def _export_service(repo: DefinitionRepository, tmp_path, orchestrator):
    from services.export_service import ExportService

    return ExportService(
        repository=repo.legacy_repo,
        export_dir=str(tmp_path / "exports"),
        validation_orchestrator=orchestrator,
        enable_validation_gate=True,
    )


class TestExportContractvelden:
    """K2: de exportgate oordeelt op het opgeslagen record."""

    def _verouderd(self, repo: DefinitionRepository) -> int:
        """Record op versie 4 met een beoordeling die bij versie 2 hoort."""
        did = repo.legacy_repo.create_definitie(_record())
        _beoordeel(repo, did)
        assert repo.legacy_repo.update_definitie(did, {"definitie": ZIN + " (v2)"})
        assert repo.legacy_repo.update_definitie(did, {"definitie": ZIN})
        rec = repo.get_definitie(did)
        assert rec is not None and rec.version_number == 4
        assert rec.get_context_review()["version_number"] == 2
        return did

    @pytest.mark.asyncio
    async def test_aanvullende_exportdata_vervangt_geen_contractvelden(self, tmp_path):
        from services.export_service import ExportFormat

        repo = _repo(tmp_path)
        did = self._verouderd(repo)
        spy = AsyncMock()
        spy.validate_text.return_value = {
            "version": "1.3.0",
            "is_acceptable": True,
            "system": {},
        }
        service = _export_service(repo, tmp_path, spy)

        await service.export_definitie_async(
            definitie_id=did,
            additional_data={
                "metadata": {
                    "versie": 2,
                    "id": did + 100,
                    "context_review": {"fingerprint": "vervalst", "actor": "x"},
                },
                "context_dict": {"organisatorisch": ["Stichting Goud"]},
            },
            format=ExportFormat.TXT,
        )

        aanroep = spy.validate_text.call_args.kwargs
        context: Any = aanroep["context"]
        assert aanroep["text"] == ZIN
        assert context.metadata["definition_id"] == did
        assert context.metadata["definition_version"] == 4
        assert context.metadata["context_review"]["version_number"] == 2
        assert context.metadata["context_review"]["actor"] == ACTOR
        assert context.metadata["organisatorische_context"] == ["Stichting Zilver"]
        assert context.metadata["juridische_context"] == ["privaatrecht"]
        assert context.metadata["wettelijke_basis"] == ["Regeling Z"]

    @pytest.mark.asyncio
    async def test_verlopen_beoordeling_blijft_verlopen_met_echte_validatie(
        self, tmp_path
    ):
        """Met de echte orchestrator: de export ziet CON-01 als Nog te
        beoordelen, ook als de aanvullende data versie 2 opgeeft."""
        from services.export_service import ExportFormat

        repo = _repo(tmp_path)
        did = self._verouderd(repo)
        orchestrator = _echte_orchestrator()
        gezien: list[dict[str, Any]] = []
        echte = orchestrator.validate_text

        async def _spion(**kwargs):
            resultaat = await echte(**kwargs)
            gezien.append(resultaat)
            return resultaat

        orchestrator.validate_text = _spion  # type: ignore[method-assign]
        service = _export_service(repo, tmp_path, orchestrator)

        with pytest.raises(ValueError, match="geblokkeerd"):
            await service.export_definitie_async(
                definitie_id=did,
                additional_data={"metadata": {"versie": 2}},
                format=ExportFormat.TXT,
            )
        assert gezien and gezien[0]["rule_statuses"]["CON-01"] == "review_required"


class TestReadbackTekstbasis:
    """K4: één tekstbasis voor beoordeling, gate, readback en validatie."""

    def test_definitiezin_is_de_tekstbasis(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(
            _record(definitie=f"{ZIN}\n\nToelichting: {TOELICHTING}")
        )
        rec = repo.get_definitie(did)
        assert rec is not None
        assert rec.get_definitie_tekst() == ZIN
        # Zonder toelichting is de zin de volledige recordtekst.
        assert _record().get_definitie_tekst() == ZIN

    @pytest.mark.asyncio
    async def test_gate_en_domeinreadback_oordelen_gelijk(self, tmp_path):
        repo = _repo(tmp_path)
        record = _record(definitie=f"{ZIN}\n\nToelichting: {TOELICHTING}")
        # Stichting Goud staat alleen in de toelichting, niet in de zin.
        record.organisatorische_context = '["Stichting Zilver", "Stichting Goud"]'
        did = repo.legacy_repo.create_definitie(record)
        _beoordeel(repo, did)

        svc = DefinitionWorkflowService(WorkflowService(), repo)
        gate = svc.preview_gate(did)
        assert gate["status"] == "pass", gate

        definition = repo.get(did)
        assert definition is not None
        assert definition.definitie == ZIN
        assert definition.toelichting == TOELICHTING
        resultaat = await _echte_orchestrator().validate_definition(definition)
        assert resultaat["rule_statuses"]["CON-01"] == "pass"
        assert resultaat["rule_results"]["CON-01"]["review"]["applied"] is True
        # De naam in de toelichting is geen naamsignaal in de definitiezin.
        assert not any(
            p.get("context_value") == "Stichting Goud"
            for p in resultaat["rule_results"]["CON-01"]["parts"]
        )
