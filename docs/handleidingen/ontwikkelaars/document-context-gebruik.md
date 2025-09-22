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

# Documentcontext gebruiken in de prompt (ontwikkelaars)

## Doel

Korte how‑to voor het doorgeven en gebruiken van documentcontext in de prompt.

## Stap 1 — Samenvatting bouwen

Gebruik `DocumentProcessor.get_aggregated_context(selected_ids)` en vorm een compacte string met de belangrijkste keywords/concepten/juridische verwijzingen.

## Stap 2 — Doorgeven aan service

Geef de samenvatting mee in `GenerationRequest` als `document_context`:

```python
from services.interfaces import GenerationRequest

request = GenerationRequest(
    id=str(uuid4()),
    begrip=begrip,
    organisatorische_context=org_list,
    juridische_context=jur_list,
    wettelijke_basis=wet_list,
    ontologische_categorie=categorie,
    options=opts,
)
request.document_context = summary  # korte samenvatting
```

HybridContextManager voegt deze bron toe met hoge confidence; `ContextAwarenessModule` formatteert de contextsectie.

## Optioneel — Snippet‑injectie

Converteer (sanitized) fragmenten naar hetzelfde schema als web_lookup sources en zet `used_in_prompt=True`. Respecteer `max_snippets` en `total_token_budget` (PromptServiceV2).

## Let op

- Installeer extractie‑libs: `pip install python-docx PyPDF2`
- Geen `.doc` en geen OCR; zie Phoenix‑EPIC voor uitgebreidere scope

## Configuratie (env)

- `DOCUMENT_SNIPPETS_ENABLED` (true|false): schakel snippet‑injectie in/uit (default: true)
- `DOCUMENT_SNIPPETS_MAX` (int): maximaal aantal snippets in de prompt over alle documenten (default: 16)
- `DOCUMENT_SNIPPETS_PER_DOC` (int): maximaal aantal matches per document (default: 4)
- `SNIPPET_WINDOW_CHARS` (int): vensterlengte rondom de match (default: 280)
- `DOCUMENT_SNIPPETS_MAX_CHARS` (int): totaal aantal tekens over alle snippets (default: 800)

Voorbeeld (shell):
```bash
export DOCUMENT_SNIPPETS_ENABLED=true
export DOCUMENT_SNIPPETS_PER_DOC=4
export SNIPPET_WINDOW_CHARS=280
export DOCUMENT_SNIPPETS_MAX=16
export DOCUMENT_SNIPPETS_MAX_CHARS=800
```
