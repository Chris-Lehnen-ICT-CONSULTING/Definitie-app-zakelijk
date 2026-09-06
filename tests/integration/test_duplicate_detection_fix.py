"""DEF-54: consistente duplicate detection tussen Checker en Repository.

Het contract is ongewijzigd: de categorie is onderdeel van de unieke sleutel.
Hetzelfde begrip met dezelfde context én dezelfde categorie is een duplicaat;
met een andere categorie is het dat niet.

Onder DEF-519 hersteld — de suite toetste dat contract niet betrouwbaar:

* Beide tests draaiden op de **repository-database** (`data/definities.db`) via
  `get_definitie_repository()` en verwijderden daar vooraf en achteraf met
  directe SQL rijen die op een testbegrip leken. De offline-gate weigert die
  opening terecht. Elke test krijgt nu een verse `DefinitieRepository` op een
  eigen pad in `tmp_path`, opgebouwd door de gewone schema-init van de
  repository zelf. Die opruiming is daarmee overbodig geworden en is verwijderd:
  een verse database bevat per definitie geen oude testrecords.
* De eerste rij werd alleen aangemaakt `if not existing`. Op een gevulde
  database sloeg de test die stap over en asserteerde hij op data van iemand
  anders. Elke rij die hier wordt teruggelezen is nu door deze test zelf
  aangemaakt.
* `pytest.raises((ValueError, Exception), match="bestaat al")` accepteerde
  iedere fout met die tekst, ook een onbruikbare database. De verwachting is nu
  de concrete `ValueError` uit `DefinitieCrudRepository._weiger_duplicaat`.
* `check_result.action != CheckAction.PROCEED` liet drie verschillende
  uitkomsten door. Voor een bestaande DRAFT-rij is de actuele uitkomst
  `UPDATE_EXISTING`; dat wordt nu exact geasserteerd, inclusief het id van de
  gevonden rij.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Any

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
    SourceType,
)
from domain.ontological_categories import OntologischeCategorie
from integration.definitie_checker import CheckAction, DefinitieChecker

pytestmark = [pytest.mark.integration]

ORGANISATORISCHE_CONTEXT = '["TestOrg"]'
JURIDISCHE_CONTEXT = ""


def _maak_record(begrip: str, definitie: str, categorie: str) -> DefinitieRecord:
    """Een DRAFT-record in de vaste testcontext."""
    return DefinitieRecord(
        begrip=begrip,
        definitie=definitie,
        categorie=categorie,
        organisatorische_context=ORGANISATORISCHE_CONTEXT,
        juridische_context=JURIDISCHE_CONTEXT,
        status=DefinitieStatus.DRAFT.value,
        source_type=SourceType.MANUAL.value,
        wettelijke_basis="[]",
    )


def _lees_rijen_terug(db_path: str, begrip: str) -> list[dict[str, Any]]:
    """Lees de opgeslagen rijen via een **nieuwe** verbinding op het bestand.

    Bewust buiten de repository om: een teruggegeven id bewijst nog geen
    duurzame rij. De verbinding wordt in `finally` gesloten.
    """
    verbinding = sqlite3.connect(db_path)
    try:
        verbinding.row_factory = sqlite3.Row
        rijen = verbinding.execute(
            "SELECT id, begrip, definitie, categorie, organisatorische_context, "
            "juridische_context, status FROM definities WHERE begrip = ? "
            "ORDER BY id",
            (begrip,),
        ).fetchall()
        return [dict(rij) for rij in rijen]
    finally:
        verbinding.close()


@pytest.fixture
def repository(tmp_path) -> Iterator[DefinitieRepository]:
    """Echte `DefinitieRepository` op een eigen, verse database in `tmp_path`.

    De database wordt aangelegd door de gewone schema-init van de repository
    (`DatabaseConnection.init_database()` → `src/database/schema.sql`), dus de
    duplicaatregels die deze suite toetst zijn precies de productieregels. Er
    wordt niets gemockt: de repository is het echte object.
    """
    repo = DefinitieRepository(str(tmp_path / "definities.db"))
    try:
        yield repo
    finally:
        # De thread-lokale verbinding die deze fixture zelf liet openen sluiten;
        # anders blijft zij open tot de garbage collector toeslaat.
        toestand = getattr(repo._db._thread_local, "state", None)
        if toestand is not None:
            toestand.close()


def test_duplicate_detection_with_same_category(repository: DefinitieRepository):
    """Zelfde begrip + context + categorie → checker meldt de bestaande rij en
    de repository weigert de tweede rij."""
    checker = DefinitieChecker(repository=repository)

    begrip = "test_begrip_duplicate"
    categorie = OntologischeCategorie.TYPE

    # Stap 1: de eerste rij wordt altijd door deze test zelf aangemaakt.
    record1_id = repository.create_definitie(
        _maak_record(begrip, "Test definitie 1", categorie.value)
    )
    assert isinstance(record1_id, int), "create_definitie moet een id teruggeven"

    # Stap 2: de checker vindt de exacte match. Een DRAFT-rij levert in de
    # huidige code UPDATE_EXISTING op (ESTABLISHED zou USE_EXISTING geven).
    check_result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=ORGANISATORISCHE_CONTEXT,
        juridische_context=JURIDISCHE_CONTEXT,
        categorie=categorie,
    )

    assert check_result.action is CheckAction.UPDATE_EXISTING
    assert check_result.existing_definitie is not None
    assert check_result.existing_definitie.id == record1_id
    assert check_result.existing_definitie.definitie == "Test definitie 1"

    # Stap 3: de tweede rij wordt geweigerd met de concrete duplicaatfout van
    # de repository — geen willekeurige exception.
    record2 = _maak_record(begrip, "Test definitie 2 (duplicate)", categorie.value)
    with pytest.raises(ValueError, match="bestaat al in deze context"):
        repository.create_definitie(record2)

    # Stap 4: verse verbinding — er staat precies één rij, met de eerste tekst.
    rijen = _lees_rijen_terug(repository.db_path, begrip)
    assert [rij["id"] for rij in rijen] == [record1_id]
    assert rijen[0]["definitie"] == "Test definitie 1"
    assert rijen[0]["categorie"] == categorie.value


def test_duplicate_detection_with_different_category(repository: DefinitieRepository):
    """Zelfde begrip + context, andere categorie → toegestaan, twee eigen rijen."""
    checker = DefinitieChecker(repository=repository)

    begrip = "test_begrip_multi_category"
    categorie_type = OntologischeCategorie.TYPE
    categorie_proces = OntologischeCategorie.PROCES

    # Stap 1: de TYPE-rij wordt altijd door deze test zelf aangemaakt.
    type_id = repository.create_definitie(
        _maak_record(begrip, "Test definitie als TYPE", categorie_type.value)
    )
    assert isinstance(type_id, int), "TYPE-rij moet een id opleveren"

    # Stap 2: dezelfde context met PROCES is géén duplicaat.
    check_result = checker.check_before_generation(
        begrip=begrip,
        organisatorische_context=ORGANISATORISCHE_CONTEXT,
        juridische_context=JURIDISCHE_CONTEXT,
        categorie=categorie_proces,
    )
    assert check_result.action is CheckAction.PROCEED
    assert check_result.existing_definitie is None

    # Stap 3: de PROCES-rij wordt geaccepteerd door dezelfde repository die de
    # gelijke categorie hierboven weigert.
    proces_id = repository.create_definitie(
        _maak_record(begrip, "Test definitie als PROCES", categorie_proces.value)
    )
    assert isinstance(proces_id, int), "PROCES-rij moet een id opleveren"
    assert proces_id != type_id, "Beide categorieën moeten een eigen rij krijgen"

    # Stap 4: verse verbinding — beide rijen staan er, met eigen tekst,
    # categorie en de gedeelde context.
    rijen = _lees_rijen_terug(repository.db_path, begrip)
    assert [rij["id"] for rij in rijen] == sorted([type_id, proces_id])
    per_categorie = {rij["categorie"]: rij for rij in rijen}
    assert set(per_categorie) == {categorie_type.value, categorie_proces.value}
    assert per_categorie[categorie_type.value]["definitie"] == "Test definitie als TYPE"
    assert (
        per_categorie[categorie_proces.value]["definitie"]
        == "Test definitie als PROCES"
    )
    for rij in rijen:
        assert rij["organisatorische_context"] == ORGANISATORISCHE_CONTEXT
        assert rij["juridische_context"] == JURIDISCHE_CONTEXT
        assert rij["status"] == DefinitieStatus.DRAFT.value
