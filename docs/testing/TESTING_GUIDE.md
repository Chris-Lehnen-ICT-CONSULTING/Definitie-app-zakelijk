---
canonical: true
status: active
owner: QA Lead
last_verified: 2025-09-19
applies_to: definitie-app@current
---

# Teststrategie en Richtlijnen

Dit document beschrijft de testmethodiek, conventies en praktische instructies voor het testen van de Definitie‑app. Het dient als richtlijn die uitgebreid of aangepast mag worden wanneer nodig.

## Doelen
- Snelle feedback via een duidelijke piramide (unit → services → integratie → regressie → performance).
- Contract‑zekerheid op kerninterfaces (Validation/Definition result).
- Herhaalbaar, voorspelbaar, zonder netwerkafhankelijkheden in CI.

## Testpiramide
- Unit (`tests/unit/`, marker `unit`): Pure functies/klassen, parametrisatie, geen I/O/netwerk.
- Services (`tests/services/`): Service‑laag met mocks; invarianten en configuratie overlays.
- Integratie (`tests/integration/`, marker `integration`): Container/wiring/orchestrators; extern gemockt.
- Contract (`tests/contracts/`, marker `contract`): JSON‑schema’s en interfacecontracten.
- Smoke (`tests/smoke/`): Minimale happy‑paths per capability.
- Regressie (`tests/regression/`, marker `regression`): Bekende scenario’s en bugfix‑bewaking.
- Performance/Benchmark (`tests/performance/`, markers `performance`/`benchmark`): Opt‑in in CI.
- Security/Compliance (`tests/security/`, `tests/compliance/`): Forbidden patterns, policies, domeinregels.

## Configuratie
- Centrale config: `pytest.ini` (repo‑root).
- Speciale suite: `tests/pytest_per007.ini` (alleen gebruiken met `-c`).
- Asynchrone tests: `asyncio_mode = auto` (pytest‑asyncio).

## Conventies
- Bestanden/klassen/functies: `test_*.py`, `Test*`, `test_*`.
- AAA‑patroon, fixtures voor setup/teardown, `@pytest.mark.parametrize` voor scenario’s.
- Mock externen en I/O; gebruik `chdir_tmp_path` om relatieve writes te sandboxen.
- Centrale Streamlit‑mock: `tests/mocks/streamlit_mock.py` (cache decorators & UI no‑ops).

## Markers (beschikbaar)
- `unit`, `integration`, `regression`, `golden`, `performance`, `benchmark`,
  `acceptance`, `red_phase`, `antipattern`, `ontological_category`.

## Uitvoeren
- Snelpad (groen): `pytest -q tests/smoke tests/unit tests/services`
- Integratie/contract: `pytest -q tests/integration tests/contracts`
- Volledig + coverage: `pytest --cov=src --cov-report=term-missing`
- PER‑007 suite: `pytest -c tests/pytest_per007.ini -m "red_phase or antipattern or acceptance"`

## Coverage
- Startbudget: `--cov=src --cov-fail-under=60` (stapsgewijs verhogen).
- Rapporteer ontbrekende regels met `--cov-report=term-missing`.

## Prestaties
- Microbenchmarks opt‑in (pytest‑benchmark). Vermijd harde drempels in de standaard CI, gebruik `benchmark_autosave` voor trendvergelijking.

## Stabiliteit & Isolatie
- Geen netwerk in tests; externe services mocken.
- Gebruik centrale mocks (Streamlit, AI‑clients) i.p.v. ad‑hoc MagicMocks.
- Vermijd tests onder `src/`; alle tests horen onder `tests/`.

## Schrijven van nieuwe tests
1. Kies laag (unit → services → integratie). Begin zo laag mogelijk.
2. Schrijf AAA‑tests met duidelijke namen: `test_<what>_<condition>_<expected>`.
3. Mock alleen rand; test eigen gedrag.
4. Voeg marker(s) toe voor juiste suite.
5. Draai gericht: `pytest tests/<pad> -q` en breid uit naar bredere suites.

## Bekende Patronen
- Contracttests op `ValidationOrchestratorV2` resultaten met JSON‑schema.
- Parametrized validator‑sweeps over `src/toetsregels/validators/*.py`.
- Service factory/wiring integratietests zonder UI/import cycles.

## Governance
- Centrale config staat in `pytest.ini` (root); eerdere varianten in `tests/` of `config/` zijn verwijderd.
- Manual/debug scripts onder `tests/manual/` worden niet verzameld (uitgesloten in `conftest.py`).

## Roadmap (hiaten die we gaan vullen)
- Unit‑tests voor `services/adapters/*`, `services/policies/approval_gate_policy.py` en prompt‑modules.
- Contract‑tests uitbreiden voor Definition/Validation results (degraded/errorcases).
- Parametrized sweep voor alle validatoren in `src/toetsregels/validators/`.

Bijdragen welkom: houd deze gids als bron van waarheid aan en breid uit bij nieuwe domeinen/suites.

