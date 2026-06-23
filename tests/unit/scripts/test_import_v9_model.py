"""Tests voor import_v9_model.py (DEF-305)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.unit]

# Import het script als module
import importlib
import sys

# Voeg scripts/ toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

# DEF-466: scripts/import_v9_model.py importeert openpyxl (optionele tooling-dep,
# niet in requirements*.txt). Skip de hele module netjes als openpyxl ontbreekt
# (zoals in CI) i.p.v. een harde collectie-fout die de coverage-gate breekt.
pytest.importorskip("openpyxl")
import import_v9_model

# Schema voor test database (matches v5_migration)
SCHEMA_SQL = """
CREATE TABLE rag_collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_name VARCHAR(255),
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ontological_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(255) NOT NULL,
    version_number INTEGER DEFAULT 1,
    parent_version_id INTEGER REFERENCES ontological_models(id),
    rag_collection_id INTEGER REFERENCES rag_collections(id),
    validation_status VARCHAR(50) DEFAULT 'draft',
    validation_score DECIMAL(3,2),
    snapshot_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE ontology_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES ontological_models(id) ON DELETE CASCADE,
    term_text VARCHAR(255) NOT NULL,
    categorie_6 VARCHAR(50),
    ufo_categorie VARCHAR(50),
    classification_confidence DECIMAL(3,2),
    wettelijke_basis VARCHAR(255),
    rechtsgebied VARCHAR(100),
    rag_context_summary TEXT
);

CREATE TABLE ontology_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES ontological_models(id) ON DELETE CASCADE,
    source_term_id INTEGER REFERENCES ontology_terms(id) ON DELETE CASCADE,
    target_term_id INTEGER REFERENCES ontology_terms(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    inferred_by VARCHAR(50) DEFAULT 'manual'
);
"""


@pytest.fixture
def db_path(tmp_path):
    """SQLite DB met ontologie schema."""
    path = tmp_path / "test.db"
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA_SQL)
    conn.close()
    return path


# ---------------------------------------------------------------------------
# Categorie mapping
# ---------------------------------------------------------------------------
class TestCategorieMapping:
    def test_all_categories_mapped(self):
        assert import_v9_model.CATEGORIE_TO_UFO["Soort"] == "Kind"
        assert import_v9_model.CATEGORIE_TO_UFO["Rol"] == "Role"
        assert import_v9_model.CATEGORIE_TO_UFO["Toestand"] == "Phase"
        assert import_v9_model.CATEGORIE_TO_UFO["Eigenschap"] == "Quality"
        assert import_v9_model.CATEGORIE_TO_UFO["Gebeurtenis"] == "Event"
        assert import_v9_model.CATEGORIE_TO_UFO["Verbinder"] == "Relator"

    def test_six_categories(self):
        assert len(import_v9_model.CATEGORIE_TO_UFO) == 6


# ---------------------------------------------------------------------------
# Parse functies (review fix: coverage van Excel parsing logica)
# ---------------------------------------------------------------------------
def _make_mock_workbook(sheet_name: str, rows: list[tuple]) -> MagicMock:
    """Maak een mock openpyxl Workbook met één sheet."""
    wb = MagicMock()
    ws = MagicMock()
    ws.iter_rows.return_value = iter(rows)
    wb.__getitem__ = lambda self, name: ws
    return wb


class TestParseBegrippen:
    def test_parses_basic_row(self):
        rows = [
            (
                "Persoon",
                "Soort",
                "Een natuurlijk persoon",
                "BW",
                "Voorbeeld 1",
                "Voorbeeld 2",
                None,
                "Tegen 1",
                None,
                None,
                "https://example.com",
            ),
        ]
        wb = _make_mock_workbook("Begrippen", rows)
        result = import_v9_model.parse_begrippen(wb)
        assert len(result) == 1
        assert result[0]["term_text"] == "Persoon"
        assert result[0]["categorie_6"] == "Soort"
        assert result[0]["ufo_categorie"] == "Kind"
        assert result[0]["definitie"] == "Een natuurlijk persoon"
        assert result[0]["wettelijke_basis"] == "BW"
        assert result[0]["voorbeelden"] == ["Voorbeeld 1", "Voorbeeld 2"]
        assert result[0]["tegenvoorbeelden"] == ["Tegen 1"]
        assert result[0]["bron_url"] == "https://example.com"

    def test_skips_empty_rows(self):
        rows = [(None, None, None, None, None, None, None, None, None, None, None)]
        wb = _make_mock_workbook("Begrippen", rows)
        assert import_v9_model.parse_begrippen(wb) == []

    def test_dash_wettelijke_basis_becomes_none(self):
        rows = [("Term", "Soort", "Def", "-", None, None, None, None, None, None, None)]
        wb = _make_mock_workbook("Begrippen", rows)
        result = import_v9_model.parse_begrippen(wb)
        assert result[0]["wettelijke_basis"] is None

    def test_unknown_categorie_gives_none_ufo(self):
        rows = [
            ("Term", "Onbekend", "Def", None, None, None, None, None, None, None, None)
        ]
        wb = _make_mock_workbook("Begrippen", rows)
        result = import_v9_model.parse_begrippen(wb)
        assert result[0]["categorie_6"] == "Onbekend"
        assert result[0]["ufo_categorie"] is None


class TestParseTaxonomie:
    def test_parses_is_a_relation(self):
        rows = [
            ("Persoon", "Entiteit", None, "CORRECT", "BW", None, None),
        ]
        wb = _make_mock_workbook("Taxonomie met Verificatie", rows)
        result = import_v9_model.parse_taxonomie(wb)
        assert len(result) == 1
        assert result[0]["source"] == "Persoon"
        assert result[0]["target"] == "Entiteit"
        assert result[0]["type"] == "is_a"
        assert result[0]["verificatie"] == "CORRECT"

    def test_skips_header_row(self):
        rows = [("Begrip", "is-een (supertype)", None, None, None, None, None)]
        wb = _make_mock_workbook("Taxonomie met Verificatie", rows)
        assert import_v9_model.parse_taxonomie(wb) == []

    def test_skips_empty_rows(self):
        rows = [(None, None, None, None, None, None, None)]
        wb = _make_mock_workbook("Taxonomie met Verificatie", rows)
        assert import_v9_model.parse_taxonomie(wb) == []


class TestParseRelaties:
    def test_parses_relation(self):
        rows = [("Identiteit", "identificeert", "Entiteit", "Fundamenteel")]
        wb = _make_mock_workbook("Relaties", rows)
        result = import_v9_model.parse_relaties(wb)
        assert len(result) == 1
        assert result[0]["source"] == "Identiteit"
        assert result[0]["type"] == "identificeert"
        assert result[0]["target"] == "Entiteit"
        assert result[0]["toelichting"] == "Fundamenteel"

    def test_skips_incomplete_rows(self):
        rows = [("Alleen bron", None, None, None)]
        wb = _make_mock_workbook("Relaties", rows)
        assert import_v9_model.parse_relaties(wb) == []


class TestParseWettelijkeGrondslagen:
    def test_parses_grondslag(self):
        rows = [
            (
                "Art. 27a Sv",
                "Sv",
                "ID vaststelling",
                "Begrip1, Begrip2",
                "https://wetten.nl",
            )
        ]
        wb = _make_mock_workbook("Wettelijke grondslagen", rows)
        result = import_v9_model.parse_wettelijke_grondslagen(wb)
        assert len(result) == 1
        assert result[0]["wet_artikel"] == "Art. 27a Sv"
        assert result[0]["bron_url"] == "https://wetten.nl"


# ---------------------------------------------------------------------------
# Idempotency (review fix)
# ---------------------------------------------------------------------------
class TestIdempotency:
    def test_raises_on_duplicate_model(self, db_path):
        begrippen = [
            {
                "term_text": "Test",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            }
        ]
        # Eerste import slaagt
        import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=[],
            grondslagen=[],
        )
        # Tweede import faalt
        with pytest.raises(RuntimeError, match="bestaat al"):
            import_v9_model.import_model(
                db_path=db_path,
                begrippen=begrippen,
                taxonomie=[],
                relaties=[],
                grondslagen=[],
            )


# ---------------------------------------------------------------------------
# Voorbeelden in snapshot (review fix)
# ---------------------------------------------------------------------------
class TestVoorbeeldenInSnapshot:
    def test_voorbeelden_stored_in_snapshot(self, db_path):
        begrippen = [
            {
                "term_text": "Persoon",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
                "voorbeelden": ["Jan", "Piet"],
                "tegenvoorbeelden": ["Een hond"],
            }
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=[],
            grondslagen=[],
        )
        conn = sqlite3.connect(str(db_path))
        snapshot = json.loads(
            conn.execute(
                "SELECT snapshot_json FROM ontological_models WHERE id=?",
                (stats["model_id"],),
            ).fetchone()[0]
        )
        conn.close()
        assert "voorbeelden" in snapshot
        assert snapshot["voorbeelden"]["Persoon"]["voorbeelden"] == ["Jan", "Piet"]
        assert snapshot["voorbeelden"]["Persoon"]["tegenvoorbeelden"] == ["Een hond"]


# ---------------------------------------------------------------------------
# import_model
# ---------------------------------------------------------------------------
class TestImportModel:
    def test_creates_model_record(self, db_path):
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=[
                {
                    "term_text": "Test",
                    "categorie_6": "Soort",
                    "ufo_categorie": "Kind",
                    "wettelijke_basis": None,
                }
            ],
            taxonomie=[],
            relaties=[],
            grondslagen=[],
        )
        assert stats["model_id"] == 1
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT model_name, version_number FROM ontological_models WHERE id=1"
        ).fetchone()
        conn.close()
        assert row[0] == "Identiteitsbehandeling v9"
        assert row[1] == 9

    def test_imports_begrippen(self, db_path):
        begrippen = [
            {
                "term_text": "Persoon",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": "BW",
            },
            {
                "term_text": "Identificeren",
                "categorie_6": "Gebeurtenis",
                "ufo_categorie": "Event",
                "wettelijke_basis": None,
            },
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=[],
            grondslagen=[],
        )
        assert stats["begrippen"] == 2

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute(
            "SELECT term_text, categorie_6, ufo_categorie FROM ontology_terms ORDER BY id"
        ).fetchall()
        conn.close()
        assert len(rows) == 2
        assert rows[0] == ("Persoon", "Soort", "Kind")
        assert rows[1] == ("Identificeren", "Gebeurtenis", "Event")

    def test_imports_taxonomie(self, db_path):
        begrippen = [
            {
                "term_text": "Entiteit",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            },
            {
                "term_text": "Persoon",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            },
        ]
        taxonomie = [
            {
                "source": "Persoon",
                "target": "Entiteit",
                "type": "is_a",
                "verificatie": "CORRECT",
                "juridische_bron": "BW",
            }
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=taxonomie,
            relaties=[],
            grondslagen=[],
        )

        assert stats["taxonomie_imported"] == 1
        assert stats["taxonomie_skipped"] == 0

        conn = sqlite3.connect(str(db_path))
        rel = conn.execute(
            "SELECT r.relationship_type, s.term_text, t.term_text "
            "FROM ontology_relationships r "
            "JOIN ontology_terms s ON r.source_term_id = s.id "
            "JOIN ontology_terms t ON r.target_term_id = t.id"
        ).fetchone()
        conn.close()
        assert rel == ("is_a", "Persoon", "Entiteit")

    def test_skips_unknown_terms_in_taxonomie(self, db_path):
        begrippen = [
            {
                "term_text": "A",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            }
        ]
        taxonomie = [
            {
                "source": "A",
                "target": "Onbekend",
                "type": "is_a",
                "verificatie": None,
                "juridische_bron": None,
            }
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=taxonomie,
            relaties=[],
            grondslagen=[],
        )
        assert stats["taxonomie_skipped"] == 1

    def test_imports_relaties(self, db_path):
        begrippen = [
            {
                "term_text": "Identiteit",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            },
            {
                "term_text": "Entiteit",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            },
        ]
        relaties = [
            {
                "source": "Identiteit",
                "type": "identificeert",
                "target": "Entiteit",
                "toelichting": "test",
            }
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=relaties,
            grondslagen=[],
        )
        assert stats["relaties_imported"] == 1

    def test_dry_run_does_not_persist(self, db_path):
        begrippen = [
            {
                "term_text": "Test",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            }
        ]
        import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=[],
            grondslagen=[],
            dry_run=True,
        )

        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM ontology_terms").fetchone()[0]
        conn.close()
        assert count == 0

    def test_golden_set_in_snapshot(self, db_path):
        begrippen = [
            {
                "term_text": "Entiteit",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            }
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=[],
            grondslagen=[],
        )

        conn = sqlite3.connect(str(db_path))
        snapshot = conn.execute(
            "SELECT snapshot_json FROM ontological_models WHERE id=?",
            (stats["model_id"],),
        ).fetchone()[0]
        conn.close()
        data = json.loads(snapshot)
        assert "golden_set" in data
        assert "golden_set_ids" in data

    def test_grondslagen_in_snapshot(self, db_path):
        grondslagen = [
            {
                "wet_artikel": "Art. 27a Sv",
                "volledige_naam": "Sv",
                "onderwerp": "ID",
                "relevante_begrippen": "test",
                "bron_url": None,
            }
        ]
        begrippen = [
            {
                "term_text": "X",
                "categorie_6": "Soort",
                "ufo_categorie": "Kind",
                "wettelijke_basis": None,
            }
        ]
        stats = import_v9_model.import_model(
            db_path=db_path,
            begrippen=begrippen,
            taxonomie=[],
            relaties=[],
            grondslagen=grondslagen,
        )

        conn = sqlite3.connect(str(db_path))
        snapshot = json.loads(
            conn.execute(
                "SELECT snapshot_json FROM ontological_models WHERE id=?",
                (stats["model_id"],),
            ).fetchone()[0]
        )
        conn.close()
        assert snapshot["grondslagen_count"] == 1
        assert snapshot["wettelijke_grondslagen"][0]["wet_artikel"] == "Art. 27a Sv"
