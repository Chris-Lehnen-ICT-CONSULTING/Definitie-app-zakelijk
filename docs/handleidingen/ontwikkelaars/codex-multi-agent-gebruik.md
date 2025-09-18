---
titel: Codex Multi‑Agent Gebruik
aangemaakt: 2025-09-10
status: active
doel: Parallelle probleemoplossing en code‑voorstellen met meerdere agents
canonical: true
owner: development
last_verified: 2025-09-11
applies_to: definitie-app@current
---

# Codex Multi‑Agent Gebruik

Deze gids beschrijft hoe je meerdere “agents” (parallele Codex‑sessies/branches) dezelfde opdracht laat uitvoeren en daarna de beste oplossing selecteert en merge’t. Gericht op analyse, debuggen en code schrijven met dieper redeneren.

## Doel
- Parallel ideeën uitwerken zonder elkaar te blokkeren
- Snelste/robuste oplossing kiezen op basis van objectieve criteria (tests, perf, codekwaliteit)
- Minimale contextswitch door kant‑en‑klare workflow/commando’s

## Strategieën

### 1) Parallel met git worktrees (aanrader)
Maak per “agent” een eigen checkout met eigen branch.

```bash
# Vanuit de hoofdrepo map
git worktree add ../Definitie-app-agent-a -b agent-a
git worktree add ../Definitie-app-agent-b -b agent-b
# Optioneel een derde
git worktree add ../Definitie-app-agent-c -b agent-c

# Open per worktree een eigen terminal/Codex sessie
cd ../Definitie-app-agent-a   # Agent A: minimal patch / quick win
cd ../Definitie-app-agent-b   # Agent B: robuust + tests
cd ../Definitie-app-agent-c   # Agent C: performance/architectuur
```

Voordelen: volledige isolatie, parallel draaien van tests, heldere diffs. Nadelen: meer directories.

### Helper script (snelle start)
Gebruik `scripts/multiagent.sh` om worktrees/branches te beheren en te vergelijken zonder handwerk:

```bash
# 2 agents aanmaken (agent-a, agent-b)
bash scripts/multiagent.sh init -n 2

# Status en review
bash scripts/multiagent.sh status
bash scripts/multiagent.sh review --quick-checks

# Opruimen
bash scripts/multiagent.sh teardown
```

Slash‑commando’s (conventie in Codex‑chat):
- `/multi init` → `bash scripts/multiagent.sh init -n 2`
- `/multi status` → `bash scripts/multiagent.sh status`
- `/multi review` → `bash scripts/multiagent.sh review --quick-checks`
- `/multi teardown` → `bash scripts/multiagent.sh teardown`

Advies‑check (wanneer multi?):
- `bash scripts/multiagent.sh check` — geeft ‘Advice: YES/NO/MAYBE’ op basis van diff‑omvang en type (docs‑only, tiny, etc.).
- `init --strict` — stopt bij advies ‘NO’; `init --force` om te forceren.

### 2) Sequentieel met patches
Ieder voorstel als patchbestand opslaan en later vergelijken/apply’en.

```bash
# Agent A
# (wijzig code)
git diff > patches/agent-a.patch
git reset --hard

# Agent B
# (wijzig code)
git diff > patches/agent-b.patch

# Vergelijk/apply test
git apply --check patches/agent-a.patch && git apply patches/agent-a.patch && pytest -q
git reset --hard
git apply --check patches/agent-b.patch && git apply patches/agent-b.patch && pytest -q
```

Voordelen: één workspace. Nadelen: meer handwerk.

### 3) Debate/Critique patroon
Agent A maakt voorstel, Agent B reviewt/critique, A verbetert → “arbiter” kiest beste variant. Combineer met worktrees.

## Evaluatiecriteria (winnaar kiezen)
- Tests: alle relevante unit/integratie groen
- EPIC‑010 conformiteit: V2‑contract (dict), geen legacy/sync, canonical keys, endpoint‑timeouts
- Codechurn laag, complexiteit minimaal, duidelijke grenzen
- Performance/stabiliteit: geen timeouts, geen dubbele init, nette shutdown

Handige quick‑checks (EPIC‑010):
```bash
# Geen legacy patterns
rg -n "from src.models.generation_result import|best_iteration|asyncio\.run\(" src/ && echo "LEGACY FOUND" || echo "OK"

# V2 UI contract keys aanwezig in UI code
rg -n "definitie_gecorrigeerd|validation_details|voorbeelden|metadata" src/ui/
```

## Scoreboard (voorbeeld)
Eenvoudige evaluatie per branch. Sla op als `scripts/agent_scoreboard.sh` of voer ad‑hoc uit.

```bash
#!/usr/bin/env bash
set -euo pipefail
branches=(agent-a agent-b agent-c)
for b in "${branches[@]}"; do
  git checkout "$b" >/dev/null 2>&1 || continue
  start=$(date +%s)
  pytest -q || status=$?
  dur=$(( $(date +%s) - start ))
  echo "BRANCH=$b DURATION=${dur}s STATUS=${status:-0}"
done
```

## Codex Config (diepere redenering)
Voor grondige analyse/debug/code:

```bash
# Model en diepte
codex config set model=o1
codex config set temperature=0.1
codex config set max_output_tokens=4096

# Plan/trace/debug
codex config set plan.enabled=true
codex config set plan.autoupdate=true
codex config set trace.enabled=true
codex config set debug.enabled=true

# Patching/validatie
codex config set patch.confirm=true
codex config set test.auto=true
codex config set patch.preview=true

# Alias (optioneel)
alias codex-deep='codex --trace --debug'
```

### Slash Commands (toggles voor gedrag)
Gebruik deze in je Codex‑sessie om agents voorspelbaar en zonder aannames te laten werken. Uitgebreid beschreven in `docs/guidelines/AGENTS.md`.

- `/strict on` — activeer strict mode: geen aannames; pauze voor akkoord bij patches, tests, netwerk en DB‑reset.
- `/strict off` — deactiveer strict mode.
- `/approve` / `/approve all` — akkoord op de volgende (of alle huidige) geblokkeerde stappen.
- `/deny` — weiger de volgende stap; agent biedt alternatief of plant om.
- `/plan on` / `/plan off` — planmodus verplicht/uit.
- Scopes: `/strict on patch,test` om alleen bepaalde domeinen te gaten (`patch`, `test`, `network`, `db`, `all`).

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

Prompt‑preset (plak bovenaan je opdracht):

> Gebruik een stap‑voor‑stap plan (update_plan) en werk het na elke stap bij. Toon aannames, alternatieven en verificaties. Houd je aan V2‑contracten; geen legacy/sync. Voor code: eerst impactanalyse, dan minimale patch, daarna teststrategie en rollbackplan.

## Workflow Template
1. Opdracht definiëren + criteria (DoD)
2. Branches/worktrees aanmaken
3. Codex configeren (diep redeneren)
4. Agents laten werken (A: minimal, B: robuust, C: perf)
5. Per branch: pytest, quick‑checks, eventueel perf‑meting
6. Scoreboard + keuze
7. Final merge naar `main` (no‑ff) en cleanup worktrees

## Merge & Cleanup
```bash
git checkout main
git merge --no-ff agent-a -m "Merge agent-a: beste oplossing op criteria XYZ"
# Worktrees opruimen
git worktree remove ../Definitie-app-agent-a --force
git branch -D agent-a
```

## Tips & Valkuilen
- Timeouts harmoniseren via endpoint config i.p.v. hardcoded
- Houd UI sync‑bridging beperkt tot `ui/helpers/async_bridge.py`
- Idempotente registratie van modules (singleton via container)
- Memoization op dure loads (bv. toetsregels), éénmalig per sessie

## Voorbeeld: EPIC‑010 toepassing
- Gates: blokkeer legacy imports/`best_iteration`/`asyncio.run` in services
- V2‑dict‑only in UI (`definitie_gecorrigeerd`, `validation_details`, `voorbeelden`, `metadata`)
- Endpoint‑timeouts via `config/rate_limit_config.py`
- Parallel agents:
  - A: fix snelle blockers (timeouts, obvious bugs)
  - B: contractconsolidatie + tests
  - C: performance (async voorbeelden, caching, idempotency)

## Werkwijzen per type handeling

### Code Review (parallelle agents)
- Doel: snelle kwaliteitsbarrières, regressies voorkomen, risico’s zichtbaar maken.
- Agent‑rollen:
  - Agent A (Static): style/lint/typos/greps, quick test‑smoke
  - Agent B (Correctness): unit/integratie, contract‑checks, edge‑cases
  - Agent C (Arch/Sec): architectuurregels, dependency‑grenzen, security greps
- Setup (worktrees): `agent-a`, `agent-b`, `agent-c`
- Commando’s (voorbeeld):
  - Greps: `rg -n "best_iteration|asyncio\.run\(|from src\.models\.generation_result" src/`
  - Tests: `pytest -q && pytest tests/integration -q`
  - Coverage (optioneel): `pytest --cov=src --cov-report=term-missing`
- Checklist:
  - [ ] V2‑contracten in UI/Services (dicts)
  - [ ] Geen legacy/sync in services
  - [ ] Endpoint‑timeouts consistent
  - [ ] Log‑noise/Duplicate init afwezig
- Criteria voor “goedgekeurd”:
  - Tests groen, geen legacy greps, duidelijke changelog/PR‑beschrijving

### Refactoring (parallelle agents)
- Doel: complexiteit omlaag, legacy eruit, gedrag behouden (of bewust breken met migratie‑notities).
- Agent‑rollen:
  - Agent A (Minimal): kleinste set wijzigingen die legacy verwijdert + gates
  - Agent B (Structure): services/container/singletons/idempotency
  - Agent C (Perf): memoization/caching en init‑pad optimalisaties
- Plan:
  1) Inventarisatie (greps + dependency overview)
  2) Minimal refactor (A), structurele cleanups (B), perf (C)
  3) Tests/greps/bench, review en merge
- Commando’s:
  - Inventarisatie: `rg -n "TODO|DEPRECATED|LEGACY|FIXME" src/`
  - Legacy‑patronen: zie EPIC‑010 quick‑checks
  - Bench (indicatief): meet init/generatie timings in logs
- Criteria:
  - [ ] Geen legacy entrypoints, één source of truth voor contracten
  - [ ] Idempotente registratie, éénmalige loads
  - [ ] Tests ongewijzigd (indien mogelijk) of logisch geüpdatet

### Developing (feature/bugfix)
- Doel: TDD/verbetering met verifieerbaar gedrag.
- Agent‑rollen:
  - Agent A (TDD Minimal): failures eerst, kleinste implementatie, snelle feedback
  - Agent B (Integration/Telemetry): wiring + debug/metrics zichtbaar
  - Agent C (Hardening): edge cases, error‑paths, timeouts en retries
- Stappen:
  1) Schrijf/actualiseer tests (Unit + Integratie)
  2) Implementeer minimale oplossing (A)
  3) Integreer + logging/telemetry (B)
  4) Edge/hardening + timeouts/retries (C)
  5) Scoreboard & keuze
- Commando’s:
  - `pytest tests/unit/<spec>.py -q`
  - `pytest tests/integration -q`
- Criteria:
  - [ ] Tests groen, debug‑zichtbaarheid, duidelijke DoD in PR

### Analyse (bug/perf/arch)
- Doel: reproduceerbaar, meetbaar, gefundeerde root‑cause en oplossingsopties.
- Agent‑rollen:
  - Agent A (Repro): minimal script + logging + toggles (flags/feature)
  - Agent B (Trace/Perf): timers, timeouts, call‑graph, bottlenecks
  - Agent C (Options): alternatieven, risico’s, impact, implementatieplan
- Stappen:
  1) Minimal repro script (A) + toggles (bv. web lookup aan/uit)
  2) Trace tijden (B): timestamps rond kritieke fasen (AI, web lookup, validatie)
  3) Root‑cause + opties (C) → voorstel met DoD/risico’s/rollback
- Commando’s (voorbeeld):
  - `python debug_scripts/repro_<bug>.py`
  - `export DEBUG_EXAMPLES=true` en logs inspecteren
- Criteria:
  - [ ] Repro duidelijk
  - [ ] Root‑cause aannemelijk + alternatief vergeleken
  - [ ] Aanbeveling met concrete stappen + verificatieplan

## Aanvullende scripts (optioneel)
- `scripts/agent_scoreboard.sh` — vergelijkt branches (duur/status)
- `scripts/agent_quick_checks.sh` — draait EPIC‑010 greps en basis tests
