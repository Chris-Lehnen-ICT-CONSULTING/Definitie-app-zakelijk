"""DEF-768 WP8 — gekoppelde actieproef vaststellen én exporteren voor ESS-05.

Echte keten: `ValidationOrchestratorV2` → `ModularValidationService` (echte
regelset) met een fake `Ess05AssessmentService` levert de ESS-05-uitkomst
voor een record in een echte tijdelijke SQLite-repository, met een door de
gebruiker bevestigd verwant begrip op het record. De uitkomst wordt zoals in de
app als `validation_issues`/`validation_score` vastgelegd. Daarna lopen de
échte vaststelroute (`DefinitionWorkflowService`) en de échte exportroute
(`ExportService` met en zonder validatiegate). Bewezen: een negatieve ESS-05
(K-8, 'voldoet niet'), een open uitkomst en een technische fout voegen geen
blokkade toe — gate- en exportuitkomsten zijn gelijk aan die bij 'voldoet';
ESS-05 komt in geen blokkadereden voor; de negatieve uitkomst is wél
zichtbaar in de exportinhoud.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from database.models import issues_uit_validatieresultaat
from domain.ess05.expertacties import voeg_buur_toe
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.export_service import ExportFormat, ExportService
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from services.workflow_service import WorkflowService
from tests.fixtures.def768_fakes import FakeEss05Assessor
from toetsregels.manager import get_toetsregel_manager
from ui.components.validation_renderer import ValidationRenderer

pytestmark = [pytest.mark.unit]

BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
VERWACHT = {
    "pass": "pass",
    "lacks": "fail",
    "error": "error",
    "open": "review_required",
}


def _definition() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="type",
        organisatorische_context=["Synthetische Uitleendienst"],
        juridische_context=["leenrecht"],
        wettelijke_basis=["Synthetische Leenwet"],
        metadata={
            "status": "review",
            "created_by": "generator",
            "ess05_buren": voeg_buur_toe(
                [],
                "werknemer",
                "Persoon met een arbeidsovereenkomst met de instelling.",
                actor="deskundige",
                at="2026-09-23T12:00:00+00:00",
            ),
        },
    )


async def _record_met_echte_validatie(tmp_path, scenario: str) -> dict[str, Any]:
    repo = DefinitionRepository(str(tmp_path / f"actie-{scenario}.db"))
    did = repo.save(_definition())
    assessor = FakeEss05Assessor(scenario=scenario)
    wrapper = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        ess05_assessment_service=assessor,
    )
    result = await wrapper.validate_definition(repo.get(did))
    assert assessor.calls, "de ESS-05-dienst is niet aangeroepen"
    assert result["rule_statuses"]["ESS-05"] == VERWACHT[scenario]
    repo.legacy_repo.update_definitie(
        did,
        {
            "validation_score": result["overall_score"],
            "validation_issues": json.dumps(
                issues_uit_validatieresultaat(result), ensure_ascii=False
            ),
        },
        "actieproef",
    )
    return {
        "repo": repo,
        "did": did,
        "record": repo.get_definitie(did),
        "result": result,
        "wrapper": wrapper,
        "assessor": assessor,
        "issues": issues_uit_validatieresultaat(result),
    }


def _workflow(geval) -> DefinitionWorkflowService:
    return DefinitionWorkflowService(
        workflow_service=WorkflowService(), repository=geval["repo"].legacy_repo
    )


class TestVaststellen:
    async def test_negatieve_ess05_staat_als_waarschuwing_op_het_record(self, tmp_path):
        basis = await _record_met_echte_validatie(tmp_path, "pass")
        negatief = await _record_met_echte_validatie(tmp_path, "lacks")
        assert not [i for i in basis["issues"] if i["rule_id"] == "ESS-05"]
        [issue] = [i for i in negatief["issues"] if i["rule_id"] == "ESS-05"]
        assert issue["severity"] == "warning"

    @pytest.mark.parametrize("scenario", ["lacks", "error", "open"])
    async def test_ess05_voegt_geen_vaststelblokkade_toe(self, tmp_path, scenario):
        basis = await _record_met_echte_validatie(tmp_path, "pass")
        ander = await _record_met_echte_validatie(tmp_path, scenario)
        uitkomsten = {}
        for naam, geval in (("pass", basis), (scenario, ander)):
            uitkomsten[naam] = _workflow(geval).approve(
                geval["did"],
                user="reviewer-a",
                user_role="reviewer",
                expected_version=geval["record"].version_number,
            )
        assert uitkomsten[scenario].success == uitkomsten["pass"].success
        assert uitkomsten[scenario].gate_status == uitkomsten["pass"].gate_status
        assert uitkomsten[scenario].gate_reasons == uitkomsten["pass"].gate_reasons
        assert not any("ESS-05" in r for r in uitkomsten[scenario].gate_reasons)
        assert _workflow(ander).preview_gate(ander["did"]) == _workflow(
            basis
        ).preview_gate(basis["did"])


class TestExporteren:
    @pytest.mark.parametrize("scenario", ["lacks", "error"])
    async def test_export_met_validatiegate_is_gelijk(self, tmp_path, scenario):
        uitkomsten = {}
        for naam in ("pass", scenario):
            geval = await _record_met_echte_validatie(tmp_path, naam)
            export = ExportService(
                repository=geval["repo"].legacy_repo,
                export_dir=str(tmp_path / "exports"),
                validation_orchestrator=geval["wrapper"],
                enable_validation_gate=True,
            )
            try:
                await export.export_definitie_async(
                    definitie_id=geval["did"], format=ExportFormat.JSON
                )
                uitkomsten[naam] = "geëxporteerd"
            except ValueError as exc:
                uitkomsten[naam] = str(exc)
            assert len(geval["assessor"].calls) == 2  # validatie + gate-run
        assert uitkomsten[scenario] == uitkomsten["pass"]
        assert "ESS-05" not in uitkomsten[scenario]

    async def test_export_zonder_gate_toont_de_negatieve_ess05(
        self, tmp_path, monkeypatch
    ):
        geval = await _record_met_echte_validatie(tmp_path, "lacks")
        toetsresultaten = ValidationRenderer().build_detailed_assessment(
            geval["result"]
        )
        assert any(r.startswith("⚠️ ESS-05") for r in toetsresultaten)
        export = ExportService(
            repository=geval["repo"].legacy_repo,
            export_dir=str(tmp_path / "exports"),
            enable_validation_gate=False,
        )
        monkeypatch.chdir(tmp_path)
        pad = await export.export_definitie_async(
            definitie_id=geval["did"],
            additional_data={"toetsresultaten": toetsresultaten},
            format=ExportFormat.TXT,
        )
        tekst = (tmp_path / pad).read_text(encoding="utf-8")
        assert BEGRIP in tekst
        assert "ESS-05" in tekst
        assert "AI-beoordeling" in tekst
