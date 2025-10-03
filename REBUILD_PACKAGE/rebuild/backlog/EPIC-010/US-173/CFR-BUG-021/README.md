---
id: CFR-BUG-021
titel: CI gate false positives (deprecated attributes scope)
status: open
owner: development-team
applies_to: definitie-app@current
last_verified: 2025-10-02
severity: LOW
gevonden_op: 2025-09-15
component: ci
---

# CFR-BUG-021: CI gate false positives (deprecated attributes scope)

## Beschrijving
EPIC-010 gate matched `.overall_score`/`best_iteration` in toegestane contexten (UI metrics, legacy demo), veroorzaakt valse failures.

## Verwacht Gedrag
Gate faalt alleen op echte regressies in services/hoofdflow; UI demo/prints/legacy uitgesloten via allowlist.

## Oplossing
Onderdeel van [US-173](../US-173.md): scope/allowlist aanpassen in `.github/workflows/epic-010-gates.yml`.

## Tests
- Trigger met voorbeeld-bestand in allowlisted pad → geen failure.
- Overtreding in services → failure.

