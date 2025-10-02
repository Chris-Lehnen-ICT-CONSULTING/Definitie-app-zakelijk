import uuid
from pathlib import Path

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from domain.ontological_categories import OntologischeCategorie


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
) -> int:
    rec = DefinitieRecord(
        begrip=begrip,
        definitie=definitie,
        categorie=categorie,
        organisatorische_context=org,
        juridische_context=jur,
    )
    return repo.create_definitie(rec)


def test_voorkeursterm_single_source_repo_roundtrip():
    repo = _make_repo()
    begrip = "Identiteitsmiddel"
    org = "OM"
    jur = "Strafrecht"

    definitie_id = _insert_definition(
        repo,
        begrip=begrip,
        definitie="Identiteitsmiddel is ...",
        categorie=OntologischeCategorie.TYPE.value,
        org=org,
        jur=jur,
    )

    # Sla synoniemen op met voorkeur = begrip
    repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": ["ID-kaart", "Identiteitsbewijs"]},
        gegenereerd_door="test",
        generation_model="manual",
        generation_params=None,
        voorkeursterm=begrip,  # basisterm als voorkeur
    )

    # Check single source via get_voorkeursterm
    assert repo.get_voorkeursterm(definitie_id) == begrip

    # Zet voorkeur op een synoniem en check
    repo.save_voorbeelden(
        definitie_id=definitie_id,
        voorbeelden_dict={"synoniemen": ["ID-kaart", "Identiteitsbewijs"]},
        gegenereerd_door="test",
        generation_model="manual",
        generation_params=None,
        voorkeursterm="ID-kaart",
    )
    assert repo.get_voorkeursterm(definitie_id) == "ID-kaart"
