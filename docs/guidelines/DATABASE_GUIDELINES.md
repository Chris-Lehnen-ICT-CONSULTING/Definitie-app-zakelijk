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
- Context (canoniek, alle drie gelijkwaardig en verplicht: minimaal 1 gevuld):
  - `organisatorische_context TEXT` (JSON array)
  - `juridische_context TEXT` (JSON array)
  - `wettelijke_basis TEXT` (JSON array)
- Opmerking: alle drie contexten worden als JSON‑lijsten opgeslagen; er is geen primair/speciaalfeld meer.
- Versiebeheer/audit: `version_number`, `previous_version_id`, triggers op `definitie_geschiedenis`.

## Normalisatie (vervolgwerk)
- Normalisatie naar relationele tabellen is niet vereist; het JSON‑array patroon is de canonieke opslag per veld.
- Zie [US‑110](../backlog/EPIC-004/US-110/US-110.md) voor bronverantwoording/generatie‑metadata tabellen.
