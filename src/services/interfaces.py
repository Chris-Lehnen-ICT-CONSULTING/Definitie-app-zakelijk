"""
Service interfaces voor clean architecture.

Deze interfaces definiëren de contracten voor de verschillende services
in de applicatie. Ze maken dependency injection en testing mogelijk.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
    context: Optional[str] = None
    domein: Optional[str] = None
    organisatie: Optional[str] = None
    extra_instructies: Optional[str] = None


@dataclass
class Definition:
    """Definitie data object."""
    id: Optional[int] = None
    begrip: str = ""
    definitie: str = ""
    toelichting: Optional[str] = None
    bron: Optional[str] = None
    context: Optional[str] = None
    domein: Optional[str] = None
    synoniemen: List[str] = None
    gerelateerde_begrippen: List[str] = None
    voorbeelden: List[str] = None
    categorie: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

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
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Resultaat van definitie validatie."""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    score: Optional[float] = None
    violations: List[ValidationViolation] = None

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
    definition: Optional[Definition] = None
    validation: Optional[ValidationResult] = None
    definition_id: Optional[int] = None
    message: Optional[str] = None


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
        pass
    
    @abstractmethod
    async def enhance(self, definition: Definition) -> Definition:
        """
        Verbeter een bestaande definitie met extra informatie.
        
        Args:
            definition: Bestaande definitie om te verbeteren
            
        Returns:
            Verbeterde definitie
        """
        pass


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
        pass
    
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
        pass


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
        pass
    
    @abstractmethod
    def get(self, definition_id: int) -> Optional[Definition]:
        """
        Haal een definitie op basis van ID.
        
        Args:
            definition_id: ID van de definitie
            
        Returns:
            Definition indien gevonden, anders None
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Definition]:
        """
        Zoek definities op basis van een query.
        
        Args:
            query: Zoekterm
            limit: Maximum aantal resultaten
            
        Returns:
            Lijst van gevonden definities
        """
        pass
    
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
        pass
    
    @abstractmethod
    def delete(self, definition_id: int) -> bool:
        """
        Verwijder een definitie.
        
        Args:
            definition_id: ID van de te verwijderen definitie
            
        Returns:
            True indien succesvol, anders False
        """
        pass
    
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
    
    def find_by_term(self, term: str) -> List[Definition]:
        """
        Zoek definities op term.
        
        Args:
            term: Zoekterm
            
        Returns:
            Lijst van gevonden definities
        """
        return self.search(term)  # Gebruik search als fallback
    
    def find_by_status(self, status: DefinitionStatus) -> List[Definition]:
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
        pass
    
    @abstractmethod
    async def update_definition(self, definition_id: int, updates: Dict[str, Any]) -> DefinitionResponse:
        """
        Orkestreer het update proces van een bestaande definitie.
        
        Args:
            definition_id: ID van de te updaten definitie
            updates: Dictionary met veld updates
            
        Returns:
            DefinitionResponse met resultaat en status
        """
        pass
    
    @abstractmethod
    async def validate_and_save(self, definition: Definition) -> DefinitionResponse:
        """
        Valideer en sla een definitie op.
        
        Args:
            definition: Te valideren en op te slaan definitie
            
        Returns:
            DefinitionResponse met resultaat en status
        """
        pass
    
    async def get_definition(self, definition_id: int) -> Optional[Definition]:
        """
        Haal een definitie op via de orchestrator.
        
        Args:
            definition_id: ID van de definitie
            
        Returns:
            Definition indien gevonden
        """
        return None  # Default implementatie
    
    async def update_definition_status(self, definition_id: int, status: DefinitionStatus) -> bool:
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
    api_type: Optional[str] = None  # "mediawiki", "sru", "scraping"


@dataclass
class LookupResult:
    """Resultaat van een web lookup operatie."""
    term: str
    source: WebSource
    definition: Optional[str] = None
    context: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LookupRequest:
    """Request voor web lookup operaties."""
    term: str
    sources: Optional[List[str]] = None  # None = alle bronnen
    context: Optional[str] = None
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
    async def lookup(self, request: LookupRequest) -> List[LookupResult]:
        """
        Zoek een term op in web bronnen.
        
        Args:
            request: LookupRequest met zoekterm en opties
            
        Returns:
            Lijst van LookupResult objecten
        """
        pass
    
    @abstractmethod
    async def lookup_single_source(self, term: str, source: str) -> Optional[LookupResult]:
        """
        Zoek een term op in een specifieke bron.
        
        Args:
            term: Zoekterm
            source: Naam van de bron
            
        Returns:
            LookupResult indien gevonden, anders None
        """
        pass
    
    @abstractmethod
    def get_available_sources(self) -> List[WebSource]:
        """
        Geef lijst van beschikbare web bronnen.
        
        Returns:
            Lijst van WebSource objecten
        """
        pass
    
    @abstractmethod
    def validate_source(self, text: str) -> WebSource:
        """
        Valideer en identificeer de bron van een tekst.
        
        Args:
            text: Te valideren tekst
            
        Returns:
            WebSource met betrouwbaarheidsscore
        """
        pass
    
    @abstractmethod
    def find_juridical_references(self, text: str) -> List[JuridicalReference]:
        """
        Vind juridische verwijzingen in tekst.
        
        Args:
            text: Te analyseren tekst
            
        Returns:
            Lijst van gevonden juridische verwijzingen
        """
        pass
    
    @abstractmethod
    def detect_duplicates(self, term: str, definitions: List[str]) -> List[Dict[str, Any]]:
        """
        Detecteer duplicate definities.
        
        Args:
            term: Zoekterm
            definitions: Lijst van definities om te vergelijken
            
        Returns:
            Lijst van duplicaat analyses
        """
        pass


# Optional: Event interfaces voor loose coupling
class DefinitionEventHandler(ABC):
    """Interface voor event handling in het definitie proces."""
    
    @abstractmethod
    def on_definition_created(self, definition: Definition) -> None:
        """Handler voor wanneer een definitie is aangemaakt."""
        pass
    
    @abstractmethod
    def on_definition_validated(self, definition: Definition, result: ValidationResult) -> None:
        """Handler voor wanneer een definitie is gevalideerd."""
        pass
    
    @abstractmethod
    def on_definition_saved(self, definition: Definition) -> None:
        """Handler voor wanneer een definitie is opgeslagen."""
        pass