"""DEF-766: de ESS-03-beoordeling duurzaam opslaan, heropenen, opnieuw toetsen; niet blokkeren.

Alles via de publieke servicelaag op een tijdelijke, echte SQLite-database,
telkens herladen met een vérse repository-instantie. Bewezen (en niet meer):

* een aan de kandidaat gebonden ESS-03-beoordeling overleeft opslaan →
  ID-only herladen exact (`metadata["ess03_assessment"]`), inclusief de
  gebruikte verduidelijking; de replay op het herladen record geeft dezelfde
  uitkomst;
* een nieuwe beoordeling vervangt de vorige mét append-only historie; een
  gelijke beoordeling is geen wijziging; een tekstwijziging laat de opgeslagen
  beoordeling staan maar de replay past haar niet meer toe (stale, benoemd);
* de editor-opslaan legt alleen een beoordeling vast die exact aan de op te
  slaan kandidaat bindt en `assessed` is, en benoemt anders waarom niet;
* een negatieve ESS-03-uitkomst verandert de vaststelgate en de
  herstelselectie niet (bestaande blokkades blijven, er komt geen bij).
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from database.definitie_repository import DefinitieStatus
from database.models import ESS03_ASSESSMENT_HISTORY_KEY, ESS03_ASSESSMENT_KEY
from domain.ess03.contract import Intentie
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    bindingsafwijzing_ess03,
    ess03_uitkomst_van_definition,
)
from services.definition_repository import DefinitionRepository
from services.exceptions import RepositoryError
from services.interfaces import Definition
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
TOELICHTING = "Synthetische conventie: elk gescheiden aaneengesloten vlak telt als één."
ORG = ["Synthetisch Waterschap"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}


def _repo(tmp_path, naam: str = "ess03.db") -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / naam))


def _intentie(**over) -> Intentie:
    velden = {"toelichting": TOELICHTING, "categorie": "type"}
    velden.update(over)
    return Intentie(**velden)


def _beoordeling(scenario="pass", *, tekst=TEKST, intentie=None, bronnen=None) -> dict:
    return bouw_ess03_beoordeling(
        BEGRIP,
        tekst,
        CONTEXT,
        bronnen,
        intentie=intentie or _intentie(),
        scenario=scenario,
    )


def _definition(**overrides: Any) -> Definition:
    metadata = {
        "status": DefinitieStatus.DRAFT.value,
        "created_by": "generator",
        "ess03_assessment": _beoordeling(),
    }
    metadata.update(overrides.pop("metadata", {}))
    velden: dict[str, Any] = {
        "begrip": BEGRIP,
        "definitie": TEKST,
        "toelichting": TOELICHTING,
        "categorie": "type",
        "organisatorische_context": list(ORG),
        "juridische_context": [],
        "wettelijke_basis": [],
        "metadata": metadata,
    }
    velden.update(overrides)
    return Definition(**velden)


def _registratie(repo: DefinitionRepository, did: int) -> dict:
    rec = repo.get_definitie(did)
    assert rec is not None
    return rec.get_generatieregistratie() or {}


class TestOpslaanEnHerladen:
    def test_beoordeling_overleeft_opslaan_en_id_only_herladen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        vers = _repo(tmp_path).get(did)
        assert vers is not None
        opgeslagen = vers.metadata["ess03_assessment"]
        assert opgeslagen == _beoordeling()
        assert vers.metadata["ess03_assessment_history"] == []
        # De replay op het herladen record: dezelfde uitkomst, gebonden.
        uitkomst = ess03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "pass"
        assert uitkomst["review"]["assessment"]["applied"] is True
        assert uitkomst["fingerprint"] == opgeslagen["fingerprint"]

    def test_verduidelijking_reist_mee_en_wordt_hersteld(self, tmp_path):
        # Correctieronde 1 (R5): de verduidelijking is een eigen recordwaarde;
        # zij wordt uit die waarde hersteld, nooit uit de beoordeling afgeleid.
        intentie = _intentie(verduidelijking="Peil P is het zomerpeil.")
        repo = _repo(tmp_path)
        did = repo.save(
            _definition(
                metadata={
                    "ess03_verduidelijking": "Peil P is het zomerpeil.",
                    "ess03_assessment": _beoordeling(intentie=intentie),
                }
            )
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["ess03_verduidelijking"] == "Peil P is het zomerpeil."
        assert ess03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "pass"
        # Zonder eigen recordwaarde is er geen verduidelijking — ook al staat
        # er een in de beoordeling — en is die beoordeling dus niet actueel.
        did2 = _repo(tmp_path, "zonder.db").save(
            _definition(metadata={"ess03_assessment": _beoordeling(intentie=intentie)})
        )
        vers2 = _repo(tmp_path, "zonder.db").get(did2)
        assert "ess03_verduidelijking" not in vers2.metadata
        assert ess03_uitkomst_van_definition(vers2, binding=BINDING)["status"] == (
            "review_required"
        )

    def test_zonder_beoordeling_wordt_niets_verzonnen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition(metadata={"ess03_assessment": None}))
        vers = _repo(tmp_path).get(did)
        assert vers.metadata.get("ess03_assessment") is None
        assert "ess03_verduidelijking" not in vers.metadata
        assert ESS03_ASSESSMENT_KEY not in _registratie(repo, did)
        uitkomst = ess03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "review_required"
        assert uitkomst["review"]["assessment"]["applied"] is False

    def test_nieuwe_beoordeling_vervangt_met_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        versie1 = repo.get_definitie(did).version_number
        geladen = repo.get(did)
        geladen.metadata["ess03_assessment"] = _beoordeling("fail")
        repo.save(geladen)
        registratie = _registratie(repo, did)
        assert registratie[ESS03_ASSESSMENT_KEY] == _beoordeling("fail")
        [vorige] = registratie[ESS03_ASSESSMENT_HISTORY_KEY]
        assert vorige["assessment"] == _beoordeling()
        assert vorige["superseded_on_version"] == versie1
        assert vorige["superseded_at"]
        assert repo.get_definitie(did).version_number == versie1 + 1
        assert (
            ess03_uitkomst_van_definition(_repo(tmp_path).get(did), binding=BINDING)[
                "status"
            ]
            == "fail"
        )

    def test_gelijke_beoordeling_maakt_geen_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        geladen = repo.get(did)
        geladen.metadata["status"] = DefinitieStatus.REVIEW.value
        repo.save(geladen)
        registratie = _registratie(repo, did)
        assert registratie[ESS03_ASSESSMENT_KEY] == _beoordeling()
        assert registratie[ESS03_ASSESSMENT_HISTORY_KEY] == []

    def test_tekstwijziging_maakt_de_opgeslagen_beoordeling_stale(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        geladen = repo.get(did)
        geladen.definitie = TEKST + " Peil P is het zomerpeil."
        repo.save(geladen)
        vers = _repo(tmp_path).get(did)
        # Historie behouden: het document staat er nog, maar telt niet.
        assert vers.metadata["ess03_assessment"] == _beoordeling()
        uitkomst = ess03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "review_required"
        samenvatting = uitkomst["review"]["assessment"]
        assert samenvatting["applied"] is False
        assert "gewijzigd" in samenvatting["reason"]

    def test_toelichtingwijziging_maakt_de_beoordeling_stale(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        geladen = repo.get(did)
        geladen.toelichting = "Andere bedoeling."
        repo.save(geladen)
        uitkomst = ess03_uitkomst_van_definition(
            _repo(tmp_path).get(did), binding=BINDING
        )
        assert uitkomst["review"]["assessment"]["applied"] is False

    def test_misvormde_beoordeling_wordt_geweigerd_niets_geschreven(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        geladen = repo.get(did)
        geladen.metadata["ess03_assessment"] = {
            "status": "assessed"
        }  # geen fingerprint
        with pytest.raises(RepositoryError):
            repo.save(geladen)
        assert _registratie(repo, did)[ESS03_ASSESSMENT_KEY] == _beoordeling()

    def test_ruwe_niet_json_registratie_kan_de_beoordeling_niet_wissen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        with pytest.raises(ValueError, match="generation_prompt_data"):
            repo.legacy_repo.update_definitie(
                did, {"generation_prompt_data": "geen json"}, "tester"
            )
        assert _registratie(repo, did)[ESS03_ASSESSMENT_KEY] == _beoordeling()


class TestEditorOpslaan:
    def _service(self, tmp_path) -> tuple[DefinitionEditService, int]:
        repo = DefinitionEditRepository(str(tmp_path / "editor.db"))
        did = repo.save(_definition(metadata={"ess03_assessment": None}))
        return DefinitionEditService(repository=repo, validation_service=None), did

    def _updates(self, service: DefinitionEditService, did: int, **over) -> dict:
        huidig = service.repository.get(did)
        updates = {
            "begrip": huidig.begrip,
            "definitie": huidig.definitie,
            "toelichting": huidig.toelichting,
            "organisatorische_context": list(huidig.organisatorische_context),
            "juridische_context": [],
            "wettelijke_basis": [],
            "categorie": huidig.categorie,
            "status": huidig.metadata.get("status"),
            "version_number": huidig.metadata.get("version_number"),
        }
        updates.update(over)
        return updates

    def test_gebonden_sessiebeoordeling_wordt_vastgelegd(self, tmp_path):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did),
            user="tester",
            validate=False,
            ess03_assessment=_beoordeling(),
        )
        assert result["success"] is True
        assert result["ess03_assessment_persisted"] is True
        assert result["ess03_assessment_reason"] is None
        vers = service.repository.get(did)
        assert vers.metadata["ess03_assessment"] == _beoordeling()
        assert ess03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "pass"

    def test_stale_sessiebeoordeling_wordt_niet_vastgelegd_en_benoemd(self, tmp_path):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did, definitie=TEKST + " Aangepast."),
            user="tester",
            validate=False,
            ess03_assessment=_beoordeling(),
        )
        assert result["success"] is True
        assert result["ess03_assessment_persisted"] is False
        assert "gewijzigd" in result["ess03_assessment_reason"]
        assert service.repository.get(did).metadata.get("ess03_assessment") is None

    def test_technische_fout_is_geen_actueel_bewijs(self, tmp_path):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did),
            user="tester",
            validate=False,
            ess03_assessment=_beoordeling("error"),
        )
        assert result["ess03_assessment_persisted"] is False
        assert "niet uitgevoerd" in result["ess03_assessment_reason"]

    def test_bindingsafwijzing_gebruikt_de_actuele_verduidelijking_van_de_kandidaat(
        self,
    ):
        # Correctieronde 1 (R5): de verduidelijking komt van de kandidaat, niet
        # uit de beoordeling; zonder eigen waarde bindt een beoordeling mét
        # verduidelijking niet.
        intentie = _intentie(verduidelijking="Peil P.")
        met = _definition(metadata={"ess03_verduidelijking": "Peil P."})
        assert bindingsafwijzing_ess03(_beoordeling(intentie=intentie), met) is None
        zonder = _definition(metadata={})
        assert "gewijzigd" in bindingsafwijzing_ess03(
            _beoordeling(intentie=intentie), zonder
        )
        # Toelichtingwijziging: stale.
        anders = _definition(toelichting="Anders.", metadata={})
        assert "gewijzigd" in bindingsafwijzing_ess03(_beoordeling(), anders)


class TestNietBlokkerend:
    def _record(self, tmp_path, issues: list[dict]):
        # Eén database per variant: hetzelfde begrip + context is anders een
        # duplicaat (DUP_01-guard van de opslag), geen gate-verschil.
        repo = _repo(tmp_path, naam=f"gate-{len(issues)}.db")
        did = repo.save(_definition(metadata={"ess03_assessment": None}))
        repo.legacy_repo.update_definitie(
            did,
            {
                "validation_score": 0.9,
                "validation_issues": json.dumps(issues, ensure_ascii=False),
            },
            "tester",
        )
        return repo, did

    def test_negatieve_ess03_voegt_geen_vaststelblokkade_toe(self, tmp_path):
        from services.definition_workflow_service import DefinitionWorkflowService

        ess03_issue = {
            "code": "ESS-03",
            "rule_id": "ESS-03",
            "severity": "warning",
            "description": "AI-beoordeling van telbaarheid (fake): voldoet niet.",
        }
        repo_zonder, did_zonder = self._record(tmp_path, [])
        repo_met, did_met = self._record(tmp_path, [ess03_issue])
        gate_zonder = DefinitionWorkflowService(
            workflow_service=object(), repository=repo_zonder.legacy_repo
        )._evaluate_gate(repo_zonder.get_definitie(did_zonder))
        gate_met = DefinitionWorkflowService(
            workflow_service=object(), repository=repo_met.legacy_repo
        )._evaluate_gate(repo_met.get_definitie(did_met))
        assert gate_met["status"] == gate_zonder["status"]
        assert gate_met["reasons"] == gate_zonder["reasons"]
        assert not any("ESS-03" in r for r in gate_met["reasons"])

    def test_herstel_negeert_de_ess03_violation(self):
        from services.orchestrators.definition_orchestrator_v2 import (
            DefinitionOrchestratorV2,
        )

        validation_result = {
            "violations": [
                {"code": "ESS-03", "severity": "warning", "message": "x"},
                {"code": "INT-01", "severity": "error", "message": "y"},
            ],
            "rule_results": {"ESS-03": {"status": "fail", "score": None}},
        }
        herstelbaar = DefinitionOrchestratorV2._herstelbare_overtredingen(
            validation_result
        )
        assert [v["code"] for v in herstelbaar] == ["INT-01"]
