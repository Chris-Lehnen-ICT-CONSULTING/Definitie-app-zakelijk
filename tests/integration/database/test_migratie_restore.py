"""Restorebewijs per actieve migratieroute (DEF-664).

Iedere route die een bestaande database kan wijzigen maakt vóór de eerste
schrijfactie een geverifieerde WAL-veilige backup via het DEF-663-contract.
Deze suite bewijst per route dat:

1. de migratie slaagt en de doelversie bereikt;
2. alle sentinelrijen (JSON-lijsten, NULL-velden, geschiedenis, voorbeelden,
   tags, synoniemen, RAG-rijen) ná de migratie exact gelijk zijn;
3. de backup werkelijk naar een NIEUW pad hersteld kan worden en dan exact de
   toestand van vóór de migratie teruggeeft, inclusief het oude schema;
4. de gemigreerde database integer is en het productiepad nooit geraakt wordt.

Herstel naar een nieuwe database is dezelfde geverifieerde kopieerroute als
de backup zelf: ``create_verified_backup(backup, nieuw_pad)``. In-place
herstel blijft DEF-666.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from database.migrate_database import migrate_database
from database.migrations import v5_migration, v6_migration, v7_migration
from database.sqlite_backup import create_verified_backup, read_manifest
from tests.fixtures.schema_profiles import (
    bouw_profiel,
    kolommen,
    lees_alles,
    projecteer,
    schema_versies,
    zaai_sentinels,
)

pytestmark = [pytest.mark.integration]

# Kolommen die een route bewust laat vervallen; élke andere verdwenen kolom
# is onbedoeld dataverlies.
BEDOELD_VERWIJDERD: dict[str, dict[str, set[str]]] = {
    "legacy": {"definities": {"voorkeursterm_is_begrip"}},
    "v5": {},
    "v6": {},
    "v7": {"rag_collections": {"document_count", "chunk_count"}},
}
# Tabellen waarin een route bewust rijen toevoegt (versiemarkers).
RIJEN_MOGEN_GROEIEN = {"schema_version"}


def _zaai_extra_gebruikerskolom(pad: Path) -> None:
    """Een extra gebruikerskolom met NULL en JSON die de rebuild moet behouden."""
    conn = sqlite3.connect(str(pad))
    try:
        conn.execute("ALTER TABLE definities ADD COLUMN external_reference TEXT")
        conn.execute(
            "UPDATE definities SET external_reference = '{\"ref\": [1, null]}' "
            "WHERE begrip = 'sentinelbegrip'"
        )
        conn.commit()
    finally:
        conn.close()


def _bump_autoincrement(pad: Path) -> None:
    """Zet de AUTOINCREMENT-teller hoger dan de hoogste aanwezige rij."""
    conn = sqlite3.connect(str(pad))
    try:
        conn.execute(
            "INSERT INTO definities (id, begrip, definitie, categorie) "
            "VALUES (1000, 'tijdelijk', 'tijdelijk', 'type')"
        )
        conn.execute("DELETE FROM definities WHERE id = 1000")
        conn.commit()
    finally:
        conn.close()


def _sequences(pad: Path) -> dict[str, int]:
    conn = sqlite3.connect(str(pad))
    try:
        if not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'sqlite_sequence'"
        ).fetchone():
            return {}
        return {
            naam: int(seq)
            for naam, seq in conn.execute("SELECT name, seq FROM sqlite_sequence")
        }
    finally:
        conn.close()


def test_volledige_herlezing_discrimineert_op_voorheen_niet_geselecteerde_kolom(
    tmp_path: Path,
):
    """Codex-herreview P2: de oude sentinelqueries misten o.a.
    rag_documents.file_path. De volledige herlezing ziet zo'n corruptie."""
    pad = bouw_profiel(tmp_path / "definities.db", 3)
    zaai_sentinels(pad)
    voor = lees_alles(pad)
    conn = sqlite3.connect(str(pad))
    try:
        conn.execute("UPDATE rag_documents SET file_path = 'CORRUPTED'")
        conn.commit()
    finally:
        conn.close()

    assert lees_alles(pad) != voor
    assert (
        voor["rag_documents"][1][0][voor["rag_documents"][0].index("file_path")]
        == "uploads/sentinel-file-path.pdf"
    )


def _integer(pad: Path) -> bool:
    conn = sqlite3.connect(str(pad))
    try:
        return (
            conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            and conn.execute("PRAGMA foreign_key_check").fetchall() == []
        )
    finally:
        conn.close()


ROUTES: list[tuple[str, int | None, str, Callable[[Path], bool], list[int]]] = [
    (
        "legacy",
        3,
        "pre_legacy_migration",
        lambda pad: migrate_database(str(pad)),
        [1, 2, 3],
    ),
    ("v5", None, "pre_v5_migration", v5_migration.run_migration, [1]),
    ("v6", 1, "pre_v6_migration", v6_migration.run_migration, [1, 2]),
    ("v7", 2, "pre_v7_migration", v7_migration.run_migration, [1, 2, 3]),
]


@pytest.mark.parametrize(
    ("route", "profiel", "prefix", "draai", "doelversies"),
    ROUTES,
    ids=[r[0] for r in ROUTES],
)
def test_route_migreert_behoudt_en_is_werkelijk_herstelbaar(
    tmp_path: Path,
    route: str,
    profiel: int | None,
    prefix: str,
    draai: Callable[[Path], bool],
    doelversies: list[int],
):
    bron_dir = tmp_path / "data"
    bron_dir.mkdir()
    pad = bouw_profiel(bron_dir / "definities.db", profiel)
    if route == "legacy":
        # De legacy-route herbouwt alleen als de verouderde kolom er nog is.
        conn = sqlite3.connect(str(pad))
        conn.execute(
            "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
        )
        conn.close()
    zaai_sentinels(pad)
    _zaai_extra_gebruikerskolom(pad)
    _bump_autoincrement(pad)
    # Volledige oorspronkelijke toestand: élke tabel, élke kolom (ook extra
    # gebruikerskolommen), élke rij, plus de AUTOINCREMENT-tellers.
    voor = lees_alles(pad)
    kolommen_voor = {tabel: inhoud[0] for tabel, inhoud in voor.items()}
    sequences_voor = _sequences(pad)
    versies_voor = schema_versies(pad)
    # Volledig bronmanifest (alle objecten mét DDL, kolommen, rijaantallen,
    # versie) van vóór de migratie: het restorebewijs vergelijkt hiertegen.
    conn = sqlite3.connect(str(pad))
    try:
        bronmanifest_voor = read_manifest(conn)
    finally:
        conn.close()
    assert voor["rag_documents"][1] if "rag_documents" in voor else True

    assert draai(pad) is True

    # 1 + 2: doelversie bereikt; alle oorspronkelijke kolomwaarden behouden,
    # met uitsluitend de expliciet bedoelde kolomverwijderingen; database integer.
    assert schema_versies(pad) == doelversies
    na = lees_alles(pad)
    kolommen_na = {tabel: inhoud[0] for tabel, inhoud in na.items()}
    for tabel, oorspronkelijk in kolommen_voor.items():
        verdwenen = set(oorspronkelijk) - set(kolommen_na[tabel])
        assert verdwenen <= BEDOELD_VERWIJDERD[route].get(
            tabel, set()
        ), f"{tabel}: onbedoeld verdwenen kolommen {sorted(verdwenen)}"
    behouden = {
        tabel: tuple(k for k in oorspronkelijk if k in kolommen_na[tabel])
        for tabel, oorspronkelijk in kolommen_voor.items()
    }
    voor_rijen = projecteer(voor, behouden)
    na_rijen = projecteer(na, behouden)
    for tabel, rijen in voor_rijen.items():
        if tabel in RIJEN_MOGEN_GROEIEN:
            # De versiemarker komt erbij; alle oorspronkelijke rijen blijven.
            assert set(rijen) <= set(na_rijen[tabel]), tabel
        else:
            assert na_rijen[tabel] == rijen, tabel
    assert _integer(pad)
    # AUTOINCREMENT-tellers gaan nooit omlaag door een migratie.
    for tabel, seq in sequences_voor.items():
        assert _sequences(pad).get(tabel, 0) >= seq, tabel

    # 3: de backup is de toestand van vóór de migratie en herstelt naar een
    # nieuw pad: exact dezelfde rijen, kolommen, tellers én het oude schema.
    backups = sorted((bron_dir / "backups").glob(f"{prefix}_*.db"))
    assert len(backups) == 1, backups
    hersteld = tmp_path / "hersteld" / "definities.db"
    hersteld.parent.mkdir()
    manifest = create_verified_backup(backups[0], hersteld)

    assert lees_alles(hersteld) == voor
    assert _sequences(hersteld) == sequences_voor
    assert schema_versies(hersteld) == versies_voor
    assert _integer(hersteld)
    conn = sqlite3.connect(str(hersteld))
    try:
        hersteld_manifest = read_manifest(conn)
    finally:
        conn.close()
    # Voor/na-manifestbewijs: de herstelde database is object-voor-object,
    # kolom-voor-kolom en rij-voor-rij de bron van vóór de migratie, en niet
    # alleen wat de helper zelf teruggaf.
    assert hersteld_manifest == bronmanifest_voor
    assert hersteld_manifest == manifest
    # Bewijs dat de vergelijking discrimineert: de gemigreerde bron wijkt af.
    conn = sqlite3.connect(str(pad))
    try:
        assert read_manifest(conn) != bronmanifest_voor
    finally:
        conn.close()
    assert na != voor

    # 4: alleen het tijdelijke pad is geraakt; geen stagingresten.
    assert {p.name for p in bron_dir.iterdir()} <= {
        "backups",
        "definities.db",
        "definities.db-wal",
        "definities.db-shm",
    }
    assert [p.name for p in (bron_dir / "backups").iterdir()] == [backups[0].name]


def test_legacy_route_zonder_kerntabel_wijzigt_niets(tmp_path: Path):
    """De backupguard (core_schema_incomplete) weigert vóór elke schrijfactie."""
    bron_dir = tmp_path / "data"
    bron_dir.mkdir()
    pad = bouw_profiel(bron_dir / "definities.db", 3)
    conn = sqlite3.connect(str(pad))
    conn.executescript(
        "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER;"
        "DROP TABLE import_export_logs;"
    )
    conn.close()
    voor = {
        tabel: kolommen(pad, tabel) for tabel in ("definities", "definitie_voorbeelden")
    }

    assert migrate_database(str(pad)) is False

    assert {
        tabel: kolommen(pad, tabel) for tabel in ("definities", "definitie_voorbeelden")
    } == voor
    assert not (bron_dir / "backups").exists()
