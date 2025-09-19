# Testen Hub

Centrale wegwijzer voor teststrategie, plannen en coverage, zonder bestaande documenten te dupliceren.

## Coverage
- Hoofdrapport: `docs/TEST_COVERAGE_ANALYSIS_UAT.md`

## Teststrategie
- Gids: `docs/testing/TESTING_GUIDE.md` (centrale richtlijn en werkwijze)

## Verdere Referenties
- Solution Architecture (Testen Strategy): `docs/architectuur/SOLUTION_ARCHITECTURE.md`
- SA Template (Testen Strategy): `docs/architectuur/templates/SOLUTION_ARCHITECTURE_TEMPLATE.md`
- Refactoring Plan (Testen Strategy): `docs/architectuur/CATEGORY-REFACTORING-PLAN.md`
- Episch Verhaal 3 Web Lookup (Coverage/Strategy secties): `docs/backlog/stories/epic-3-web-lookup-modernization.md`
- Verbeterplan test suite: `docs/testing/TEST_SUITE_IMPROVEMENT_PLAN.md`

## Testplannen en resultaten
- Validation Orchestrator Testplan: `docs/testing/validation_orchestrator_testplan.md`
- Golden Dataset Validatie: `docs/testing/golden-dataset-validation.md`
- Business Rules Tests: `docs/testing/BUSINESS_RULES.md`
- Legacy Test Mapping: `docs/testing/LEGACY_TEST_MAPPING.md`
- Story 2.3 Implementatie Tests: `docs/testing/story-2.3-test-implementation.md`
- Testresultaten 09-01-2025: `docs/testing/test-results-09-01-2025.md`

## Conventies (kort)
- AAA‑patroon; naamgeving `test_<what>_<condition>_<expected>.py`.
- Fixtures voor setup/teardown; `@pytest.mark.parametrize` voor scenario’s; mock externe afhankelijkheden.
- Valideer tegen BA‑acceptatiecriteria; houd coverage ≥ baseline (zie coverage‑rapport).
- Zie ook QA‑agent richtlijnen: `docs/AGENTS.md` → `quality-assurance-tester`.

## Waar nieuwe docs te plaatsen
- Nieuwe testplannen/rapporten: deze map (`docs/testing/`).
- Coverage‑updates: aanvullen in `docs/TEST_COVERAGE_ANALYSIS_UAT.md` of een datumspecifiek document hier linken.
- Strategie‑updates: voeg secties toe in relevante architectuur/stories en link hierheen.
