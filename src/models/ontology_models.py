"""Dataclasses voor het ontologisch model (DEF-403, Fase 2.1).

Representeert termen, relaties en modellen uit de ontologie-tabellen
(ontological_models, ontology_terms, ontology_relationships).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OntologyTerm:
    """Één begrip in het ontologisch model."""

    id: int
    model_id: int
    term_text: str
    categorie_6: str | None = None
    ufo_categorie: str | None = None
    classification_confidence: float = 1.0
    wettelijke_basis: str | None = None
    rechtsgebied: str | None = None


@dataclass
class OntologyRelationship:
    """Relatie tussen twee termen (is-a, bevat, identificeert, etc.)."""

    id: int
    model_id: int
    source_term_id: int
    target_term_id: int
    relationship_type: str
    confidence_score: float = 1.0
    inferred_by: str = "manual"
    # Optioneel gevuld bij laden met JOINs
    source_term_text: str | None = None
    target_term_text: str | None = None


@dataclass
class OntologyModel:
    """Container voor een volledig ontologisch model."""

    id: int
    model_name: str
    version_number: int
    validation_status: str = "draft"
    validation_score: float | None = None
    snapshot: dict = field(default_factory=dict)
    terms: list[OntologyTerm] = field(default_factory=list)
    relationships: list[OntologyRelationship] = field(default_factory=list)
