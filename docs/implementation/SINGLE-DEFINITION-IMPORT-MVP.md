---
canonical: true
status: draft
owner: development
last_verified: 2025-09-22
applies_to: definitie-app@current
---

# Single Definition Import (MVP) – Implementatieplan

Doel: een veilige, begrijpelijke flow om één definitie via de UI te importeren met V2‑validatie, duplicaatcontrole en logging.

Gerelateerd: EPIC-005 (Export & Import), US-234 (Single Definition Import), REQ-043 (Import), REQ-037 (Batch validatie – component hergebruik).

## MVP Doelstellingen
- UI‑flow voor één definitie (formulier/JSON)
- Validatie vóór opslag (ValidationOrchestratorV2)
- Duplicaatcontrole op begrip + context
- Opslag als Draft met juiste herkomstmetadata
- Logging naar `import_export_logs`

Niet‑doel (volgende iteraties): CSV/XLSX/JSONL, streaming, jobs/queue, batch‑rapportage.

## Architectuur & Componenten

### UI (Management tab)
- Sectie “Enkelvoudige import (MVP)” toevoegen in bestaande Management tab.
- Twee modi:
  1) Formulier: begrip, definitie, categorie, organisatorische_context[], juridische_context[]?, wettelijke_basis[]?
  2) JSON‑plakveld (zelfde schema)
- Knoppen: “Valideren”, daarna “Importeer als Draft”.
- Duplicate‑waarschuwing vóór definitieve opslag.

### Service‑laag
- Nieuwe service: `DefinitionImportService`
  - `validate_single(payload: dict) -> ValidationResult`
  - `import_single(payload: dict, *, allow_duplicate: bool=False) -> ImportResult`
- Hergebruik:
  - `ValidationOrchestratorV2.validate_definition(Definition)`
  - `DefinitionRepository.create_definitie(...)`
- Metadata bij opslag:
  - `source_type = "imported"`, `imported_from = "single_import_ui"`, `created_by = current_user|"ui_user"`

### Datamodel/Contract
Input JSON (formulier mapped):
```json
{
  "begrip": "string",
  "definitie": "string",
  "categorie": "string",
  "organisatorische_context": ["string"],
  "juridische_context": ["string"],
  "wettelijke_basis": ["string"]
}
```
Opmerkingen:
- Lijsten worden opgeslagen volgens V2‑model (repository verwacht JSON/tekst representatie op kolommen; mapping gebeurt in service/repository helpers).

## Flow
1) Gebruiker vult formulier of plakt JSON
2) UI roept `validate_single` aan → toon score + violations
3) Duplicate‑check (begrip + context); toon waarschuwing
4) Gebruiker bevestigt → `import_single` slaat als Draft op
5) Resultaat tonen + logging in `import_export_logs`

## Validatie
- Gebruik `ValidationOrchestratorV2` met contextverrijking uit payload
- Timeouts volgen bestaande instellingen
- Toon samenvatting: acceptable flag/score + violations (code, severity, message)

## Duplicaatstrategie (MVP)
- Default: blokkeren bij exact duplicaat (toon welke record bestaat)
- Optioneel (feature‑toggle): overschrijven toestaan (buiten MVP veilig uit)

## Veiligheid & UX
- Input sanitiseren, lengte‑limieten, UTF‑8
- Duidelijke foutmeldingen (wat en waarom)
- Geen secrets/PII in logs; alleen noodzakelijke metadata loggen

## Stappenplan Implementatie
1) Service skeleton `DefinitionImportService` (validate/import_single)
2) UI‑sectie in Management tab (Form/JSON, validate→preview→import)
3) Duplicate‑check integreren (repository.find_duplicates)
4) Logging naar `import_export_logs`
5) Documentatie en helptekst in UI

## Teststrategie
- Unit: service.validate_single (happy/invalid/edge cases)
- Unit: service.import_single (nieuw record, duplicate blok, metadata check)
- Integratie: UI → service → repository → logtabel
- Negatief: lege velden, te lange input, invalid JSON

## Rollbackplan
- Geen migraties; alleen nieuwe service + UI sectie
- Feature‑toggle voor overschrijven uit; alleen Draft‑opslag
- Herstel: verwijder laatste geïmporteerde record via Management tab (admin)

## Bekende risico’s
- Onbedoelde duplicaten (mitigatie: blokkerende default)
- Validatie‑latentie (mitigatie: behoud timeout; toon spinner)
- Onjuiste mapping (mitigatie: minimale velden, duidelijke types)

## Links
- EPIC-005: docs/backlog/EPIC-005/EPIC-005.md
- US-234: docs/backlog/EPIC-005/US-234/US-234.md
- Vereisten: docs/backlog/requirements/REQ-043.md, docs/backlog/requirements/REQ-037.md

