#!/bin/bash
# Onderzoeker B — fase 1 (eigen v1), Codex CLI. Gestart door onderzoeker A (Cowork) op 25-09-2026 via osascript.
set -u
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd /Users/chrislehnen/Projecten/Definitie-app || exit 2
OUT=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925
ABS=/Users/chrislehnen/Projecten/Definitie-app/$OUT
echo "start $(date -u +%FT%TZ) codex=$(codex --version 2>&1)" > "$OUT/b-codex-cli-run1.status"
nohup codex exec -s workspace-write -C "$ABS/b-codex-cli" --add-dir /Users/chrislehnen/Projecten/Definitie-app/cache --json --output-last-message "$ABS/b-codex-cli-run1.last.md" - < "$ABS/gedeeld/startopdracht-b-v1.md" > "$ABS/b-codex-cli-run1.jsonl" 2> "$ABS/b-codex-cli-run1.err" &
echo "pid=$! started $(date -u +%FT%TZ)" >> "$OUT/b-codex-cli-run1.status"
disown
