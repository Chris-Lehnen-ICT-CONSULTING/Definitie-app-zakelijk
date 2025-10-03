---
aangemaakt: 2025-09-22
applies_to: definitie-app@current
bijgewerkt: 2025-09-22
canonical: true
completion: 0%
id: EPIC-018
last_verified: 2025-09-22
owner: architecture
prioriteit: HOOG
status: Nog te bepalen
stories:
- US-225
- US-227
- US-228
- US-229
- US-230
- US-231
- US-232
- US-233
target_release: v1.3
titel: Document Context Integratie (Upload, Extractie, Promptgebruik)
vereisten:
- REQ-022
---

# EPIC-018: Document Context Integratie (Upload, Extractie, Promptgebruik)

## Managementsamenvatting

Gebruikers kunnen documenten (DOCX/PDF/TXT/…) uploaden voor context. De applicatie extraheert tekst, aggregeert kernsignalen (keywords/concepten/juridische verwijzingen) en gebruikt deze documentcontext bij het genereren van definities. Optioneel kunnen korte fragmenten als “Bron” in de prompt worden geïnjecteerd met token‑budgetbewaking.

## Bedrijfswaarde

- Verhoogde relevantie: definities sluiten beter aan op aangeleverde context
- Efficiëntie: minder handmatig knip‑/plakwerk uit brondocumenten
- Transparantie: zichtbare bronvermelding en herleidbaarheid

## Succesmetrieken (SMART)

- [ ] ≥ 80% van uploads levert > 1.000 tekens bruikbare tekst op (DOCX/PDF)
- [ ] Prompt toont documentcontext aanwezig (UI‑indicator) bij ≥ 90% van generaties met selectie
- [ ] End‑to‑end test upload→selectie→generatie groen in CI
- [ ] Geen PII in logs; extractie‑fouten < 5% bij ondersteunde formaten

## Scope

- Minimale extractie: python‑docx, PyPDF2 (geen OCR, geen .doc)
- UI selectie en aggregatie van documentcontext
- Doorvoer van documentcontext naar prompt (contextsectie)
- Optioneel: snippet‑injectie als “Bron X” met token‑budget

## Out‑of‑Scope (voor nu)

- OCR scan‑PDFs, sectieselectie, preview, storage encryptie (zie EPIC‑020‑PHOENIX/US‑211)

## Gebruikersverhalen (overzicht)

- US‑225: DOCX/PDF extractors actief (python‑docx, PyPDF2)
- US‑227: Documentcontext doorgeven aan service (GenerationRequest)
- US‑228: UI‑feedback dat documentcontext is gebruikt
- US‑229: Optioneel — document‑snippets in promptinjectie
- US‑230: Extractor unit tests
- US‑231: Integratietests upload→selectie→generatie
- US‑232: Monitoring/metrics voor extractie
- US‑233: Documentatie (usage + troubleshooting)

## Niet‑functioneel

- Performance: extractie < 2s voor standaard DOCX 10 pagina’s; < 5s voor PDF 10 pagina’s
- Beveiliging: geen PII in logs; geen opslag van oorspronkelijke bestanden buiten cache/testomgevingen
- Logging: type, lengte, duur, status (zonder content dumps)

## Definitie van Gereed

- [ ] Upload→extractie→selectie→generatie gebruikt documentcontext aantoonbaar
- [ ] UI toont indicator en logging bevestigt contextverwerking
- [ ] Unit + integratietests groen in CI
- [ ] Documentatie up‑to‑date (handleiding + troubleshooting)

