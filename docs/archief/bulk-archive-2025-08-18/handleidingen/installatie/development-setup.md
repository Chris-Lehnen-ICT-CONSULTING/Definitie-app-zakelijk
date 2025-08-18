# Development Setup Guide

## Prerequisites

Voordat je begint met de DefinitieAgent development setup, zorg ervoor dat je de volgende software geïnstalleerd hebt:

- **Python 3.8 of hoger** (3.11+ aanbevolen)
- **Git** voor version control
- **pip** of **poetry** voor package management
- **SQLite3** (meestal meegeleverd met Python)
- **Een code editor** (VS Code, PyCharm, etc.)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/definitie-app.git
cd definitie-app
```

### 2. Virtual Environment

Maak en activeer een virtual environment:

```bash
# Maak virtual environment
python -m venv venv

# Activeer (Windows)
venv\Scripts\activate

# Activeer (Mac/Linux)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Kopieer het voorbeeld .env bestand:

```bash
cp .env.example .env
```

Bewerk `.env` met je eigen waarden:

```bash
# OpenAI API
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3

# Database
DATABASE_URL=sqlite:///data/database/definities.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/application/app.log

# Cache
CACHE_DIR=cache/
CACHE_TTL=3600

# Development
DEBUG=True
RELOAD=True
```

### 5. Database Setup

Initialiseer de database:

```bash
python src/tools/setup_database.py
```

Of gebruik de migration scripts:

```bash
# Run migrations
python scripts/setup/migration/run_migrations.py
```

### 6. Run Application

Start de Streamlit applicatie:

```bash
streamlit run src/main.py
```

De applicatie is nu beschikbaar op: http://localhost:8501

## Development Tools

### Code Formatting

Het project gebruikt Black voor consistente code formatting:

```bash
# Format alle Python files
black src/ tests/

# Check formatting zonder wijzigingen
black --check src/ tests/
```

### Linting

Gebruik ruff voor snelle linting:

```bash
# Run linter
ruff src/

# Fix automatisch waar mogelijk
ruff --fix src/
```

### Type Checking

Mypy voor type checking:

```bash
mypy src/
```

### Testing

Run de test suite:

```bash
# Alle tests
pytest

# Met coverage
pytest --cov=src --cov-report=html

# Specifieke test file
pytest tests/unit/test_validation_system.py

# Alleen unit tests
pytest tests/unit/

# Met verbose output
pytest -v
```

## Project Structure

```
definitie-app/
├── src/                    # Source code
│   ├── ai_toetsing/       # Validation rules engine
│   ├── services/          # Business logic services
│   ├── ui/                # Streamlit UI components
│   ├── database/          # Database models en repos
│   ├── utils/             # Helper functies
│   └── main.py            # Application entry point
├── tests/                  # Test files
├── docs/                   # Documentation
├── config/                 # Configuration files
├── data/                   # Data storage
└── scripts/               # Utility scripts
```

## Common Development Tasks

### Een nieuwe validator toevoegen

1. Maak JSON config in `src/toetsregels/regels/NEW-01.json`
2. Implementeer validator in `src/toetsregels/validators/NEW_01.py`
3. Voeg tests toe in `tests/unit/test_new_validator.py`
4. Update documentation in `docs/technical/validation-rules.md`

### Een nieuwe UI tab toevoegen

1. Maak component in `src/ui/components/new_tab.py`
2. Registreer in `src/ui/tabbed_interface.py`
3. Voeg session state management toe
4. Test de integratie

### Database wijzigingen

1. Maak migration script in `src/database/migrations/`
2. Update SQLAlchemy models
3. Run migration: `python scripts/setup/migration/run_migrations.py`
4. Update `docs/technical/database-schema.md`

## Debugging

### Streamlit Debugging

Voor debugging in Streamlit:

```python
# In je code
import streamlit as st

# Debug info tonen
st.write("Debug:", variable)

# Of gebruik st.sidebar voor debug panel
with st.sidebar:
    st.write("Session State:", st.session_state)
```

### Python Debugger

```python
import pdb

# Breakpoint toevoegen
pdb.set_trace()
```

Of met Python 3.7+:

```python
# Gewoon dit toevoegen waar je wilt stoppen
breakpoint()
```

### Logging

Check logs in verschillende locaties:

```bash
# Application logs
tail -f logs/application/app.log

# Streamlit logs
tail -f ~/.streamlit/logs/

# Database queries (met SQLAlchemy echo)
# Zet in .env: DATABASE_ECHO=True
```

## Performance Profiling

### CPU Profiling

```bash
# Profile de applicatie
python -m cProfile -o profile.stats src/main.py

# Analyseer results
python -m pstats profile.stats
```

### Memory Profiling

```bash
# Installeer memory profiler
pip install memory-profiler

# Run met memory profiling
mprof run src/main.py
mprof plot
```

## Troubleshooting

### Import Errors

Als je import errors krijgt:

```bash
# Voeg project root toe aan PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Of in Windows
set PYTHONPATH=%PYTHONPATH%;%CD%
```

### Database Locked

SQLite "database is locked" error:

1. Stop alle running instances
2. Verwijder `.db-shm` en `.db-wal` files
3. Restart applicatie

### OpenAI Rate Limits

Bij rate limit errors:

1. Check je API quota op OpenAI dashboard
2. Verhoog `RATE_LIMIT_DELAY` in `.env`
3. Implementeer exponential backoff

### Streamlit Cache Issues

Clear Streamlit cache:

```bash
streamlit cache clear
```

Of verwijder cache folder:

```bash
rm -rf ~/.streamlit/cache/
```

## VS Code Setup

Aanbevolen `.vscode/settings.json`:

```json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        "htmlcov": true
    }
}
```

Aanbevolen extensions:

- Python
- Pylance
- Black Formatter
- GitLens
- Thunder Client (voor API testing)

## Pre-commit Hooks

Installeer pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Dit runt automatisch formatting en linting voor elke commit.

## Deployment Preparation

Voor deployment naar productie:

1. Zet `DEBUG=False` in `.env`
2. Gebruik PostgreSQL i.p.v. SQLite
3. Setup proper secrets management
4. Configure reverse proxy (nginx)
5. Setup monitoring (Sentry, etc.)

Zie `docs/deployment/` voor gedetailleerde deployment instructies.