"""DEF-624: de levende opslag-, hertoetsings- en exportgrenzen bij ontbrekend runbewijs.

Vier consumenten van het validatieresultaat schrijven of accepteren iets op
basis van `is_acceptable`/`overall_score`. Elk van hen keek alleen naar een
expliciete `validation_unknown`; een resultaat zónder status gold daar als
uitgevoerde run. Hier wordt per grens bewezen dat een ontbrekende (of
ongeldige) discriminator géén score bewaart, géén voorstel toepast, géén
hertoetsing als bewijs laat gelden en géén export vrijgeeft. Waar
repositorydata nodig is, draait de test op een echte tijdelijke SQLite.

Tegenhangers met een expliciete `validated` staan ernaast, zodat de guard
niet simpelweg alles kan weigeren.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import (
    CheckAction,
    DefinitieChecker,
    DefinitieCheckResult,
    _opslaanbare_validatiescore,
)
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    normaliseer_validatieresultaat,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.source_proposal_service import (
    OORZAAK_TECHNISCH,
    SourceProposalService,
    diagnose_bronbasis,
)
from services.validation.interfaces import (
    UNKNOWN_REASON_CONTRACT_STATUS_MISSING,
    VALIDATION_STATUS_UNKNOWN,
    VALIDATION_STATUS_VALIDATED,
)
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    JUR,
    ORG,
    TEKST,
    WET,
    FakeAI,
    FakeBronbeoordeling,
    bouw_beoordeling,
)

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-redacteur"
CONTEXTEN = {
    "organisatorische_context": ORG,
    "juridische_context": JUR,
    "wettelijke_basis": WET,
}


# ------------------------------------------------------ 1. DefinitieChecker


def _ui_response(status: Any, *, aanwezig: bool = True) -> dict[str, Any]:
    details: dict[str, Any] = {
        "overall_score": 0.82,
        "is_acceptable": True,
        "violations": [],
        "passed_rules": ["CON-01"],
    }
    if aanwezig:
        details["validation_status"] = status
    return {
        "success": True,
        "definitie_origineel": "een schriftelijke beslissing",
        "definitie_gecorrigeerd": "een schriftelijke beslissing van een bestuursorgaan",
        "final_score": 0.82,
        "validation_details": details,
        "voorbeelden": {},
        "metadata": {},
        "sources": [],
    }


class _StubAdapter:
    def __init__(self, ui_response: dict[str, Any]) -> None:
        self._ui_response = ui_response

    async def generate_definition(self, *args: Any, **kwargs: Any) -> object:
        return object()

    def to_ui_response(self, response: Any) -> dict[str, Any]:
        return self._ui_response


@pytest.mark.parametrize(
    "ui",
    [
        pytest.param(_ui_response(None, aanwezig=False), id="afwezig"),
        pytest.param(_ui_response(None), id="null"),
        pytest.param(_ui_response("VALIDATED"), id="ongeldig"),
    ],
)
def test_opslaanbare_score_is_none_zonder_runbewijs(ui: dict[str, Any]) -> None:
    assert _opslaanbare_validatiescore(ui) is None
    assert _opslaanbare_validatiescore(ui, standaard=0.0) is None


def test_opslaanbare_score_blijft_bij_validated() -> None:
    assert _opslaanbare_validatiescore(_ui_response(VALIDATION_STATUS_VALIDATED)) == (
        0.82
    )


def _checker(ui_response: dict[str, Any]) -> tuple[DefinitieChecker, MagicMock]:
    repo = MagicMock()
    repo.create_definitie.return_value = 42
    repo.update_definitie.return_value = True
    checker = DefinitieChecker(repository=repo)
    checker._get_integrated_service = lambda: _StubAdapter(ui_response)  # type: ignore[method-assign]
    checker.check_before_generation = lambda *a, **kw: DefinitieCheckResult(  # type: ignore[method-assign]
        action=CheckAction.PROCEED
    )
    return checker, repo


def test_generatieroute_bewaart_geen_score_zonder_status() -> None:
    checker, repo = _checker(_ui_response(None, aanwezig=False))
    checker.generate_with_check(
        begrip="besluit",
        organisatorische_context="Gemeente",
        categorie=OntologischeCategorie.TYPE,
        force_generate=True,
    )
    assert repo.create_definitie.called
    assert repo.create_definitie.call_args.args[0].validation_score is None


def test_echte_updateroute_wist_de_oude_score_zonder_status(tmp_path) -> None:
    """Route 2 door de échte repository: de oude 0.75 blijft niet staan."""
    repo = DefinitieRepository(str(tmp_path / "def624_update.db"))
    record_id = repo.create_definitie(
        DefinitieRecord(
            begrip="besluit",
            definitie="oude definitie",
            categorie=OntologischeCategorie.TYPE.value,
            organisatorische_context="Gemeente",
            juridische_context="",
            validation_score=0.75,
        )
    )
    checker = DefinitieChecker(repository=repo)
    checker._get_integrated_service = lambda: _StubAdapter(  # type: ignore[method-assign]
        _ui_response(None, aanwezig=False)
    )

    succes, _ = checker.update_existing_definition(
        record_id, updated_by="tester", regenerate=True
    )

    na = repo.get_definitie(record_id)
    assert succes is True
    assert na.definitie == "een schriftelijke beslissing van een bestuursorgaan"
    assert na.validation_score is None, na.validation_score
    with repo._get_connection() as conn:
        rij = conn.execute(
            "SELECT validation_score FROM definities WHERE id = ?", (record_id,)
        ).fetchone()
    assert rij[0] is None, repr(rij[0])


# ----------------------------------------- 2. editor: normaliseren en hertoetsen


def test_editor_normalisatie_maakt_ontbrekende_status_expliciet_onbekend() -> None:
    bron = {
        "overall_score": 0.9,
        "is_acceptable": True,
        "violations": [],
        "rule_statuses": {"CON-01": "pass"},
        "source_assessment": {"status": "assessed", "fingerprint": "abc"},
    }
    kopie = deepcopy(bron)

    uit = normaliseer_validatieresultaat(bron)

    assert bron == kopie
    assert uit["valid"] is False
    assert uit["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["unknown_reason"] == UNKNOWN_REASON_CONTRACT_STATUS_MISSING
    assert uit["raw_v2"]["validation_status"] == VALIDATION_STATUS_UNKNOWN
    assert uit["raw_v2"]["is_acceptable"] is False
    # Behoud voor uitleg.
    assert uit["rule_statuses"] == {"CON-01": "pass"}
    assert uit["source_assessment"] == {"status": "assessed", "fingerprint": "abc"}
    # De 0.9 is geen oordeel: fail-closed placeholder, geen verzonnen None.
    assert uit["score"] == 0.0


def test_editor_normalisatie_laat_een_validated_resultaat_intact() -> None:
    uit = normaliseer_validatieresultaat(
        {
            "validation_status": VALIDATION_STATUS_VALIDATED,
            "overall_score": None,
            "is_acceptable": True,
            "violations": [],
        }
    )
    assert uit["valid"] is True
    assert uit["validation_status"] == VALIDATION_STATUS_VALIDATED
    assert uit["unknown_reason"] is None
    assert uit["score"] is None


@pytest.mark.parametrize(
    "resultaat",
    [
        pytest.param({"source_assessment": {"status": "assessed"}}, id="afwezig"),
        pytest.param(
            {"validation_status": None, "source_assessment": {"status": "assessed"}},
            id="null",
        ),
        pytest.param(
            {"validation_status": "ok", "source_assessment": {"status": "assessed"}},
            id="ongeldig",
        ),
    ],
)
def test_hertoetsing_zonder_runbewijs_is_geen_bewijs(resultaat: dict[str, Any]) -> None:
    fout = DefinitionEditService._technische_fout_in_validatie(resultaat)
    assert fout is not None
    assert "validation_status" in fout or "runbewijs" in fout


def _echte_validatie(beoordeling: FakeBronbeoordeling):
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
        ),
        source_assessment_service=beoordeling,
    )


class _ZonderStatus:
    """Een producent die werkelijk toetst maar zijn runstatus kwijtraakt."""

    def __init__(self, echte: Any) -> None:
        self._echte = echte
        self.calls = 0

    async def validate_text(self, **kwargs: Any) -> dict[str, Any]:
        self.calls += 1
        resultaat = dict(await self._echte.validate_text(**kwargs))
        resultaat.pop("validation_status", None)
        return resultaat


def _definition(*, scenario: str = "fail", **meta: Any) -> Definition:
    metadata: dict[str, Any] = {
        "status": "draft",
        "created_by": "generator",
        "sources": deepcopy(BRONNEN),
        "provenance_sources": deepcopy(BRONNEN),
        "source_assessment": bouw_beoordeling(
            BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario=scenario, peildatum="2026-09-15"
        ),
        "definitie_origineel": TEKST,
        "definitie_eindtekst": TEKST,
        "peildatum": "2026-09-15",
    }
    metadata.update(meta)
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata=metadata,
    )


def _record(repo: DefinitionEditRepository, did: int) -> DefinitieRecord:
    rec = DefinitieRepository(repo.db_path).get_definitie(did)
    assert rec is not None
    return rec


def _voorgesteld(
    tmp_path, validatie: Any
) -> tuple[Any, DefinitionEditService, int, str]:
    repo = DefinitionEditRepository(str(tmp_path / "def624_voorstel.db"))
    service = DefinitionEditService(
        repository=repo,
        validation_service=validatie,
        proposal_service=SourceProposalService(FakeAI()),
    )
    did = repo.save(_definition(scenario="fail"))
    aanvraag = asyncio.run(service.vraag_verbetervoorstel(did, actor=ACTOR))
    assert aanvraag["status"] == "proposed", aanvraag
    return repo, service, did, aanvraag["proposal_id"]


def test_toepassen_weigert_een_hertoetsing_zonder_runstatus(tmp_path) -> None:
    """Echte hertoetsing, echte SQLite; alleen de discriminator ontbreekt."""
    zonder = _ZonderStatus(_echte_validatie(FakeBronbeoordeling("pass")))
    repo, service, did, pid = _voorgesteld(tmp_path, zonder)
    versie = _record(repo, did).version_number

    uit = asyncio.run(service.pas_voorstel_toe(did, pid, actor=ACTOR))

    assert zonder.calls == 1
    assert uit["status"] == "technical_error", uit
    assert "validation_status" in uit["message"] or "runbewijs" in uit["message"]
    rec = _record(repo, did)
    assert rec.get_definitie_tekst() == TEKST
    assert rec.version_number == versie
    assert rec.get_source_proposal(pid)["status"] == "proposed"


def test_repository_weigert_toepassing_zonder_runstatus(tmp_path) -> None:
    """De opslaggrens zelf (apply_source_proposal), los van de servicelaag."""
    echte = _echte_validatie(FakeBronbeoordeling("pass"))
    repo, service, did, pid = _voorgesteld(tmp_path, echte)
    record = _record(repo, did)
    kandidaat = record.get_source_proposal(pid)["outcome"]["candidate_text"]
    hertoetsing = asyncio.run(service._hertoets_kandidaat(did, record, kandidaat))
    assert isinstance(hertoetsing, dict), hertoetsing
    assert hertoetsing["validation_status"] == VALIDATION_STATUS_VALIDATED

    zonder_status = dict(hertoetsing)
    zonder_status.pop("validation_status")
    uit = repo.apply_source_proposal(
        did,
        pid,
        updated_by=ACTOR,
        expected_version=record.version_number,
        validation=zonder_status,
        source_assessment=dict(hertoetsing["source_assessment"]),
    )
    assert uit.status == "technical_error", uit
    assert "validation_status" in (uit.reason or "")
    assert _record(repo, did).get_definitie_tekst() == TEKST
    assert _record(repo, did).validation_score is None

    # Tegenhanger: hetzelfde resultaat mét status wordt wél toegepast.
    toegepast = repo.apply_source_proposal(
        did,
        pid,
        updated_by=ACTOR,
        expected_version=record.version_number,
        validation=dict(hertoetsing),
        source_assessment=dict(hertoetsing["source_assessment"]),
    )
    assert toegepast.status == "applied", toegepast
    assert _record(repo, did).get_definitie_tekst() == kandidaat


def test_sessieresultaat_zonder_status_geldt_als_technisch_onbekend(tmp_path) -> None:
    """De bronbasis leest de status van een sessieresultaat via het contract."""
    repo = DefinitionEditRepository(str(tmp_path / "def624_basis.db"))
    ai = FakeAI()
    service = DefinitionEditService(
        repository=repo,
        validation_service=_echte_validatie(FakeBronbeoordeling("fail")),
        proposal_service=SourceProposalService(ai),
    )
    # Het record draagt zelf geen beoordeling: de sessie is de enige bron.
    did = repo.save(_definition(scenario="fail", source_assessment=None))
    rec = _record(repo, did)
    beoordeling = bouw_beoordeling(
        BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="fail", peildatum="2026-09-15"
    )
    sessie = {"source_assessment": beoordeling}  # geen validation_status

    basis = service.bronbasis_van_record(rec, sessie)
    assert basis["bron"] == "sessie"
    assert basis["validation_status"] == VALIDATION_STATUS_UNKNOWN

    uit = asyncio.run(
        service.vraag_verbetervoorstel(did, actor=ACTOR, huidig_resultaat=sessie)
    )
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_TECHNISCH
    assert ai.calls == 0


def test_diagnose_behandelt_een_ongeldige_status_als_technisch() -> None:
    assert (
        diagnose_bronbasis(None, None, validation_status="VALIDATED").oorzaak
        == OORZAAK_TECHNISCH
    )
    assert (
        diagnose_bronbasis(None, None, validation_status="validation_unknown").oorzaak
        == OORZAAK_TECHNISCH
    )


# ------------------------------------------------------------ 3. exportgate


def _export_record() -> DefinitieRecord:
    return DefinitieRecord(
        begrip="keurmerk",
        definitie="kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend",
        categorie="type",
        organisatorische_context='["Stichting Zilver"]',
        juridische_context='["privaatrecht"]',
        wettelijke_basis='["Regeling Z"]',
        status="review",
    )


@pytest.mark.parametrize(
    "resultaat",
    [
        pytest.param({"is_acceptable": True, "system": {}}, id="afwezig"),
        pytest.param(
            {"is_acceptable": True, "validation_status": None, "system": {}},
            id="null",
        ),
        pytest.param(
            {"is_acceptable": True, "validation_status": "ok", "system": {}},
            id="ongeldig",
        ),
    ],
)
@pytest.mark.asyncio
async def test_exportgate_blokkeert_zonder_runbewijs(
    tmp_path, resultaat: dict[str, Any]
) -> None:
    from services.export_service import ExportFormat, ExportService

    repo = DefinitionRepository(str(tmp_path / "def624_export.db"))
    did = repo.legacy_repo.create_definitie(_export_record())
    spy = AsyncMock()
    spy.validate_text.return_value = {"version": "2.0.0", **resultaat}
    service = ExportService(
        repository=repo.legacy_repo,
        export_dir=str(tmp_path / "exports"),
        validation_orchestrator=spy,
        enable_validation_gate=True,
    )

    with pytest.raises(ValueError, match="geblokkeerd"):
        await service.export_definitie_async(definitie_id=did, format=ExportFormat.TXT)
    assert spy.validate_text.await_count == 1


@pytest.mark.asyncio
async def test_exportgate_laat_een_validated_resultaat_door(tmp_path) -> None:
    from pathlib import Path

    from services.export_service import ExportFormat, ExportService

    repo = DefinitionRepository(str(tmp_path / "def624_export_ok.db"))
    did = repo.legacy_repo.create_definitie(_export_record())
    spy = AsyncMock()
    spy.validate_text.return_value = {
        "version": "2.0.0",
        "validation_status": VALIDATION_STATUS_VALIDATED,
        "is_acceptable": True,
        "system": {},
    }
    service = ExportService(
        repository=repo.legacy_repo,
        export_dir=str(tmp_path / "exports"),
        validation_orchestrator=spy,
        enable_validation_gate=True,
    )

    pad = await service.export_definitie_async(
        definitie_id=did, format=ExportFormat.TXT
    )
    assert Path(pad).exists()
