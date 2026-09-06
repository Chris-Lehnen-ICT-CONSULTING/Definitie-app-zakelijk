"""JSON-export van échte opgeslagen datumwaarden (DEF-519).

`DataAggregationService.aggregate_definitie_for_export` zet
`metadata["datum_voorstel"]` op het `created_at` van het record. Bij een echte
repositorylezing is dat een `datetime` (`AuditHelpers.row_to_record` roept
`datetime.fromisoformat` aan), en `ExportService._export_to_json` gaf dat object
ongewijzigd door aan `json.dump`. Elke export van een opgeslagen definitie brak
daardoor af met ``TypeError: Object of type datetime is not JSON serializable``,
met een half geschreven `.json` als enige spoor.

Deze tests draaien op de échte `DefinitieRepository`, `DataAggregationService`
en `ExportService`. Het record wordt door de productiecode weggeschreven en
teruggelezen; er wordt geen exportdubbel gebruikt en geen datum gemockt. De
laatste test bewaakt de andere kant van de grens: een objecttype dat de export
niet kent blijft een zichtbare `TypeError` en mag niet stil als tekst worden
geaccepteerd.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from services.data_aggregation_service import DataAggregationService
from services.export_service import ExportFormat, ExportService

pytestmark = [pytest.mark.unit]

#: Bewust géén UTC: een afwijkende offset laat zien of de zone behouden blijft
#: in plaats van stilzwijgend te worden genormaliseerd. De microseconden staan
#: er om precisieverlies zichtbaar te maken. Deze waarde gaat via
#: `additional_data` de export in; `created_at` van het record is niet stuurbaar
#: (zie `_record`).
ZONE = timezone(timedelta(hours=2))
MOMENT = datetime(2026, 9, 6, 14, 58, 57, 30475, tzinfo=ZONE)
MOMENT_ISO = "2026-09-06T14:58:57.030475+02:00"
BESLUITDATUM = date(2026, 9, 6)

BEGRIP = "vervoersverbod"
DEFINITIE = (
    "Handeling waarbij een bevoegde instantie een persoon verbiedt zich met een "
    "vervoermiddel te verplaatsen."
)
ORGANISATORISCH = "Openbaar Ministerie"
JURIDISCH = "strafprocesrecht"
WETTELIJK = "Wetboek van Strafvordering artikel 509"
STATUS = "review"
VERSIE = 3
VOORSTELLER = "synthetische-indiener"


def _record() -> DefinitieRecord:
    """Synthetisch record voor de echte opslagweg.

    `created_at`/`updated_at` staan hier bewust niet: `create_definitie`
    overschrijft ze onvoorwaardelijk met `datetime.now(UTC)` (gemeten). De
    datum die de export moet verwerken komt dus van de productiecode zelf, niet
    uit deze test.
    """
    return DefinitieRecord(
        begrip=BEGRIP,
        definitie=DEFINITIE,
        categorie="ACT",
        organisatorische_context=json.dumps([ORGANISATORISCH]),
        juridische_context=json.dumps([JURIDISCH]),
        wettelijke_basis=json.dumps([WETTELIJK]),
        status=STATUS,
        version_number=VERSIE,
        created_by=VOORSTELLER,
    )


@contextmanager
def _repository(db_pad: Path) -> Iterator[DefinitieRepository]:
    """Echte repository op een eigen tijdelijk databasebestand.

    `DefinitieRepository.__init__` roept `init_database()` aan en houdt daarna
    één thread-local verbinding vast. Die verbinding is van deze test zodra de
    repository is aangemaakt, dus de `finally` sluit haar — ook wanneer de body
    op een rode assertie afbreekt.
    """
    repository = DefinitieRepository(str(db_pad))
    try:
        yield repository
    finally:
        toestand = getattr(repository._db._thread_local, "state", None)
        if toestand is not None:
            toestand.close()


def _export_service(repository: DefinitieRepository, map_pad: Path) -> ExportService:
    """Echte exportservice met de echte aggregatieservice erachter."""
    return ExportService(
        repository=repository,
        data_aggregation_service=DataAggregationService(repository),
        export_dir=str(map_pad),
    )


class _OnbekendVeld:
    """Objecttype dat de export niet kent — mag nooit stil geserialiseerd worden."""


def test_json_export_bewaart_opgeslagen_datetime_verliesvrij(tmp_path: Path) -> None:
    """De geparseerde JSON bevat de opgeslagen datum als exacte ISO 8601-tekst."""
    with _repository(tmp_path / "definities.db") as repository:
        definitie_id = repository.create_definitie(_record())
        opgeslagen = repository.get_definitie(definitie_id)

        # Voorwaarde: de bron levert werkelijk een datetime-object. Zonder deze
        # controle zou de rest ook slagen op een database die al tekst teruggeeft
        # en toetst de test de serialisatiegrens niet.
        assert opgeslagen is not None, "opslag: record niet teruggelezen"
        assert isinstance(
            opgeslagen.created_at, datetime
        ), f"opslag: created_at is {type(opgeslagen.created_at).__name__}, geen datetime"
        assert (
            opgeslagen.created_at.tzinfo is not None
        ), "opslag: created_at is tijdzoneloos, dan toetst de export geen zonebehoud"
        verwachte_datum = opgeslagen.created_at
        verwachte_bijwerking = opgeslagen.updated_at

        service = _export_service(repository, tmp_path / "exports")
        pad = Path(
            service.export_definitie(
                definitie_id=definitie_id, format=ExportFormat.JSON
            )
        )

    inhoud = json.loads(pad.read_text(encoding="utf-8"))
    metadata = inhoud["metadata"]

    assert (
        metadata["datum_voorstel"] == verwachte_datum.isoformat()
    ), f"export: datum wijkt af: {metadata['datum_voorstel']!r}"
    assert (
        datetime.fromisoformat(metadata["datum_voorstel"]) == verwachte_datum
    ), "export: datum is niet verliesvrij terug te lezen"
    assert (
        datetime.fromisoformat(metadata["datum_voorstel"]).utcoffset()
        == verwachte_datum.utcoffset()
    ), f"export: tijdzone verdwenen uit {metadata['datum_voorstel']!r}"

    assert metadata["id"] == definitie_id, f"export: id wijkt af: {metadata['id']!r}"
    assert (
        metadata["status"] == STATUS
    ), f"export: status wijkt af: {metadata['status']!r}"
    assert (
        metadata["versie"] == VERSIE
    ), f"export: versie wijkt af: {metadata['versie']!r}"
    assert (
        metadata["voorsteller"] == VOORSTELLER
    ), f"export: voorsteller wijkt af: {metadata['voorsteller']!r}"

    definitieblok = inhoud["definitie"]
    assert (
        definitieblok["begrip"] == BEGRIP
    ), f"export: begrip wijkt af: {definitieblok['begrip']!r}"
    assert (
        definitieblok["definitie_origineel"] == DEFINITIE
    ), f"export: tekst wijkt af: {definitieblok['definitie_origineel']!r}"

    technisch = inhoud["technisch"]
    assert (
        technisch["created_at"] == verwachte_datum.isoformat()
    ), f"export: created_at wijkt af: {technisch['created_at']!r}"
    assert verwachte_bijwerking is not None, "opslag: updated_at niet gezet"
    assert (
        technisch["updated_at"] == verwachte_bijwerking.isoformat()
    ), f"export: updated_at wijkt af: {technisch['updated_at']!r}"


def test_json_export_bewaart_offset_en_microseconden(tmp_path: Path) -> None:
    """Een afwijkende offset en microseconden overleven de serialisatie exact.

    `created_at` staat altijd in UTC, dus zonebehoud is daar niet te toetsen.
    Deze datums gaan via de aggregatiegrens (`additional_data["metadata"]`) de
    export in — hetzelfde `metadata`-blok waar `datum_voorstel` in landt.
    """
    with _repository(tmp_path / "definities.db") as repository:
        definitie_id = repository.create_definitie(_record())
        service = _export_service(repository, tmp_path / "exports")
        pad = Path(
            service.export_definitie(
                definitie_id=definitie_id,
                additional_data={
                    "metadata": {
                        "vastgesteld_op": MOMENT,
                        "besluitdatum": BESLUITDATUM,
                    }
                },
                format=ExportFormat.JSON,
            )
        )

    metadata = json.loads(pad.read_text(encoding="utf-8"))["metadata"]
    assert (
        metadata["vastgesteld_op"] == MOMENT_ISO
    ), f"export: offset of precisie verloren: {metadata['vastgesteld_op']!r}"
    assert (
        datetime.fromisoformat(metadata["vastgesteld_op"]) == MOMENT
    ), "export: datum is niet verliesvrij terug te lezen"
    assert (
        metadata["besluitdatum"] == BESLUITDATUM.isoformat()
    ), f"export: kale datum wijkt af: {metadata['besluitdatum']!r}"


def test_json_export_weigert_onbekend_objecttype(tmp_path: Path) -> None:
    """Een objecttype dat de export niet kent blijft een zichtbare fout.

    De reparatie mag geen algemene `default=str` zijn: dan zou hier stilzwijgend
    een betekenisloze `<... object at 0x...>` in de export belanden.
    """
    with _repository(tmp_path / "definities.db") as repository:
        definitie_id = repository.create_definitie(_record())
        service = _export_service(repository, tmp_path / "exports")

        with pytest.raises(TypeError) as fout:
            service.export_definitie(
                definitie_id=definitie_id,
                additional_data={"metadata": {"vreemd": _OnbekendVeld()}},
                format=ExportFormat.JSON,
            )

    melding = str(fout.value)
    assert (
        "_OnbekendVeld" in melding
    ), f"export: fout benoemt het objecttype niet: {melding}"
