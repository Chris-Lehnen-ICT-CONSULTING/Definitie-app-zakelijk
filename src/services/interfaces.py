"""
Service interfaces voor clean architecture.

Deze interfaces definiëren de contracten voor de verschillende services
in de applicatie. Ze maken dependency injection en testing mogelijk.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# Enums
class DefinitionStatus(Enum):
    """Status van een definitie."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ValidationSeverity(Enum):
    """Ernst van validatie fouten."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Data Transfer Objects
@dataclass
class GenerationRequest:
    """Request voor het genereren van een definitie."""

    begrip: str
    context: str | None = None
    domein: str | None = None
    organisatie: str | None = None
    extra_instructies: str | None = None


@dataclass
class Definition:
    """Definitie data object."""

    id: int | None = None
    begrip: str = ""
    definitie: str = ""
    toelichting: str | None = None
    bron: str | None = None
    context: str | None = None
    domein: str | None = None
    synoniemen: list[str] | None = None
    gerelateerde_begrippen: list[str] | None = None
    voorbeelden: list[str] | None = None
    categorie: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.synoniemen is None:
            self.synoniemen = []
        if self.gerelateerde_begrippen is None:
            self.gerelateerde_begrippen = []
        if self.voorbeelden is None:
            self.voorbeelden = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ValidationViolation:
    """Een specifieke validatie overtreding."""

    rule_id: str
    severity: ValidationSeverity
    description: str
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """Resultaat van definitie validatie."""

    is_valid: bool
    errors: list[str] | None = None
    warnings: list[str] | None = None
    suggestions: list[str] | None = None
    score: float | None = None
    violations: list[ValidationViolation] | None = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.violations is None:
            self.violations = []


@dataclass
class DefinitionResponse:
    """Response object voor definitie operaties."""

    success: bool = True
    definition: Definition | None = None
    validation: ValidationResult | None = None
    definition_id: int | None = None
    message: str | None = None


# Service Interfaces
class DefinitionGeneratorInterface(ABC):
    """Interface voor definitie generatie services."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> Definition:
        """
        Genereer een nieuwe definitie op basis van het request.

        Args:
            request: GenerationRequest met begrip en context

        Returns:
            Definition object met gegenereerde content
        """

    @abstractmethod
    async def enhance(self, definition: Definition) -> Definition:
        """
        Verbeter een bestaande definitie met extra informatie.

        Args:
            definition: Bestaande definitie om te verbeteren

        Returns:
            Verbeterde definitie
        """


class DefinitionValidatorInterface(ABC):
    """Interface voor definitie validatie services."""

    @abstractmethod
    def validate(self, definition: Definition) -> ValidationResult:
        """
        Valideer een definitie volgens de geldende regels.

        Args:
            definition: Te valideren definitie

        Returns:
            ValidationResult met status en eventuele fouten/waarschuwingen
        """

    @abstractmethod
    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        Valideer een specifiek veld van een definitie.

        Args:
            field_name: Naam van het veld
            value: Waarde om te valideren

        Returns:
            ValidationResult voor het specifieke veld
        """


class DefinitionRepositoryInterface(ABC):
    """Interface voor definitie opslag services."""

    @abstractmethod
    def save(self, definition: Definition) -> int:
        """
        Sla een definitie op in de repository.

        Args:
            definition: Op te slaan definitie

        Returns:
            ID van de opgeslagen definitie
        """

    @abstractmethod
    def get(self, definition_id: int) -> Definition | None:
        """
        Haal een definitie op basis van ID.

        Args:
            definition_id: ID van de definitie

        Returns:
            Definition indien gevonden, anders None
        """

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[Definition]:
        """
        Zoek definities op basis van een query.

        Args:
            query: Zoekterm
            limit: Maximum aantal resultaten

        Returns:
            Lijst van gevonden definities
        """

    @abstractmethod
    def update(self, definition_id: int, definition: Definition) -> bool:
        """
        Update een bestaande definitie.

        Args:
            definition_id: ID van de te updaten definitie
            definition: Nieuwe definitie data

        Returns:
            True indien succesvol, anders False
        """

    @abstractmethod
    def delete(self, definition_id: int) -> bool:
        """
        Verwijder een definitie.

        Args:
            definition_id: ID van de te verwijderen definitie

        Returns:
            True indien succesvol, anders False
        """

    def update_status(self, definition_id: int, status: DefinitionStatus) -> bool:
        """
        Update de status van een definitie.

        Args:
            definition_id: ID van de definitie
            status: Nieuwe status

        Returns:
            True indien succesvol, anders False
        """
        return False  # Default implementatie

    def find_by_term(self, term: str) -> list[Definition]:
        """
        Zoek definities op term.

        Args:
            term: Zoekterm

        Returns:
            Lijst van gevonden definities
        """
        return self.search(term)  # Gebruik search als fallback

    def find_by_status(self, status: DefinitionStatus) -> list[Definition]:
        """
        Zoek definities op status.

        Args:
            status: DefinitionStatus om op te zoeken

        Returns:
            Lijst van definities met de gegeven status
        """
        return []  # Default implementatie


class DefinitionOrchestratorInterface(ABC):
    """Interface voor het orkestreren van definitie operaties."""

    @abstractmethod
    async def create_definition(self, request: GenerationRequest) -> DefinitionResponse:
        """
        Orkestreer het complete proces van definitie creatie.

        Dit omvat generatie, validatie en opslag.

        Args:
            request: GenerationRequest met input data

        Returns:
            DefinitionResponse met resultaat en status
        """

    @abstractmethod
    async def update_definition(
        self, definition_id: int, updates: dict[str, Any]
    ) -> DefinitionResponse:
        """
        Orkestreer het update proces van een bestaande definitie.

        Args:
            definition_id: ID van de te updaten definitie
            updates: Dictionary met veld updates

        Returns:
            DefinitionResponse met resultaat en status
        """

    @abstractmethod
    async def validate_and_save(self, definition: Definition) -> DefinitionResponse:
        """
        Valideer en sla een definitie op.

        Args:
            definition: Te valideren en op te slaan definitie

        Returns:
            DefinitionResponse met resultaat en status
        """

    async def get_definition(self, definition_id: int) -> Definition | None:
        """
        Haal een definitie op via de orchestrator.

        Args:
            definition_id: ID van de definitie

        Returns:
            Definition indien gevonden
        """
        return None  # Default implementatie

    async def update_definition_status(
        self, definition_id: int, status: DefinitionStatus
    ) -> bool:
        """
        Update de status van een definitie.

        Args:
            definition_id: ID van de definitie
            status: Nieuwe status

        Returns:
            True indien succesvol
        """
        return False  # Default implementatie


# Web Lookup Data Transfer Objects
@dataclass
class WebSource:
    """Een web bron voor lookup."""

    name: str
    url: str
    confidence: float = 0.0
    is_juridical: bool = False
    api_type: str | None = None  # "mediawiki", "sru", "scraping"


@dataclass
class LookupResult:
    """Resultaat van een web lookup operatie."""

    term: str
    source: WebSource
    definition: str | None = None
    context: str | None = None
    examples: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    success: bool = True
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LookupRequest:
    """Request voor web lookup operaties."""

    term: str
    sources: list[str] | None = None  # None = alle bronnen
    context: str | None = None
    max_results: int = 5
    include_examples: bool = True
    timeout: int = 30


@dataclass
class JuridicalReference:
    """Een juridische verwijzing."""

    type: str  # "artikel", "wet", "uitspraak", etc.
    reference: str
    context: str
    confidence: float = 0.0


# Web Lookup Service Interface
class WebLookupServiceInterface(ABC):
    """Interface voor web lookup services."""

    @abstractmethod
    async def lookup(self, request: LookupRequest) -> list[LookupResult]:
        """
        Zoek een term op in web bronnen.

        Args:
            request: LookupRequest met zoekterm en opties

        Returns:
            Lijst van LookupResult objecten
        """

    @abstractmethod
    async def lookup_single_source(self, term: str, source: str) -> LookupResult | None:
        """
        Zoek een term op in een specifieke bron.

        Args:
            term: Zoekterm
            source: Naam van de bron

        Returns:
            LookupResult indien gevonden, anders None
        """

    @abstractmethod
    def get_available_sources(self) -> list[WebSource]:
        """
        Geef lijst van beschikbare web bronnen.

        Returns:
            Lijst van WebSource objecten
        """

    @abstractmethod
    def validate_source(self, text: str) -> WebSource:
        """
        Valideer en identificeer de bron van een tekst.

        Args:
            text: Te valideren tekst

        Returns:
            WebSource met betrouwbaarheidsscore
        """

    @abstractmethod
    def find_juridical_references(self, text: str) -> list[JuridicalReference]:
        """
        Vind juridische verwijzingen in tekst.

        Args:
            text: Te analyseren tekst

        Returns:
            Lijst van gevonden juridische verwijzingen
        """

    @abstractmethod
    def detect_duplicates(
        self, term: str, definitions: list[str]
    ) -> list[dict[str, Any]]:
        """
        Detecteer duplicate definities.

        Args:
            term: Zoekterm
            definitions: Lijst van definities om te vergelijken

        Returns:
            Lijst van duplicaat analyses
        """


# Optional: Event interfaces voor loose coupling
class DefinitionEventHandler(ABC):
    """Interface voor event handling in het definitie proces."""

    @abstractmethod
    def on_definition_created(self, definition: Definition) -> None:
        """Handler voor wanneer een definitie is aangemaakt."""

    @abstractmethod
    def on_definition_validated(
        self, definition: Definition, result: ValidationResult
    ) -> None:
        """Handler voor wanneer een definitie is gevalideerd."""

    @abstractmethod
    def on_definition_saved(self, definition: Definition) -> None:
        """Handler voor wanneer een definitie is opgeslagen."""


@dataclass
class CleaningResult:
    """Resultaat van een opschoning operatie."""

    original_text: str
    cleaned_text: str
    was_cleaned: bool
    applied_rules: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CleaningServiceInterface(ABC):
    """Interface voor definitie opschoning services."""

    @abstractmethod
    def clean_definition(self, definition: Definition) -> CleaningResult:
        """
        Schoon een definitie op en geef gedetailleerd resultaat terug.

        Args:
            definition: Definition object om op te schonen

        Returns:
            CleaningResult met origineel, opgeschoond en metadata
        """

    @abstractmethod
    def clean_text(self, text: str, term: str) -> CleaningResult:
        """
        Schoon een definitie tekst op voor een specifieke term.

        Args:
            text: Te schonen definitie tekst
            term: Het begrip dat gedefinieerd wordt

        Returns:
            CleaningResult met resultaat en metadata
        """

    @abstractmethod
    def validate_cleaning_rules(self) -> bool:
        """
        Valideer of de opschoning regels correct geladen zijn.

        Returns:
            True als regels correct zijn, anders False
        """
