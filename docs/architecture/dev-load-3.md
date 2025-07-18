# Dev Load 3: Services & Integrations

## Overview

Dit document beschrijft de services architectuur, externe integraties, en API patterns in DefinitieAgent.

## ⚠️ WAARSCHUWING VOOR AI AGENTS

**De UnifiedDefinitionService is een problematisch God Object:**
- 1000+ regels code met te veel verantwoordelijkheden
- Mix van sync/async zonder duidelijke strategie
- Legacy compatibility verhindert clean design
- Zie ADR-005 voor refactoring strategie

**Web Lookup Module Status: 🔴 KRITIEK**
- 5 versies waarvan 3 broken
- Encoding problemen niet opgelost
- Prioriteit voor fix in Sprint 1

## Core Services Architecture

### UnifiedDefinitionService (⚠️ Problematisch - Refactoring Nodig)

```python
class UnifiedDefinitionService:
    """
    WAARSCHUWING: God Object anti-pattern
    Te veel verantwoordelijkheden: generatie, validatie, orchestratie, caching
    Gepland voor refactoring naar focused services (zie ADR-005)
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # Modes (complexe conditional logic)
    class GenerationMode(Enum):
        AUTO = "auto"      # Kiest beste approach
        MODERN = "modern"  # Nieuwe implementatie
        LEGACY = "legacy"  # Legacy wrapper
        HYBRID = "hybrid"  # Mix van beide
```

**Key Methods (te veel in één class):**
- `generate_definition()` - Hoofdfunctie voor definitie generatie
- `validate_definition()` - Roept validation service aan
- `enrich_content()` - Content enrichment (TODO)
- `export_definition()` - Export naar verschillende formats
- Plus 20+ andere methods...

### Service Integration Points

```
UnifiedDefinitionService
├── ToetsingService (Validation)
├── OntologyAnalyzer (6-step protocol)
├── VoorbeeldenService (Examples)
├── WebLookupService (External sources)
├── ExportService (File generation)
└── DatabaseRepository (Persistence)
```

## External Integrations

### 1. OpenAI Integration

```python
# Configuration
OPENAI_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-4-turbo-preview",
    "temperature": 0.3,
    "max_tokens": 1500,
    "timeout": 30
}

# Usage pattern
async def call_openai(prompt: str) -> str:
    client = AsyncOpenAI(api_key=OPENAI_CONFIG["api_key"])
    
    response = await client.chat.completions.create(
        model=OPENAI_CONFIG["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=OPENAI_CONFIG["temperature"],
        max_tokens=OPENAI_CONFIG["max_tokens"]
    )
    
    return response.choices[0].message.content
```

### 2. Web Lookup Services (🔴 BROKEN - PRIORITEIT FIX)

```python
# ⚠️ WAARSCHUWING: Deze module heeft kritieke problemen
# - 5 verschillende versies in web_lookup/ directory
# - 3 files met "_broken" of "_encoding_issue" suffix
# - UTF-8 encoding problemen niet opgelost
# - Duplicaat code overal

# External sources for definition lookup
WEB_SOURCES = {
    "wetten.nl": {
        "base_url": "https://wetten.overheid.nl",
        "search_endpoint": "/zoeken",
        "encoding": "UTF-8"  # ❌ ENCODING ISSUES
    },
    "officielebekendmakingen.nl": {
        "base_url": "https://www.officielebekendmakingen.nl",
        "search_endpoint": "/zoeken"
    }
}

# ⚠️ BROKEN: Deze implementatie werkt niet correct
async def lookup_definition(term: str, source: str) -> List[Dict]:
    # TODO: Fix encoding issues
    # TODO: Consolideer de 5 verschillende implementaties
    # TODO: Implementeer proper error handling
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{WEB_SOURCES[source]['base_url']}/search",
            params={"q": term}
        )
    return parse_results(response.text)  # ❌ Faalt bij special characters
```

### 3. Document Processing

```python
# Document upload and parsing
SUPPORTED_FORMATS = {
    ".pdf": process_pdf,
    ".docx": process_docx,
    ".txt": process_text,
    ".csv": process_csv
}

def process_document(file_path: str) -> Dict:
    ext = Path(file_path).suffix.lower()
    if ext in SUPPORTED_FORMATS:
        return SUPPORTED_FORMATS[ext](file_path)
    raise ValueError(f"Unsupported format: {ext}")
```

## API Patterns

### 1. Service Response Pattern

```python
@dataclass
class ServiceResponse:
    success: bool
    data: Optional[Any]
    error: Optional[str]
    metadata: Dict[str, Any]
    
    @classmethod
    def success(cls, data: Any, **metadata):
        return cls(True, data, None, metadata)
    
    @classmethod
    def error(cls, error: str, **metadata):
        return cls(False, None, error, metadata)
```

### 2. Async Service Pattern

```python
class AsyncServiceMixin:
    """Mixin voor async service operations"""
    
    async def execute_async(self, *args, **kwargs):
        try:
            result = await self._async_operation(*args, **kwargs)
            return ServiceResponse.success(result)
        except Exception as e:
            logger.error(f"Async operation failed: {e}")
            return ServiceResponse.error(str(e))
```

### 3. Rate Limiting Pattern

```python
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = deque()
    
    def allow_request(self) -> bool:
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

## Database Integration

### Repository Pattern

```python
class DefinitionRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, definition: Definition) -> Definition:
        self.session.add(definition)
        self.session.commit()
        return definition
    
    def find_by_term(self, term: str) -> Optional[Definition]:
        return self.session.query(Definition)\
            .filter(Definition.term == term)\
            .order_by(Definition.created_at.desc())\
            .first()
    
    def get_history(self, limit: int = 10) -> List[Definition]:
        return self.session.query(Definition)\
            .order_by(Definition.created_at.desc())\
            .limit(limit)\
            .all()
```

### Database Models

```python
class Definition(Base):
    __tablename__ = 'definitions'
    
    id = Column(Integer, primary_key=True)
    term = Column(String, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    context = Column(String)
    context_type = Column(String)  # proces/resultaat/type/exemplaar
    metadata = Column(JSON)
    validation_score = Column(Integer)
    ontology_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

## Export Services

### Export Formats

```python
EXPORT_HANDLERS = {
    'txt': export_to_text,
    'pdf': export_to_pdf,
    'docx': export_to_word,
    'xlsx': export_to_excel,
    'json': export_to_json
}

def export_definition(definition: Definition, format: str) -> bytes:
    if format not in EXPORT_HANDLERS:
        raise ValueError(f"Unsupported format: {format}")
    
    handler = EXPORT_HANDLERS[format]
    return handler(definition)
```

### Export Templates

```python
# Text export template
TEXT_TEMPLATE = """
DEFINITIE EXPORT
================
Begrip: {term}
Context: {context}
Datum: {date}

Definitie:
{definition}

Validatie Score: {validation_score}%
Ontologie Score: {ontology_score}/10

Metadata:
- Model: {model}
- Temperature: {temperature}
"""
```

## Performance Optimizations

### 1. Connection Pooling

```python
# Database connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### 2. Caching Strategy

```python
# In-memory cache for definitions
@lru_cache(maxsize=1000)
def get_cached_definition(term: str, context: str) -> Optional[Definition]:
    cache_key = f"{term}:{context}"
    return cache.get(cache_key)

# Redis for distributed cache (planned)
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "ttl": 3600  # 1 hour
}
```

### 3. Batch Processing

```python
async def process_batch(terms: List[str]) -> List[Definition]:
    """Process multiple terms efficiently"""
    tasks = []
    for term in terms:
        task = asyncio.create_task(generate_definition(term))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

## Error Handling & Resilience

### 1. Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError)
)
async def resilient_api_call(url: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### 2. Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

### 3. Fallback Strategies

```python
async def get_definition_with_fallback(term: str) -> Definition:
    try:
        # Try modern implementation
        return await modern_implementation(term)
    except Exception as e:
        logger.warning(f"Modern failed, using legacy: {e}")
        # Fallback to legacy
        return legacy_implementation(term)
```

## Integration Testing Points

1. **OpenAI API**: Mock responses for testing
2. **Web Lookup**: ⚠️ BROKEN - needs complete rewrite first
3. **Database**: In-memory SQLite for tests
4. **Export**: Verify file format compliance

## Refactoring Suggesties voor AI Agents

### Prioriteit 1 (Sprint 1)
1. **Fix Web Lookup Module**
   - Consolideer 5 versies naar 1 werkende implementatie
   - Los UTF-8 encoding problemen op
   - Implementeer proper error handling

### Prioriteit 2 (Sprint 2)
2. **Split UnifiedDefinitionService**
   ```python
   # Van: God Object
   UnifiedDefinitionService (1000+ lines)
   
   # Naar: Focused Services
   DefinitionGenerator (generate only)
   DefinitionValidator (validate only)
   DefinitionOrchestrator (coordinate)
   DefinitionRepository (persist)
   ```

### Prioriteit 3 (Sprint 3)
3. **Remove Layering Violations**
   - UI tabs mogen GEEN directe database calls maken
   - Implementeer proper service interfaces
   - Use dependency injection

## Bekende Problemen

1. **UnifiedDefinitionService**: God Object anti-pattern
2. **Web Lookup**: 3/5 implementaties broken
3. **No Abstractions**: Tight coupling overal
4. **Mixed Async/Sync**: Inconsistente patterns
5. **Direct DB Access**: UI components bypass services

---
*Dit document wordt automatisch geladen door BMAD dev agents*
*⚠️ LET OP: Bevat waarschuwingen over bekende architecturale problemen*