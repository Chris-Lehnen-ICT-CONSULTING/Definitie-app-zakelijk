import pytest

from integration.definitie_checker import DefinitieChecker, CheckAction
from database.definitie_repository import (
    DefinitieRepository,
    DefinitieRecord,
    DefinitieStatus,
)
from domain.ontological_categories import OntologischeCategorie
import uuid
from pathlib import Path


def _make_repo() -> DefinitieRepository:
    # Use file-based temporary database to keep schema across connections
    tmp_dir = Path(".tmp_test_dbs")
    tmp_dir.mkdir(exist_ok=True)
    db_path = tmp_dir / f"definities_{uuid.uuid4().hex}.sqlite"
    return DefinitieRepository(str(db_path))


def _insert_definition(
    repo: DefinitieRepository,
    *,
    begrip: str,
    definitie: str,
    categorie: str,
    org: str,
    jur: str,
    wet: list[str],
    status: DefinitieStatus = DefinitieStatus.ESTABLISHED,
) -> int:
    rec = DefinitieRecord(
        begrip=begrip,
        definitie=definitie,
        categorie=categorie,
        organisatorische_context=org,
        juridische_context=jur,
        status=status.value,
    )
    rec.set_wettelijke_basis(wet)
    return repo.create_definitie(rec)


def test_exact_match_requires_all_three_lists_equal_order_independent():
    repo = _make_repo()
    begrip = "aanhouding"
    org = "OM"
    jur = "Strafrecht"
    wet = ["Art. 27 Sv", "Art. 67 Sv"]

    _insert_definition(
        repo,
        begrip=begrip,
        definitie="Aanhouding is ...",
        categorie=OntologischeCategorie.TYPE.value,
        org=org,
        jur=jur,
        wet=wet,
        status=DefinitieStatus.ESTABLISHED,
    )

    checker = DefinitieChecker(repository=repo)

    # Provide wettelijke_basis in different order -> still exact match
    result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=org,
        juridische_context=jur,
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=list(reversed(wet)),
    )

    assert result.action == CheckAction.USE_EXISTING
    assert result.existing_definitie is not None
    assert result.existing_definitie.status == DefinitieStatus.ESTABLISHED.value


def test_mismatch_wettelijke_basis_does_not_count_as_exact_or_duplicate():
    repo = _make_repo()
    begrip = "aanhouding"
    org = "OM"
    jur = "Strafrecht"
    wet = ["Art. 27 Sv", "Art. 67 Sv"]

    _insert_definition(
        repo,
        begrip=begrip,
        definitie="Aanhouding is ...",
        categorie=OntologischeCategorie.TYPE.value,
        org=org,
        jur=jur,
        wet=wet,
        status=DefinitieStatus.ESTABLISHED,
    )

    checker = DefinitieChecker(repository=repo)

    # Different wettelijke_basis -> should proceed (no exact, no filtered duplicate)
    result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=org,
        juridische_context=jur,
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=["Art. 12 Pw"],
    )

    assert result.action == CheckAction.PROCEED
    assert result.existing_definitie is None


def test_draft_status_returns_update_existing_when_all_three_match():
    repo = _make_repo()
    begrip = "aanhouding"
    org = "OM"
    jur = "Strafrecht"
    wet = ["Art. 27 Sv"]

    _insert_definition(
        repo,
        begrip=begrip,
        definitie="Aanhouding is ...",
        categorie=OntologischeCategorie.TYPE.value,
        org=org,
        jur=jur,
        wet=wet,
        status=DefinitieStatus.DRAFT,
    )

    checker = DefinitieChecker(repository=repo)

    result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=org,
        juridische_context=jur,
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=wet,
    )

    assert result.action == CheckAction.UPDATE_EXISTING
    assert result.existing_definitie is not None
    assert result.existing_definitie.status == DefinitieStatus.DRAFT.value
