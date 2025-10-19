"""
Synonym Models - Data models voor Synonym Orchestrator Architecture v3.1.

Deze module bevat de dataclasses voor synonym groups, members en weighted queries.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SynonymGroup:
    """
    Representatie van een synonym group.

    Een groep bundelt gerelateerde termen zonder hiërarchie.
    """

    id: int | None = None
    canonical_term: str = ""  # Voorkeurs term voor display
    domain: str | None = None  # "strafrecht", "civielrecht", etc.
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None

    def __post_init__(self):
        """Valideer canonical_term is niet leeg."""
        if not self.canonical_term or not self.canonical_term.strip():
            msg = "canonical_term mag niet leeg zijn"
            raise ValueError(msg)


@dataclass
class SynonymGroupMember:
    """
    Representatie van een member binnen een synonym group.

    Alle members zijn peers (geen hiërarchie), met weighting voor ranking.
    """

    id: int | None = None
    group_id: int = 0
    term: str = ""

    # Weighting & Priority
    weight: float = 1.0  # 0.0-1.0 range
    is_preferred: bool = False  # Top-5 priority flag

    # Lifecycle Status
    status: str = "active"  # active, ai_pending, rejected_auto, deprecated

    # Source Tracking
    source: str = "manual"  # db_seed, manual, ai_suggested, imported_yaml

    # Context & Rationale
    context_json: str | None = None  # JSON: {"rationale": "...", "model": "gpt-4"}

    # Scoping (global vs per-definitie)
    definitie_id: int | None = None  # NULL = global, anders scoped

    # Analytics
    usage_count: int = 0
    last_used_at: datetime | None = None

    # Audit Trail
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    def __post_init__(self):
        """Valideer velden."""
        if not self.term or not self.term.strip():
            msg = "term mag niet leeg zijn"
            raise ValueError(msg)

        if not (0.0 <= self.weight <= 1.0):
            msg = f"weight moet tussen 0.0 en 1.0 zijn: {self.weight}"
            raise ValueError(msg)

        valid_statuses = {"active", "ai_pending", "rejected_auto", "deprecated"}
        if self.status not in valid_statuses:
            msg = f"status moet een van {valid_statuses} zijn: {self.status}"
            raise ValueError(msg)

        valid_sources = {"db_seed", "manual", "ai_suggested", "imported_yaml"}
        if self.source not in valid_sources:
            msg = f"source moet een van {valid_sources} zijn: {self.source}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor serialization."""
        return {
            "id": self.id,
            "group_id": self.group_id,
            "term": self.term,
            "weight": self.weight,
            "is_preferred": self.is_preferred,
            "status": self.status,
            "source": self.source,
            "context_json": self.context_json,
            "definitie_id": self.definitie_id,
            "usage_count": self.usage_count,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


@dataclass
class WeightedSynonym:
    """
    Lightweight model voor synonym query results.

    Gebruikt voor efficiënte bidirectionele lookups zonder alle metadata.
    """

    term: str
    weight: float
    status: str
    is_preferred: bool
    usage_count: int = 0

    def __post_init__(self):
        """Valideer velden."""
        if not (0.0 <= self.weight <= 1.0):
            msg = f"weight moet tussen 0.0 en 1.0 zijn: {self.weight}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            "term": self.term,
            "weight": self.weight,
            "status": self.status,
            "is_preferred": self.is_preferred,
            "usage_count": self.usage_count,
        }
