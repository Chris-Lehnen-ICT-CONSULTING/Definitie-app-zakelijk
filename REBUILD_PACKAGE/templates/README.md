# Templates Directory

**Purpose:** Ready-to-use templates for Week 2+ implementation
**Status:** ✅ Populated with core templates

## Directory Structure

```
templates/
├── docker/              # Docker & infrastructure templates
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── .env.example
├── fastapi/             # FastAPI backend templates
│   ├── main.py
│   ├── api_router.py
│   └── service_template.py
├── testing/             # Test templates
│   ├── pytest.ini
│   ├── conftest.py
│   └── test_template.py
├── validation/          # Validation rule templates
│   └── validation_rule_template.yaml
└── README.md            # This file
```

## Usage by Week

### Week 2: Infrastructure Setup
- Use `docker/docker-compose.yml` for local development
- Copy `docker/.env.example` → `.env` and configure
- Use `docker/Dockerfile.backend` for FastAPI container

### Week 3-4: Core MVP
- Use `fastapi/main.py` as application entry point
- Use `fastapi/service_template.py` for business logic services
- Use `testing/conftest.py` for pytest fixtures

### Week 1: Validation Extraction
- Use `validation/validation_rule_template.yaml` for YAML generation

## Template Philosophy

All templates follow:
- ✅ **Opinionated defaults** (FastAPI best practices, pytest patterns)
- ✅ **Production-ready** (logging, error handling, type hints)
- ✅ **Minimal but complete** (not boilerplate, not bare-bones)
- ✅ **Copy-paste-modify workflow** (clear TODOs, easy customization)

## Quick Start

```bash
# Week 2 Day 1: Setup infrastructure
cp templates/docker/docker-compose.yml .
cp templates/docker/.env.example .env
# Edit .env with your OPENAI_API_KEY

# Week 2 Day 2: Create FastAPI skeleton
mkdir -p app/api app/services app/models
cp templates/fastapi/main.py app/main.py
cp templates/fastapi/api_router.py app/api/router.py

# Week 2 Day 3: Setup testing
cp templates/testing/pytest.ini .
cp templates/testing/conftest.py tests/conftest.py

# Week 1: Extract validation rules
python rebuild/scripts/extract_rule.py src/toetsregels/regels/ARAI-01.py
# Uses templates/validation/validation_rule_template.yaml
```

## Customization

Templates include:
- 🔧 **TODO markers** for required customizations
- 💡 **OPTIONAL markers** for nice-to-have enhancements
- ⚠️ **IMPORTANT markers** for critical configurations

Example:
```python
# TODO: Replace with your database URL
DATABASE_URL = "postgresql://user:pass@localhost/db"

# OPTIONAL: Add Redis caching for 70% cost savings
# CACHE_URL = "redis://localhost:6379"

# IMPORTANT: Keep API key secure, use environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```
