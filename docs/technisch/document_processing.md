---
aangemaakt: '2025-09-22'
applies_to: definitie-app@current
bijgewerkt: '2025-09-22'
canonical: true
last_verified: 2025-09-22
owner: architecture
prioriteit: medium
status: active
---

# Document Processing & Context Flow

Dit document beschrijft de extractie‑ en contextverwerkingsflow van geüploade documenten.

## Ondersteunde formaten en dependencies

- TXT (geen extra deps)
- DOCX → python‑docx (vereist)
- PDF → PyPDF2 (vereist)
- MD/CSV/JSON/HTML/RTF (basisextractie)

Niet ondersteund (nu):
- Legacy `.doc`
- OCR voor gescande PDF’s (zie EPIC‑020‑PHOENIX/US‑211)

## Dataflow

1) UI upload: Streamlit `file_uploader` → bytes + bestandsnaam
2) Extractie: `extract_text_from_file(...)` (op basis van MIME) → tekst of fallbackmelding
3) Analyse: `DocumentProcessor` → keywords, concepten, juridische verwijzingen, hints
4) Aggregatie (bij selectie): `get_aggregated_context(ids)` → compactte samenvatting
5) Promptgebruik:
   - Contextsectie: samenvatting als `document_context` in `GenerationRequest` → HybridContextManager → ContextAwarenessModule
   - Optioneel snippets: korte “Bron”‑regels binnen tokenbudget

## Beperkingen & foutafhandeling

- Bij ontbrekende libs levert extractie een korte waarschuwingstekst; dit is géén geldige documentcontext
- Logging bevat alleen type/duur/status/length, geen content (AVG)

## Integratiepunten

- UI: selectie van documenten + weergave “Totale tekst”
- ServiceFactory: doorgeven `document_context` naar `GenerationRequest`
- PromptServiceV2: HybridContextManager (documentbron) + optionele snippet‑injectie

## Snippet‑injectie (EPIC‑018)

- Doel: korte fragmenten uit geüploade documenten toevoegen aan de prompt met bronvermelding.
- Matching: case‑insensitive zoek op het ingevoerde begrip in de geselecteerde documenten.
- Locatiebepaling:
  - PDF: pagina via form feed scheiding tussen pagina’s in de geëxtraheerde tekst → label “p. X”.
  - DOCX: paragraaf benaderd via newline‑tellingen → label “¶ Y”.
- Grenzen en toggles (env):
  - `DOCUMENT_SNIPPETS_ENABLED` (default: `true`)
  - `DOCUMENT_SNIPPETS_MAX` totaal in prompt (default: `16`)
  - `DOCUMENT_SNIPPETS_PER_DOC` per document (default: `4`)
  - `SNIPPET_WINDOW_CHARS` venstergrootte per match (default: `280`)
  - `DOCUMENT_SNIPPETS_MAX_CHARS` totaal aantal tekens over alle snippets (default: `800`)
- Sanitization: fragmenten worden geschoond via de bestaande `sanitize_snippet` logica voordat ze in de prompt worden geplaatst.
- UI: onder “📚 Gebruikte Bronnen” verschijnen `documents`‑bronnen met bestandsnaam en “Locatie: p. X/¶ Y” en de badge “→ In prompt”.
