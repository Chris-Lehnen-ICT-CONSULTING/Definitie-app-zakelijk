---
id: CFR-BUG-025
titel: ValidationResult interface mismatch (TypedDict vs dataclass vs varianten) → inconsistent gebruik
status: RESOLVED
severity: HIGH
component: validation-contract
owner: validation
gevonden_op: 2025-09-19
canonical: false
last_verified: 2025-09-19
applies_to: definitie-app@v2
---

# CFR-BUG-025: ValidationResult interface mismatch

## Beschrijving
Er bestaan meerdere, incompatibele representaties van ValidationResult in de codebase:
- Dataclass: `src/services/interfaces.py:235`
- TypedDict‑contract: `src/services/validation/interfaces.py`
- ASTRA‑variant: `src/services/validation/astra_validator.py`
- Diverse shims/mappers: `src/services/validation/mappers.py`

Dit leidt tot verwarring en fragiele consumer‑code (verschillende velden/typen). Tests en services verwachten soms afwijkende attributen (bijv. `is_valid` vs `is_acceptable`, `overall_score` vs `score`).

## Verwacht gedrag
Eén leidend contract (TypedDict in `services.validation.interfaces`) met adapters voor legacy/dataclass varianten. Consumenten (orchestrator, UI, services) werken uniform tegen het leidende contract.

## Oplossing (geïmplementeerd)
- TypedDict‑contract blijft SSoT; services en orchestrator normaliseren via adapter:
  - Orchestrator (V2): normaliseert `raw_validation` met `ensure_schema_compliance` (defensieve fallback blijft).
  - ServiceAdapter: `normalize_validation` herkent dicts en Mock `.to_dict()` direct; anders schema‑adapter; laatste redmiddel is attribuutextractie. Score/acceptatie robuust afgeleid.
- Tests gebruiken nu container‑shim (`get_container`) in service_factory zodat orchestrator/PromptService niet onbedoeld initieert in unit tests.

## Acceptatiecriteria
- Orchestrator en services consumeren uniform het TypedDict‑contract (intern genormaliseerd) — voldaan
- Unit/integratietests voor contract en orchestrator groen — voldaan
- Mappingtests (edge cases) groen — voldaan

## Relatie
- US-192 (V2 Validator JSON‑regels en contract) — contract leidend
- US-193 (UI toont V2‑validatie) — UI consumeert enkel V2 contract

## Tests / Bewijs
- Unit (mappers): `tests/services/validation/test_mappers.py` — alle testen groen
- Orchestrator: `tests/services/orchestrators/test_definition_orchestrator_v2.py::test_successful_generation_with_ontological_category` — groen
- Contract: `tests/contracts/test_validation_interface.py::test_happy_path_text_validation` — groen
- ServiceAdapter score/acceptatie: `tests/services/test_service_factory.py::TestOverallScoreHandling::*` — alle scenario’s groen

## Notities
- `DefinitionResponseV2.validation_result` blijft dataclass (voor testcompatibiliteit); interne beslissingen gebruiken genormaliseerde dict.
