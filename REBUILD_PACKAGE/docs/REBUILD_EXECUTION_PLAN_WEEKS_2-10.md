# DefinitieAgent Rebuild Execution Plan - Weeks 2-10

*Continuation of REBUILD_EXECUTION_PLAN.md*

---

## Week 2: Modern Stack Setup & Infrastructure
**Goal:** Build complete development environment with Docker, FastAPI, PostgreSQL, Redis
**Hours:** 40 hours (8h/day × 5 days)
**Success Criteria:** Working local environment + CI/CD pipeline + green smoke tests

### Day 5 - Monday: Docker & Development Environment (8h)

#### Morning Session (4h): Docker Setup

**Tasks:**
1. Create Dockerfile for FastAPI application
2. Create docker-compose.yml with all services
3. Setup development vs production configurations
4. Configure volume mounts and networking

**File: Dockerfile**
```dockerfile
# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File: docker-compose.yml**
```yaml
version: '3.8'

services:
  # PostgreSQL database
  postgres:
    image: postgres:15-alpine
    container_name: definitie_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-definitie_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-definitie_pass}
      POSTGRES_DB: ${POSTGRES_DB:-definitie_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-definitie_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - definitie_network

  # Redis cache
  redis:
    image: redis:7-alpine
    container_name: definitie_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redis_pass}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - definitie_network

  # FastAPI application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: definitie_api
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-definitie_user}:${POSTGRES_PASSWORD:-definitie_pass}@postgres:5432/${POSTGRES_DB:-definitie_db}
      - REDIS_URL=redis://:${REDIS_PASSWORD:-redis_pass}@redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app  # Hot reload for development
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - definitie_network

  # Streamlit UI (optional, for development)
  ui:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: definitie_ui
    environment:
      - API_URL=http://api:8000
      - STREAMLIT_SERVER_PORT=8501
    ports:
      - "8501:8501"
    volumes:
      - ./ui:/app/ui
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

**File: docker-compose.dev.yml**
```yaml
# Development overrides
version: '3.8'

services:
  api:
    build:
      target: builder  # Use builder stage for dev tools
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./app:/app/app:ro  # Mount source code read-only
      - ./tests:/app/tests:ro

  postgres:
    ports:
      - "5432:5432"  # Expose for local tools
    environment:
      - POSTGRES_DB=definitie_db_dev

  redis:
    command: redis-server --appendonly yes --requirepass redis_pass --loglevel debug
```

**File: .env.example**
```bash
# Database
POSTGRES_USER=definitie_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=definitie_db

# Redis
REDIS_PASSWORD=your_redis_password_here

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=false

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:3000
```

**Commands:**
```bash
# Create .env file from template
cp .env.example .env

# Edit .env with real values (especially OPENAI_API_KEY)
# Use your favorite editor to set OPENAI_API_KEY

# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f api

# Verify services are running
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "2.0.0"}
```

**Validation Checklist:**
- [ ] All services build successfully
- [ ] PostgreSQL accepts connections
- [ ] Redis accepts connections
- [ ] API health endpoint returns 200
- [ ] Hot reload works (edit app/main.py and see changes)

---

#### Afternoon Session (4h): FastAPI Application Skeleton

**Tasks:**
1. Create FastAPI application structure
2. Setup database connection
3. Configure logging and monitoring
4. Create health and status endpoints

**File: app/main.py**
```python
"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.db.session import engine, init_db

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting DefinitieAgent API...")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down DefinitieAgent API...")
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="DefinitieAgent API",
    description="AI-powered Dutch legal definition generator",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "DefinitieAgent API v2.0",
        "docs": "/api/docs",
        "health": "/health",
    }
```

**File: app/core/config.py**
```python
"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # API
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=4, env="API_WORKERS")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")

    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4", env="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    OPENAI_MAX_TOKENS: int = Field(default=500, env="OPENAI_MAX_TOKENS")

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:8501"],
        env="ALLOWED_ORIGINS"
    )

    # Performance
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    MAX_CONCURRENT_VALIDATIONS: int = Field(default=10, env="MAX_CONCURRENT_VALIDATIONS")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

**File: app/core/logging.py**
```python
"""Logging configuration."""

import logging
import sys
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """Configure application logging."""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log"),
        ],
    )

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
```

**File: app/db/session.py**
```python
"""Database session management."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables if not exist)."""
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered
        from app.models import definition  # noqa: F401

        # Create tables
        await conn.run_sync(Base.metadata.create_all)
```

**File: app/api/v1/__init__.py**
```python
"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    definitions,
    validation,
    generation,
    health,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(definitions.router, prefix="/definitions", tags=["Definitions"])
api_router.include_router(validation.router, prefix="/validation", tags=["Validation"])
api_router.include_router(generation.router, prefix="/generation", tags=["Generation"])
```

**File: app/api/v1/endpoints/health.py**
```python
"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status."""

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check Redis (TODO: implement when cache service is ready)
    redis_status = "not_implemented"

    # Check OpenAI (just verify key is set)
    openai_status = "configured" if settings.OPENAI_API_KEY else "not_configured"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
            "openai": openai_status,
        },
    }
```

**Commands:**
```bash
# Create directory structure
mkdir -p app/{api/v1/endpoints,core,db,models,schemas,services,utils}

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/core/__init__.py
touch app/db/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py

# Rebuild and restart API
docker-compose down
docker-compose up -d --build api

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health/
curl http://localhost:8000/api/v1/health/detailed

# Check API docs
open http://localhost:8000/api/docs
```

**Validation Checklist:**
- [ ] API starts without errors
- [ ] Health endpoints return 200
- [ ] Database connection works
- [ ] API docs accessible at /api/docs
- [ ] Logs visible in docker-compose logs

**End of Day 5 Commit:**
```bash
git add Dockerfile docker-compose.yml app/
git commit -m "feat(infra): setup Docker + FastAPI skeleton with health checks"
```

---

### Day 6 - Tuesday: Database & Migrations (8h)

#### Morning Session (4h): Database Models

**Tasks:**
1. Create SQLAlchemy models for definitions
2. Setup Alembic for migrations
3. Create initial migration
4. Test database operations

**File: app/models/definition.py**
```python
"""Definition database model."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Numeric, Boolean, JSON, CheckConstraint
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Definition(Base):
    """Definition model."""

    __tablename__ = "definities"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Core fields
    begrip = Column(String(255), nullable=False, index=True)
    definitie = Column(Text, nullable=False)
    categorie = Column(
        String(50),
        nullable=False,
        index=True,
        # ENT, ACT, REL, ATT, AUT, STA, OTH
    )

    # Context (stored as JSON arrays)
    organisatorische_context = Column(JSON, default=list)
    juridische_context = Column(JSON, default=list)
    wettelijke_basis = Column(JSON, default=list)

    # UFO category
    ufo_categorie = Column(String(50), nullable=True)

    # Status
    status = Column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
        # draft, review, established, archived
    )

    # Versioning
    version_number = Column(Integer, nullable=False, default=1)
    previous_version_id = Column(Integer, nullable=True)

    # Validation
    validation_score = Column(Numeric(3, 2), nullable=True)
    validation_date = Column(DateTime, nullable=True)
    validation_issues = Column(JSON, nullable=True)

    # Source tracking
    source_type = Column(
        String(50),
        default="generated",
        # generated, imported, manual
    )
    source_reference = Column(String(500), nullable=True)
    imported_from = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    # Approval
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Export tracking
    last_exported_at = Column(DateTime, nullable=True)
    export_destinations = Column(JSON, nullable=True)

    # Legacy fields
    datum_voorstel = Column(DateTime, nullable=True)
    ketenpartners = Column(JSON, nullable=True)

    # Voorkeursterm
    voorkeursterm = Column(Text, nullable=True)

    # Process notes
    toelichting_proces = Column(Text, nullable=True)

    # Relationships
    examples = relationship("DefinitionExample", back_populates="definition", cascade="all, delete-orphan")
    history = relationship("DefinitionHistory", back_populates="definition", cascade="all, delete-orphan")
    tags = relationship("DefinitionTag", back_populates="definition", cascade="all, delete-orphan")


class DefinitionExample(Base):
    """Definition examples model."""

    __tablename__ = "definitie_voorbeelden"

    id = Column(Integer, primary_key=True, index=True)
    definitie_id = Column(Integer, nullable=False, index=True)

    # Example data
    voorbeeld_type = Column(
        String(50),
        nullable=False,
        # sentence, practical, counter, synonyms, antonyms, explanation
    )
    voorbeeld_tekst = Column(Text, nullable=False)
    voorbeeld_volgorde = Column(Integer, default=1)

    # Generation metadata
    gegenereerd_door = Column(String(50), default="system")
    generation_model = Column(String(50), nullable=True)
    generation_parameters = Column(JSON, nullable=True)

    # Status
    actief = Column(Boolean, nullable=False, default=True)
    beoordeeld = Column(Boolean, nullable=False, default=False)
    beoordeeling = Column(String(50), nullable=True)
    beoordeeling_notities = Column(Text, nullable=True)
    beoordeeld_door = Column(String(255), nullable=True)
    beoordeeld_op = Column(DateTime, nullable=True)

    # Timestamps
    aangemaakt_op = Column(DateTime, nullable=False, default=datetime.utcnow)
    bijgewerkt_op = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    definition = relationship("Definition", back_populates="examples")


class DefinitionHistory(Base):
    """Definition change history model."""

    __tablename__ = "definitie_geschiedenis"

    id = Column(Integer, primary_key=True, index=True)
    definitie_id = Column(Integer, nullable=False, index=True)

    # Snapshot
    begrip = Column(String(255), nullable=False)
    definitie_oude_waarde = Column(Text, nullable=True)
    definitie_nieuwe_waarde = Column(Text, nullable=True)

    # Change metadata
    wijziging_type = Column(
        String(50),
        nullable=False,
        # created, updated, status_changed, approved, archived, auto_save
    )
    wijziging_reden = Column(Text, nullable=True)

    # User info
    gewijzigd_door = Column(String(255), nullable=True)
    gewijzigd_op = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Context snapshot
    context_snapshot = Column(JSON, nullable=True)

    # Relationship
    definition = relationship("Definition", back_populates="history")


class DefinitionTag(Base):
    """Definition tags model."""

    __tablename__ = "definitie_tags"

    id = Column(Integer, primary_key=True, index=True)
    definitie_id = Column(Integer, nullable=False, index=True)

    tag_naam = Column(String(100), nullable=False, index=True)
    tag_waarde = Column(String(255), nullable=True)

    # Metadata
    toegevoegd_door = Column(String(255), nullable=True)
    toegevoegd_op = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    definition = relationship("Definition", back_populates="tags")
```

**File: alembic.ini**
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql://definitie_user:definitie_pass@localhost:5432/definitie_db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Commands:**
```bash
# Initialize Alembic
docker-compose exec api alembic init alembic

# Edit alembic/env.py to import models
# (see next file)

# Create initial migration
docker-compose exec api alembic revision --autogenerate -m "Initial schema"

# Apply migration
docker-compose exec api alembic upgrade head

# Verify tables created
docker-compose exec postgres psql -U definitie_user -d definitie_db -c "\dt"

# Expected tables:
# - definities
# - definitie_voorbeelden
# - definitie_geschiedenis
# - definitie_tags
# - alembic_version
```

**File: alembic/env.py**
```python
"""Alembic environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings
from app.db.session import Base
from app.models import definition  # Import all models

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata
target_metadata = Base.metadata

# Override sqlalchemy.url with environment variable
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

#### Afternoon Session (4h): Database Layer & Repository Pattern

**Tasks:**
1. Create repository pattern for database access
2. Implement CRUD operations
3. Add caching layer
4. Create database utilities

**File: app/repositories/definition_repository.py**
```python
"""Definition repository for database operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.definition import Definition, DefinitionExample, DefinitionHistory
from app.schemas.definition import DefinitionCreate, DefinitionUpdate


class DefinitionRepository:
    """Repository for definition database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, definition: DefinitionCreate) -> Definition:
        """Create a new definition."""

        db_definition = Definition(
            begrip=definition.begrip,
            definitie=definition.definitie,
            categorie=definition.categorie,
            organisatorische_context=definition.organisatorische_context or [],
            juridische_context=definition.juridische_context or [],
            wettelijke_basis=definition.wettelijke_basis or [],
            status="draft",
            source_type="generated",
            created_by=definition.created_by,
        )

        self.db.add(db_definition)
        await self.db.commit()
        await self.db.refresh(db_definition)

        # Create history entry
        await self._create_history_entry(
            db_definition.id,
            "created",
            None,
            definition.definitie,
            definition.created_by,
        )

        return db_definition

    async def get_by_id(self, definition_id: int) -> Optional[Definition]:
        """Get definition by ID."""

        result = await self.db.execute(
            select(Definition).where(Definition.id == definition_id)
        )
        return result.scalar_one_or_none()

    async def get_by_begrip(self, begrip: str) -> List[Definition]:
        """Get all definitions for a given begrip."""

        result = await self.db.execute(
            select(Definition)
            .where(Definition.begrip == begrip)
            .where(Definition.status != "archived")
            .order_by(Definition.version_number.desc())
        )
        return result.scalars().all()

    async def get_latest_by_begrip(self, begrip: str) -> Optional[Definition]:
        """Get latest definition for a given begrip."""

        definitions = await self.get_by_begrip(begrip)
        return definitions[0] if definitions else None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        categorie: Optional[str] = None,
    ) -> List[Definition]:
        """Get all definitions with optional filters."""

        query = select(Definition)

        # Apply filters
        if status:
            query = query.where(Definition.status == status)
        if categorie:
            query = query.where(Definition.categorie == categorie)

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self, definition_id: int, update_data: DefinitionUpdate, updated_by: Optional[str] = None
    ) -> Optional[Definition]:
        """Update a definition."""

        # Get existing definition
        db_definition = await self.get_by_id(definition_id)
        if not db_definition:
            return None

        # Store old value for history
        old_value = db_definition.definitie

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_definition, field, value)

        db_definition.updated_at = datetime.utcnow()
        if updated_by:
            db_definition.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(db_definition)

        # Create history entry
        await self._create_history_entry(
            definition_id,
            "updated",
            old_value,
            db_definition.definitie,
            updated_by,
        )

        return db_definition

    async def delete(self, definition_id: int) -> bool:
        """Delete a definition (soft delete by archiving)."""

        db_definition = await self.get_by_id(definition_id)
        if not db_definition:
            return False

        db_definition.status = "archived"
        db_definition.updated_at = datetime.utcnow()

        await self.db.commit()
        return True

    async def search(
        self, query: str, limit: int = 20
    ) -> List[Definition]:
        """Search definitions by text."""

        # Simple text search (can be enhanced with full-text search)
        result = await self.db.execute(
            select(Definition)
            .where(
                or_(
                    Definition.begrip.ilike(f"%{query}%"),
                    Definition.definitie.ilike(f"%{query}%"),
                )
            )
            .where(Definition.status != "archived")
            .limit(limit)
        )
        return result.scalars().all()

    async def find_duplicates(
        self, begrip: str, definitie: str, threshold: float = 0.95
    ) -> List[Definition]:
        """Find potential duplicate definitions."""

        # Exact match
        result = await self.db.execute(
            select(Definition)
            .where(Definition.begrip == begrip)
            .where(Definition.definitie == definitie)
            .where(Definition.status != "archived")
        )
        exact_matches = result.scalars().all()

        if exact_matches:
            return exact_matches

        # TODO: Implement fuzzy matching with similarity threshold
        # For now, return empty list
        return []

    async def get_statistics(self) -> Dict[str, Any]:
        """Get definition statistics."""

        # Total counts
        total_result = await self.db.execute(select(func.count(Definition.id)))
        total = total_result.scalar()

        # By status
        status_result = await self.db.execute(
            select(Definition.status, func.count(Definition.id))
            .group_by(Definition.status)
        )
        by_status = {status: count for status, count in status_result}

        # By category
        category_result = await self.db.execute(
            select(Definition.categorie, func.count(Definition.id))
            .group_by(Definition.categorie)
        )
        by_category = {cat: count for cat, count in category_result}

        # Average validation score
        score_result = await self.db.execute(
            select(func.avg(Definition.validation_score))
            .where(Definition.validation_score.isnot(None))
        )
        avg_score = score_result.scalar() or 0.0

        return {
            "total": total,
            "by_status": by_status,
            "by_category": by_category,
            "average_validation_score": float(avg_score),
        }

    async def _create_history_entry(
        self,
        definition_id: int,
        wijziging_type: str,
        old_value: Optional[str],
        new_value: Optional[str],
        changed_by: Optional[str],
    ) -> DefinitionHistory:
        """Create a history entry for a definition change."""

        history_entry = DefinitionHistory(
            definitie_id=definition_id,
            begrip="",  # Will be filled from definition
            definitie_oude_waarde=old_value,
            definitie_nieuwe_waarde=new_value,
            wijziging_type=wijziging_type,
            gewijzigd_door=changed_by,
        )

        self.db.add(history_entry)
        await self.db.commit()

        return history_entry
```

**File: app/schemas/definition.py**
```python
"""Pydantic schemas for definitions."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DefinitionBase(BaseModel):
    """Base definition schema."""

    begrip: str = Field(..., min_length=2, max_length=255)
    definitie: str = Field(..., min_length=20, max_length=1000)
    categorie: str = Field(..., pattern="^(ENT|ACT|REL|ATT|AUT|STA|OTH)$")

    organisatorische_context: Optional[List[str]] = None
    juridische_context: Optional[List[str]] = None
    wettelijke_basis: Optional[List[str]] = None

    ufo_categorie: Optional[str] = None
    voorkeursterm: Optional[str] = None


class DefinitionCreate(DefinitionBase):
    """Schema for creating a definition."""

    created_by: Optional[str] = None


class DefinitionUpdate(BaseModel):
    """Schema for updating a definition."""

    definitie: Optional[str] = None
    categorie: Optional[str] = None
    status: Optional[str] = None

    organisatorische_context: Optional[List[str]] = None
    juridische_context: Optional[List[str]] = None
    wettelijke_basis: Optional[List[str]] = None

    validation_score: Optional[float] = None
    validation_issues: Optional[List[dict]] = None


class DefinitionResponse(DefinitionBase):
    """Schema for definition response."""

    id: int
    status: str
    version_number: int

    validation_score: Optional[float] = None
    validation_date: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
```

**Commands:**
```bash
# Create repository tests
cat > tests/test_definition_repository.py << 'EOF'
import pytest
from app.repositories.definition_repository import DefinitionRepository
from app.schemas.definition import DefinitionCreate

@pytest.mark.asyncio
async def test_create_definition(db_session):
    """Test creating a definition."""
    repo = DefinitionRepository(db_session)

    definition_data = DefinitionCreate(
        begrip="test_begrip",
        definitie="Een test definitie voor validatie",
        categorie="ENT",
        created_by="test_user",
    )

    definition = await repo.create(definition_data)

    assert definition.id is not None
    assert definition.begrip == "test_begrip"
    assert definition.status == "draft"
    assert definition.version_number == 1

@pytest.mark.asyncio
async def test_get_by_id(db_session):
    """Test getting definition by ID."""
    repo = DefinitionRepository(db_session)

    # Create definition
    definition_data = DefinitionCreate(
        begrip="test_get",
        definitie="Test definitie ophalen",
        categorie="ACT",
    )
    created = await repo.create(definition_data)

    # Retrieve it
    retrieved = await repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.begrip == "test_get"
EOF

# Run repository tests
docker-compose exec api pytest tests/test_definition_repository.py -v
```

**End of Day 6 Commit:**
```bash
git add app/models/ app/repositories/ app/schemas/ alembic/
git commit -m "feat(db): implement database models, migrations, and repository pattern"
```

---

### Day 7 - Wednesday: CI/CD Pipeline (8h)

[Continue with CI/CD setup, GitHub Actions, automated testing...]

---

## Week 3-4: Core MVP Implementation

[Continue with detailed daily breakdown of core services...]

---

## Week 5-6: Advanced Features

[Continue with detailed daily breakdown of advanced features...]

---

## Week 7-8: UI & Migration

[Continue with detailed daily breakdown of UI and data migration...]

---

## Week 9: Testing & Validation

[Continue with detailed daily breakdown of final testing...]

---

## Week 10: Buffer & Polish

[Continue with buffer week activities...]

---

## Appendices

### Appendix A: Complete File Structure

```
definitie-app/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── definitions.py
│   │           ├── validation.py
│   │           ├── generation.py
│   │           └── health.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   ├── models/
│   │   ├── definition.py
│   │   └── __init__.py
│   ├── repositories/
│   │   ├── definition_repository.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── definition.py
│   │   └── validation.py
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── validation_service.py
│   │   ├── generation_service.py
│   │   ├── cache_service.py
│   │   └── __init__.py
│   └── utils/
│       ├── text_processing.py
│       └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── test_validation.py
│   ├── test_generation.py
│   └── test_repository.py
├── config/
│   └── validation_rules/
│       ├── arai/
│       ├── con/
│       ├── ess/
│       ├── int/
│       ├── sam/
│       ├── str/
│       └── ver/
├── alembic/
│   ├── versions/
│   └── env.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

### Appendix B: Complete Configuration Examples

[Configuration file templates...]

### Appendix C: Migration Scripts

[Data migration procedures...]

### Appendix D: Testing Procedures

[Complete testing methodology...]

### Appendix E: Deployment Checklist

[Production deployment steps...]

