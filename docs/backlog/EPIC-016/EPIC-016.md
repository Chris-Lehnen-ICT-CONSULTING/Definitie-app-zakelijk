---
id: EPIC-016
titel: "EPIC-016: Beheer & Configuratie Console - UI-beheer voor gate-policy, validatieregels, context en audit met hot-reload"
status: active
prioriteit: HOOG
owner: product-owner
applies_to: definitie-app@current
canonical: true
last_verified: 2025-09-15
stories:
  - US-181
  - US-182
  - US-183
  - US-184
  - US-185
  - US-186
  - US-187
---

# EPIC-016: Beheer & Configuratie Console

## Doel
Één centrale, beheerder‑gerichte UI‑tab om alle belangrijke variabelen en policies te beheren zonder codewijziging: gate‑policy, validatieregels, contextopties, audit en import/export. Veranderingen zijn auditeerbaar, versioneerbaar en direct effectief binnen de V2‑architectuur.

## Business Value
- Verkort doorlooptijd van configuratiewijzigingen (geen code‑deploy nodig).
- Auditability/compliance: elke wijziging is traceerbaar en terug te draaien.
- Betere kwaliteitsbewaking via centrale gate‑ en regels‑configuratie.

## Scope
### In Scope
- UI‑tab “⚙️ Beheer” met subsections: Gate‑policy, Validatieregels, Contextopties, Audit, Import/Export, Autorisatie.
- Configuratieopslag in DB met audit + versies; hot‑reload voor services.
- Minimal‑auth: beheerderrol via flag/env (voor nu), audit van alle beheeracties.

### Out of Scope
- Volledige identity & access management (OIDC/SAML) integratie (valt onder EPIC‑006).
- Nieuwe database migraties buiten de noodzakelijke configtabellen (schema.sql blijft bron; configtabellen kunnen separaat worden beheerd indien al aanwezig).

## Dependencies
- EPIC‑004 (UI): layout, navigatie, componenten.
- EPIC‑012 (orchestrator/validation): integratie om live config te lezen.
- GatePolicyService en ModularValidationService bestaan reeds (loader/TTL‑cache) en worden hergebruikt (src/services/policies/approval_gate_policy.py, container wiring).

## Non‑Functionals & Constraints
- Respecteer CLAUDE.md: canonical locaties, geen backwards‑compat paden, services async‑puur (UI doet bridging).
- Veiligheid: geen secrets loggen; export/import zonder PII; audit verplicht.
- Performance: hot‑reload zonder app‑restart; UI reactietijd < 300ms voor lijstweergaves bij 1k regels.

## Acceptatiecriteria (Epic)
- Alle subsections bedienbaar in UI; wijzigingen worden in DB opgeslagen met audit én versie.
- Services lezen actuele config (TTL‑cache, invalidatie bij wijzigingen) – zichtbaar effect zonder herstart.
- Import/Export JSON/YAML met diff‑preview; rollback naar vorige versies mogelijk.
- Autorisatie: beheer‑tab en mutaties alleen voor beheerderrol (flag‑based in deze iteratie) met audit van acties.

## Definition of Done (Epic)
- US‑171..US‑177 gerealiseerd en groen getest (unit/integratie).
- Documentatie bijgewerkt (README secties, referentie naar GatePolicy/validatieregelsbeheer).
- CI‑gates en smoke checks dekken critical paths (geen Streamlit in services, V2‑contracten onveranderd).

## Risks & Mitigations
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Onjuiste config blokkeert vaststellen | Hoog | Medium | Preview/validatie, soft‑gate fallback, rollback |
| Inconsistentie cache vs DB | Medium | Low | TTL‑cache + expliciete invalidatie bij update |
| Te veel toggles → onvoorspelbaar gedrag | Medium | Medium | Audit, testprotocol bij wijziging, export snapshot |

## Implementation Plan (Fases)
1) US‑181 UI‑skelet Beheer‑tab (navigatie, secties, geen mutaties).
2) US‑182 Gate‑policy beheer (CRUD + audit + hot‑reload; DI in workflow).
3) US‑183 Validatieregelsbeheer (gewichten/drempels/actief + audit + reload).
4) US‑184 Contextopties (CRUD lijsten; hot‑reload in ContextManager).
5) US‑185 Auditlog & versiebeheer (diff/rollback, retentiebeleid).
6) US‑186 Import/Export JSON/YAML (preview/diff, atomic apply).
7) US‑187 Autorisatie voor Beheer (flag‑gebaseerde rol, server‑side checks).

## Traceability
- REQ‑093/US‑160: Gate‑policy integratie in workflow.
- REQ‑094: Validatieregels beheerbaar maken.
- REQ‑095: Contextopties centraal beheer.
- REQ‑097: Gate‑afhankelijkheden m.b.t. iteratieve acceptatie (alleen policy‑zijde; iteraties zijn EPIC‑017).
