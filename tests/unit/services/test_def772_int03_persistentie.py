"""DEF-772 WP4: de INT-03-beoordeling duurzaam opslaan, heropenen en herbinden.

Alles via de publieke servicelaag op een tijdelijke, echte SQLite-database,
telkens herladen met een vérse repository-instantie (ESS-03-patroon, DEF-766).
Bewezen (en niet meer):

* een aan de kandidaat gebonden INT-03-beoordeling overleeft opslaan →
  ID-only herladen exact (`metadata["int03_assessment"]`); de replay op het
  herladen record geeft dezelfde uitkomst — ook de K7-uitkomst 'voldoet: niet
  van toepassing (geen verwijzend voornaamwoord)';
* een nieuwe beoordeling vervangt de vorige mét append-only historie; een
  gelijke beoordeling is geen wijziging; een wijziging van tekst, term,
  context, toelichting, prompt, norm, provider of model laat de opgeslagen
  beoordeling staan maar de replay past haar niet meer toe (historisch,
  benoemd);
* de editor-opslaan legt alleen een beoordeling vast die exact aan de op te
  slaan kandidaat en de actuele binding bindt en `assessed` is, en benoemt
  anders waarom niet;
* de generatieroute (echte validatiewrapper, tijdelijke SQLite) slaat de
  beoordeling van exact de opgeslagen kandidaat op;
* een ruwe registratie-aanlevering kan de beoordeling niet wissen of
  vervalsen; een misvormd document wordt geweigerd zonder schrijfactie.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from database.definitie_repository import DefinitieStatus
from domain.int03.contract import (
    BEVINDING_GEEN_VERWIJZEND_WOORD,
    MOTIVERING_GEEN_VERWIJZEND_WOORD,
    Beoordelingsbinding,
)
from domain.int03.opslag import INT03_ASSESSMENT_HISTORY_KEY, INT03_ASSESSMENT_KEY
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    bindingsafwijzing_int03,
    int03_uitkomst_van_definition,
)
from services.definition_repository import DefinitionRepository
from services.exceptions import RepositoryError
from services.interfaces import (
    AIGenerationResult,
    CleaningResult,
    Definition,
    GenerationRequest,
    OrchestratorConfig,
    PromptResult,
)
from services.null_repository import NullDefinitionRepository
from services.orchestrators.definition_orchestrator_v2 import DefinitionOrchestratorV2
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.modular_validation_service import ModularValidationService
from tests.fixtures.def772_fakes import (
    BINDING,
    FakeInt03Assessor,
    bouw_int03_beoordeling,
)
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
TEKST = "Beschrijving van een verzameling documenten die bij een zaak horen."
TEKST_ZONDER = "Beschrijving van een verzameling documenten van een archiefvormer."
TOELICHTING = "Synthetische toelichting bij de archiefkaart."
ORG = ["Stichting Zilver"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}


def _repo(tmp_path, naam: str = "int03.db") -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / naam))


def _beoordeling(
    scenario: str = "pass",
    *,
    begrip: str = BEGRIP,
    tekst: str = TEKST,
    contexten: dict[str, Any] | None = None,
    toelichting: str | None = TOELICHTING,
    model: str | None = None,
) -> dict[str, Any]:
    extra = {"model": model} if model is not None else {}
    return bouw_int03_beoordeling(
        begrip,
        tekst,
        contexten if contexten is not None else CONTEXT,
        toelichting,
        scenario=scenario,
        **extra,
    )


def _definition(**overrides: Any) -> Definition:
    metadata: dict[str, Any] = {
        "status": DefinitieStatus.DRAFT.value,
        "created_by": "generator",
        "int03_assessment": _beoordeling(),
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


def _registratie(repo: DefinitionRepository, did: int) -> dict[str, Any]:
    rec = repo.get_definitie(did)
    assert rec is not None
    return rec.get_generatieregistratie() or {}


def _samenvatting(uitkomst: dict[str, Any]) -> dict[str, Any]:
    return uitkomst["review"]["assessment"]


class TestOpslaanEnHerladen:
    def test_beoordeling_overleeft_opslaan_en_id_only_herladen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        vers = _repo(tmp_path).get(did)
        assert vers is not None
        opgeslagen = vers.metadata["int03_assessment"]
        assert opgeslagen == _beoordeling()
        assert vers.metadata["int03_assessment_history"] == []
        # Het record draagt het document onder de beheerde sleutel.
        assert _registratie(repo, did)[INT03_ASSESSMENT_KEY] == _beoordeling()
        assert repo.get_definitie(did).get_int03_assessment() == _beoordeling()
        # De replay op het herladen record: dezelfde uitkomst, gebonden.
        uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "pass"
        assert _samenvatting(uitkomst)["applied"] is True
        assert _samenvatting(uitkomst)["historical"] is False
        assert uitkomst["fingerprint"] == opgeslagen["fingerprint"]
        assert uitkomst["assessment"] == opgeslagen
        # Het volledige oordeel (woord, passage, kandidaten) is exact terug.
        [verwijzing] = opgeslagen["judgment"]["references"]
        assert verwijzing["word"] == "die"
        assert verwijzing["passage"] in TEKST

    def test_k7_uitkomst_wordt_exact_teruggelezen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(
            _definition(
                definitie=TEKST_ZONDER,
                metadata={
                    "int03_assessment": _beoordeling("no_word", tekst=TEKST_ZONDER)
                },
            )
        )
        uitkomst = int03_uitkomst_van_definition(
            _repo(tmp_path).get(did), binding=BINDING
        )
        assert uitkomst["status"] == "pass"
        assert _samenvatting(uitkomst)["applied"] is True
        assert _samenvatting(uitkomst)["finding"] == BEVINDING_GEEN_VERWIJZEND_WOORD
        assert uitkomst["parts"][0]["reason"] == MOTIVERING_GEEN_VERWIJZEND_WOORD

    def test_zonder_beoordeling_wordt_niets_verzonnen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition(metadata={"int03_assessment": None}))
        vers = _repo(tmp_path).get(did)
        assert vers.metadata.get("int03_assessment") is None
        assert "int03_assessment_history" not in vers.metadata
        assert INT03_ASSESSMENT_KEY not in _registratie(repo, did)
        assert repo.get_definitie(did).get_int03_assessment() is None
        uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "review_required"
        assert _samenvatting(uitkomst)["applied"] is False
        assert "niet uitgevoerd" in _samenvatting(uitkomst)["reason"]

    def test_nieuwe_beoordeling_vervangt_met_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        versie1 = repo.get_definitie(did).version_number
        geladen = repo.get(did)
        geladen.metadata["int03_assessment"] = _beoordeling("fail")
        repo.save(geladen)
        registratie = _registratie(repo, did)
        assert registratie[INT03_ASSESSMENT_KEY] == _beoordeling("fail")
        [vorige] = registratie[INT03_ASSESSMENT_HISTORY_KEY]
        assert vorige["assessment"] == _beoordeling()
        assert vorige["superseded_on_version"] == versie1
        assert vorige["superseded_at"]
        assert repo.get_definitie(did).version_number == versie1 + 1
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["int03_assessment_history"] == [vorige]
        assert int03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "fail"

    def test_gelijke_beoordeling_maakt_geen_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        geladen = repo.get(did)
        geladen.metadata["status"] = DefinitieStatus.REVIEW.value
        repo.save(geladen)
        registratie = _registratie(repo, did)
        assert registratie[INT03_ASSESSMENT_KEY] == _beoordeling()
        assert registratie[INT03_ASSESSMENT_HISTORY_KEY] == []

    @pytest.mark.parametrize(
        "wijziging",
        [
            {"definitie": TEKST + " Aangepast."},
            {"toelichting": "Andere toelichting."},
            {"begrip": "archiefstuk"},
            {"organisatorische_context": ["Stichting Goud"]},
        ],
        ids=["tekst", "toelichting", "term", "context"],
    )
    def test_relevante_wijziging_maakt_de_opgeslagen_beoordeling_historisch(
        self, tmp_path, wijziging
    ):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        geladen = repo.get(did)
        for veld, waarde in wijziging.items():
            setattr(geladen, veld, waarde)
        repo.save(geladen)
        vers = _repo(tmp_path).get(did)
        # Historie behouden: het document staat er nog, maar telt niet.
        assert vers.metadata["int03_assessment"] == _beoordeling()
        uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "review_required"
        samenvatting = _samenvatting(uitkomst)
        assert samenvatting["applied"] is False
        assert samenvatting["historical"] is True
        assert "gewijzigd" in samenvatting["reason"]
        assert samenvatting["verdict"] == "pass"  # zichtbaar als historie
        assert "historisch" in uitkomst["parts"][0]["reason"]

    @pytest.mark.parametrize(
        ("binding", "fragment"),
        [
            (
                Beoordelingsbinding(**{**BINDING.als_dict(), "model": "ander-model"}),
                "model",
            ),
            (
                Beoordelingsbinding(
                    **{**BINDING.als_dict(), "prompt_version": "int03-assess/9"}
                ),
                "promptversie",
            ),
            (
                Beoordelingsbinding(**{**BINDING.als_dict(), "norm_sha256": "x" * 64}),
                "norm",
            ),
            (None, "onbekend"),
        ],
        ids=["ander-model", "andere-prompt", "andere-norm", "geen-binding"],
    )
    def test_prompt_norm_of_modelwijziging_maakt_de_beoordeling_niet_actueel(
        self, tmp_path, binding, fragment
    ):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        uitkomst = int03_uitkomst_van_definition(
            _repo(tmp_path).get(did), binding=binding
        )
        assert uitkomst["status"] == "review_required"
        samenvatting = _samenvatting(uitkomst)
        assert samenvatting["applied"] is False
        assert samenvatting["historical"] is (binding is not None)
        assert fragment in samenvatting["reason"]
        assert samenvatting["expected_binding"] == (
            binding.als_dict() if binding else None
        )

    def test_technische_fout_en_niet_beschikbaar_worden_bewaard_maar_tellen_niet(
        self, tmp_path
    ):
        repo = _repo(tmp_path, "fout.db")
        did = repo.save(
            _definition(metadata={"int03_assessment": _beoordeling("error")})
        )
        vers = _repo(tmp_path, "fout.db").get(did)
        assert vers.metadata["int03_assessment"]["status"] == "error"
        uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "error"
        assert "geen inhoudelijk oordeel" in uitkomst["parts"][0]["reason"]

        repo2 = _repo(tmp_path, "dienst.db")
        did2 = repo2.save(
            _definition(metadata={"int03_assessment": _beoordeling("unavailable")})
        )
        uitkomst2 = int03_uitkomst_van_definition(
            _repo(tmp_path, "dienst.db").get(did2), binding=BINDING
        )
        assert uitkomst2["status"] == "review_required"
        assert "geen dienst" in _samenvatting(uitkomst2)["reason"]

    @pytest.mark.parametrize(
        "misvormd",
        [{"status": "assessed"}, {"fingerprint": "f" * 64, "status": "onbekend"}],
        ids=["zonder-vingerafdruk", "onbekende-status"],
    )
    def test_misvormde_beoordeling_wordt_geweigerd_niets_geschreven(
        self, tmp_path, misvormd
    ):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        versie = repo.get_definitie(did).version_number
        geladen = repo.get(did)
        geladen.metadata["int03_assessment"] = misvormd
        with pytest.raises(RepositoryError):
            repo.save(geladen)
        assert _registratie(repo, did)[INT03_ASSESSMENT_KEY] == _beoordeling()
        assert repo.get_definitie(did).version_number == versie

    def test_misvormde_beoordeling_bij_aanmaak_wordt_geweigerd(self, tmp_path):
        repo = _repo(tmp_path)
        with pytest.raises(RepositoryError):
            repo.save(
                _definition(metadata={"int03_assessment": {"status": "assessed"}})
            )

    def test_ruwe_niet_json_registratie_kan_de_beoordeling_niet_wissen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        with pytest.raises(ValueError, match="generation_prompt_data"):
            repo.legacy_repo.update_definitie(
                did, {"generation_prompt_data": "geen json"}, "tester"
            )
        assert _registratie(repo, did)[INT03_ASSESSMENT_KEY] == _beoordeling()

    def test_ruwe_json_registratie_kan_de_beoordeling_niet_vervalsen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(
            _definition(metadata={"int03_assessment": _beoordeling("fail")})
        )
        vervalst = {
            INT03_ASSESSMENT_KEY: _beoordeling("pass"),
            INT03_ASSESSMENT_HISTORY_KEY: [],
            "x": 1,
        }
        assert repo.legacy_repo.update_definitie(
            did, {"generation_prompt_data": json.dumps(vervalst)}, "tester"
        )
        registratie = _registratie(repo, did)
        assert registratie[INT03_ASSESSMENT_KEY] == _beoordeling("fail")
        assert registratie["x"] == 1
        with pytest.raises(ValueError, match="beheerde"):
            repo.legacy_repo.update_definitie(
                did, {"generation_prompt_data": None}, "tester"
            )


class TestEditorOpslaan:
    def _service(self, tmp_path) -> tuple[DefinitionEditService, int]:
        repo = DefinitionEditRepository(str(tmp_path / "editor.db"))
        did = repo.save(_definition(metadata={"int03_assessment": None}))
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
            int03_assessment=_beoordeling(),
            int03_binding=BINDING,
        )
        assert result["success"] is True
        assert result["int03_assessment_persisted"] is True
        assert result["int03_assessment_reason"] is None
        vers = service.repository.get(did)
        assert vers.metadata["int03_assessment"] == _beoordeling()
        assert int03_uitkomst_van_definition(vers, binding=BINDING)["status"] == "pass"

    def test_stale_sessiebeoordeling_wordt_niet_vastgelegd_en_benoemd(self, tmp_path):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did, definitie=TEKST + " Aangepast."),
            user="tester",
            validate=False,
            int03_assessment=_beoordeling(),
            int03_binding=BINDING,
        )
        assert result["success"] is True
        assert result["int03_assessment_persisted"] is False
        assert "gewijzigd" in result["int03_assessment_reason"]
        assert service.repository.get(did).metadata.get("int03_assessment") is None

    def test_technische_fout_is_geen_actueel_bewijs(self, tmp_path):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did),
            user="tester",
            validate=False,
            int03_assessment=_beoordeling("error"),
            int03_binding=BINDING,
        )
        assert result["int03_assessment_persisted"] is False
        assert "niet uitgevoerd" in result["int03_assessment_reason"]
        assert service.repository.get(did).metadata.get("int03_assessment") is None

    @pytest.mark.parametrize(
        ("binding", "fragment"),
        [
            (
                Beoordelingsbinding(**{**BINDING.als_dict(), "model": "ander-model"}),
                "model",
            ),
            (
                Beoordelingsbinding(
                    **{**BINDING.als_dict(), "prompt_version": "int03-assess/9"}
                ),
                "promptversie",
            ),
            (
                Beoordelingsbinding(**{**BINDING.als_dict(), "norm_sha256": "x" * 64}),
                "norm",
            ),
        ],
        ids=["ander-model", "andere-prompt", "andere-norm"],
    )
    def test_beoordeling_van_een_andere_binding_wordt_niet_vastgelegd(
        self, tmp_path, binding, fragment
    ):
        service, did = self._service(tmp_path)
        result = service.save_definition(
            did,
            self._updates(service, did),
            user="tester",
            validate=False,
            int03_assessment=_beoordeling(),
            int03_binding=binding,
        )
        assert result["int03_assessment_persisted"] is False
        assert fragment in result["int03_assessment_reason"]
        assert service.repository.get(did).metadata.get("int03_assessment") is None

    def test_bindingsafwijzing_volgt_tekst_toelichting_context_en_binding(self):
        assert (
            bindingsafwijzing_int03(_beoordeling(), _definition(), binding=BINDING)
            is None
        )
        # Zonder bekende binding wordt alleen de kandidaatbinding getoetst
        # (ESS-03-patroon); de replay benoemt de onbekende binding zelf.
        assert bindingsafwijzing_int03(_beoordeling(), _definition()) is None
        anders = _definition(toelichting="Anders.")
        assert "gewijzigd" in bindingsafwijzing_int03(_beoordeling(), anders)
        context = _definition(organisatorische_context=["Stichting Goud"])
        assert "gewijzigd" in bindingsafwijzing_int03(_beoordeling(), context)
        assert "geen object" in bindingsafwijzing_int03([], _definition())
        assert "niet uitgevoerd" in bindingsafwijzing_int03(
            _beoordeling("unavailable"), _definition()
        )


class TestGeneratieroute:
    """De echte validatiewrapper met een fake INT-03-dienst en een echte
    tijdelijke SQLite-repository: de beoordeling van de opgeslagen kandidaat
    komt op het record terecht en is na herladen actueel."""

    @pytest.fixture
    def generate(self, monkeypatch, tmp_path):
        from voorbeelden import unified_voorbeelden

        monkeypatch.setattr(
            unified_voorbeelden,
            "genereer_alle_voorbeelden_async",
            AsyncMock(return_value={}),
        )

        async def run(*, scenario="pass", definitie=TEKST):
            assessor = FakeInt03Assessor(scenario=scenario)
            prompt = AsyncMock()
            prompt.build_generation_prompt.return_value = PromptResult(
                text="Offline",
                token_count=1,
                components_used=(),
                feedback_integrated=False,
                optimization_applied=False,
                metadata={},
            )
            ai = AsyncMock()
            ai.generate_definition.return_value = AIGenerationResult(
                text=definitie, model="offline", tokens_used=1, generation_time=0.0
            )
            cleaning = AsyncMock()
            cleaning.clean_text.return_value = CleaningResult(
                original_text=definitie, cleaned_text=definitie, was_cleaned=False
            )
            validation = ValidationOrchestratorV2(
                ModularValidationService(
                    get_toetsregel_manager(), repository=NullDefinitionRepository()
                ),
                int03_assessment_service=assessor,
            )
            db = str(tmp_path / f"generatie-{scenario}.db")
            orch = DefinitionOrchestratorV2(
                prompt_service=prompt,
                ai_service=ai,
                validation_service=validation,
                cleaning_service=cleaning,
                repository=DefinitionRepository(db),
                config=OrchestratorConfig(
                    enable_feedback_loop=False, enable_enhancement=False
                ),
            )
            response = await orch.create_definition(
                GenerationRequest(
                    id="int03-wp4",
                    begrip=BEGRIP,
                    ontologische_categorie="type",
                    organisatorische_context=list(ORG),
                ),
                context={},
            )
            assert response.success, response.error
            return SimpleNamespace(
                response=response, assessor=assessor, repo=DefinitionRepository(db)
            )

        return run

    async def test_beoordeling_van_de_generatie_staat_op_het_record(self, generate):
        uit = await generate()
        raw = uit.response.validation_result
        document = raw["rule_results"]["INT-03"]["assessment"]
        vers = uit.repo.get(uit.response.definition.id)
        assert vers.metadata["int03_assessment"] == document
        assert vers.metadata["int03_assessment_history"] == []
        uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "pass"
        assert _samenvatting(uitkomst)["applied"] is True

    async def test_negatieve_generatiebeoordeling_wordt_als_fail_bewaard(
        self, generate
    ):
        uit = await generate(scenario="fail")
        vers = uit.repo.get(uit.response.definition.id)
        assert vers.metadata["int03_assessment"]["judgment"]["verdict"] == "fail"
        uitkomst = int03_uitkomst_van_definition(vers, binding=BINDING)
        assert uitkomst["status"] == "fail"
        # De tekst is door beoordelen/opslaan niet gewijzigd.
        assert vers.definitie == TEKST
