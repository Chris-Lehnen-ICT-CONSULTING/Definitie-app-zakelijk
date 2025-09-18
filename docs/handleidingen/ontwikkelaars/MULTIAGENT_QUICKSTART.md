---
titel: Multi‑Agent Quickstart (Codex)
status: active
owner: development
canonical: false
last_verified: 2025-09-18
applies_to: definitie-app@current
---

# Multi‑Agent Quickstart (Codex)

Deze quickstart laat zien hoe je parallelle agents met Codex inzet via het script `scripts/multiagent.sh` en hoe je dit met slash‑commando’s aanstuurt.

## Installatie
Niets extra’s nodig. Het script staat in deze repo: `scripts/multiagent.sh`.

## Basiscommando’s
```bash
# 1) Maak 2 worktrees voor agent-a en agent-b
bash scripts/multiagent.sh init -n 2

# 2) Statusoverzicht (worktrees + lokale agent branches)
bash scripts/multiagent.sh status

# 3) Review/vergelijk branches (scoreboard); optioneel met quick checks
bash scripts/multiagent.sh review --quick-checks

# 4) Opruimen (worktrees weg, branches behouden of verwijderen)
bash scripts/multiagent.sh teardown
bash scripts/multiagent.sh teardown --delete-branches
```

## Aanbevolen werkwijze (2 agents)
1. `init -n 2` → opent `agent-a` (minimal) en `agent-b` (robuust)
2. Open beide worktrees in aparte terminals/editors en voer je aanpassingen uit
3. `review --quick-checks` → vergelijkt teststatus en timing (zie `reports/agent_scoreboard_*.log`)
4. Merge de winnaar naar `main` en ruim op met `teardown`

## Slash‑commando’s (conventie)
Gebruik onderstaande commando’s in je chat met Codex. De assistent vertaalt deze naar scriptacties:

- `/multi init` → `bash scripts/multiagent.sh init -n 2`
- `/multi status` → `bash scripts/multiagent.sh status`
- `/multi review` → `bash scripts/multiagent.sh review --quick-checks`
- `/multi teardown` → `bash scripts/multiagent.sh teardown`
- `/multi teardown all` → `bash scripts/multiagent.sh teardown --delete-branches`

Optioneel kun je namen meegeven: `/multi init agent-a agent-b agent-c`.

## Triggers via natuurlijke prompts
De assistent herkent ook enkele natuurtaal‑triggers en stelt het bijpassende commando voor:
- “Voer een parallelle multi‑agent code base review uit” → `/multi review`
- “Maak twee parallelle agents aan” → `/multi init`
- “Ruim de multi‑agent worktrees op” → `/multi teardown`

## Integratie met bestaande scripts
- Scoreboard: `scripts/agent_scoreboard.sh` (vereist `pytest`)
- Quick checks: `scripts/agent_quick_checks.sh` (EPIC‑010 greps + snelle tests)

## Tips
- Gebruik per worktree een andere Codex/Claude‑agent (bijv. minimal vs. robuust) voor variatie.
- Houd patches klein en doelgericht; kies de lichtste oplossing die voldoet.

