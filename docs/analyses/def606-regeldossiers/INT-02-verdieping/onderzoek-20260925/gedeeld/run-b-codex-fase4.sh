#!/bin/bash
# Onderzoeker B — fase 4 (synthesecontrole), Codex CLI, hervat thread 01a0d783-365b-7d82-81d3-684fd0e016fc. Gestart door A (Cowork) 25-09-2026.
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
OUT=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925
ABS=/Users/chrislehnen/Projecten/Definitie-app/$OUT
cd "$ABS/b-codex-cli" || exit 2
echo "start $(date -u +%FT%TZ)" > "$ABS/b-codex-cli-run4.status"
nohup codex exec resume 01a0d783-365b-7d82-81d3-684fd0e016fc - < "$ABS/gedeeld/synthesecontrole-opdracht-b-v1.md" > "$ABS/b-codex-cli-run4.out" 2> "$ABS/b-codex-cli-run4.err" &
echo "pid=$! started $(date -u +%FT%TZ)" >> "$ABS/b-codex-cli-run4.status"
disown
