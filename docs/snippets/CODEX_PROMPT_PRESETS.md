---
titel: Codex Prompt Presets & Multi‑Agent Cheatsheet
aangemaakt: 2025-09-12
status: active
canonical: false
owner: development
last_verified: 2025-09-12
applies_to: definitie-app@current
---

# Codex Prompt Presets & Multi‑Agent Cheatsheet

Korte, praktische referentie voor parallel werken met meerdere agents (worktrees/patches) en voor hoogwaardige analyse‑prompts voor Codex.

## Samenvatting
- Doel: parallel ideeën laten uitwerken en beste patch kiezen met objectieve criteria.
- Strategieën: git worktrees (aanrader), sequentiële patches, debate/critique met arbiter.
- Beoordeling: tests groen, EPIC‑010 conform (geen legacy), lage codechurn, stabiel en snel.

## Kerncommando’s Multi‑Agent

### Parallel (git worktrees)
```bash
git worktree add ../Definitie-app-agent-a -b agent-a
git worktree add ../Definitie-app-agent-b -b agent-b
git worktree add ../Definitie-app-agent-c -b agent-c

# Open per worktree een eigen sessie
cd ../Definitie-app-agent-a
```

### Sequentieel (patches)
```bash
# Agent A
git diff > patches/agent-a.patch && git reset --hard

# Apply en testen
git apply --check patches/agent-a.patch && git apply patches/agent-a.patch && pytest -q
```

### Quick checks (legacy/V2‑UI)
```bash
rg -n "from src.models.generation_result import|best_iteration|asyncio\.run\(" src/ && echo "LEGACY FOUND" || echo "OK"
rg -n "definitie_gecorrigeerd|validation_details|voorbeelden|metadata" src/ui/
```

### Scoreboard (simpel)
```bash
for b in agent-a agent-b agent-c; do 
  git checkout "$b" >/dev/null 2>&1 || continue
  start=$(date +%s)
  pytest -q || status=$?
  dur=$(( $(date +%s) - start ))
  echo "BRANCH=$b DURATION=${dur}s STATUS=${status:-0}"
done
```

### Codex deep config
```bash
codex config set model=o1
codex config set temperature=0.1
codex config set max_output_tokens=4096
codex config set plan.enabled=true
codex config set plan.autoupdate=true
codex config set trace.enabled=true
codex config set debug.enabled=true
codex config set patch.confirm=true
codex config set test.auto=true
codex config set patch.preview=true

# Alias (optioneel)
alias codex-deep='codex --trace --debug'
```

### Slash Commands (agent toggles)
Gebruik deze in je chat om gedrag te sturen (details in `docs/guidelines/AGENTS.md`).

- `/strict on` | `/strict off` — strict mode (geen aannames; pauzes voor akkoord bij patches/tests/netwerk/DB).
- `/approve` | `/approve all` — geef akkoord voor geblokkeerde stap(pen).
- `/deny` — weiger volgende geblokkeerde stap.
- `/plan on` | `/plan off` — planmodus forceren/uitzetten.
- Scopes: `/strict on patch,test` om alleen bepaalde domeinen te gaten (`patch`, `test`, `network`, `db`, `all`).

## Prompt Presets (Copy‑Paste)

### How to use (quick)
- Open deze cheatsheet naast je Codex sessie.
- Plak de “Deep‑Analysis Prompt” bovenaan je opdracht en vul doel/scope in.
- Run de “Pre‑flight Checklist” als sub‑taken; laat Codex resultaten inline rapporteren.
- Na analyse: gebruik de “Implementatie‑verdieping” prompt voor patchvoorstellen.
- Werk met agents via worktrees of patches (zie Kerncommando’s) en kies de beste variant met het Scoreboard.

### Deep‑Analysis Prompt
```
Context:
- Doel: <beschrijf kort je doel/issue>
- Scope/Bestanden: <noem kernbestanden of dirs>
- Constraints: respecteer CLAUDE.md (geen backwards‑compat, geen Streamlit in services, geen asyncio.run in services), README gates (EPIC‑010), canonical locations (geen nieuwe docs), schema.sql als bron, V2‑contracten.

Opdracht:
1) Doe eerst een grondige analyse:
   - Lees en kruislijn: IMPLEMENTATION_PLAN_CODEX.md, IMPLEMENTATION_PLAN_claude.md, CLAUDE.md, README.md.
   - Scan relevante codepaden en highlight API‑mismatches, naming/invariants (repo/workflow/validator/UI).
   - Benoem onbekenden/assumpties, quick wins vs. root‑cause fixes.
2) Lever output in deze structuur:
   - Bevindingen (feitelijk, met paden/IDs)
   - Conflicten/mismatches (wat ↔ waar)
   - Aanbevolen aanpak (stappen + rationale)
   - Risico’s + mitigaties
   - Testplan (unit/integratie, wat te verifiëren)
   - Acceptatiecriteria (checklist)
3) Gebruik het plan‑tool en werk het bij na elke fase.
4) Pas nog geen code; stel patches voor met minimale diffs en duidelijke context.
5) Vraag expliciet toestemming voor zware/risicovolle acties.

Let op:
- Gebruik `rg` voor snelle zoekacties; lees files in blokken ≤250 regels.
- Respecteer repository‑conventies (V2 orchestrator/validator, repository API, workflowservice, query‑param fallback).
- Noem alternatieven met voor/nadelen waar zinvol.
```

### Implementatie‑verdieping (na analyse)
```
Nu graag: 1) kort akkoord op aanpak, 2) minimal‑diff patchvoorstellen.
- Lever patchsets per logische unit (repo/validator/UI/workflow).
- Voeg bij elke patch: impact, rollback, en tests om groen te krijgen.
- Houd je aan: geen niet‑gerelateerde wijzigingen; gebruik bestaande namen/structuur.
```

### Pre‑flight Checklist
- Lees: `docs/backlog/EPIC-004/US-064/IMPLEMENTATION_PLAN_CODEX.md`
- Lees: `docs/backlog/EPIC-004/US-064/IMPLEMENTATION_PLAN_claude.md`
- Lees: `CLAUDE.md`, `README.md`
- Scan repo op: `get_or_create_draft`, `update_with_lock_check`, `change_status/update_status`, `ValidationOrchestratorV2.validate_text`, `definitie_voorbeelden` typen
- Check schema: `src/database/schema.sql` (UNIQUE, triggers, voorbeelden‑types)
- Noteer API‑mismatches en naming afwijken (organisatorische_context/juridische_context, detailed_scores, severity)

### Acceptatiecriteria (in je prompt opnemen)
- Eén actieve draft per combinatie (UNIQUE enforced; race‑safe INSERT→SELECT).
- Optimistic locking via `updated_at` + rowcount check; conflict‑UX voorstel aanwezig.
- Gates: `overall_score ≥ 0.80`; `detailed_scores['juridisch'] & ['structuur'] ≥ 0.75`; violations: error=blok, warning=waarschuwing.
- Voorbeelden‑delta: alleen gewijzigde rows; types exact volgens schema.
- Workflow: statuswijziging via `DefinitionWorkflowService` en `change_status` (of adapter `update_status`).
- UI: stateless navigatie met query‑param fallback; geen services in UI‑services importen; caching conform CLAUDE.md.

### Korte “Deep‑read” opener
```
Voer een deep‑read uit: kruis IMPLEMENTATION_PLAN_CODEX.md ↔ IMPLEMENTATION_PLAN_claude.md ↔ CLAUDE.md ↔ README.md. Som concrete mismatches + fixes op (API, naming, gates, repo/locking, workflow, voorbeelden). Nog geen code. Lever daarna een compact stappenplan + testplan.
```

---
Bronnen:
- Agents richtlijnen: `docs/guidelines/AGENTS.md`
- Multi‑Agent gids: `docs/handleidingen/ontwikkelaars/codex-multi-agent-gebruik.md`
- Projectrichtlijnen: `README.md`, `CLAUDE.md`

## No‑Assumptions / Strict Mode (Codex)

Doel: werken zonder aannames door beslissingen expliciet te maken en akkoord te vragen op tussenstappen.

- Strict proces
  - Start elk werk met `update_plan` + “open vragen/unknowns”; pauzeer tot goedkeuring.
  - Approval gates: geen codepatch, tests, netwerk of DB‑reset zonder expliciete OK.
  - Decision Log: leg beslissingen (geen aannames), motivatie en akkoordmoment vast.
- Vereiste input (voorkomt aannames)
  - Doel & scope, Definition of Done, acceptatiecriteria.
  - API/contracten en wijzigingsruimte (wat wel/niet aanpassen).
  - Randvoorwaarden: security, performance, UX/i18n/a11y, foutafhandeling.
  - Voorbeelden/tegenvoorbeelden + testdata (happy/edge/error cases).
  - Bron van waarheid en conflictbeleid bij inconsistenties.
- Verificatie en bewijs
  - Lever testopdracht/scenario’s; draai tests en toon resultaten (logs/diff/screenshot waar passend).
  - Per planstap een kort verificatieblok: wat geverifieerd, hoe, en met welk bewijs.
- Alternatieven en keuzes
  - Geef per ontwerpbesluit 2–3 alternatieven met trade‑offs; vraag om keuze vóór implementatie.
- Scope‑bescherming
  - Stel wijzigingsgrenzen: enkel paden X/Y, maximaal N regels diff, geen hernoem/format buiten scope.
  - Specificeer welke feature flags/env‑vars gebruikt mogen worden.
- Templates (handig)
  - Opdrachtbrief: doel, scope, DoD, constraints, risico’s, testcases, SSoT.
  - Review‑gate: beslissingen ter goedkeuring, impact, rollback, testplan.
- Direct toepasbaar in deze repo
  - Zet “no‑assumptions” actief: de agent stopt bij unknowns en vraagt om akkoord.
  - Start met een unknowns‑lijst en laat die expliciet goedkeuren vóór implementatie.

Zie ook: “Slash Commands (agent toggles)” hierboven om strict mode snel te togglen tijdens je sessie.
