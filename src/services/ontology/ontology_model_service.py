"""OntologyModelService — lees en beheer ontologische modellen (DEF-403).

Service-laag voor de ontologie-tabellen (ontological_models, ontology_terms,
ontology_relationships). Biedt CRUD-achtige leesoperaties op het geïmporteerde
v9 model en toekomstige modellen.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import defaultdict

from models.ontology_models import OntologyModel, OntologyRelationship, OntologyTerm

logger = logging.getLogger(__name__)


class OntologyModelService:
    """Leesoperaties op ontologische modellen.

    Verantwoordelijkheden:
    - Model laden met termen en relaties
    - Termen filteren op categorie, zoeken op tekst
    - Relaties ophalen per term of per model
    - Taxonomie-boom genereren (is-a hiërarchie)
    - Golden set begrippen ophalen
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    # ── Model operaties ─────────────────────────────────

    def list_models(self) -> list[dict]:
        """Overzicht van alle modellen (zonder termen/relaties)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT m.id, m.model_name, m.version_number, "
                "m.validation_status, m.created_at, "
                "(SELECT COUNT(*) FROM ontology_terms WHERE model_id = m.id) AS term_count, "
                "(SELECT COUNT(*) FROM ontology_relationships WHERE model_id = m.id) AS rel_count "
                "FROM ontological_models m ORDER BY m.created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_model(self, model_id: int) -> OntologyModel:
        """Laad een volledig model met alle termen en relaties."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM ontological_models WHERE id = ?", (model_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Model {model_id} niet gevonden")

            snapshot = {}
            if row["snapshot_json"]:
                try:
                    snapshot = json.loads(row["snapshot_json"])
                except json.JSONDecodeError:
                    logger.warning("Ongeldige snapshot_json voor model %d", model_id)

            terms = self._load_terms(conn, model_id)
            relationships = self._load_relationships(conn, model_id)

            return OntologyModel(
                id=row["id"],
                model_name=row["model_name"],
                version_number=row["version_number"],
                validation_status=row["validation_status"] or "draft",
                validation_score=(
                    float(row["validation_score"])
                    if row["validation_score"] is not None
                    else None
                ),
                snapshot=snapshot,
                terms=terms,
                relationships=relationships,
            )
        finally:
            conn.close()

    def get_model_by_name(self, name: str) -> OntologyModel | None:
        """Zoek model op naam. Retourneert None als niet gevonden."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id FROM ontological_models WHERE model_name = ?", (name,)
            ).fetchone()
            model_id = row["id"] if row else None
        finally:
            conn.close()
        # Connectie gesloten voordat we get_model aanroepen (review fix: voorkom dubbele connectie)
        return self.get_model(model_id) if model_id is not None else None

    # ── Term operaties ──────────────────────────────────

    def get_terms(
        self, model_id: int, categorie: str | None = None
    ) -> list[OntologyTerm]:
        """Alle termen van een model, optioneel gefilterd op categorie."""
        conn = self._connect()
        try:
            sql = "SELECT * FROM ontology_terms WHERE model_id = ?"
            params: list = [model_id]
            if categorie:
                sql += " AND categorie_6 = ?"
                params.append(categorie)
            sql += " ORDER BY term_text"
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_term(r) for r in rows]
        finally:
            conn.close()

    def get_term_by_text(self, model_id: int, term_text: str) -> OntologyTerm | None:
        """Zoek term op exacte tekst."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM ontology_terms WHERE model_id = ? AND term_text = ?",
                (model_id, term_text),
            ).fetchone()
            return self._row_to_term(row) if row else None
        finally:
            conn.close()

    # ── Relatie operaties ───────────────────────────────

    def get_relationships(
        self,
        model_id: int,
        term_id: int | None = None,
        relationship_type: str | None = None,
    ) -> list[OntologyRelationship]:
        """Relaties van een model, optioneel gefilterd op term en/of type."""
        conn = self._connect()
        try:
            sql = (
                "SELECT r.*, s.term_text AS source_text, t.term_text AS target_text "
                "FROM ontology_relationships r "
                "JOIN ontology_terms s ON r.source_term_id = s.id "
                "JOIN ontology_terms t ON r.target_term_id = t.id "
                "WHERE r.model_id = ?"
            )
            params: list = [model_id]
            if term_id is not None:
                sql += " AND (r.source_term_id = ? OR r.target_term_id = ?)"
                params.extend([term_id, term_id])
            if relationship_type:
                sql += " AND r.relationship_type = ?"
                params.append(relationship_type)
            sql += " ORDER BY s.term_text"
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_relationship(r) for r in rows]
        finally:
            conn.close()

    def get_taxonomy_tree(self, model_id: int) -> dict:
        """Bouw geneste is-a hiërarchie.

        Returns:
            Dict met root termen als keys, elk met "children" dict.
            Voorbeeld: {"Entiteit": {"children": {"Persoon": {"children": {...}}}}}
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT s.term_text AS child, t.term_text AS parent "
                "FROM ontology_relationships r "
                "JOIN ontology_terms s ON r.source_term_id = s.id "
                "JOIN ontology_terms t ON r.target_term_id = t.id "
                "WHERE r.model_id = ? AND r.relationship_type = 'is_a'",
                (model_id,),
            ).fetchall()

            # Bouw parent→children mapping
            children_of: dict[str, list[str]] = defaultdict(list)
            all_children = set()
            for row in rows:
                children_of[row["parent"]].append(row["child"])
                all_children.add(row["child"])

            # Root termen = termen die parent zijn maar niet child
            all_parents = set(children_of.keys())
            roots = all_parents - all_children

            def build_tree(term: str, visited: set | None = None) -> dict:
                if visited is None:
                    visited = set()
                node: dict = {"children": {}}
                for child in sorted(children_of.get(term, [])):
                    if child in visited:
                        logger.warning("Cyclus gedetecteerd: %s → %s", term, child)
                        continue
                    node["children"][child] = build_tree(child, visited | {child})
                return node

            tree = {}
            for root in sorted(roots):
                tree[root] = build_tree(root)
            return tree
        finally:
            conn.close()

    # ── Golden set ──────────────────────────────────────

    def get_golden_set(self, model_id: int) -> list[OntologyTerm]:
        """Retourneer de golden set benchmark termen."""
        model = self.get_model(model_id)
        golden_names = model.snapshot.get("golden_set", [])
        if not golden_names:
            return []

        conn = self._connect()
        try:
            placeholders = ",".join("?" for _ in golden_names)
            rows = conn.execute(
                f"SELECT * FROM ontology_terms "
                f"WHERE model_id = ? AND term_text IN ({placeholders})",
                [model_id, *golden_names],
            ).fetchall()
            return [self._row_to_term(r) for r in rows]
        finally:
            conn.close()

    # ── Helpers ─────────────────────────────────────────

    @staticmethod
    def _row_to_term(row: sqlite3.Row) -> OntologyTerm:
        return OntologyTerm(
            id=row["id"],
            model_id=row["model_id"],
            term_text=row["term_text"],
            categorie_6=row["categorie_6"],
            ufo_categorie=row["ufo_categorie"],
            classification_confidence=(
                float(row["classification_confidence"])
                if row["classification_confidence"] is not None
                else 1.0
            ),
            wettelijke_basis=row["wettelijke_basis"],
            rechtsgebied=row["rechtsgebied"],
        )

    @staticmethod
    def _row_to_relationship(row: sqlite3.Row) -> OntologyRelationship:
        return OntologyRelationship(
            id=row["id"],
            model_id=row["model_id"],
            source_term_id=row["source_term_id"],
            target_term_id=row["target_term_id"],
            relationship_type=row["relationship_type"],
            confidence_score=(
                float(row["confidence_score"])
                if row["confidence_score"] is not None
                else 1.0
            ),
            inferred_by=row["inferred_by"] or "manual",
            source_term_text=row["source_text"],
            target_term_text=row["target_text"],
        )

    @staticmethod
    def _load_terms(conn: sqlite3.Connection, model_id: int) -> list[OntologyTerm]:
        rows = conn.execute(
            "SELECT * FROM ontology_terms WHERE model_id = ? ORDER BY term_text",
            (model_id,),
        ).fetchall()
        return [OntologyModelService._row_to_term(r) for r in rows]

    @staticmethod
    def _load_relationships(
        conn: sqlite3.Connection, model_id: int
    ) -> list[OntologyRelationship]:
        rows = conn.execute(
            "SELECT r.*, s.term_text AS source_text, t.term_text AS target_text "
            "FROM ontology_relationships r "
            "JOIN ontology_terms s ON r.source_term_id = s.id "
            "JOIN ontology_terms t ON r.target_term_id = t.id "
            "WHERE r.model_id = ? ORDER BY s.term_text",
            (model_id,),
        ).fetchall()
        return [OntologyModelService._row_to_relationship(r) for r in rows]
