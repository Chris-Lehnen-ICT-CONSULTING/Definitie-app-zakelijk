---
canonical: false
status: active
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# Backend Refactor Checklist (Q1 2025)

Doel: afronden Story 2.4, quick wins, en een kleine FastAPI‑basis, passend bij een kleine gebruikersgroep.

## Week 1 — Story 2.4 (Integration & Migration)
- [ ] DefinitionOrchestratorV2 valideert uitsluitend via ValidationOrchestratorV2 (gerealiseerd; verifiëren in UI‑flow)
- [ ] Verwijder resterende directe validatie‑calls (search & confirm)
- [ ] Golden tests (zie Testblok):
  - [ ] Contract: schema‑conform resultaat (overall_score, is_acceptable, violations)
  - [ ] Mapping: dataclass→schema mapping consistent (errors/suggestions)
  - [ ] Failure path: degraded result met correlation_id

## Week 2 — Quick Wins
- DB
  - [ ] Indexes voor duplicate detection en queries (begrip, organisatorische_context, categorie, status)
- Tests/QA
  - [ ] pytest‑cov baseline (bijv. 20–30%)
  - [ ] Pre‑commit doc‑lint actief (location, links, staleness); `pre-commit run --all-files`
  - [ ] Fix aggregatie afronding (0.81 vs 0.80) in ModularValidationService (indien nog open)
  - [ ] Mini performance sanity: determinisme/score‑stabiliteit (100 runs op hetzelfde input)
- Docs
  - [ ] INDEX canonical mapping check (alles onder `docs/architectuur/`)
  - [ ] last_verified bijwerken voor gewijzigde canonieke docs

## Week 3+ — FastAPI Foundation (read‑only)
- API laag (los van Streamlit)
  - [ ] FastAPI skeleton (health, versie, simpele read‑only endpoint voor definities)
  - [ ] Auth skeleton (eenvoudige API‑key check)
  - [ ] Smoke tests (uvicorn startup, 200 op /health)

## Testblok (Golden/Contract)
1) ValidationOrchestratorV2 contract
   - Input: (begrip, text) combinaties, met/zonder cleaning
   - Verwacht:
     - `version`, `overall_score`, `is_acceptable`, `violations`, `passed_rules`, `detailed_scores`, `system.correlation_id`
     - Violations gesorteerd, correlation_id aanwezig

2) ModularValidationService determinisme & aggregatie
   - Zelfde input → identieke output (scores/violations) over 100 runs
   - Aggregatie afronding consistent (2 decimalen) en >= threshold → is_acceptable True

3) PromptServiceV2 golden prompts (light)
   - Zelfde request/context → stabiele prompt‑componenten (category‑aware component aanwezig)
   - `token_count` ~gelijk (±10%)

## Observability & Config (continu)
- [ ] Loggen in orchestrator V2: duration, generation_id, validatie status
- [ ] Feature flags: geen legacy fallbacks in productie‑pad

