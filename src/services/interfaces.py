"""
Service interfaces voor clean architecture.

Deze interfaces definiëren de contracten voor de verschillende services
in de applicatie. Ze maken dependency injection en testing mogelijk.
"""

from abc import ABC, abstractmethod  # Abstract Base Classes voor interface definitie
from dataclasses import (  # Dataclass decorators voor gestructureerde data
    dataclass,
    field,
)
from datetime import datetime  # Datum/tijd functionaliteit voor timestamps
from enum import Enum  # Enumeratie types voor constante waarden
from typing import Any  # Type hints voor flexibele type definities

# GenerationResult compatibility class for tests (EPIC-010 FASE 1 shim)
# This avoids circular imports and maintains backward compatibility


@dataclass
class GenerationResult:
    """
    Compatibility wrapper for legacy interface.
    This is a temporary shim for EPIC-010 FASE 1 to fix test imports.
    The actual implementation is in src/orchestration/definitie_agent.py
    """

    definitie: str
    metadata: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    voorbeelden: dict[str, Any] | None = None
    voorbeelden_gegenereerd: bool = False
    voorbeelden_error: str | None = None

    @property
    def prompt_template(self):
        """Get prompt template from metadata for debug section"""
        return (
            self.metadata.get("prompt_template", "Geen prompt beschikbaar")
            if self.metadata
            else "Geen prompt beschikbaar"
        )


# Enumeraties voor status en severity tracking
class DefinitionStatus(Enum):
    """Status van een definitie in de workflow."""

    DRAFT = "draft"  # Concept versie, nog in bewerking
    REVIEW = "review"  # Klaar voor juridische review
    APPROVED = "approved"  # Goedgekeurd voor gebruik
    REJECTED = "rejected"  # Afgekeurd, moet aangepast worden
    ARCHIVED = "archived"  # Gearchiveerd, niet meer actief


class ValidationSeverity(Enum):
    """Ernst niveau van validatie fouten voor prioritering."""

    LOW = "low"  # Kleine verbeteringen, niet kritisch
    MEDIUM = "medium"  # Moet opgelost worden maar niet urgent
    HIGH = "high"  # Belangrijke problemen die aandacht vereisen
    CRITICAL = "critical"  # Kritieke fouten die directe actie vereisen


# Data Transfer Objects voor service communicatie
@dataclass
class GenerationRequest:
    """Request object voor het genereren van een definitie."""

    id: str  # Unieke identifier voor tracking en logging
    begrip: str  # Het begrip waarvoor een definitie gegenereerd wordt
    # DEPRECATED (EPIC-010): use list-based fields; kept for legacy callers until full removal
    context: str | None = None  # Contextuele informatie (legacy)
    domein: str | None = None  # Juridisch domein (bijv. "Belasting", "Milieu")
    organisatie: str | None = None  # Verantwoordelijke organisatie
    extra_instructies: str | None = None  # Specifieke instructies van gebruiker
    ontologische_categorie: str | None = (
        None  # Categorie uit 6-stappen classificatie protocol
    )
    options: dict[str, Any] | None = (
        None  # AI model opties (temperatuur, model type, etc.)
    )
    actor: str | None = None  # Gebruiker/systeem die request maakt
    legal_basis: str | None = None  # Juridische basis voor DPIA/privacy compliance
    # Uitgebreide context velden voor rijke context ondersteuning
    juridische_context: list[str] | None = (
        None  # Juridische context (Civiel recht, Strafrecht, etc.)
    )
    wettelijke_basis: list[str] | None = (
        None  # Wettelijke basis (Wetboek van Strafvordering, etc.)
    )
    organisatorische_context: list[str] | None = (
        None  # Organisatorische context (DJI, OM, etc.)
    )


@dataclass
class Definition:
    """Definitie data object met alle benodigde metadata voor juridische definities."""

    id: int | None = None  # Database primary key voor unieke identificatie
    begrip: str = ""  # Het begrip dat wordt gedefinieerd (hoofdterm)
    definitie: str = ""  # De eigenlijke definitie tekst
    toelichting: str | None = None  # Uitgebreidere uitleg of context
    bron: str | None = None  # Juridische bron (wet, artikel, jurisprudentie)
    # DEPRECATED (EPIC-010): maintain for UI compatibility only; prefer list-based context fields in requests
    context: str | None = None  # Specifieke context (legacy)
    domein: str | None = None  # Juridisch domein (bijv. belastingrecht)
    synoniemen: list[str] | None = None  # Alternatieve benamingen voor hetzelfde begrip
    gerelateerde_begrippen: list[str] | None = (
        None  # Begrippen die inhoudelijk gerelateerd zijn
    )
    voorbeelden: list[str] | None = None  # Concrete voorbeelden ter verduidelijking
    categorie: str | None = None  # Legacy categorisering (wordt vervangen)
    ontologische_categorie: str | None = (
        None  # V2: Nieuwe classificatie volgens 6-stappen protocol
    )
    valid: bool | None = None  # Status van laatste validatie check
    validation_violations: list | None = (
        None  # V2: Lijst van gevonden validatie overtredingen
    )
    created_by: str | None = None  # Wie heeft deze definitie aangemaakt (audit trail)
    created_at: datetime | None = None  # Wanneer werd definitie aangemaakt
    updated_at: datetime | None = None  # Laatste wijzigingsdatum
    metadata: dict[str, Any] | None = None  # Extra metadata voor uitbreidbaarheid

    def __post_init__(self) -> None:
        """Post-initialisatie om None waarden te vervangen door lege lijsten/dictionaries."""
        if self.synoniemen is None:
            self.synoniemen = []  # Zorg voor lege lijst in plaats van None
        if self.gerelateerde_begrippen is None:
            self.gerelateerde_begrippen = []  # Voorkom None pointer fouten
        if self.voorbeelden is None:
            self.voorbeelden = []  # Initialiseer als lege lijst
        if self.metadata is None:
            self.metadata = {}  # Zorg voor lege dictionary voor uitbreidbaarheid
        if self.validation_violations is None:
            self.validation_violations = []  # Lege lijst voor validatie resultaten


@dataclass
class ValidationViolation:
    """Een specifieke validatie overtreding met details voor herstel."""

    rule_id: str  # Unieke identifier van de overtreden validatieregel
    severity: ValidationSeverity  # Ernst niveau van de overtreding
    description: str  # Menselijke beschrijving van wat er fout is
    suggestion: str | None = None  # Optioneel voorstel voor verbetering


@dataclass
class ValidationResult:
    """Resultaat van definitie validatie met gedetailleerde feedback."""

    is_valid: bool  # Hoofdresultaat: is de definitie geldig volgens alle regels
    definition_text: str | None = None  # V2: De tekst die gevalideerd werd
    errors: list[str] | None = None  # Kritieke fouten die opgelost moeten worden
    warnings: list[str] | None = None  # Waarschuwingen voor mogelijke problemen
    suggestions: list[str] | None = None  # Voorstellen voor verbeteringen
    score: float | None = None  # Numerieke kwaliteitsscore (0.0 - 1.0)
    violations: list[ValidationViolation] | None = (
        None  # V2: Gedetailleerde overtreding lijst
    )

    def __post_init__(self) -> None:
        """Post-initialisatie om None waarden te vervangen door lege lijsten."""
        if self.errors is None:
            self.errors = []  # Initialiseer lege error lijst
        if self.warnings is None:
            self.warnings = []  # Initialiseer lege warning lijst
        if self.suggestions is None:
            self.suggestions = []  # Initialiseer lege suggestie lijst
        if self.violations is None:
            self.violations = []  # Initialiseer lege violations lijst


@dataclass
class DefinitionResponse:
    """Response object voor definitie operaties met status en resultaat."""

    success: bool = True  # Geeft aan of de operatie succesvol was
    definition: Definition | None = None  # De resulterende definitie (bij success)
    validation: ValidationResult | None = None  # Validatie resultaat indien uitgevoerd
    definition_id: int | None = None  # Database ID van opgeslagen definitie
    message: str | None = None  # Optionele message (fout of info)


# Service Interfaces - Abstract base classes voor service contracten
class DefinitionGeneratorInterface(ABC):
    """Interface voor definitie generatie services die AI models aansturen."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> Definition:
        """
        Genereer een nieuwe definitie op basis van het request.

        Deze methode gebruikt AI modellen om een juridische definitie te creëren
        op basis van het opgegeven begrip en context informatie.

        Args:
            request: GenerationRequest met begrip, context en generatie opties

        Returns:
            Definition object met gegenereerde definitie tekst en metadata
        """

    @abstractmethod
    async def enhance(self, definition: Definition) -> Definition:
        """
        Verbeter een bestaande definitie met extra informatie en context.

        Deze methode verrijkt een bestaande definitie door het toevoegen van
        synoniemen, gerelateerde begrippen, voorbeelden en verbeterde toelichting.

        Args:
            definition: Bestaande definitie om te verbeteren en uit te breiden

        Returns:
            Verbeterde definitie met aanvullende informatie
        """


class DefinitionValidatorInterface(ABC):
    """Interface voor definitie validatie services volgens Nederlandse kwaliteitseisen.

    DEPRECATED: Deze sync interface is onderdeel van V1 architectuur.
    Gebruik ValidationServiceInterface voor V2 async implementaties.
    """

    @abstractmethod
    def validate(self, definition: Definition) -> ValidationResult:
        """
        Valideer een definitie volgens alle geldende juridische en taalkundige regels.

        Deze methode controleert de definitie op conformiteit met Nederlandse
        overheids-standaarden voor juridische definities, inclusief taalgebruik,
        structuur en inhoudelijke volledigheid.

        Args:
            definition: Te valideren definitie object

        Returns:
            ValidationResult met validatie status, fouten, waarschuwingen en verbetervoorstellen
        """

    @abstractmethod
    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        Valideer een specifiek veld van een definitie tegen geldende regels.

        Deze methode maakt gedetailleerde validatie mogelijk per individueel
        veld voor real-time feedback in de gebruikersinterface.

        Args:
            field_name: Naam van het definitie veld (bijv. "begrip", "definitie")
            value: De waarde om te valideren

        Returns:
            ValidationResult specifiek voor dit veld met gerichte feedback
        """


class DefinitionRepositoryInterface(ABC):
    """Interface voor definitie opslag services met database operaties."""

    @abstractmethod
    def save(self, definition: Definition) -> int:
        """
        Sla een definitie op in de database repository.

        Deze methode persisteert een definitie object in de database
        en houdt audit trails bij voor traceability.

        Args:
            definition: Definitie object om op te slaan

        Returns:
            Database ID van de opgeslagen definitie voor referentie
        """

    @abstractmethod
    def get(self, definition_id: int) -> Definition | None:
        """
        Haal een definitie op uit de database op basis van ID.

        Deze methode haalt een complete definitie op inclusief
        alle metadata en gerelateerde informatie.

        Args:
            definition_id: Database ID van de definitie om op te halen

        Returns:
            Definition object indien gevonden, anders None
        """

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[Definition]:
        """
        Zoek definities op basis van een zoekterm in begrip en definitie tekst.

        Deze methode voert een full-text search uit over alle definitie
        velden om relevante matches te vinden.

        Args:
            query: Zoekterm of zoekopdracht
            limit: Maximum aantal resultaten om te retourneren

        Returns:
            Lijst van gevonden definities gesorteerd op relevantie
        """

    @abstractmethod
    def update(self, definition_id: int, definition: Definition) -> bool:
        """
        Update een bestaande definitie in de database.

        Deze methode werkt een bestaande definitie bij en houdt
        versie historie bij voor audit doeleinden.

        Args:
            definition_id: Database ID van de te updaten definitie
            definition: Nieuwe definitie data om op te slaan

        Returns:
            True indien update succesvol was, anders False
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
    async def create_definition(
        self, request: GenerationRequest, context: dict[str, Any] | None = None
    ) -> "DefinitionResponse | DefinitionResponseV2":
        """
        Orkestreer het complete proces van definitie creatie.

        Dit omvat generatie, validatie en opslag.

        Args:
            request: GenerationRequest met input data
            context: Optionele extra context voor orchestratie

        Returns:
            DefinitionResponse of DefinitionResponseV2 met resultaat en status
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
    """Interface voor definitie opschoning services - V2 async versie."""

    @abstractmethod
    async def clean_definition(self, definition: Definition) -> CleaningResult:
        """
        Schoon een definitie op en geef gedetailleerd resultaat terug.

        Args:
            definition: Definition object om op te schonen

        Returns:
            CleaningResult met origineel, opgeschoond en metadata
        """

    @abstractmethod
    async def clean_text(self, text: str, term: str) -> CleaningResult:
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


# ==========================================
# V2 ARCHITECTURE ADDITIONS
# ==========================================


# AI Service Data Transfer Objects
@dataclass
class AIGenerationResult:
    """Resultaat van een AI generatie operatie met alle metadata."""

    text: str  # De gegenereerde tekst
    model: str  # Het gebruikte AI model (bijv. "gpt-4", "gpt-4-1106-preview")
    tokens_used: int | None  # Aantal tokens gebruikt (None als estimated)
    generation_time: float  # Generatie tijd in seconden
    cached: bool = False  # Geeft aan of resultaat uit cache kwam
    retry_count: int = 0  # Aantal retries voordat succes werd behaald
    metadata: dict[str, Any] = field(
        default_factory=dict
    )  # Extra metadata zoals tokens_estimated flag

    def __post_init__(self):
        """Post-initialisatie voor metadata validatie."""
        if self.tokens_used is None and "tokens_estimated" not in self.metadata:
            self.metadata["tokens_estimated"] = True


@dataclass
class AIBatchRequest:
    """Request voor batch AI generatie operaties."""

    prompt: str  # De prompt voor AI generatie
    temperature: float = 0.7  # Temperatuur parameter voor creativiteit
    max_tokens: int = 500  # Maximum aantal tokens in response
    model: str | None = None  # Optioneel specifiek model
    system_prompt: str | None = None  # Optionele system prompt
    timeout_seconds: int = 30  # Timeout voor deze specifieke request
    metadata: dict[str, Any] = field(default_factory=dict)  # Extra metadata


# AI Service Interface
class AIServiceInterface(ABC):
    """Interface voor AI service implementaties met async support."""

    @abstractmethod
    async def generate_definition(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str | None = None,
        system_prompt: str | None = None,
        timeout_seconds: int = 30,
    ) -> AIGenerationResult:
        """
        Genereer een definitie met AI op basis van de gegeven prompt.

        Deze methode roept het AI model aan met de opgegeven parameters
        en retourneert een gestructureerd resultaat met metadata.

        Args:
            prompt: De prompt voor het AI model
            temperature: Creativiteit parameter (0.0 = deterministisch, 1.0 = creatief)
            max_tokens: Maximum aantal tokens in de response
            model: Optioneel specifiek model om te gebruiken
            system_prompt: Optionele system prompt voor context
            timeout_seconds: Timeout voor de AI call

        Returns:
            AIGenerationResult met gegenereerde tekst en metadata

        Raises:
            AIServiceError: Bij fouten in de AI service (rate limits, timeouts, etc.)
        """

    @abstractmethod
    async def batch_generate(
        self, requests: list[AIBatchRequest]
    ) -> list[AIGenerationResult]:
        """
        Voer meerdere AI generatie requests parallel uit.

        Deze methode optimaliseert batch verwerking door parallelle
        uitvoering waar mogelijk, met respect voor rate limits.

        Args:
            requests: Lijst van AIBatchRequest objecten

        Returns:
            Lijst van AIGenerationResult objecten in dezelfde volgorde

        Raises:
            AIServiceError: Bij fouten in de AI service
        """


# AI Service Exceptions
class AIServiceError(Exception):
    """Base exception voor AI service fouten."""


class AIRateLimitError(AIServiceError):
    """Exception voor rate limit overschrijdingen."""


class AITimeoutError(AIServiceError):
    """Exception voor timeout fouten."""


# ==========================================


# (Verplaatst naar Appendix in SA document – geen codewijzigingen nu)


@dataclass
class PromptResult:
    """Enhanced prompt result with feedback integration."""

    text: str
    token_count: int
    components_used: list[str]
    feedback_integrated: bool
    optimization_applied: bool
    metadata: dict[str, Any]


# Prompt Service V2 Interfaces
class PromptServiceInterface(ABC):
    """Interface voor prompt building services met V2 features."""

    @abstractmethod
    async def build_generation_prompt(
        self,
        request: GenerationRequest,
        feedback_history: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> PromptResult:
        """
        Bouw een geoptimaliseerde prompt voor definitie generatie.

        Args:
            request: GenerationRequest met begrip en context
            feedback_history: Historische feedback voor optimalisatie
            context: Extra context informatie

        Returns:
            PromptResult met gestructureerde prompt informatie
        """

    @abstractmethod
    async def optimize_prompt(self, prompt: str, max_tokens: int) -> str:
        """
        Optimaliseer een prompt binnen token limieten.

        Args:
            prompt: Originele prompt
            max_tokens: Maximum aantal tokens

        Returns:
            Geoptimaliseerde prompt
        """


# Validation Service V2 Interface
class ValidationServiceInterface(ABC):
    """Interface voor async definitie validatie met V2 features."""

    @abstractmethod
    async def validate_definition(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Valideer een definitie async volgens alle regels.

        Args:
            begrip: Het begrip dat gedefinieerd wordt
            text: De definitie tekst
            ontologische_categorie: Optionele categorie
            context: Extra validatie context

        Returns:
            ValidationResult met validatie details
        """

    @abstractmethod
    async def batch_validate(
        self, definitions: list[tuple[str, str]]
    ) -> list[ValidationResult]:
        """
        Valideer meerdere definities tegelijk.

        Args:
            definitions: Lijst van (begrip, definitie) tuples

        Returns:
            Lijst van ValidationResult objecten
        """


# Enhancement Service Interface
class EnhancementServiceInterface(ABC):
    """Interface voor definitie verrijking services."""

    @abstractmethod
    async def enhance_definition(
        self,
        text: str,
        violations: list[ValidationViolation],  # Concrete type voor betere type safety
        context: GenerationRequest,
    ) -> str:
        """
        Verbeter een definitie op basis van validatie violations.

        Args:
            text: De definitie tekst om te verbeteren
            violations: Lijst van validatie violations
            context: Originele GenerationRequest voor context

        Returns:
            Verbeterde definitie tekst
        """

    @abstractmethod
    async def generate_examples(
        self, begrip: str, definitie: str, aantal: int = 3
    ) -> list[str]:
        """
        Genereer voorbeelden voor een definitie.

        Args:
            begrip: Het begrip
            definitie: De definitie tekst
            aantal: Aantal voorbeelden om te genereren

        Returns:
            Lijst van gegenereerde voorbeelden
        """


# Security Service Interface
class SecurityServiceInterface(ABC):
    """Interface voor security en privacy services."""

    @abstractmethod
    async def sanitize_request(self, request: GenerationRequest) -> GenerationRequest:
        """
        Sanitize een request voor DPIA/AVG compliance.

        Args:
            request: Te sanitizen GenerationRequest

        Returns:
            Gesanitized GenerationRequest
        """

    @abstractmethod
    async def redact_pii(self, text: str, redaction_level: str = "medium") -> str:
        """
        Verwijder persoonlijk identificeerbare informatie uit tekst.

        Args:
            text: Te redacteren tekst
            redaction_level: Niveau van redactie (low/medium/high)

        Returns:
            Geredacteerde tekst
        """

    @abstractmethod
    async def validate_compliance(
        self, definition: Definition, compliance_rules: list[str] | None = None
    ) -> dict[str, bool]:
        """
        Valideer compliance met privacy regels.

        Args:
            definition: Te valideren definitie
            compliance_rules: Specifieke regels om te checken

        Returns:
            Dictionary met compliance status per regel
        """


# Monitoring Service Interface
class MonitoringServiceInterface(ABC):
    """Interface voor monitoring en metrics services."""

    @abstractmethod
    async def start_generation(self, generation_id: str) -> None:
        """
        Start tracking van een generatie operatie.

        Args:
            generation_id: Unieke generatie identifier
        """

    @abstractmethod
    async def complete_generation(
        self,
        generation_id: str,
        success: bool,
        duration: float,
        token_count: int | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Markeer een generatie als compleet met metrics.

        Args:
            generation_id: Unieke generatie identifier
            success: Of generatie succesvol was
            duration: Duur in seconden
            token_count: Aantal gebruikte tokens
            **kwargs: Extra metrics
        """

    @abstractmethod
    async def track_error(
        self, generation_id: str, error: Exception, error_type: str | None = None
    ) -> None:
        """
        Track een error tijdens generatie.

        Args:
            generation_id: Unieke generatie identifier
            error: De opgetreden error
            error_type: Optioneel error type
        """

    @abstractmethod
    def get_metrics_summary(
        self, time_range: tuple[datetime, datetime] | None = None
    ) -> dict[str, Any]:
        """
        Haal metrics samenvatting op.

        Args:
            time_range: Optioneel tijdsbereik

        Returns:
            Dictionary met metrics samenvatting
        """


# Feedback Engine Interface
class FeedbackEngineInterface(ABC):
    """Interface voor feedback processing en integratie."""

    @abstractmethod
    async def get_feedback_for_request(
        self, begrip: str, categorie: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Haal relevante feedback op voor een request.

        Args:
            begrip: Het begrip waarvoor feedback gezocht wordt
            categorie: Optionele ontologische categorie

        Returns:
            Lijst van relevante feedback items
        """

    @abstractmethod
    async def process_validation_feedback(
        self,
        definition_id: str,
        validation_result: ValidationResult,
        original_request: GenerationRequest,
    ) -> dict[str, Any]:
        """
        Verwerk validatie feedback voor toekomstig gebruik.

        Args:
            definition_id: ID van de definitie
            validation_result: Validatie resultaat
            original_request: Originele generatie request

        Returns:
            Verwerkte feedback resultaat
        """

    @abstractmethod
    async def process_feedback(
        self,
        definition_id: str,
        feedback_type: str,
        feedback_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Verwerk algemene gebruikersfeedback voor een definitie.

        Args:
            definition_id: ID van de definitie
            feedback_type: Type feedback (quality/accuracy/etc)
            feedback_content: Feedback inhoud
            metadata: Extra metadata

        Returns:
            Verwerkte feedback resultaat
        """

    @abstractmethod
    async def get_feedback_history(
        self, definition_id: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Haal feedback geschiedenis op.

        Args:
            definition_id: Optioneel filter op definitie ID
            limit: Maximum aantal resultaten

        Returns:
            Lijst van feedback items
        """


# ==========================================


@dataclass
class OrchestratorConfig:
    """Configuration for DefinitionOrchestratorV2 behavior."""

    enable_feedback_loop: bool = True
    enable_enhancement: bool = True
    enable_caching: bool = True
    enable_web_lookup: bool = True
    web_lookup_top_k: int = 3
    max_retries: int = 3
    timeout_seconds: int = 30


@dataclass
class PromptServiceConfig:
    """Configuration for prompt service behavior."""

    max_token_limit: int = 10000  # Hard limit
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    feedback_integration: bool = True
    token_optimization: bool = True


# Enhanced DefinitionResponse for V2
@dataclass
class DefinitionResponseV2:
    """Enhanced response object voor V2 orchestrator."""

    success: bool = True
    definition: Definition | None = None
    validation_result: ValidationResult | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
