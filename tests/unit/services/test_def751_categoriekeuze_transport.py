"""DEF-751 B2 — transport van de categoriekeuze door de servicelaag.

* Nieuw record (`DefinitionRepository.save`): de keuze-invoer in
  `metadata["category_choice_input"]` is onbevestigde invoer — alleen
  herkomst manual/model + reasoning/scores worden gelezen; een meegestuurde
  actor wordt genegeerd (nooit een gefabriceerde bevestiging), een herkomst
  die alleen in een eigen route mag ontstaan wordt geweigerd (niets
  opgeslagen). Generatiegebonden: `generation_id` + tekstvingerafdruk.
* Bewezen default: valt `Definition.categorie` terug op de repositorydefault
  "proces", dan staat dát als `default`-event geregistreerd — geen
  verzonnen handmatige keuze.
* Bestaand record: een menselijke keuze loopt uitsluitend via het commando
  `save_met_categoriekeuze` → `record_category_choice`, met de versie van de
  getoonde kandidaat als optimistic lock; een gewone `update` draagt de
  geladen versie eveneens tot de uiteindelijke UPDATE (reviewbevinding 3).
* Readback (`_record_to_definition`): event, status en historie in metadata.
* Orchestrator `_create_definition_object`: bouwt de invoer uit
  `request.options["category_choice"]` (grens: `lees_keuze_invoer`).
"""

from __future__ import annotations

import pytest

from database.definitie_repository import DefinitieRepository
from services.definition_repository import DefinitionRepository
from services.exceptions import RepositoryError
from services.interfaces import Definition, GenerationRequest
from services.orchestrators.definition_orchestrator_v2 import (
    DefinitionOrchestratorV2,
)

pytestmark = [pytest.mark.unit]

ORG = ["DJI"]
JUR = ["Strafrecht"]
WET = ["Pbw"]


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "transport.db")


def _definition(**over) -> Definition:
    basis = {
        "begrip": "keurmerk",
        "definitie": "Een synthetische definitie.",
        "categorie": "type",
        "organisatorische_context": list(ORG),
        "juridische_context": list(JUR),
        "wettelijke_basis": list(WET),
        "metadata": {"status": "draft", "created_by": "legacy_ui"},
    }
    basis.update(over)
    return Definition(**basis)


def test_generatiekeuze_wordt_zonder_actor_en_generatiegebonden_opgeslagen(db_path):
    repo = DefinitionRepository(db_path)
    definition = _definition(
        metadata={
            "status": "draft",
            "created_by": "legacy_ui",
            "generation_id": "gen-42",
            "category_choice_input": {
                "origin": "manual",
                "actor": "Henk",  # aangeleverd → genegeerd
                "actor_source": "session_user",
                "recorded_at": "2000-01-01T00:00:00+00:00",
            },
        }
    )
    did = repo.save(definition)

    record = DefinitieRepository(db_path).get_definitie(did)
    keuze = record.get_category_choice()
    assert keuze["origin"] == "manual" and keuze["value"] == "type"
    assert keuze["actor"] is None and keuze["actor_source"] is None
    assert keuze["recorded_at"] != "2000-01-01T00:00:00+00:00"
    assert keuze["binding"] == "generation_candidate"
    assert keuze["generation_id"] == "gen-42"
    assert record.get_category_choice_status()["status"] == "manual_unattributed"

    # Readback in de servicelaag, via een nieuwe repository-instantie.
    opnieuw = DefinitionRepository(db_path).get(did)
    assert opnieuw.metadata["category_choice"]["origin"] == "manual"
    assert opnieuw.metadata["category_choice_status"]["status"] == "manual_unattributed"
    assert opnieuw.metadata["category_choice_status"]["text_unchanged"] is True
    assert opnieuw.metadata["category_choice_history"] == []


def test_modelvoorstel_neemt_reasoning_en_scores_mee(db_path):
    repo = DefinitionRepository(db_path)
    did = repo.save(
        _definition(
            metadata={
                "status": "draft",
                "category_choice_input": {
                    "origin": "model",
                    "reasoning": "woordpatroon",
                    "scores": {"type": 0.8},
                },
            }
        )
    )
    keuze = DefinitieRepository(db_path).get_definitie(did).get_category_choice()
    assert keuze["origin"] == "model"
    assert keuze["reasoning"] == "woordpatroon" and keuze["scores"] == {"type": 0.8}
    assert (
        DefinitionRepository(db_path)
        .get(did)
        .metadata["category_choice_status"]["status"]
        == "model_suggestion"
    )


@pytest.mark.parametrize("herkomst", ["editor", "import", "default", "bevestigd"])
def test_niet_aanleverbare_herkomst_wordt_geweigerd_en_niets_opgeslagen(
    db_path, herkomst
):
    repo = DefinitionRepository(db_path)
    with pytest.raises(Exception, match="herkomst"):
        repo.save(
            _definition(
                metadata={
                    "status": "draft",
                    "category_choice_input": {"origin": herkomst},
                }
            )
        )
    assert DefinitieRepository(db_path).search_definities(query="keurmerk") == []


def test_repositorydefault_wordt_als_bewezen_default_geregistreerd(db_path):
    repo = DefinitionRepository(db_path)
    did = repo.save(_definition(categorie=None))
    record = DefinitieRepository(db_path).get_definitie(did)
    assert record.categorie == "proces"
    keuze = record.get_category_choice()
    assert keuze["origin"] == "default" and keuze["value"] == "proces"
    assert record.get_category_choice_status()["status"] == "default"


def test_zonder_invoer_geen_event_dus_unknown_origin(db_path):
    repo = DefinitionRepository(db_path)
    did = repo.save(_definition())
    assert DefinitieRepository(db_path).get_definitie(did).get_category_choice() is None
    assert (
        DefinitionRepository(db_path)
        .get(did)
        .metadata["category_choice_status"]["status"]
        == "unknown_origin"
    )


def test_save_met_categoriekeuze_is_het_commando_voor_de_editorroute(db_path):
    repo = DefinitionRepository(db_path)
    did = repo.save(_definition())
    geladen = DefinitionRepository(db_path).get(did)
    geladen.categorie = "proces"
    geladen.toelichting = "nieuwe toelichting"
    assert (
        repo.save_met_categoriekeuze(
            geladen,
            herkomst="editor",
            actor="Reviewer Rood",
            actor_source="typed_name",
            updated_by="Reviewer Rood",
        )
        == did
    )

    opnieuw = DefinitionRepository(db_path).get(did)
    assert opnieuw.categorie == "proces" and opnieuw.toelichting == "nieuwe toelichting"
    assert opnieuw.metadata["category_choice"]["actor"] == "Reviewer Rood"
    assert opnieuw.metadata["category_choice_status"]["status"] == "manual_confirmed"
    assert opnieuw.metadata["version_number"] == 2
    # Een gewone update (geen keuze) maakt geen tweede event; een
    # tekstwijziging wordt wél blijvend zichtbaar.
    opnieuw.definitie = "Andere tekst."
    assert repo.update(did, opnieuw) is True
    laatste = DefinitionRepository(db_path).get(did)
    assert laatste.metadata["category_choice_history"] == []
    status = laatste.metadata["category_choice_status"]
    assert status["status"] == "manual_confirmed" and status["text_unchanged"] is False


def test_save_met_categoriekeuze_eist_de_versie_en_weigert_een_verouderd_object(
    db_path,
):
    repo = DefinitionRepository(db_path)
    did = repo.save(_definition())
    geladen = DefinitionRepository(db_path).get(did)
    # Tussentijdse wijziging door een ander.
    DefinitieRepository(db_path).update_definitie(did, {"begrip": "vergunning"}, "x")
    geladen.categorie = "proces"
    with pytest.raises(RepositoryError):
        repo.save_met_categoriekeuze(
            geladen, herkomst="editor", actor=None, actor_source=None, updated_by=None
        )
    na = DefinitieRepository(db_path).get_definitie(did)
    assert na.begrip == "vergunning" and na.categorie == "type"
    assert na.get_category_choice() is None

    geladen.metadata.pop("version_number")
    with pytest.raises(RepositoryError, match="version_number"):
        repo.save_met_categoriekeuze(
            geladen, herkomst="editor", actor=None, actor_source=None, updated_by=None
        )


def test_gewone_update_draagt_de_geladen_versie_als_optimistic_lock(db_path):
    repo = DefinitionRepository(db_path)
    did = repo.save(_definition())
    geladen = DefinitionRepository(db_path).get(did)
    DefinitieRepository(db_path).update_definitie(did, {"begrip": "vergunning"}, "x")
    geladen.definitie = "Nieuwe tekst."
    assert repo.update(did, geladen) is False
    assert DefinitieRepository(db_path).get_definitie(did).begrip == "vergunning"


def test_orchestrator_bouwt_generatiegebonden_keuze_invoer_uit_de_request():
    orch = DefinitionOrchestratorV2.__new__(DefinitionOrchestratorV2)
    request = GenerationRequest(
        id="r1",
        begrip="keurmerk",
        ontologische_categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        options={
            "category_choice": {
                "origin": "manual",
                "actor": "Henk",
                "status": "manual_confirmed",
            }
        },
    )
    definition = orch._create_definition_object(
        request=request,
        text="Een keurmerk is …",
        validation_result={"is_acceptable": True, "violations": []},
        generation_metadata={"generation_id": "gen-7"},
    )
    assert definition.categorie == "type"
    assert definition.metadata["category_choice_input"] == {"origin": "manual"}
    assert definition.metadata["generation_id"] == "gen-7"

    request.options = {"category_choice": {"origin": "editor"}}
    with pytest.raises(ValueError, match="herkomst"):
        orch._create_definition_object(
            request=request,
            text="x",
            validation_result={},
            generation_metadata={},
        )

    request.options = None
    definition = orch._create_definition_object(
        request=request, text="x", validation_result={}, generation_metadata={}
    )
    assert "category_choice_input" not in definition.metadata
