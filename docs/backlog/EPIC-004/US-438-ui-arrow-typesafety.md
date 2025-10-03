---
id: US-438
epic: EPIC-004
titel: "US-438: - Dtypes afdwingen (kolom 'status' e.a.) vóór Streamlit render om ArrowTypeError te voorkomen."
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

id: US-438
titel: UI DataFrame type-safety (ArrowTypeError fix)

Doel
- Dtypes afdwingen (kolom 'status' e.a.) vóór Streamlit render om ArrowTypeError te voorkomen.

Waarom
- Logs tonen ArrowTypeError door mixed types (int/bytes) in DataFrame; belemmert gebruikservaring en debugging.

Scope
- Normaliseer types (string/categorical) in UI pipeline.
- Toevoegen tests met gemengde input.

Acceptatiecriteria
- 0 ArrowTypeErrors in UI smoke suite.

