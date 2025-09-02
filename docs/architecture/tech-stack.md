---
canonical: true
status: active
last_verified: 2025-09-02
owner: architecture
---

# Technology Stack - DefinitieAgent

## Wijzigingshistorie

- 2025-08-28: Consistentie en API‑first
  - Python versie gesynchroniseerd naar 3.11+
  - Startcommando gecorrigeerd naar `streamlit run src/main.py`
  - UI ↔ Service laag verduidelijkt (Orchestrator‑first, geen directe DB/SDK in UI)
  - Security/Observability en Cost‑management toegelicht

## Overzicht

Dit document beschrijft de complete technology stack van DefinitieAgent, inclusief frameworks, libraries, tools en infrastructuur componenten.

## Core Technologies

### Programming Language

**Python 3.11+**
- Modern async/await support
- Type hints en annotations
- Structured pattern matching
- Performance verbeteringen

### UI Framework

**Streamlit 1.45.1**
- Rapid prototyping voor data-driven apps
- Native Python integration
- Reactive UI updates
- Session state management
- Component ecosystem

### Database

**SQLite** (Huidige implementatie)
- Lightweight, serverless
- Zero-configuration
- ACID compliant
- Embedded database

**PostgreSQL** (Voorbereid in schema)
- Production-ready RDBMS
- Advanced JSON support
- Full-text search capabilities
- Concurrent access

### AI/LLM Integration

**OpenAI API**
- Model: GPT-4.1 (gpt-4-1106-preview)
- Async client support
- Structured outputs
- Function calling capabilities
- Token management

## Backend Stack

### Core Dependencies

#### Async & Concurrency
- **anyio** (5.0.0): Unified async library
- **aiohttp**: Async HTTP client/server
- **httpx** (0.28.0): Modern async HTTP client
- **asyncio**: Native Python async support

#### Data Processing
- **pandas** (2.2.3): Data manipulation and analysis
- **numpy**: Numerical computing
- **jsonschema**: JSON validation
- **pydantic**: Data validation using Python type annotations

#### Web & API
- **beautifulsoup4**: HTML/XML parsing
- **requests**: Simple HTTP library (legacy)
- **urllib3**: HTTP client (dependency)

#### Caching & Performance
- **cachetools**: Extensible memoizing collections
- **Memory caching**: In-process caching
- **TTL-based expiration**: Time-based cache invalidation

### Security & Validation

- **Input sanitization**: XSS prevention
- **API key management**: Environment-based secrets
- **Rate limiting**: Token bucket algorithm
- **Circuit breakers**: Failure protection

### Configuration Management

- **Environment variables**: Runtime secrets/config via OS env (geen `.env` loading in runtime)
- **YAML configs**: Hierarchical configuration
- **Environment overrides**: 12-factor app compliance
- **Feature flags**: Runtime configuration

## Development Stack

### Code Quality Tools

#### Formatting
- **black**: Opinionated code formatter
- Line length: 88 characters
- String normalization
- Magic trailing comma

#### Linting
- **ruff**: Fast Python linter
  - E/F rules (pycodestyle/Pyflakes)
  - Security checks (S)
  - Import sorting (I)
  - Naming conventions (N)
  - Bug detection (B)
  - Complexity (C90, PLR0915)
  - 30+ rule sets enabled

#### Type Checking
- **mypy**: Static type checker
- Gradual typing support
- Type inference
- Plugin system

### Testing Framework

#### Test Runners
- **pytest**: Modern testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance testing

#### Testing Tools
- **coverage**: Code coverage measurement
- **unittest.mock**: Mocking framework
- **fixtures**: Test data management
- **parameterized tests**: Data-driven testing

### Development Tools

- **pre-commit**: Git hook framework
- **ipython**: Enhanced Python shell
- **watchdog**: File system monitoring
- **python-decouple**: Settings management

## Infrastructure Components

### Containerization (Prepared)

```dockerfile
# Multi-stage build ready
FROM python:3.10-slim as base
# Build stage
FROM base as builder
# Runtime stage
FROM base as runtime
```

### CI/CD Pipeline

- **GitHub Actions**: Automated workflows
- **Pre-commit hooks**: Local quality gates
- **Automated testing**: On PR/push
- **Security scanning**: Dependency checks

### Monitoring & Logging

- **Python logging**: Structured logging
- **Error tracking**: Detailed error context
- **Performance metrics**: Response time tracking
- **Usage analytics**: Feature adoption metrics

### Security & Observability (uitgebreid)

- **Security**: OAuth2/JWT + RBAC, input‑sanitization, rate limiting, circuit breakers, secrets‑beheer, encryptie in transit (TLS) en at rest (SQLCipher/PostgreSQL TDE).
- **Observability**: Structured JSON logging (request_id, user_id, latency_ms, tokens_used), Prometheus‑metrics (cache hit‑ratio, AI‑tokens, validatie‑fouten), OpenTelemetry tracing (10–20% sampling).
- **Cost management**: Dagelijkse AI‑kostenrapportage, budget‑alerts, token‑limieten per omgeving.

## Architecture Components

### Service Layer

```
ServiceContainer
├── AI Services (V1 & V2)
├── Cache Service
├── Database Service
├── Validation Service
├── Orchestration Service
└── Web Lookup Service
```

### Prompt System Architecture

18+ Specialized Modules:
- `AchtergrondModule`: Context handling
- `AlgemeneKennisModule`: General knowledge
- `BeschrijvingModule`: Description generation
- `ContextModule`: Contextual understanding
- `DynamischeElementenModule`: Dynamic content
- `GerelateerdeBegrippenModule`: Related concepts
- `GVIModule`: Generation-Validation-Integration
- `JuridischeContextModule`: Legal context
- `OntologieModule`: Ontological classification
- `PromptFormatterModule`: Prompt structuring
- `ReflectieModule`: Self-reflection
- `SamenvattingModule`: Summarization
- `StructuurModule`: Structural formatting
- `TaalModule`: Language processing
- `ValidatieModule`: Validation logic
- `VerbeteringModule`: Improvement suggestions
- `VoorbeeldModule`: Example generation
- `VoorbeeldZinModule`: Example sentences

### Validation Framework

Toetsregels (40+ rules):
- **ARAI**: Afbakening, Reikwijdte, Afbakening Inhoud
- **CON**: Context, Consistentie checks
- **ESS**: Essentiële elementen validation
- **INT**: Integriteit, Internal consistency
- **SAM**: Samenhang, Samenvatting quality
- **STR**: Structuur validation
- **VER**: Verificatie rules

### Data Models

```python
# Domain Models
Definition
├── term: str
├── beschrijving: str
├── category: DefinitionCategory
├── context: Optional[str]
├── organisatie_context: Optional[str]
├── juridische_context: Optional[str]
├── examples: List[str]
├── related_terms: List[str]
└── metadata: Dict

# Categories
DefinitionCategory:
- TYPE
- PROCES
- RESULTAAT
- EXEMPLAAR
```

## Technology Decisions

### Async-First Architecture

**Rationale**:
- Verbeterde performance voor I/O-bound operations
- Better resource utilization
- Native OpenAI async client support
- Future microservices compatibility

**Implementation**:
- AsyncGPTClient voor AI calls
- Async database operations
- Async web scraping
- Event-driven orchestration

### Modular Prompt System

**Rationale**:
- Separation of concerns
- Reusable prompt components
- Easier testing en maintenance
- Flexible composition

**Benefits**:
- 18+ gespecialiseerde modules
- Clean interfaces
- Dynamic module selection
- Extensible architecture

### SQLite → PostgreSQL Path

**Current (SQLite)**:
- Development simplicity
- No server required
- Single file database
- Good for prototyping

**Future (PostgreSQL)**:
- Production scalability
- Concurrent users
- Advanced features
- Cloud-ready

### Rate Limiting Strategy

**Implementation**:
- Token bucket algorithm
- Priority-based allocation
- Burst handling
- Graceful degradation

**Configuration**:
```python
rate_limit_config = RateLimitConfig(
    requests_per_minute=60,
    requests_per_day=10000,
    burst_size=10,
    priority_allocation=0.3
)
```

## Integration Points

### External Services

1. **OpenAI API**
   - Primary AI service
   - Structured outputs
   - Function calling
   - Embeddings (future)

2. **Web Lookup Services**
   - BeautifulSoup scraping
   - Content extraction
   - Link validation
   - Metadata parsing

3. **Future Integrations**
   - PostgreSQL database
   - Redis cache
   - Elasticsearch
   - External APIs

### Internal Integrations

- **UI ↔ Services**: Orchestrator‑first (UI roept services/orchestrator aan; geen directe DB/SDK‑imports)
- **Services ↔ Database**: Repository pattern
- **AI ↔ Validation**: Prompt/validator integratie via services
- **Cache ↔ Services**: Decorator pattern (TTL, bounded size)

## Performance Optimizations

### Caching Strategy

**Multi-Level Caching**:
1. In-memory cache (cachetools)
2. Session cache (Streamlit)
3. Database cache (future)
4. CDN cache (static assets)

**Cache Keys**:
```python
cache_key = f"definition:{term}:{category}:{context_hash}"
```

### Async Optimizations

- Connection pooling
- Concurrent request handling
- Batch processing support
- Stream processing (future)

### Database Optimizations

- Prepared statements
- Index optimization
- Query result caching
- Connection pooling

## Security Considerations

### API Security

- API key rotation
- Rate limiting per client
- Request validation
- Error message sanitization

### Input Security

- XSS prevention
- SQL injection protection
- Command injection prevention
- Path traversal protection

### Data Security

- Encryption at rest (future)
- Encryption in transit (HTTPS)
- PII handling compliance
- Audit logging

## Monitoring Stack

### Application Metrics

- Response times
- Error rates
- API usage
- Cache hit rates

### System Metrics

- CPU usage
- Memory consumption
- Disk I/O
- Network traffic

### Business Metrics

- Definitions created
- User engagement
- Feature adoption
- Quality scores

## Future Technology Considerations

### Potential Additions

1. **Vector Database**
   - Pinecone/Weaviate
   - Semantic search
   - Embeddings storage

2. **Message Queue**
   - RabbitMQ/Kafka
   - Async processing
   - Event streaming

3. **Container Orchestration**
   - Kubernetes
   - Auto-scaling
   - High availability

4. **Observability**
   - OpenTelemetry
   - Distributed tracing
   - APM integration

### AI/ML Enhancements

- Multiple model support
- Fine-tuning capabilities
- Local model options
- Embeddings pipeline

## Development Environment

### Required Tools

```bash
# Python environment
python >= 3.10
pip >= 21.0
virtualenv / venv

# Development tools
git
make (optional)
docker (optional)

# IDE recommendations
- VS Code with Python extension
- PyCharm Professional
- Cursor AI
```

### Environment Setup

```bash
# Clone repository
git clone <repository>
cd definitie-app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Environment configuration (geen `.env` loading in runtime)
# Optie A (aanbevolen): zet je sleutel in de omgeving en start
export OPENAI_API_KEY_PROD='sk-...'
OPENAI_API_KEY="$OPENAI_API_KEY_PROD" streamlit run src/main.py

# Optie B: gebruik het run-script dat automatisch mapt
bash scripts/run_app.sh

# VS Code: gebruik het launch-profiel dat
# OPENAI_API_KEY ← ${env:OPENAI_API_KEY_PROD} zet
```

## Deployment Considerations

### Development
- Local SQLite database
- File-based caching
- Debug logging
- Hot reload enabled

### Staging
- PostgreSQL database
- Redis caching
- Info logging
- Performance monitoring

### Production
- PostgreSQL cluster
- Redis cluster
- Error logging only
- Full monitoring stack

### Configuratie & Secrets per omgeving
- Config via environment variables in alle omgevingen; geen `.env` loading in runtime.
- Feature flags per omgeving (toggle orchestrator‑first, modern lookup).
- Afgesproken limieten voor AI‑tokens/kosten per omgeving met alerts.

---

Dit technology stack document wordt regelmatig bijgewerkt om de huidige staat van de applicatie te reflecteren.
