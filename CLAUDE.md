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
make test-cov          # coverage op unit-tests (deterministisch)
make test-cov-ci       # coverage met ratchet-vloer 45% (CI-gate, unit-only)
make test-parallel     # unit tests parallel (-n auto)
make test-smoke        # smoke tests
make test-markers-check  # CI guard: check dat alle files markers hebben

# Lint / dependency-audit
make lint          # ruff + black
make audit         # pip-audit CVE-scan (requirements.txt)
```

### Coverage-baseline (DEF-416, gemeten 2026-06-10)

- **Baseline unit-coverage = 46%** (45,9%; 34.663 statements, 18.754 missed) — vers `.coverage`-artefact, gate slaagt op de 45%-vloer.
- **Gate = unit-only.** De `integration`-suite bevat meerdere real-API/timing-tests die zonder geldige respons **hangen** (verspreid over markers; zie DEF-428/DEF-429). Een gate met `integration` kan daardoor niet betrouwbaar voltooien, dus `test-cov(-ci)` meten **alleen `unit`** (deterministisch).
- **Ratchet-vloer = 45%** (baseline). Verhogen richting 80/85% naarmate coverage groeit (Fase 1). Integration-coverage komt erbij zodra de hangs zijn opgelost.
- **Bewuste afwijking van de globale 80%-regel (DEF-405).** De globale `code-quality`-skill hanteert ≥80% als blocker; dit project draait een **ratchet-vloer van 45%** omdat de echte unit-coverage 46% is — een eerlijke, niet-zakkende ondergrens die per stap omhoog gaat richting 80/85%, i.p.v. een onhaalbare 80%-gate die de pipeline permanent rood zet. Single source of truth = `make test-cov-ci` (`--cov-fail-under=45`, aangeroepen door CI in `test.yml`). `make test-cov` (lokaal) draait bewust **zonder** vloer voor dev-snelheid; alleen de CI-gate handhaaft.
- De cache-unit-tests draaien sinds DEF-427 groen (de eerdere 3 falende `test_cache_utilities_comprehensive.py`-tests zijn opgelost; unit-suite groen in CI).

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

*Versie: 1.0 · 10 maart 2026 · Extendeert: ~/.claude/CLAUDE.md v8.0*
