---
id: US-437
epic: EPIC-003
titel: Provider Health Metrics
status: open
prioriteit: P2
story_points: 5
aangemaakt: 2025-09-30
bijgewerkt: 2025-09-30
owner: tbd
applies_to: definitie-app@current
canonical: false
last_verified: 2025-09-30
---

id: US-437
titel: Provider health & metrics (success rate, latency, error mix)

Doel
- Inzicht in beschikbaarheid en prestaties per web lookup provider met eenvoudige health-checks en metrics.

Waarom
- Proactief zien wanneer SRU-providers 404/406/503 geven of wanneer DNS/connect faalt; sneller debuggen en betere UX.

Scope
- Health-check per provider (bv. SRU explain, MediaWiki ping).
- Metrics: success rate, median latency, error mix per provider; eenvoudige dashboard/export.
- Alarms op spikes (minimaal log-based alerts/thresholds).

Acceptatiecriteria
- Metrics beschikbaar in logs of endpoint; documenteer velden.
- Smoke-test die health-checks aanroept en resultaten evalueert.

