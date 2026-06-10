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

- Python 3.13
- Streamlit 1.51 (frontend)
- FastAPI + Uvicorn (API)
- SQLite 3 (`data/definities.db`)
- Anthropic SDK (AI generatie)
- pytest + pytest-asyncio + pytest-cov

## Structuur

```
src/   (selectie; volledige lijst: `ls -d src/*/`)
├── main.py               ← Streamlit entry point
├── api/                  ← FastAPI routes
├── database/             ← SQLite + migraties (schema.sql)
├── domain/               ← Domein-entiteiten
├── orchestration/        ← DefinitieAgent orchestrator
├── services/             ← Business logica (incl. services/ai/ + services/validation/ — AI-validatie engine, KRITIEK: niet wijzigen zonder overleg)
├── toetsregels/          ← 53 validatieregels (regels/*.json)
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
make test-cov          # coverage unit+integration (GEEN threshold; zie test-cov-ci)
make test-cov-ci       # coverage met --cov-fail-under=85 (CI-gate)
make test-parallel     # unit tests parallel (-n auto)
make test-smoke        # smoke tests
make test-markers-check  # CI guard: check dat alle files markers hebben

# Lint / dependency-audit
make lint          # ruff + black
make audit         # pip-audit CVE-scan (requirements.txt)
```

### Coverage-baseline (DEF-416, gemeten 2026-06-10)

- **Werkelijke unit-coverage = 45%** (34.660 statements, 18.952 missed) — vers `.coverage`-artefact. De 85%-drempel in `test-cov-ci` is **aspiratie**, geen huidige realiteit.
- ⚠️ De volledige `unit or integration`-suite **hangt** op een integration-test → `test-cov`/`test-cov-ci` voltooien momenteel niet. De 85%-gate is dus in CI niet afdwingbaar tot de hang is opgelost (zie DEF-420/DEF-416).
- Drempel-policy (45% ratchet-vloer vs 80/85 doel; badge `minimum_coverage`) = bewuste Fase 1-beslissing, nog open.

## Kritieke Constraints

- Prompt builders NIET wijzigen zonder overleg
- `config/toetsregels/toetsregels_config.yaml` is single source of truth voor validatieregels
- Geen persoonsdata in logs, API keys alleen via `.env`

## Lokale Rules

Project-specifieke rules staan in `.claude/rules/` en laden automatisch.

## Verificatie bij oplevering

- [ ] Tests slagen: `make test`
- [ ] Lint schoon: `make lint`
- [ ] Geen `print()` statements in productie-code

## Workflow

Feature branch: `feature/DEF-XX-beschrijving`

*Versie: 1.0 · 10 maart 2026 · Extendeert: ~/.claude/CLAUDE.md v7.2*
