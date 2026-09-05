"""I/O-fouten, resourcesluiting en versietypevalidatie (DEF-664, Codex-interimreview).

Bewezen op de tussenversie:

- v5/v6/v7 gaven False bij een PRAGMA-fout ná ``connect`` maar sloten de
  verbinding niet;
- de verse init liet een ``OSError`` uit het in-memory canonieke contract
  rauw ontsnappen, zonder ROLLBACK en met een open transactie;
- de legacy-route sloot haar verbinding niet (``with sqlite3.connect``
  commit alleen);
- een ``PermissionError`` bij het aanmaken van ``backups/`` ontsnapte uit
  v5/v6/v7 in plaats van False + niets gewijzigd;
- ``schema_version`` accepteerde ``3.5`` als 3 en lekte ``ValueError`` bij
  ``'unexpected'``.

Alle tests op tijdelijke databases; injecties zijn functioneel (echte
SQLite-connecties met een falende stap), nooit een spiegel van het contract.
"""

from __future__ import annotations

import sqlite3
import types
from pathlib import Path

import pytest

import database.migrate_database as legacy
import database.migrations.v5_migration as v5
import database.migrations.v6_migration as v6
import database.migrations.v7_migration as v7
from database.db_connection import DatabaseConnection
from tests.fixtures.schema_profiles import bouw_profiel, kolommen, schema_versies

pytestmark = [pytest.mark.unit]


class _Cursor(sqlite3.Cursor):
    """Cursor die dezelfde faalregel toepast als zijn verbinding."""

    def execute(self, sql, *args):  # type: ignore[override]
        faal_op = getattr(self.connection, "faal_op", None)
        if faal_op and str(sql).lstrip().upper().startswith(faal_op):
            raise sqlite3.OperationalError("disk I/O error")
        return super().execute(sql, *args)


class _Verbinding(sqlite3.Connection):
    """Echte connectie die één statement laat falen en het sluiten telt."""

    faal_op: str | None = None
    close_calls = 0

    def execute(self, sql, *args):  # type: ignore[override]
        if self.faal_op and str(sql).lstrip().upper().startswith(self.faal_op):
            raise sqlite3.OperationalError("disk I/O error")
        return super().execute(sql, *args)

    def cursor(self, factory=None):  # type: ignore[override]
        return super().cursor(factory or _Cursor)

    def close(self) -> None:
        type(self).close_calls += 1
        super().close()


def _verbindingsklasse(faal_op: str | None) -> type[_Verbinding]:
    return type("Verbinding", (_Verbinding,), {"faal_op": faal_op, "close_calls": 0})


def _sqlite_namespace(factory: type[sqlite3.Connection]) -> types.SimpleNamespace:
    def connect(*args, **kwargs):
        kwargs.setdefault("factory", factory)
        return sqlite3.connect(*args, **kwargs)

    return types.SimpleNamespace(
        connect=connect,
        Connection=sqlite3.Connection,
        Error=sqlite3.Error,
        OperationalError=sqlite3.OperationalError,
        DatabaseError=sqlite3.DatabaseError,
        IntegrityError=sqlite3.IntegrityError,
    )


ROUTES = [
    pytest.param(v5, None, "pre_v5_migration", id="v5"),
    pytest.param(v6, 1, "pre_v6_migration", id="v6"),
    pytest.param(v7, 2, "pre_v7_migration", id="v7"),
]


def _profiel(tmp_path: Path, versie: int | None) -> Path:
    (tmp_path / "data").mkdir()
    return bouw_profiel(tmp_path / "data" / "definities.db", versie)


class TestVerbindingWordtGesloten:
    @pytest.mark.parametrize(("module", "profiel", "_prefix"), ROUTES)
    def test_pragma_fout_na_connect_geeft_false_en_sluit(
        self, tmp_path, monkeypatch, module, profiel, _prefix
    ):
        pad = _profiel(tmp_path, profiel)
        klasse = _verbindingsklasse("PRAGMA JOURNAL_MODE")
        monkeypatch.setattr(module, "sqlite3", _sqlite_namespace(klasse))

        assert module.run_migration(pad) is False

        assert klasse.close_calls == 1
        assert schema_versies(pad) == (
            [] if profiel is None else list(range(1, profiel + 1))
        )

    @pytest.mark.parametrize(("module", "profiel", "_prefix"), ROUTES)
    def test_geslaagde_route_sluit_de_verbinding(
        self, tmp_path, monkeypatch, module, profiel, _prefix
    ):
        pad = _profiel(tmp_path, profiel)
        klasse = _verbindingsklasse(None)
        monkeypatch.setattr(module, "sqlite3", _sqlite_namespace(klasse))

        assert module.run_migration(pad) is True

        assert klasse.close_calls == 1

    def test_legacy_route_sluit_de_verbinding_bij_succes_en_bij_fout(
        self, tmp_path, monkeypatch
    ):
        pad = _profiel(tmp_path, 3)
        klasse = _verbindingsklasse(None)
        monkeypatch.setattr(legacy, "sqlite3", _sqlite_namespace(klasse))
        assert legacy.migrate_database(str(pad)) is True
        assert klasse.close_calls == 1

        kapot = _verbindingsklasse("PRAGMA FOREIGN_KEYS = ON")
        monkeypatch.setattr(legacy, "sqlite3", _sqlite_namespace(kapot))
        assert legacy.migrate_database(str(pad)) is False
        assert kapot.close_calls == 1


class TestBackupIoFouten:
    @pytest.mark.parametrize(("module", "profiel", "_prefix"), ROUTES)
    def test_onschrijfbare_backupmap_geeft_false_en_wijzigt_niets(
        self, tmp_path, monkeypatch, module, profiel, _prefix
    ):
        pad = _profiel(tmp_path, profiel)
        origineel = Path.mkdir

        def _weiger(self, *args, **kwargs):
            if self.name == "backups":
                raise PermissionError(13, "Permission denied")
            return origineel(self, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", _weiger)
        versies_voor = schema_versies(pad)

        assert module.run_migration(pad) is False

        assert schema_versies(pad) == versies_voor
        assert not (pad.parent / "backups").exists()

    def test_legacy_onschrijfbare_backupmap_geeft_false(self, tmp_path, monkeypatch):
        pad = _profiel(tmp_path, 3)
        origineel = Path.mkdir

        def _weiger(self, *args, **kwargs):
            if self.name == "backups":
                raise PermissionError(13, "Permission denied")
            return origineel(self, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", _weiger)

        assert legacy.migrate_database(str(pad)) is False


class TestVersietypeValidatie:
    @pytest.mark.parametrize("waarde", ["3.5", "'unexpected'"], ids=["float", "tekst"])
    def test_ongeldige_versiewaarde_is_typed(self, tmp_path, waarde):
        # NULL is geen geval: schema_version.version is NOT NULL.
        from database.schema_contract import SchemaContractError, schema_version

        pad = bouw_profiel(tmp_path / "v3.db", 3)
        conn = sqlite3.connect(str(pad))
        conn.execute(
            f"INSERT INTO schema_version (version, description) VALUES ({waarde}, 'x')"
        )
        conn.commit()
        try:
            with pytest.raises(SchemaContractError) as excinfo:
                schema_version(conn)
            assert excinfo.value.reason == "schema_version_invalid"
        finally:
            conn.close()

    def test_startup_op_ongeldige_versie_is_typed(self, tmp_path):
        from database.schema_contract import SchemaContractError

        pad = bouw_profiel(tmp_path / "v3.db", 3)
        conn = sqlite3.connect(str(pad))
        conn.execute(
            "INSERT INTO schema_version (version, description) VALUES (3.5, 'x')"
        )
        conn.commit()
        conn.close()

        with pytest.raises(SchemaContractError) as excinfo:
            DatabaseConnection(str(pad)).init_database()
        assert excinfo.value.reason == "schema_version_invalid"

    def test_migratie_op_ongeldige_versie_geeft_false(self, tmp_path):
        pad = _profiel(tmp_path, 2)
        conn = sqlite3.connect(str(pad))
        conn.execute(
            "INSERT INTO schema_version (version, description) VALUES ('x', 'x')"
        )
        conn.commit()
        conn.close()

        assert v7.run_migration(pad) is False
        assert "document_count" in kolommen(pad, "rag_collections")


class _PragmaRegistrerendeVerbinding(_Verbinding):
    """Leest bij het sluiten de PRAGMA's van déze verbinding (per-connectie!)."""

    laatste_pragmas: tuple[int, int] | None = None

    def close(self) -> None:
        try:
            fk = super().execute("PRAGMA foreign_keys").fetchone()[0]
            legacy = super().execute("PRAGMA legacy_alter_table").fetchone()[0]
            type(self).laatste_pragmas = (int(fk), int(legacy))
        except sqlite3.Error:
            type(self).laatste_pragmas = None
        super().close()


def _registrerende_klasse(faal_op: str | None) -> type[_PragmaRegistrerendeVerbinding]:
    return type(
        "Registrerend",
        (_PragmaRegistrerendeVerbinding,),
        {"faal_op": faal_op, "close_calls": 0, "laatste_pragmas": None},
    )


def _pragmas_op(conn: sqlite3.Connection) -> tuple[int, int]:
    return (
        int(conn.execute("PRAGMA foreign_keys").fetchone()[0]),
        int(conn.execute("PRAGMA legacy_alter_table").fetchone()[0]),
    )


class TestMigratiemodusHersteltOpDezelfdeVerbinding:
    """Codex-herreview P2: een fout bij `PRAGMA legacy_alter_table=ON` ná een
    geslaagde `foreign_keys=OFF` liet foreign_keys=0 achter; de bestaande
    test las PRAGMA's op een nieuwe verbinding en bewees dus niets."""

    def _verbinding(self, tmp_path, faal_op):
        klasse = _verbindingsklasse(faal_op)
        conn = sqlite3.connect(str(tmp_path / "pragma.db"), factory=klasse)
        conn.isolation_level = None
        conn.execute("PRAGMA foreign_keys=ON")
        assert _pragmas_op(conn) == (1, 0)
        return conn

    def test_falende_tweede_setup_pragma_herstelt_de_eerste(self, tmp_path):
        conn = self._verbinding(tmp_path, "PRAGMA LEGACY_ALTER_TABLE=ON")
        try:
            with pytest.raises(sqlite3.OperationalError), legacy._migratiemodus(conn):
                pass  # pragma: no cover - setup faalt al
            assert _pragmas_op(conn) == (1, 0)
        finally:
            conn.close()

    def test_falende_body_herstelt_beide(self, tmp_path):
        conn = self._verbinding(tmp_path, None)
        gezien: list[tuple[int, int]] = []

        def _body_faalt() -> None:
            with legacy._migratiemodus(conn):
                gezien.append(_pragmas_op(conn))
                raise RuntimeError("geinjecteerde bodyfout")

        try:
            with pytest.raises(RuntimeError):
                _body_faalt()
            assert gezien == [(0, 1)]
            assert _pragmas_op(conn) == (1, 0)
        finally:
            conn.close()

    def test_falende_herstelstap_herstelt_de_rest(self, tmp_path):
        conn = self._verbinding(tmp_path, "PRAGMA LEGACY_ALTER_TABLE=0")
        try:
            with pytest.raises(sqlite3.OperationalError), legacy._migratiemodus(conn):
                pass
            assert int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) == 1
        finally:
            conn.close()

    def test_legacy_route_laat_pragmas_hersteld_op_de_gebruikte_verbinding(
        self, tmp_path, monkeypatch
    ):
        pad = _profiel(tmp_path, 3)
        conn = sqlite3.connect(str(pad))
        conn.execute(
            "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER"
        )
        conn.commit()
        conn.close()
        klasse = _registrerende_klasse(None)
        monkeypatch.setattr(legacy, "sqlite3", _sqlite_namespace(klasse))

        def _klapt(conn, table_name="definities"):
            raise sqlite3.OperationalError("geinjecteerde fout in rebuild")

        monkeypatch.setattr(legacy, "_create_definities_table", _klapt)

        assert legacy.migrate_database(str(pad)) is False

        assert klasse.close_calls == 1
        assert klasse.laatste_pragmas == (1, 0)


class TestVerifyMigrationSluitDeVerbinding:
    """Codex-herreview P2: de aanvullende CLI-verificatie gebruikte alleen de
    SQLite-contextmanager (commit, geen close)."""

    def test_succespad_sluit(self, tmp_path, monkeypatch):
        pad = _profiel(tmp_path, 3)
        klasse = _verbindingsklasse(None)
        monkeypatch.setattr(legacy, "sqlite3", _sqlite_namespace(klasse))

        assert legacy.verify_migration(str(pad)) is True

        assert klasse.close_calls == 1

    def test_foutpad_sluit(self, tmp_path, monkeypatch):
        pad = _profiel(tmp_path, 3)
        klasse = _verbindingsklasse("PRAGMA TABLE_INFO")
        monkeypatch.setattr(legacy, "sqlite3", _sqlite_namespace(klasse))

        assert legacy.verify_migration(str(pad)) is False

        assert klasse.close_calls == 1


class TestInitIoGrens:
    """Rootprobe (probe-init-io-boundary): mkdir, connect en de eerste query
    van init stonden buiten de getypeerde foutgrens."""

    def test_bovenliggend_pad_is_een_bestand(self, tmp_path):
        from database.schema_contract import SchemaContractError

        (tmp_path / "bestand").write_text("x")
        pad = tmp_path / "bestand" / "definities.db"

        with pytest.raises(SchemaContractError) as excinfo:
            DatabaseConnection(str(pad)).init_database()
        assert excinfo.value.reason == "schema_init_failed"
        assert "database_dir_unavailable" in excinfo.value.details

    def test_corrupt_bestand_is_typed_en_lekt_geen_verbinding(
        self, tmp_path, monkeypatch
    ):
        import database.db_connection as dbc
        from database.schema_contract import SchemaContractError

        pad = tmp_path / "corrupt.db"
        pad.write_bytes(b"dit is geen sqlite-database " * 64)
        klasse = _verbindingsklasse(None)
        ns = _sqlite_namespace(klasse)
        ns.Row = sqlite3.Row
        monkeypatch.setattr(dbc, "sqlite3", ns)
        db = DatabaseConnection(str(pad))

        with pytest.raises(SchemaContractError) as excinfo:
            db.init_database()

        assert excinfo.value.reason == "database_unreadable"
        assert klasse.close_calls == 1
        assert db._thread_local.state.connection is None

    def test_pragma_fout_in_get_connection_sluit_de_nieuwe_verbinding(
        self, tmp_path, monkeypatch
    ):
        import database.db_connection as dbc

        klasse = _verbindingsklasse("PRAGMA FOREIGN_KEYS")
        ns = _sqlite_namespace(klasse)
        ns.Row = sqlite3.Row
        monkeypatch.setattr(dbc, "sqlite3", ns)
        db = DatabaseConnection(str(tmp_path / "vers.db"))

        with pytest.raises(sqlite3.Error):
            db.get_connection()

        assert klasse.close_calls == 1

    def test_open_buitenste_transactie_wordt_niet_aangeraakt(self, tmp_path):
        from database.schema_contract import SchemaContractError

        db = DatabaseConnection(str(tmp_path / "vers.db"))
        conn = db.get_connection()
        conn.execute("BEGIN")
        conn.execute("CREATE TABLE buitenste (x INTEGER)")

        with pytest.raises(SchemaContractError) as excinfo:
            db.init_database()

        assert excinfo.value.reason == "schema_init_failed"
        assert conn.in_transaction is True
        conn.execute("ROLLBACK")
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0


class TestOnleesbaarCanoniekSchema:
    def test_verse_init_geeft_typed_fout_en_rolt_terug(self, tmp_path, monkeypatch):
        from database import schema_contract

        monkeypatch.setattr(
            schema_contract, "SCHEMA_PATH", tmp_path / "canoniek-bestaat-niet.sql"
        )
        pad = tmp_path / "vers.db"
        db = DatabaseConnection(str(pad))

        with pytest.raises(schema_contract.SchemaContractError) as excinfo:
            db.init_database()

        assert excinfo.value.reason == "canonical_schema_unreadable"
        conn = db.get_connection()
        assert conn.in_transaction is False
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0

    def test_bestaande_database_geeft_typed_fout(self, tmp_path, monkeypatch):
        from database import schema_contract

        pad = bouw_profiel(tmp_path / "v3.db", 3)
        monkeypatch.setattr(
            schema_contract, "SCHEMA_PATH", tmp_path / "canoniek-bestaat-niet.sql"
        )

        with pytest.raises(schema_contract.SchemaContractError) as excinfo:
            DatabaseConnection(str(pad)).init_database()
        assert excinfo.value.reason == "canonical_schema_unreadable"
