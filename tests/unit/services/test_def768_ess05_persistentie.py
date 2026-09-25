"""DEF-768 WP5: opslag, herstel en burenlookup van ESS-05 op een echte tijdelijke SQLite.

Bewezen, zonder schemawijziging (alles in `generation_prompt_data`):

* een nieuw record bewaart `ess05_assessment` (historie start leeg), de
  burenlijst met expertbesluiten en een lege-ruimtebevestiging; bij laden
  staan ze weer in `Definition.metadata`;
* een update met een nieuwe beoordeling of burenlijst bewaart het vorige
  document/de vorige lijst in een append-only historie; gelijk = geen
  wijziging; `{}` wist de lege-ruimtebevestiging;
* ongeldige invoer laat de opslag falen, niets geschreven;
* een ruwe `generation_prompt_data`-schrijfactie overschrijft de beheerde
  ESS-05-sleutels niet;
* `zoek_ess05_buren` levert actieve records met exact dezelfde drie
  (genormaliseerde) contextlijsten, ander begrip, niet het record zelf;
* de echte keten opslaan → laden → wrapper → replay geeft een actuele pass.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from domain.ess05.contract import CONTRACTVERSIE
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.evaluators.base import EvaluationDeps
from services.validation.evaluators.distinction_assessment import (
    DistinctionAssessmentEvaluator,
)
from services.validation.types_internal import EvaluationContext
from tests.fixtures.def768_fakes import (
    BINDING,
    FakeEss05Assessor,
    bouw_ess05_beoordeling,
)
from tests.unit.validation.test_def768_ess05_evaluator import ESS05, _StubSupport
from toetsregels.runtime_contract import RequiredInput, ResultStatus

pytestmark = [pytest.mark.unit]

BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
WERKNEMER = "Persoon met een arbeidsovereenkomst met de instelling."
ORG = ["Synthetische Uitleendienst"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": [],
    "wettelijke_basis": [],
}
BUREN = [
    {
        "id": "gebruiker:werknemer",
        "term": "werknemer",
        "definitie": WERKNEMER,
        "herkomst": "gebruiker",
        "bevestigd": True,
    },
    {
        "id": "model:borg",
        "term": "borg",
        "definitie": None,
        "herkomst": "model",
        "bevestigd": False,
        "afgewezen": True,
        "actor": "deskundige",
        "at": "2026-09-23T10:00:00+00:00",
        "grond": "Synthetisch: geen verwant begrip.",
    },
]


def _repo(tmp_path, naam="ess05.db") -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / naam))


def _beoordeling(scenario="pass", *, buren=None, tekst=TEKST) -> dict[str, Any]:
    return bouw_ess05_beoordeling(
        BEGRIP,
        tekst,
        CONTEXT,
        [],
        buren=buren if buren is not None else BUREN,
        scenario=scenario,
    )


def _definition(**overrides: Any) -> Definition:
    metadata: dict[str, Any] = {
        "status": "draft",
        "created_by": "generator",
        "ess05_assessment": _beoordeling(),
        "ess05_buren": deepcopy(BUREN),
    }
    metadata.update(overrides.pop("metadata", {}))
    velden: dict[str, Any] = {
        "begrip": BEGRIP,
        "definitie": TEKST,
        "categorie": "type",
        "organisatorische_context": list(ORG),
        "juridische_context": [],
        "wettelijke_basis": [],
        "metadata": metadata,
    }
    velden.update(overrides)
    return Definition(**velden)


def _registratie(repo: DefinitionRepository, definitie_id: int) -> dict[str, Any]:
    return repo.get_generation_prompt_data(definitie_id) or {}


class TestOpslagEnHerstel:
    def test_nieuw_record_bewaart_en_herstelt_alles(self, tmp_path):
        repo = _repo(tmp_path)
        lege = {
            "fingerprint": "f" * 64,
            "contract_version": CONTRACTVERSIE,
            "grond": "g",
            "actor": "a",
            "at": "2026-09-23T10:00:00+00:00",
        }
        definitie_id = repo.save(_definition(metadata={"ess05_lege_ruimte": lege}))
        registratie = _registratie(repo, definitie_id)
        assert registratie["ess05_assessment"] == _beoordeling()
        assert registratie["ess05_assessment_history"] == []
        assert registratie["ess05_buren"] == BUREN
        assert registratie["ess05_lege_ruimte"] == lege

        geladen = repo.get(definitie_id)
        assert geladen.metadata["ess05_assessment"] == _beoordeling()
        assert geladen.metadata["ess05_assessment_history"] == []
        assert geladen.metadata["ess05_buren"] == BUREN
        assert geladen.metadata["ess05_lege_ruimte"] == lege

    def test_record_zonder_ess05_verzint_niets(self, tmp_path):
        repo = _repo(tmp_path)
        definitie_id = repo.save(
            _definition(metadata={"ess05_assessment": None, "ess05_buren": None})
        )
        geladen = repo.get(definitie_id)
        for sleutel in ("ess05_assessment", "ess05_buren", "ess05_lege_ruimte"):
            assert sleutel not in geladen.metadata
            assert sleutel not in _registratie(repo, definitie_id)

    def test_nieuwe_beoordeling_gaat_met_historie_mee_gelijk_niet(self, tmp_path):
        repo = _repo(tmp_path)
        definitie_id = repo.save(_definition())
        geladen = repo.get(definitie_id)
        assert repo.save(geladen) == definitie_id  # gelijk: geen historie
        assert _registratie(repo, definitie_id)["ess05_assessment_history"] == []

        geladen = repo.get(definitie_id)
        geladen.metadata["ess05_assessment"] = _beoordeling("fail")
        repo.save(geladen)
        registratie = _registratie(repo, definitie_id)
        assert registratie["ess05_assessment"] == _beoordeling("fail")
        (vorige,) = registratie["ess05_assessment_history"]
        assert vorige["assessment"] == _beoordeling()
        assert "superseded_at" in vorige

    def test_gewijzigde_burenlijst_gaat_met_historie_mee(self, tmp_path):
        repo = _repo(tmp_path)
        definitie_id = repo.save(_definition())
        geladen = repo.get(definitie_id)
        nieuw = deepcopy(BUREN)
        nieuw[1]["afgewezen"] = False
        nieuw[1]["bevestigd"] = True
        geladen.metadata["ess05_buren"] = nieuw
        repo.save(geladen)
        registratie = _registratie(repo, definitie_id)
        assert registratie["ess05_buren"] == nieuw
        (vorige,) = registratie["ess05_buren_history"]
        assert vorige["neighbours"] == BUREN

    def test_lege_dict_wist_de_lege_ruimtebevestiging(self, tmp_path):
        repo = _repo(tmp_path)
        lege = {
            "fingerprint": "f" * 64,
            "contract_version": CONTRACTVERSIE,
            "grond": "g",
            "actor": "a",
            "at": "t",
        }
        definitie_id = repo.save(_definition(metadata={"ess05_lege_ruimte": lege}))
        geladen = repo.get(definitie_id)
        geladen.metadata["ess05_lege_ruimte"] = {}
        repo.save(geladen)
        assert "ess05_lege_ruimte" not in _registratie(repo, definitie_id)
        assert "ess05_lege_ruimte" not in repo.get(definitie_id).metadata

    @pytest.mark.parametrize(
        ("sleutel", "waarde"),
        [
            ("ess05_buren", [{"term": "x", "herkomst": "onbekend", "bevestigd": True}]),
            ("ess05_buren", "geen lijst"),
            ("ess05_assessment", {"status": "assessed"}),
            ("ess05_lege_ruimte", {"fingerprint": "f", "grond": "g"}),
        ],
        ids=[
            "herkomst",
            "buren-geen-lijst",
            "zonder-vingerafdruk",
            "lege-ruimte-onvolledig",
        ],
    )
    def test_ongeldige_invoer_schrijft_niets(self, tmp_path, sleutel, waarde):
        from services.exceptions import RepositoryError

        repo = _repo(tmp_path)
        definitie_id = repo.save(_definition())
        voor = _registratie(repo, definitie_id)
        geladen = repo.get(definitie_id)
        geladen.metadata[sleutel] = waarde
        with pytest.raises((RepositoryError, ValueError)):
            repo.save(geladen)
        assert _registratie(repo, definitie_id) == voor

    def test_ruwe_registratie_overschrijft_de_beheerde_sleutels_niet(self, tmp_path):
        repo = _repo(tmp_path)
        definitie_id = repo.save(_definition())
        voor = _registratie(repo, definitie_id)
        ruw = {**voor, "ess05_buren": [], "ess05_assessment": {"fingerprint": "x"}}
        repo.legacy_repo.update_definitie(
            definitie_id, {"generation_prompt_data": json.dumps(ruw)}, "tester"
        )
        na = _registratie(repo, definitie_id)
        assert na["ess05_buren"] == voor["ess05_buren"]
        assert na["ess05_assessment"] == voor["ess05_assessment"]


class TestBurenlookup:
    def _record(self, repo, begrip, org, *, status="draft", jur=(), wb=()):
        return repo.save(
            Definition(
                begrip=begrip,
                definitie=f"Synthetische definitie van {begrip}.",
                categorie="type",
                organisatorische_context=list(org),
                juridische_context=list(jur),
                wettelijke_basis=list(wb),
                metadata={"status": status, "created_by": "tester"},
            )
        )

    def test_zelfde_context_ander_begrip_niet_zichzelf(self, tmp_path):
        repo = _repo(tmp_path)
        eigen = self._record(repo, BEGRIP, ORG)
        klant = self._record(repo, "klant", [" synthetische uitleendienst "])
        self._record(repo, "werknemer", ["Andere Dienst"])
        self._record(repo, "borg", ORG, jur=["Synthetisch recht"])
        self._record(repo, "gearchiveerd", ORG, status="archived")

        rijen = repo.zoek_ess05_buren(BEGRIP, CONTEXT, eigen)
        assert [(r["id"], r["begrip"]) for r in rijen] == [(klant, "klant")]
        assert rijen[0]["definitie"] == "Synthetische definitie van klant."

    def test_zonder_context_geen_buren(self, tmp_path):
        repo = _repo(tmp_path)
        self._record(repo, "klant", ORG)
        leeg = {
            "organisatorische_context": [],
            "juridische_context": [],
            "wettelijke_basis": [],
        }
        assert repo.zoek_ess05_buren(BEGRIP, leeg, None) == []


class TestKeten:
    async def test_opslaan_laden_wrapper_replay_geeft_actuele_pass(self, tmp_path):
        from unittest.mock import AsyncMock

        repo = _repo(tmp_path)
        definitie_id = repo.save(_definition(metadata={"ess05_assessment": None}))
        geladen = repo.get(definitie_id)

        service = AsyncMock()
        ontvangen: dict[str, Any] = {}

        async def _bewaar(*_a, **kwargs):
            ontvangen.update(deepcopy(kwargs.get("context") or {}))
            return {"version": "2.1.0", "system": {}}

        service.validate_definition.side_effect = _bewaar
        orch = ValidationOrchestratorV2(
            service,
            ess05_assessment_service=FakeEss05Assessor(scenario="pass"),
            ess05_burenbron=repo,
        )
        result = await orch.validate_definition(geladen)
        doc = result["ess05_assessment"]
        assert doc["status"] == "assessed"
        assert [b["term"] for b in ontvangen["ess05_actieve_buren"]] == ["werknemer"]
        assert ontvangen["ess05_uitgesloten_termen"] == ["borg"]

        assert ontvangen["ess05_binding"] == BINDING.als_dict()

        # Opslaan en herladen; de echte evaluator speelt de beoordeling af op
        # exact de context die de wrapper samenstelde.
        geladen.metadata["ess05_assessment"] = doc
        repo.save(geladen)
        herladen = repo.get(definitie_id)
        assert herladen.metadata["ess05_assessment"] == doc
        uitkomst = DistinctionAssessmentEvaluator().evaluate(
            ESS05,
            EvaluationContext(
                raw_text=TEKST,
                cleaned_text=TEKST,
                begrip=BEGRIP,
                metadata={
                    **ontvangen,
                    "ess05_assessment": herladen.metadata["ess05_assessment"],
                },
            ),
            EvaluationDeps(
                support=_StubSupport(),
                available_inputs=frozenset(RequiredInput),
                pattern_cache={},
            ),
        )
        assert uitkomst.status is ResultStatus.PASS, uitkomst.reason
        assert uitkomst.score is None
