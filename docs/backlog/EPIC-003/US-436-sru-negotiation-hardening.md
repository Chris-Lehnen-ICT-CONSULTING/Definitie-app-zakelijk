---
id: US-436
epic: EPIC-003
titel: "US-436: - Robuuste SRU-integratie met oai_dc → srw_dc → dc schema-ladder en correcte content negotiation (Accept/httpAccept/r..."
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

id: US-436
titel: SRU negotiation hardening (schema ladder, Accept/httpAccept, diagnostics)

Doel
- Robuuste SRU-integratie met oai_dc → srw_dc → dc schema-ladder en correcte content negotiation (Accept/httpAccept/recordPacking) per provider.

Waarom
- Historisch 406 Not Acceptable op BWB en 404 op alternatieve paden. We willen voorspelbaar gedrag, minder fallback-spam en duidelijke diagnostics.

Scope
- SRU v2.0: voeg httpAccept=application/xml, recordPacking=xml toe; schema-fallback bij 406.
- Diagnostics parsing en logging (code/message/details).
- (Optioneel) explain-caching met TTL; index-checks voor titel/dc.title.

Acceptatiecriteria
- ≤ 5% 404/406 per 100 requests op testset (niet-netwerk gerelateerd).
- Attempts bevatten diag_message/diag_details bij non-200.
- Unit/integration tests voor BWB en Overheid.nl Zoekservice.

Notities
- Rechtspraak DNS/connect blijft omgevingsafhankelijk; detecteer en log apart.

