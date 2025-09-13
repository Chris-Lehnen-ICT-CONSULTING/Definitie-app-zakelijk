---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-12
applies_to: definitie-app@current
---

# Database Richtlijnen

## Single Source
- Enige actieve databasebestand: `data/definities.db`.
- Geen databasebestanden in de projectroot of andere mappen.

## Initialisatie & Migratie
- Initieer schema via `src/database/schema.sql`.
- Optionele migraties: `python src/database/migrate_database.py data/definities.db`.
- Fallback CREATE in code is een noodpad; voorkeursroute is altijd `schema.sql`.

## Opslag & Backups
- Backups (optioneel) in `data/backups/` (git‑ignored).
- Verwijder stray `*.db`, `*.db-shm`, `*.db-wal` buiten `data/`.

## Kolommen (kern)
- Context: `organisatorische_context`, `juridische_context`.
- Wettelijke basis: `wettelijke_basis TEXT` (JSON array). Zie ook US‑154 voor normalisatievoorstel.
- Versiebeheer/audit: `version_number`, `previous_version_id`, triggers op `definitie_geschiedenis`.

## Normalisatie (vervolgwerk)
- Zie [US‑154](../backlog/EPIC-004/US-154/US-154.md) voor normalisatie naar `definitie_wettelijke_basis`.
- Zie [US‑110](../backlog/EPIC-004/US-110/US-110.md) voor bronverantwoording/generatie‑metadata tabellen.
