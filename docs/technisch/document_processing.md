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

