---
id: EPIC-016
titel: Beheer & Configuratie Console
status: Backlog
prioriteit: HOOG
owner: product-owner
applies_to: definitie-app@current
canonical: true
last_verified: 2025-09-13
stories:
- US-161
- US-162
- US-163
- US-164
- US-165
- US-166
- US-167
---

# EPIC-016: Beheer & Configuratie Console

## Doel
Één centrale UI‑tab om alle belangrijke variabelen en policies te beheren zonder codewijziging: gate‑policy, validatieregels, contextopties, audit en import/export.

## Succescriteria
- [ ] Alle variabelen via UI te beheren (met confirmatie en audit)
- [ ] Wijzigingen direct effectief (hot‑reload of veilige herlaad)
- [ ] Autoriseerbaar (beheerderrol in vervolg)
- [ ] Geen regressie in bestaande flows

## Globale scope
- UI‑tab “⚙️ Beheer” met subsecties
- Opslag in DB (config‑tabel) met audit trail en versies
- Minimale caching, hot‑reload support

## Dependencies
- EPIC‑004 (UI)
- EPIC‑012 (validation/orchestrator) – integratie voor validatieregels

