#!/bin/bash
# Onderzoeker C — gerichte controle van v4 (synthesecontrole-opdracht-c-v2.md) in een VERSE Codex CLI-sessie (zelfde reden als fase2b: de app-thread 01a0d7b1… houdt een actieve writer). Gestart door A (Cowork) 25-09-2026.
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
ABS=/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925
cd "$ABS/c-codex-app" || exit 2
echo "start $(date -u +%FT%TZ)" > "$ABS/c-codex-app-run3.status"
{ echo "Je bent onderzoeker C voor INT-02 (DEF-771). Jouw eigen onderzoek staat in c-codex-app/onderzoek-c-v1.md en casusregister-c-v1.md; jouw synthesecontrole in c-codex-app/synthesecontrole-c-v1.md (gemaakt in een verse Codex CLI-sessie op 25-09, omdat de app-thread 01a0d7b1… een actieve writer houdt; deze controle draait om dezelfde reden opnieuw in een verse sessie). Lees eerst jouw synthesecontrole-c-v1.md volledig om je punten te hernemen; voer daarna de onderstaande opdracht uit. Werkroot is c-codex-app/; alle paden in de opdracht zijn relatief aan de onderzoeksmap $ABS (gebruik ../gedeeld/… en ../a-cowork/… vanuit jouw werkroot). Alles in het Nederlands."; echo; cat "$ABS/gedeeld/synthesecontrole-opdracht-c-v2.md"; } | nohup codex exec -s workspace-write -C "$ABS/c-codex-app" - > "$ABS/c-codex-app-run3.out" 2> "$ABS/c-codex-app-run3.err" &
echo "pid=$! started $(date -u +%FT%TZ)" >> "$ABS/c-codex-app-run3.status"
disown
exit 0
