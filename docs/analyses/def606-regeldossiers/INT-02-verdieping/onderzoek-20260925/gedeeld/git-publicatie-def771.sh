#!/bin/bash
# Publicatie van het INT-02-onderzoeksdossier (DEF-771) in git: aparte docs-branch vanaf origin/main
# in een eigen worktree (de hoofdwerkboom staat op de INT-03-branch van een andere sessie en blijft onaangeroerd).
# Uitgevoerd door A (Cowork) op verzoek van Chris, 25-09-2026. Nooit op main.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO=/Users/chrislehnen/Projecten/Definitie-app
REL=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925
BRANCH=docs/DEF-771-int02-regeldossier
WT="$REPO/.claude/worktrees/DEF-771-int02-regeldossier"
cd "$REPO"
git fetch origin --quiet
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then echo "branch bestaat al: $BRANCH"; exit 3; fi
git worktree add "$WT" -b "$BRANCH" origin/main --quiet
mkdir -p "$WT/$(dirname "$REL")"
rsync -a "$REPO/$REL/" "$WT/$REL/"
cd "$WT"
git add "$REL"
echo "--- te committen bestanden: $(git status --short | wc -l | tr -d ' ')"
git status --short | awk '{print $2}' | sed "s#^$REL/##" | cut -d/ -f1 | sort | uniq -c
git commit --quiet -F - <<'MSG'
docs(DEF-771): INT-02-regeldossier — onderzoek vier lijnen, synthese v5 en besluiten Chris 25-09-2026

Onderzoeksdossier INT-02 (Geen beslisregel): onderzoekslijnen A (Claude Code CLI),
B (Codex CLI), C (Codex-app) en coördinator (Cowork), wederzijdse reviews,
verwerkingen, synthesecontroles B en C, gezamenlijke synthese v1–v5, besluitnotitie
v1–v5, gezamenlijk casusregister v1–v5 (76 casus-ID's), besluiten Chris K1–K5
(gedeeld/besluiten-chris-v1.md; DEF-831, DEF-832), bewijs (proeven, logs, manifests
met SHA-256), processtatus en ontvangstlog, en de uitvoeringsopdracht voor de
Codex-coördinator (niet gestart). Geen code-, norm- of skillwijziging.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01J97BQmzDZQwpmjJXXrccdi
MSG
echo "--- commit: $(git rev-parse --short HEAD) op $(git branch --show-current)"
git push --quiet -u origin "$BRANCH"
echo "--- gepusht: origin/$BRANCH"
