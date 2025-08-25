"""Domain models voor category management."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DefinitionCategory:
    """Domain model voor definitie categorie."""

    code: str  # ENT, REL, ACT, etc.
    display_name: str
    reasoning: str | None = None
    confidence: float = 0.0
    analysis_details: dict | None = None

    @classmethod
    def from_code(cls, code: str) -> "DefinitionCategory":
        """Factory method om category van code te maken."""
        category_map = {
            "ENT": "Entiteit",
            "REL": "Relatie",
            "ACT": "Activiteit",
            "ATT": "Attribuut",
            "AUT": "Autorisatie",
            "STA": "Status",
            "OTH": "Overig",
        }
        return cls(code=code, display_name=category_map.get(code, code))


@dataclass
class CategoryChangeResult:
    """Result van een category wijziging."""

    success: bool
    message: str
    previous_category: str | None = None
    new_category: str | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class CategoryUpdateEvent:
    """Event voor category updates."""

    definition_id: int
    old_category: str
    new_category: str
    changed_by: str
    reason: str | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
