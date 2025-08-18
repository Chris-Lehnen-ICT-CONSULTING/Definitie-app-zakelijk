# Technology Stack - DefinitieAgent

> **🧪 Quinn QA Status**: Architecture review voltooid (2025-08-15) - Production readiness gaps geïdentificeerd

## Overview

Dit document beschrijft de complete technology stack van DefinitieAgent, inclusief frameworks, libraries, tools, en externe services. Alle technologie keuzes zijn gedocumenteerd met rationale.

**⚠️ CRITICAL**: Na Quinn senior QA architect review zijn significante gaps gevonden in security, performance, en code quality tooling.

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

### 🧪 AI Code Review Stack (Added by Quinn)

| Tool | Version | Purpose | Configuration | Status |
|------|---------|---------|--------------|--------|
| **AI Code Reviewer** | Custom | Automated review | `scripts/ai_code_reviewer.py` | ✅ Implemented |
| **BMAD Framework** | Custom | Agent workflow | `.bmad-core/` structure | ✅ Active |
| **Quinn QA Agent** | Custom | Architecture review | Senior QA protocols | ✅ Completed |
| **Bandit** | Latest | Security scanning | Python vulnerability detection | 🔄 Needed |
| **Safety** | Latest | Dependency check | Known vulnerability scanning | 🔄 Needed |

**Quinn Review Findings:**
- **pytest**: 522 tests but 87% failures due to import issues
- **pytest-cov**: 26% test-to-code ratio (target: 75%+)
- **ruff**: 235 issues found (92 important, 175 suggestions)
- **mypy**: Limited type hint coverage across codebase

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

### Current Bottlenecks (Quinn Identified)
1. **Database N+1 Queries** - voorbeelden system performance degradation
2. **Memory Leaks** - unlimited cache growth (no cleanup)
3. **Blocking I/O** - UI freezing bij trage external APIs
4. **SQLite Concurrency** - multi-user limitations
5. **Import Chaos** - E402 errors affecting startup performance
6. **OpenAI API calls** - 8-12 seconds (secondary priority)

### 🚨 CRITICAL Optimization Strategy (Quinn Priority)
1. **Fix Database Queries**: Add composite indexes, eliminate N+1
2. **Implement Memory Management**: Cache size limits, TTL cleanup
3. **Async I/O Implementation**: Non-blocking external API calls
4. **Connection Pooling**: SQLite WAL mode + connection pool
5. **Import Architecture**: Fix E402 module-level import issues
6. **Performance Monitoring**: Add APM tooling for production insight

## Security Stack (Critical Gaps Identified by Quinn)

### ❌ Current Implementation - INADEQUATE FOR PRODUCTION
- Environment variables for secrets ⚠️ No encryption
- Input validation via Pydantic ✅ Basic validation
- SQL injection prevention (SQLAlchemy) ✅ Working
- Rate limiting (basic) ⚠️ Performance issues found

### 🚨 CRITICAL MISSING (Production Blockers)
- **Authentication/Authorization**: NONE (OWASP A07:2021)
- **Data Encryption**: SQLite unencrypted (OWASP A02:2021)
- **Input Length Validation**: Missing (DoS risk)
- **Error Information Leakage**: 8 bare except clauses
- **ReDoS Vulnerability**: Complex regex patterns
- **Dependency Scanning**: No automated vulnerability checks

### 🎯 Immediate Security Requirements
- **Streamlit Authenticator**: Basic user authentication
- **Cryptography/Fernet**: Database encryption
- **Input Sanitization**: Length and content validation
- **Security Headers**: XSS, CSRF protection
- **Audit Logging**: Security event tracking
- **Secrets Management**: Proper secret encryption

### Planned Enhancements (Post-Security Basics)
- JWT authentication
- Role-based access control
- API key management
- Advanced audit logging

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

## Tech Debt (Quinn Assessment - CRITICAL UPDATE)

### 🚨 CRITICAL DEBT (Production Blockers)
1. **Legacy Architecture Chaos** - UnifiedDefinitionService (698 regels) not split
2. **No Authentication System** - Zero security layer (OWASP A07:2021)
3. **Unencrypted Data Storage** - SQLite plaintext (OWASP A02:2021)
4. **Import Architecture Broken** - E402 errors in main.py, legacy modules
5. **8 Bare Except Clauses** - Error masking, debugging impossible
6. **Test Infrastructure Crisis** - 87% failures, import issues

### ⚠️ HIGH DEBT (Performance Impact)
7. **Database N+1 Queries** - Performance degradation under load
8. **Memory Leaks** - Cache system unlimited growth
9. **WebLookupService Broken** - Complete rebuild needed (3-4 weeks)
10. **Feature Flags Missing** - Documented but not implemented

### 📈 MEDIUM DEBT (Development Velocity)
11. **Code Quality Issues** - 92 important, 175 suggestions (ruff)
12. **Mixed Language Docs** - 175 files English docstrings in Dutch codebase
13. **Test Coverage** - AI Toetser 5%, overall 26% (target: 75%)
14. **No proper caching** - Implement Redis
15. **Limited monitoring** - Add APM solution

### 🎯 Quinn Debt Prioritization
**Week 1-2**: Items 1-6 (Foundation stability)
**Week 3-4**: Items 7-10 (Performance & security)
**Week 5-8**: Items 11-15 (Quality & development experience)

## 🧪 Quinn QA Architect Conclusions

**Production Readiness Assessment**: **45% ready** - significant gaps in security and performance
**Primary Blocker**: Legacy architecture chaos prevents efficient development and security implementation
**Immediate Action Required**: Foundation stabiliteit (Week 1-2) before any feature development
**Security Status**: **Critical** - multiple OWASP vulnerabilities, no authentication layer
**Performance Status**: **Concerning** - database bottlenecks and memory leaks under load
**Code Quality**: **Needs improvement** - 235 issues requiring attention

**Recommendation**: Focus on CRITICAL and HIGH debt items before production deployment.

---
*Laatste update: 2025-08-15 (Quinn QA Review)*