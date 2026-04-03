# CLAUDE.md - DefinitieAgent

> **Extensie** op `~/.claude/CLAUDE.md` (globaal)

## Project Info

| Item | Waarde |
|------|--------|
| **Project key** | `DEF` |
| **Repository** | `github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakisch` |
| **Type** | Web app (Streamlit + FastAPI) |
| **Taal** | Nederlands (UI + juridisch domein), Engels (code) |

## Tech Stack

- Python 3.11
- Streamlit 1.51 (frontend)
- FastAPI + Uvicorn (API)
- SQLite 3 (`data/definities.db`)
- Anthropic SDK (AI generatie)
- pytest + pytest-asyncio + pytest-cov

## Structuur

```
src/
├── main.py               ← Streamlit entry point
├── ai_toetser/           ← Validatie engine (KRITIEK - niet wijzigen zonder overleg)
├── api/                  ← FastAPI routes
├── database/             ← SQLite + migraties (schema.sql)
├── domain/               ← Domein-entiteiten
├── orchestration/        ← DefinitieAgent orchestrator
├── services/             ← Business logica
├── toetsregels/          ← 45 validatieregels
├── ui/                   ← Streamlit componenten + SessionStateManager
└── validation/           ← ModularValidationService
tests/
```

## Build / Run / Test

```bash
# Run
make dev

# Test (marker-gebaseerd, alle test files hebben pytestmark)
make test              # unit tests (-m unit), fail-fast
make test-integration  # integration tests (-m integration)
make test-all          # volledige suite (alle markers)
make test-cov          # coverage op unit + integration (threshold 85%)
make test-parallel     # unit tests parallel (-n auto)
make test-smoke        # smoke tests
make test-markers-check  # CI guard: check dat alle files markers hebben

# Lint
make lint          # ruff + black
```

## Kritieke Constraints

- ai_toetser/ en prompt builders NIET wijzigen zonder overleg
- `config/toetsregels.json` is single source of truth voor validatieregels
- Geen persoonsdata in logs, API keys alleen via `.env`

## Lokale Rules

Project-specifieke rules staan in `.claude/rules/` en laden automatisch.

## Verificatie bij oplevering

- [ ] Tests slagen: `make test`
- [ ] Lint schoon: `make lint`
- [ ] Geen `print()` statements in productie-code

## Workflow

Feature branch: `feature/DEF-XX-beschrijving`

*Versie: 1.0 · 10 maart 2026 · Extendeert: ~/.claude/CLAUDE.md v7.1*
