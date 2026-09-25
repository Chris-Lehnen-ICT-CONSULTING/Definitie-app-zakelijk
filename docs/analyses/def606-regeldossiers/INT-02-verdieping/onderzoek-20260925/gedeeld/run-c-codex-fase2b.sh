#!/bin/bash
# Onderzoeker C — synthesecontrole in een VERSE Codex CLI-sessie (de app-thread 01a0d7b1… houdt een actieve writer; resume via CLI en thread-wissel via de app-UI in de achtergrond mislukten). Gestart door A (Cowork) 25-09-2026.
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
ABS=/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925
cd "$ABS/c-codex-app" || exit 2
echo "start $(date -u +%FT%TZ)" > "$ABS/c-codex-app-run2.status"
{ echo "Je bent onderzoeker C voor INT-02 (DEF-771). Jouw eigen eerste onderzoek staat in c-codex-app/onderzoek-c-v1.md en casusregister-c-v1.md (gemaakt in de Codex-app-sessie 01a0d7b1…; deze controle draait in een verse Codex CLI-sessie omdat die app-thread een actieve writer houdt). Lees eerst jouw eigen v1 volledig om je standpunt te hernemen; voer daarna de onderstaande opdracht uit. Werkroot is c-codex-app/; alle paden in de opdracht zijn relatief aan de onderzoeksmap $ABS (gebruik ../gedeeld/… en ../a-cowork/… vanuit jouw werkroot). Alles in het Nederlands."; echo; cat "$ABS/gedeeld/synthesecontrole-opdracht-c-v1.md"; } | nohup codex exec -s workspace-write -C "$ABS/c-codex-app" - > "$ABS/c-codex-app-run2.out" 2> "$ABS/c-codex-app-run2.err" &
echo "pid=$! started $(date -u +%FT%TZ)" >> "$ABS/c-codex-app-run2.status"
disown
exit 0
