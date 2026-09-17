"""Tests voor V8 Migration (DEF-751): `definities.categorie` optioneel.

Op een tijdelijke profiel-3-database (eigen fixture-DDL) met alle elf
categoriewaarden, FK-kinderen, een extra gebruikerskolom en -index en
sentinels in de overige tabellen. Na de migratie: NULL toegestaan, de CHECK
weigert nog steeds ongeldige waarden, ids/rijen/waarden/objecten/teller/
FK's exact behouden, startupcontract v4 groen; bij een fout halverwege blijft
de database exact zoals ervoor (backup aanwezig).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

import database.migrations.v8_migration as v8
from database.db_connection import DatabaseConnection
from database.schema_contract import (
    CANONICAL_VERSION,
    SchemaContractError,
    assert_startup_contract,
    target_contract,
)
from tests.fixtures.schema_profiles import (
    bouw_profiel,
    kolommen,
    lees_sentinels,
    schema_versies,
    zaai_sentinels,
)

pytestmark = [pytest.mark.unit]

ELF = (
    "type",
    "proces",
    "resultaat",
    "exemplaar",
    "ENT",
    "ACT",
    "REL",
    "ATT",
    "AUT",
    "STA",
    "OTH",
)


def _sql(pad: Path, script: str) -> None:
    conn = sqlite3.connect(str(pad))
    try:
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()


def _rijen(pad: Path, query: str) -> list[tuple]:
    conn = sqlite3.connect(str(pad))
    try:
        return conn.execute(query).fetchall()
    finally:
        conn.close()


def _objecten(pad: Path) -> set[tuple[str, str]]:
    return {
        (t, n)
        for t, n in _rijen(
            pad,
            "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'",
        )
    }


def _categorie_notnull(pad: Path) -> bool:
    for _cid, naam, _t, notnull, _d, _pk in _rijen(
        pad, "PRAGMA table_info(definities)"
    ):
        if naam == "categorie":
            return bool(notnull)
    raise AssertionError("kolom categorie ontbreekt")


@pytest.fixture
def v3_db(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    pad = bouw_profiel(tmp_path / "data" / "definities.db", 3)
    zaai_sentinels(pad)
    # Alle elf waarden, met FK-kinderen op de eerste; een extra gebruikerskolom
    # en -index die de rebuild moet behouden.
    _sql(
        pad,
        "ALTER TABLE definities ADD COLUMN extra_kolom TEXT;"
        "CREATE INDEX idx_extra_kolom ON definities(extra_kolom);"
        + "".join(
            "INSERT INTO definities (begrip, definitie, categorie, "
            "organisatorische_context, extra_kolom) VALUES "
            f"('b-{w}', 'kern {w}', '{w}', '[\"DJI\"]', 'x-{w}');"
            for w in ELF
        )
        + "INSERT INTO definitie_tags (definitie_id, tag_naam, tag_waarde) "
        "SELECT id, 'elf', 'ja' FROM definities WHERE begrip = 'b-type';"
        "DELETE FROM definities WHERE begrip = 'b-OTH';",  # gat in de id-reeks
    )
    return pad


def _bron(pad: Path) -> dict:
    return {
        "sentinels": lees_sentinels(pad),
        "definities": _rijen(
            pad, "SELECT id, begrip, categorie, extra_kolom FROM definities ORDER BY id"
        ),
        "tags": _rijen(
            pad, "SELECT definitie_id, tag_naam FROM definitie_tags ORDER BY 1, 2"
        ),
        "objecten": _objecten(pad),
        "seq": _rijen(pad, "SELECT seq FROM sqlite_sequence WHERE name = 'definities'"),
        # Kolomvolgorde is geen contract (de rebuild volgt de canonieke DDL en
        # zet extra kolommen achteraan); de verzameling wél.
        "kolommen": sorted(kolommen(pad, "definities")),
    }


class TestGeslaagdeMigratie:
    def test_v3_naar_v4_verliesvrij(self, v3_db: Path):
        voor = _bron(v3_db)
        assert _categorie_notnull(v3_db)
        assert schema_versies(v3_db) == [1, 2, 3]

        assert v8.run_migration(v3_db) is True

        assert not _categorie_notnull(v3_db)
        assert schema_versies(v3_db) == [1, 2, 3, 4]
        assert (
            _bron(v3_db) == voor
        )  # ids, rijen, waarden, extra kolom, objecten, teller
        assert _rijen(v3_db, "PRAGMA foreign_key_check") == []
        assert _rijen(v3_db, "PRAGMA integrity_check") == [("ok",)]
        assert sorted((v3_db.parent / "backups").glob("pre_v8_migration_*.db"))

    def test_na_migratie_is_null_toegestaan_en_ongeldig_nog_geweigerd(self, v3_db):
        assert v8.run_migration(v3_db) is True
        conn = sqlite3.connect(str(v3_db))
        try:
            conn.execute(
                "INSERT INTO definities (begrip, definitie, categorie) VALUES (?,?,NULL)",
                ("zonder", "kern"),
            )
            with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
                conn.execute(
                    "INSERT INTO definities (begrip, definitie, categorie) VALUES (?,?,?)",
                    ("fout", "kern", "Type"),
                )
            conn.commit()
        finally:
            conn.close()
        assert _rijen(
            v3_db, "SELECT categorie FROM definities WHERE begrip='zonder'"
        ) == [(None,)]

    def test_gemigreerde_database_haalt_het_startupcontract(self, v3_db):
        assert v8.run_migration(v3_db) is True
        conn = sqlite3.connect(str(v3_db))
        try:
            assert_startup_contract(conn)  # geen exceptie
        finally:
            conn.close()
        db = DatabaseConnection(str(v3_db))
        db.init_database()  # tweede startup is idempotent

    def test_herhaald_uitvoeren_is_idempotent(self, v3_db):
        assert v8.run_migration(v3_db) is True
        na_een = _bron(v3_db)
        assert v8.run_migration(v3_db) is True
        assert _bron(v3_db) == na_een
        assert schema_versies(v3_db) == [1, 2, 3, 4]

    def test_teller_hergebruikt_geen_verwijderd_id(self, v3_db):
        laatste_voor = _rijen(v3_db, "SELECT MAX(id) FROM definities")[0][0]
        assert v8.run_migration(v3_db) is True
        _sql(
            v3_db,
            "INSERT INTO definities (begrip, definitie, categorie) "
            "VALUES ('nieuw', 'kern', 'type');",
        )
        nieuw_id = _rijen(v3_db, "SELECT id FROM definities WHERE begrip='nieuw'")[0][0]
        assert nieuw_id > laatste_voor + 1  # het gat van b-OTH wordt niet hergebruikt


class TestFailClosed:
    def test_fout_in_rebuild_laat_de_database_exact_zoals_ervoor(self, v3_db):
        voor = _bron(v3_db)
        with patch.object(
            v8,
            "_ensure_definities_indexes",
            side_effect=sqlite3.OperationalError("boem"),
        ):
            assert v8.run_migration(v3_db) is False
        assert _bron(v3_db) == voor
        assert _categorie_notnull(v3_db)
        assert schema_versies(v3_db) == [1, 2, 3]
        assert _rijen(v3_db, "PRAGMA foreign_key_check") == []
        # PRAGMA's hersteld: foreign keys weer afdwingbaar op een nieuwe verbinding
        conn = sqlite3.connect(str(v3_db))
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO definitie_tags (definitie_id, tag_naam) VALUES (999999, 'x')"
                )
        finally:
            conn.close()

    def test_v2_database_wordt_geweigerd(self, tmp_path):
        (tmp_path / "data").mkdir()
        pad = bouw_profiel(tmp_path / "data" / "definities.db", 2)
        assert v8.run_migration(pad) is False
        assert schema_versies(pad) == [1, 2]

    def test_ontbrekende_database(self, tmp_path):
        assert v8.run_migration(tmp_path / "bestaat-niet.db") is False


class TestContractPerVersie:
    def test_profiel_3_eist_not_null_en_profiel_4_niet(self):
        assert CANONICAL_VERSION == 4
        kolom3 = target_contract(3).columns["definities"]["categorie"]
        kolom4 = target_contract(4).columns["definities"]["categorie"]
        assert kolom3[1] == 1 and kolom4[1] == 0  # notnull-vlag
        assert (
            target_contract(3).checks["definities"]
            == target_contract(4).checks["definities"]
        )

    def test_v3_database_wordt_bij_startup_geweigerd_met_v8_hint(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        conn = sqlite3.connect(str(pad))
        try:
            with pytest.raises(SchemaContractError) as excinfo:
                assert_startup_contract(conn)
        finally:
            conn.close()
        assert excinfo.value.reason == "schema_version_outdated"
        assert any("v8" in d for d in excinfo.value.details)
