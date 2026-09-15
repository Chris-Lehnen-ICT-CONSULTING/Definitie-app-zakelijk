"""DUP_01 — een opgeslagen record is niet zijn eigen duplicaat (DEF-622 R2, DEF-677).

`ValidationOrchestratorV2` zet `definition_id` in de metadata ("het record mag
niet zijn eigen duplicaat zijn"), maar `DuplicateDetectionEvaluator._zoek_duplicaat`
leest die sleutel niet en retourneert bij hertoetsing van een opgeslagen
record het record zelf. Gevolg: elke opgeslagen definitie met context krijgt
een DUP_01-melding op zichzelf, en een écht tweede duplicaat wordt niet meer
gezien zodra het eigen record als eerste kandidaat komt.

Norm: sla uitsluitend het aantoonbaar eigen record over (zelfde canonieke
ID, strikt geheel getal) en onderzoek de volledige kandidatenset verder. Een
ongeldig ID (bool/float/None/cijfertekst) is géén eigen-record-bewijs en
slaat niets over. Zonder eigen ID (nog niet opgeslagen) blijft een bestaand
record een duplicaat. Overige DEF-677-scope (capability/severity/
runtimecontract) valt hier buiten; de algemene gate blijft DEF-630.

Bewijs op de echte keten: echte `DefinitionRepository` op een synthetische
SQLite, echte `ModularValidationService` met de echte regelset, echte
`ValidationOrchestratorV2` (recordadapter zet `definition_id`).
"""

from __future__ import annotations

from typing import Any

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieStatus
from domain.context.normalisatie import contextsleutel
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition, DuplicateCandidate
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.validation.evaluators.duplicate_detection import (
    DuplicateDetectionEvaluator,
)
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

BEGRIP = "dossiercheck"
TEKST = "Controle waarbij wordt vastgesteld of alle vereiste velden zijn ingevuld."
ORG = '["Team Koper"]'
JUR = '["bestuursrecht"]'
WET = '["Regeling K"]'


@pytest.fixture
def repo(tmp_path) -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / "eigen-duplicaat.db"))


def _record() -> DefinitieRecord:
    return DefinitieRecord(
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="proces",
        organisatorische_context=ORG,
        juridische_context=JUR,
        wettelijke_basis=WET,
        status=DefinitieStatus.DRAFT.value,
    )


def _zet(repo: DefinitionRepository, *, geforceerd: bool = False) -> int:
    """Via de productieroute; een tweede gelijk record alleen als bewust
    geforceerd duplicaat mét auditreden (geen guard-bypass)."""
    if geforceerd:
        return repo.legacy_repo.create_definitie(
            _record(),
            allow_duplicate=True,
            duplicate_reason="synthetische proef: bewust tweede concept",
        )
    return repo.legacy_repo.create_definitie(_record())


def _orchestrator(repo: DefinitionRepository) -> ValidationOrchestratorV2:
    return ValidationOrchestratorV2(
        ModularValidationService(get_toetsregel_manager(), None, None, repository=repo)
    )


def _dup01(resultaat: dict) -> list[dict]:
    return [v for v in resultaat.get("violations", []) if v.get("code") == "DUP_01"]


# ------------------------------------------------------- echte keten (V2 + SQLite)


@pytest.mark.asyncio
async def test_alleen_eigen_record_is_geen_duplicaat(repo):
    eigen = _zet(repo)

    resultaat = await _orchestrator(repo).validate_definition(repo.get(eigen))

    assert _dup01(resultaat) == [], _dup01(resultaat)
    assert resultaat["rule_statuses"]["DUP_01"] == "pass"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "eigen_eerst", [True, False], ids=["eigen-eerst", "ander-eerst"]
)
async def test_tweede_echt_duplicaat_wordt_gevonden_naast_eigen_record(
    repo, eigen_eerst
):
    """De kandidatenset wordt volledig onderzocht: het eigen record wordt
    overgeslagen, het andere record — vóór of ná het eigen record in de
    kandidatenvolgorde — is het gemelde duplicaat."""
    if eigen_eerst:
        eigen = _zet(repo)
        ander = _zet(repo, geforceerd=True)
    else:
        ander = _zet(repo)
        eigen = _zet(repo, geforceerd=True)

    resultaat = await _orchestrator(repo).validate_definition(repo.get(eigen))

    meldingen = _dup01(resultaat)
    assert len(meldingen) == 1, meldingen
    assert meldingen[0]["metadata"]["existing_definition_id"] == ander
    assert meldingen[0]["metadata"]["existing_definition_id"] != eigen
    assert resultaat["rule_statuses"]["DUP_01"] == "fail"


@pytest.mark.asyncio
async def test_zonder_eigen_id_blijft_bestaand_record_een_duplicaat(repo):
    """Een nog niet opgeslagen kandidaat (id None) heeft geen eigen record om
    over te slaan: het bestaande record is en blijft het duplicaat."""
    bestaand = _zet(repo)
    kandidaat = Definition(
        id=None,
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="proces",
        organisatorische_context=["Team Koper"],
        juridische_context=["bestuursrecht"],
        wettelijke_basis=["Regeling K"],
    )

    resultaat = await _orchestrator(repo).validate_definition(kandidaat)

    meldingen = _dup01(resultaat)
    assert len(meldingen) == 1, meldingen
    assert meldingen[0]["metadata"]["existing_definition_id"] == bestaand


# ------------------------------------------------- ID-contract op de evaluatorgrens


class _Kandidaten:
    def __init__(self, *ids: int) -> None:
        self.ids = ids

    def find_duplicate_candidates(self, begrip: str) -> list[DuplicateCandidate]:
        return [
            DuplicateCandidate(
                id=i,
                status="draft",
                categorie="proces",
                organisatorische_context=contextsleutel(["Team Koper"]),
                juridische_context=contextsleutel(["bestuursrecht"]),
                wettelijke_basis=contextsleutel(["Regeling K"]),
            )
            for i in self.ids
        ]


def _zoek(repository: Any, definition_id: Any) -> dict[str, Any] | None:
    return DuplicateDetectionEvaluator._zoek_duplicaat(
        repository,
        BEGRIP,
        [["Team Koper"], ["bestuursrecht"], ["Regeling K"]],
        {"categorie": "proces", "definition_id": definition_id},
    )


def test_eigen_id_slaat_alleen_het_eigen_record_over_en_zoekt_door():
    assert _zoek(_Kandidaten(1), 1) is None
    assert _zoek(_Kandidaten(1, 2), 1) == {"id": 2, "status": "draft"}
    assert _zoek(_Kandidaten(2, 1), 1) == {"id": 2, "status": "draft"}


@pytest.mark.parametrize(
    "ongeldig",
    [True, 1.0, "1", None],
    ids=["bool", "float", "cijfertekst", "None"],
)
def test_ongeldig_eigen_id_slaat_niets_over(ongeldig):
    """`True == 1` en `1.0 == 1` zijn geen bewijs van hetzelfde record: alleen
    een strikt geheel getal is een canonieke record-ID."""
    assert _zoek(_Kandidaten(1), ongeldig) == {"id": 1, "status": "draft"}
