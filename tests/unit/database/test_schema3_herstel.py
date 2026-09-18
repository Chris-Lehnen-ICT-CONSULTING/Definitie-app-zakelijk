"""Tests voor de schema-3-herstelroute (DEF-751, ESS-02 lokale activering).

Synthetische, minimale reproductie van de gebruikersdatabase: een profiel-3-
database waarvan ``definitie_geschiedenis``, ``definitie_tags`` en
``import_export_logs`` de oude vorm hebben (geen FK/CHECK, TEXT-tijdstempels),
waarin ``externe_bronnen``, vier indexen, twee triggers en drie views
ontbreken, en waarin een deel van de geschiedenis naar een niet-bestaande
definitie verwijst.

RED: de bestaande v8- en legacy-routes weigeren die bron (reproductie).
GREEN: de herstelroute maakt uit de read-only bron een nieuw doel op versie 4
zonder verlies; de verweesde geschiedenis staat volledig en herleidbaar in
de bewaartabel. Eigen fixture-DDL, geen import uit de module (geen spiegel).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

import database.migrations.schema3_herstel as herstel
import database.migrations.v8_migration as v8
from database.migrate_database import migrate_database
from database.schema_contract import SchemaContractError, assert_startup_contract
from database.sqlite_backup import BackupError
from tests.fixtures.schema_profiles import (
    bouw_profiel,
    lees_alles,
    schema_versies,
    zaai_sentinels,
)

pytestmark = [pytest.mark.unit]

BEWAARTABEL = "definitie_geschiedenis_verweesd"

# De legacy-vorm zoals gemeten in de gebruikersdatabase (eigen tekst).
_LEGACY_DDL = """
DROP TABLE definitie_geschiedenis;
DROP TABLE definitie_tags;
DROP TABLE import_export_logs;
DROP TABLE externe_bronnen;
CREATE TABLE definitie_geschiedenis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    begrip TEXT NOT NULL,
    definitie_oude_waarde TEXT,
    definitie_nieuwe_waarde TEXT,
    wijziging_type TEXT NOT NULL,
    wijziging_reden TEXT,
    gewijzigd_door TEXT,
    gewijzigd_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context_snapshot TEXT
);
CREATE INDEX idx_geschiedenis_definitie_id ON definitie_geschiedenis(definitie_id);
CREATE INDEX idx_geschiedenis_datum ON definitie_geschiedenis(gewijzigd_op);
CREATE TABLE definitie_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    definitie_id INTEGER NOT NULL,
    tag_naam TEXT NOT NULL,
    tag_waarde TEXT,
    toegevoegd_door TEXT,
    toegevoegd_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(definitie_id, tag_naam)
);
CREATE INDEX idx_tags_definitie_id ON definitie_tags(definitie_id);
CREATE INDEX idx_tags_naam ON definitie_tags(tag_naam);
CREATE TABLE import_export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operatie_type TEXT NOT NULL,
    bron_bestemming TEXT NOT NULL,
    aantal_verwerkt INTEGER NOT NULL DEFAULT 0,
    aantal_succesvol INTEGER NOT NULL DEFAULT 0,
    aantal_gefaald INTEGER NOT NULL DEFAULT 0,
    bestand_pad TEXT,
    formaat TEXT,
    fouten_details TEXT,
    gestart_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    voltooid_op TEXT,
    gestart_door TEXT,
    status TEXT NOT NULL DEFAULT 'running'
);
CREATE INDEX idx_logs_operatie_type ON import_export_logs(operatie_type);
CREATE INDEX idx_logs_datum ON import_export_logs(gestart_op);
DROP TRIGGER update_definities_timestamp;
DROP TRIGGER log_definitie_changes;
DROP VIEW actieve_definities;
DROP VIEW vastgestelde_definities;
DROP VIEW definitie_statistieken;
DROP INDEX idx_definities_begrip;
DROP INDEX idx_definities_status;
DROP INDEX idx_definities_begrip_nocase_actief;
DROP INDEX idx_definities_datum_voorstel;
"""

# Diverse inhoud: gekoppelde én verweesde geschiedenis (ids 5 en 7 bestaan
# niet), NULL-velden, JSON, een tag, logs met beide operatietypen, en een
# autoincrement-teller boven het hoogste id (eerder verwijderde rijen).
_LEGACY_DATA = """
INSERT INTO definities (begrip, definitie, categorie, organisatorische_context)
    VALUES ('tweede', 'tweede kern', 'proces', '["OM"]');
INSERT INTO definitie_geschiedenis
    (id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
     wijziging_type, wijziging_reden, gewijzigd_door, gewijzigd_op, context_snapshot)
VALUES
    (10, 1, 'sentinelbegrip', NULL, 'kern-1', 'created', NULL, 'u1',
     '2025-01-02 03:04:05', '{"oude_status": "draft"}'),
    (11, 1, 'sentinelbegrip', 'kern-1', 'kern-2', 'updated', 'reden-11', NULL,
     '2025-01-03 03:04:05', NULL),
    (12, 2, 'tweede', NULL, 'tweede kern', 'created', NULL, 'u2',
     '2025-02-01 00:00:00', '{}'),
    (20, 5, 'verdwenen-5', 'oud-5', 'nieuw-5', 'updated', 'reden-20', 'u9',
     '2024-12-31 23:59:59', '{"oude_status": "review"}'),
    (21, 5, 'verdwenen-5', NULL, NULL, 'archived', NULL, NULL,
     '2025-01-01 00:00:00', NULL),
    (22, 7, 'verdwenen-7', 'x', 'y', 'status_changed', 'reden-22', 'u7',
     '2025-03-03 03:03:03', '{"nieuwe_status": "established"}');
UPDATE sqlite_sequence SET seq = 500 WHERE name = 'definitie_geschiedenis';
INSERT INTO definitie_tags (definitie_id, tag_naam, tag_waarde, toegevoegd_door, toegevoegd_op)
    VALUES (1, 'sentinel', 'ja', 'admin', '2025-01-01 10:00:00'),
           (2, 'thema', NULL, NULL, '2025-01-01 11:00:00');
INSERT INTO import_export_logs
    (operatie_type, bron_bestemming, aantal_verwerkt, aantal_succesvol, aantal_gefaald,
     bestand_pad, formaat, fouten_details, gestart_op, voltooid_op, gestart_door, status)
VALUES
    ('import', 'bestand.json', 3, 2, 1, '/tmp/x.json', 'json', '["fout"]',
     '2025-05-05 05:05:05', '2025-05-05 05:06:05', 'u1', 'completed'),
    ('export', 'uit.csv', 0, 0, 0, NULL, 'csv', NULL,
     '2025-06-06 06:06:06', NULL, NULL, 'running');
"""


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


def _bestandshash(pad: Path) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


def _objecten(pad: Path) -> set[tuple[str, str]]:
    return {
        (t, n)
        for t, n in _rijen(
            pad, "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        )
    }


GESCHIEDENIS_KOLOMMEN = (
    "id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde, "
    "wijziging_type, wijziging_reden, gewijzigd_door, gewijzigd_op, context_snapshot"
)


@pytest.fixture
def legacy_bron(tmp_path: Path) -> Path:
    """Minimale synthetische variant van de gebruikersdatabase (profiel 3, legacy)."""
    bronmap = tmp_path / "bron"
    bronmap.mkdir()
    pad = bouw_profiel(bronmap / "definities.db", 3)
    zaai_sentinels(pad)
    _sql(pad, _LEGACY_DDL)
    _sql(pad, _LEGACY_DATA)
    assert schema_versies(pad) == [1, 2, 3]
    return pad


@pytest.fixture
def doel(tmp_path: Path) -> Path:
    (tmp_path / "doel").mkdir()
    return tmp_path / "doel" / "definities-v4.db"


def _extra_bestanden(doel: Path) -> list[str]:
    return sorted(p.name for p in doel.parent.iterdir() if p != doel)


# ---------------------------------------------------------------------------
# RED: reproductie van de blokkade met de bestaande routes
# ---------------------------------------------------------------------------
class TestReproductie:
    def test_bestaande_v8_weigert_de_legacy_bron(self, legacy_bron: Path):
        voor = lees_alles(legacy_bron)
        assert v8.run_migration(legacy_bron) is False
        assert lees_alles(legacy_bron) == voor
        assert schema_versies(legacy_bron) == [1, 2, 3]

    def test_bestaande_legacy_route_weigert_de_legacy_bron(self, legacy_bron: Path):
        voor = lees_alles(legacy_bron)
        assert migrate_database(str(legacy_bron)) is False
        assert lees_alles(legacy_bron) == voor

    def test_zonder_herstelstap_weigert_ook_de_nieuwe_route(
        self, legacy_bron: Path, doel: Path
    ):
        """Mutatie: de herstelstap is de noodzakelijke stap, niet de kopie."""
        with (
            patch.object(herstel, "herstel_schema3", lambda conn, rapport: None),
            pytest.raises(SchemaContractError) as excinfo,
        ):
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_v8_mislukt"
        assert not doel.exists()
        assert _extra_bestanden(doel) == []


# ---------------------------------------------------------------------------
# GREEN: happy path
# ---------------------------------------------------------------------------
class TestGeslaagdHerstel:
    def test_nieuw_doel_is_volledig_v4_en_verliesvrij(
        self, legacy_bron: Path, doel: Path
    ):
        bron_bytes = _bestandshash(legacy_bron)
        bron_inhoud = lees_alles(legacy_bron)
        bron_objecten = _objecten(legacy_bron)

        rapport = herstel.herstel_naar_nieuw_doel(legacy_bron, doel)

        # Bron byte-voor-byte onaangeroerd; doel gepubliceerd, werkmap weg.
        assert _bestandshash(legacy_bron) == bron_bytes
        assert doel.exists()
        assert _extra_bestanden(doel) == []
        assert not legacy_bron.with_name("backups").exists()

        # Volledig schema 4: het strikte startupcontract, ongewijzigd.
        conn = sqlite3.connect(str(doel))
        try:
            assert_startup_contract(conn)
            assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
            assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        finally:
            conn.close()
        assert schema_versies(doel) == [1, 2, 3, 4]
        assert rapport.contract_problemen == []
        assert rapport.integrity_check == "ok"
        assert rapport.foreign_key_check_schendingen == 0

        # Alle bronobjecten bestaan nog (plus de aangevulde canonieke).
        assert bron_objecten <= _objecten(doel)
        assert ("table", "externe_bronnen") in _objecten(doel)
        assert ("trigger", "log_definitie_changes") in _objecten(doel)
        assert ("view", "definitie_statistieken") in _objecten(doel)
        assert ("index", "idx_definities_begrip_nocase_actief") in _objecten(doel)

        # Alle overige tabellen exact gelijk: elke bronkolom, elke rij, elke
        # waarde (kolomvolgorde is geen contract: de v8-rebuild van
        # `definities` volgt de canonieke DDL).
        doel_inhoud = lees_alles(doel)
        for tabel, (kolommen, rijen) in bron_inhoud.items():
            if tabel in ("definitie_geschiedenis", "schema_version"):
                continue
            doel_kolommen, doel_rijen = doel_inhoud[tabel]
            assert set(kolommen) <= set(doel_kolommen), tabel
            posities = [doel_kolommen.index(k) for k in kolommen]
            assert [
                tuple(rij[p] for p in posities) for rij in doel_rijen
            ] == rijen, tabel
        assert sorted(rapport.tabellen) == sorted([*bron_inhoud, BEWAARTABEL])
        assert all(v.gelijk for v in rapport.tabellen.values())

    def test_geschiedenis_exact_gesplitst_in_gekoppeld_en_bewaard(
        self, legacy_bron: Path, doel: Path
    ):
        alle = _rijen(
            legacy_bron,
            f"SELECT {GESCHIEDENIS_KOLOMMEN} FROM definitie_geschiedenis ORDER BY id",
        )
        verweesd = [rij for rij in alle if rij[1] in (5, 7)]
        gekoppeld = [rij for rij in alle if rij[1] not in (5, 7)]
        # De sentinelrij verdween met de DROP in de fixture: zes eigen rijen.
        assert len(alle) == 6 and len(verweesd) == 3

        rapport = herstel.herstel_naar_nieuw_doel(legacy_bron, doel)

        assert (rapport.geschiedenis_totaal, rapport.geschiedenis_gekoppeld) == (6, 3)
        assert rapport.geschiedenis_verweesd == 3
        assert (
            _rijen(
                doel,
                f"SELECT {GESCHIEDENIS_KOLOMMEN} FROM definitie_geschiedenis ORDER BY id",
            )
            == gekoppeld
        )
        assert (
            _rijen(
                doel, f"SELECT {GESCHIEDENIS_KOLOMMEN} FROM {BEWAARTABEL} ORDER BY id"
            )
            == verweesd
        )
        # Herleidbare reden op elke bewaarde rij; geen verzonnen definities.
        assert _rijen(
            doel,
            f"SELECT DISTINCT bewaar_reden, bewaard_door FROM {BEWAARTABEL}",
        ) == [("definitie_ontbreekt", "DEF-751 schema3_herstel")]
        assert _rijen(
            doel, f"SELECT COUNT(*) FROM {BEWAARTABEL} WHERE bewaard_op IS NULL"
        ) == [(0,)]
        assert _rijen(doel, "SELECT id FROM definities WHERE id IN (5, 7)") == []
        # Geen FK op de bewaartabel: de oorspronkelijke verwijzing blijft staan.
        assert _rijen(doel, f"PRAGMA foreign_key_list({BEWAARTABEL})") == []
        # Bewaartabel draagt exact de brondeclaraties (TEXT, NOT NULL, DEFAULT).
        kolommen = {
            rij[1]: (rij[2], rij[3], rij[4])
            for rij in _rijen(doel, f"PRAGMA table_info({BEWAARTABEL})")
        }
        assert kolommen["gewijzigd_op"] == ("TEXT", 1, "CURRENT_TIMESTAMP")
        assert kolommen["definitie_id"] == ("INTEGER", 1, None)

    def test_tellers_niet_teruggezet_en_constraints_actief(
        self, legacy_bron: Path, doel: Path
    ):
        bron_seq = dict(_rijen(legacy_bron, "SELECT name, seq FROM sqlite_sequence"))
        herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        seq = dict(_rijen(doel, "SELECT name, seq FROM sqlite_sequence"))
        assert seq["definitie_geschiedenis"] == 500
        assert seq["schema_version"] == bron_seq["schema_version"] + 1
        assert {k: v for k, v in seq.items() if k != "schema_version"} == {
            k: v for k, v in bron_seq.items() if k != "schema_version"
        }
        conn = sqlite3.connect(str(doel))
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO definitie_geschiedenis (definitie_id, begrip, wijziging_type) "
                    "VALUES (999, 'x', 'created')"
                )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO definitie_geschiedenis (definitie_id, begrip, wijziging_type) "
                    "VALUES (1, 'x', 'onbekend')"
                )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO import_export_logs (operatie_type, bron_bestemming) "
                    "VALUES ('verkeerd', 'x')"
                )
            # De teller geeft een nieuw id boven de oude high-water-mark.
            cur = conn.execute(
                "INSERT INTO definitie_geschiedenis (definitie_id, begrip, wijziging_type) "
                "VALUES (1, 'x', 'created')"
            )
            assert cur.lastrowid == 501
            conn.rollback()
        finally:
            conn.close()

    def test_rapport_bevat_alleen_metadata(
        self, legacy_bron: Path, doel: Path, tmp_path: Path
    ):
        rapport_pad = tmp_path / "rapport.json"
        herstel.herstel_naar_nieuw_doel(legacy_bron, doel, rapport_pad=rapport_pad)
        tekst = rapport_pad.read_text(encoding="utf-8")
        data = json.loads(tekst)
        assert data["bronversie"] == 3 and data["doelversie"] == 4
        assert data["schema_version_doel"] == [1, 2, 3, 4]
        assert data["tabellen"][BEWAARTABEL]["gelijk"] is True
        assert data["tabellen"][BEWAARTABEL]["doel_aantal"] == 3
        assert "definitie_geschiedenis" in data["herbouwde_tabellen"]
        assert "table externe_bronnen" in data["aangevulde_objecten"]
        # Geen rijinhoud, geen paden.
        for verboden in ("sentinelbegrip", "verdwenen-5", "reden-20", str(tmp_path)):
            assert verboden not in tekst

    def test_bron_die_al_canoniek_v3_is_wordt_alleen_naar_v4_gebracht(
        self, tmp_path: Path, doel: Path
    ):
        bron = bouw_profiel(tmp_path / "canoniek.db", 3)
        zaai_sentinels(bron)
        totaal = _rijen(bron, "SELECT COUNT(*) FROM definitie_geschiedenis")[0][0]
        rapport = herstel.herstel_naar_nieuw_doel(bron, doel)
        assert rapport.herbouwde_tabellen == []
        assert rapport.aangevulde_objecten == []
        assert rapport.nieuwe_tabellen == []
        assert (rapport.geschiedenis_gekoppeld, rapport.geschiedenis_verweesd) == (
            totaal,
            0,
        )
        assert schema_versies(doel) == [1, 2, 3, 4]
        assert (BEWAARTABEL not in _objecten(doel)) and doel.exists()

    def test_cli_publiceert_en_meldt_alleen_aantallen(
        self, legacy_bron: Path, doel: Path, tmp_path: Path
    ):
        rapport_pad = tmp_path / "cli-rapport.json"
        assert (
            herstel.main([str(legacy_bron), str(doel), "--rapport", str(rapport_pad)])
            == 0
        )
        assert doel.exists() and rapport_pad.exists()
        with pytest.raises(SystemExit) as excinfo:
            herstel.main([str(legacy_bron), str(doel)])  # doel bestaat nu
        assert excinfo.value.code == 1


# ---------------------------------------------------------------------------
# Bronbehoud en doelweigering
# ---------------------------------------------------------------------------
class TestBronbehoudEnDoelweigering:
    def test_read_only_bron_volstaat(self, legacy_bron: Path, doel: Path):
        legacy_bron.chmod(0o444)
        try:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        finally:
            legacy_bron.chmod(0o644)
        assert doel.exists()

    def test_bestaand_doel_wordt_geweigerd_en_niet_overschreven(
        self, legacy_bron: Path, doel: Path
    ):
        doel.write_bytes(b"bestaand")
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_doel_ongeldig"
        assert excinfo.value.details == ("destination_exists",)
        assert doel.read_bytes() == b"bestaand"
        assert _extra_bestanden(doel) == []

    def test_bron_gelijk_aan_doel_wordt_geweigerd(self, legacy_bron: Path):
        voor = _bestandshash(legacy_bron)
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, legacy_bron)
        assert excinfo.value.details == ("destination_exists",)
        assert _bestandshash(legacy_bron) == voor

    def test_bron_via_symlink_wordt_geweigerd(
        self, legacy_bron: Path, doel: Path, tmp_path: Path
    ):
        link = tmp_path / "link.db"
        link.symlink_to(legacy_bron)
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(link, doel)
        assert excinfo.value.reason == "herstel_kopie_geweigerd"
        assert excinfo.value.details == ("source_symlink",)
        assert not doel.exists() and _extra_bestanden(doel) == []

    def test_doel_via_symlinkmap_wordt_geweigerd(
        self, legacy_bron: Path, tmp_path: Path
    ):
        echte_map = tmp_path / "echt"
        echte_map.mkdir()
        (tmp_path / "alias").symlink_to(echte_map)
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, tmp_path / "alias" / "x.db")
        assert excinfo.value.details == ("destination_symlink",)
        assert list(echte_map.iterdir()) == []

    def test_bestaand_rapport_wordt_niet_overschreven(
        self, legacy_bron: Path, doel: Path, tmp_path: Path
    ):
        rapport = tmp_path / "rapport.json"
        rapport.write_text("{}")
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel, rapport_pad=rapport)
        assert excinfo.value.reason == "herstel_rapport_ongeldig"
        assert rapport.read_text() == "{}"
        assert not doel.exists() and _extra_bestanden(doel) == []

    def test_cli_meldt_bij_rauwe_fout_alleen_de_foutklasse(
        self, legacy_bron: Path, doel: Path, capsys: pytest.CaptureFixture[str]
    ):
        with (
            patch.object(
                herstel,
                "herstel_schema3",
                side_effect=sqlite3.OperationalError(f"geheim pad {legacy_bron}"),
            ),
            pytest.raises(SystemExit) as excinfo,
        ):
            herstel.main([str(legacy_bron), str(doel)])
        assert excinfo.value.code == 1
        uitvoer = capsys.readouterr().err
        assert "OperationalError" in uitvoer and str(legacy_bron) not in uitvoer
        assert not doel.exists()

    def test_ontbrekende_bron_wordt_geweigerd(self, tmp_path: Path, doel: Path):
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(tmp_path / "nee.db", doel)
        assert excinfo.value.details == ("source_missing",)
        assert _extra_bestanden(doel) == []


# ---------------------------------------------------------------------------
# Fouten halverwege: geen (gedeeltelijk) doel, geen resten
# ---------------------------------------------------------------------------
class TestFoutenLatenGeenDoelAchter:
    def test_v8_die_faalt(self, legacy_bron: Path, doel: Path):
        voor = _bestandshash(legacy_bron)
        with (
            patch.object(herstel, "v8_run_migration", return_value=False),
            pytest.raises(SchemaContractError) as excinfo,
        ):
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_v8_mislukt"
        assert not doel.exists() and _extra_bestanden(doel) == []
        assert _bestandshash(legacy_bron) == voor

    def test_eindcontrole_die_faalt_publiceert_niet(
        self, legacy_bron: Path, doel: Path
    ):
        with (
            patch.object(
                herstel, "verify_target_contract", return_value=["afwijkend: test"]
            ),
            pytest.raises(SchemaContractError) as excinfo,
        ):
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "migration_target_contract_failed"
        assert not doel.exists() and _extra_bestanden(doel) == []

    def test_gegevensvergelijking_die_faalt_publiceert_niet(
        self, legacy_bron: Path, doel: Path
    ):
        with (
            patch.object(herstel, "vergelijk_bron_en_doel", return_value=["x"]),
            pytest.raises(SchemaContractError) as excinfo,
        ):
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_gegevensvergelijking_mislukt"
        assert not doel.exists() and _extra_bestanden(doel) == []

    def test_publicatie_die_faalt_laat_geen_resten(self, legacy_bron: Path, doel: Path):
        def _weiger(_staging: Path, _doel: Path) -> None:
            raise BackupError("destination_exists")

        with (
            patch.object(herstel, "publish_staged_file", _weiger),
            pytest.raises(SchemaContractError) as excinfo,
        ):
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_publicatie_mislukt"
        assert not doel.exists() and _extra_bestanden(doel) == []

    def test_fout_in_de_hersteltransactie_rolt_de_kopie_terug(
        self, legacy_bron: Path, doel: Path
    ):
        """De v8-stap ziet dan een onveranderde (legacy) kopie en weigert."""
        with (
            patch.object(
                herstel,
                "_ensure_definities_indexes",
                side_effect=sqlite3.OperationalError("boem"),
            ),
            pytest.raises(sqlite3.OperationalError),
        ):
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert not doel.exists() and _extra_bestanden(doel) == []


# ---------------------------------------------------------------------------
# Onbekende varianten en ongeldige gegevens: weigeren, niet aanpassen
# ---------------------------------------------------------------------------
class TestOnbekendeVariantenWordenGeweigerd:
    @pytest.mark.parametrize(
        "mutatie",
        [
            "ALTER TABLE definitie_geschiedenis ADD COLUMN extra_kolom TEXT",
            "ALTER TABLE import_export_logs ADD COLUMN extra INTEGER NOT NULL DEFAULT 1",
            (
                "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, definitie_id INTEGER "
                "NOT NULL, tag_naam TEXT NOT NULL CHECK (tag_naam <> ''), tag_waarde TEXT, "
                "toegevoegd_door TEXT, toegevoegd_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "UNIQUE(definitie_id, tag_naam)); DROP TABLE definitie_tags; "
                "ALTER TABLE t RENAME TO definitie_tags"
            ),
            (
                "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, definitie_id INTEGER "
                "NOT NULL, tag_naam TEXT NOT NULL, tag_waarde TEXT, toegevoegd_door TEXT, "
                "toegevoegd_op TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP); "
                "DROP TABLE definitie_tags; ALTER TABLE t RENAME TO definitie_tags"
            ),
        ],
        ids=[
            "extra-kolom",
            "extra-kolom-met-default",
            "extra-check",
            "unique-ontbreekt",
        ],
    )
    def test_afwijkende_tabelvorm(self, legacy_bron: Path, doel: Path, mutatie: str):
        _sql(legacy_bron, mutatie + ";")
        voor = _bestandshash(legacy_bron)
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_onbekende_variant"
        assert not doel.exists() and _extra_bestanden(doel) == []
        assert _bestandshash(legacy_bron) == voor

    def test_extra_gebruikersindex_blijft_behouden(self, legacy_bron: Path, doel: Path):
        _sql(
            legacy_bron,
            "CREATE INDEX idx_eigen_geschiedenis ON definitie_geschiedenis(gewijzigd_door);",
        )
        herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert ("index", "idx_eigen_geschiedenis") in _objecten(doel)

    def test_bron_op_andere_versie_wordt_geweigerd(self, tmp_path: Path, doel: Path):
        bron = bouw_profiel(tmp_path / "v4.db", 4)
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(bron, doel)
        assert excinfo.value.reason == "herstel_precondition_failed"
        assert not doel.exists() and _extra_bestanden(doel) == []


class TestOngeldigeGegevensWordenGeweigerd:
    def test_ongeldig_wijziging_type_op_gekoppelde_rij(
        self, legacy_bron: Path, doel: Path
    ):
        _sql(
            legacy_bron,
            "UPDATE definitie_geschiedenis SET wijziging_type = 'raar' WHERE id = 11;",
        )
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_ongeldige_waarden"
        assert "definitie_geschiedenis" in excinfo.value.details[0]
        assert "raar" not in str(excinfo.value)
        assert not doel.exists() and _extra_bestanden(doel) == []

    def test_ongeldig_wijziging_type_op_verweesde_rij_blijft_letterlijk_bewaard(
        self, legacy_bron: Path, doel: Path
    ):
        _sql(
            legacy_bron,
            "UPDATE definitie_geschiedenis SET wijziging_type = 'raar' WHERE id = 21;",
        )
        herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert _rijen(
            doel, f"SELECT wijziging_type FROM {BEWAARTABEL} WHERE id = 21"
        ) == [("raar",)]

    @pytest.mark.parametrize(
        "mutatie",
        [
            "UPDATE import_export_logs SET status = 'bezig' WHERE id = 1",
            "UPDATE import_export_logs SET operatie_type = 'sync' WHERE id = 2",
        ],
        ids=["status", "operatie_type"],
    )
    def test_ongeldige_logwaarden(self, legacy_bron: Path, doel: Path, mutatie: str):
        _sql(legacy_bron, mutatie + ";")
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_ongeldige_waarden"
        assert not doel.exists()

    def test_verweesde_tag_wordt_geweigerd(self, legacy_bron: Path, doel: Path):
        _sql(
            legacy_bron,
            "INSERT INTO definitie_tags (definitie_id, tag_naam) VALUES (999, 'los');",
        )
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_ongeldige_waarden"
        assert excinfo.value.details == ("definitie_tags: 1 rij(en) zonder definitie",)
        assert not doel.exists()

    @pytest.mark.parametrize(
        ("tabel", "kolom", "rij"),
        [
            ("definitie_geschiedenis", "gewijzigd_op", 10),
            ("import_export_logs", "voltooid_op", 1),
            ("definitie_tags", "toegevoegd_op", 1),
        ],
        ids=["geschiedenis", "logs", "tags"],
    )
    def test_tijdstempel_die_door_affiniteit_zou_veranderen(
        self, legacy_bron: Path, doel: Path, tabel: str, kolom: str, rij: int
    ):
        """``'20250101'`` is tekst in de bron; NUMERIC-affiniteit zou er een
        integer van maken. Dat is een waardeverandering en wordt geweigerd."""
        _sql(legacy_bron, f"UPDATE {tabel} SET {kolom} = '20250101' WHERE id = {rij};")
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert excinfo.value.reason == "herstel_waarden_gewijzigd"
        assert excinfo.value.details == (f"{tabel}.{kolom}: 1 rij(en)",)
        assert not doel.exists()

    def test_verweesde_rij_met_numerieke_tekst_blijft_tekst(
        self, legacy_bron: Path, doel: Path
    ):
        """De bewaartabel draagt de bronaffiniteit (TEXT): niets verandert."""
        _sql(
            legacy_bron,
            "UPDATE definitie_geschiedenis SET gewijzigd_op = '20250101' WHERE id = 20;",
        )
        herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        assert _rijen(
            doel,
            f"SELECT typeof(gewijzigd_op), gewijzigd_op FROM {BEWAARTABEL} WHERE id = 20",
        ) == [("text", "20250101")]


# ---------------------------------------------------------------------------
# Herhaalgebruik
# ---------------------------------------------------------------------------
class TestHerhaalgebruik:
    def test_dezelfde_bron_twee_keer_geeft_hetzelfde_doel(
        self, legacy_bron: Path, doel: Path
    ):
        voor = _bestandshash(legacy_bron)
        eerste = herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        tweede = herstel.herstel_naar_nieuw_doel(
            legacy_bron, doel.with_name("tweede.db")
        )
        assert _bestandshash(legacy_bron) == voor
        assert eerste.tabellen == tweede.tabellen
        assert eerste.doel_schema_hash == tweede.doel_schema_hash
        assert eerste.sqlite_sequence_doel == tweede.sqlite_sequence_doel
        assert sorted(p.name for p in doel.parent.iterdir()) == [
            "definities-v4.db",
            "tweede.db",
        ]

    def test_het_doel_is_geen_geldige_bron_meer(self, legacy_bron: Path, doel: Path):
        herstel.herstel_naar_nieuw_doel(legacy_bron, doel)
        with pytest.raises(SchemaContractError) as excinfo:
            herstel.herstel_naar_nieuw_doel(doel, doel.with_name("derde.db"))
        assert excinfo.value.reason == "herstel_precondition_failed"
        assert not doel.with_name("derde.db").exists()
