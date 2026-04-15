"""Tests voor OntologyModelService (DEF-403)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from models.ontology_models import OntologyModel, OntologyRelationship, OntologyTerm
from services.ontology.ontology_model_service import OntologyModelService

pytestmark = [pytest.mark.unit]

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
    path = str(tmp_path / "test.db")
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    conn.close()
    return path


@pytest.fixture
def service(db_path):
    return OntologyModelService(db_path=db_path)


@pytest.fixture
def model_id(db_path):
    """Maak een test-model met termen en relaties."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Model
    cursor = conn.execute(
        "INSERT INTO ontological_models (model_name, version_number, snapshot_json) "
        "VALUES (?, ?, ?)",
        (
            "Test Model",
            1,
            json.dumps({"golden_set": ["Entiteit", "Persoon"], "golden_set_ids": {}}),
        ),
    )
    mid = cursor.lastrowid

    # Termen
    terms = [
        ("Entiteit", "Soort", "Kind", 1.0, None),
        ("Persoon", "Soort", "Kind", 1.0, "BW"),
        ("Natuurlijk Persoon", "Soort", "Kind", 0.9, "BW"),
        ("Identificeren", "Gebeurtenis", "Event", 1.0, "Art. 27a Sv"),
        ("Ketenpartner", "Rol", "Role", 1.0, None),
    ]
    term_ids = {}
    for text, cat, ufo, conf, wet in terms:
        c = conn.execute(
            "INSERT INTO ontology_terms "
            "(model_id, term_text, categorie_6, ufo_categorie, "
            "classification_confidence, wettelijke_basis) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (mid, text, cat, ufo, conf, wet),
        )
        term_ids[text] = c.lastrowid

    # Relaties: Persoon is-a Entiteit, NP is-a Persoon
    conn.execute(
        "INSERT INTO ontology_relationships "
        "(model_id, source_term_id, target_term_id, relationship_type, "
        "confidence_score, inferred_by) VALUES (?, ?, ?, 'is_a', 1.0, 'import')",
        (mid, term_ids["Persoon"], term_ids["Entiteit"]),
    )
    conn.execute(
        "INSERT INTO ontology_relationships "
        "(model_id, source_term_id, target_term_id, relationship_type, "
        "confidence_score, inferred_by) VALUES (?, ?, ?, 'is_a', 1.0, 'import')",
        (mid, term_ids["Natuurlijk Persoon"], term_ids["Persoon"]),
    )
    # Niet-taxonomische relatie
    conn.execute(
        "INSERT INTO ontology_relationships "
        "(model_id, source_term_id, target_term_id, relationship_type, "
        "confidence_score, inferred_by) VALUES (?, ?, ?, 'identificeert', 1.0, 'import')",
        (mid, term_ids["Identificeren"], term_ids["Persoon"]),
    )

    conn.commit()
    conn.close()
    return mid


# ---------------------------------------------------------------------------
# list_models
# ---------------------------------------------------------------------------
class TestListModels:
    def test_empty(self, service):
        assert service.list_models() == []

    def test_returns_summary(self, service, model_id):
        models = service.list_models()
        assert len(models) == 1
        m = models[0]
        assert m["model_name"] == "Test Model"
        assert m["term_count"] == 5
        assert m["rel_count"] == 3


# ---------------------------------------------------------------------------
# get_model
# ---------------------------------------------------------------------------
class TestGetModel:
    def test_loads_full_model(self, service, model_id):
        model = service.get_model(model_id)
        assert isinstance(model, OntologyModel)
        assert model.model_name == "Test Model"
        assert model.version_number == 1
        assert len(model.terms) == 5
        assert len(model.relationships) == 3
        assert model.snapshot.get("golden_set") == ["Entiteit", "Persoon"]

    def test_nonexistent_raises(self, service):
        with pytest.raises(ValueError, match="niet gevonden"):
            service.get_model(9999)


# ---------------------------------------------------------------------------
# get_model_by_name
# ---------------------------------------------------------------------------
class TestGetModelByName:
    def test_found(self, service, model_id):
        model = service.get_model_by_name("Test Model")
        assert model is not None
        assert model.id == model_id

    def test_not_found(self, service):
        assert service.get_model_by_name("Bestaat Niet") is None


# ---------------------------------------------------------------------------
# get_terms
# ---------------------------------------------------------------------------
class TestGetTerms:
    def test_all_terms(self, service, model_id):
        terms = service.get_terms(model_id)
        assert len(terms) == 5
        assert all(isinstance(t, OntologyTerm) for t in terms)

    def test_filter_on_categorie(self, service, model_id):
        soort = service.get_terms(model_id, categorie="Soort")
        assert len(soort) == 3
        assert all(t.categorie_6 == "Soort" for t in soort)

        events = service.get_terms(model_id, categorie="Gebeurtenis")
        assert len(events) == 1
        assert events[0].term_text == "Identificeren"

    def test_sorted_by_name(self, service, model_id):
        terms = service.get_terms(model_id)
        names = [t.term_text for t in terms]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# get_term_by_text
# ---------------------------------------------------------------------------
class TestGetTermByText:
    def test_found(self, service, model_id):
        term = service.get_term_by_text(model_id, "Persoon")
        assert term is not None
        assert term.categorie_6 == "Soort"
        assert term.wettelijke_basis == "BW"

    def test_not_found(self, service, model_id):
        assert service.get_term_by_text(model_id, "Onbekend") is None


# ---------------------------------------------------------------------------
# get_relationships
# ---------------------------------------------------------------------------
class TestGetRelationships:
    def test_all_relationships(self, service, model_id):
        rels = service.get_relationships(model_id)
        assert len(rels) == 3
        assert all(isinstance(r, OntologyRelationship) for r in rels)
        assert all(r.source_term_text is not None for r in rels)

    def test_filter_on_type(self, service, model_id):
        is_a = service.get_relationships(model_id, relationship_type="is_a")
        assert len(is_a) == 2

        ident = service.get_relationships(model_id, relationship_type="identificeert")
        assert len(ident) == 1

    def test_filter_on_term(self, service, model_id):
        # Zoek relaties waar Persoon bij betrokken is
        term = service.get_term_by_text(model_id, "Persoon")
        rels = service.get_relationships(model_id, term_id=term.id)
        # Persoon is source in: is-a Entiteit, en target in: NP is-a Persoon + Identificeren
        assert len(rels) == 3


# ---------------------------------------------------------------------------
# get_taxonomy_tree
# ---------------------------------------------------------------------------
class TestGetTaxonomyTree:
    def test_builds_hierarchy(self, service, model_id):
        tree = service.get_taxonomy_tree(model_id)
        assert "Entiteit" in tree
        assert "Persoon" in tree["Entiteit"]["children"]
        assert (
            "Natuurlijk Persoon" in tree["Entiteit"]["children"]["Persoon"]["children"]
        )

    def test_empty_model(self, service, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "INSERT INTO ontological_models (model_name, version_number) VALUES ('Empty', 1)"
        )
        empty_id = cursor.lastrowid
        conn.commit()
        conn.close()
        assert service.get_taxonomy_tree(empty_id) == {}


# ---------------------------------------------------------------------------
# get_golden_set
# ---------------------------------------------------------------------------
class TestGetGoldenSet:
    def test_returns_golden_terms(self, service, model_id):
        golden = service.get_golden_set(model_id)
        names = {t.term_text for t in golden}
        assert "Entiteit" in names
        assert "Persoon" in names
        assert len(golden) == 2

    def test_no_golden_set(self, service, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "INSERT INTO ontological_models (model_name, version_number, snapshot_json) "
            "VALUES ('No Golden', 1, '{}')"
        )
        mid = cursor.lastrowid
        conn.commit()
        conn.close()
        assert service.get_golden_set(mid) == []
