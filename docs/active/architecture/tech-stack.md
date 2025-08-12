# Technology Stack - DefinitieAgent

## Overview

Dit document beschrijft de complete technology stack van DefinitieAgent, inclusief frameworks, libraries, tools, en externe services. Alle technologie keuzes zijn gedocumenteerd met rationale.

## Core Technologies

### Runtime & Language

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Python** | 3.8+ (3.11 recommended) | Primary language | - Excellent AI/ML ecosystem<br>- Streamlit native language<br>- Team expertise |
| **pip** | Latest | Package management | Standard Python tooling |
| **venv** | Built-in | Virtual environments | Simple, no external dependencies |

### Frontend Framework

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Streamlit** | 1.29.0 | Web UI Framework | - Rapid prototyping<br>- Python-native<br>- Built-in components<br>- Good for data apps |

**Streamlit Limitations Acknowledged:**
- Limited customization options
- Session state complexity
- Performance with large datasets
- Single-page application only

### AI/ML Stack

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **OpenAI API** | 1.12.0 | LLM Integration | - GPT-4 quality<br>- Stable API<br>- Good documentation |
| **tiktoken** | Latest | Token counting | Official OpenAI tokenizer |
| **langchain** | Not used | - | Avoided for simplicity |

**Model Configuration:**
- Primary: GPT-4 (`gpt-4-turbo-preview`)
- Fallback: GPT-3.5 (`gpt-3.5-turbo`)
- Temperature: 0.3 (consistency)

### Resilience & Performance

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **tenacity** | Latest | Retry logic | Robust retry mechanisms |
| **circuitbreaker** | Custom | Circuit breaking | Prevent cascade failures |
| **cachetools** | Latest | In-memory caching | Performance optimization |
| **asyncio** | Built-in | Async operations | Concurrent processing |

### Web Scraping & Integration

| Technology | Version | Purpose | Status |
|------------|---------|---------|---------|
| **httpx** | 0.26.0 | HTTP client | ✅ Working |
| **beautifulsoup4** | Latest | HTML parsing | ⚠️ Encoding issues |
| **lxml** | Latest | XML parsing | ⚠️ Encoding issues |
| **selenium** | Not used | - | Considered for JS sites |

### Data Layer

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **SQLAlchemy** | 2.0.25 | ORM | - Industry standard<br>- Async support<br>- Type safety |
| **SQLite** | Built-in | Dev Database | - Zero configuration<br>- File-based<br>- Good for prototyping |
| **PostgreSQL** | 14+ (planned) | Prod Database | - Production ready<br>- Full-text search<br>- JSON support |

**Database Design:**
- Repository pattern for data access
- Migration support via Alembic (planned)
- Connection pooling configured

### Data Processing

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **pandas** | 2.1.4 | Data manipulation | - De facto standard<br>- Excel/CSV support |
| **openpyxl** | Latest | Excel files | Required by pandas |
| **python-docx** | Latest | Word docs | Document processing |

### HTTP & Networking

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **httpx** | 0.26.0 | HTTP client | - Modern async support<br>- Connection pooling<br>- Better than requests |
| **aiohttp** | Alternative | Not used | httpx sufficient |

### Validation & Serialization

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **pydantic** | 2.5.3 | Data validation | - Type safety<br>- Automatic validation<br>- JSON schema generation |
| **python-multipart** | Latest | File uploads | Required for Streamlit |

### Development Tools

| Tool | Version | Purpose | Configuration |
|------|---------|---------|--------------|
| **pytest** | 7.4.4 | Testing | `pytest.ini` configured |
| **black** | 23.12.1 | Code formatting | Line length: 88 |
| **ruff** | Latest | Linting | Fast, replacing flake8 |
| **mypy** | Latest | Type checking | Gradual typing |
| **pre-commit** | Latest | Git hooks | Auto formatting |

### Monitoring & Logging

| Technology | Version | Purpose | Status |
|------------|---------|---------|---------|
| **logging** | Built-in | Application logs | ✅ Implemented |
| **Sentry** | Not yet | Error tracking | 🔄 Planned |
| **Prometheus** | Not yet | Metrics | 🔄 Planned |

### Deployment & Infrastructure

| Technology | Version | Purpose | Status |
|------------|---------|---------|---------|
| **Docker** | Latest | Containerization | 🔄 Planned |
| **nginx** | Latest | Reverse proxy | 🔄 Planned |
| **GitHub Actions** | N/A | CI/CD | 🔄 Planned |

## Architecture Patterns

### Application Architecture
- **Pattern**: Modular Monolith
- **Service Layer**: Singleton services
- **Data Access**: Repository pattern
- **UI Pattern**: Component-based

### Code Organization
```
src/
├── services/      # Business logic
├── ai_toetsing/   # Domain-specific AI
├── ui/            # Presentation layer
├── models/        # Data models
├── repositories/  # Data access
└── utils/         # Cross-cutting
```

### Key Design Decisions

1. **Monolith over Microservices**
   - Simplicity for small team
   - Easier debugging
   - Lower operational overhead

2. **SQLite for Development**
   - Zero configuration
   - Easy onboarding
   - Portable databases

3. **Streamlit for UI**
   - Rapid development
   - Python-only stack
   - Good enough for MVP

4. **No Frontend Framework**
   - Streamlit handles UI
   - No React/Vue complexity
   - Focus on backend

## External Services

### Required Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **OpenAI API** | LLM provider | API key required |
| **PostgreSQL** | Production DB | Self-hosted/managed |

### Optional Services

| Service | Purpose | When Needed |
|---------|---------|-------------|
| **Redis** | Caching | High traffic |
| **S3/MinIO** | Object storage | Document storage |
| **Elasticsearch** | Full-text search | Advanced search |

## Performance Considerations

### Current Bottlenecks
1. **OpenAI API calls** - 8-12 seconds
2. **Sequential processing** - No parallelization
3. **Large prompts** - 35k characters

### Optimization Strategy
1. Implement caching layer
2. Parallel API calls where possible
3. Prompt optimization
4. Database query optimization

## Security Stack

### Current Implementation
- Environment variables for secrets
- Input validation via Pydantic
- SQL injection prevention (SQLAlchemy)
- Rate limiting (basic)

### Planned Enhancements
- JWT authentication
- Role-based access control
- API key management
- Audit logging

## Migration Path

### Short Term (Current)
```
Streamlit → SQLite → OpenAI API
```

### Medium Term (Planned)
```
Streamlit → PostgreSQL → OpenAI API
    ↓           ↓            ↓
  FastAPI    Redis      Rate Limiter
```

### Long Term (Future)
```
React/Vue → FastAPI → PostgreSQL → OpenAI/Local LLM
             ↓           ↓              ↓
          GraphQL    Redis         Load Balancer
```

## Version Management

### Python Dependencies
- Managed via `requirements.txt`
- Considering Poetry for better dependency resolution
- Security updates via Dependabot (planned)

### Version Pinning Strategy
- Pin major versions for stability
- Allow minor updates
- Security patches ASAP

## Development Environment

### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 10GB disk space
- Internet connection (OpenAI API)

### Recommended Setup
- Python 3.11
- 8GB RAM
- SSD storage
- VS Code with Python extensions

## Decision Log

| Decision | Date | Rationale | Status |
|----------|------|-----------|---------|
| Streamlit over Flask | 2024-01 | Faster development | Active |
| SQLAlchemy 2.0 | 2024-02 | Modern, async support | Active |
| httpx over requests | 2024-03 | Better async support | Active |
| No frontend framework | 2024-01 | Streamlit sufficient | Under review |

## Tech Debt

1. **No proper caching** - Implement Redis
2. **No API versioning** - Add versioning layer
3. **Limited monitoring** - Add APM solution
4. **No message queue** - Consider Celery
5. **SQLite in dev** - Move to PostgreSQL

---
*Laatste update: 2025-01-18*