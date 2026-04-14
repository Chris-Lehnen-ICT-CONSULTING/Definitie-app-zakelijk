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
