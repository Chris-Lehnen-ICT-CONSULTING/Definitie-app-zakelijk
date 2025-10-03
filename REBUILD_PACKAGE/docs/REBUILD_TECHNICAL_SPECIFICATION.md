# TECHNICAL SPECIFICATION: DefinitieAgent Rebuild

**Version:** 1.0
**Status:** Draft for Review
**Date:** 2025-10-02
**Target Audience:** Single Developer
**Expected Codebase:** 25k LOC (vs 83k current)
**Performance Target:** <2s generation (vs 8-12s current)

---

## Executive Summary

This document provides comprehensive technical specifications for rebuilding DefinitieAgent from scratch using modern patterns and eliminating 70% of code bloat. The rebuild focuses on:

- **Clean Architecture** with proper separation of concerns
- **Service-oriented design** with explicit contracts
- **Performance first** - sub-2s generation time
- **Developer experience** - clear patterns, no god objects
- **Production ready** - proper error handling, logging, monitoring

**Key Metrics:**
- Current: 321 Python files, 83k LOC, 8-12s response time
- Target: ~100 files, 25k LOC, <2s response time
- Reduction: 70% less code, 80% faster

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Service Specifications](#2-service-specifications)
3. [Data Model Specification](#3-data-model-specification)
4. [API Design](#4-api-design)
5. [Code Quality Standards](#5-code-quality-standards)
6. [Implementation Guidelines](#6-implementation-guidelines)
7. [Quality Gates](#7-quality-gates)
8. [Testing Requirements](#8-testing-requirements)
9. [Performance Specifications](#9-performance-specifications)
10. [Security Requirements](#10-security-requirements)

---

## 1. Architecture Overview

### 1.1 Architectural Principles

**PRINCIPLE 1: Clean Architecture**
```
UI Layer (Streamlit)
    ↓ (calls)
Application Layer (Use Cases/Orchestrators)
    ↓ (calls)
Domain Layer (Business Logic/Services)
    ↓ (calls)
Infrastructure Layer (Database/External APIs)
```

**PRINCIPLE 2: No Session State in Business Logic**
- Services MUST be stateless
- All state passed as parameters
- Testable without UI framework

**PRINCIPLE 3: Explicit Dependencies**
- Use dependency injection
- No hidden coupling
- Clear service boundaries

**PRINCIPLE 4: Single Responsibility**
- One service = one concern
- No god objects
- No "helper" modules with mixed responsibilities

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     UI Layer                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐            │
│  │ Generator │ │ Validator │ │ History   │            │
│  │ Tab       │ │ Tab       │ │ Tab       │            │
│  └───────────┘ └───────────┘ └───────────┘            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Application Layer                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  DefinitionOrchestrator (Use Case Coordinator)   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│               Domain Services                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Generator │ │Validator │ │ Enricher │ │Repository│  │
│  │Service   │ │Service   │ │ Service  │ │Service   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│            Infrastructure Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ OpenAI   │ │SQLite/   │ │Wikipedia │               │
│  │ Client   │ │Postgres  │ │  SRU     │               │
│  └──────────┘ └──────────┘ └──────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 1.3 Service Boundaries

| Service | Responsibility | Dependencies |
|---------|---------------|--------------|
| **DefinitionOrchestrator** | Coordinate generation flow | All domain services |
| **GeneratorService** | AI prompt + call OpenAI | PromptBuilder, AIClient |
| **ValidationService** | Run 45 validation rules | RuleEngine, Repository |
| **EnrichmentService** | Add examples, synonyms | AIClient, WebLookup |
| **RepositoryService** | Data persistence | Database |
| **PromptBuilder** | Construct AI prompts | RuleRegistry |
| **AIClient** | OpenAI API wrapper | None (infrastructure) |
| **WebLookupService** | External data sources | Wikipedia, SRU APIs |

---

## 2. Service Specifications

### 2.1 DefinitionOrchestrator

**Purpose:** Coordinate the complete definition generation flow

**Contract:**
```python
from dataclasses import dataclass
from typing import Protocol, List, Optional
from enum import Enum

class GenerationPhase(Enum):
    """Phases of definition generation"""
    CONTEXT_VALIDATION = "context_validation"
    PROMPT_BUILDING = "prompt_building"
    AI_GENERATION = "ai_generation"
    POST_PROCESSING = "post_processing"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"
    PERSISTENCE = "persistence"

@dataclass
class GenerationRequest:
    """Input for definition generation"""
    term: str
    organisatorische_context: List[str]
    juridische_context: List[str]
    wettelijke_basis: List[str]

    # Optional parameters
    include_examples: bool = True
    include_synonyms: bool = True
    target_length: int = 300  # characters
    user_id: Optional[str] = None

@dataclass
class GenerationResult:
    """Output of definition generation"""
    success: bool
    definition_id: Optional[int]
    definition_text: str

    # Quality metrics
    validation_score: float
    validation_feedback: List[str]

    # Metadata
    generation_time_ms: int
    tokens_used: int
    model_used: str
    phases_completed: List[GenerationPhase]

    # Optional enrichments
    examples: Optional[List[str]] = None
    synonyms: Optional[List[str]] = None

    # Error information
    error_message: Optional[str] = None
    error_phase: Optional[GenerationPhase] = None

class DefinitionOrchestrator(Protocol):
    """Orchestrator for definition generation workflow"""

    async def generate_definition(
        self,
        request: GenerationRequest
    ) -> GenerationResult:
        """
        Generate a complete definition with validation and enrichment.

        Flow:
        1. Validate context inputs
        2. Build AI prompt from request
        3. Call AI service for generation
        4. Post-process and clean output
        5. Validate against 45 rules
        6. Optionally enrich with examples/synonyms
        7. Save to repository
        8. Return complete result

        Args:
            request: Generation request with term and context

        Returns:
            GenerationResult with definition, validation, metadata

        Raises:
            ValidationError: Invalid input context
            ServiceError: Generation failed
            RateLimitError: API quota exceeded
        """
        ...

    async def regenerate_definition(
        self,
        definition_id: int,
        feedback: str
    ) -> GenerationResult:
        """
        Regenerate definition incorporating feedback.

        Args:
            definition_id: ID of definition to regenerate
            feedback: User feedback to incorporate

        Returns:
            GenerationResult with improved definition
        """
        ...
```

**Implementation Requirements:**
- Each phase MUST be independently testable
- MUST track metrics for each phase
- MUST support graceful degradation (skip enrichment if WebLookup fails)
- MUST use circuit breaker for external services
- Total generation time target: <2000ms

**Error Handling:**
```python
class OrchestratorError(Exception):
    """Base error for orchestrator"""
    phase: GenerationPhase
    recoverable: bool

class ContextValidationError(OrchestratorError):
    """Invalid context provided"""
    phase = GenerationPhase.CONTEXT_VALIDATION
    recoverable = False

class AIGenerationError(OrchestratorError):
    """AI service failed"""
    phase = GenerationPhase.AI_GENERATION
    recoverable = True  # Can retry
```

### 2.2 GeneratorService

**Purpose:** AI prompt construction and OpenAI interaction

**Contract:**
```python
@dataclass
class PromptContext:
    """Context for prompt generation"""
    term: str
    contexts: Dict[str, List[str]]  # org, jur, wet
    validation_rules: List[str]  # Active rule IDs
    target_length: int = 300

@dataclass
class AIRequest:
    """Request to AI service"""
    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AIResponse:
    """Response from AI service"""
    text: str
    tokens_used: int
    model: str
    finish_reason: str
    latency_ms: int

class GeneratorService(Protocol):
    """AI-powered definition generator"""

    async def generate(
        self,
        context: PromptContext
    ) -> AIResponse:
        """
        Generate definition using AI.

        Steps:
        1. Build prompt from context
        2. Add validation rules to prompt
        3. Call OpenAI API
        4. Parse and validate response

        Args:
            context: Prompt context

        Returns:
            AIResponse with generated text

        Raises:
            PromptBuildError: Failed to build prompt
            AIServiceError: OpenAI API error
            RateLimitError: Quota exceeded
        """
        ...
```

**Performance Requirements:**
- Prompt construction: <50ms
- AI call (including network): <1500ms
- Token optimization: ≤2000 tokens per prompt
- Caching: Same context = cached response (1 hour TTL)

**Prompt Structure:**
```python
class PromptBuilder:
    """Builds optimized prompts"""

    TEMPLATE = """Je bent een juridische definitie-expert.

TAAK: Genereer een precieze definitie voor: {term}

CONTEXT:
{context_block}

VALIDATIEREGELS (TOP 10):
{validation_rules}

FORMAAT:
- 1 zin, max {max_length} tekens
- B1 taalniveau
- Geen circulaire definities
- Actieve zinsvorm

Definitie:"""

    def build(self, context: PromptContext) -> str:
        """Build prompt with token optimization"""
        # Select top 10 most relevant rules (not all 45!)
        top_rules = self._select_relevant_rules(
            context.validation_rules,
            limit=10
        )

        return self.TEMPLATE.format(
            term=context.term,
            context_block=self._format_context(context.contexts),
            validation_rules=self._format_rules(top_rules),
            max_length=context.target_length
        )
```

### 2.3 ValidationService

**Purpose:** Execute 45 validation rules against definitions

**Contract:**
```python
from enum import Enum
from typing import List, Dict

class RuleSeverity(Enum):
    ERROR = "error"      # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"        # Nice to have

class RuleCategory(Enum):
    ARAI = "ARAI"  # Afbakening, Relevantie, Authenticiteit
    CON = "CON"    # Consistentie
    ESS = "ESS"    # Essentie
    INT = "INT"    # Integriteit
    SAM = "SAM"    # Samenhang
    STR = "STR"    # Structuur
    VER = "VER"    # Verstaanbaarheid

@dataclass
class ValidationIssue:
    """Single validation issue"""
    rule_id: str
    category: RuleCategory
    severity: RuleSeverity
    message: str
    suggestion: Optional[str] = None
    score: float = 0.0  # 0.0 = fail, 1.0 = pass

@dataclass
class ValidationResult:
    """Complete validation result"""
    overall_score: float  # 0.0 - 1.0
    passed: bool  # True if score >= threshold
    issues: List[ValidationIssue]
    rules_executed: int
    execution_time_ms: int

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Check if validation passes threshold"""
        return self.overall_score >= threshold

class ValidationRule(Protocol):
    """Protocol for validation rules"""

    rule_id: str
    category: RuleCategory
    severity: RuleSeverity
    description: str

    async def validate(
        self,
        definition: str,
        context: PromptContext
    ) -> ValidationIssue:
        """
        Validate definition against this rule.

        Args:
            definition: Text to validate
            context: Generation context

        Returns:
            ValidationIssue with score and feedback
        """
        ...

class ValidationService(Protocol):
    """Validation orchestrator"""

    async def validate(
        self,
        definition: str,
        context: PromptContext,
        rules: Optional[List[str]] = None  # None = all rules
    ) -> ValidationResult:
        """
        Validate definition against rules.

        Args:
            definition: Text to validate
            context: Generation context
            rules: Specific rule IDs (None = all active rules)

        Returns:
            ValidationResult with overall score and issues

        Raises:
            ValidationError: Critical validation failure
        """
        ...
```

**Performance Requirements:**
- Execute ALL 45 rules in <300ms
- Use async/parallel execution
- Cache rule results (definition hash → results)
- Early exit on critical failures

**Rule Implementation Pattern:**
```python
class ARAI01Rule(ValidationRule):
    """No circular definitions"""

    rule_id = "ARAI-01"
    category = RuleCategory.ARAI
    severity = RuleSeverity.ERROR
    description = "Definitie mag geen circulaire verwijzing bevatten"

    async def validate(
        self,
        definition: str,
        context: PromptContext
    ) -> ValidationIssue:
        """Check for circular reference"""
        term_lower = context.term.lower()
        definition_lower = definition.lower()

        # Simple check: term in definition
        if term_lower in definition_lower:
            return ValidationIssue(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                message=f"Circulaire definitie gedetecteerd: '{context.term}' komt voor in definitie",
                suggestion="Herformuleer zonder de term zelf te gebruiken",
                score=0.0
            )

        return ValidationIssue(
            rule_id=self.rule_id,
            category=self.category,
            severity=self.severity,
            message="Geen circulaire verwijzing gedetecteerd",
            score=1.0
        )
```

**Rule Organization:**
```
src/validation/
├── rules/
│   ├── arai/
│   │   ├── arai_01.py  # Circular definitions
│   │   ├── arai_02.py  # Relevance check
│   │   └── ...
│   ├── con/
│   │   ├── con_01.py
│   │   └── ...
│   ├── ess/
│   ├── int/
│   ├── sam/
│   ├── str/
│   └── ver/
├── engine.py         # Validation orchestrator
├── registry.py       # Rule registration
└── protocols.py      # Shared interfaces
```

### 2.4 RepositoryService

**Purpose:** Data persistence with proper abstractions

**Contract:**
```python
@dataclass
class Definition:
    """Domain model for definition"""
    id: Optional[int]
    term: str
    definition_text: str

    # Context
    organisatorische_context: List[str]
    juridische_context: List[str]
    wettelijke_basis: List[str]

    # Metadata
    category: str
    status: str  # draft, review, established, archived
    validation_score: float

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Optional enrichments
    examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)

class RepositoryService(Protocol):
    """Data persistence abstraction"""

    async def save(self, definition: Definition) -> int:
        """
        Save definition to database.

        Args:
            definition: Definition to save

        Returns:
            ID of saved definition

        Raises:
            DuplicateError: Definition already exists
            ValidationError: Invalid data
        """
        ...

    async def get_by_id(self, definition_id: int) -> Optional[Definition]:
        """Retrieve definition by ID"""
        ...

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[Definition]:
        """
        Search definitions.

        Args:
            query: Search term
            filters: Optional filters (status, category, etc)
            limit: Max results

        Returns:
            List of matching definitions
        """
        ...

    async def check_duplicate(
        self,
        term: str,
        context: Dict[str, List[str]]
    ) -> Optional[Definition]:
        """
        Check for duplicate definition.

        Uses semantic similarity, not exact match.

        Args:
            term: Term to check
            context: Context to compare

        Returns:
            Existing definition if duplicate found, else None
        """
        ...
```

**Implementation Requirements:**
- Support both SQLite (dev) and PostgreSQL (prod)
- Use SQLAlchemy Core (not ORM for performance)
- Connection pooling enabled
- Query timeout: 100ms max
- Proper indexing on term, status, contexts

**Database Schema (simplified):**
```sql
CREATE TABLE definitions (
    id SERIAL PRIMARY KEY,
    term VARCHAR(255) NOT NULL,
    definition_text TEXT NOT NULL,

    -- Context as JSON arrays
    organisatorische_context JSONB NOT NULL DEFAULT '[]',
    juridische_context JSONB NOT NULL DEFAULT '[]',
    wettelijke_basis JSONB NOT NULL DEFAULT '[]',

    -- Metadata
    category VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    validation_score DECIMAL(3,2),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('dutch', term || ' ' || definition_text)
    ) STORED
);

-- Indexes
CREATE INDEX idx_definitions_term ON definitions(term);
CREATE INDEX idx_definitions_status ON definitions(status);
CREATE INDEX idx_definitions_search ON definitions USING GIN(search_vector);
CREATE INDEX idx_definitions_context ON definitions USING GIN(organisatorische_context);
```

---

## 3. Data Model Specification

### 3.1 Domain Models

**Core Entities:**

```python
# Domain models (pure Python, no framework coupling)

@dataclass(frozen=True)
class Term:
    """Value object for terms"""
    value: str

    def __post_init__(self):
        if not 2 <= len(self.value) <= 200:
            raise ValueError("Term must be 2-200 characters")

    def normalized(self) -> str:
        """Get normalized term for comparison"""
        return self.value.lower().strip()

@dataclass
class Context:
    """Value object for context"""
    organisatorisch: List[str]
    juridisch: List[str]
    wettelijk: List[str]

    def __post_init__(self):
        # Validate context
        if not any([self.organisatorisch, self.juridisch, self.wettelijk]):
            raise ValueError("At least one context field required")

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "organisatorisch": self.organisatorisch,
            "juridisch": self.juridisch,
            "wettelijk": self.wettelijk
        }

@dataclass
class ValidationState:
    """Aggregate validation state"""
    score: float
    passed: bool
    issues: List[ValidationIssue]
    timestamp: datetime

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == RuleSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == RuleSeverity.WARNING)

@dataclass
class Definition:
    """Aggregate root for definition"""
    id: Optional[int]
    term: Term
    text: str
    context: Context
    category: str
    status: str
    validation: Optional[ValidationState]

    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    # Enrichments
    examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)

    def is_established(self) -> bool:
        """Check if definition is established"""
        return self.status == "established"

    def can_be_established(self) -> bool:
        """Check if definition can transition to established"""
        return (
            self.status == "review" and
            self.validation is not None and
            self.validation.passed and
            self.validation.error_count == 0
        )
```

### 3.2 Data Transfer Objects (DTOs)

**API Layer DTOs:**

```python
# DTOs for API boundaries (JSON serializable)

@dataclass
class GenerationRequestDTO:
    """DTO for API requests"""
    term: str
    organisatorische_context: List[str]
    juridische_context: List[str]
    wettelijke_basis: List[str]

    # Optional
    include_examples: bool = True
    include_synonyms: bool = True

    def to_domain(self) -> GenerationRequest:
        """Convert to domain model"""
        return GenerationRequest(
            term=self.term,
            organisatorische_context=self.organisatorische_context,
            juridische_context=self.juridische_context,
            wettelijke_basis=self.wettelijke_basis,
            include_examples=self.include_examples,
            include_synonyms=self.include_synonyms
        )

@dataclass
class DefinitionDTO:
    """DTO for API responses"""
    id: int
    term: str
    definition: str
    context: Dict[str, List[str]]
    status: str
    validation_score: float
    created_at: str  # ISO format

    @classmethod
    def from_domain(cls, definition: Definition) -> "DefinitionDTO":
        """Convert from domain model"""
        return cls(
            id=definition.id,
            term=definition.term.value,
            definition=definition.text,
            context=definition.context.to_dict(),
            status=definition.status,
            validation_score=definition.validation.score if definition.validation else 0.0,
            created_at=definition.created_at.isoformat()
        )
```

### 3.3 Database Models

**SQLAlchemy Models:**

```python
from sqlalchemy import Table, Column, Integer, String, Text, DECIMAL, TIMESTAMP, JSON
from sqlalchemy.sql import func

metadata = MetaData()

definitions_table = Table(
    'definitions',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('term', String(255), nullable=False, index=True),
    Column('definition_text', Text, nullable=False),

    # Context as JSON
    Column('organisatorische_context', JSON, nullable=False, default=list),
    Column('juridische_context', JSON, nullable=False, default=list),
    Column('wettelijke_basis', JSON, nullable=False, default=list),

    # Metadata
    Column('category', String(50), nullable=False),
    Column('status', String(50), nullable=False, default='draft', index=True),
    Column('validation_score', DECIMAL(3, 2)),

    # Timestamps
    Column('created_at', TIMESTAMP, nullable=False, server_default=func.now()),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()),
    Column('created_by', String(255)),

    # Enrichments (stored as JSON for simplicity)
    Column('examples', JSON, default=list),
    Column('synonyms', JSON, default=list)
)
```

---

## 4. API Design

### 4.1 REST API Endpoints

**Base URL:** `/api/v1`

**Endpoints:**

```python
# Definitions
POST   /definitions              # Create new definition
GET    /definitions/{id}         # Get definition by ID
GET    /definitions/search       # Search definitions
PATCH  /definitions/{id}         # Update definition
DELETE /definitions/{id}         # Delete definition
POST   /definitions/{id}/regenerate  # Regenerate with feedback

# Validation
POST   /validate                 # Validate text
GET    /validation/rules         # Get active rules

# Export/Import
POST   /export                   # Export definitions
POST   /import                   # Import definitions batch

# Health
GET    /health                   # Health check
GET    /metrics                  # Prometheus metrics
```

**Request/Response Examples:**

```json
// POST /definitions
{
  "term": "verdachte",
  "organisatorische_context": ["OM", "Politie"],
  "juridische_context": ["Strafrecht"],
  "wettelijke_basis": ["Sv"],
  "include_examples": true
}

// Response 201 Created
{
  "id": 123,
  "term": "verdachte",
  "definition": "Persoon tegen wie een redelijk vermoeden bestaat van schuld aan een strafbaar feit",
  "context": {
    "organisatorisch": ["OM", "Politie"],
    "juridisch": ["Strafrecht"],
    "wettelijk": ["Sv"]
  },
  "status": "draft",
  "validation": {
    "score": 0.85,
    "passed": true,
    "issues": [
      {
        "rule_id": "VER-02",
        "severity": "warning",
        "message": "Overweeg kortere zin"
      }
    ]
  },
  "examples": [
    "De verdachte werd aangehouden op heterdaad"
  ],
  "created_at": "2025-10-02T10:30:00Z",
  "generation_time_ms": 1250
}
```

### 4.2 FastAPI Implementation

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional

app = FastAPI(
    title="DefinitieAgent API",
    version="2.0.0",
    description="AI-powered legal definition generation"
)

# Dependency injection
def get_orchestrator() -> DefinitionOrchestrator:
    """Get orchestrator instance"""
    return container.orchestrator()

# Endpoints
@app.post("/api/v1/definitions", status_code=201)
async def create_definition(
    request: GenerationRequestDTO,
    orchestrator: DefinitionOrchestrator = Depends(get_orchestrator)
) -> DefinitionDTO:
    """
    Generate new definition.

    Returns:
        DefinitionDTO with generated content

    Raises:
        400: Invalid input
        429: Rate limit exceeded
        500: Generation failed
    """
    try:
        result = await orchestrator.generate_definition(request.to_domain())

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=result.error_message
            )

        # Convert to DTO
        definition = await repository.get_by_id(result.definition_id)
        return DefinitionDTO.from_domain(definition)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))

@app.get("/api/v1/definitions/search")
async def search_definitions(
    q: str,
    status: Optional[str] = None,
    limit: int = 20,
    repository: RepositoryService = Depends(get_repository)
) -> List[DefinitionDTO]:
    """
    Search definitions.

    Query parameters:
        q: Search query
        status: Filter by status (draft, review, established)
        limit: Max results (default 20)
    """
    filters = {}
    if status:
        filters['status'] = status

    definitions = await repository.search(q, filters, limit)
    return [DefinitionDTO.from_domain(d) for d in definitions]

# Error handlers
@app.exception_handler(OrchestratorError)
async def orchestrator_error_handler(request, exc: OrchestratorError):
    """Handle orchestrator errors"""
    return JSONResponse(
        status_code=500 if not exc.recoverable else 503,
        content={
            "error": exc.__class__.__name__,
            "phase": exc.phase.value,
            "message": str(exc),
            "recoverable": exc.recoverable
        }
    )
```

---

## 5. Code Quality Standards

### 5.1 Coding Conventions

**Python Style:**
- Follow PEP 8 strictly
- Use Black formatter (line length: 88)
- Use Ruff linter
- 100% type hints coverage

**Type Hints Example:**
```python
# GOOD
async def generate_definition(
    self,
    request: GenerationRequest
) -> GenerationResult:
    """Generate definition with full typing"""
    ...

# BAD
def generate_definition(self, request):
    """No type hints"""
    ...
```

**Naming Conventions:**
```python
# Classes: PascalCase
class DefinitionOrchestrator:
    pass

# Functions/methods: snake_case
def generate_definition():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private: prefix with _
def _internal_helper():
    pass
```

### 5.2 Documentation Standards

**Module Docstrings:**
```python
"""
Definition generation orchestration.

This module coordinates the complete flow of definition generation,
from input validation through AI generation to enrichment and storage.

Key components:
    - DefinitionOrchestrator: Main orchestration logic
    - GenerationPhase: Enum of generation phases
    - GenerationResult: Output dataclass

Usage:
    orchestrator = DefinitionOrchestrator(services...)
    result = await orchestrator.generate_definition(request)
"""
```

**Function Docstrings (Google Style):**
```python
async def generate_definition(
    self,
    request: GenerationRequest
) -> GenerationResult:
    """
    Generate complete definition with validation and enrichment.

    This method orchestrates the full generation pipeline including
    context validation, AI generation, validation against rules,
    and optional enrichment with examples.

    Args:
        request: Generation request containing term and context.
            Must include at least one context field.

    Returns:
        GenerationResult containing:
            - Generated definition text
            - Validation score and feedback
            - Enrichments (if requested)
            - Performance metrics

    Raises:
        ValidationError: Invalid input context
        AIServiceError: OpenAI API call failed
        RateLimitError: API quota exceeded

    Example:
        >>> request = GenerationRequest(
        ...     term="verdachte",
        ...     organisatorische_context=["OM"],
        ...     juridische_context=["Strafrecht"],
        ...     wettelijke_basis=["Sv"]
        ... )
        >>> result = await orchestrator.generate_definition(request)
        >>> print(result.definition_text)
        "Persoon tegen wie een redelijk vermoeden bestaat..."
    """
```

### 5.3 Error Handling Standards

**Exception Hierarchy:**
```python
class DefinitieAgentError(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(DefinitieAgentError):
    """Input validation failed"""
    pass

class ServiceError(DefinitieAgentError):
    """Service-level error"""
    pass

class AIServiceError(ServiceError):
    """AI service (OpenAI) error"""
    pass

class RateLimitError(AIServiceError):
    """Rate limit exceeded"""
    pass
```

**Error Handling Pattern:**
```python
# Use try-except with specific exceptions
try:
    result = await ai_service.generate(prompt)
except RateLimitError:
    # Specific handling for rate limits
    await asyncio.sleep(60)
    result = await ai_service.generate(prompt)
except AIServiceError as e:
    # Log and re-raise
    logger.error(f"AI service failed: {e}", extra=e.details)
    raise
except Exception as e:
    # Catch-all for unexpected errors
    logger.exception("Unexpected error")
    raise ServiceError(f"Unexpected error: {e}")
```

### 5.4 Testing Standards

**Test Structure:**
```python
class TestDefinitionOrchestrator:
    """Tests for DefinitionOrchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked dependencies"""
        return DefinitionOrchestrator(
            generator=Mock(spec=GeneratorService),
            validator=Mock(spec=ValidationService),
            repository=Mock(spec=RepositoryService)
        )

    @pytest.mark.asyncio
    async def test_generate_definition_success(self, orchestrator):
        """Should generate definition successfully"""
        # Arrange
        request = GenerationRequest(
            term="test",
            organisatorische_context=["OM"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Sv"]
        )

        # Act
        result = await orchestrator.generate_definition(request)

        # Assert
        assert result.success
        assert result.definition_text
        assert result.validation_score >= 0.7

    @pytest.mark.asyncio
    async def test_generate_definition_validation_error(self, orchestrator):
        """Should raise ValidationError for invalid input"""
        # Arrange
        request = GenerationRequest(
            term="",  # Invalid: empty term
            organisatorische_context=[],
            juridische_context=[],
            wettelijke_basis=[]
        )

        # Act & Assert
        with pytest.raises(ValidationError):
            await orchestrator.generate_definition(request)
```

**Test Coverage Requirements:**
- Unit tests: ≥80% line coverage
- Integration tests: All service boundaries
- E2E tests: Critical user flows
- Performance tests: <2s target validation

---

## 6. Implementation Guidelines

### 6.1 Service Implementation Pattern

**Standard Service Structure:**
```python
# src/services/generator_service.py

import logging
from typing import Protocol
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 1. Define protocols/interfaces
class GeneratorService(Protocol):
    async def generate(self, context: PromptContext) -> AIResponse:
        ...

# 2. Implementation class
class OpenAIGeneratorService:
    """AI generator using OpenAI"""

    def __init__(
        self,
        ai_client: AIClient,
        prompt_builder: PromptBuilder,
        config: GeneratorConfig
    ):
        """Initialize with dependencies"""
        self.ai_client = ai_client
        self.prompt_builder = prompt_builder
        self.config = config
        self._metrics = MetricsCollector()

    async def generate(
        self,
        context: PromptContext
    ) -> AIResponse:
        """Generate definition using AI"""
        start_time = time.time()

        try:
            # 1. Build prompt
            prompt = self.prompt_builder.build(context)
            logger.debug(f"Built prompt ({len(prompt)} chars)")

            # 2. Call AI
            ai_request = AIRequest(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            response = await self.ai_client.complete(ai_request)

            # 3. Track metrics
            duration_ms = int((time.time() - start_time) * 1000)
            self._metrics.track_generation(
                model=ai_request.model,
                tokens=response.tokens_used,
                duration_ms=duration_ms
            )

            logger.info(
                f"Generated definition ({response.tokens_used} tokens, {duration_ms}ms)"
            )

            return response

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            self._metrics.track_error(type(e).__name__)
            raise AIServiceError(
                f"Failed to generate: {e}",
                details={"context": context}
            )
```

### 6.2 Validation Rules Implementation

**Rule Template:**
```python
# src/validation/rules/arai/arai_01.py

from validation.protocols import ValidationRule
from validation.types import RuleCategory, RuleSeverity, ValidationIssue

class CircularDefinitionRule(ValidationRule):
    """
    ARAI-01: No circular definitions.

    A definition should not include the term being defined,
    as this creates a circular reference.

    Examples:
        BAD:  "Een verdachte is iemand die verdacht wordt"
        GOOD: "Een verdachte is iemand tegen wie een vermoeden bestaat"
    """

    rule_id = "ARAI-01"
    category = RuleCategory.ARAI
    severity = RuleSeverity.ERROR
    description = "Definitie mag geen circulaire verwijzing bevatten"

    async def validate(
        self,
        definition: str,
        context: PromptContext
    ) -> ValidationIssue:
        """Check for circular reference"""
        term_lower = context.term.lower()
        definition_lower = definition.lower()

        # Check if term appears in definition
        # (excluding common variations like plurals)
        if self._contains_term(definition_lower, term_lower):
            return ValidationIssue(
                rule_id=self.rule_id,
                category=self.category,
                severity=self.severity,
                message=f"Circulaire definitie: '{context.term}' komt voor in definitie",
                suggestion="Herformuleer zonder de term zelf te gebruiken",
                score=0.0
            )

        return ValidationIssue(
            rule_id=self.rule_id,
            category=self.category,
            severity=self.severity,
            message="Geen circulaire verwijzing",
            score=1.0
        )

    def _contains_term(self, definition: str, term: str) -> bool:
        """Check if definition contains term (smart matching)"""
        # Simple word boundary check
        import re
        pattern = r'\b' + re.escape(term) + r'\b'
        return bool(re.search(pattern, definition))

# Registration
RULES = [CircularDefinitionRule()]
```

### 6.3 Prompt Engineering Best Practices

**Prompt Structure:**
```python
class OptimizedPromptBuilder:
    """Build optimized prompts for definition generation"""

    # Base template (minimize tokens)
    TEMPLATE = """Je bent juridische expert.

TAAK: Definieer '{term}'

CONTEXT:
{context}

REGELS (TOP 10):
{rules}

FORMAT:
- 1 zin
- B1 niveau
- Geen circulatie

Definitie:"""

    def build(self, context: PromptContext) -> str:
        """Build optimized prompt"""
        # 1. Select most relevant rules (not all 45!)
        top_rules = self._select_relevant_rules(
            context.validation_rules,
            context.term,
            limit=10
        )

        # 2. Format context concisely
        context_block = self._format_context_compact(context.contexts)

        # 3. Format rules concisely
        rules_block = "\n".join(
            f"{i+1}. {r.short_description}"
            for i, r in enumerate(top_rules)
        )

        return self.TEMPLATE.format(
            term=context.term,
            context=context_block,
            rules=rules_block
        )

    def _select_relevant_rules(
        self,
        all_rules: List[str],
        term: str,
        limit: int = 10
    ) -> List[ValidationRule]:
        """
        Select most relevant rules based on term and context.

        Strategy:
        1. Always include ERROR severity rules
        2. Include WARNING rules relevant to term category
        3. Fill remaining with general rules
        """
        rules = []
        rule_registry = get_rule_registry()

        # Get all rules
        all_rule_objects = [
            rule_registry.get(r) for r in all_rules
        ]

        # Priority 1: ERROR severity
        error_rules = [
            r for r in all_rule_objects
            if r.severity == RuleSeverity.ERROR
        ]
        rules.extend(error_rules[:limit])

        if len(rules) >= limit:
            return rules[:limit]

        # Priority 2: Context-relevant warnings
        warning_rules = [
            r for r in all_rule_objects
            if r.severity == RuleSeverity.WARNING
        ]
        remaining = limit - len(rules)
        rules.extend(warning_rules[:remaining])

        return rules
```

**Token Optimization:**
```python
class TokenOptimizer:
    """Optimize prompts for token usage"""

    def __init__(self, model: str = "gpt-4"):
        import tiktoken
        self.encoder = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))

    def truncate_to_tokens(
        self,
        text: str,
        max_tokens: int
    ) -> str:
        """Truncate text to max tokens"""
        tokens = self.encoder.encode(text)
        if len(tokens) <= max_tokens:
            return text

        # Truncate and decode
        truncated = tokens[:max_tokens]
        return self.encoder.decode(truncated)

    def optimize_prompt(
        self,
        prompt: str,
        target_tokens: int = 2000
    ) -> str:
        """Optimize prompt to target token count"""
        current_tokens = self.count_tokens(prompt)

        if current_tokens <= target_tokens:
            return prompt

        # Optimization strategies
        optimized = prompt

        # 1. Remove extra whitespace
        optimized = self._remove_extra_whitespace(optimized)

        # 2. Abbreviate common phrases
        optimized = self._abbreviate_phrases(optimized)

        # 3. Truncate examples if needed
        if self.count_tokens(optimized) > target_tokens:
            optimized = self._truncate_examples(optimized, target_tokens)

        return optimized
```

### 6.4 Async Best Practices

**Concurrent Execution:**
```python
import asyncio
from typing import List

class ParallelValidationService:
    """Execute validation rules in parallel"""

    async def validate(
        self,
        definition: str,
        context: PromptContext,
        rules: List[ValidationRule]
    ) -> ValidationResult:
        """Validate using parallel execution"""
        start_time = time.time()

        # Execute all rules concurrently
        tasks = [
            rule.validate(definition, context)
            for rule in rules
        ]

        # Gather results (continue on individual failures)
        issues = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        # Filter out exceptions, log them
        valid_issues = []
        for i, issue in enumerate(issues):
            if isinstance(issue, Exception):
                logger.error(
                    f"Rule {rules[i].rule_id} failed: {issue}"
                )
            else:
                valid_issues.append(issue)

        # Calculate overall score
        overall_score = sum(i.score for i in valid_issues) / len(valid_issues)

        duration_ms = int((time.time() - start_time) * 1000)

        return ValidationResult(
            overall_score=overall_score,
            passed=overall_score >= 0.7,
            issues=valid_issues,
            rules_executed=len(valid_issues),
            execution_time_ms=duration_ms
        )
```

**Rate Limiting:**
```python
from asyncio import Semaphore
from tenacity import retry, stop_after_attempt, wait_exponential

class RateLimitedAIClient:
    """AI client with rate limiting and retries"""

    def __init__(self, api_key: str, max_concurrent: int = 5):
        self.api_key = api_key
        self.semaphore = Semaphore(max_concurrent)
        self.client = openai.AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    async def complete(self, request: AIRequest) -> AIResponse:
        """Complete with rate limiting and retries"""
        async with self.semaphore:
            try:
                start_time = time.time()

                response = await self.client.chat.completions.create(
                    model=request.model,
                    messages=[
                        {"role": "user", "content": request.prompt}
                    ],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )

                latency_ms = int((time.time() - start_time) * 1000)

                return AIResponse(
                    text=response.choices[0].message.content,
                    tokens_used=response.usage.total_tokens,
                    model=response.model,
                    finish_reason=response.choices[0].finish_reason,
                    latency_ms=latency_ms
                )

            except openai.RateLimitError as e:
                logger.warning(f"Rate limit hit: {e}")
                raise RateLimitError(f"Rate limit exceeded: {e}")
            except openai.APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise AIServiceError(f"AI service failed: {e}")
```

---

## 7. Quality Gates

### 7.1 Pre-Commit Checks

**Required Checks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]
```

**Quality Metrics:**
```bash
# Must pass before commit
make lint          # Ruff + Black + mypy
make test          # All tests
make coverage      # Min 80% coverage
```

### 7.2 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint
        run: |
          ruff check src tests
          black --check src tests
          mypy src

      - name: Test
        run: |
          pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term \
            --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Performance tests
        run: |
          pytest tests/performance/ \
            --benchmark-only \
            --benchmark-max-time=2.0

      - name: Fail if too slow
        run: |
          # Fail if generation >2s
          pytest tests/performance/test_generation_speed.py \
            --max-duration=2000
```

### 7.3 Code Review Checklist

**Must Check:**
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No bare `except:` clauses
- [ ] No direct `st.session_state` access in services
- [ ] Tests cover happy path and error cases
- [ ] Performance: <2s for generation
- [ ] Logging: appropriate level (DEBUG/INFO/ERROR)
- [ ] Error handling: specific exceptions
- [ ] No code duplication (DRY)
- [ ] Follow naming conventions

### 7.4 Acceptance Criteria Template

**Per Feature:**
```markdown
## Feature: Definition Generation

### Functional Requirements
- [ ] Generates definition from term + context
- [ ] Validates against 45 rules
- [ ] Returns validation feedback
- [ ] Saves to database
- [ ] Handles duplicate detection

### Non-Functional Requirements
- [ ] Response time <2s (p95)
- [ ] Token usage <2000 per generation
- [ ] Error rate <1%
- [ ] Test coverage ≥80%

### Quality Requirements
- [ ] All code passes linting
- [ ] All type hints present
- [ ] All functions documented
- [ ] Integration tests pass
- [ ] Performance tests pass

### Definition of Done
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Deployed to staging
```

---

## 8. Testing Requirements

### 8.1 Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── services/
│   │   ├── test_generator_service.py
│   │   ├── test_validation_service.py
│   │   └── test_repository_service.py
│   ├── validation/
│   │   └── rules/
│   │       ├── test_arai_01.py
│   │       └── ...
│   └── utils/
├── integration/             # Integration tests (cross-service)
│   ├── test_orchestrator_flow.py
│   ├── test_database_integration.py
│   └── test_ai_integration.py
├── performance/            # Performance/benchmark tests
│   ├── test_generation_speed.py
│   └── test_validation_speed.py
├── e2e/                    # End-to-end tests
│   └── test_complete_flow.py
└── conftest.py             # Shared fixtures
```

### 8.2 Test Coverage Requirements

**Minimum Coverage:**
- Overall: 80%
- Critical services (orchestrator, generator, validator): 90%
- Validation rules: 100%

**Example Unit Test:**
```python
# tests/unit/services/test_generator_service.py

import pytest
from unittest.mock import Mock, AsyncMock
from services.generator_service import OpenAIGeneratorService
from services.protocols import AIClient, PromptBuilder

class TestGeneratorService:
    """Test suite for OpenAIGeneratorService"""

    @pytest.fixture
    def ai_client(self):
        """Mock AI client"""
        mock = AsyncMock(spec=AIClient)
        mock.complete.return_value = AIResponse(
            text="Test definition",
            tokens_used=50,
            model="gpt-4",
            finish_reason="stop",
            latency_ms=500
        )
        return mock

    @pytest.fixture
    def prompt_builder(self):
        """Mock prompt builder"""
        mock = Mock(spec=PromptBuilder)
        mock.build.return_value = "Test prompt"
        return mock

    @pytest.fixture
    def service(self, ai_client, prompt_builder):
        """Create service with mocks"""
        config = GeneratorConfig(
            model="gpt-4",
            temperature=0.0,
            max_tokens=300
        )
        return OpenAIGeneratorService(ai_client, prompt_builder, config)

    @pytest.mark.asyncio
    async def test_generate_success(self, service, ai_client, prompt_builder):
        """Should generate definition successfully"""
        # Arrange
        context = PromptContext(
            term="test",
            contexts={"organisatorisch": ["OM"]},
            validation_rules=["ARAI-01"]
        )

        # Act
        result = await service.generate(context)

        # Assert
        assert result.text == "Test definition"
        assert result.tokens_used == 50
        assert result.latency_ms == 500

        # Verify calls
        prompt_builder.build.assert_called_once_with(context)
        ai_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_ai_error(self, service, ai_client):
        """Should raise AIServiceError on API failure"""
        # Arrange
        ai_client.complete.side_effect = Exception("API error")
        context = PromptContext(
            term="test",
            contexts={"organisatorisch": ["OM"]},
            validation_rules=[]
        )

        # Act & Assert
        with pytest.raises(AIServiceError) as exc_info:
            await service.generate(context)

        assert "Failed to generate" in str(exc_info.value)
```

### 8.3 Integration Tests

```python
# tests/integration/test_orchestrator_flow.py

import pytest
from services.container import ServiceContainer

class TestOrchestratorIntegration:
    """Integration tests for complete orchestrator flow"""

    @pytest.fixture
    async def container(self):
        """Create service container with real dependencies"""
        container = ServiceContainer(config={
            "db_path": ":memory:",  # In-memory for tests
            "openai_api_key": pytest.OPENAI_TEST_KEY
        })

        # Initialize database
        await container.repository().initialize()

        yield container

        # Cleanup
        await container.repository().close()

    @pytest.mark.asyncio
    async def test_complete_generation_flow(self, container):
        """
        Test complete flow: request → generation → validation → save

        This is a SLOW test (~2s) as it makes real API calls.
        Use sparingly.
        """
        # Arrange
        orchestrator = container.orchestrator()
        request = GenerationRequest(
            term="testterm",
            organisatorische_context=["OM"],
            juridische_context=["Strafrecht"],
            wettelijke_basis=["Sv"]
        )

        # Act
        result = await orchestrator.generate_definition(request)

        # Assert
        assert result.success
        assert result.definition_id is not None
        assert len(result.definition_text) > 10
        assert 0.0 <= result.validation_score <= 1.0
        assert result.generation_time_ms < 2000  # Performance check

        # Verify saved to database
        repository = container.repository()
        saved = await repository.get_by_id(result.definition_id)
        assert saved is not None
        assert saved.term.value == "testterm"
```

### 8.4 Performance Tests

```python
# tests/performance/test_generation_speed.py

import pytest
import time
from statistics import mean, stdev

class TestGenerationPerformance:
    """Performance benchmarks for generation"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_generation_speed_p95(self, container):
        """
        P95 generation time must be <2s

        Runs 20 generations and checks 95th percentile
        """
        orchestrator = container.orchestrator()

        # Run 20 generations
        durations = []
        for i in range(20):
            request = GenerationRequest(
                term=f"performance_test_{i}",
                organisatorische_context=["OM"],
                juridische_context=["Strafrecht"],
                wettelijke_basis=["Sv"],
                include_examples=False  # Skip for speed
            )

            start = time.time()
            result = await orchestrator.generate_definition(request)
            duration = (time.time() - start) * 1000  # ms

            durations.append(duration)
            assert result.success

        # Calculate P95
        sorted_durations = sorted(durations)
        p95_index = int(len(sorted_durations) * 0.95)
        p95_duration = sorted_durations[p95_index]

        # Report
        print(f"\nGeneration Performance:")
        print(f"  Mean: {mean(durations):.0f}ms")
        print(f"  StdDev: {stdev(durations):.0f}ms")
        print(f"  P95: {p95_duration:.0f}ms")

        # Assert P95 <2s
        assert p95_duration < 2000, f"P95 ({p95_duration}ms) exceeds 2000ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_validation_speed(self, container):
        """Validation of 45 rules must complete in <300ms"""
        validator = container.validation_orchestrator()

        definition = "Test definition voor performance testing"
        context = PromptContext(
            term="test",
            contexts={"organisatorisch": ["OM"]},
            validation_rules=[]  # All rules
        )

        # Run validation
        start = time.time()
        result = await validator.validate(definition, context)
        duration = (time.time() - start) * 1000

        print(f"\nValidation Performance:")
        print(f"  Duration: {duration:.0f}ms")
        print(f"  Rules executed: {result.rules_executed}")

        assert duration < 300, f"Validation ({duration}ms) exceeds 300ms"
        assert result.rules_executed == 45
```

---

## 9. Performance Specifications

### 9.1 Performance Targets

| Operation | Target | Maximum | Measurement |
|-----------|--------|---------|-------------|
| Definition generation (end-to-end) | <1500ms | 2000ms | P95 |
| AI call (OpenAI) | <1000ms | 1500ms | P95 |
| Validation (45 rules) | <200ms | 300ms | P95 |
| Database query | <50ms | 100ms | P95 |
| Prompt construction | <30ms | 50ms | P95 |

### 9.2 Resource Limits

**Memory:**
- Service container: <200MB
- Single request: <50MB
- Database connections: 5 max

**Network:**
- API calls: max 3 concurrent
- Request timeout: 30s
- Retry limit: 3 attempts

**Tokens:**
- Prompt: ≤2000 tokens
- Response: ≤500 tokens
- Total per request: ≤2500 tokens

### 9.3 Optimization Strategies

**1. Caching:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedValidationService:
    """Validation with result caching"""

    def __init__(self):
        self._cache: Dict[str, Tuple[ValidationResult, datetime]] = {}
        self._cache_ttl = timedelta(hours=1)

    async def validate(
        self,
        definition: str,
        context: PromptContext
    ) -> ValidationResult:
        """Validate with caching"""
        # Generate cache key
        cache_key = self._make_cache_key(definition, context)

        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return result

        # Execute validation
        result = await self._execute_validation(definition, context)

        # Store in cache
        self._cache[cache_key] = (result, datetime.now())

        return result

    def _make_cache_key(
        self,
        definition: str,
        context: PromptContext
    ) -> str:
        """Generate cache key from definition + context"""
        import hashlib
        content = f"{definition}:{context.term}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
```

**2. Parallel Execution:**
```python
async def validate_parallel(
    definition: str,
    rules: List[ValidationRule]
) -> List[ValidationIssue]:
    """Execute rules in parallel"""
    # Split into batches
    batch_size = 10
    batches = [
        rules[i:i+batch_size]
        for i in range(0, len(rules), batch_size)
    ]

    all_issues = []
    for batch in batches:
        # Execute batch concurrently
        issues = await asyncio.gather(*[
            rule.validate(definition, context)
            for rule in batch
        ])
        all_issues.extend(issues)

    return all_issues
```

**3. Database Indexing:**
```sql
-- Critical indexes for performance
CREATE INDEX idx_definitions_term_trigram ON definitions
    USING gin(term gin_trgm_ops);  -- Fuzzy search

CREATE INDEX idx_definitions_fts ON definitions
    USING gin(search_vector);  -- Full-text search

CREATE INDEX idx_definitions_context_gin ON definitions
    USING gin(organisatorische_context jsonb_path_ops);  -- JSON queries
```

**4. Connection Pooling:**
```python
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600
)
```

---

## 10. Security Requirements

### 10.1 Input Validation

**Validation Rules:**
```python
from pydantic import BaseModel, validator, Field

class SafeGenerationRequest(BaseModel):
    """Validated generation request"""

    term: str = Field(..., min_length=2, max_length=200)
    organisatorische_context: List[str] = Field(default_factory=list, max_items=10)
    juridische_context: List[str] = Field(default_factory=list, max_items=10)
    wettelijke_basis: List[str] = Field(default_factory=list, max_items=10)

    @validator('term')
    def validate_term(cls, v):
        """Sanitize term input"""
        # Remove dangerous characters
        import re
        if re.search(r'[<>{}"\']', v):
            raise ValueError("Term contains forbidden characters")
        return v.strip()

    @validator('organisatorische_context', 'juridische_context', 'wettelijke_basis')
    def validate_context_items(cls, v):
        """Sanitize context lists"""
        # Limit length and sanitize each item
        return [
            item.strip()[:100]  # Max 100 chars per item
            for item in v[:10]  # Max 10 items
            if item.strip()
        ]
```

### 10.2 API Security

**Authentication (future):**
```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Use in endpoints
@app.post("/api/v1/definitions")
async def create_definition(
    request: GenerationRequestDTO,
    user: Dict = Depends(verify_token)
):
    """Protected endpoint"""
    ...
```

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/definitions")
@limiter.limit("10/minute")
async def create_definition(request: Request, ...):
    """Rate limited endpoint"""
    ...
```

### 10.3 Data Security

**Secrets Management:**
```python
import os
from pathlib import Path

def get_api_key() -> str:
    """Get API key from secure source"""
    # Priority: environment variable > secrets file > error

    # 1. Try environment
    if key := os.getenv("OPENAI_API_KEY"):
        return key

    # 2. Try secrets file (gitignored)
    secrets_file = Path(".secrets/openai.key")
    if secrets_file.exists():
        return secrets_file.read_text().strip()

    # 3. Error
    raise ValueError(
        "OpenAI API key not found. "
        "Set OPENAI_API_KEY environment variable or create .secrets/openai.key"
    )
```

**Database Encryption (future):**
```python
from cryptography.fernet import Fernet

class EncryptedRepository:
    """Repository with field-level encryption"""

    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    async def save(self, definition: Definition) -> int:
        """Save with encrypted fields"""
        # Encrypt sensitive fields
        encrypted_definition = Definition(
            ...
            created_by=self._encrypt(definition.created_by),
            ...
        )
        return await super().save(encrypted_definition)

    def _encrypt(self, value: Optional[str]) -> Optional[str]:
        """Encrypt string value"""
        if not value:
            return None
        return self.cipher.encrypt(value.encode()).decode()
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Setup project structure
- [ ] Define core protocols/interfaces
- [ ] Implement ServiceContainer with DI
- [ ] Setup testing infrastructure
- [ ] Implement basic logging/monitoring

### Phase 2: Core Services (Week 3-4)
- [ ] Implement GeneratorService
- [ ] Implement ValidationService (45 rules)
- [ ] Implement RepositoryService
- [ ] Implement PromptBuilder
- [ ] Write unit tests for all services

### Phase 3: Orchestration (Week 5-6)
- [ ] Implement DefinitionOrchestrator
- [ ] Implement error handling
- [ ] Implement retry logic
- [ ] Write integration tests
- [ ] Performance optimization

### Phase 4: API & UI (Week 7-8)
- [ ] Implement FastAPI endpoints
- [ ] Implement Streamlit UI
- [ ] Write E2E tests
- [ ] Performance testing
- [ ] Documentation

### Phase 5: Production Ready (Week 9-10)
- [ ] Security hardening
- [ ] Monitoring setup
- [ ] Deployment scripts
- [ ] Load testing
- [ ] Final review

---

## Appendix A: File Structure

```
definitie-app/
├── src/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── container.py           # ServiceContainer
│   │   ├── orchestrator.py        # DefinitionOrchestrator
│   │   ├── generator.py           # GeneratorService
│   │   ├── validator.py           # ValidationService
│   │   └── repository.py          # RepositoryService
│   ├── validation/
│   │   ├── rules/
│   │   │   ├── arai/
│   │   │   ├── con/
│   │   │   ├── ess/
│   │   │   ├── int/
│   │   │   ├── sam/
│   │   │   ├── str/
│   │   │   └── ver/
│   │   ├── engine.py
│   │   └── protocols.py
│   ├── domain/
│   │   ├── models.py              # Domain models
│   │   └── value_objects.py       # Value objects
│   ├── infrastructure/
│   │   ├── database.py            # Database access
│   │   ├── openai_client.py       # OpenAI wrapper
│   │   └── web_lookup.py          # External APIs
│   ├── api/
│   │   ├── main.py                # FastAPI app
│   │   ├── routes.py              # API routes
│   │   └── dtos.py                # DTOs
│   ├── ui/
│   │   ├── app.py                 # Streamlit app
│   │   └── tabs/                  # UI tabs
│   └── utils/
│       ├── logging.py
│       ├── monitoring.py
│       └── exceptions.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── e2e/
├── config/
│   ├── config.yaml
│   └── validation_rules.yaml
├── docs/
│   └── REBUILD_TECHNICAL_SPECIFICATION.md
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Appendix B: Key Dependencies

```toml
# pyproject.toml
[project]
name = "definitie-app"
version = "2.0.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.104.0",
    "streamlit>=1.28.0",
    "openai>=1.0.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "pydantic>=2.0.0",
    "tenacity>=8.2.0",          # Retry logic
    "tiktoken>=0.5.0",          # Token counting
    "asyncpg>=0.29.0",          # PostgreSQL async driver
    "aiosqlite>=0.19.0",        # SQLite async driver
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "black>=23.9.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]
```

---

**End of Technical Specification**

This specification provides the foundation for rebuilding DefinitieAgent with:
- 70% less code
- 80% better performance
- 100% better architecture
- Clear path to production

Ready for implementation by a single developer with clear guidance at every step.
