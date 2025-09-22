---
id: CFR-BUG-031
titel: Legacy cleanup – container API, validator interface en service_factory marker (tests failing)
status: OPEN
severity: HIGH
component: core-infra
owner: architecture
gevonden_op: 2025-09-22
canonical: false
applies_to: definitie-app@current
---

# CFR-BUG-031: Legacy cleanup — container API, validator interface en service_factory marker

## Symptomen (tests die falen)
- tests/test_legacy_validation_removed_simple.py::test_service_factory_get_stats_no_validator → AttributeError: `ServiceContainer.get_instance()` ontbreekt.
- tests/test_legacy_validation_removed_simple.py::test_no_validator_in_service_factory_source → verwacht tekst “Legacy validator removed” in `services/service_factory.py` (marker ontbreekt).
- tests/test_legacy_validation_removed_simple.py::test_orchestrator_handles_validation → idem `get_instance()` ontbreekt.
- tests/test_legacy_validation_removed_simple.py::test_no_validator_interface_in_interfaces → `DefinitionValidatorInterface` bestaat nog in `services/interfaces.py` (zou verwijderd moeten zijn).

## Root causes
1) Container API is niet volledig gelijkgetrokken met tests: `ServiceContainer.get_instance()` ontbreekt (we hebben `get_container()` module‑functie).
2) Legacy validator interface blijft aanwezig: `DefinitionValidatorInterface` staat nog in `src/services/interfaces.py:308` ondanks migratie naar V2.
3) Service factory mist expliciete marker/tekst “Legacy validator removed” (tests controleren hierop als regressie‑guard).
4) Consistentie: enkele niet‑UI paden gebruiken nog `repository.change_status(...)` direct (bijv. `src/integration/definitie_checker.py:373`). Voor ESTABLISHED zou dit via `DefinitionWorkflowService` moeten lopen (gate‑enforcement).

## Geimpacteerde bestanden
- src/services/container.py — voeg `@classmethod get_instance()` toe (delegate naar globale container), geen gedrag wijzigen verder.
- src/services/interfaces.py — verwijder class `DefinitionValidatorInterface` (of zet onder guarded legacy stub die tests passeert door afwezigheid van class).
- src/services/service_factory.py — voeg duidelijke marker (docstring/comment) “Legacy validator removed” toe; verifieer dat geen `container.validator()` referenties bestaan.
- src/integration/definitie_checker.py — vervang directe `repository.change_status(...)` door `DefinitionWorkflowService` voor status “established” (consistentie met gate‑beleid).

## Acceptatiecriteria
- [ ] Tests `test_legacy_validation_removed_simple.py` en `test_legacy_validation_removed.py` slagen zonder aanpassing van tests.
- [ ] `ServiceContainer.get_instance()` retourneert dezelfde singleton als `get_container()` (zonder dubbele initialisatie).
- [ ] `services/interfaces.py` bevat geen `class DefinitionValidatorInterface`.
- [ ] `services/service_factory.py` bevat een duidelijke marker “Legacy validator removed” en geen legacy validator calls.
- [ ] (Optioneel) Integratiepad naar ESTABLISHED gebruikt `DefinitionWorkflowService` i.p.v. directe repo‑calls.

## Aanpak (kleine PR)
1) Container: implementeer `@classmethod get_instance(cls) -> ServiceContainer:` dat `return get_container()` doet.
2) Interfaces: verwijder de classdefinitie van `DefinitionValidatorInterface` en update docstring bovenin met verwijzing naar V2 contract (`services/validation/interfaces.py`).
3) Service factory: voeg korte docstringregel “Legacy validator removed (US‑043)” en check dat er geen `container.validator()` in de code staat.
4) Integratie: in `src/integration/definitie_checker.py` gebruik `DefinitionWorkflowService.submit_for_review(...)` voor ESTABLISHED (gate‑enforcement), en `workflow.update_status(...)` voor niet‑gate statussen.

## Gerelateerde US/EPIC
- EPIC‑010 / US‑043 — Remove Legacy Context Routes (breder legacy‑opruimwerk, tests refereren hiernaar)
- EPIC‑012 — Legacy Orchestrator Refactoring (achtergrond refactor)

## Testen
- Draai minimaal:
  - `pytest -q tests/test_legacy_validation_removed_simple.py`
  - `pytest -q tests/test_legacy_validation_removed.py`
  - rook: `tests/services/test_container_wiring_v2_cutover.py`

## Opmerkingen
- In `docs/migration/remove-legacy-validation-plan.md` staat dat de interface verwijderd is; deze bug brengt code in lijn met documentatie en tests.

