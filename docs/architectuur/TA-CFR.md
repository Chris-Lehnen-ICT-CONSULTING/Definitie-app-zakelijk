---
canonical: false
status: active
owner: architecture
last_verified: 2025-09-04
applies_to: definitie-app@v2-cfr
---

# Technical Architecture - Context Flow Refactoring (Epic CFR)

## Executive Summary

This Technical Architecture specifies the implementation details, technology stack, infrastructure requirements, and non-functional requirements for the Context Flow Refactoring. It provides concrete technical solutions for the single-path context flow with full type safety and ASTRA compliance.

## Context & Scope

The technical implementation focuses on Python/Streamlit for the UI, FastAPI for services, PostgreSQL for persistence, and Docker for containerization, ensuring compatibility with existing government IT infrastructure.

## Architecture Decisions

### Technology Stack Selection

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | Streamlit 1.28+ | Government approved, already in use |
| Backend Services | FastAPI 0.104+ | Async support, OpenAPI generation |
| Database | PostgreSQL 15+ | ACID compliance, JSON support |
| Caching | Redis 7.0+ | Session management, performance |
| Container | Docker 24+ | Standardized deployment |
| Orchestration | Docker Compose | Simple multi-container management |
| Monitoring | Prometheus + Grafana | Government standard monitoring |
| Logging | Structured logging (JSON) | Elasticsearch integration ready |

## Technical Solution

### 1. Context Data Model Implementation

```python
# src/models/context_models.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ContextType(Enum):
    ORGANISATORISCH = "organisatorisch"
    JURIDISCH = "juridisch"
    WETTELIJK = "wettelijk"

@dataclass
class ContextData:
    """UI Layer context data model"""
    organisatorische_context: List[str] = field(default_factory=list)
    juridische_context: List[str] = field(default_factory=list)
    wettelijke_basis: List[str] = field(default_factory=list)
    custom_entries: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "organisatorische_context": self.organisatorische_context,
            "juridische_context": self.juridische_context,
            "wettelijke_basis": self.wettelijke_basis,
            "custom_entries": self.custom_entries or {},
            "metadata": self.metadata or {}
        }

@dataclass
class ValidatedContext:
    """Validated context after processing"""
    organisatorische_context: List[str]
    juridische_context: List[str]
    wettelijke_basis: List[str]
    validation_metadata: Dict[str, Any]

    @property
    def is_complete(self) -> bool:
        """Check if minimum required context is present"""
        return bool(self.organisatorische_context)
```

### 2. Context Validator Implementation

```python
# src/services/validation/context_validator.py
import re
from typing import List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class ContextValidator:
    """Validates and sanitizes context data"""

    # Prevent injection attacks
    INVALID_CHARS_PATTERN = re.compile(r'[<>\"\'%;()&+]')
    MAX_CUSTOM_LENGTH = 100

    # Vocabulary validation
    VALID_ORGANISATIONS = {
        "OM", "ZM", "DJI", "KMAR", "NP", "JUSTID",
        "FIOD", "CJIB", "Reclassering"
    }

    VALID_JURIDICAL = {
        "Strafrecht", "Civiel recht", "Bestuursrecht",
        "Internationaal recht", "Europees recht", "Migratierecht"
    }

    async def validate(self, data: ContextData) -> ValidatedContext:
        """Main validation entry point"""
        try:
            # Ensure all fields are lists
            org_context = self._ensure_list_type(
                data.organisatorische_context
            )
            jur_context = self._ensure_list_type(
                data.juridische_context
            )
            wet_basis = self._ensure_list_type(
                data.wettelijke_basis
            )

            # Process custom entries
            if data.custom_entries:
                org_context = self._merge_custom_entry(
                    org_context,
                    data.custom_entries.get("organisatorisch")
                )
                jur_context = self._merge_custom_entry(
                    jur_context,
                    data.custom_entries.get("juridisch")
                )
                wet_basis = self._merge_custom_entry(
                    wet_basis,
                    data.custom_entries.get("wettelijk")
                )

            # Validate against vocabulary
            warnings = []
            org_context = self._validate_vocabulary(
                org_context, self.VALID_ORGANISATIONS, warnings
            )
            jur_context = self._validate_vocabulary(
                jur_context, self.VALID_JURIDICAL, warnings
            )

            # Create validated context
            return ValidatedContext(
                organisatorische_context=org_context,
                juridische_context=jur_context,
                wettelijke_basis=wet_basis,
                validation_metadata={
                    "validated_at": datetime.utcnow().isoformat(),
                    "rules_applied": ["type_check", "vocabulary", "sanitization"],
                    "warnings": warnings
                }
            )

        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            raise ValueError(f"Invalid context data: {str(e)}")

    def _ensure_list_type(self, value: Any) -> List[str]:
        """Convert any input to list of strings"""
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value else []
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        return []

    def _merge_custom_entry(
        self,
        base_list: List[str],
        custom: Optional[str]
    ) -> List[str]:
        """Merge custom entry after sanitization"""
        if not custom:
            return base_list

        # Sanitize custom entry
        sanitized = self._sanitize_input(custom)
        if sanitized and sanitized not in base_list:
            base_list.append(sanitized)

        return base_list

    def _sanitize_input(self, text: str) -> Optional[str]:
        """Sanitize user input to prevent injection"""
        if not text:
            return None

        # Remove dangerous characters
        cleaned = self.INVALID_CHARS_PATTERN.sub("", text)
        cleaned = cleaned.strip()

        # Enforce length limit
        if len(cleaned) > self.MAX_CUSTOM_LENGTH:
            cleaned = cleaned[:self.MAX_CUSTOM_LENGTH]

        return cleaned if cleaned else None

    def _validate_vocabulary(
        self,
        values: List[str],
        valid_set: set,
        warnings: List[str]
    ) -> List[str]:
        """Validate against known vocabulary"""
        validated = []
        for value in values:
            if value in valid_set:
                validated.append(value)
            else:
                # Custom values are allowed but generate warning
                validated.append(value)
                warnings.append(
                    f"Custom value '{value}' not in standard vocabulary"
                )
        return validated
```

### 3. Fixed Context Selector Implementation

```python
# src/ui/components/context_selector_fixed.py
import streamlit as st
from typing import Dict, List, Any, Optional

class ContextSelectorFixed:
    """Fixed context selector without 'Anders...' crashes"""

    def render(self) -> Dict[str, Any]:
        """Main rendering function with fixed multiselect handling"""
        st.markdown("#### Context Selectie")

        col1, col2 = st.columns(2)

        with col1:
            # Organisational context with "Anders..." support
            org_result = self._render_context_field(
                field_name="organisatorische_context",
                label="📋 Organisatorische context",
                options=[
                    "OM", "ZM", "DJI", "KMAR", "NP",
                    "JUSTID", "FIOD", "CJIB", "Reclassering"
                ],
                help_text="Selecteer één of meerdere organisaties"
            )

            # Legal basis
            wet_result = self._render_context_field(
                field_name="wettelijke_basis",
                label="📜 Wettelijke basis",
                options=[
                    "Wetboek van Strafvordering (huidige versie)",
                    "Wetboek van strafvordering (nieuwe versie)",
                    "Wet op de Identificatieplicht",
                    "Wet op de politiegegevens",
                    "Wetboek van Strafrecht",
                    "Algemene verordening gegevensbescherming"
                ],
                help_text="Selecteer relevante wetgeving"
            )

        with col2:
            # Juridical context
            jur_result = self._render_context_field(
                field_name="juridische_context",
                label="⚖️ Juridische context",
                options=[
                    "Strafrecht", "Civiel recht", "Bestuursrecht",
                    "Internationaal recht", "Europees recht", "Migratierecht"
                ],
                help_text="Selecteer juridische gebieden"
            )

        # Combine results
        return {
            "organisatorische_context": org_result["values"],
            "juridische_context": jur_result["values"],
            "wettelijke_basis": wet_result["values"],
            "custom_entries": {
                "organisatorisch": org_result.get("custom"),
                "juridisch": jur_result.get("custom"),
                "wettelijk": wet_result.get("custom")
            }
        }

    def _render_context_field(
        self,
        field_name: str,
        label: str,
        options: List[str],
        help_text: str
    ) -> Dict[str, Any]:
        """Render a single context field with Anders... support"""

        # Add "Anders..." checkbox instead of in options
        use_custom = st.checkbox(
            f"Anders... ({field_name})",
            key=f"use_custom_{field_name}"
        )

        # Regular multiselect without "Anders..." in options
        selected = st.multiselect(
            label=label,
            options=options,  # Clean options list
            default=[],
            help=help_text,
            key=f"select_{field_name}"
        )

        # Custom input field if needed
        custom_value = None
        if use_custom:
            custom_value = st.text_input(
                f"Aangepaste {label.lower()}",
                key=f"custom_{field_name}",
                placeholder="Voer aangepaste waarde in...",
                max_chars=100
            )

        return {
            "values": selected,
            "custom": custom_value if custom_value else None
        }
```

### 4. Fixed Service Adapter Implementation

```python
# src/services/service_factory_fixed.py
from services.interfaces import GenerationRequest
import uuid

class ServiceAdapterFixed:
    """Fixed adapter with proper context mapping"""

    def generate_definition(self, begrip: str, context_dict: dict, **kwargs):
        """Fixed context mapping - no string concatenation"""

        # Create request with proper list types
        request = GenerationRequest(
            id=str(uuid.uuid4()),
            begrip=begrip,
            # Direct list mapping - NO string concatenation
            organisatorische_context=context_dict.get("organisatorisch", []),
            juridische_context=context_dict.get("juridisch", []),
            wettelijke_basis=context_dict.get("wettelijk", []),
            # Optional fields
            organisatie=kwargs.get("organisatie", ""),
            extra_instructies=kwargs.get("extra_instructies", ""),
            ontologische_categorie=kwargs.get("categorie"),
            # Deprecated fields - kept empty for compatibility
            context=None,  # DEPRECATED
            domein=None,   # DEPRECATED
        )

        # Continue with orchestration...
        return self._execute_generation(request)
```

### 5. Audit Service Implementation

```python
# src/services/audit/audit_service.py
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
import asyncpg
from dataclasses import dataclass

@dataclass
class AuditRecord:
    """Immutable audit record"""
    id: str
    request_id: str
    timestamp: datetime
    context_data: Dict[str, List[str]]
    user_id: str
    definition_id: Optional[int]
    checksum: str

class AuditService:
    """ASTRA-compliant audit logging service"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def log_context_usage(
        self,
        request_id: str,
        context_data: ValidatedContext,
        user_id: str,
        definition_id: Optional[int] = None
    ) -> AuditRecord:
        """Log context usage with integrity protection"""

        # Create audit data
        audit_data = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "organisatorische_context": context_data.organisatorische_context,
                "juridische_context": context_data.juridische_context,
                "wettelijke_basis": context_data.wettelijke_basis
            },
            "user_id": user_id,
            "definition_id": definition_id
        }

        # Calculate checksum for integrity
        checksum = self._calculate_checksum(audit_data)

        # Store in database
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO context_audit_trail
                (request_id, timestamp, context_data, user_id,
                 definition_id, checksum)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                request_id,
                audit_data["timestamp"],
                json.dumps(audit_data["context"]),
                user_id,
                definition_id,
                checksum
            )

        return AuditRecord(
            id=str(row["id"]),
            request_id=request_id,
            timestamp=audit_data["timestamp"],
            context_data=audit_data["context"],
            user_id=user_id,
            definition_id=definition_id,
            checksum=checksum
        )

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 checksum for integrity"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
```

### 6. Database Schema

```sql
-- migrations/001_context_audit_trail.sql
CREATE TABLE IF NOT EXISTS context_audit_trail (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    context_data JSONB NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    definition_id BIGINT REFERENCES definitions(id),
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes for performance
    INDEX idx_audit_request_id (request_id),
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_user_id (user_id),
    INDEX idx_audit_definition_id (definition_id)
);

-- Partitioning for 7-year retention
CREATE TABLE context_audit_trail_2025 PARTITION OF context_audit_trail
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Read-only after 30 days (compliance)
CREATE OR REPLACE FUNCTION make_audit_readonly()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.created_at < NOW() - INTERVAL '30 days' THEN
        RAISE EXCEPTION 'Audit records older than 30 days are immutable';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_immutability
BEFORE UPDATE OR DELETE ON context_audit_trail
FOR EACH ROW EXECUTE FUNCTION make_audit_readonly();
```

## Infrastructure Requirements

### Container Architecture

```yaml
# docker-compose.yml
version: '3.9'

services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/definitie
      - REDIS_URL=redis://redis:6379
      - AUDIT_ENABLED=true
      - CONTEXT_VALIDATION_ENABLED=true
    depends_on:
      - db
      - redis
    ports:
      - "8501:8501"  # Streamlit
      - "8000:8000"  # FastAPI
    volumes:
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=definitie
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    deploy:
      resources:
        limits:
          memory: 1G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 512M

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### Monitoring Configuration

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Context metrics
context_validations = Counter(
    'context_validations_total',
    'Total number of context validations',
    ['status', 'type']
)

context_validation_duration = Histogram(
    'context_validation_duration_seconds',
    'Time spent validating context',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

custom_entries_count = Counter(
    'custom_context_entries_total',
    'Number of custom context entries',
    ['type']
)

audit_writes = Counter(
    'audit_writes_total',
    'Total audit log writes',
    ['status']
)

# Usage example
def track_validation(func):
    """Decorator to track validation metrics"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            context_validations.labels(status='success', type='full').inc()
            return result
        except Exception as e:
            context_validations.labels(status='failure', type='full').inc()
            raise
        finally:
            duration = time.time() - start
            context_validation_duration.observe(duration)
    return wrapper
```

## Non-Functional Requirements

### Performance Requirements

| Metric | Requirement | Measurement |
|--------|------------|-------------|
| Context validation latency | < 50ms p95 | Prometheus histogram |
| Audit write latency | < 100ms p95 | Prometheus histogram |
| UI responsiveness | < 200ms | Frontend monitoring |
| Database query time | < 30ms p95 | pg_stat_statements |
| Memory usage | < 2GB per container | Docker stats |
| CPU usage | < 80% sustained | Prometheus node exporter |

### Security Requirements

```python
# src/security/context_security.py
import secrets
from typing import Dict, Any
import jwt
from datetime import datetime, timedelta

class ContextSecurity:
    """Security layer for context operations"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_context_token(
        self,
        context_data: Dict[str, Any],
        user_id: str
    ) -> str:
        """Create signed token for context integrity"""
        payload = {
            "context": context_data,
            "user_id": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "nonce": secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_context_token(self, token: str) -> Dict[str, Any]:
        """Verify context token integrity"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"]
            )
            return payload
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid context token: {e}")
```

### Logging Configuration

```python
# src/config/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging for audit compliance"""

    # Create custom formatter
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        json_ensure_ascii=False
    )
    logHandler.setFormatter(formatter)

    # Configure root logger
    logging.root.handlers = [logHandler]
    logging.root.setLevel(logging.INFO)

    # Specific loggers
    logging.getLogger("context_flow").setLevel(logging.DEBUG)
    logging.getLogger("audit").setLevel(logging.INFO)
    logging.getLogger("security").setLevel(logging.WARNING)

    # Audit logger with separate handler
    audit_logger = logging.getLogger("audit")
    audit_handler = logging.FileHandler("/logs/audit.jsonl")
    audit_handler.setFormatter(formatter)
    audit_logger.addHandler(audit_handler)

    return logging.getLogger(__name__)
```

## Deployment Configuration

### Environment Variables

```bash
# .env.production
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/definitie
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50

# Security
SECRET_KEY=${SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=1

# Context Configuration
CONTEXT_VALIDATION_ENABLED=true
CUSTOM_ENTRY_MAX_LENGTH=100
CUSTOM_ENTRY_RATE_LIMIT=10/hour

# Audit
AUDIT_ENABLED=true
AUDIT_RETENTION_YEARS=7
AUDIT_COMPRESSION_AFTER_DAYS=90

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_ENABLED=true
```

### CI/CD Pipeline

```yaml
# .github/workflows/cfr-deployment.yml
name: CFR Deployment Pipeline

on:
  push:
    branches: [feature/context-flow-refactoring]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run unit tests
        run: |
          pytest tests/unit/context/ -v --cov=src/context

      - name: Run integration tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit

      - name: Security scan
        run: |
          bandit -r src/
          safety check

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/feature/context-flow-refactoring'
    steps:
      - name: Deploy to staging
        run: |
          docker build -t definitie-app:cfr-${{ github.sha }} .
          docker push registry.gov.nl/definitie-app:cfr-${{ github.sha }}
          kubectl set image deployment/definitie-app app=registry.gov.nl/definitie-app:cfr-${{ github.sha }}
```

## Testing Framework

```python
# tests/integration/test_context_flow_e2e.py
import pytest
from httpx import AsyncClient
import asyncio

@pytest.mark.asyncio
async def test_complete_context_flow():
    """E2E test for complete context flow"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Step 1: Submit context
        context_data = {
            "organisatorische_context": ["OM", "DJI"],
            "juridische_context": ["Strafrecht"],
            "wettelijke_basis": ["Wetboek van Strafrecht"],
            "custom_entries": {
                "organisatorisch": "Test Organisatie"
            }
        }

        response = await client.post(
            "/api/context/validate",
            json=context_data
        )
        assert response.status_code == 200
        validated = response.json()

        # Step 2: Generate definition with context
        gen_response = await client.post(
            "/api/definition/generate",
            json={
                "begrip": "voorlopige hechtenis",
                "context": validated["validated_context"]
            }
        )
        assert gen_response.status_code == 200
        definition = gen_response.json()

        # Step 3: Verify audit trail
        audit_response = await client.get(
            f"/api/audit/context/{definition['request_id']}"
        )
        assert audit_response.status_code == 200
        audit = audit_response.json()

        # Verify context was logged
        assert audit["context_used"]["organisatorische_context"] == [
            "OM", "DJI", "Test Organisatie"
        ]

@pytest.mark.asyncio
async def test_anders_option_handling():
    """Test that 'Anders...' option doesn't crash"""
    # Test implementation here
    pass
```

## References

- [Python Best Practices](https://docs.python-guide.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL JSON Support](https://www.postgresql.org/docs/15/datatype-json.html)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Government Cloud Standards](https://www.government.nl/cloud-standards)
