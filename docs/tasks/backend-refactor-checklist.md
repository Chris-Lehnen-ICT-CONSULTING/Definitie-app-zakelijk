---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# Backend Refactor Checklist (Focused, Small User Base)

Doel: afronden Validatie V2 (Story 2.4), quick wins, en minimale API‑fundering. Geen enterprise‑scope.

## Week 1 — Story 2.4: Integration & Migration (±3 dagen)

- [ ] Integratie: `DefinitionOrchestratorV2` → `ValidationOrchestratorV2`
  - Code: `src/services/orchestrators/definition_orchestrator_v2.py`
- [ ] Migratie: alle validatie‑aanroepen naar V2‑pad
  - Code: `src/ui/` tabs, `src/services/service_factory.py`
- [ ] Verwijder legacy coupling (geen V1 validators/adapters)
  - Code: `src/services/` (controleer imports), container wiring
- [ ] Golden tests/regressie voor validatieflow
  - Tests: `tests/regression/`, `tests/integration/`

## Week 2 — Quick Wins

- [ ] Database indexes (SQLite) op hot‑paths
  - Code: `src/database/` of migratiescript; verifieer met explain/analyse
- [ ] Testing/coverage (pytest‑cov) en markers scheiding
  - Config: `pytest.ini`, test markers (`unit`, `integration`)
- [ ] Pre‑commit uitbreiden voor doc‑lint/linkcheck (lichtgewicht)
  - Scripts: `scripts/hooks/`, CI (optioneel)

## Week 3+ — FastAPI Foundation (parallel, klein)

- [ ] Projectstructuur opzetten (naast Streamlit)
  - Pad: `api/` of `src/api/`
- [ ] Read‑only endpoints (health, status, definities lezen)
  - Statusbron: `reports/status/validation-status.json`
- [ ] OpenAPI doc genereren, auth skeleton (zonder rollout)

## Observability & Config (doorlopend)

- [ ] Structured logging (request_id, latency, tokens)
  - Code: `src/utils/`, centrale logger
- [ ] Kern‑metrics (validatie‑latency, errors)
  - (Optioneel) export voor toekomstige Prometheus integratie
- [ ] Feature flags afdwingen (orchestrator‑first, modern lookup)
  - Config: `src/config/`, `service_factory.py`

## Gereed (niet opnieuw doen)

- [x] Geen runtime `.env`; env/mapping via OS of editor
- [x] Fallback `OPENAI_API_KEY_PROD` als `OPENAI_API_KEY` ontbreekt
- [x] Legacy DefinitionValidator/Interface verwijderd
- [x] Canonical docs + statuspad bijgewerkt
