"""Fail-closed schema-initialisatie en canoniek schemacontract (DEF-664).

Gemeten vóór deze reparatie (root-schema-probe.log en de CLI-specificatie):

- een database met alleen een minimale ``definities``-tabel werd bij init
  stilzwijgend geaccepteerd;
- een botsend object liet ``executescript`` halverwege falen; drie tabellen en
  negen indexen bleven staan en de constructor keerde normaal terug;
- een verse database kreeg de schema.sql-vorm van vóór v6/v7: geen
  ``bron_type``/``metadata`` op rag_chunks terwijl de embedding-store die
  kolommen schrijft, en een lege ``schema_version``.

Deze suite draait uitsluitend op tijdelijke databases.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database.db_connection import DatabaseConnection
from tests.fixtures.schema_profiles import bouw_profiel, kolommen, schema_versies

pytestmark = [pytest.mark.unit]


def _objecten(pad: Path) -> set[tuple[str, str]]:
    conn = sqlite3.connect(str(pad))
    try:
        return {
            (rij[0], rij[1])
            for rij in conn.execute(
                "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            )
        }
    finally:
        conn.close()


def _sql(pad: Path, script: str) -> None:
    conn = sqlite3.connect(str(pad))
    try:
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()


def _init(pad: Path) -> DatabaseConnection:
    db = DatabaseConnection(str(pad))
    db.init_database()
    return db


def _contractfout(pad: Path):
    from database.schema_contract import SchemaContractError

    with pytest.raises(SchemaContractError) as excinfo:
        _init(pad)
    return excinfo.value


class TestVerseDatabase:
    def test_verse_init_levert_het_canonieke_versie_3_schema(self, tmp_path):
        from database.schema_contract import (
            CANONICAL_VERSION,
            canonical_contract,
            contract_problems,
            read_contract,
        )

        pad = tmp_path / "vers.db"
        db = _init(pad)

        conn = db.get_connection()
        assert contract_problems(read_contract(conn), canonical_contract()) == []
        assert schema_versies(pad) == [1, 2, 3]
        assert CANONICAL_VERSION == 3
        assert [tuple(r) for r in conn.execute("PRAGMA integrity_check")] == [("ok",)]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    def test_verse_init_heeft_de_kolommen_die_de_app_schrijft(self, tmp_path):
        pad = tmp_path / "vers.db"
        _init(pad)

        assert {"bron_type", "metadata"} <= set(kolommen(pad, "rag_chunks"))
        assert "file_path" in kolommen(pad, "rag_documents")
        assert not {"document_count", "chunk_count"} & set(
            kolommen(pad, "rag_collections")
        )

    def test_verse_init_bevat_de_verplichte_historietrigger(self, tmp_path):
        pad = tmp_path / "vers.db"
        _init(pad)
        assert ("trigger", "log_definitie_changes") in _objecten(pad)

    def test_verse_init_behoudt_het_bestaande_seedcontract(self, tmp_path):
        # Voorbeelddata blijft zoals het bestaande contract (twee definities,
        # vier tags); een nieuw seedbeleid valt buiten DEF-664.
        pad = tmp_path / "vers.db"
        db = _init(pad)
        conn = db.get_connection()
        assert conn.execute("SELECT COUNT(*) FROM definities").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM definitie_tags").fetchone()[0] == 4

    def test_tweede_init_op_dezelfde_database_is_idempotent(self, tmp_path):
        pad = tmp_path / "vers.db"
        _init(pad)
        voor = _objecten(pad)
        _init(pad)
        assert _objecten(pad) == voor
        assert schema_versies(pad) == [1, 2, 3]


class TestInitFaaltGesloten:
    def test_deelschema_wordt_geweigerd_en_niet_aangevuld(self, tmp_path):
        pad = tmp_path / "deel.db"
        _sql(pad, "CREATE TABLE definities (id INTEGER PRIMARY KEY, begrip TEXT);")

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert _objecten(pad) == {("table", "definities")}

    def test_deelschema_via_de_repositoryconstructor_faalt_ook(self, tmp_path):
        from database.definitie_repository import DefinitieRepository
        from database.schema_contract import SchemaContractError

        pad = tmp_path / "deel.db"
        _sql(pad, "CREATE TABLE definities (id INTEGER PRIMARY KEY, begrip TEXT);")

        with pytest.raises(SchemaContractError):
            DefinitieRepository(str(pad))

    def test_botsend_object_laat_geen_half_schema_achter(self, tmp_path):
        # Een bestaande, afwijkende tabel is geen verse database: init mag
        # het script niet eens starten en niets aanvullen.
        pad = tmp_path / "bots.db"
        _sql(pad, "CREATE TABLE definitie_tags (id INTEGER);")

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert _objecten(pad) == {("table", "definitie_tags")}

    def test_syntaxfout_in_het_schemascript_rolt_alles_terug(
        self, tmp_path, monkeypatch
    ):
        import database.db_connection as dbc

        kapot = tmp_path / "kapot.sql"
        kapot.write_text(
            "CREATE TABLE definities (id INTEGER PRIMARY KEY);\n"
            "CREATE TABLE synonym_groups (id INTEGER PRIMARY KEY);\n"
            "CREATE TABLE definities (id INTEGER PRIMARY KEY);\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(dbc, "SCHEMA_PATH", kapot)
        pad = tmp_path / "vers.db"

        fout = _contractfout(pad)

        assert fout.reason == "schema_init_failed"
        assert _objecten(pad) == set()

    def test_ontbrekend_schemascript_maakt_geen_noodschema(self, tmp_path, monkeypatch):
        import database.db_connection as dbc

        monkeypatch.setattr(dbc, "SCHEMA_PATH", tmp_path / "bestaat-niet.sql")
        pad = tmp_path / "vers.db"

        fout = _contractfout(pad)

        assert fout.reason == "schema_init_failed"
        assert _objecten(pad) == set()

    def test_commitfout_bij_init_rolt_terug_en_sluit_de_transactie(
        self, tmp_path, monkeypatch
    ):
        from database import schema_contract

        def _commit_faalt(conn):
            raise sqlite3.OperationalError("disk I/O error")

        monkeypatch.setattr(schema_contract, "_commit", _commit_faalt)
        pad = tmp_path / "vers.db"
        db = DatabaseConnection(str(pad))

        with pytest.raises(schema_contract.SchemaContractError) as excinfo:
            db.init_database()

        assert excinfo.value.reason == "schema_init_failed"
        assert db.get_connection().in_transaction is False
        assert _objecten(pad) == set()

    def test_onvolledige_versiegeschiedenis_wordt_niet_gepubliceerd(
        self, tmp_path, monkeypatch
    ):
        # Codex-herreview P2: het script zaaide alleen marker 3; init committe
        # en startup weigerde daarna dezelfde database. Alleen de uitgevoerde
        # seedmarkers worden gesaboteerd; het canonieke contract blijft.
        import database.db_connection as dbc
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        oud = (
            "    (1, 'Initial v5 migration'),\n"
            "    (2, 'Hybrid schema: bron_type + JSONB metadata on rag_chunks'),\n"
        )
        assert tekst.count(oud) == 1
        alleen_3 = tmp_path / "alleen-marker-3.sql"
        alleen_3.write_text(tekst.replace(oud, ""), encoding="utf-8")
        monkeypatch.setattr(dbc, "SCHEMA_PATH", alleen_3)
        pad = tmp_path / "vers.db"

        fout = _contractfout(pad)

        assert fout.reason in {"schema_drift", "schema_incomplete"}
        assert any("schema_version" in d for d in fout.details)
        assert _objecten(pad) == set()

    @pytest.mark.parametrize("marker", ["2.5", "'unexpected'"], ids=["float", "tekst"])
    def test_ongeldige_seedmarker_wordt_niet_gepubliceerd(
        self, tmp_path, monkeypatch, marker
    ):
        # Codex-review 3 (P2): 2.5 werd tot 2 geconverteerd en gecommit;
        # 'unexpected' lekte een ValueError met open transactie en 62 objecten.
        import database.db_connection as dbc
        from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

        tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        oud = "    (2, 'Hybrid schema: bron_type + JSONB metadata on rag_chunks'),\n"
        assert tekst.count(oud) == 1
        script = tmp_path / "marker.sql"
        script.write_text(
            tekst.replace(oud, f"    ({marker}, 'gesaboteerd'),\n"), encoding="utf-8"
        )
        monkeypatch.setattr(dbc, "SCHEMA_PATH", script)
        pad = tmp_path / "vers.db"
        db = DatabaseConnection(str(pad))

        from database.schema_contract import SchemaContractError

        with pytest.raises(SchemaContractError) as excinfo:
            db.init_database()

        assert excinfo.value.reason == "schema_version_invalid"
        assert db.get_connection().in_transaction is False
        assert _objecten(pad) == set()
        # Een volgende startup is consistent: nog steeds een verse, lege database.
        with pytest.raises(SchemaContractError):
            DatabaseConnection(str(pad)).init_database()
        assert _objecten(pad) == set()

    def test_incompleet_verse_schema_wordt_niet_gepubliceerd(
        self, tmp_path, monkeypatch
    ):
        # Het script slaagt syntactisch maar levert niet het canonieke
        # contract: de init mag dat niet committen.
        import database.db_connection as dbc

        onvolledig = tmp_path / "onvolledig.sql"
        onvolledig.write_text(
            "CREATE TABLE definities (id INTEGER PRIMARY KEY, begrip TEXT, definitie TEXT);\n"
            "CREATE TABLE synonym_groups (id INTEGER PRIMARY KEY, canonical_term TEXT);\n"
            "CREATE TABLE schema_version (id INTEGER PRIMARY KEY, version INTEGER);\n"
            "INSERT INTO schema_version (version) VALUES (3);\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(dbc, "SCHEMA_PATH", onvolledig)
        pad = tmp_path / "vers.db"

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert _objecten(pad) == set()


class TestVersieprofielen:
    @pytest.mark.parametrize("versie", [None, 1, 2], ids=["pre-v5", "v1", "v2"])
    def test_lagere_versie_wordt_geweigerd_als_startupschema(self, tmp_path, versie):
        pad = bouw_profiel(tmp_path / "oud.db", versie)
        voor = _objecten(pad)

        fout = _contractfout(pad)

        assert fout.reason == "schema_version_outdated"
        assert "3" in " ".join(fout.details)
        assert _objecten(pad) == voor, "startup mag een oude database niet migreren"

    def test_hogere_versie_wordt_geweigerd(self, tmp_path):
        pad = bouw_profiel(tmp_path / "toekomst.db", 3)
        _sql(pad, "INSERT INTO schema_version (version, description) VALUES (4, 'x');")

        fout = _contractfout(pad)

        assert fout.reason == "schema_version_unsupported"

    def test_versie_3_profiel_start(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _init(pad)


class TestDoelcontractPerVersie:
    """De ondersteunde profielen zijn expliciet en de doelcontracten kloppen
    met onafhankelijk opgebouwde profieldatabases (geen spiegel: de fixture
    heeft haar eigen DDL)."""

    @pytest.mark.parametrize(("profiel", "versie"), [(None, 0), (1, 1), (2, 2), (3, 3)])
    def test_profiel_haalt_zijn_eigen_doelcontract(self, tmp_path, profiel, versie):
        from database.schema_contract import (
            SUPPORTED_VERSIONS,
            verify_target_contract,
        )

        assert versie in SUPPORTED_VERSIONS
        pad = bouw_profiel(tmp_path / "profiel.db", profiel)
        conn = sqlite3.connect(str(pad))
        try:
            assert verify_target_contract(conn, versie) == []
        finally:
            conn.close()

    def test_profiel_haalt_een_ander_doelcontract_niet(self, tmp_path):
        # Objectgewijs zijn de profielen supersets van elkaar (extra objecten
        # blijven toegestaan); de versiemarkers maken het onderscheid.
        from database.schema_contract import verify_target_contract

        pad = bouw_profiel(tmp_path / "v2.db", 2)
        conn = sqlite3.connect(str(pad))
        try:
            assert verify_target_contract(conn, 3) != []
            assert verify_target_contract(conn, 1) != []
        finally:
            conn.close()

    def test_beschadigd_profiel_haalt_zijn_doelcontract_niet(self, tmp_path):
        from database.schema_contract import verify_target_contract

        pad = bouw_profiel(tmp_path / "v1.db", 1)
        _sql(pad, "DROP TRIGGER log_definitie_changes;")
        conn = sqlite3.connect(str(pad))
        try:
            problemen = verify_target_contract(conn, 1)
        finally:
            conn.close()
        assert any("log_definitie_changes" in p for p in problemen)

    def test_onbekende_versie_heeft_geen_doelcontract(self):
        from database.schema_contract import SchemaContractError, target_contract

        with pytest.raises(SchemaContractError) as excinfo:
            target_contract(4)
        assert excinfo.value.reason == "schema_version_unsupported"


class TestCanoniekeVolledigheid:
    """Naam-aanwezigheid alleen is niet genoeg: de definitie moet kloppen."""

    def test_ontbrekende_trigger_is_incompleet(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(pad, "DROP TRIGGER log_definitie_changes;")

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert any("log_definitie_changes" in d for d in fout.details)

    def test_ontbrekende_kolom_is_incompleet(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(pad, "ALTER TABLE definities DROP COLUMN toelichting_proces;")

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert any("toelichting_proces" in d for d in fout.details)

    def test_ontbrekende_index_is_incompleet(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(pad, "DROP INDEX idx_chunks_bron_type;")

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert any("idx_chunks_bron_type" in d for d in fout.details)

    def test_index_met_juiste_naam_maar_verkeerde_definitie_is_drift(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(
            pad,
            "DROP INDEX idx_definities_begrip_nocase_actief;"
            "CREATE INDEX idx_definities_begrip_nocase_actief ON definities(begrip);",
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("idx_definities_begrip_nocase_actief" in d for d in fout.details)

    def test_trigger_met_juiste_naam_maar_verkeerde_body_is_drift(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(
            pad,
            "DROP TRIGGER log_definitie_changes;"
            "CREATE TRIGGER log_definitie_changes AFTER UPDATE ON definities "
            "FOR EACH ROW BEGIN SELECT 1; END;",
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("log_definitie_changes" in d for d in fout.details)

    def test_view_met_juiste_naam_maar_verkeerde_definitie_is_drift(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(
            pad,
            "DROP VIEW actieve_definities;"
            "CREATE VIEW actieve_definities AS SELECT * FROM definities;",
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("actieve_definities" in d for d in fout.details)

    def test_ontbrekende_foreign_key_is_drift(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(
            pad,
            """
            DROP TABLE definitie_tags;
            CREATE TABLE definitie_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                definitie_id INTEGER NOT NULL,
                tag_naam VARCHAR(100) NOT NULL,
                tag_waarde VARCHAR(255),
                toegevoegd_door VARCHAR(255),
                toegevoegd_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(definitie_id, tag_naam)
            );
            CREATE INDEX idx_tags_definitie_id ON definitie_tags(definitie_id);
            CREATE INDEX idx_tags_naam ON definitie_tags(tag_naam);
            """,
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definitie_tags" in d and "definities" in d for d in fout.details)

    def test_kolom_met_verkeerde_affiniteit_is_drift(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(
            pad,
            """
            DROP TABLE externe_bronnen;
            CREATE TABLE externe_bronnen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bron_naam VARCHAR(255) NOT NULL UNIQUE,
                bron_type VARCHAR(50) NOT NULL,
                bron_url VARCHAR(500),
                configuratie TEXT,
                api_key_encrypted VARCHAR(500),
                gebruikersnaam VARCHAR(255),
                actief TEXT NOT NULL DEFAULT 'ja',
                laatste_sync TIMESTAMP,
                laatste_sync_status VARCHAR(50),
                aangemaakt_op TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                aangemaakt_door VARCHAR(255)
            );
            """,
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("externe_bronnen" in d and "actief" in d for d in fout.details)


def _opslagklassen(declaratie: str | None) -> tuple[str, ...]:
    """De opslagklassen die echte SQLite aan 1, '1' en 1.0 geeft in ``declaratie``.

    Dit is het enige gezaghebbende antwoord op "welke affiniteit past SQLite
    werkelijk toe": de affiniteitsregels zijn niet los waarneembaar, hun
    conversiegedrag wel.
    """
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            "CREATE TABLE t(x)"
            if declaratie is None
            else f"CREATE TABLE t(x {declaratie})"
        )
        conn.executemany("INSERT INTO t VALUES (?)", [(1,), ("1",), (1.0,)])
        return tuple(rij[0] for rij in conn.execute("SELECT typeof(x) FROM t"))
    finally:
        conn.close()


# INTEGER- en NUMERIC-affiniteit zijn in SQLite niet los waarneembaar (datatype3
# §3.1); de overige groepen wel. Deze afbeelding koppelt de helperuitkomst aan
# de waarneming van `_opslagklassen`.
_WAARNEEMBAAR = {
    ("integer", "integer", "integer"): ("INTEGER", "NUMERIC"),
    ("real", "real", "real"): ("REAL",),
    ("text", "text", "text"): ("TEXT",),
    ("integer", "text", "real"): ("BLOB",),
}


class TestAffiniteitsclassificatie:
    """`column_affinity` moet dezelfde affiniteit geven als echte SQLite.

    SQLite bepaalt de affiniteit met `sqlite3AffinityType`, dat — net als de
    identifiervergelijking — uitsluitend ASCII vouwt. Python `str.upper()`
    trekt niet-ASCII de keywords in en klopte daardoor niet: het geldige
    REAL-type `FLOATING POıNT` (dotloze ı, U+0131) werd `FLOATING POINT`
    en dus INTEGER (Codex-review 6, rootprobe `probe-unicode-affinity`). De
    ligatuur `ﬂ` (U+FB02) is dezelfde oorzaak in de andere richting:
    `ﬂOAT` heeft in SQLite géén REAL-affiniteit, maar `.upper()` maakte er
    `FLOAT` van. Die classificatie stuurt zowel de startupdrift-controle als de
    rebuildgrens, dus een fout hier verandert opgeslagen waarden.
    """

    @pytest.mark.parametrize(
        ("declaratie", "verwacht"),
        [
            pytest.param("INTEGER", "INTEGER", id="integer"),
            pytest.param("INT", "INTEGER", id="int"),
            pytest.param("BIGINT", "INTEGER", id="bigint"),
            pytest.param("int", "INTEGER", id="kleine-letters"),
            pytest.param("InTeGeR", "INTEGER", id="gemengde-letters"),
            pytest.param("VARCHAR(255)", "TEXT", id="varchar"),
            pytest.param("CLOB", "TEXT", id="clob"),
            pytest.param("text", "TEXT", id="text"),
            pytest.param("BLOB", "BLOB", id="blob"),
            pytest.param("", "BLOB", id="leeg"),
            pytest.param(None, "BLOB", id="geen-declaratie"),
            pytest.param("REAL", "REAL", id="real"),
            pytest.param("DOUBLE", "REAL", id="double"),
            pytest.param("FLOAT", "REAL", id="float"),
            pytest.param("FLOATING POINT", "INTEGER", id="floating-point-ascii"),
            pytest.param("floating point", "INTEGER", id="floating-point-klein"),
            pytest.param("DECIMAL(10,5)", "NUMERIC", id="decimal"),
            pytest.param("BOOLEAN", "NUMERIC", id="boolean"),
            pytest.param("DATE", "NUMERIC", id="date"),
            pytest.param("FLOATING POıNT", "REAL", id="floating-point-dotloze-i"),
            pytest.param("ﬂOAT", "NUMERIC", id="fl-ligatuur"),
            pytest.param("ıNTEGER", "NUMERIC", id="integer-dotloze-i"),
        ],
    )
    def test_classificatie_komt_overeen_met_echte_sqlite(self, declaratie, verwacht):
        from database.schema_contract import column_affinity

        klassen = _opslagklassen(declaratie)
        assert klassen in _WAARNEEMBAAR, (declaratie, klassen)
        assert verwacht in _WAARNEEMBAAR[klassen], (declaratie, klassen, verwacht)

        assert column_affinity(declaratie) == verwacht

    @pytest.mark.parametrize(
        ("declaratie", "andere"),
        [
            pytest.param("FLOATING POıNT", "FLOATING POINT", id="dotloze-i"),
            pytest.param("ﬂOAT", "FLOAT", id="fl-ligatuur"),
        ],
    )
    def test_unicode_en_ascii_typenaam_zijn_echt_verschillend(self, declaratie, andere):
        # Discriminator: de twee declaraties slaan dezelfde waarde anders op.
        # Zonder dit verschil zou de test hierboven ook groen zijn met een
        # helper die alles op INTEGER gooit.
        from database.schema_contract import column_affinity

        assert _opslagklassen(declaratie) != _opslagklassen(andere)
        assert column_affinity(declaratie) != column_affinity(andere)


def _profiel_uit_schematekst(pad: Path, *vervangingen: tuple[str, str]) -> Path:
    """Bouw een database uit schema.sql met exact één tekstuele afwijking per paar.

    Het canonieke contract blijft uit het échte bestand komen; alleen de te
    toetsen database wijkt af. Elke vervanging moet werkelijk voorkomen.
    """
    from tests.fixtures.schema_profiles import SCHEMA_SQL_PATH

    tekst = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    for oud, nieuw in vervangingen:
        assert tekst.count(oud) >= 1, f"vervanging niet gevonden: {oud!r}"
        tekst = tekst.replace(oud, nieuw, 1)
    _sql(pad, tekst)
    return pad


class TestFunctioneleDefinitiesWordenBewaakt:
    """Rootprobe (probe-manifest-semantics): drie schema's met een verkeerde
    functionele definitie passeerden het contract. Naam, kolommen en
    affiniteit alleen zijn niet genoeg."""

    def test_omgekeerd_indexpredicaat_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            ("WHERE status != 'archived';", "WHERE status = 'archived';"),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("idx_definities_begrip_nocase_actief" in d for d in fout.details)

    def test_sorteerrichting_van_index_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "CREATE INDEX idx_definities_created_at ON definities(created_at);",
                "CREATE INDEX idx_definities_created_at ON definities(created_at DESC);",
            ),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("idx_definities_created_at" in d for d in fout.details)

    def test_triggerliteral_met_andere_hoofdletters_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            ("THEN 'status_changed'", "THEN 'STATUS_CHANGED'"),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("log_definitie_changes" in d for d in fout.details)

    def test_andere_default_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "status VARCHAR(50) NOT NULL DEFAULT 'draft'",
                "status VARCHAR(50) NOT NULL DEFAULT 'archived'",
            ),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definities.status" in d for d in fout.details)

    def test_weggevallen_not_null_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "wettelijke_basis TEXT NOT NULL DEFAULT '[]'",
                "wettelijke_basis TEXT DEFAULT '[]'",
            ),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definities.wettelijke_basis" in d for d in fout.details)

    def test_gewijzigde_check_constraint_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "'STA',    -- Status (toestand/fase)\n        'OTH'     -- Overig (niet-gecategoriseerd)",
                "'STA'     -- Status (toestand/fase)",
            ),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definities" in d and "check" in d.lower() for d in fout.details)

    def test_andere_on_delete_actie_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE CASCADE,\n    tag_naam",
                "definitie_id INTEGER NOT NULL REFERENCES definities(id) ON DELETE SET NULL,\n    tag_naam",
            ),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definitie_tags" in d and "definities" in d for d in fout.details)

    def test_unique_constraint_met_andere_kolommen_is_drift(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            ("UNIQUE(definitie_id, tag_naam)", "UNIQUE(definitie_id, tag_waarde)"),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definitie_tags" in d for d in fout.details)

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param("id BIGINT PRIMARY KEY", id="bigint"),
            pytest.param("id INT PRIMARY KEY", id="int"),
            pytest.param("id INTEGER PRIMARY KEY DESC", id="desc"),
            pytest.param("id INTEGER PRIMARY KEY", id="zonder-autoincrement"),
        ],
    )
    def test_andere_sleutelsemantiek_dan_integer_primary_key_is_drift(
        self, tmp_path, declaratie
    ):
        # Codex-herreview P1: affiniteit + pk-positie maakte BIGINT PRIMARY KEY
        # gelijk aan INTEGER PRIMARY KEY AUTOINCREMENT, terwijl alleen de
        # laatste een rowid-alias met AUTOINCREMENT is.
        oud = "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db", (oud, f"CREATE TABLE definities (\n    {declaratie},")
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definities.id" in d for d in fout.details)

    @pytest.mark.parametrize(
        ("tabel", "kolom", "oud"),
        [
            pytest.param(
                "definities",
                "version_number",
                "    version_number INTEGER NOT NULL DEFAULT 1,",
                id="definities-version-number",
            ),
            pytest.param(
                "definitie_voorbeelden",
                "voorbeeld_volgorde",
                "    voorbeeld_volgorde INTEGER DEFAULT 1,",
                id="voorbeelden-volgorde",
            ),
        ],
    )
    def test_unicode_typenaam_met_andere_affiniteit_is_drift(
        self, tmp_path, tabel, kolom, oud
    ):
        # Codex-review 6 (P1) / rootprobe `probe-unicode-affinity`: de bron
        # declareert `FLOATING POıNT` (U+0131). Dat is in SQLite REAL, niet
        # INTEGER — de kolom bewaart 1.0 en `/2` levert 0.5. De startupcontrole
        # zag door `str.upper()` INTEGER en meldde geen drift.
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db", (oud, oud.replace("INTEGER", "FLOATING POıNT"))
        )
        conn = sqlite3.connect(str(pad))
        try:
            if tabel == "definitie_voorbeelden":
                conn.execute(
                    "INSERT INTO definitie_voorbeelden "
                    "(definitie_id, voorbeeld_type, voorbeeld_tekst) "
                    "VALUES (1, 'sentence', 'sentinel')"
                )
                conn.commit()
            waargenomen = conn.execute(
                f"SELECT typeof({kolom}), {kolom} / 2 FROM {tabel} LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        # De bron is werkelijk REAL; het canonieke schema is INTEGER.
        assert waargenomen == ("real", 0.5), waargenomen

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any(f"{tabel}.{kolom}" in d for d in fout.details)

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param(
                'id INTEGER PRIMARY KEY CONSTRAINT "autoincrement" CHECK(id > 0)',
                id="gequote-constraintnaam",
            ),
            pytest.param(
                "id INTEGER PRIMARY KEY CHECK(id > 0 OR 'autoincrement' = '')",
                id="literal-in-check",
            ),
            pytest.param(
                "id INTEGER PRIMARY KEY -- autoincrement\n    ",
                id="commentaar",
            ),
        ],
    )
    def test_woord_autoincrement_zonder_sleutelwoord_is_drift(
        self, tmp_path, declaratie
    ):
        # Codex-review 3 (P1): `"autoincrement" in eigen` las een gequote
        # constraintnaam als sleutelwoord; ID 1000 werd daarna als 3 hergebruikt.
        oud = "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db", (oud, f"CREATE TABLE definities (\n    {declaratie},")
        )
        # Functioneel: zonder echt AUTOINCREMENT wordt een verwijderd id hergebruikt.
        conn = sqlite3.connect(str(pad))
        try:
            conn.execute(
                "INSERT INTO definities (id, begrip, definitie, categorie) "
                "VALUES (1000, 't', 't', 'type')"
            )
            conn.execute("DELETE FROM definities WHERE id = 1000")
            cur = conn.execute(
                "INSERT INTO definities (begrip, definitie, categorie) VALUES ('n', 'n', 'type')"
            )
            assert cur.lastrowid < 1000
        finally:
            conn.close()

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definities.id" in d for d in fout.details)

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param("'id' INTEGER PRIMARY KEY AUTOINCREMENT", id="singlequoted"),
            pytest.param(
                '"ID" INTEGER PRIMARY KEY AUTOINCREMENT', id="doublequoted-caps"
            ),
            pytest.param(
                "[id] INTEGER PRIMARY/**/KEY AUTOINCREMENT", id="brackets-commentaar"
            ),
            pytest.param(
                "`id` INTEGER PRIMARY KEY -- k\n    AUTOINCREMENT",
                id="backticks-lijncommentaar",
            ),
        ],
    )
    def test_canonieke_sleutel_in_geldige_quote_en_commentaarvormen_blijft_groen(
        self, tmp_path, declaratie
    ):
        # Codex-review 4: de kolomnaam moet als echt identifier-token worden
        # herkend en commentaar als tokenscheiding, anders wordt een geldige
        # canonieke sleutel ten onrechte drift (of andersom).
        oud = "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db", (oud, f"CREATE TABLE definities (\n    {declaratie},")
        )
        _init(pad)

    @pytest.mark.parametrize(
        "declaratie",
        [
            pytest.param(
                '"id" INTEGER PRIMARY KEY', id="doublequoted-zonder-autoincrement"
            ),
            pytest.param("'id' INTEGER PRIMARY KEY DESC", id="singlequoted-desc"),
        ],
    )
    def test_gequote_sleutel_zonder_canonieke_semantiek_is_drift(
        self, tmp_path, declaratie
    ):
        oud = "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db", (oud, f"CREATE TABLE definities (\n    {declaratie},")
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("definities.id" in d for d in fout.details)

    def test_niet_ascii_identifier_maskeert_geen_canonieke_kolom(self, tmp_path):
        # Codex-review 5 (P1): een schema met uitsluitend "Ketenpartners"
        # (Kelvinteken) passeerde startup omdat Python .lower() er
        # `ketenpartners` van maakte; de echte query faalde daarna.
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            ("    ketenpartners TEXT,", '    "Ketenpartners" TEXT,'),
        )
        conn = sqlite3.connect(str(pad))
        try:
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("SELECT ketenpartners FROM definities")
        finally:
            conn.close()

        fout = _contractfout(pad)

        assert fout.reason == "schema_incomplete"
        assert any("ketenpartners" in d for d in fout.details)

    @pytest.mark.parametrize(
        "kolom",
        [
            pytest.param('"KETENPARTNERS"', id="ascii-caps"),
            pytest.param('"Ketenpartners"', id="ascii-mixed"),
            pytest.param("[ketenPARTNERS]", id="brackets-ascii-mixed"),
        ],
    )
    def test_ascii_casevarianten_van_canonieke_kolom_blijven_groen(
        self, tmp_path, kolom
    ):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db", ("    ketenpartners TEXT,", f"    {kolom} TEXT,")
        )
        _init(pad)

    def test_unicode_casevarianten_zijn_aparte_extra_kolommen(self, tmp_path):
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "    generation_prompt_data TEXT,",
                (
                    '    "Éxtra" TEXT,\n    "éxtra" TEXT COLLATE NOCASE,\n'
                    "    generation_prompt_data TEXT,"
                ),
            ),
        )
        # Twee verschillende extra kolommen: toegestaan, en het contract
        # mag ze niet samenvoegen.
        _init(pad)
        from database.schema_contract import read_contract

        conn = sqlite3.connect(str(pad))
        try:
            kolommen = read_contract(conn).columns["definities"]
        finally:
            conn.close()
        assert "Éxtra" in kolommen and "éxtra" in kolommen

    def test_normalisatie_houdt_commentaar_als_tokenscheiding(self):
        from database.schema_contract import normalize_sql

        assert (
            normalize_sql("UNIQUE ON/**/CONFLICT IGNORE") == "unique on conflict ignore"
        )
        assert (
            normalize_sql("UNIQUE ON -- x\n CONFLICT IGNORE")
            == "unique on conflict ignore"
        )
        assert normalize_sql("a/* c */,b") == "a,b"
        assert normalize_sql("x 'ON/**/CONFLICT'") == "x 'ON/**/CONFLICT'"

    def test_canoniek_autoincrement_met_extra_constraintnaam_blijft_groen(
        self, tmp_path
    ):
        oud = "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                oud,
                (
                    "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT "
                    'CONSTRAINT "geen_sleutelwoord" CHECK(id > 0),'
                ),
            ),
        )
        # Extra CHECK is een extra object: toegestaan; de sleutel is canoniek.
        _init(pad)

    def test_bigint_primary_key_geeft_echt_geen_rowid_alias(self, tmp_path):
        # De motivatie, functioneel: een gewone INSERT levert dan id NULL.
        oud = "CREATE TABLE definities (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        pad = _profiel_uit_schematekst(
            tmp_path / "bigint.db",
            (oud, "CREATE TABLE definities (\n    id BIGINT PRIMARY KEY,"),
        )
        conn = sqlite3.connect(str(pad))
        try:
            conn.execute(
                "INSERT INTO definities (begrip, definitie, categorie) "
                "VALUES ('probe', 'probe', 'type')"
            )
            assert (
                conn.execute(
                    "SELECT id FROM definities WHERE begrip = 'probe'"
                ).fetchone()[0]
                is None
            )
        finally:
            conn.close()

    def test_check_tekst_in_een_literal_is_geen_constraint(self, tmp_path):
        # Rootprobe (probe-check-literal): de echte status-CHECK weg en de
        # canonieke CHECK-tekst als DEFAULT-literal van een extra kolom.
        # `find('check(')` zonder quotecontext telde die literal als
        # constraint; een INSERT met status INVALID slaagde.
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            (
                "CHECK (status IN ('imported', 'draft', 'review', 'established', 'archived'))",
                "",
            ),
            (
                "    generation_prompt_data TEXT,",
                (
                    "    fake_constraint TEXT DEFAULT \"check(status in('imported','draft',"
                    "'review','established','archived'))\",\n    generation_prompt_data TEXT,"
                ),
            ),
        )

        fout = _contractfout(pad)

        assert fout.reason == "schema_drift"
        assert any("check-constraint definities" in d for d in fout.details)

    def test_check_expressions_negeert_literals_en_commentaar(self):
        from database.schema_contract import check_expressions

        ddl = (
            "CREATE TABLE t (\n"
            "  a TEXT DEFAULT \"check(a in('x'))\", -- check(a in('commentaar'))\n"
            "  b TEXT DEFAULT 'CHECK (b > 0)',\n"
            "  c INTEGER CHECK (c > 0)\n"
            ")"
        )
        assert check_expressions(ddl) == frozenset({"c>0"})

    def test_normalisatie_laat_literal_inhoud_staan(self):
        # Rootprobe (probe-normalizer-literals): 'if not exists' bínnen een
        # literal werd weggehaald door een globale replace op de eindstring.
        from database.schema_contract import normalize_sql

        met = normalize_sql("CREATE VIEW p AS SELECT 'if not exists sentinel' AS value")
        zonder = normalize_sql("CREATE VIEW p AS SELECT 'sentinel' AS value")
        assert met != zonder
        assert "'if not exists sentinel'" in met

        # De tegenhanger: buiten quotes verdwijnt IF NOT EXISTS wél.
        assert normalize_sql("CREATE INDEX IF NOT EXISTS x ON t(a)") == normalize_sql(
            "create index x on t(a)"
        )
        assert normalize_sql("CREATE INDEX IF  NOT\nEXISTS x ON t(a)") == normalize_sql(
            "create index x on t(a)"
        )

    def test_alleen_witruimte_en_commentaar_verschil_passeert(self, tmp_path):
        # De tegenhanger: cosmetische verschillen buiten quotes mogen niet als
        # drift tellen, anders keurt het contract de DEF-672-rebuild af.
        pad = _profiel_uit_schematekst(
            tmp_path / "v3.db",
            ("THEN 'status_changed'", "THEN    'status_changed' -- extra"),
            ("WHERE status != 'archived';", "WHERE  status  !=  'archived' ;"),
        )

        _init(pad)


class TestBestaandeExtraObjectenBlijvenToegestaan:
    def test_extra_gebruikersobjecten_en_kolommen_passeren(self, tmp_path):
        pad = bouw_profiel(tmp_path / "v3.db", 3)
        _sql(
            pad,
            """
            CREATE TABLE gebruiker_extra (id INTEGER PRIMARY KEY, notitie TEXT);
            ALTER TABLE definities ADD COLUMN extra_kolom TEXT;
            CREATE INDEX idx_extra_kolom ON definities(extra_kolom);
            CREATE INDEX idx_synonyms_text_ci ON definitie_voorbeelden(
                voorbeeld_type, actief, voorbeeld_tekst COLLATE NOCASE);
            CREATE TABLE definitie_drafts (
                definitie_id INTEGER PRIMARY KEY REFERENCES definities(id),
                draft_content TEXT NOT NULL,
                saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                saved_by TEXT
            );
            """,
        )
        voor = _objecten(pad)

        _init(pad)

        assert _objecten(pad) == voor

    def test_door_de_legacy_route_herbouwde_tabel_passeert(self, tmp_path):
        # De rebuild uit DEF-672 schrijft `definities` met een andere
        # kolomvolgorde en DDL-tekst; het contract toetst structuur, geen tekst.
        from database.migrate_database import migrate_database

        pad = tmp_path / "herbouwd.db"
        _init(pad)
        _sql(pad, "ALTER TABLE definities ADD COLUMN voorkeursterm_is_begrip INTEGER;")
        assert migrate_database(str(pad)) is True

        _init(pad)
