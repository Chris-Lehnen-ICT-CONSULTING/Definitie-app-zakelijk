import uuid
from pathlib import Path

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker


def _make_repo() -> DefinitieRepository:
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


def test_exact_synonym_match_counts_as_duplicate():
    repo = _make_repo()
    begrip = "Identiteitsmiddel"
    synoniem = "ID-kaart"
    org = "OM"
    jur = "Strafrecht"
    wet = ["Art. 27 Sv", "Art. 67 Sv"]

    definitie_id = _insert_definition(
        repo,
        begrip=begrip,
        definitie="Identiteitsmiddel is ...",
        categorie=OntologischeCategorie.TYPE.value,
        org=org,
        jur=jur,
        wet=wet,
        status=DefinitieStatus.ESTABLISHED,
    )

    # Sla synoniemen op (actief)
    repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": [synoniem, "Identiteitsbewijs"]},
        gegenereerd_door="test",
        generation_model="manual",
        generation_params=None,
        voorkeursterm=None,
    )

    checker = DefinitieChecker(repository=repo)

    # Zoek via synoniem met identieke context → moet als bestaande gezien worden
    result = checker.check_before_generation(
        begrip=synoniem,
        organisatorische_context=org,
        juridische_context=jur,
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=list(reversed(wet)),  # orde-onafhankelijk
    )

    assert result.action in (CheckAction.USE_EXISTING, CheckAction.UPDATE_EXISTING)
    assert result.existing_definitie is not None
    assert result.existing_definitie.begrip == begrip


def test_synonym_match_with_different_context_is_not_duplicate():
    repo = _make_repo()
    begrip = "Identiteitsmiddel"
    synoniem = "ID-kaart"
    org = "OM"
    jur = "Strafrecht"
    wet = ["Art. 27 Sv"]

    definitie_id = _insert_definition(
        repo,
        begrip=begrip,
        definitie="Identiteitsmiddel is ...",
        categorie=OntologischeCategorie.TYPE.value,
        org=org,
        jur=jur,
        wet=wet,
        status=DefinitieStatus.ESTABLISHED,
    )

    repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": [synoniem]},
        gegenereerd_door="test",
        generation_model="manual",
        generation_params=None,
        voorkeursterm=None,
    )

    checker = DefinitieChecker(repository=repo)

    # Zelfde synoniem maar andere context (juridisch) → geen duplicate gate
    result = checker.check_before_generation(
        begrip=synoniem,
        organisatorische_context=org,
        juridische_context="Civiel recht",  # anders
        categorie=OntologischeCategorie.TYPE,
        wettelijke_basis=wet,
    )

    assert result.action == CheckAction.PROCEED
    assert result.existing_definitie is None
