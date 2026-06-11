# Linear Backlog-Audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (aparte sessie) of subagent-driven-development (deze sessie) om dit plan taak-voor-taak uit te voeren.

**Goal:** Alle 68 open DEF-issues verifiëren tegen de werkelijke codebase, tech-debt correct labelen, en per issue een controle-comment plaatsen met advies (BIJWERKEN / SLUITEN / HOUDEN / SPLITSEN).

**Architectuur:** Orchestrator-met-agent-teams. De orchestrator (hoofdagent) doet alle Linear-writes (comments, labels — Linear MCP ondersteunt geen bulk, dus één call per issue) en dispatcht read-only Explore-agents per themacluster voor codebase-verificatie. Max 5 agents parallel (globale regel), dus 8 clusters in 2 waves. Orchestrator verifieert agent-bevindingen steekproefsgewijs vóór publicatie (orchestrator-verificatie is verplicht).

**Tech Stack:** Claude Code Agent tool (Explore, read-only), Linear MCP (`mcp__claude_ai_Linear__*`), git/grep voor bewijsvoering.

---

## Scope & Inventaris (vastgesteld 2026-06-10)

- **68 open issues**, allemaal status `Backlog` (triage/unstarted/started: leeg).
- Label `tech-debt` **bestaat nog niet** in team DEF → aanmaken in Taak 1.
- Volledige issue-lijst (JSON, incl. afgekapte beschrijvingen): reeds opgehaald; per cluster worden volledige beschrijvingen via `get_issue` opgehaald.
- Reeds geverifieerde grounding: `src/ai_toetser/` bestaat NIET (DEF-417 klopt); geen frontend-code in repo (DEF-330/341–348 zijn greenfield); `src/services/rag/` bestaat (RAG deels gestart).

### Verdicts (vast vocabulaire)

| Verdict | Betekenis |
|---------|-----------|
| ACTUEEL | Issue klopt met codebase, werk is nog nodig |
| VEROUDERD | Beschrijving verwijst naar niet-meer-bestaande code/paden/aantallen |
| DEELS-GEDAAN | Deel van het werk is al gerealiseerd (commit-bewijs) |
| AL-GEDAAN | Volledig gerealiseerd → advies SLUITEN |
| ONJUIST | Claim klopt aantoonbaar niet → advies SLUITEN/STOPPEN |

### Adviezen

`HOUDEN` · `BIJWERKEN` (beschrijving actualiseren) · `SLUITEN` (done/onjuist/obsolete) · `SPLITSEN` (te groot) — altijd met motivatie + bewijs (file:regel of commit-hash).

### Comment-template (per issue, door orchestrator geplaatst)

```markdown
## 🔍 Backlog-audit 2026-06-10

**Status t.o.v. codebase:** {VERDICT}
**Bevindingen:** {bullets met bewijs: file:regel / commit / grep-resultaat}
**Tech-debt:** {ja → label toegekend / nee}
**Advies:** {HOUDEN|BIJWERKEN|SLUITEN|SPLITSEN} — {motivatie}

_Gecontroleerd door Claude Code agent-team; bevindingen geverifieerd door orchestrator._
```

### Clusterindeling (8 clusters, 68 issues)

| # | Cluster | Issues | Aantal | Focus verificatie |
|---|---------|--------|--------|-------------------|
| 1 | Verse tech-debt-audit | DEF-416…426 | 11 | Sanity-check (vandaag aangemaakt) + `tech-debt` label toekennen |
| 2 | Meta/config-debt | DEF-192, 312, 404, 405, 407 | 5 | Bestaan genoemde files/regels nog? Overlap met cluster 1? |
| 3 | Improvements/bugs | DEF-197, 382, 391, 392, 393, 394 | 6 | Is werk (deels) gedaan? Bestaat `hybrid_context/` nog? |
| 4 | Ontologie fase 2–4 | DEF-47, 49, 286, 287, 288, 294–302, 306, 307, 308 | 17 | Epics/stories vs. bestaande `domain/`/`services/`; duplicaten |
| 5 | VALOR | DEF-383, 384, 385, 386 | 4 | Bestaat al VALOR-code? (root bevat valor-html-artefacten) |
| 6 | RAG | DEF-285, 292, 368, 369 | 4 | `src/services/rag/` bestaat — wat is al af? |
| 7 | Frontend/deployment | DEF-311, 330, 341, 342, 343, 347, 348 | 7 | Greenfield-check + post-mvp-labeling; DEF-311 vs `.env`-praktijk |
| 8 | Prompt-system (nov 2025) | DEF-106, 157–168, 253 | 14 | Oudste cluster — prompt-modules zijn sindsdien verbouwd; veel kans op AL-GEDAAN/VEROUDERD |

---

## Taken

> NB: dit is een audit-/orkestratieplan, geen code-feature — de TDD-cyclus is hier "verifieer vóór je schrijft": elke Linear-write wordt voorafgegaan door bewijs-verificatie. Geen git-commits per taak (er wordt geen code gewijzigd); wel een eindrapport-commit in Taak 7.

### Taak 0: Werkmap + tracking

**Step 1:** Maak werkmap: `.claude/audits/2026-06-10-backlog-audit/`
**Step 2:** Maak takenlijst aan (TaskCreate) met één taak per cluster + setup + rapport.
**Step 3:** Update `.claude/handovers/WIP-active.md` (wip-tracker regel).

### Taak 1: Linear-setup — `tech-debt` label

**Step 1:** `mcp__claude_ai_Linear__create_issue_label` → team DEF, naam `tech-debt`, kleur `#8B7355`, beschrijving "Technische schuld — gevonden via backlog-audit".
**Step 2:** Verifieer met `list_issue_labels` dat het label bestaat; noteer label-UUID.

### Taak 2: Briefing-bestanden per cluster

**Step 1:** Haal per cluster de volledige beschrijvingen op (`get_issue`, één call per issue — alleen waar de dump afgekapt is).
**Step 2:** Schrijf per cluster `.claude/audits/2026-06-10-backlog-audit/cluster-{N}-briefing.md` met: issue-ID, titel, prioriteit, labels, volledige beschrijving, en de cluster-specifieke verificatievragen uit de tabel hierboven.
**Step 3:** Controleer dat alle 68 issues in precies één briefing staan (`grep -c "DEF-"`).

### Taak 3: Wave 1 — dispatch clusters 1–5 (5 Explore-agents parallel)

**Step 1:** Dispatch 5 Explore-agents (read-only) in één bericht. Prompt per agent bevat:
- Pad naar briefing-bestand (agent leest zelf).
- Verificatieprotocol: (a) elke claim in de issue checken tegen codebase met Read/Grep/`git log`; (b) GEEN BEWIJS = NIET RAPPORTEREN (review-guidelines); (c) per issue verdict + bewijs + tech-debt ja/nee + advies + concept-comment in NL volgens template.
- Outputformaat: markdown-tabel + per issue een blok, terugschrijven als agent-resultaat (NIET zelf naar Linear of WIP schrijven).
**Step 2:** Sla elk agent-resultaat op als `cluster-{N}-resultaat.md`.

### Taak 4: Wave 2 — dispatch clusters 6–8 (3 agents parallel)

Zelfde protocol als Taak 3.

### Taak 5: Orchestrator-verificatie (verplicht)

**Step 1:** Per cluster minimaal 2 bevindingen zelf naverifiëren (Read/Grep op de geciteerde file:regel; `git log` voor AL-GEDAAN-claims).
**Step 2:** Elke SLUITEN- of ONJUIST-verdict: 100% naverifiëren (onomkeerbaar advies = hoogste bewijslast).
**Step 3:** Bij discrepantie: verdict degraderen naar "needs review" en dat in de comment vermelden. Max 3 pogingen per verificatie, daarna rapporteren.

### Taak 6: Linear-updates (orchestrator, sequentieel)

**Step 1:** Per issue één `save_comment` met ingevulde template (68 calls, één per issue — Linear MCP quirk: geen bulk).
**Step 2:** Tech-debt-issues: label toekennen via `mcp__linear-mcp__linear_bulk_update_issues` met `issueIds=[één-id]` en `update={"labelIds": [...bestaande + tech-debt-uuid]}` — let op: labelIds VERVANGT, dus eerst bestaande labels meenemen.
**Step 3:** Issues met advies SLUITEN: NIET zelf sluiten — alleen comment + advies; sluiten is een gebruikersbeslissing.
**Step 4:** Telling verifiëren: 68 comments geplaatst (steekproef `list_comments` op 3 issues).

### Taak 7: Eindrapport + afronding

**Step 1:** Schrijf `.claude/audits/2026-06-10-backlog-audit/eindrapport.md`: totalen per verdict/advies, tech-debt-lijst, aanbevolen sluitingen (besliswachtrij voor gebruiker), bronnenlijst.
**Step 2:** Commit audit-artefacten op feature branch `chore/DEF-backlog-audit-2026-06-10` (NOOIT op main).
**Step 3:** Archiveer WIP, presenteer eindrapport-samenvatting aan gebruiker met de SLUITEN-besliswachtrij.

---

## Risico's & mitigaties

| Risico | Mitigatie |
|--------|-----------|
| Subagents hebben geen Linear MCP-toegang | Briefing-bestanden bevatten volledige issue-tekst; agents raken Linear nooit aan |
| `labelIds` vervangt bestaande labels | Vóór elke label-update eerste huidige labels ophalen en meesturen |
| Agent-hallucinatie (vals AL-GEDAAN) | Taak 5: 100% naverificatie op SLUITEN/ONJUIST |
| Context-overflow orchestrator | Agent-resultaten naar bestanden; orchestrator leest per cluster |
| 68 comments = veel writes | Sequentieel, met telling-verificatie achteraf |

## Verificatie bij oplevering

- [ ] 68/68 issues hebben een audit-comment
- [ ] `tech-debt` label bestaat en is toegekend aan alle bevestigde tech-debt-issues
- [ ] Alle SLUITEN-adviezen 100% naverifieerd met bewijs
- [ ] Eindrapport met bronnenlijst opgeleverd
- [ ] Geen enkel issue gesloten zonder expliciete gebruikersinstructie
