"""DEF-772 WP4 — gekoppelde actieproef: vaststellen, menselijke afwijking en export.

Echte keten: `ValidationOrchestratorV2` → `ModularValidationService` (echte
regelset) met een fake `Int03AssessmentService` levert de INT-03-uitkomst
(pass, fail, geen verwijzend woord) voor een record in een echte tijdelijke
SQLite-repository; de beoordeling wordt via de echte editor-servicelaag
(`DefinitionEditService.save_definition`) gebonden op het record vastgelegd
en de validatie-uitkomst zoals in de app als `validation_issues` op het record
gezet. Daarna lopen de échte vaststelroute (`DefinitionWorkflowService.approve`
met de echte `WorkflowService` en het gedeelde poortbeleid) en de échte
exportroute (`ExportService`/`DataAggregationService`, met en zonder
validatiegate). Bewezen:

* de gate- en exportuitkomsten zijn voor een negatieve INT-03 identiek aan
  die voor een positieve (geen eigen INT-03-poort, INT-03 in geen
  blokkadereden); een blokkade door andere regels blijft in beide gevallen;
* de menselijke afwijkingsroute is de bestaande expertvaststelling: de expert
  stelt een definitie mét negatieve AI-verwijzingsbeoordeling vast, met
  motivering; de menselijke beslissing (approved_by/approval_notes/status)
  wordt afzonderlijk bewaard en overschrijft het oorspronkelijke AI-oordeel
  niet — dat blijft gebonden en zichtbaar als AI-beoordeling;
* de export draagt de actuele gestructureerde uitkomst mét binding; een
  stale (tekst gewijzigd), niet-gebonden (andere prompt/model) of ontbrekende
  beoordeling wordt in de exportinhoud nooit een actuele goedkeuring
  (readback uit de geschreven bestanden: JSON, CSV, TXT, enkel en bulk).
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from database.definitie_repository import DefinitieRepository, DefinitieStatus
from database.models import issues_uit_validatieresultaat
from domain.int03.contract import Beoordelingsbinding
from domain.int03.opslag import INT03_ASSESSMENT_KEY
from services.data_aggregation_service import DataAggregationService
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.export_service import ExportFormat, ExportLevel, ExportService
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from services.workflow_service import WorkflowService
from tests.fixtures.def743_fakes import geen_bron_uitzondering_marker
from tests.fixtures.def772_fakes import BINDING, FakeInt03Assessor
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
TEKST = "Beschrijving van een verzameling documenten die bij een zaak horen."
TEKST_ZONDER = "Beschrijving van een verzameling documenten van een archiefvormer."
TOELICHTING = "Synthetische toelichting bij de archiefkaart."
ORG = ["Stichting Zilver"]
JUR = ["privaatrecht"]
WET = ["Regeling Z"]
ACTOR = "synthetische-expert"
NOTITIE = "Expertoordeel: 'die' verwijst in dit vakgebied eenduidig naar documenten."


def _definition(tekst: str = TEKST) -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=tekst,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata={"status": "review", "created_by": "generator"},
    )


def _wrapper(scenario: str) -> tuple[ValidationOrchestratorV2, FakeInt03Assessor]:
    assessor = FakeInt03Assessor(scenario=scenario)
    wrapper = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=NullDefinitionRepository()
        ),
        int03_assessment_service=assessor,
    )
    return wrapper, assessor


async def _record_met_echte_validatie(
    tmp_path, scenario: str, *, tekst: str = TEKST
) -> dict[str, Any]:
    """Record + echte validatie-uitkomst (incl. echte INT-03-evaluatoruitvoer),
    beoordeling via de editor-servicelaag gebonden opgeslagen."""
    pad = tmp_path / f"actie-{scenario}.db"
    repo = DefinitionEditRepository(str(pad))
    did = repo.save(_definition(tekst))
    wrapper, assessor = _wrapper(scenario)
    geladen = repo.get(did)
    result = await wrapper.validate_definition(geladen)
    assert assessor.calls, "de INT-03-dienst is niet aangeroepen"
    verwacht = {"pass": "pass", "fail": "fail", "no_word": "pass"}[scenario]
    assert result["rule_statuses"]["INT-03"] == verwacht
    document = result["rule_results"]["INT-03"]["assessment"]

    # Zoals de editor: 'Opslaan' na 'Valideren' legt de gebonden beoordeling vast.
    service = DefinitionEditService(repository=repo, validation_service=None)
    opslag = service.save_definition(
        did,
        {
            "begrip": geladen.begrip,
            "definitie": geladen.definitie,
            "toelichting": geladen.toelichting,
            "organisatorische_context": list(geladen.organisatorische_context),
            "juridische_context": list(geladen.juridische_context),
            "wettelijke_basis": list(geladen.wettelijke_basis),
            "categorie": geladen.categorie,
            "status": "review",
            "version_number": geladen.metadata["version_number"],
        },
        user="tester",
        validate=False,
        int03_assessment=document,
        int03_binding=BINDING,
    )
    assert opslag["success"] and opslag["int03_assessment_persisted"], opslag

    # Zoals de app: violations → validation_issues. Hier alleen de INT-03-issue
    # uit de echte evaluatoruitvoer plus de gedocumenteerde CON-02-uitzondering
    # (record zonder bronnen), zodat de proef INT-03 isoleert; de overige
    # gatecomponenten zijn synthetisch positief (score; DEF-630 blijft eigenaar).
    record = repo.get_definitie(did)
    int03_issues = [
        i for i in issues_uit_validatieresultaat(result) if i["rule_id"] == "INT-03"
    ]
    marker = geen_bron_uitzondering_marker(
        BEGRIP,
        record.get_definitie_tekst(),
        record.get_contextlijsten(),
        actor=ACTOR,
        version_number=record.version_number,
    )
    repo.legacy_repo.update_definitie(
        did,
        {
            "validation_score": 0.9,
            "validation_issues": json.dumps(
                [*int03_issues, marker], ensure_ascii=False
            ),
        },
        "actieproef",
    )
    record = repo.get_definitie(did)
    return {
        "pad": pad,
        "repo": repo,
        "did": did,
        "record": record,
        "result": result,
        "wrapper": wrapper,
        "assessor": assessor,
        "document": document,
        "int03_issues": int03_issues,
    }


def _workflow(geval: dict[str, Any]) -> DefinitionWorkflowService:
    return DefinitionWorkflowService(
        workflow_service=WorkflowService(), repository=geval["repo"].legacy_repo
    )


def _exportservice(
    pad: Path,
    tmp_path: Path,
    *,
    binding: Any = BINDING,
    **extra: Any,
) -> ExportService:
    repo = DefinitieRepository(str(pad))
    return ExportService(
        repository=repo,
        data_aggregation_service=DataAggregationService(repo, int03_binding=binding),
        export_dir=str(tmp_path / "exports"),
        **extra,
    )


def _bulk(pad: Path, tmp_path: Path, did: int, formaat: ExportFormat, **kw) -> Path:
    repo = DefinitieRepository(str(pad))
    resultaat = _exportservice(pad, tmp_path, **kw).export_multiple_definitions(
        [repo.get_definitie(did)], format=formaat, level=ExportLevel.COMPLEET
    )
    return Path(resultaat.path)


def _json_rij(pad: Path, tmp_path: Path, did: int, **kw) -> dict:
    inhoud = _bulk(pad, tmp_path, did, ExportFormat.JSON, **kw).read_text(
        encoding="utf-8"
    )
    [rij] = json.loads(inhoud)["definities"]
    return rij


def _csv_int03(pad: Path, tmp_path: Path, did: int) -> dict:
    with open(_bulk(pad, tmp_path, did, ExportFormat.CSV), newline="") as f:
        [rij] = list(csv.DictReader(f))
    return json.loads(rij["int03_beoordeling"])


class TestVaststellen:
    async def test_negatieve_int03_voegt_geen_vaststelblokkade_toe(self, tmp_path):
        basis = await _record_met_echte_validatie(tmp_path, "pass")
        negatief = await _record_met_echte_validatie(tmp_path, "fail")
        # De echte INT-03-violation staat op het record — zichtbaar, advisory.
        assert len(negatief["int03_issues"]) == 1
        assert negatief["int03_issues"][0]["severity"] == "warning"
        assert basis["int03_issues"] == []

        gate_basis = _workflow(basis).preview_gate(basis["did"])
        gate_negatief = _workflow(negatief).preview_gate(negatief["did"])
        assert gate_negatief == gate_basis
        assert not any("INT-03" in r for r in gate_negatief["reasons"])

    async def test_andere_blokkades_blijven_voor_beide_gelijk(self, tmp_path):
        basis = await _record_met_echte_validatie(tmp_path, "pass")
        negatief = await _record_met_echte_validatie(tmp_path, "fail")
        for geval in (basis, negatief):
            # Zonder totaalscore sluit de bestaande scorepoort (DEF-622/630);
            # welke uitkomst zij precies geeft blijft haar beleid — hier telt
            # dat die voor beide gevallen gelijk is en niet 'pass'.
            geval["repo"].legacy_repo.update_definitie(
                geval["did"], {"validation_score": None}, "actieproef"
            )
        gate_basis = _workflow(basis).preview_gate(basis["did"])
        gate_negatief = _workflow(negatief).preview_gate(negatief["did"])
        assert gate_basis["status"] != "pass"
        assert gate_negatief["status"] == gate_basis["status"]
        assert gate_negatief["reasons"] == gate_basis["reasons"]
        assert gate_negatief["reasons"], "de scorepoort benoemt haar reden"
        assert not any("INT-03" in r for r in gate_negatief["reasons"])

    async def test_expert_stelt_vast_ondanks_negatieve_ai_beoordeling(self, tmp_path):
        """De menselijke afwijkingsroute (K2/ADR-001): de bestaande
        expertvaststelling met motivering. Geen verzonnen goedkeuring, geen
        overschrijving van het AI-oordeel."""
        negatief = await _record_met_echte_validatie(tmp_path, "fail")
        record_voor = negatief["record"]
        document_voor = deepcopy(record_voor.get_int03_assessment())
        assert document_voor == negatief["document"]

        uitkomst = _workflow(negatief).approve(
            negatief["did"],
            user=ACTOR,
            user_role="reviewer",
            notes=NOTITIE,
            expected_version=record_voor.version_number,
        )
        assert uitkomst.success is True, uitkomst.error_message

        na = negatief["repo"].get_definitie(negatief["did"])
        assert na.status == DefinitieStatus.ESTABLISHED.value
        assert na.approved_by == ACTOR
        assert na.approval_notes == NOTITIE
        assert na.version_number == record_voor.version_number + 1
        # Het AI-oordeel is niet overschreven en niet als menselijk oordeel
        # herschreven: hetzelfde document, geen historie, nog gebonden.
        assert na.get_int03_assessment() == document_voor
        assert na.get_int03_assessment_history() == []
        assert na.get_definitie_tekst() == TEKST
        from services.definition_edit_service import int03_uitkomst_van_definition

        replay = int03_uitkomst_van_definition(
            DefinitionRepository(str(negatief["pad"])).get(negatief["did"]),
            binding=BINDING,
        )
        assert replay["status"] == "fail"
        assert replay["review"]["assessment"]["applied"] is True
        assert replay["parts"][0]["field"] == "int03_assessment"  # AI-herkomst
        # De INT-03-violation blijft als AI-bevinding op het record staan.
        assert [
            i for i in na.get_validation_issues_list() if i.get("rule_id") == "INT-03"
        ] == negatief["int03_issues"]

        # Export: AI-oordeel en menselijke beslissing afzonderlijk zichtbaar.
        rij = _json_rij(negatief["pad"], tmp_path, negatief["did"])
        assert rij["status"] == "established"
        assert rij["approved_by"] == ACTOR
        assert rij["approval_notes"] == NOTITIE
        int03 = rij["int03_beoordeling"]
        assert int03["status"] == "fail" and int03["applied"] is True
        assert int03["verdict"] == "fail"
        assert int03["binding"]["model"] == "fake-int03-model"
        assert int03["document"] == document_voor
        assert "AI" in int03["herkomst"]
        txt = _bulk(negatief["pad"], tmp_path, negatief["did"], ExportFormat.TXT)
        inhoud = txt.read_text(encoding="utf-8")
        assert "INT-03 — voldoet niet" in inhoud
        assert "AI-beoordeling" in inhoud
        assert f"Goedgekeurd door: {ACTOR}" in inhoud
        assert NOTITIE in inhoud

    async def test_expert_kan_ook_de_geen_voornaamwoord_uitkomst_vaststellen(
        self, tmp_path
    ):
        geval = await _record_met_echte_validatie(
            tmp_path, "no_word", tekst=TEKST_ZONDER
        )
        uitkomst = _workflow(geval).approve(
            geval["did"],
            user=ACTOR,
            user_role="reviewer",
            notes="",
            expected_version=geval["record"].version_number,
        )
        assert uitkomst.success is True, uitkomst.error_message
        int03 = _json_rij(geval["pad"], tmp_path, geval["did"])["int03_beoordeling"]
        assert int03["status"] == "pass" and int03["applied"] is True
        assert int03["finding"] == "no_referring_word"
        assert "niet van toepassing" in int03["reason"]


class TestExporteren:
    async def test_export_met_validatiegate_is_voor_negatieve_int03_gelijk(
        self, tmp_path
    ):
        uitkomsten = {}
        aanroepen = {}
        for scenario in ("pass", "fail"):
            geval = await _record_met_echte_validatie(tmp_path, scenario)
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
                uitkomsten[scenario] = "geëxporteerd"
            except ValueError as exc:
                uitkomsten[scenario] = str(exc)
            aanroepen[scenario] = len(geval["assessor"].calls)
        # De gate draait de echte wrapper (dus de echte INT-03-evaluator) op het
        # record; de bestaande gate (is_acceptable) beslist — voor beide
        # gelijk; INT-03 voegt geen exportblokkade toe.
        assert aanroepen == {"pass": 2, "fail": 2}  # validatie + gate-run
        assert uitkomsten["fail"] == uitkomsten["pass"]
        assert uitkomsten["fail"].startswith("Export geblokkeerd")
        assert "INT-03" not in uitkomsten["fail"]

    async def test_export_draagt_de_actuele_uitkomst_met_binding(
        self, tmp_path, monkeypatch
    ):
        geval = await _record_met_echte_validatie(tmp_path, "fail")
        pad, did = geval["pad"], geval["did"]
        rij = _json_rij(pad, tmp_path, did)
        int03 = rij["int03_beoordeling"]
        assert int03["rule_id"] == "INT-03"
        assert int03["status"] == "fail"
        assert int03["applied"] is True and int03["historical"] is False
        assert int03["score"] is None
        assert int03["binding"] == {
            "prompt_version": BINDING.prompt_version,
            "norm_sha256": BINDING.norm_sha256,
            "provider": BINDING.provider,
            "model": BINDING.model,
        }
        assert int03["expected_binding"] == BINDING.als_dict()
        [verwijzing] = int03["references"]
        assert verwijzing["word"] == "die"
        assert [k["quote"] for k in verwijzing["candidates"]] == [
            "Beschrijving",
            "verzameling",
        ]
        assert int03["document"]["fingerprint"] == int03["fingerprint"]
        # Dezelfde inhoud in de CSV-cel (compacte JSON) en leesbaar in TXT.
        assert _csv_int03(pad, tmp_path, did) == int03
        txt = _bulk(pad, tmp_path, did, ExportFormat.TXT).read_text(encoding="utf-8")
        assert "Verwijzingen (INT-03)" in txt
        assert "INT-03 — voldoet niet" in txt
        assert "'die'" in txt and "'Beschrijving'" in txt
        # Enkele export (UI-exportknop): JSON, CSV en TXT.
        monkeypatch.chdir(tmp_path)
        service = _exportservice(pad, tmp_path)
        enkel_json = json.loads(
            Path(
                service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
            ).read_text(encoding="utf-8")
        )
        assert enkel_json["validatie"]["int03_beoordeling"] == int03
        enkel_csv = service.export_definitie(definitie_id=did, format=ExportFormat.CSV)
        with open(enkel_csv, newline="", encoding="utf-8") as f:
            [csv_rij] = list(csv.DictReader(f))
        assert json.loads(csv_rij["int03_beoordeling"]) == int03
        enkel_txt = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.TXT)
        ).read_text(encoding="utf-8")
        assert "Verwijzingen (INT-03)" in enkel_txt
        assert "INT-03 — voldoet niet" in enkel_txt
        assert "'die'" in enkel_txt

    async def test_stale_beoordeling_wordt_in_de_export_geen_goedkeuring(
        self, tmp_path, monkeypatch
    ):
        geval = await _record_met_echte_validatie(tmp_path, "pass")
        pad, did = geval["pad"], geval["did"]
        assert _json_rij(pad, tmp_path, did)["int03_beoordeling"]["status"] == "pass"
        # Tekstwijziging buiten de toetsing om: het document blijft, telt niet.
        assert geval["repo"].legacy_repo.update_definitie(
            did, {"definitie": TEKST + " Aangepast."}, "tester"
        )
        assert geval["repo"].get_definitie(did).get_int03_assessment() is not None
        int03 = _json_rij(pad, tmp_path, did)["int03_beoordeling"]
        assert int03["status"] == "review_required"
        assert int03["applied"] is False and int03["historical"] is True
        assert "gewijzigd" in int03["reason"]
        assert int03["verdict"] == "pass"  # zichtbaar als historie, geen pass
        assert int03["references"] == []
        assert _csv_int03(pad, tmp_path, did)["applied"] is False
        txt = _bulk(pad, tmp_path, did, ExportFormat.TXT).read_text(encoding="utf-8")
        assert "INT-03 — nog te beoordelen" in txt
        assert "niet toegepast" in txt
        monkeypatch.chdir(tmp_path)
        enkel = _exportservice(pad, tmp_path).export_definitie(
            definitie_id=did, format=ExportFormat.TXT
        )
        assert "niet toegepast" in Path(enkel).read_text(encoding="utf-8")

    async def test_andere_binding_of_onbekende_binding_is_geen_goedkeuring(
        self, tmp_path
    ):
        geval = await _record_met_echte_validatie(tmp_path, "pass")
        pad, did = geval["pad"], geval["did"]
        ander = Beoordelingsbinding(**{**BINDING.als_dict(), "model": "ander-model"})
        int03 = _json_rij(pad, tmp_path, did, binding=ander)["int03_beoordeling"]
        assert int03["status"] == "review_required"
        assert int03["applied"] is False and int03["historical"] is True
        assert "ander-model" in int03["reason"]
        assert int03["expected_binding"]["model"] == "ander-model"
        onbekend = _json_rij(pad, tmp_path, did, binding=lambda: None)[
            "int03_beoordeling"
        ]
        assert onbekend["status"] == "review_required"
        assert onbekend["applied"] is False
        assert "onbekend" in onbekend["reason"]
        assert onbekend["expected_binding"] is None

    async def test_standaardbinding_komt_uit_de_configuratie(self, tmp_path):
        """Zonder geïnjecteerde binding leest de aggregatie de actuele prompt-,
        norm- en modelbinding uit code, regelrecord en `config.yaml`; een
        document van de fake-dienst is daaraan niet gebonden."""
        from services.ai.model_router import ModelRouter
        from services.validation.int03_assessment_service import (
            Int03AssessmentService,
        )

        geval = await _record_met_echte_validatie(tmp_path, "pass")
        pad, did = geval["pad"], geval["did"]
        repo = DefinitieRepository(str(pad))
        export = ExportService(
            repository=repo,
            data_aggregation_service=DataAggregationService(repo),
            export_dir=str(tmp_path / "exports"),
        )
        uit = Path(
            export.export_multiple_definitions(
                [repo.get_definitie(did)],
                format=ExportFormat.JSON,
                level=ExportLevel.COMPLEET,
            ).path
        )
        [rij] = json.loads(uit.read_text(encoding="utf-8"))["definities"]
        int03 = rij["int03_beoordeling"]
        provider, model = ModelRouter.from_config().get_model("validation")
        assert int03["expected_binding"]["prompt_version"] == (
            Int03AssessmentService.PROMPT_VERSION
        )
        assert int03["expected_binding"]["provider"] == provider
        assert int03["expected_binding"]["model"] == model
        assert int03["applied"] is False and int03["historical"] is True

    async def test_record_zonder_beoordeling_is_zichtbaar_niet_beoordeeld(
        self, tmp_path, monkeypatch
    ):
        pad = tmp_path / "leeg.db"
        repo = DefinitionRepository(str(pad))
        did = repo.save(_definition())
        assert repo.get_definitie(did).get_int03_assessment() is None
        rij = _json_rij(pad, tmp_path, did)
        assert rij["int03_beoordeling"] == ""
        monkeypatch.chdir(tmp_path)
        service = _exportservice(pad, tmp_path)
        enkel_txt = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.TXT)
        ).read_text(encoding="utf-8")
        assert "geen opgeslagen INT-03-beoordeling: niet beoordeeld" in enkel_txt
        enkel_json = json.loads(
            Path(
                service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
            ).read_text(encoding="utf-8")
        )
        assert enkel_json["validatie"]["int03_beoordeling"] is None

    async def test_export_zonder_gate_toont_de_negatieve_int03_zonder_te_blokkeren(
        self, tmp_path, monkeypatch
    ):
        from ui.components.validation_renderer import ValidationRenderer

        geval = await _record_met_echte_validatie(tmp_path, "fail")
        toetsresultaten = ValidationRenderer().build_detailed_assessment(
            geval["result"]
        )
        assert any(r.startswith("⚠️ INT-03") for r in toetsresultaten)
        export = _exportservice(geval["pad"], tmp_path, enable_validation_gate=False)
        monkeypatch.chdir(tmp_path)
        pad = await export.export_definitie_async(
            definitie_id=geval["did"],
            additional_data={"toetsresultaten": toetsresultaten},
            format=ExportFormat.TXT,
        )
        tekst = (tmp_path / pad).read_text(encoding="utf-8")
        assert BEGRIP in tekst
        assert "INT-03" in tekst
        assert "Verwijzingen (INT-03)" in tekst
        assert "voldoet niet" in tekst
        # Exporteren wijzigt de definitietekst niet.
        assert geval["repo"].get_definitie(geval["did"]).get_definitie_tekst() == TEKST

    async def test_aanvullende_exportdata_kan_de_int03_uitkomst_niet_vervangen(
        self, tmp_path, monkeypatch
    ):
        geval = await _record_met_echte_validatie(tmp_path, "fail")
        monkeypatch.chdir(tmp_path)
        service = _exportservice(geval["pad"], tmp_path)
        uit = json.loads(
            Path(
                service.export_definitie(
                    definitie_id=geval["did"],
                    additional_data={"int03_beoordeling": {"status": "pass"}},
                    format=ExportFormat.JSON,
                )
            ).read_text(encoding="utf-8")
        )
        assert uit["validatie"]["int03_beoordeling"]["status"] == "fail"
        registratie = (
            geval["repo"].get_definitie(geval["did"]).get_generatieregistratie()
        )
        assert registratie[INT03_ASSESSMENT_KEY] == geval["document"]
