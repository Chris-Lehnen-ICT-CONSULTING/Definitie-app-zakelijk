# BATCH-020 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 1/1 blob, 5.754/5.754 fysieke regels en 0 Python-symbolen

De volledige prompt is line-by-line gelezen en mechanisch tegen de immutable
Git-tree vergeleken. De prompt is niet met externe agents uitgevoerd.

## Verificatie

- Exact 98 `Task(`-calls en 31 gebieden geteld.
- De scopeglobs zijn via set equality tegen alle 372 `src/**/*.py`-paden getest.
- Geen repositorycaller gevonden; geen netwerk of credentials gebruikt.

## Bevindingen

### B020-001 — P2 — scopeclaim mist 78 productie-Pythonbestanden

`prompts/orchestrate-architecture-analysis.md` bevat 36 one-level globs. Deze
dekken 294 van 372 productie-Pythonbestanden; 78 ontbreken, waaronder
`src/main.py`, migraties, AI, RAG, prompts en UI-handlers. Gebieden 6, 10 en 17
matchen niets. Aanbevolen: scope uit de immutable Git-tree genereren, recursive
of exacte assignments gebruiken en set equality als fail-gate afdwingen.

### B020-002 — P2 — analyseprompt bevat edit-retry-instructies en fout Git-model

`orchestrate-architecture-analysis.md:188-345` en alle 98 taken instrueren na
iedere file-edit te verifiëren en bij falen opnieuw te editen, hoewel de opdracht
analyse is. Dit is een bewezen prompt-confusionrisico; daadwerkelijke mutatie is
niet getest. De tabel op 215-220 verwisselt bovendien ` M` (unstaged) en `M `
(staged). Aanbevolen: expliciet read-only/verboden writes, editinstructies
verwijderen en een machinegeteste porcelain-X/Y-uitleg opnemen.

## Niet getest

- Geen uitvoering van de 98 externe taken of modelconsensus.
- Geen applicatie- of UI-flow; dit is een promptdocument.
