# 🏗️ REFACTOR PLAN - DEFINITIE-APP
*Door Winston, System Architect*  
*Datum: 2025-08-15*

## Executive Summary

De Definitie-app transformatie van prototype naar enterprise-ready applicatie via moderne microservices architectuur. Dit document bevat het complete 12-weken refactor plan inclusief technische details, migratie strategie en success metrics.

## 🎯 Target Architecture

### High-Level Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Web Frontend                              │
│                   (React/Vue.js + Nginx)                        │
├─────────────────────────────────────────────────────────────────┤
│                      API Gateway Layer                           │
│                    (FastAPI + OAuth2/JWT)                       │
├─────────────────────────────────────────────────────────────────┤
│                        Service Mesh                              │
│                 (Istio/Linkerd + Envoy Proxy)                  │
├────────────┬────────────┬────────────┬─────────────────────────┤
│ Definition │ Validation │   Web      │    AI/ML                │
│  Service   │  Service   │  Lookup    │   Service               │
│ (FastAPI)  │ (FastAPI)  │ (FastAPI)  │  (FastAPI)              │
├────────────┴────────────┴────────────┴─────────────────────────┤
│                    Event Bus Layer                               │
│                  (RabbitMQ/Kafka/NATS)                         │
├─────────────────────────────────────────────────────────────────┤
│                      Data Layer                                  │
│              PostgreSQL (Primary) + Redis (Cache)               │
└─────────────────────────────────────────────────────────────────┘
```

### Service Breakdown

#### 1. **Definition Service**
- **Verantwoordelijkheid**: CRUD operaties voor definities
- **Tech Stack**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL met read replicas
- **Endpoints**:
  - `POST /definitions` - Create nieuwe definitie
  - `GET /definitions/{id}` - Haal definitie op
  - `PUT /definitions/{id}` - Update definitie
  - `DELETE /definitions/{id}` - Verwijder definitie
  - `GET /definitions/search` - Zoek definities

#### 2. **Validation Service**
- **Verantwoordelijkheid**: Toetsregels validatie
- **Tech Stack**: FastAPI, Pydantic, Redis
- **Features**:
  - Async validatie met queue
  - Rule engine voor toetsregels
  - Caching van validatie resultaten
  - Batch validatie support

#### 3. **Web Lookup Service** (Complete Rebuild)
- **Verantwoordelijkheid**: Web bronnen lookup
- **Tech Stack**: FastAPI, httpx, BeautifulSoup4
- **Features**:
  - Async web scraping
  - Rate limiting per domain
  - Result caching
  - Proxy rotation support

#### 4. **AI/ML Service**
- **Verantwoordelijkheid**: GPT-4 integratie en ML features
- **Tech Stack**: FastAPI, OpenAI SDK, Celery
- **Features**:
  - Prompt management
  - Token optimization
  - Cost tracking
  - Model versioning

### Infrastructure Components

#### **API Gateway**
```python
# FastAPI Gateway configuratie
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
import httpx

app = FastAPI(title="DefinitieApp API Gateway")

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.definitie.nl"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implement rate limiting logic
    pass

# Service routing
SERVICE_URLS = {
    "definitions": "http://definition-service:8001",
    "validation": "http://validation-service:8002",
    "web-lookup": "http://web-lookup-service:8003",
    "ai": "http://ai-service:8004",
}
```

#### **Event Bus Architecture**
```python
# Event definitions
from enum import Enum
from pydantic import BaseModel

class EventType(Enum):
    DEFINITION_CREATED = "definition.created"
    DEFINITION_VALIDATED = "definition.validated"
    VALIDATION_FAILED = "validation.failed"
    WEB_LOOKUP_COMPLETED = "web_lookup.completed"

class Event(BaseModel):
    type: EventType
    payload: dict
    timestamp: datetime
    correlation_id: str
```

## 📋 Gefaseerd Implementatie Plan

### FASE 0: Critical Security Fix (Week 1)

#### Dag 1-2: API Key Security
```bash
# 1. Rotate API key
# Login to OpenAI dashboard and generate new key

# 2. Remove from repository
git rm .env
echo ".env" >> .gitignore
git commit -m "fix: remove exposed API key from repository"

# 3. Setup local environment
cp .env.example .env
# Add new API key locally
```

#### Dag 3-4: Secrets Management
```python
# HashiCorp Vault integration
from hvac import Client

class SecretsManager:
    def __init__(self):
        self.client = Client(
            url=os.getenv("VAULT_URL"),
            token=os.getenv("VAULT_TOKEN")
        )
    
    def get_secret(self, path: str) -> str:
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path
        )
        return response["data"]["data"]["value"]

# Usage
secrets = SecretsManager()
openai_key = secrets.get_secret("openai/api_key")
```

#### Dag 5: Basic Authentication
```python
# JWT implementation
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except JWTError:
        raise HTTPException(status_code=401)
```

### FASE 1: Containerization & Infrastructure (Week 2-3)

#### Docker Setup
```dockerfile
# Multi-stage Dockerfile
FROM python:3.11-slim as base

# Security: non-root user
RUN useradd -m -r appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Build stage
FROM base as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM base
WORKDIR /app
COPY --from=builder /home/appuser/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose voor Development
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: definitie_app
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  definition-service:
    build:
      context: ./services/definition-service
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres/definitie_app
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    ports:
      - "8001:8000"

  # Other services...

volumes:
  postgres_data:
  redis_data:
```

#### Database Migration
```python
# Alembic setup for PostgreSQL migration
# alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql://user:pass@localhost/definitie_app

# migrations/env.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from alembic import context

Base = declarative_base()

def run_migrations_online():
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

### FASE 2: Service Decomposition (Week 4-6)

#### Service Extraction Pattern
```python
# Van monoliet naar microservice

# OLD: UnifiedDefinitionService (monoliet)
class UnifiedDefinitionService:
    def create_definition(self, data):
        # 698 regels mixed concerns
        pass

# NEW: Separate services
# services/definition-service/app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI(title="Definition Service")

@app.post("/definitions")
async def create_definition(
    definition: DefinitionCreate,
    db: Session = Depends(get_db)
):
    repo = DefinitionRepository(db)
    return repo.create(definition)

# services/validation-service/app/main.py
from fastapi import FastAPI
import httpx

app = FastAPI(title="Validation Service")

@app.post("/validate")
async def validate_definition(definition: Definition):
    validator = ToetsregelValidator()
    result = await validator.validate(definition)
    
    # Publish event
    await publish_event(
        EventType.DEFINITION_VALIDATED,
        {"definition_id": definition.id, "result": result}
    )
    
    return result
```

#### API Gateway Implementation
```python
# gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from httpx import AsyncClient
import asyncio

app = FastAPI(title="DefinitieApp API Gateway")

# Service registry
services = {
    "definitions": "http://definition-service:8000",
    "validation": "http://validation-service:8000",
    "web-lookup": "http://web-lookup-service:8000",
    "ai": "http://ai-service:8000"
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in services:
        raise HTTPException(404, "Service not found")
    
    async with AsyncClient() as client:
        url = f"{services[service]}/{path}"
        
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers,
            params=request.query_params,
            content=await request.body()
        )
        
        return response.json()
```

### FASE 3: Performance Optimization (Week 7-8)

#### Redis Caching Layer
```python
# cache/redis_cache.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class RedisCache:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ):
        self.client.set(
            key,
            json.dumps(value),
            ex=ttl.total_seconds() if ttl else None
        )
    
    async def invalidate_pattern(self, pattern: str):
        for key in self.client.scan_iter(match=pattern):
            self.client.delete(key)
```

#### Database Optimization
```python
# Fix N+1 queries with eager loading
from sqlalchemy.orm import joinedload

# OLD: N+1 problem
definitions = session.query(Definition).all()
for definition in definitions:
    print(definition.examples)  # N additional queries

# NEW: Eager loading
definitions = session.query(Definition)\
    .options(joinedload(Definition.examples))\
    .all()

# Add database indexes
class Definition(Base):
    __tablename__ = "definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    begrip = Column(String, index=True)  # Index for search
    created_at = Column(DateTime, index=True)  # Index for sorting
    
    __table_args__ = (
        Index('idx_begrip_created', 'begrip', 'created_at'),
    )
```

### FASE 4: Frontend Modernization (Week 9-10)

#### React Component Architecture
```jsx
// frontend/src/components/DefinitionForm.jsx
import React, { useState } from 'react';
import { useDefinitions } from '../hooks/useDefinitions';

export const DefinitionForm = () => {
    const [formData, setFormData] = useState({
        begrip: '',
        context: '',
        domein: ''
    });
    
    const { createDefinition, isLoading } = useDefinitions();
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        const result = await createDefinition(formData);
        if (result.success) {
            // Handle success
        }
    };
    
    return (
        <form onSubmit={handleSubmit}>
            {/* Form fields */}
        </form>
    );
};
```

#### API Integration Layer
```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL;

class ApiClient {
    private client = axios.create({
        baseURL: API_BASE_URL,
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    constructor() {
        this.setupInterceptors();
    }
    
    private setupInterceptors() {
        // Request interceptor for auth
        this.client.interceptors.request.use(
            config => {
                const token = localStorage.getItem('token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            }
        );
        
        // Response interceptor for errors
        this.client.interceptors.response.use(
            response => response,
            error => {
                if (error.response?.status === 401) {
                    // Handle auth error
                }
                return Promise.reject(error);
            }
        );
    }
    
    async createDefinition(data: DefinitionCreate) {
        const response = await this.client.post('/definitions', data);
        return response.data;
    }
}

export const apiClient = new ApiClient();
```

### FASE 5: Monitoring & Production (Week 11-12)

#### Observability Stack
```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"

  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

#### Application Metrics
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# Middleware for metrics collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

## 🔄 Migration Strategy

### Strangler Fig Pattern Implementation

```python
# Feature flag based migration
from feature_flags import FeatureFlag

class DefinitionService:
    def __init__(self):
        self.legacy_service = UnifiedDefinitionService()
        self.new_service = NewDefinitionService()
        self.feature_flag = FeatureFlag("use_new_definition_service")
    
    async def create_definition(self, data):
        if self.feature_flag.is_enabled():
            # New microservice
            return await self.new_service.create(data)
        else:
            # Legacy monolith
            return self.legacy_service.create_definition(data)
```

### Database Migration Strategy

```sql
-- Step 1: Create new schema alongside old
CREATE SCHEMA new_app;

-- Step 2: Dual writes
-- Application writes to both old and new schema

-- Step 3: Migrate historical data
INSERT INTO new_app.definitions 
SELECT * FROM public.definitions;

-- Step 4: Switch reads to new schema
-- Update application configuration

-- Step 5: Stop dual writes
-- Remove old schema references
```

## 📊 Success Metrics & KPIs

### Technical Metrics
- **Response Time**: P95 < 200ms (current: ~2s)
- **Availability**: 99.9% uptime (current: ~95%)
- **Error Rate**: < 0.1% (current: ~2%)
- **Concurrent Users**: 10,000+ (current: ~100)
- **Test Coverage**: > 80% (current: 26%)

### Business Metrics
- **User Satisfaction**: NPS > 50
- **Feature Velocity**: 2x current speed
- **Maintenance Cost**: -70% reduction
- **Incident Response**: < 15 minutes MTTR

### Security Metrics
- **Vulnerabilities**: 0 critical, < 5 medium
- **Authentication Coverage**: 100%
- **Data Encryption**: 100% at rest and in transit
- **Compliance**: GDPR, ISO 27001 ready

## 💰 Cost Analysis

### Development Investment
- **Team**: 3 developers x 12 weeks
- **Infrastructure**: ~€500/month (AWS/Azure)
- **Tools & Licenses**: ~€200/month
- **Total**: ~€150,000

### Expected ROI
- **Performance**: 5x improvement = €50k/year saved
- **Maintenance**: 70% reduction = €100k/year saved
- **New Features**: 2x velocity = €200k value/year
- **Security**: Risk mitigation = €500k potential saved
- **Break-even**: 4-6 months

## 🚀 Quick Wins (Week 1 Implementable)

1. **Move API key to environment** (1 hour)
```bash
export OPENAI_API_KEY="sk-..."
```

2. **Add connection pooling** (2 hours)
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)
```

3. **Enable disabled tests** (4 hours)
```bash
# Rename .disabled files back
find tests -name "*.disabled" -exec bash -c 'mv "$0" "${0%.disabled}"' {} \;
```

4. **Add structured logging** (3 hours)
```python
import structlog
logger = structlog.get_logger()
```

5. **Basic Docker setup** (4 hours)
```bash
docker build -t definitie-app .
docker run -p 8000:8000 definitie-app
```

## 🎓 Team Training Plan

### Week 1-2: Foundation
- Microservices architecture principles
- Docker & Kubernetes basics
- FastAPI framework
- Security best practices

### Week 3-4: Advanced Topics
- Event-driven architecture
- Service mesh concepts
- Monitoring & observability
- Performance optimization

### Ongoing
- Weekly architecture reviews
- Pair programming sessions
- Knowledge sharing presentations
- External training budget: €5000

## 📚 Documentation Updates Required

1. **API Documentation** (OpenAPI/Swagger)
2. **Deployment Guide** (Docker, K8s, CI/CD)
3. **Security Documentation** (Auth, encryption, compliance)
4. **Monitoring Playbook** (Alerts, dashboards, runbooks)
5. **Architecture Decision Records** (ADRs)
6. **Development Guidelines** (Code style, git flow, review process)

## ✅ Definition of Done

Een fase is compleet wanneer:
1. Alle code heeft >80% test coverage
2. Security scan toont geen critical issues
3. Performance benchmarks zijn gehaald
4. Documentatie is bijgewerkt
5. Code review door 2 developers
6. Deployment naar staging succesvol
7. Monitoring en alerting geconfigureerd

## 🔮 Future Considerations

### Year 2 Roadmap
- Multi-tenant architecture
- GraphQL API layer
- Machine learning pipeline
- Global CDN deployment
- Mobile native apps

### Technical Debt Prevention
- Quarterly architecture reviews
- Automated dependency updates
- Regular security audits
- Performance regression tests
- Code quality gates in CI/CD

---

## 🔧 Gedetailleerde Implementatie Specificaties

### Security Architecture

#### OAuth2/JWT Implementatie
```python
# auth_middleware.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

class AuthHandler:
    security = HTTPBearer()
    secret = settings.JWT_SECRET
    algorithm = "HS256"
    
    def encode_token(self, user_id: str, roles: List[str]) -> str:
        payload = {
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow(),
            "sub": user_id,
            "roles": roles,
            "permissions": self.get_permissions_for_roles(roles)
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

#### Rate Limiting & DDoS Protection
```python
# rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri="redis://redis:6379"
)

# Advanced rate limiting per user tier
def get_user_rate_limit(request: Request) -> str:
    user = get_current_user(request)
    if user.tier == "enterprise":
        return "10000 per hour"
    elif user.tier == "pro":
        return "5000 per hour"
    return "1000 per hour"
```

### Database Architecture

#### Multi-Tenant Schema Design
```sql
-- Shared schema approach with row-level security
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE definitions ENABLE ROW LEVEL SECURITY;

CREATE POLICY definitions_isolation ON definitions
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);
```

#### Database Connection Pooling
```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo_pool=settings.DEBUG
)
```

### Caching Strategy

#### Redis Implementation
```python
# cache_service.py
import redis
import pickle
from typing import Optional, Any
from functools import wraps

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=False,
            connection_pool_kwargs={
                'max_connections': 50,
                'socket_keepalive': True
            }
        )
    
    def cache_key(self, prefix: str, *args) -> str:
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def cache_result(self, prefix: str, ttl: int = 3600):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self.cache_key(prefix, *args, *kwargs.values())
                
                # Try to get from cache
                cached = self.redis_client.get(cache_key)
                if cached:
                    return pickle.loads(cached)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    pickle.dumps(result)
                )
                
                return result
            return wrapper
        return decorator
```

### Event-Driven Architecture

#### Event Bus Implementation
```python
# event_bus.py
from typing import Dict, List, Callable
import asyncio
import aio_pika
import json

class EventBus:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        
    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}/"
        )
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            'definitie_events',
            aio_pika.ExchangeType.TOPIC
        )
    
    async def publish(self, event_type: str, data: dict):
        message = aio_pika.Message(
            body=json.dumps({
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }).encode(),
            content_type='application/json'
        )
        
        await self.exchange.publish(
            message,
            routing_key=event_type
        )
```

### Monitoring & Observability

#### OpenTelemetry Setup
```python
# telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter(
    'definitie_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'definitie_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Tracing
tracer = trace.get_tracer(__name__)

def setup_telemetry(app: FastAPI):
    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Auto-instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        service="definitie-service"
    )
    
    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(
            generate_latest(),
            media_type="text/plain"
        )
```

### Testing Strategy

#### Integration Test Framework
```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
async def test_containers():
    postgres = PostgresContainer("postgres:14")
    redis = RedisContainer("redis:7")
    
    with postgres, redis:
        yield {
            "postgres_url": postgres.get_connection_url(),
            "redis_url": f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}"
        }

@pytest.mark.asyncio
async def test_definition_lifecycle(test_containers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create definition
        response = await client.post(
            "/api/v1/definitions",
            json={
                "title": "Test Definition",
                "content": "Test content",
                "category": "test"
            },
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 201
        definition_id = response.json()["id"]
        
        # Verify caching
        response2 = await client.get(
            f"/api/v1/definitions/{definition_id}",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response2.headers.get("X-Cache-Hit") == "true"
```

### Deployment Configuration

#### Kubernetes Manifests
```yaml
# k8s/definition-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: definition-service
  namespace: definitie-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: definition-service
  template:
    metadata:
      labels:
        app: definition-service
    spec:
      containers:
      - name: definition-service
        image: definitie-app/definition-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: definition-service
  namespace: definitie-app
spec:
  selector:
    app: definition-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run tests
      run: |
        poetry run pytest --cov=src --cov-report=xml
    
    - name: SonarQube Scan
      uses: sonarsource/sonarqube-scan-action@master
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker images
      env:
        DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
      run: |
        docker build -t $DOCKER_REGISTRY/definition-service:$GITHUB_SHA ./services/definition
        docker push $DOCKER_REGISTRY/definition-service:$GITHUB_SHA
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > /tmp/kubeconfig
        export KUBECONFIG=/tmp/kubeconfig
        kubectl set image deployment/definition-service definition-service=$DOCKER_REGISTRY/definition-service:$GITHUB_SHA -n definitie-app
        kubectl rollout status deployment/definition-service -n definitie-app
```

### Performance Optimization

#### Query Optimization
```python
# repositories/definition_repository.py
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, func

class DefinitionRepository:
    async def get_definitions_with_stats(
        self, 
        org_id: UUID, 
        limit: int = 50,
        offset: int = 0
    ) -> List[DefinitionWithStats]:
        # Optimized query with subquery for stats
        stats_subquery = (
            select(
                ValidationLog.definition_id,
                func.count(ValidationLog.id).label('validation_count'),
                func.avg(ValidationLog.duration_ms).label('avg_duration')
            )
            .group_by(ValidationLog.definition_id)
            .subquery()
        )
        
        query = (
            select(Definition, stats_subquery.c.validation_count, stats_subquery.c.avg_duration)
            .outerjoin(stats_subquery, Definition.id == stats_subquery.c.definition_id)
            .where(Definition.org_id == org_id)
            .options(selectinload(Definition.tags))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(query)
        return result.all()
```

### API Versioning Strategy

#### Versioned Routes
```python
# api/v1/routes.py
from fastapi import APIRouter, Header
from typing import Optional

router = APIRouter(prefix="/api/v1")

# Header-based versioning support
@router.get("/definitions")
async def get_definitions(
    accept_version: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0
):
    # Handle version-specific logic
    if accept_version == "2.0":
        return await get_definitions_v2(limit, offset)
    return await get_definitions_v1(limit, offset)
```

### Error Handling & Recovery

#### Global Error Handler
```python
# middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return JSONResponse(
                status_code=422,
                content={
                    "error": "validation_error",
                    "message": "Invalid input data",
                    "details": e.errors()
                }
            )
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "database_error",
                    "message": "Service temporarily unavailable",
                    "retry_after": 30
                }
            )
        except Exception as e:
            logger.exception("Unhandled exception")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                    "trace_id": request.state.trace_id
                }
            )
```

### Data Migration Strategy

#### Zero-Downtime Migration
```python
# migrations/migrate_to_microservices.py
import asyncio
from datetime import datetime
from typing import List, Dict

class MicroservicesMigrator:
    def __init__(self):
        self.old_db = get_legacy_db_connection()
        self.new_dbs = {
            'definitions': get_definitions_db(),
            'validations': get_validations_db(),
            'users': get_users_db()
        }
        
    async def migrate_with_verification(self):
        # Phase 1: Dual-write mode
        await self.enable_dual_write_mode()
        
        # Phase 2: Backfill historical data
        await self.backfill_data()
        
        # Phase 3: Verify data consistency
        discrepancies = await self.verify_data_consistency()
        if discrepancies:
            await self.reconcile_discrepancies(discrepancies)
        
        # Phase 4: Switch read traffic
        await self.switch_read_traffic()
        
        # Phase 5: Stop writes to old system
        await self.disable_legacy_writes()
    
    async def backfill_data(self):
        batch_size = 1000
        offset = 0
        
        while True:
            # Get batch from legacy system
            legacy_data = await self.old_db.fetch(
                "SELECT * FROM definitions LIMIT %s OFFSET %s",
                batch_size, offset
            )
            
            if not legacy_data:
                break
            
            # Transform and insert into new system
            transformed_data = self.transform_legacy_data(legacy_data)
            await self.new_dbs['definitions'].insert_many(transformed_data)
            
            offset += batch_size
            
            # Progress tracking
            logger.info(f"Migrated {offset} records")
```

### Feature Flag System

#### Dynamic Feature Control
```python
# feature_flags.py
from typing import Dict, Any
import aioredis

class FeatureFlags:
    def __init__(self):
        self.redis = aioredis.create_redis_pool('redis://localhost')
        self.default_flags = {
            'new_validation_engine': False,
            'ai_suggestions': True,
            'rate_limiting_v2': False,
            'graphql_api': False
        }
    
    async def is_enabled(
        self, 
        feature: str, 
        user_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> bool:
        # Check user-specific override
        if user_id:
            user_flag = await self.redis.get(f"ff:user:{user_id}:{feature}")
            if user_flag is not None:
                return user_flag == "1"
        
        # Check org-specific override
        if org_id:
            org_flag = await self.redis.get(f"ff:org:{org_id}:{feature}")
            if org_flag is not None:
                return org_flag == "1"
        
        # Check global flag
        global_flag = await self.redis.get(f"ff:global:{feature}")
        if global_flag is not None:
            return global_flag == "1"
        
        # Return default
        return self.default_flags.get(feature, False)
```

### Load Testing & Performance Benchmarks

#### Locust Test Configuration
```python
# load_tests/test_api_performance.py
from locust import HttpUser, task, between
import random

class DefinitieAPIUser(HttpUser):
    wait_time = between(0.5, 2)
    
    def on_start(self):
        # Authenticate once
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_definitions(self):
        self.client.get(
            "/api/v1/definitions",
            headers=self.headers,
            params={"limit": 50}
        )
    
    @task(2)
    def search_definitions(self):
        search_terms = ["wet", "artikel", "besluit", "regeling"]
        self.client.get(
            "/api/v1/definitions/search",
            headers=self.headers,
            params={"q": random.choice(search_terms)}
        )
    
    @task(1)
    def create_definition(self):
        self.client.post(
            "/api/v1/definitions",
            headers=self.headers,
            json={
                "title": f"Test Definition {random.randint(1, 10000)}",
                "content": "Test content for load testing",
                "category": "test"
            }
        )
```

### Documentation Generation

#### OpenAPI Schema Extensions
```python
# api/documentation.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Definitie App API",
        version="1.0.0",
        description="""
        ## Overview
        The Definitie App API provides programmatic access to legal definitions and validation services.
        
        ## Authentication
        All API requests require authentication using Bearer tokens.
        
        ## Rate Limiting
        - Free tier: 1000 requests/hour
        - Pro tier: 5000 requests/hour
        - Enterprise: Custom limits
        
        ## Webhooks
        Subscribe to events for real-time updates.
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add webhook definitions
    openapi_schema["webhooks"] = {
        "definitionCreated": {
            "post": {
                "requestBody": {
                    "description": "Definition creation event",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/DefinitionEvent"}
                        }
                    }
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

### Cost Optimization

#### Resource Scaling Strategy
```yaml
# k8s/horizontal-pod-autoscaler.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: definition-service-hpa
  namespace: definitie-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: definition-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

### Development Environment

#### Docker Compose for Local Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: definitie
      POSTGRES_PASSWORD: localdev
      POSTGRES_DB: definitie_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
  
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin
    ports:
      - "5672:5672"
      - "15672:15672"
  
  definition-service:
    build:
      context: ./services/definition
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/definition:/app
    environment:
      DATABASE_URL: postgresql://definitie:localdev@postgres/definitie_db
      REDIS_URL: redis://redis:6379
      RABBITMQ_URL: amqp://admin:admin@rabbitmq:5672/
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - redis
      - rabbitmq
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
  redis_data:
```

---

*Dit refactor plan transformeert de Definitie-app van een prototype naar een production-ready, schaalbare enterprise applicatie geschikt voor commerciële deployment.*
