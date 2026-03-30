"""Data models voor de database laag.

Bevat de dataclasses en enums die door alle database sub-modules
en service-lagen worden gebruikt.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, cast

logger = logging.getLogger(__name__)


def normalize_wettelijke_basis(basis: list[str] | None) -> str:
    """Normaliseer wettelijke basis naar gesorteerde, unieke JSON string."""
    try:
        norm = sorted({str(x).strip() for x in (basis or [])})
        return json.dumps(norm, ensure_ascii=False)
    except Exception as e:
        logger.debug(f"Wettelijke basis normalisatie gefaald, gebruik raw dump: {e}")
        return json.dumps(basis or [], ensure_ascii=False)


class DefinitieStatus(Enum):
    """Status van een definitie in het systeem."""

    IMPORTED = "imported"
    DRAFT = "draft"
    REVIEW = "review"
    ESTABLISHED = "established"
    ARCHIVED = "archived"


class SourceType(Enum):
    """Type van de bron waaruit definitie komt."""

    GENERATED = "generated"
    IMPORTED = "imported"
    MANUAL = "manual"


@dataclass
class DefinitieRecord:
    """Representatie van een definitie record in de database."""

    # Basis definitie informatie
    id: int | None = None
    begrip: str = ""
    definitie: str = ""
    categorie: str = ""
    organisatorische_context: str = ""
    juridische_context: str | None = ""
    wettelijke_basis: str | None = None
    ufo_categorie: str | None = None

    # Procesmatige velden
    toelichting_proces: str | None = None

    # Status en versioning
    status: str = DefinitieStatus.DRAFT.value
    version_number: int = 1
    previous_version_id: int | None = None

    # Validation
    validation_score: float | None = None
    validation_date: datetime | None = None
    validation_issues: str | None = None

    # Source tracking
    source_type: str = SourceType.GENERATED.value
    source_reference: str | None = None
    imported_from: str | None = None

    # Voorkeursterm (single source of truth op definitie-niveau)
    voorkeursterm: str | None = None

    # Metadata
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    # Legacy metadata fields
    datum_voorstel: datetime | None = None
    ketenpartners: str | None = None

    # Approval
    approved_by: str | None = None
    approved_at: datetime | None = None
    approval_notes: str | None = None

    # Export
    last_exported_at: datetime | None = None
    export_destinations: str | None = None

    # Generation Prompt Storage (DEF-151)
    generation_prompt_data: str | None = None

    # Deprecated
    voorkeursterm_is_begrip: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialization."""
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result

    def get_validation_issues_list(self) -> list[dict[str, Any]]:
        """Haal validation issues op als list."""
        if not self.validation_issues:
            return []
        try:
            return cast(list[dict[str, Any]], json.loads(self.validation_issues))
        except json.JSONDecodeError:
            return []

    def set_validation_issues(self, issues: list[dict[str, Any]]):
        """Set validation issues als JSON string."""
        self.validation_issues = json.dumps(issues, ensure_ascii=False)

    def get_wettelijke_basis_list(self) -> list[str]:
        """Haal wettelijke basis op als list."""
        if not self.wettelijke_basis:
            return []
        try:
            return cast(list[str], json.loads(self.wettelijke_basis))
        except json.JSONDecodeError:
            return []

    def set_wettelijke_basis(self, basis: list[str]):
        """Set wettelijke basis als JSON string."""
        self.wettelijke_basis = normalize_wettelijke_basis(basis)

    def get_export_destinations_list(self) -> list[str]:
        """Haal export destinations op als list."""
        if not self.export_destinations:
            return []
        try:
            return cast(list[str], json.loads(self.export_destinations))
        except json.JSONDecodeError:
            return []

    def add_export_destination(self, destination: str):
        """Voeg export destination toe."""
        destinations = self.get_export_destinations_list()
        if destination not in destinations:
            destinations.append(destination)
            self.export_destinations = json.dumps(destinations)

    def get_ketenpartners_list(self) -> list[str]:
        """Haal ketenpartners op als list."""
        if not self.ketenpartners:
            return []
        try:
            return cast(list[str], json.loads(self.ketenpartners))
        except json.JSONDecodeError:
            return []

    def set_ketenpartners(self, partners: list[str]):
        """Set ketenpartners als JSON string."""
        self.ketenpartners = json.dumps(partners, ensure_ascii=False)


@dataclass
class VoorbeeldenRecord:
    """Representatie van een voorbeelden record in de database."""

    id: int | None = None
    definitie_id: int = 0
    voorbeeld_type: str = ""
    voorbeeld_tekst: str = ""
    voorbeeld_volgorde: int = 1
    is_voorkeursterm: bool = False

    # Generation metadata
    gegenereerd_door: str = "system"
    generation_model: str | None = None
    generation_parameters: str | None = None

    # Status
    actief: bool = True
    beoordeeld: bool = False
    beoordeeling: str | None = None
    beoordeeling_notities: str | None = None
    beoordeeld_door: str | None = None
    beoordeeld_op: datetime | None = None

    # Metadata
    aangemaakt_op: datetime | None = None
    bijgewerkt_op: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converteer naar dictionary voor JSON serialization."""
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result

    def get_generation_parameters_dict(self) -> dict[str, Any]:
        """Haal generation parameters op als dictionary."""
        if not self.generation_parameters:
            return {}
        try:
            return cast(dict[str, Any], json.loads(self.generation_parameters))
        except json.JSONDecodeError:
            return {}

    def set_generation_parameters(self, params: dict[str, Any]):
        """Stel generatie parameters in als JSON string."""
        self.generation_parameters = json.dumps(params, ensure_ascii=False)


@dataclass
class DuplicateMatch:
    """Representatie van een mogelijk duplicaat match."""

    definitie_record: DefinitieRecord
    match_score: float
    match_reasons: list[str]
