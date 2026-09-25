#!/bin/bash
# Onderzoeker C — synthesecontrole; hervat de Codex-app-sessie 01a0d7b1-e2da-7973-b542-44b023339e89 via de CLI (de app-UI kon vanuit de achtergrond niet naar de thread worden geschakeld). Gestart door A (Cowork) 25-09-2026.
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
ABS=/Users/chrislehnen/Projecten/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925
cd "$ABS/c-codex-app" || exit 2
echo "start $(date -u +%FT%TZ)" > "$ABS/c-codex-app-run2.status"
nohup codex exec resume 01a0d7b1-e2da-7973-b542-44b023339e89 - < "$ABS/gedeeld/synthesecontrole-opdracht-c-v1.md" > "$ABS/c-codex-app-run2.out" 2> "$ABS/c-codex-app-run2.err" &
echo "pid=$! started $(date -u +%FT%TZ)" >> "$ABS/c-codex-app-run2.status"
disown
exit 0
