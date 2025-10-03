# DefinitieAgent Rebuild - Appendices

**Companion to:** REBUILD_EXECUTION_PLAN.md
**Last Updated:** 2025-10-02
**Version:** 2.0

---

## Appendix A: Complete File Structure

### Target File Structure (Post-Rebuild)

```
definitie-app-v2/
│
├── app/                           # FastAPI application
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   │
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # Main router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── definitions.py # Definition CRUD
│   │           ├── validation.py  # Validation endpoints
│   │           ├── generation.py  # Generation endpoints
│   │           ├── export.py      # Export endpoints
│   │           └── health.py      # Health checks
│   │
│   ├── core/                      # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py              # Settings management
│   │   ├── logging.py             # Logging setup
│   │   ├── security.py            # Security utilities
│   │   └── dependencies.py        # Dependency injection
│   │
│   ├── db/                        # Database
│   │   ├── __init__.py
│   │   ├── base.py                # Base model
│   │   └── session.py             # Session management
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── definition.py          # Definition model
│   │   ├── example.py             # Example model
│   │   ├── history.py             # History model
│   │   └── tag.py                 # Tag model
│   │
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                # Base repository
│   │   ├── definition_repository.py
│   │   └── cache_repository.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── definition.py          # Definition schemas
│   │   ├── validation.py          # Validation schemas
│   │   ├── generation.py          # Generation schemas
│   │   └── common.py              # Shared schemas
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── ai_service.py          # OpenAI integration
│   │   ├── validation_service.py  # Validation orchestrator
│   │   ├── generation_service.py  # Generation orchestrator
│   │   ├── cache_service.py       # Redis cache
│   │   ├── web_lookup_service.py  # Wikipedia/SRU
│   │   └── duplicate_service.py   # Duplicate detection
│   │
│   ├── validators/                # Validation rules
│   │   ├── __init__.py
│   │   ├── base.py                # Base validator
│   │   ├── loader.py              # Rule loader
│   │   ├── arai/                  # ARAI rules
│   │   │   ├── __init__.py
│   │   │   ├── arai_01.py
│   │   │   └── ...
│   │   ├── con/                   # CON rules
│   │   ├── ess/                   # ESS rules
│   │   ├── int/                   # INT rules
│   │   ├── sam/                   # SAM rules
│   │   ├── str/                   # STR rules
│   │   └── ver/                   # VER rules
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── text_processing.py     # Text utilities
│       ├── similarity.py          # Similarity algorithms
│       └── decorators.py          # Custom decorators
│
├── ui/                            # Streamlit UI
│   ├── __init__.py
│   ├── app.py                     # Main UI entry
│   ├── components/                # UI components
│   │   ├── __init__.py
│   │   ├── definition_form.py
│   │   ├── validation_view.py
│   │   └── export_dialog.py
│   └── pages/                     # UI pages
│       ├── home.py
│       ├── generate.py
│       ├── validate.py
│       └── manage.py
│
├── config/                        # Configuration files
│   ├── validation_rules/          # Validation rule configs
│   │   ├── arai/
│   │   │   ├── ARAI-01.yaml
│   │   │   └── ...
│   │   ├── con/
│   │   ├── ess/
│   │   ├── int/
│   │   ├── sam/
│   │   ├── str/
│   │   └── ver/
│   ├── prompts/                   # Prompt templates
│   │   ├── system_prompt.md
│   │   ├── context_template.md
│   │   └── rules_injection.md
│   └── settings/                  # App settings
│       ├── development.yaml
│       ├── production.yaml
│       └── test.yaml
│
├── alembic/                       # Database migrations
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   └── ...
│   ├── env.py
│   └── script.py.mako
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   │
│   ├── unit/                      # Unit tests
│   │   ├── __init__.py
│   │   ├── test_validators.py
│   │   ├── test_services.py
│   │   └── test_repositories.py
│   │
│   ├── integration/               # Integration tests
│   │   ├── __init__.py
│   │   ├── test_generation_flow.py
│   │   ├── test_validation_flow.py
│   │   └── test_api_endpoints.py
│   │
│   ├── baseline/                  # Baseline validation tests
│   │   ├── __init__.py
│   │   ├── fixtures/
│   │   │   └── baseline_definitions.py
│   │   └── test_baseline_validation.py
│   │
│   └── performance/               # Performance tests
│       ├── __init__.py
│       └── test_response_times.py
│
├── scripts/                       # Utility scripts
│   ├── extract_business_logic.py  # Extraction script
│   ├── migrate_data.py            # Data migration
│   ├── seed_database.py           # Database seeding
│   └── benchmark.py               # Performance benchmarks
│
├── docs/                          # Documentation
│   ├── api/                       # API documentation
│   │   └── openapi.json
│   ├── architecture/              # Architecture docs
│   │   ├── overview.md
│   │   ├── data_flow.md
│   │   └── deployment.md
│   └── user/                      # User documentation
│       ├── getting_started.md
│       └── api_guide.md
│
├── .github/                       # GitHub configuration
│   └── workflows/
│       ├── ci.yml                 # CI pipeline
│       ├── deploy.yml             # Deployment
│       └── tests.yml              # Test automation
│
├── docker-compose.yml             # Docker orchestration
├── docker-compose.dev.yml         # Dev overrides
├── Dockerfile                     # API Dockerfile
├── Dockerfile.streamlit           # UI Dockerfile
│
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Dev dependencies
├── pyproject.toml                 # Python project config
├── pytest.ini                     # Pytest configuration
├── alembic.ini                    # Alembic configuration
│
├── .env.example                   # Environment template
├── .gitignore
├── .dockerignore
├── README.md
└── LICENSE
```

---

## Appendix B: Configuration File Templates

### B.1: Validation Rule YAML Template

**File:** `config/validation_rules/{category}/{RULE-ID}.yaml`

```yaml
# Validation Rule: {RULE-ID}
# Category: {CATEGORY}
# Priority: {high|medium|low}

id: "ARAI-01"
category: "ARAI"
priority: "high"
enabled: true

metadata:
  naam: "Geen werkwoorden als kern"
  uitleg: |
    Een juridische definitie mag niet beginnen met een werkwoord als kernwoord.
    Definities beschrijven wat iets IS, niet wat het DOET.

  versie: "1.0"
  last_updated: "2025-10-02"
  author: "Extracted from legacy system"

  # Rule type classification
  rule_type: "structural"  # structural, semantic, contextual

  # Applicable contexts
  applies_to:
    categories: ["ENT", "ACT", "REL", "ATT", "AUT", "STA", "OTH"]  # All
    contexts: []  # Empty = all contexts

implementation:
  # How this rule is implemented
  type: "regex"  # regex, logic, ai, hybrid

  # Regex patterns (if type = regex)
  patterns:
    # Patterns that SHOULD NOT match (bad patterns)
    forbidden:
      - pattern: '^\s*(is|zijn|wordt|worden)\s+'
        description: "Definition starts with verb"
        case_sensitive: false

      - pattern: '^\s*(kan|mag|moet|zal)\s+'
        description: "Definition starts with modal verb"
        case_sensitive: false

    # Patterns that SHOULD match (good patterns)
    required:
      - pattern: '^\s*(een|de|het)\s+\w+'
        description: "Definition starts with article"
        case_sensitive: false

  # Logic description (for non-regex rules)
  logic_description: |
    1. Check if definition starts with forbidden verb patterns
    2. Check if definition starts with required article patterns
    3. Cross-reference with good/bad examples
    4. Return score based on match results

  # Code reference in legacy system
  legacy_reference: "src/toetsregels/regels/ARAI-01.py"

validation:
  # Input fields required for validation
  input_fields:
    - name: "definitie"
      type: "string"
      required: true

    - name: "begrip"
      type: "string"
      required: true

    - name: "context"
      type: "dict"
      required: false

  # Output structure
  output:
    success:
      type: "boolean"
      description: "Whether validation passed"

    message:
      type: "string"
      description: "Human-readable validation message"

    score:
      type: "float"
      min: 0.0
      max: 1.0
      description: "Validation score (0.0 = fail, 1.0 = perfect)"

    details:
      type: "dict"
      optional: true
      description: "Additional validation details"

examples:
  # Good examples (should pass validation)
  good:
    - input:
        definitie: "Een systematische controle van identiteitsgegevens tegen authentieke bronnen"
        begrip: "verificatie"
      expected:
        success: true
        score: 1.0
        message_pattern: "✔️.*ARAI.*01"

    - input:
        definitie: "De handeling waarbij gegevens worden vastgelegd in een gestructureerd systeem"
        begrip: "registratie"
      expected:
        success: true
        score: 1.0

  # Bad examples (should fail validation)
  bad:
    - input:
        definitie: "Is een proces waarbij gegevens worden gecontroleerd"
        begrip: "verificatie"
      expected:
        success: false
        score: 0.0
        message_pattern: "❌.*ARAI.*01.*werkwoord"

    - input:
        definitie: "Wordt gebruikt om identiteit te verifiëren"
        begrip: "verificatieproces"
      expected:
        success: false
        score: 0.0

  # Edge cases
  edge_cases:
    - input:
        definitie: "Een is een bepaald lidwoord"  # "is" in middle, not start
        begrip: "test"
      expected:
        success: true
        score: 1.0
        note: "Verb in middle is okay, only start matters"

generation_hints:
  # Instructions for AI generator to follow this rule
  - "Begin de definitie met een lidwoord (Een, De, Het)"
  - "Gebruik een zelfstandig naamwoord als kernwoord"
  - "Vermijd werkwoorden aan het begin van de definitie"
  - "Formuleer als 'X is een Y die Z' structuur"
  - "Beschrijf WAT iets is, niet WAT het doet"

test_cases:
  # Comprehensive test cases for pytest
  - name: "valid_definition_with_article_een"
    input:
      definitie: "Een systematische controle van identiteitsgegevens"
      begrip: "verificatie"
    expected:
      success: true
      score: 1.0
      message_contains: "✔️"

  - name: "valid_definition_with_article_de"
    input:
      definitie: "De handeling waarbij data wordt vastgelegd"
      begrip: "registratie"
    expected:
      success: true
      score: 1.0

  - name: "invalid_starts_with_is"
    input:
      definitie: "Is een proces waarbij gegevens worden gecontroleerd"
      begrip: "verificatie"
    expected:
      success: false
      score: 0.0
      message_contains: "❌"

  - name: "invalid_starts_with_wordt"
    input:
      definitie: "Wordt gebruikt om identiteit te verifiëren"
      begrip: "verificatie"
    expected:
      success: false
      score: 0.0

  - name: "edge_case_verb_in_middle"
    input:
      definitie: "Een proces is een reeks stappen"
      begrip: "proces"
    expected:
      success: true
      score: 1.0

performance:
  # Performance requirements
  max_execution_time_ms: 50
  complexity: "O(n)"  # Time complexity
  memory_usage: "O(1)"  # Space complexity

dependencies:
  # Other rules this rule depends on
  requires: []

  # Rules that should run before this one
  run_after: []

  # Rules that conflict with this one
  conflicts_with: []

metadata_extended:
  # Extended metadata for analytics
  created_date: "2024-01-15"
  last_review_date: "2025-10-02"
  review_frequency_days: 90
  success_rate: 0.95  # Historical success rate
  false_positive_rate: 0.02
  false_negative_rate: 0.03
```

### B.2: Environment Configuration

**File:** `.env.example`

```bash
# ==============================================
# DefinitieAgent v2.0 Environment Configuration
# ==============================================
#
# IMPORTANT: Copy this file to .env and fill in real values
# DO NOT commit .env to version control
#

# ----------------------------------------------
# Environment
# ----------------------------------------------
ENVIRONMENT=development  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# ----------------------------------------------
# API Configuration
# ----------------------------------------------
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true  # Auto-reload on code changes (dev only)

# Security
SECRET_KEY=your-secret-key-here-minimum-32-characters-long-and-random
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:3000

# ----------------------------------------------
# Database (PostgreSQL)
# ----------------------------------------------
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=definitie_user
POSTGRES_PASSWORD=your_secure_postgres_password_here
POSTGRES_DB=definitie_db

# Full connection string (auto-generated from above)
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_ECHO=false  # Set to true for SQL query logging

# ----------------------------------------------
# Redis Cache
# ----------------------------------------------
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password_here
REDIS_DB=0

# Full connection string
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# Cache settings
CACHE_TTL=3600  # Default TTL in seconds (1 hour)
CACHE_PREFIX=definitie:v2:
CACHE_ENABLED=true

# ----------------------------------------------
# OpenAI Configuration
# ----------------------------------------------
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_ORGANIZATION=  # Optional organization ID

# Model settings
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=500
OPENAI_TIMEOUT=30  # Seconds

# Rate limiting
OPENAI_MAX_RETRIES=3
OPENAI_RETRY_DELAY=1  # Seconds between retries
OPENAI_REQUESTS_PER_MINUTE=60

# ----------------------------------------------
# Validation Configuration
# ----------------------------------------------
VALIDATION_RULES_DIR=config/validation_rules
VALIDATION_CACHE_ENABLED=true
VALIDATION_CACHE_TTL=7200  # 2 hours

# Scoring weights
VALIDATION_WEIGHT_HIGH=1.0
VALIDATION_WEIGHT_MEDIUM=0.7
VALIDATION_WEIGHT_LOW=0.4

# Quality gates
VALIDATION_AUTO_ACCEPT_THRESHOLD=0.85
VALIDATION_REVIEW_THRESHOLD=0.70
VALIDATION_RETRY_THRESHOLD=0.50
VALIDATION_REJECT_THRESHOLD=0.50

# ----------------------------------------------
# Generation Configuration
# ----------------------------------------------
GENERATION_MAX_RETRIES=2
GENERATION_TIMEOUT=10  # Seconds for entire workflow

# Phase toggles
GENERATION_ENABLE_WEB_LOOKUP=true
GENERATION_ENABLE_EXAMPLES=true
GENERATION_ENABLE_DUPLICATE_CHECK=true

# Prompt settings
PROMPT_TEMPLATES_DIR=config/prompts
PROMPT_MAX_TOKENS=4000
PROMPT_CACHE_ENABLED=true

# ----------------------------------------------
# Web Lookup Configuration
# ----------------------------------------------
WEB_LOOKUP_ENABLED=true
WEB_LOOKUP_TIMEOUT=5  # Seconds per source

# Wikipedia
WIKIPEDIA_ENABLED=true
WIKIPEDIA_LANGUAGE=nl
WIKIPEDIA_MAX_SUMMARY_LENGTH=500

# SRU (Search/Retrieve via URL)
SRU_ENABLED=true
SRU_ENDPOINT=https://example.sru.nl/search
SRU_TIMEOUT=5

# ----------------------------------------------
# Performance Settings
# ----------------------------------------------
MAX_CONCURRENT_VALIDATIONS=10
MAX_CONCURRENT_GENERATIONS=5
REQUEST_TIMEOUT=30  # Seconds
WORKER_TIMEOUT=120  # Seconds

# ----------------------------------------------
# Monitoring & Logging
# ----------------------------------------------
LOG_FORMAT=json  # json or text
LOG_FILE_PATH=logs/app.log
LOG_FILE_MAX_SIZE=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=10

# Metrics
METRICS_ENABLED=false
METRICS_PORT=9090

# Sentry (optional error tracking)
SENTRY_DSN=
SENTRY_ENVIRONMENT=${ENVIRONMENT}

# ----------------------------------------------
# Feature Flags
# ----------------------------------------------
FEATURE_FLAG_NEW_VALIDATION_ENGINE=true
FEATURE_FLAG_PARALLEL_VALIDATION=false
FEATURE_FLAG_AI_FEEDBACK_LOOP=true
FEATURE_FLAG_ADVANCED_CACHING=true

# ----------------------------------------------
# Development Settings
# ----------------------------------------------
DEV_SKIP_AUTH=true  # Skip authentication in dev
DEV_MOCK_OPENAI=false  # Use mock responses instead of real API
DEV_SEED_DATABASE=true  # Seed with sample data on startup

# ----------------------------------------------
# Testing
# ----------------------------------------------
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db
TEST_REDIS_URL=redis://localhost:6379/1
TEST_OPENAI_API_KEY=sk-test-key
TEST_SKIP_SLOW=false  # Skip slow tests

# ----------------------------------------------
# Production Settings (only if ENVIRONMENT=production)
# ----------------------------------------------
PRODUCTION_ENABLE_HTTPS=true
PRODUCTION_CERT_PATH=/path/to/cert.pem
PRODUCTION_KEY_PATH=/path/to/key.pem
PRODUCTION_AUTO_MIGRATION=false  # Disable auto-migrations
PRODUCTION_READ_ONLY_MODE=false  # Emergency read-only mode
```

### B.3: Docker Compose Production

**File:** `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: definitie_postgres_prod
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: always
    networks:
      - definitie_network
    # No port exposure to host

  redis:
    image: redis:7-alpine
    container_name: definitie_redis_prod
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always
    networks:
      - definitie_network
    # No port exposure to host

  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: definitie_api_prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=WARNING
    volumes:
      - ./logs:/app/logs:rw
      - ./exports:/app/exports:rw
    restart: always
    depends_on:
      - postgres
      - redis
    networks:
      - definitie_network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  nginx:
    image: nginx:alpine
    container_name: definitie_nginx_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/usr/share/nginx/html/static:ro
    restart: always
    depends_on:
      - api
    networks:
      - definitie_network

networks:
  definitie_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

---

## Appendix C: Migration Scripts

### C.1: Data Migration from SQLite to PostgreSQL

**File:** `scripts/migrate_data.py`

```python
#!/usr/bin/env python3
"""Migrate data from legacy SQLite to new PostgreSQL database."""

import asyncio
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any

import asyncpg
from tqdm import tqdm

# Configuration
SQLITE_DB_PATH = "data/definities.db"
POSTGRES_DSN = "postgresql://definitie_user:password@localhost:5432/definitie_db"


async def migrate_definitions(sqlite_conn: sqlite3.Connection, pg_pool: asyncpg.Pool):
    """Migrate definitions table."""

    print("Migrating definitions...")

    # Extract from SQLite
    cursor = sqlite_conn.execute("""
        SELECT
            id, begrip, definitie, categorie,
            organisatorische_context, juridische_context, wettelijke_basis,
            ufo_categorie, status, version_number, previous_version_id,
            validation_score, validation_date, validation_issues,
            source_type, source_reference, imported_from,
            created_at, updated_at, created_by, updated_by,
            approved_by, approved_at, approval_notes,
            last_exported_at, export_destinations,
            datum_voorstel, ketenpartners, voorkeursterm, toelichting_proces
        FROM definities
        WHERE status != 'archived'
        ORDER BY id
    """)

    rows = cursor.fetchall()
    print(f"Found {len(rows)} definitions to migrate")

    # Insert into PostgreSQL
    migrated = 0
    failed = 0

    async with pg_pool.acquire() as conn:
        for row in tqdm(rows, desc="Migrating"):
            try:
                # Parse JSON fields
                org_context = json.loads(row[4]) if row[4] else []
                jur_context = json.loads(row[5]) if row[5] else []
                wet_basis = json.loads(row[6]) if row[6] else []
                validation_issues = json.loads(row[13]) if row[13] else None
                export_dest = json.loads(row[25]) if row[25] else None
                ketenpartners = json.loads(row[27]) if row[27] else None

                # Insert
                await conn.execute("""
                    INSERT INTO definities (
                        id, begrip, definitie, categorie,
                        organisatorische_context, juridische_context, wettelijke_basis,
                        ufo_categorie, status, version_number, previous_version_id,
                        validation_score, validation_date, validation_issues,
                        source_type, source_reference, imported_from,
                        created_at, updated_at, created_by, updated_by,
                        approved_by, approved_at, approval_notes,
                        last_exported_at, export_destinations,
                        datum_voorstel, ketenpartners, voorkeursterm, toelichting_proces
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                        $12, $13, $14, $15, $16, $17, $18, $19, $20, $21,
                        $22, $23, $24, $25, $26, $27, $28, $29, $30
                    )
                """,
                    row[0], row[1], row[2], row[3],
                    org_context, jur_context, wet_basis,
                    row[7], row[8], row[9], row[10],
                    row[11], row[12], validation_issues,
                    row[14], row[15], row[16],
                    row[17], row[18], row[19], row[20],
                    row[21], row[22], row[23],
                    row[24], export_dest,
                    row[26], ketenpartners, row[28], row[29]
                )

                migrated += 1

            except Exception as e:
                print(f"\nError migrating definition {row[0]} ({row[1]}): {e}")
                failed += 1

    print(f"\nDefinitions migration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Failed: {failed}")

    return migrated, failed


async def migrate_examples(sqlite_conn: sqlite3.Connection, pg_pool: asyncpg.Pool):
    """Migrate definition examples."""

    print("\nMigrating examples...")

    cursor = sqlite_conn.execute("""
        SELECT
            id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
            gegenereerd_door, generation_model, generation_parameters,
            actief, beoordeeld, beoordeeling, beoordeeling_notities,
            beoordeeld_door, beoordeeld_op,
            aangemaakt_op, bijgewerkt_op
        FROM definitie_voorbeelden
    """)

    rows = cursor.fetchall()
    print(f"Found {len(rows)} examples to migrate")

    migrated = 0
    failed = 0

    async with pg_pool.acquire() as conn:
        for row in tqdm(rows, desc="Migrating examples"):
            try:
                gen_params = json.loads(row[7]) if row[7] else None

                await conn.execute("""
                    INSERT INTO definitie_voorbeelden (
                        id, definitie_id, voorbeeld_type, voorbeeld_tekst, voorbeeld_volgorde,
                        gegenereerd_door, generation_model, generation_parameters,
                        actief, beoordeeld, beoordeeling, beoordeeling_notities,
                        beoordeeld_door, beoordeeld_op,
                        aangemaakt_op, bijgewerkt_op
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                """,
                    row[0], row[1], row[2], row[3], row[4],
                    row[5], row[6], gen_params,
                    row[8], row[9], row[10], row[11],
                    row[12], row[13],
                    row[14], row[15]
                )

                migrated += 1

            except Exception as e:
                print(f"\nError migrating example {row[0]}: {e}")
                failed += 1

    print(f"\nExamples migration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Failed: {failed}")

    return migrated, failed


async def migrate_history(sqlite_conn: sqlite3.Connection, pg_pool: asyncpg.Pool):
    """Migrate definition history."""

    print("\nMigrating history...")

    cursor = sqlite_conn.execute("""
        SELECT
            id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
            wijziging_type, wijziging_reden,
            gewijzigd_door, gewijzigd_op,
            context_snapshot
        FROM definitie_geschiedenis
    """)

    rows = cursor.fetchall()
    print(f"Found {len(rows)} history entries to migrate")

    migrated = 0
    failed = 0

    async with pg_pool.acquire() as conn:
        for row in tqdm(rows, desc="Migrating history"):
            try:
                context_snap = json.loads(row[9]) if row[9] else None

                await conn.execute("""
                    INSERT INTO definitie_geschiedenis (
                        id, definitie_id, begrip, definitie_oude_waarde, definitie_nieuwe_waarde,
                        wijziging_type, wijziging_reden,
                        gewijzigd_door, gewijzigd_op,
                        context_snapshot
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                    )
                """,
                    row[0], row[1], row[2], row[3], row[4],
                    row[5], row[6],
                    row[7], row[8],
                    context_snap
                )

                migrated += 1

            except Exception as e:
                print(f"\nError migrating history {row[0]}: {e}")
                failed += 1

    print(f"\nHistory migration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Failed: {failed}")

    return migrated, failed


async def migrate_tags(sqlite_conn: sqlite3.Connection, pg_pool: asyncpg.Pool):
    """Migrate definition tags."""

    print("\nMigrating tags...")

    cursor = sqlite_conn.execute("""
        SELECT
            id, definitie_id, tag_naam, tag_waarde,
            toegevoegd_door, toegevoegd_op
        FROM definitie_tags
    """)

    rows = cursor.fetchall()
    print(f"Found {len(rows)} tags to migrate")

    migrated = 0
    failed = 0

    async with pg_pool.acquire() as conn:
        for row in tqdm(rows, desc="Migrating tags"):
            try:
                await conn.execute("""
                    INSERT INTO definitie_tags (
                        id, definitie_id, tag_naam, tag_waarde,
                        toegevoegd_door, toegevoegd_op
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6
                    )
                """,
                    row[0], row[1], row[2], row[3],
                    row[4], row[5]
                )

                migrated += 1

            except Exception as e:
                print(f"\nError migrating tag {row[0]}: {e}")
                failed += 1

    print(f"\nTags migration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Failed: {failed}")

    return migrated, failed


async def verify_migration(sqlite_conn: sqlite3.Connection, pg_pool: asyncpg.Pool):
    """Verify migration completeness."""

    print("\n" + "="*50)
    print("MIGRATION VERIFICATION")
    print("="*50)

    async with pg_pool.acquire() as conn:
        # Count definitions
        sqlite_count = sqlite_conn.execute("SELECT COUNT(*) FROM definities").fetchone()[0]
        pg_count = await conn.fetchval("SELECT COUNT(*) FROM definities")

        print(f"\nDefinitions:")
        print(f"  SQLite: {sqlite_count}")
        print(f"  PostgreSQL: {pg_count}")
        print(f"  Match: {'✓ YES' if sqlite_count == pg_count else '✗ NO'}")

        # Count examples
        sqlite_count = sqlite_conn.execute("SELECT COUNT(*) FROM definitie_voorbeelden").fetchone()[0]
        pg_count = await conn.fetchval("SELECT COUNT(*) FROM definitie_voorbeelden")

        print(f"\nExamples:")
        print(f"  SQLite: {sqlite_count}")
        print(f"  PostgreSQL: {pg_count}")
        print(f"  Match: {'✓ YES' if sqlite_count == pg_count else '✗ NO'}")

        # Count history
        sqlite_count = sqlite_conn.execute("SELECT COUNT(*) FROM definitie_geschiedenis").fetchone()[0]
        pg_count = await conn.fetchval("SELECT COUNT(*) FROM definitie_geschiedenis")

        print(f"\nHistory:")
        print(f"  SQLite: {sqlite_count}")
        print(f"  PostgreSQL: {pg_count}")
        print(f"  Match: {'✓ YES' if sqlite_count == pg_count else '✗ NO'}")

        # Count tags
        sqlite_count = sqlite_conn.execute("SELECT COUNT(*) FROM definitie_tags").fetchone()[0]
        pg_count = await conn.fetchval("SELECT COUNT(*) FROM definitie_tags")

        print(f"\nTags:")
        print(f"  SQLite: {sqlite_count}")
        print(f"  PostgreSQL: {pg_count}")
        print(f"  Match: {'✓ YES' if sqlite_count == pg_count else '✗ NO'}")


async def main():
    """Main migration function."""

    print("="*50)
    print("DefinitieAgent Data Migration")
    print("SQLite → PostgreSQL")
    print("="*50)

    # Connect to SQLite
    print(f"\nConnecting to SQLite: {SQLITE_DB_PATH}")
    if not Path(SQLITE_DB_PATH).exists():
        print(f"ERROR: SQLite database not found: {SQLITE_DB_PATH}")
        return

    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)

    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL: {POSTGRES_DSN}")
    try:
        pg_pool = await asyncpg.create_pool(POSTGRES_DSN, min_size=5, max_size=20)
    except Exception as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        sqlite_conn.close()
        return

    try:
        # Run migrations
        await migrate_definitions(sqlite_conn, pg_pool)
        await migrate_examples(sqlite_conn, pg_pool)
        await migrate_history(sqlite_conn, pg_pool)
        await migrate_tags(sqlite_conn, pg_pool)

        # Verify
        await verify_migration(sqlite_conn, pg_pool)

        print("\n" + "="*50)
        print("MIGRATION COMPLETE")
        print("="*50)

    finally:
        # Cleanup
        sqlite_conn.close()
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Appendix D: Testing Procedures

### D.1: Baseline Validation Test

**File:** `tests/baseline/test_baseline_validation.py`

```python
"""Baseline validation tests.

Tests that the new system validates the 42 production definitions
at least as well as the legacy system.
"""

import pytest
from typing import List, Dict

from app.services.validation_service import ValidationService
from app.schemas.validation import ValidationRequest, ValidationResult

# Import fixtures
from tests.baseline.fixtures.baseline_definitions import (
    baseline_definitions,
    baseline_high_quality,
    baseline_edge_cases,
)


@pytest.mark.baseline
@pytest.mark.asyncio
async def test_baseline_pass_rate(
    validation_service: ValidationService,
    baseline_definitions: List[Dict],
):
    """Test that at least 90% of baseline definitions pass validation."""

    total = len(baseline_definitions)
    passed = 0
    failed = 0
    results = []

    for defn in baseline_definitions:
        request = ValidationRequest(
            begrip=defn["begrip"],
            text=defn["definitie"],
            ontologische_categorie=defn.get("categorie"),
        )

        result = await validation_service.validate(request)
        results.append({
            "begrip": defn["begrip"],
            "score": result.score,
            "passed": result.score >= 0.7,
        })

        if result.score >= 0.7:
            passed += 1
        else:
            failed += 1

    pass_rate = passed / total
    avg_score = sum(r["score"] for r in results) / total

    # Assertions
    assert pass_rate >= 0.90, f"Pass rate {pass_rate:.2%} below 90% threshold"
    assert avg_score >= 0.80, f"Average score {avg_score:.2f} below 0.80 threshold"

    # Report
    print(f"\nBaseline Validation Results:")
    print(f"  Total definitions: {total}")
    print(f"  Passed (>= 0.7): {passed} ({pass_rate:.2%})")
    print(f"  Failed (< 0.7): {failed}")
    print(f"  Average score: {avg_score:.2f}")

    # Show failures for debugging
    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\nFailed definitions:")
        for f in failures[:5]:  # Show first 5
            print(f"  - {f['begrip']}: {f['score']:.2f}")


@pytest.mark.baseline
@pytest.mark.asyncio
async def test_high_quality_100_percent_pass(
    validation_service: ValidationService,
    baseline_high_quality: List[Dict],
):
    """Test that 100% of high-quality definitions pass."""

    total = len(baseline_high_quality)
    passed = 0

    for defn in baseline_high_quality:
        request = ValidationRequest(
            begrip=defn["begrip"],
            text=defn["definitie"],
            ontologische_categorie=defn.get("categorie"),
        )

        result = await validation_service.validate(request)

        if result.score >= 0.7:
            passed += 1
        else:
            print(f"\nHigh-quality definition FAILED: {defn['begrip']} (score: {result.score:.2f})")

    pass_rate = passed / total

    assert pass_rate == 1.0, f"High-quality pass rate {pass_rate:.2%} not 100%"


@pytest.mark.baseline
@pytest.mark.slow
@pytest.mark.asyncio
async def test_no_regression_in_scores(
    validation_service: ValidationService,
    baseline_definitions: List[Dict],
):
    """Test that validation scores don't regress from legacy system."""

    regressions = []

    for defn in baseline_definitions:
        legacy_score = defn.get("validation_score")
        if not legacy_score:
            continue  # Skip if no legacy score

        request = ValidationRequest(
            begrip=defn["begrip"],
            text=defn["definitie"],
            ontologische_categorie=defn.get("categorie"),
        )

        result = await validation_service.validate(request)
        new_score = result.score

        # Allow 5% tolerance
        if new_score < legacy_score - 0.05:
            regressions.append({
                "begrip": defn["begrip"],
                "legacy_score": legacy_score,
                "new_score": new_score,
                "diff": new_score - legacy_score,
            })

    # Report regressions
    if regressions:
        print(f"\nFound {len(regressions)} score regressions:")
        for r in regressions[:10]:
            print(f"  - {r['begrip']}: {r['legacy_score']:.2f} → {r['new_score']:.2f} ({r['diff']:+.2f})")

    # Allow up to 10% regressions
    max_allowed_regressions = int(len(baseline_definitions) * 0.10)
    assert len(regressions) <= max_allowed_regressions, \
        f"Too many score regressions: {len(regressions)} > {max_allowed_regressions}"
```

### D.2: Performance Test

**File:** `tests/performance/test_response_times.py`

```python
"""Performance tests for response time requirements."""

import pytest
import time
from statistics import mean, median, stdev

from app.services.validation_service import ValidationService
from app.services.generation_service import GenerationService
from app.schemas.validation import ValidationRequest
from app.schemas.generation import GenerationRequest


@pytest.mark.performance
@pytest.mark.asyncio
async def test_validation_response_time(validation_service: ValidationService):
    """Test that validation completes in < 500ms."""

    test_cases = [
        {
            "begrip": "verificatie",
            "text": "Een systematische controle van identiteitsgegevens",
        },
        {
            "begrip": "registratie",
            "text": "De handeling waarbij gegevens worden vastgelegd",
        },
        # Add more test cases...
    ]

    times = []

    for case in test_cases:
        request = ValidationRequest(**case)

        start = time.time()
        result = await validation_service.validate(request)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        times.append(elapsed)

    avg_time = mean(times)
    max_time = max(times)

    print(f"\nValidation Performance:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Median: {median(times):.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    print(f"  StdDev: {stdev(times):.2f}ms")

    assert avg_time < 500, f"Average validation time {avg_time:.2f}ms exceeds 500ms target"
    assert max_time < 1000, f"Max validation time {max_time:.2f}ms exceeds 1000ms limit"


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_generation_response_time(generation_service: GenerationService):
    """Test that generation completes in < 2000ms."""

    test_cases = [
        {"begrip": "test_begrip_1"},
        {"begrip": "test_begrip_2"},
        # Add more...
    ]

    times = []

    for case in test_cases:
        request = GenerationRequest(**case)

        start = time.time()
        result = await generation_service.generate(request)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        times.append(elapsed)

    avg_time = mean(times)
    max_time = max(times)

    print(f"\nGeneration Performance:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Median: {median(times):.2f}ms")
    print(f"  Max: {max_time:.2f}ms")

    assert avg_time < 2000, f"Average generation time {avg_time:.2f}ms exceeds 2000ms target"
    assert max_time < 5000, f"Max generation time {max_time:.2f}ms exceeds 5000ms limit"
```

---

## Appendix E: Deployment Checklist

### Production Deployment Checklist

```markdown
# DefinitieAgent v2.0 Production Deployment Checklist

## Pre-Deployment (T-7 days)

### Code & Testing
- [ ] All tests passing (unit, integration, baseline)
- [ ] Test coverage >= 85%
- [ ] No critical or high-priority bugs
- [ ] Code review completed and approved
- [ ] Performance benchmarks met (<2s generation, <500ms validation)
- [ ] 42 baseline definitions validating at >= 90%

### Infrastructure
- [ ] Production server provisioned and configured
- [ ] SSL certificates installed and valid
- [ ] Domain name configured and DNS propagated
- [ ] Firewall rules configured
- [ ] Backup system tested and working
- [ ] Monitoring tools installed (logs, metrics, alerts)

### Database
- [ ] PostgreSQL production instance running
- [ ] Database migrations tested and ready
- [ ] Data migration from SQLite tested successfully
- [ ] Database backups automated and tested
- [ ] Connection pooling configured
- [ ] Database indexes optimized

### Security
- [ ] All secrets stored in secure vault (not in code)
- [ ] API keys rotated for production
- [ ] HTTPS enforced
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Dependency vulnerabilities scanned and resolved

### Documentation
- [ ] API documentation up to date
- [ ] User guide completed
- [ ] Admin guide completed
- [ ] Runbook for common operations
- [ ] Incident response plan documented
- [ ] Rollback procedure documented

## Deployment Day (T-0)

### Pre-Deployment (09:00 - 10:00)
- [ ] Announce maintenance window to users
- [ ] Create backup of current production database
- [ ] Tag release in git (e.g., v2.0.0)
- [ ] Build and test Docker images
- [ ] Run final smoke tests

### Deployment (10:00 - 12:00)
- [ ] Pull latest code to production server
- [ ] Build production Docker images
- [ ] Stop current services (if any)
- [ ] Run database migrations
- [ ] Migrate data from SQLite to PostgreSQL
- [ ] Start new services (docker-compose up)
- [ ] Verify all services healthy
- [ ] Run smoke tests on production

### Post-Deployment (12:00 - 13:00)
- [ ] Verify health endpoints responding
- [ ] Test critical user workflows
- [ ] Check logs for errors
- [ ] Monitor resource usage (CPU, memory, disk)
- [ ] Verify database connections
- [ ] Test API endpoints with real data
- [ ] Announce deployment complete

## Post-Deployment (T+1 day)

### Monitoring
- [ ] Check error logs for unexpected issues
- [ ] Monitor API response times
- [ ] Monitor database performance
- [ ] Check OpenAI API usage and costs
- [ ] Verify no data loss or corruption
- [ ] Review user feedback

### Performance
- [ ] Verify <2s generation time
- [ ] Verify <500ms validation time
- [ ] Check cache hit rates
- [ ] Monitor concurrent user capacity
- [ ] Review and optimize slow queries

## Post-Deployment (T+7 days)

### Validation
- [ ] All baseline definitions still validating correctly
- [ ] User acceptance testing completed
- [ ] Performance metrics meeting targets
- [ ] No critical issues reported
- [ ] Resource usage within expected range

### Documentation
- [ ] Update deployment log
- [ ] Document any issues encountered
- [ ] Update runbook with lessons learned
- [ ] Share deployment report with stakeholders

## Rollback Plan

If critical issues occur:

1. **Stop services:**
   ```bash
   docker-compose down
   ```

2. **Restore database backup:**
   ```bash
   psql -U user -d definitie_db < backup_YYYYMMDD.sql
   ```

3. **Revert to previous version:**
   ```bash
   git checkout <previous-tag>
   docker-compose up -d
   ```

4. **Verify rollback:**
   - Check health endpoints
   - Test critical workflows
   - Verify data integrity

5. **Investigate:**
   - Review logs
   - Identify root cause
   - Document for post-mortem
```

---

**End of Appendices**

This completes the comprehensive rebuild execution plan documentation. All appendices provide the necessary templates, configurations, scripts, and procedures to execute the 9-10 week rebuild successfully.
