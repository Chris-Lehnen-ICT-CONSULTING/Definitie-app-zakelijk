# BATCH-021 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 2/2 blobs, 5.595/5.595 fysieke regels en 0 Python-symbolen

Alle regels zijn uit immutable blobs gelezen; tellingen en Git-statussemantiek
zijn onafhankelijk gereproduceerd. De externe agentprompt is niet uitgevoerd.

## Bevindingen

### B021-001 — P2 — severityrubric kan ernstige codedefecten niet classificeren

`prompts/orchestrate-definitie-app-v2.md:84-91` staat CRITICAL alleen toe bij
een missing node plus Linear-bevestiging en HIGH bij AST-bevestiging. Een bewezen
RCE, datacorruptie of credentiallek zonder missing node past daardoor niet.
Aanbevolen: impactcriteria voor security, integriteit, beschikbaarheid en privacy;
bewijs/consensus los van issue tracker of AST classificeren.

### B021-002 — P2 — drie kritieke gebieden missen de derde reviewer

`orchestrate-definitie-app-v2.md:17-18,45-49,70-71,2161-2490` belooft drie
agents voor 31 gebieden maar bevat 90 in plaats van 93 `Task(`-calls. Gebieden
12, 13 en 14 hebben alleen A/B en missen architectuurreview. Aanbevolen: 12C,
13C en 14C toevoegen en de volledige matrix `(1..31) × (A,B,C)` testen.

### B021-003 — P3 — staged en unstaged staan omgekeerd

`orchestrate-definitie-app-v2.md:200-221` noemt ` M` staged en `M ` unstaged.
Git porcelain gebruikt X voor index/staged en Y voor worktree/unstaged.
Aanbevolen: labels omwisselen en X/Y expliciet documenteren.

## Niet getest

- Geen dynamische uitvoering van de 90 externe agenttaken.
- Geen netwerk, credentials, modelconsensus of UI-flow.
