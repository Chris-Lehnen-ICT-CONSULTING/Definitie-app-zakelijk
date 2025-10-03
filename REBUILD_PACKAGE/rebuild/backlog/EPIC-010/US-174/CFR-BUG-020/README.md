---
id: CFR-BUG-020
titel: Status-inconsistentie (APPROVED vs ESTABLISHED) in services/doc
status: open
owner: development-team
applies_to: definitie-app@current
last_verified: 2025-10-02
severity: MEDIUM
gevonden_op: 2025-09-15
component: workflow/status
---

# CFR-BUG-020: Status-inconsistentie (APPROVED vs ESTABLISHED) in services/doc

## Beschrijving
- `src/services/category_service.py:163` gebruikt string `"APPROVED"` i.p.v. canonieke `ESTABLISHED`.
- `src/services/interfaces.py::DefinitionStatus` definieert `APPROVED` terwijl workflow/repository `ESTABLISHED` gebruiken.
- README bevat verouderde notitie over APPROVED-bug.

## Verwacht Gedrag
Eén canonieke statusbron; services volgen `ESTABLISHED` terminologie.

## Oplossing
Onderdeel van [US-174](../US-174.md): code refactor + doc‑sync.

## Tests
- Unit: category‑wijziging bij ESTABLISHED niet toegestaan.
- Regex: geen `APPROVED` meer in services.

