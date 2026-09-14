"""DEF-622 (B-03): gelijke context herkennen bij de lookup vóór generatie.

`find_definitie` en `find_duplicates` vergeleken de opgeslagen JSON-strings
letterlijk met de invoer. Daardoor was `["stichting zilver"]` een andere
context dan `["Stichting Zilver"]`, en `["B", "A"]` een andere dan
`["A", "B"]` — terwijl DUP_01 en de opslag al op `contextsleutel`
normaliseren. Deze tests binden de lookup aan dezelfde normalisatie:
volledige gelijkheid van de drie lijsten, hoofdletter-, volgorde-,
whitespace- en duplicaatonafhankelijk. Overlap is géén gelijke context.
"""

from __future__ import annotations

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)

pytestmark = [pytest.mark.unit]

ORG = '["Stichting Zilver", "Gemeente X"]'
JUR = '["privaatrecht"]'
WET = '["Regeling Z"]'


def _record(
    begrip: str = "keurmerk",
    *,
    org: str = ORG,
    jur: str | None = JUR,
    wet: str | None = WET,
    categorie: str = "type",
    status: str = DefinitieStatus.DRAFT.value,
    definitie: str = "kwaliteitsmerk voor gecontroleerde producten",
) -> DefinitieRecord:
    return DefinitieRecord(
        begrip=begrip,
        definitie=definitie,
        categorie=categorie,
        organisatorische_context=org,
        juridische_context=jur,
        wettelijke_basis=wet,
        status=status,
    )


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "lookup.db"))


def test_find_definitie_herkent_case_volgorde_en_dubbele_waarden(repo):
    bewaard = repo.create_definitie(_record())
    gevonden = repo.find_definitie(
        "Keurmerk",
        '["gemeente x", " STICHTING ZILVER ", "stichting zilver"]',
        '["Privaatrecht"]',
        wettelijke_basis=["regeling z"],
    )
    assert gevonden is not None
    assert gevonden.id == bewaard


def test_overlap_is_geen_gelijke_context(repo):
    repo.create_definitie(_record())
    # Eén gedeelde waarde is niet dezelfde contextverzameling (B-03).
    assert (
        repo.find_definitie(
            "keurmerk", '["Stichting Zilver"]', JUR, wettelijke_basis=["Regeling Z"]
        )
        is None
    )
    # Een extra waarde evenmin.
    assert (
        repo.find_definitie(
            "keurmerk",
            '["Stichting Zilver", "Gemeente X", "Provincie Y"]',
            JUR,
            wettelijke_basis=["Regeling Z"],
        )
        is None
    )
    # En een lege lijst is niet gelijk aan een gevulde.
    assert (
        repo.find_definitie("keurmerk", ORG, "", wettelijke_basis=["Regeling Z"])
        is None
    )
    assert repo.find_definitie("keurmerk", ORG, JUR, wettelijke_basis=[]) is None


def test_categorieverschil_telt_bij_de_lookup_wanneer_opgegeven(repo):
    """Bestaand onderscheid behouden: categorie is onderdeel van de lookup."""
    bewaard = repo.create_definitie(_record(categorie="type"))
    assert (
        repo.find_definitie(
            "keurmerk", ORG, JUR, categorie="proces", wettelijke_basis=["Regeling Z"]
        )
        is None
    )
    zonder = repo.find_definitie("keurmerk", ORG, JUR, wettelijke_basis=["Regeling Z"])
    assert zonder is not None and zonder.id == bewaard


def test_vastgesteld_record_gaat_voor_concept_en_historie(repo):
    concept = repo.create_definitie(_record(status=DefinitieStatus.DRAFT.value))
    vastgesteld = repo.create_definitie(
        _record(status=DefinitieStatus.ESTABLISHED.value, definitie="andere tekst"),
        allow_duplicate=True,
        duplicate_reason="synthetische testopstelling",
    )
    # Het concept krijgt een hogere versie dan het vastgestelde record.
    repo.update_definitie(concept, {"definitie": "nieuwere concepttekst"})
    repo.update_definitie(concept, {"definitie": "nog nieuwere concepttekst"})

    gevonden = repo.find_definitie(
        "keurmerk", ORG, JUR, wettelijke_basis=["Regeling Z"]
    )
    assert gevonden is not None
    assert gevonden.id == vastgesteld
    assert gevonden.status == DefinitieStatus.ESTABLISHED.value


def test_gearchiveerd_record_is_geen_leidende_definitie(repo):
    gearchiveerd = repo.create_definitie(_record(status=DefinitieStatus.ARCHIVED.value))
    assert (
        repo.find_definitie("keurmerk", ORG, JUR, wettelijke_basis=["Regeling Z"])
        is None
    )
    expliciet = repo.find_definitie(
        "keurmerk",
        ORG,
        JUR,
        status=DefinitieStatus.ARCHIVED,
        wettelijke_basis=["Regeling Z"],
    )
    assert expliciet is not None and expliciet.id == gearchiveerd


def test_lookup_blijft_begrensd_op_begrip(repo):
    repo.create_definitie(_record(begrip="waarmerk"))
    assert (
        repo.find_definitie("keurmerk", ORG, JUR, wettelijke_basis=["Regeling Z"])
        is None
    )


def test_find_duplicates_gebruikt_genormaliseerde_context(repo):
    bewaard = repo.create_definitie(_record())
    matches = repo.find_duplicates(
        "keurmerk",
        '["gemeente x", "stichting zilver"]',
        '["PRIVAATRECHT"]',
        wettelijke_basis=["regeling z"],
    )
    assert [m.definitie_record.id for m in matches] == [bewaard]
    assert not repo.find_duplicates(
        "keurmerk", '["stichting zilver"]', JUR, wettelijke_basis=["Regeling Z"]
    )


def test_create_weigert_duplicaat_op_genormaliseerde_context(repo):
    repo.create_definitie(_record())
    with pytest.raises(ValueError, match="bestaat al"):
        repo.create_definitie(
            _record(
                org='["gemeente x", "STICHTING ZILVER"]',
                jur='["Privaatrecht"]',
                wet='["regeling z"]',
            )
        )


def test_bewust_nieuw_concept_vereist_reden_en_laat_bestaand_record_ongemoeid(repo):
    """B-09/besluit 5: Genereer Nieuw levert een concept ernaast, met auditreden.

    Het bestaande (vastgestelde) record verandert niet van status, versie of
    tekst; het nieuwe record draagt de reden in zijn geschiedenis.
    """
    eerste = repo.create_definitie(
        _record(status=DefinitieStatus.ESTABLISHED.value, definitie="oorspronkelijk")
    )
    with pytest.raises(ValueError, match="reden"):
        repo.create_definitie(_record(definitie="nieuw concept"), allow_duplicate=True)

    tweede = repo.create_definitie(
        _record(definitie="nieuw concept"),
        allow_duplicate=True,
        duplicate_reason="Bestaande definitie dekt de nieuwe regeling niet.",
    )
    assert tweede != eerste

    bestaand = repo.get_definitie(eerste)
    assert bestaand is not None
    assert bestaand.status == DefinitieStatus.ESTABLISHED.value
    assert bestaand.definitie == "oorspronkelijk"
    assert bestaand.version_number == 1

    nieuw = repo.get_definitie(tweede)
    assert nieuw is not None and nieuw.status == DefinitieStatus.DRAFT.value

    rijen = (
        repo._db.get_connection()
        .execute(
            "SELECT wijziging_type, wijziging_reden FROM definitie_geschiedenis "
            "WHERE definitie_id = ? ORDER BY id",
            (tweede,),
        )
        .fetchall()
    )
    assert [r[0] for r in rijen] == ["created"]
    assert "Bestaande definitie dekt de nieuwe regeling niet." in rijen[0][1]
    assert f"bestaande definitie {eerste}" in rijen[0][1]

    # Zonder duplicaat is een reden niet nodig: er valt niets te verantwoorden.
    assert repo.create_definitie(_record(begrip="waarmerk"), allow_duplicate=True)
