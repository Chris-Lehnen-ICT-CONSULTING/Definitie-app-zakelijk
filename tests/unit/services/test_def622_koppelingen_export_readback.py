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

from pathlib import Path
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


def _record(definitie: str = ZIN, org: str = '["Stichting Zilver"]') -> DefinitieRecord:
    # DEF-743: zonder bronnen is vaststelling alleen mogelijk met een
    # gedocumenteerde uitzondering "geen passende bron" (CON-02); als echte,
    # gebonden marker gezaaid (geen versiebump) zodat deze proeven CON-01
    # blijven isoleren. De tekstbasis van de binding is de definitiezin.
    import json as _json

    from database.models import splits_definitietekst
    from domain.context.normalisatie import lees_contextwaarden
    from tests.fixtures.def743_fakes import geen_bron_uitzondering_marker

    zin, _ = splits_definitietekst(definitie)
    marker = geen_bron_uitzondering_marker(
        "keurmerk",
        zin,
        {
            "organisatorische_context": lees_contextwaarden(org),
            "juridische_context": ["privaatrecht"],
            "wettelijke_basis": ["Regeling Z"],
        },
        actor=ACTOR,
    )
    return DefinitieRecord(
        begrip="keurmerk",
        definitie=definitie,
        categorie="type",
        organisatorische_context=org,
        juridische_context='["privaatrecht"]',
        wettelijke_basis='["Regeling Z"]',
        status=DefinitieStatus.REVIEW.value,
        validation_score=0.9,
        validation_issues=_json.dumps([marker], ensure_ascii=False),
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
            "version_number": rec.version_number,
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

    @pytest.mark.asyncio
    async def test_exportuitvoer_draagt_dezelfde_contractvelden_als_de_validator(
        self, tmp_path
    ):
        """K2 (delta 1): aanvullende data mag de contractvelden ook in het
        exportobject/de uitvoer niet vervangen — validator en uitvoer gebruiken
        exact dezelfde recordgegevens."""
        import json as _json

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

        pad = await service.export_definitie_async(
            definitie_id=did,
            additional_data={
                "metadata": {
                    "id": did + 100,
                    "versie": 2,
                    "context_review": {"fingerprint": "vervalst", "actor": "x"},
                    "organisatorische_context": "Stichting Goud",
                },
                "context_dict": {"organisatorisch": ["Stichting Goud"]},
            },
            format=ExportFormat.JSON,
        )
        uitvoer = _json.loads(Path(pad).read_text(encoding="utf-8"))
        assert uitvoer["metadata"]["id"] == did
        assert uitvoer["metadata"]["versie"] == 4
        assert uitvoer["metadata"]["context_review"]["actor"] == ACTOR
        assert uitvoer["metadata"]["context_review"]["version_number"] == 2
        assert uitvoer["metadata"]["organisatorische_context"] == "Stichting Zilver"
        assert uitvoer["context"]["organisatorisch"] == ["Stichting Zilver"]
        assert uitvoer["context"]["juridisch"] == ["privaatrecht"]
        assert uitvoer["context"]["wettelijk"] == ["Regeling Z"]

    @pytest.mark.asyncio
    async def test_export_leest_het_record_een_keer(self, tmp_path):
        """K2 (delta 2): één recordlezing voor aggregatie én validatie; een
        tussentijdse wijziging kan niet tot 'validatie v3 / export v2' leiden."""
        from services.export_service import ExportFormat

        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(_record())
        spy = AsyncMock()
        spy.validate_text.return_value = {
            "version": "1.3.0",
            "is_acceptable": True,
            "system": {},
        }
        service = _export_service(repo, tmp_path, spy)

        lezingen: list[int] = []
        echte_get = service.repository.get_definitie

        def _geteld(definitie_id: int):
            rec = echte_get(definitie_id)
            lezingen.append(rec.version_number if rec else -1)
            # Tussen twee lezingen wijzigt het record: een tweede lezing zou
            # een andere snapshot zien.
            repo.legacy_repo.update_definitie(
                definitie_id, {"definitie": "ander kwaliteitsmerk"}
            )
            return rec

        service.repository.get_definitie = _geteld  # type: ignore[method-assign]
        service.data_aggregation_service.repository.get_definitie = _geteld  # type: ignore[method-assign]

        await service.export_definitie_async(definitie_id=did, format=ExportFormat.TXT)

        assert lezingen == [1], lezingen
        aanroep = spy.validate_text.call_args.kwargs
        assert aanroep["text"] == ZIN
        assert aanroep["context"].metadata["definition_version"] == 1

    @pytest.mark.asyncio
    async def test_expliciete_legacytekst_krijgt_dezelfde_tekstbasis(self, tmp_path):
        """K4 (delta 4): exact dezelfde opgeslagen legacytekst als
        `definitie_aangepast` meegeven verandert de vingerafdruk niet; de
        toelichting blijft een afzonderlijk gegeven."""
        from services.export_service import ExportFormat

        repo = _repo(tmp_path)
        volledig = f"{ZIN}\n\nToelichting: {TOELICHTING}"
        did = repo.legacy_repo.create_definitie(_record(definitie=volledig))
        _beoordeel(repo, did)
        orchestrator = _echte_orchestrator()
        gezien: list[dict[str, Any]] = []
        echte = orchestrator.validate_text

        async def _spion(**kwargs):
            resultaat = await echte(**kwargs)
            gezien.append({"text": kwargs["text"], "resultaat": resultaat})
            return {**resultaat, "is_acceptable": True}

        orchestrator.validate_text = _spion  # type: ignore[method-assign]
        service = _export_service(repo, tmp_path, orchestrator)

        pad = await service.export_definitie_async(
            definitie_id=did,
            additional_data={"definitie_aangepast": volledig},
            format=ExportFormat.JSON,
        )
        assert gezien[0]["text"] == ZIN
        assert gezien[0]["resultaat"]["rule_statuses"]["CON-01"] == "pass"
        import json as _json

        uitvoer = _json.loads(Path(pad).read_text(encoding="utf-8"))
        assert uitvoer["definitie"]["definitie_aangepast"] == ZIN
        assert uitvoer["definitie"]["definitie_origineel"] == ZIN
        assert uitvoer["taalkundig"]["toelichting"] == TOELICHTING


class TestReadbackTekstbasis:
    """K4: één tekstbasis voor beoordeling, gate, readback en validatie."""

    @pytest.mark.asyncio
    async def test_cleaning_verandert_de_tekstbasis_van_de_binding_niet(self, tmp_path):
        """Record→domein-readback met de productie-orchestrator (mét
        cleaning): de binding hoort bij de recordtekst, niet bij de
        opgeschoonde tekst die `clean_definition` in het object schrijft."""
        from services.cleaning_service import CleaningConfig, CleaningService
        from services.null_repository import NullDefinitionRepository
        from services.orchestrators.validation_orchestrator_v2 import (
            ValidationOrchestratorV2,
        )
        from services.validation.modular_validation_service import (
            ModularValidationService,
        )
        from toetsregels.manager import get_toetsregel_manager

        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(_record())
        _beoordeel(repo, did)
        svc = DefinitionWorkflowService(WorkflowService(), repo)
        assert svc.preview_gate(did)["status"] == "pass"

        orchestrator = ValidationOrchestratorV2(
            ModularValidationService(
                toetsregel_manager=get_toetsregel_manager(),
                repository=NullDefinitionRepository(),
            ),
            cleaning_service=CleaningService(CleaningConfig()),
        )
        definition = repo.get(did)
        resultaat = await orchestrator.validate_definition(definition)
        assert resultaat["rule_statuses"]["CON-01"] == "pass", resultaat[
            "rule_results"
        ]["CON-01"]["review"]
        assert resultaat["rule_results"]["CON-01"]["review"]["applied"] is True

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
        # Stichting Goud staat alleen in de toelichting, niet in de zin.
        record = _record(
            definitie=f"{ZIN}\n\nToelichting: {TOELICHTING}",
            org='["Stichting Zilver", "Stichting Goud"]',
        )
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
