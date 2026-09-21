"""DEF-766 correctieronde 1 — gekoppelde actieproef vaststellen én exporteren.

Echte keten: `ValidationOrchestratorV2` → `ModularValidationService` (echte
regelset) met een fake `Ess03AssessmentService` levert de ESS-03-uitkomst
(pass, fail, not_applicable) voor een record in een echte tijdelijke
SQLite-repository; de validatie-uitkomst wordt zoals in de app als
`validation_issues`/`validation_score` op het record vastgelegd. Daarna lopen
de échte vaststelroute (`DefinitionWorkflowService.approve` met de echte
`WorkflowService`) en de échte exportroute (`ExportService` met en zonder
validatiegate). Bewezen: de gate- en exportuitkomsten zijn voor een
negatieve ESS-03 identiek aan die voor een positieve (geen nieuwe blokkade,
ESS-03 komt in geen blokkadereden voor), terwijl de bestaande blokkades door
andere regels (scoregate DEF-622/630, CON-01/CON-02) in beide gevallen exact
behouden blijven; de negatieve ESS-03-uitkomst is wél zichtbaar in de
exportinhoud. Geen zelf samengesteld issue: de issues komen uit de echte
evaluatoruitvoer.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from database.models import issues_uit_validatieresultaat
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.export_service import ExportFormat, ExportService
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from services.workflow_service import WorkflowService
from tests.fixtures.def766_fakes import FakeEss03Assessor
from toetsregels.manager import get_toetsregel_manager
from ui.components.validation_renderer import ValidationRenderer

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
TOELICHTING = "Synthetische conventie: elk gescheiden aaneengesloten vlak telt als één."


def _definition() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=["Synthetisch Waterschap"],
        juridische_context=["waterrecht"],
        wettelijke_basis=["Synthetische Waterwet"],
        metadata={"status": "review", "created_by": "generator"},
    )


def _wrapper(scenario: str) -> tuple[ValidationOrchestratorV2, FakeEss03Assessor]:
    assessor = FakeEss03Assessor(scenario=scenario)
    wrapper = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        ess03_assessment_service=assessor,
    )
    return wrapper, assessor


async def _record_met_echte_validatie(tmp_path, scenario: str) -> dict[str, Any]:
    """Record + echte validatie-uitkomst (incl. echte ESS-03-evaluatoruitvoer)."""
    repo = DefinitionRepository(str(tmp_path / f"actie-{scenario}.db"))
    did = repo.save(_definition())
    wrapper, assessor = _wrapper(scenario)
    geladen = repo.get(did)
    result = await wrapper.validate_definition(geladen)
    assert assessor.calls, "de ESS-03-dienst is niet aangeroepen"
    assert (
        result["rule_statuses"]["ESS-03"]
        == {
            "pass": "pass",
            "fail": "fail",
            "not_applicable": "not_applicable",
        }[scenario]
    )
    # Zoals de app: violations → validation_issues; overall_score (None,
    # regels zonder cijfer) → validation_score.
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
    record = repo.get_definitie(did)
    return {
        "repo": repo,
        "did": did,
        "record": record,
        "result": result,
        "wrapper": wrapper,
        "assessor": assessor,
        "issues": issues_uit_validatieresultaat(result),
    }


class TestVaststellen:
    async def test_negatieve_ess03_voegt_geen_vaststelblokkade_toe_en_andere_blijven(
        self, tmp_path
    ):
        basis = await _record_met_echte_validatie(tmp_path, "pass")
        negatief = await _record_met_echte_validatie(tmp_path, "fail")
        # De echte ESS-03-violation staat op het record — zichtbaar, niet kritiek.
        ess03_issues = [i for i in negatief["issues"] if i["rule_id"] == "ESS-03"]
        assert len(ess03_issues) == 1 and ess03_issues[0]["severity"] == "warning"
        assert not [i for i in basis["issues"] if i["rule_id"] == "ESS-03"]

        uitkomsten = {}
        for naam, geval in (("pass", basis), ("fail", negatief)):
            dienst = DefinitionWorkflowService(
                workflow_service=WorkflowService(), repository=geval["repo"].legacy_repo
            )
            uitkomsten[naam] = dienst.approve(
                geval["did"],
                user="reviewer-a",
                user_role="reviewer",
                expected_version=geval["record"].version_number,
            )
            # Vaststellen blijft geblokkeerd door bestaande regels (scoregate
            # DEF-622/630, CON-01/CON-02) — niet door ESS-03.
            assert uitkomsten[naam].success is False
            assert uitkomsten[naam].gate_status == "blocked"
            assert (
                geval["repo"].get_definitie(geval["did"]).status == "review"
            ), "status mag niet veranderen bij een geblokkeerde vaststelling"
        assert uitkomsten["fail"].gate_reasons == uitkomsten["pass"].gate_reasons
        assert uitkomsten[
            "fail"
        ].gate_reasons, "de bestaande blokkades moeten zichtbaar zijn"
        assert not any("ESS-03" in r for r in uitkomsten["fail"].gate_reasons)
        assert any("CON-0" in r for r in uitkomsten["fail"].gate_reasons)

    async def test_niet_van_toepassing_verandert_de_vaststelgate_evenmin(
        self, tmp_path
    ):
        basis = await _record_met_echte_validatie(tmp_path, "pass")
        nvt = await _record_met_echte_validatie(tmp_path, "not_applicable")
        gate_basis = DefinitionWorkflowService(
            workflow_service=WorkflowService(), repository=basis["repo"].legacy_repo
        ).preview_gate(basis["did"])
        gate_nvt = DefinitionWorkflowService(
            workflow_service=WorkflowService(), repository=nvt["repo"].legacy_repo
        ).preview_gate(nvt["did"])
        assert gate_nvt == gate_basis


class TestExporteren:
    async def test_export_met_validatiegate_is_voor_negatieve_ess03_gelijk(
        self, tmp_path
    ):
        uitkomsten = {}
        for scenario in ("pass", "fail"):
            geval = await _record_met_echte_validatie(tmp_path, scenario)
            export = ExportService(
                repository=geval["repo"].legacy_repo,
                export_dir=str(tmp_path / "exports"),
                validation_orchestrator=geval["wrapper"],
                enable_validation_gate=True,
            )
            try:
                # JSON schrijft in export_dir (TXT schrijft cwd-relatief).
                await export.export_definitie_async(
                    definitie_id=geval["did"], format=ExportFormat.JSON
                )
                uitkomsten[scenario] = "geëxporteerd"
            except ValueError as exc:
                uitkomsten[scenario] = str(exc)
        # De gate draait de echte wrapper (dus de echte ESS-03-evaluator) op
        # het record; de bestaande gate (is_acceptable, scoregate) beslist —
        # voor beide gelijk; ESS-03 voegt geen exportblokkade toe.
        assert len(geval["assessor"].calls) == 2  # validatie + gate-run
        assert uitkomsten["fail"] == uitkomsten["pass"]
        assert uitkomsten["fail"].startswith("Export geblokkeerd")
        assert "ESS-03" not in uitkomsten["fail"]

    async def test_export_zonder_gate_toont_de_negatieve_ess03_zonder_te_blokkeren(
        self, tmp_path, monkeypatch
    ):
        geval = await _record_met_echte_validatie(tmp_path, "fail")
        # Zoals de app: het echte validatieresultaat wordt via ValidationRenderer
        # omgezet naar de regels van `beoordeling_gen` → `toetsresultaten`.
        toetsresultaten = ValidationRenderer().build_detailed_assessment(
            geval["result"]
        )
        assert any(r.startswith("⚠️ ESS-03") for r in toetsresultaten)
        export = ExportService(
            repository=geval["repo"].legacy_repo,
            export_dir=str(tmp_path / "exports"),
            enable_validation_gate=False,
        )
        monkeypatch.chdir(tmp_path)  # de TXT-export schrijft naar ./exports
        pad = await export.export_definitie_async(
            definitie_id=geval["did"],
            additional_data={"toetsresultaten": toetsresultaten},
            format=ExportFormat.TXT,
        )
        tekst = (tmp_path / pad).read_text(encoding="utf-8")
        assert BEGRIP in tekst
        assert "ESS-03" in tekst  # zichtbaar in de exportinhoud, niet blokkerend
        assert "AI-beoordeling" in tekst
