"""DEF-766 correctieronde 1 — R1 (binding in keten en replay), R4, R5 en de readbackmatrix.

Echte tijdelijke SQLite-repository, echte evaluator/wrapper met een fake
ESS-03-dienst. Bewezen:

* R1: de wrapper geeft de actuele beoordelingsbinding aan de evaluator; de
  replay op een herladen record past een beoordeling alleen toe bij die
  binding en toont haar anders als historisch;
* R4: `betekenisverduidelijking` bereikt ESS-03 in generatievalidatie,
  recordvalidatie en editor-toetsing, en de replay gebruikt dezelfde waarde;
* R5: de actuele ESS-03-verduidelijking wordt expliciet bij opslaan
  vervoerd (ook bewust leeg), zonder eerst een geslaagde beoordeling; zij
  wordt heropend en getoetst; een oud oordeel blijft historisch;
* readbackmatrix: elke relevante wijziging (term, tekst, drie contextlijsten,
  broninhoud, toelichting, betekenisverduidelijking, verduidelijking, norm,
  prompt, provider, model) maakt de opgeslagen beoordeling zichtbaar
  niet-actueel, met behoud van het document.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from database import models as db_models
from domain.ess03.contract import Beoordelingsbinding, Intentie
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    bindingsafwijzing_ess03,
    bouw_validatiecontext,
    ess03_intentie_van_definition,
    ess03_uitkomst_van_definition,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.interfaces import ValidationContext
from tests.fixtures.def766_fakes import (
    NORM_SHA256,
    PROMPT_VERSION,
    FakeEss03Assessor,
    bouw_ess03_beoordeling,
)

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = (
    "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken peilmoment "
    "volledig door water is omgeven."
)
TOELICHTING = "Synthetische conventie: elk gescheiden aaneengesloten vlak telt als één."
ORG = ["Synthetisch Waterschap"]
BRON = {
    "provider": "documents",
    "doc_id": "conv-1",
    "snippet": "Elk gescheiden aaneengesloten vlak telt op peil P als één.",
}
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}
BINDING = Beoordelingsbinding(
    prompt_version=PROMPT_VERSION,
    norm_sha256=NORM_SHA256,
    provider="fake",
    model="fake-ess03-model",
)


def _repo(tmp_path, naam="ess03-correcties.db") -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / naam))


def _intentie(**over) -> Intentie:
    velden: dict[str, Any] = {"toelichting": TOELICHTING, "categorie": "type"}
    velden.update(over)
    return Intentie(**velden)


def _beoordeling(scenario="pass", *, intentie=None, tekst=TEKST, bronnen=None, **over):
    doc = bouw_ess03_beoordeling(
        BEGRIP,
        tekst,
        CONTEXT,
        bronnen if bronnen is not None else [BRON],
        intentie=intentie or _intentie(),
        scenario=scenario,
    )
    doc.update(over)
    return doc


def _definition(**overrides: Any) -> Definition:
    metadata = {
        "status": "draft",
        "created_by": "generator",
        "provenance_sources": [deepcopy(BRON)],
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


# --- R1: binding in keten en replay ------------------------------------------------


class TestBindingInKeten:
    async def test_wrapper_geeft_de_actuele_binding_aan_de_evaluator(self):
        from unittest.mock import AsyncMock

        service = AsyncMock()
        ontvangen: dict[str, Any] = {}

        async def _bewaar(*_a, **kwargs):
            ontvangen.update(kwargs.get("context") or {})
            return {"version": "2.1.0", "system": {}}

        service.validate_definition.side_effect = _bewaar
        assessor = FakeEss03Assessor()
        orch = ValidationOrchestratorV2(service, ess03_assessment_service=assessor)
        await orch.validate_text(BEGRIP, TEKST, context=ValidationContext(metadata={}))
        assert ontvangen["ess03_binding"] == BINDING.als_dict()

    def test_evaluator_past_alleen_toe_bij_actuele_binding(self):
        from services.validation.evaluators.base import EvaluationDeps
        from services.validation.evaluators.countability_assessment import (
            CountabilityAssessmentEvaluator,
        )
        from services.validation.types_internal import EvaluationContext
        from tests.unit.validation.test_def766_ess03_evaluator import (
            ESS03,
            _StubSupport,
        )
        from toetsregels.runtime_contract import RequiredInput, ResultStatus

        deps = EvaluationDeps(
            support=_StubSupport(),
            available_inputs=frozenset(RequiredInput),
            pattern_cache={},
        )
        doc = _beoordeling("pass", bronnen=[])
        basis = {
            **CONTEXT,
            "record_text": TEKST,
            "definition": {"toelichting": TOELICHTING},
            "ontologische_categorie": "type",
            "ess03_assessment": doc,
        }
        met = CountabilityAssessmentEvaluator().evaluate(
            ESS03,
            EvaluationContext(
                raw_text=TEKST,
                cleaned_text=TEKST,
                begrip=BEGRIP,
                metadata={**basis, "ess03_binding": BINDING.als_dict()},
            ),
            deps,
        )
        assert met.status is ResultStatus.PASS
        zonder = CountabilityAssessmentEvaluator().evaluate(
            ESS03,
            EvaluationContext(
                raw_text=TEKST, cleaned_text=TEKST, begrip=BEGRIP, metadata=basis
            ),
            deps,
        )
        assert zonder.status is ResultStatus.REVIEW_REQUIRED
        assert "actuele beoordelingsbinding" in (zonder.reason or "")
        ander_model = CountabilityAssessmentEvaluator().evaluate(
            ESS03,
            EvaluationContext(
                raw_text=TEKST,
                cleaned_text=TEKST,
                begrip=BEGRIP,
                metadata={
                    **basis,
                    "ess03_binding": {**BINDING.als_dict(), "model": "nieuw-model"},
                },
            ),
            deps,
        )
        assert ander_model.status is ResultStatus.REVIEW_REQUIRED
        assert "historisch" in (ander_model.reason or "")

    def test_replay_op_record_vereist_binding(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        vers = _repo(tmp_path).get(did)
        assert ess03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "pass"
        zonder = ess03_uitkomst_van_definition(vers)
        assert zonder["status"] == "review_required"
        assert zonder["review"]["assessment"]["applied"] is False


# --- R4: betekenisverduidelijking in alle paden ---------------------------------


class TestBetekenisverduidelijking:
    def test_editorcontext_neemt_de_betekenisverduidelijking_van_het_record_over(self):
        geladen = {
            "version_number": 2,
            "generation_prompt_data": {
                "betekenisverduidelijking": "Bedoeld als handeling."
            },
        }
        ctx = bouw_validatiecontext(_definition(metadata={}), geladen)
        assert ctx["betekenisverduidelijking"] == "Bedoeld als handeling."

    async def test_recordvalidatie_geeft_de_betekenisverduidelijking_door(self):
        from unittest.mock import AsyncMock

        service = AsyncMock()
        service.validate_definition.return_value = {"version": "2.1.0", "system": {}}
        assessor = FakeEss03Assessor()
        orch = ValidationOrchestratorV2(service, ess03_assessment_service=assessor)
        definitie = _definition(
            metadata={
                "generation_prompt_data": {
                    "betekenisverduidelijking": "Bedoeld als handeling."
                }
            }
        )
        await orch.validate_definition(definitie)
        (call,) = assessor.calls
        assert call["intentie"].betekenisverduidelijking == "Bedoeld als handeling."

    def test_replay_gebruikt_dezelfde_betekenisverduidelijking(self, tmp_path):
        intentie = _intentie(betekenisverduidelijking="Bedoeld als handeling.")
        repo = _repo(tmp_path)
        did = repo.save(
            _definition(
                metadata={
                    "prompt_text": "p",
                    "betekenisverduidelijking": "Bedoeld als handeling.",
                    "ess03_assessment": _beoordeling(intentie=intentie),
                }
            )
        )
        vers = _repo(tmp_path).get(did)
        assert ess03_intentie_van_definition(vers).betekenisverduidelijking == (
            "Bedoeld als handeling."
        )
        assert ess03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "pass"


# --- R5: de actuele ESS-03-verduidelijking -----------------------------------------


class TestVerduidelijking:
    def _service(self, tmp_path):
        repo = DefinitionEditRepository(str(tmp_path / "verduidelijking.db"))
        did = repo.save(_definition(metadata={"ess03_assessment": None}))
        return DefinitionEditService(repository=repo, validation_service=None), did

    def _updates(self, service, did, **over):
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

    def test_verduidelijking_wordt_zonder_beoordeling_bewaard_en_heropend(
        self, tmp_path
    ):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(
                service, did, ess03_verduidelijking="Peil P is het zomerpeil."
            ),
            user="tester",
            validate=False,
        )
        assert result["success"] is True
        vers = service.repository.get(did)
        assert vers.metadata["ess03_verduidelijking"] == "Peil P is het zomerpeil."
        record = vers.metadata["generation_prompt_data"]
        assert (
            record[db_models.ESS03_VERDUIDELIJKING_VELD] == "Peil P is het zomerpeil."
        )
        assert db_models.ESS03_ASSESSMENT_KEY not in record
        # De toetsingscontext van een volgende sessie draagt haar mee.
        ctx = bouw_validatiecontext(_definition(metadata={}), vers.metadata)
        assert ctx["ess03_verduidelijking"] == "Peil P is het zomerpeil."

    def test_verduidelijking_en_categoriekeuze_landen_samen_in_een_update(
        self, tmp_path
    ):
        """Regressie (make test correctieronde 1): een editor-opslaan met een
        gewijzigde categorie (expliciet commando `record_category_choice`)
        vervoert nu óók de ESS-03-verduidelijking (R5). De ESS-03-stap mag de
        zojuist in dezelfde UPDATE gezette keuze niet als 'ruwe invoer' uit de
        registratie filteren: keuze, keuzestaat én verduidelijking staan na
        readback alle drie op het record."""
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(
                service, did, categorie="proces", ess03_verduidelijking="Peil P."
            ),
            user="Reviewer Rood",
            validate=False,
            categoriekeuze={
                "herkomst": "editor",
                "actor": "Reviewer Rood",
                "actor_source": "typed_name",
            },
        )
        assert result["success"] is True, result
        record = DefinitionRepository(service.repository.db_path).get_definitie(did)
        assert record.categorie == "proces"
        keuze = record.get_category_choice()
        assert keuze is not None and keuze["origin"] == "editor"
        assert keuze["actor"] == "Reviewer Rood"
        assert record.get_ess03_verduidelijking() == "Peil P."
        registratie = record.get_generatieregistratie()
        assert registratie[db_models.ESS03_VERDUIDELIJKING_VELD] == "Peil P."
        # Omgekeerd: een beoordeling in dezelfde UPDATE als een keuze.
        result2 = service.save_definition(
            did,
            self._updates(service, did, categorie="type"),
            user="Reviewer Rood",
            validate=False,
            ess03_assessment=_beoordeling(
                intentie=_intentie(categorie="type", verduidelijking="Peil P.")
            ),
            ess03_binding=BINDING,
            categoriekeuze={
                "herkomst": "editor",
                "actor": "Reviewer Rood",
                "actor_source": "typed_name",
            },
        )
        assert result2["success"] is True, result2
        assert result2["ess03_assessment_persisted"] is True, result2
        record2 = DefinitionRepository(service.repository.db_path).get_definitie(did)
        assert record2.get_category_choice()["value"] == "type"
        assert len(record2.get_category_choice_history()) == 1
        assert record2.get_ess03_assessment()["status"] == "assessed"
        assert record2.get_ess03_verduidelijking() == "Peil P."

    def test_bewust_gewiste_verduidelijking_valt_niet_terug_op_de_oude(self, tmp_path):
        service, did = self._service(tmp_path)
        oud = _intentie(verduidelijking="Peil P.")
        service.save_definition(
            did,
            self._updates(service, did, ess03_verduidelijking="Peil P."),
            user="tester",
            validate=False,
            ess03_assessment=_beoordeling(intentie=oud),
        )
        vers = service.repository.get(did)
        assert ess03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "pass"
        # Wissen: expliciet lege waarde, geen terugval op de oude tekst.
        service.save_definition(
            did,
            self._updates(service, did, ess03_verduidelijking=""),
            user="tester",
            validate=False,
        )
        vers2 = service.repository.get(did)
        assert vers2.metadata["ess03_verduidelijking"] == ""
        assert ess03_intentie_van_definition(vers2).verduidelijking is None
        uitkomst = ess03_uitkomst_van_definition(vers2, binding=BINDING)
        assert uitkomst["status"] == "review_required"
        assert uitkomst["review"]["assessment"]["historical"] is True
        # Het oude document blijft als historie beschikbaar.
        assert vers2.metadata["ess03_assessment"]["input"]["intentie"][
            "verduidelijking"
        ] == ("Peil P.")

    def test_nieuwe_verduidelijking_met_verse_beoordeling_wordt_opgeslagen(
        self, tmp_path
    ):
        service, did = self._service(tmp_path)
        service.save_definition(
            did,
            self._updates(service, did, ess03_verduidelijking="Oud."),
            user="tester",
            validate=False,
            ess03_assessment=_beoordeling(intentie=_intentie(verduidelijking="Oud.")),
        )
        nieuw = _beoordeling(
            scenario="fail", intentie=_intentie(verduidelijking="Nieuw.")
        )
        result = service.save_definition(
            did,
            self._updates(service, did, ess03_verduidelijking="Nieuw."),
            user="tester",
            validate=False,
            ess03_assessment=nieuw,
        )
        assert result["ess03_assessment_persisted"] is True, result
        vers = service.repository.get(did)
        assert vers.metadata["ess03_verduidelijking"] == "Nieuw."
        assert ess03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "fail"
        assert len(vers.metadata["ess03_assessment_history"]) == 1

    def test_verduidelijking_gewijzigd_na_de_toetsing_maakt_de_beoordeling_stale(
        self, tmp_path
    ):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did, ess03_verduidelijking="Anders dan getoetst."),
            user="tester",
            validate=False,
            ess03_assessment=_beoordeling(
                intentie=_intentie(verduidelijking="Getoetst.")
            ),
        )
        assert result["ess03_assessment_persisted"] is False
        assert "gewijzigd" in result["ess03_assessment_reason"]
        vers = service.repository.get(did)
        assert vers.metadata["ess03_verduidelijking"] == "Anders dan getoetst."
        assert vers.metadata.get("ess03_assessment") is None

    def test_bindingsafwijzing_gebruikt_de_actuele_verduidelijking_en_binding(self):
        definition = _definition(metadata={"ess03_verduidelijking": "Peil P."})
        goed = _beoordeling(intentie=_intentie(verduidelijking="Peil P."))
        assert bindingsafwijzing_ess03(goed, definition, binding=BINDING) is None
        # Oude prompt: geen actueel bewijs.
        assert "promptversie" in bindingsafwijzing_ess03(
            {**goed, "prompt_version": "ess03-assess/0"}, definition, binding=BINDING
        )
        # De opgeslagen verduidelijking van de beoordeling telt niet als de
        # actuele: zonder metadata-sleutel is er geen verduidelijking.
        assert "gewijzigd" in bindingsafwijzing_ess03(
            goed, _definition(metadata={}), binding=BINDING
        )


# --- readbackmatrix ------------------------------------------------------------------


def _wijzig(definition: Definition, veld: str) -> None:
    if veld == "term":
        definition.begrip = "eilandje"
    elif veld == "tekst":
        definition.definitie = TEKST + " Aanvulling."
    elif veld == "organisatorische_context":
        definition.organisatorische_context = ["Ander Waterschap"]
    elif veld == "juridische_context":
        definition.juridische_context = ["waterrecht"]
    elif veld == "wettelijke_basis":
        definition.wettelijke_basis = ["Synthetische Waterwet"]
    elif veld == "broninhoud":
        bronnen = [{**BRON, "snippet": BRON["snippet"] + " Aangepast."}]
        definition.metadata["provenance_sources"] = bronnen
        definition.metadata["sources"] = deepcopy(bronnen)
    elif veld == "toelichting":
        definition.toelichting = "Andere bedoeling."
    elif veld == "categorie":
        definition.categorie = "proces"
    elif veld == "verduidelijking":
        definition.metadata["ess03_verduidelijking"] = "Nieuwe verduidelijking."
    else:  # pragma: no cover - programmeerfout in de test
        raise AssertionError(veld)


@pytest.mark.parametrize(
    "veld",
    [
        "term",
        "tekst",
        "organisatorische_context",
        "juridische_context",
        "wettelijke_basis",
        "broninhoud",
        "toelichting",
        "categorie",
        "verduidelijking",
    ],
)
def test_readbackmatrix_invoerwijziging_maakt_de_beoordeling_niet_actueel(
    tmp_path, veld
):
    repo = _repo(tmp_path)
    did = repo.save(_definition())
    geladen = repo.get(did)
    _wijzig(geladen, veld)
    repo.save(geladen)
    vers = _repo(tmp_path).get(did)
    # Het document blijft bewaard (historie), maar telt niet als actueel.
    assert vers.metadata["ess03_assessment"] == _beoordeling()
    uitkomst = ess03_uitkomst_van_definition(vers, binding=BINDING)
    assert uitkomst["status"] == "review_required", veld
    samenvatting = uitkomst["review"]["assessment"]
    assert samenvatting["applied"] is False
    assert "gewijzigd" in samenvatting["reason"]


@pytest.mark.parametrize(
    ("binding", "fragment"),
    [
        (
            Beoordelingsbinding(
                "ess03-assess/9", NORM_SHA256, "fake", "fake-ess03-model"
            ),
            "promptversie",
        ),
        (
            Beoordelingsbinding(PROMPT_VERSION, "m" * 64, "fake", "fake-ess03-model"),
            "norm",
        ),
        (
            Beoordelingsbinding(
                PROMPT_VERSION, NORM_SHA256, "ander", "fake-ess03-model"
            ),
            "provider",
        ),
        (
            Beoordelingsbinding(PROMPT_VERSION, NORM_SHA256, "fake", "nieuw-model"),
            "model",
        ),
    ],
)
def test_readbackmatrix_configuratiewijziging_maakt_de_beoordeling_historisch(
    tmp_path, binding, fragment
):
    repo = _repo(tmp_path)
    did = repo.save(_definition())
    vers = _repo(tmp_path).get(did)
    uitkomst = ess03_uitkomst_van_definition(vers, binding=binding)
    assert uitkomst["status"] == "review_required"
    samenvatting = uitkomst["review"]["assessment"]
    assert samenvatting["applied"] is False
    assert samenvatting["historical"] is True
    assert fragment in samenvatting["reason"].lower()
    assert samenvatting["verdict"] == "pass"  # het oude oordeel blijft benoemd
    assert "historisch" in uitkomst["parts"][0]["reason"]
