# Code Patterns — DefinitieAgent

> Niet-Streamlit patronen. Lees VOOR je bouwt; update bij oplevering.
> Streamlit/UI: zie `streamlit-patterns.md`.

## Services & DI

| Patroon | Conventie |
|---------|-----------|
| Container | Singleton `ServiceContainer` — lazy-loaded properties per service |
| Naamgeving | `{Feature}Service` of `{Feature}OrchestratorV2` voor multi-step |
| Async | Async-first voor alle I/O (AI calls, DB, web) |
| Config | `config.yaml` (bron van waarheid) + optionele env overlay |
| Errors | `DefinitionServiceError` hiërarchie met domein-context (begrip, veld) |

## Data Models

| Patroon | Conventie |
|---------|-----------|
| Data transfer | `@dataclass`: `DefinitieRecord`, `Definition` |
| Validatie | `Pydantic BaseModel` alleen voor runtime input-validatie |
| None-handling | `__post_init__` converteert `None` → lege list/dict |
| Context | Altijd 3 lijsten: `organisatorische_context`, `juridische_context`, `wettelijke_basis` |

## Database

| Patroon | Conventie |
|---------|-----------|
| Driver | Raw `sqlite3` — geen ORM |
| Repository | `DefinitieRepository` (low-level) + `DefinitionRepositoryInterface` (service) |
| Migraties | `database/migrations/v{N}_migration.py` — versioned SQL modules |
| JSON velden | `validation_issues`, `wettelijke_basis` als TEXT JSON; helpers voor serialisatie |

## LLM Integratie

| Patroon | Conventie |
|---------|-----------|
| Abstractie | `AsyncAIClient` Protocol — provider-agnostisch (OpenAI + Anthropic) |
| Calls | Altijd via `AIServiceV2.generate_definition()` — nooit direct |
| Model selectie | Via `ModelRouter.get_model()` — geen hardcoded model namen |
| Rate limiting | Time-windowed + async semaphore (`AsyncRateLimiter`) |
| Retries | Exponential backoff (factor 1.5, max 3) |
| API keys | Altijd sanitizen via `sanitize_error()` in error messages |

## Anti-patronen

- `print()` in productie-code — gebruik logger
- Hardcoded model namen — gebruik `ModelRouter`
- Validatieregels in code — `config/toetsregels.json` is de bron
- Sync+async mixen — commit to async voor V2 services
