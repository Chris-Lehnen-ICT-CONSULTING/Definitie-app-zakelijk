---
id: CFR-BUG-025
titel: ValidationResult interface mismatch (TypedDict vs dataclass vs varianten) → inconsistent gebruik
status: OPEN
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

## Oplossing
- Standaardiseer op TypedDict‑contract (schema‑first) als SSoT
- Breid/adopteer bestaande mappers:
  - Dataclass → TypedDict en omgekeerd waar nodig
  - Zorg voor consistente velden: `overall_score`, `is_acceptable`, `violations`, `passed_rules`
- Verwijder directe afhankelijkheden op alternatieve vormen in services; gebruik adapters

## Acceptatiecriteria
- Orchestrator en services geven/verwachten alleen TypedDict‑vorm naar buiten
- Alle tests passen zonder type/attribuut mismatch
- Mappingtests toegevoegd voor edge cases (ontbrekende velden, alternate names)

## Relatie
- US-192 (V2 Validator JSON‑regels en contract) — contract leidend
- US-193 (UI toont V2‑validatie) — UI consumeert enkel V2 contract

## Tests
- Unit: round‑trip mappers (dataclass ↔ TypedDict)
- Integratie: orchestrator.validate_definition levert schema‑conform resultaat, UI render OK

