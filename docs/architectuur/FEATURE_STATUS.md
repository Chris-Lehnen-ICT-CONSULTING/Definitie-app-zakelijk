---
canonical: false
status: active
owner: architecture
last_verified: 2025-09-02
applies_to: definitie-app@v2
---

# Feature/Status Overzicht (Dashboard-only)

Dit document wijst de dashboard‑bron aan voor statusoverzichten.

- Canonieke health/statusbron: `reports/status/validation-status.json`.
- `architectuur/feature-status.json` wordt alleen gebruikt door het web‑dashboard en is geen bron van waarheid voor implementatiestatus.

Richtlijn:
- Gebruik `reports/status/validation-status.json` voor rapportage en audits.
- Verwijs in stories/architectuur naar de canonieke bron.
